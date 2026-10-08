"""Read side: the Today queue, timely signals, and opportunity detail."""

from collections import Counter
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tr3ndly.config import Settings
from tr3ndly.db.models import (
    EventCluster,
    EventStatus,
    ListingSearchFailure,
    Opportunity,
    OpportunityEvidence,
    OpportunityReason,
    OpportunityStatus,
    Sensitivity,
)
from tr3ndly.db.types import utcnow
from tr3ndly.intelligence.catalog import NEED_LABELS
from tr3ndly.operations import has_live_data, overall_health, source_statuses
from tr3ndly.opportunities.decisions import is_decidable
from tr3ndly.opportunities.listings import is_matchable
from tr3ndly.opportunities.views import (
    rank_value,
    to_decision,
    to_match,
    to_search_failure,
    to_summary,
)
from tr3ndly.schemas import OpportunityDetail, TimelySignal, TodayResponse

TODAY_LIMIT = 8
# Diversity rule: at most this many cards may come from the same event.
PER_EVENT_LIMIT = 2
SIGNAL_LIMIT = 3
HIDDEN_FROM_TODAY = (OpportunityStatus.REJECTED, OpportunityStatus.EXPIRED)


class OpportunityQueries:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def today(
        self,
        now: datetime | None = None,
        *,
        location: str | None = None,
        reason_type: OpportunityReason | None = None,
    ) -> TodayResponse:
        now = now or utcnow()
        live = await has_live_data(self.session)
        statuses = await source_statuses(self.session, self.settings, now)

        candidates = [
            item for item in await self.session.scalars(self._open_queue(now, live)) if item.scores
        ]
        locations = sorted({item.location for item in candidates})
        if location:
            candidates = [item for item in candidates if item.location == location]
        if reason_type:
            candidates = [item for item in candidates if item.reason_type == reason_type]
        candidates.sort(key=rank_value, reverse=True)

        return TodayResponse(
            generated_at=now,
            mode="live" if live else "demo",
            source_health=overall_health(statuses, live),
            sources=statuses,
            locations=locations,
            signals=await self._top_signals(now, location),
            opportunities=[to_summary(item) for item in _diverse(candidates)],
        )

    async def detail(
        self, opportunity_id: str, now: datetime | None = None
    ) -> OpportunityDetail | None:
        now = now or utcnow()
        opportunity = await self.session.scalar(
            select(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .options(
                selectinload(Opportunity.evidence).selectinload(OpportunityEvidence.raw_signal),
                selectinload(Opportunity.scores),
                selectinload(Opportunity.decisions),
                selectinload(Opportunity.product_matches),
            )
        )
        if opportunity is None or not opportunity.scores:
            return None
        decisions = sorted(opportunity.decisions, key=lambda item: item.created_at, reverse=True)
        matches = sorted(
            opportunity.product_matches, key=lambda item: item.created_at, reverse=True
        )
        failures = await self.session.scalars(
            select(ListingSearchFailure)
            .where(ListingSearchFailure.opportunity_id == opportunity.id)
            .order_by(ListingSearchFailure.created_at.desc())
        )
        return OpportunityDetail(
            **to_summary(opportunity).model_dump(),
            status=opportunity.status.value,
            decidable=is_decidable(opportunity, now),
            matchable=is_matchable(opportunity, now),
            decisions=[to_decision(item) for item in decisions],
            product_matches=[to_match(item) for item in matches],
            search_failures=[to_search_failure(item) for item in failures],
        )

    def _open_queue(self, now: datetime, live: bool) -> Select[tuple[Opportunity]]:
        statement = (
            select(Opportunity)
            .where(Opportunity.expires_at > now, Opportunity.status.not_in(HIDDEN_FROM_TODAY))
            .options(
                selectinload(Opportunity.evidence).selectinload(OpportunityEvidence.raw_signal),
                selectinload(Opportunity.scores),
            )
        )
        if live:
            # Seeded demo cards must never sit next to live recommendations.
            statement = statement.where(Opportunity.is_demo.is_(False))
        return statement

    async def _top_signals(self, now: datetime, location: str | None) -> list[TimelySignal]:
        statement = (
            select(EventCluster)
            .where(
                EventCluster.status == EventStatus.ACTIVE,
                EventCluster.expires_at > now,
                EventCluster.sensitivity != Sensitivity.BLOCKED,
                EventCluster.timely_score >= self.settings.min_timely_score,
            )
            .order_by(EventCluster.timely_score.desc(), EventCluster.last_seen_at.desc())
            .limit(SIGNAL_LIMIT)
        )
        if location:
            statement = statement.where(EventCluster.location == location)
        return [
            TimelySignal(
                id=cluster.id,
                headline=cluster.title,
                event_type=cluster.event_type,
                location=cluster.location,
                summary=cluster.summary,
                confidence=cluster.confidence,
                consumer_needs=[NEED_LABELS.get(need, need) for need in cluster.consumer_needs],
                timely_score=cluster.timely_score,
                sensitivity=cluster.sensitivity.value,
                expires_at=cluster.expires_at,
            )
            for cluster in await self.session.scalars(statement)
        ]


def _diverse(ranked: list[Opportunity]) -> list[Opportunity]:
    chosen: list[Opportunity] = []
    per_event: Counter[str] = Counter()
    for item in ranked:
        group = item.event_cluster_id or item.id
        if per_event[group] >= PER_EVENT_LIMIT:
            continue
        per_event[group] += 1
        chosen.append(item)
        if len(chosen) == TODAY_LIMIT:
            break
    return chosen

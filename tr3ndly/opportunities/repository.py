from collections import Counter
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tr3ndly.config import Settings
from tr3ndly.db.models import (
    DecisionEvent,
    DecisionType,
    EventCluster,
    EventStatus,
    Opportunity,
    OpportunityStatus,
    ScoreSnapshot,
    Sensitivity,
)
from tr3ndly.db.types import utcnow
from tr3ndly.intelligence.catalog import NEED_LABELS
from tr3ndly.operations import has_live_data, overall_health, source_statuses
from tr3ndly.schemas import (
    DecisionCreate,
    DecisionResponse,
    Evidence,
    OpportunityDetail,
    OpportunitySummary,
    ScoreBreakdown,
    TimelySignal,
    TodayResponse,
)

TODAY_LIMIT = 8
# Diversity rule: at most this many cards may come from the same event.
PER_EVENT_LIMIT = 2
SIGNAL_LIMIT = 3
HIDDEN_FROM_TODAY = (OpportunityStatus.REJECTED, OpportunityStatus.EXPIRED)

STATUS_BY_DECISION = {
    DecisionType.ACCEPTED: OpportunityStatus.ACCEPTED,
    DecisionType.REJECTED: OpportunityStatus.REJECTED,
    DecisionType.DEFERRED: OpportunityStatus.DEFERRED,
    DecisionType.INSUFFICIENT_EVIDENCE: OpportunityStatus.DEFERRED,
}
# Expired and matched opportunities are closed to new decisions.
DECIDABLE = (
    OpportunityStatus.ELIGIBLE,
    OpportunityStatus.ACCEPTED,
    OpportunityStatus.REJECTED,
    OpportunityStatus.DEFERRED,
)


class OpportunityNotFound(Exception):
    pass


class DecisionNotAllowed(Exception):
    pass


class OpportunityRepository:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def get_today(self, now: datetime | None = None) -> TodayResponse:
        now = now or utcnow()
        live = await has_live_data(self.session)
        statuses = await source_statuses(self.session, self.settings, now)

        statement = (
            select(Opportunity)
            .where(Opportunity.expires_at > now, Opportunity.status.not_in(HIDDEN_FROM_TODAY))
            .options(selectinload(Opportunity.evidence), selectinload(Opportunity.scores))
        )
        if live:
            # Seeded demo cards must never sit next to live recommendations.
            statement = statement.where(Opportunity.is_demo.is_(False))
        candidates = [item for item in await self.session.scalars(statement) if item.scores]
        candidates.sort(key=lambda item: _latest_score(item).discovery_priority, reverse=True)

        chosen: list[Opportunity] = []
        per_event: Counter[str] = Counter()
        for item in candidates:
            group = item.event_cluster_id or item.id
            if per_event[group] >= PER_EVENT_LIMIT:
                continue
            per_event[group] += 1
            chosen.append(item)
            if len(chosen) == TODAY_LIMIT:
                break

        return TodayResponse(
            generated_at=now,
            mode="live" if live else "demo",
            source_health=overall_health(statuses, live),
            sources=statuses,
            signals=await self._top_signals(now),
            opportunities=[_to_summary(item) for item in chosen],
        )

    async def get_detail(self, opportunity_id: str) -> OpportunityDetail | None:
        opportunity = await self.session.scalar(
            select(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .options(
                selectinload(Opportunity.evidence),
                selectinload(Opportunity.scores),
                selectinload(Opportunity.decisions),
            )
        )
        if opportunity is None or not opportunity.scores:
            return None
        decisions = sorted(opportunity.decisions, key=lambda item: item.created_at, reverse=True)
        return OpportunityDetail(
            **_to_summary(opportunity).model_dump(),
            status=opportunity.status.value,
            decisions=[_to_decision(item) for item in decisions],
        )

    async def record_decision(
        self, opportunity_id: str, payload: DecisionCreate, now: datetime | None = None
    ) -> DecisionResponse:
        now = now or utcnow()
        opportunity = await self.session.scalar(
            select(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .options(selectinload(Opportunity.scores))
        )
        if opportunity is None:
            raise OpportunityNotFound(opportunity_id)
        if opportunity.status not in DECIDABLE or opportunity.expires_at <= now:
            raise DecisionNotAllowed(
                f"Opportunity is {opportunity.status.value} and can no longer be decided"
                if opportunity.status not in DECIDABLE
                else "Opportunity window has expired"
            )
        if not opportunity.scores:
            raise DecisionNotAllowed("Opportunity has no score snapshot to decide against")

        decision_type = DecisionType(payload.decision)
        event = DecisionEvent(
            opportunity_id=opportunity_id,
            decision=decision_type,
            reason_code=payload.reason_code,
            note=payload.note,
            score_version=_latest_score(opportunity).version,
        )
        opportunity.status = STATUS_BY_DECISION[decision_type]
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return _to_decision(event)

    async def _top_signals(self, now: datetime) -> list[TimelySignal]:
        clusters = await self.session.scalars(
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
            for cluster in clusters
        ]


def _latest_score(opportunity: Opportunity) -> ScoreSnapshot:
    return max(opportunity.scores, key=lambda item: (item.created_at, item.id))


def _to_summary(opportunity: Opportunity) -> OpportunitySummary:
    score = _latest_score(opportunity)
    # Evidence rows are append-only; show the newest observation of each item.
    newest: dict[tuple[str, str], Evidence] = {}
    for item in sorted(opportunity.evidence, key=lambda row: row.observed_at):
        key = (item.source_name, item.summary.split(".")[0])
        newest[key] = Evidence(
            source_name=item.source_name,
            source_url=item.source_url,
            observed_at=item.observed_at,
            summary=item.summary,
        )
    return OpportunitySummary(
        id=opportunity.id,
        product_concept=opportunity.product_concept,
        category=opportunity.category,
        reason_type=opportunity.reason_type.value,
        why_now=opportunity.why_now,
        target_user=opportunity.target_user,
        location=opportunity.location,
        expires_at=opportunity.expires_at,
        score=ScoreBreakdown(
            demand=score.demand,
            execution=score.execution,
            marketplace_fit_prior=score.marketplace_fit_prior,
            uncertainty_penalty=score.uncertainty_penalty,
            discovery_priority=score.discovery_priority,
            timely_score=score.timely_score,
            trend_score=score.trend_score,
            version=score.version,
        ),
        search_queries=opportunity.search_queries,
        uncertainties=opportunity.uncertainties,
        evidence=list(newest.values()),
    )


def _to_decision(event: DecisionEvent) -> DecisionResponse:
    return DecisionResponse(
        id=event.id,
        opportunity_id=event.opportunity_id,
        decision=event.decision.value,
        reason_code=event.reason_code,
        note=event.note,
        score_version=event.score_version,
        created_at=event.created_at,
    )

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.schemas import (
    DecisionCreate,
    DecisionResponse,
    Evidence,
    OpportunityDetail,
    OpportunitySummary,
    ScoreBreakdown,
    SourceHealth,
    TodayResponse,
)
from tr3ndly.db.models import (
    DecisionEvent,
    DecisionType,
    Opportunity,
    OpportunityStatus,
    ScoreSnapshot,
)


class OpportunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_today(self, now: datetime | None = None) -> TodayResponse:
        now = now or datetime.now(UTC)
        statement = (
            select(Opportunity)
            .where(
                Opportunity.expires_at > now,
                Opportunity.status.not_in([OpportunityStatus.REJECTED, OpportunityStatus.EXPIRED]),
            )
            .options(selectinload(Opportunity.evidence), selectinload(Opportunity.scores))
        )
        opportunities = list((await self.session.scalars(statement)).unique())
        opportunities.sort(
            key=lambda item: self._latest_score(item).discovery_priority,
            reverse=True,
        )
        summaries = [self._to_summary(item) for item in opportunities]
        is_demo = bool(opportunities) and all(item.is_demo for item in opportunities)
        return TodayResponse(
            generated_at=now,
            mode="demo" if is_demo else "live",
            source_health=SourceHealth.DEMO if is_demo else SourceHealth.HEALTHY,
            signals=[],
            opportunities=summaries,
        )

    async def get_detail(self, opportunity_id: str) -> OpportunityDetail | None:
        statement = (
            select(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .options(
                selectinload(Opportunity.evidence),
                selectinload(Opportunity.scores),
                selectinload(Opportunity.decisions),
            )
        )
        opportunity = (await self.session.scalars(statement)).unique().one_or_none()
        if opportunity is None:
            return None
        summary = self._to_summary(opportunity)
        decisions = sorted(opportunity.decisions, key=lambda item: item.created_at, reverse=True)
        return OpportunityDetail(
            **summary.model_dump(),
            status=opportunity.status.value,
            decisions=[self._to_decision(item) for item in decisions],
        )

    async def record_decision(
        self, opportunity_id: str, payload: DecisionCreate
    ) -> DecisionResponse | None:
        opportunity = await self.session.get(Opportunity, opportunity_id)
        if opportunity is None:
            return None

        latest_score = await self._load_latest_score(opportunity_id)
        decision_type = DecisionType(payload.decision)
        event = DecisionEvent(
            opportunity_id=opportunity_id,
            decision=decision_type,
            reason_code=payload.reason_code,
            note=payload.note,
            score_version=latest_score.version,
        )
        status_by_decision = {
            DecisionType.ACCEPTED: OpportunityStatus.ACCEPTED,
            DecisionType.REJECTED: OpportunityStatus.REJECTED,
            DecisionType.DEFERRED: OpportunityStatus.DEFERRED,
            DecisionType.INSUFFICIENT_EVIDENCE: OpportunityStatus.DEFERRED,
        }
        opportunity.status = status_by_decision[decision_type]
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return self._to_decision(event)

    async def _load_latest_score(self, opportunity_id: str) -> ScoreSnapshot:
        statement = (
            select(ScoreSnapshot)
            .where(ScoreSnapshot.opportunity_id == opportunity_id)
            .order_by(ScoreSnapshot.created_at.desc(), ScoreSnapshot.id.desc())
            .limit(1)
        )
        score = await self.session.scalar(statement)
        if score is None:
            raise ValueError("Opportunity has no score snapshot")
        return score

    @staticmethod
    def _latest_score(opportunity: Opportunity) -> ScoreSnapshot:
        if not opportunity.scores:
            raise ValueError("Opportunity has no score snapshot")
        return max(opportunity.scores, key=lambda item: (item.created_at, item.id))

    @classmethod
    def _to_summary(cls, opportunity: Opportunity) -> OpportunitySummary:
        score = cls._latest_score(opportunity)
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
                version=score.version,
            ),
            search_queries=opportunity.search_queries,
            uncertainties=opportunity.uncertainties,
            evidence=[
                Evidence(
                    source_name=item.source_name,
                    source_url=item.source_url,
                    observed_at=item.observed_at,
                    summary=item.summary,
                )
                for item in opportunity.evidence
            ],
        )

    @staticmethod
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

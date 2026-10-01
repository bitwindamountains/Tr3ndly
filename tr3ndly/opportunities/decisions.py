"""Write side: operator decisions and the opportunity state rules they follow."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tr3ndly.db.models import DecisionEvent, DecisionType, Opportunity, OpportunityStatus
from tr3ndly.db.types import utcnow
from tr3ndly.opportunities.views import latest_score, to_decision
from tr3ndly.schemas import DecisionCreate, DecisionResponse

STATUS_BY_DECISION = {
    DecisionType.ACCEPTED: OpportunityStatus.ACCEPTED,
    DecisionType.REJECTED: OpportunityStatus.REJECTED,
    DecisionType.DEFERRED: OpportunityStatus.DEFERRED,
    DecisionType.INSUFFICIENT_EVIDENCE: OpportunityStatus.DEFERRED,
}
# Expired and matched opportunities are closed to new decisions; a rejection can be revisited.
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


async def record_decision(
    session: AsyncSession,
    opportunity_id: str,
    payload: DecisionCreate,
    now: datetime | None = None,
) -> DecisionResponse:
    now = now or utcnow()
    opportunity = await session.scalar(
        select(Opportunity)
        .where(Opportunity.id == opportunity_id)
        .options(selectinload(Opportunity.scores))
    )
    if opportunity is None:
        raise OpportunityNotFound(opportunity_id)
    if opportunity.status not in DECIDABLE:
        raise DecisionNotAllowed(
            f"Opportunity is {opportunity.status.value} and can no longer be decided"
        )
    if opportunity.expires_at <= now:
        raise DecisionNotAllowed("Opportunity window has expired")
    if not opportunity.scores:
        raise DecisionNotAllowed("Opportunity has no score snapshot to decide against")

    decision_type = DecisionType(payload.decision)
    event = DecisionEvent(
        opportunity_id=opportunity_id,
        decision=decision_type,
        reason_code=payload.reason_code,
        note=payload.note,
        score_version=latest_score(opportunity).version,
    )
    opportunity.status = STATUS_BY_DECISION[decision_type]
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return to_decision(event)

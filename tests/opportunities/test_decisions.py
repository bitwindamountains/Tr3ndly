from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tr3ndly.config import Settings
from tr3ndly.db.models import Opportunity, OpportunityStatus
from tr3ndly.db.types import utcnow
from tr3ndly.opportunities.demo import DEMO_OPPORTUNITY_ID, build_demo_opportunity
from tr3ndly.opportunities.repository import (
    DecisionNotAllowed,
    OpportunityNotFound,
    OpportunityRepository,
)
from tr3ndly.schemas import DecisionCreate

Sessions = async_sessionmaker[AsyncSession]
ACCEPT = DecisionCreate(decision="accepted", reason_code="useful_opportunity")


async def seed(sessions: Sessions, status: OpportunityStatus, expires_in: timedelta) -> None:
    async with sessions() as session:
        opportunity = build_demo_opportunity()
        opportunity.status = status
        opportunity.expires_at = utcnow() + expires_in
        session.add(opportunity)
        await session.commit()


@pytest.mark.parametrize("status", [OpportunityStatus.EXPIRED, OpportunityStatus.MATCHED])
async def test_closed_opportunities_refuse_decisions(
    sessions: Sessions, status: OpportunityStatus
) -> None:
    await seed(sessions, status, timedelta(days=1))
    async with sessions() as session:
        with pytest.raises(DecisionNotAllowed, match=status.value):
            await OpportunityRepository(session, Settings()).record_decision(
                DEMO_OPPORTUNITY_ID, ACCEPT
            )


async def test_window_that_has_passed_refuses_decisions(sessions: Sessions) -> None:
    await seed(sessions, OpportunityStatus.ELIGIBLE, timedelta(hours=-1))
    async with sessions() as session:
        with pytest.raises(DecisionNotAllowed, match="expired"):
            await OpportunityRepository(session, Settings()).record_decision(
                DEMO_OPPORTUNITY_ID, ACCEPT
            )


async def test_operator_can_reconsider_a_rejection(sessions: Sessions) -> None:
    await seed(sessions, OpportunityStatus.REJECTED, timedelta(days=1))
    async with sessions() as session:
        await OpportunityRepository(session, Settings()).record_decision(
            DEMO_OPPORTUNITY_ID, ACCEPT
        )
        opportunity = await session.get(Opportunity, DEMO_OPPORTUNITY_ID)
        assert opportunity is not None and opportunity.status == OpportunityStatus.ACCEPTED


async def test_unknown_opportunity_is_not_found(sessions: Sessions) -> None:
    async with sessions() as session:
        with pytest.raises(OpportunityNotFound):
            await OpportunityRepository(session, Settings()).record_decision("missing", ACCEPT)

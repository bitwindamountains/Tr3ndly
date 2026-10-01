import asyncio

from sqlalchemy import select

from apps.api.app.database import dispose_engine, session_factory
from tr3ndly.db.models import Opportunity
from tr3ndly.opportunities.demo import DEMO_OPPORTUNITY_ID, build_demo_opportunity


async def seed() -> None:
    async with session_factory() as session:
        existing = await session.scalar(
            select(Opportunity.id).where(Opportunity.id == DEMO_OPPORTUNITY_ID)
        )
        if existing:
            print("Demo opportunity already exists.")
            return

        session.add(build_demo_opportunity())
        await session.commit()
        print(f"Created {DEMO_OPPORTUNITY_ID}.")


async def main() -> None:
    try:
        await seed()
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())

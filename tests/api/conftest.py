import asyncio
from collections.abc import AsyncIterator, Callable, Iterator
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from apps.api.app.database import get_session
from apps.api.app.main import app
from tests.conftest import database_url, load_forecast, mock_client, reset_schema
from tr3ndly.db.session import build_engine
from tr3ndly.db.types import utcnow
from tr3ndly.geo import MANILA
from tr3ndly.opportunities.demo import build_demo_opportunity
from tr3ndly.pipeline import run_source
from tr3ndly.sources.open_meteo import OpenMeteoAdapter

Prepare = Callable[[async_sessionmaker[AsyncSession]], object]


async def seed_demo(sessions: async_sessionmaker[AsyncSession]) -> None:
    async with sessions() as session:
        session.add(build_demo_opportunity())
        await session.commit()


async def seed_live(sessions: async_sessionmaker[AsyncSession]) -> None:
    await seed_demo(sessions)
    # Shift the fixture so its first day is today in Manila, keeping tests date-independent.
    today = utcnow().astimezone(MANILA).date()
    forecast = load_forecast()
    for location in forecast:
        location["daily"]["time"] = [str(today + timedelta(days=day)) for day in range(3)]
    async with mock_client(forecast) as client:
        await run_source(sessions, OpenMeteoAdapter(), client, min_timely_score=65)


def make_client(tmp_path: Path, prepare: Prepare) -> Iterator[TestClient]:
    # Setup and TestClient run in different event loops; asyncpg connections cannot cross them.
    test_engine = build_engine(database_url(tmp_path), poolclass=NullPool)
    test_sessions = async_sessionmaker(test_engine, expire_on_commit=False)

    async def prepare_database() -> None:
        await reset_schema(test_engine)
        await prepare(test_sessions)  # type: ignore[misc]

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with test_sessions() as session:
            yield session

    asyncio.run(prepare_database())
    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    asyncio.run(test_engine.dispose())


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    yield from make_client(tmp_path, seed_demo)


@pytest.fixture
def live_client(tmp_path: Path) -> Iterator[TestClient]:
    yield from make_client(tmp_path, seed_live)

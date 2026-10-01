import copy
import json
import os
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from tr3ndly.db.base import Base
from tr3ndly.db.session import build_engine

FIXTURES = Path(__file__).parent / "fixtures"
# 08:00 in Manila on the first fixture day.
FIXTURE_NOW = datetime(2026, 10, 2, 0, 0, tzinfo=UTC)


def load_forecast() -> list[dict[str, Any]]:
    return json.loads((FIXTURES / "open_meteo_forecast.json").read_text(encoding="utf-8"))


@pytest.fixture
def forecast() -> list[dict[str, Any]]:
    return copy.deepcopy(load_forecast())


def mock_client(payload: Callable[[], Any] | Any, status_code: int = 200) -> httpx.AsyncClient:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body = payload() if callable(payload) else payload
        return httpx.Response(status_code, json=body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client.requests = requests  # type: ignore[attr-defined]
    return client


def database_url(tmp_path: Path) -> str:
    """TEST_DATABASE_URL (e.g. PostgreSQL in CI) or a throwaway SQLite file."""
    return os.environ.get("TEST_DATABASE_URL") or f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"


async def reset_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            # A shared server keeps state between tests (including alembic_version).
            await connection.execute(text("DROP SCHEMA public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))
        await connection.run_sync(Base.metadata.create_all)


@pytest.fixture
async def sessions(tmp_path: Path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = build_engine(database_url(tmp_path))
    await reset_schema(engine)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()

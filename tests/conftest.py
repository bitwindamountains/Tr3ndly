import copy
import json
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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


@pytest.fixture
async def sessions(tmp_path: Path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = build_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()

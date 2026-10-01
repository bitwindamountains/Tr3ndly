from datetime import timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.conftest import mock_client
from tr3ndly.config import Settings
from tr3ndly.db.models import SourceRun, SourceRunStatus
from tr3ndly.db.types import utcnow
from tr3ndly.pipeline import ensure_source_config
from tr3ndly.sources.open_meteo import OpenMeteoAdapter
from tr3ndly.worker import fail_abandoned_runs, is_due, tick

Sessions = async_sessionmaker[AsyncSession]


async def add_run(sessions: Sessions, status: SourceRunStatus, age: timedelta) -> None:
    async with sessions() as session:
        source = await ensure_source_config(session, OpenMeteoAdapter.definition, enabled=True)
        session.add(SourceRun(source_id=source.id, status=status, started_at=utcnow() - age))
        await session.commit()


async def test_never_run_source_is_due(sessions: Sessions) -> None:
    assert await is_due(sessions, OpenMeteoAdapter(), utcnow())


async def test_due_follows_poll_interval_and_retries_failures_sooner(sessions: Sessions) -> None:
    adapter = OpenMeteoAdapter()
    await add_run(sessions, SourceRunStatus.SUCCEEDED, timedelta(hours=1))
    assert not await is_due(sessions, adapter, utcnow())

    await add_run(sessions, SourceRunStatus.FAILED, timedelta(minutes=20))
    assert await is_due(sessions, adapter, utcnow())


async def test_running_source_is_not_started_twice(sessions: Sessions) -> None:
    await add_run(sessions, SourceRunStatus.RUNNING, timedelta(minutes=5))
    assert not await is_due(sessions, OpenMeteoAdapter(), utcnow())


async def test_abandoned_runs_are_failed(sessions: Sessions) -> None:
    await add_run(sessions, SourceRunStatus.RUNNING, timedelta(hours=2))
    assert await fail_abandoned_runs(sessions, utcnow()) == 1


async def test_tick_runs_only_enabled_sources(
    sessions: Sessions, forecast: list[dict[str, Any]]
) -> None:
    adapters = {"open-meteo": OpenMeteoAdapter()}
    async with mock_client(forecast) as client:
        disabled = await tick(sessions, adapters, Settings(enabled_sources=[]), client)
        enabled = await tick(sessions, adapters, Settings(enabled_sources=["open-meteo"]), client)

    assert disabled == []
    assert [result.status for result in enabled] == [SourceRunStatus.SUCCEEDED]


def test_enabled_sources_accepts_a_comma_separated_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("ENABLED_SOURCES", "open-meteo, other")
    assert Settings().enabled_sources == ["open-meteo", "other"]


def test_production_refuses_the_non_commercial_free_api() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="non-commercial"):
        Settings(environment="production", enabled_sources=["open-meteo"])
    Settings(environment="production", enabled_sources=["open-meteo"], open_meteo_api_key="k")

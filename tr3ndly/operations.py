"""Source health and run history: what the operator needs to know before trusting Today."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tr3ndly.config import Settings
from tr3ndly.db.models import SourceConfig, SourceRun, SourceRunStatus
from tr3ndly.schemas import SourceHealth, SourceRunView, SourceState, SourceStatus
from tr3ndly.sources import build_adapters

# How late a source may be before Today is marked degraded.
STALE_GRACE = timedelta(minutes=15)


async def source_statuses(
    session: AsyncSession, settings: Settings, now: datetime
) -> list[SourceStatus]:
    configs = {config.slug: config for config in await session.scalars(select(SourceConfig))}
    statuses: list[SourceStatus] = []
    for slug, adapter in build_adapters(settings).items():
        definition = adapter.definition
        config = configs.get(slug)
        last_run = last_finished = last_success = None
        if config is not None:
            last_run = await _latest_run(session, config.id)
            last_finished = await _latest_run(session, config.id, exclude_running=True)
            last_success = await _latest_run(session, config.id, SourceRunStatus.SUCCEEDED)

        if slug not in settings.enabled_sources:
            state = SourceState.DISABLED
        elif last_finished is None:
            state = SourceState.NEVER_RUN
        elif last_finished.status == SourceRunStatus.FAILED:
            state = SourceState.FAILING
        elif last_success is None or _is_stale(last_success, definition.poll_interval, now):
            state = SourceState.DEGRADED
        else:
            state = SourceState.HEALTHY

        statuses.append(
            SourceStatus(
                slug=slug,
                display_name=definition.display_name,
                state=state,
                poll_interval_minutes=int(definition.poll_interval.total_seconds() // 60),
                attribution=definition.attribution,
                last_run_at=last_run.started_at if last_run else None,
                last_success_at=_finished(last_success),
                last_error=last_finished.error
                if last_finished and last_finished.status == SourceRunStatus.FAILED
                else None,
            )
        )
    return statuses


def overall_health(statuses: list[SourceStatus], live: bool) -> SourceHealth:
    if not live:
        return SourceHealth.DEMO
    active = [status for status in statuses if status.state != SourceState.DISABLED]
    if active and all(status.state == SourceState.HEALTHY for status in active):
        return SourceHealth.HEALTHY
    return SourceHealth.DEGRADED


async def has_live_data(session: AsyncSession) -> bool:
    run_id = await session.scalar(
        select(SourceRun.id).where(SourceRun.status == SourceRunStatus.SUCCEEDED).limit(1)
    )
    return run_id is not None


async def recent_runs(session: AsyncSession, limit: int = 20) -> list[SourceRunView]:
    runs = await session.scalars(
        select(SourceRun)
        .options(selectinload(SourceRun.source))
        .order_by(SourceRun.started_at.desc())
        .limit(limit)
    )
    return [
        SourceRunView(
            id=run.id,
            source=run.source.slug,
            status=run.status.value,
            started_at=run.started_at,
            finished_at=run.finished_at,
            error=run.error,
            stats=run.stats or {},
        )
        for run in runs
    ]


async def _latest_run(
    session: AsyncSession,
    source_id: str,
    status: SourceRunStatus | None = None,
    exclude_running: bool = False,
) -> SourceRun | None:
    statement = select(SourceRun).where(SourceRun.source_id == source_id)
    if status is not None:
        statement = statement.where(SourceRun.status == status)
    if exclude_running:
        statement = statement.where(SourceRun.status != SourceRunStatus.RUNNING)
    return await session.scalar(statement.order_by(SourceRun.started_at.desc()).limit(1))


def _finished(run: SourceRun | None) -> datetime | None:
    if run is None:
        return None
    return run.finished_at or run.started_at


def _is_stale(run: SourceRun, poll_interval: timedelta, now: datetime) -> bool:
    finished = _finished(run)
    return finished is None or now - finished > 2 * poll_interval + STALE_GRACE

"""The single background worker: polls due sources and expires stale opportunities.

    python -m tr3ndly.worker                       # run forever
    python -m tr3ndly.worker --once                # run every enabled source now, then exit
    python -m tr3ndly.worker --once --source open-meteo

Run exactly one worker per database. Overlapping runs of a source are skipped, and runs left
RUNNING by a crashed worker are marked failed after RUN_TIMEOUT.
"""

import argparse
import asyncio
from datetime import datetime, timedelta

import httpx
import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tr3ndly import __version__
from tr3ndly.config import Settings, get_settings
from tr3ndly.db.models import SourceConfig, SourceRun, SourceRunStatus
from tr3ndly.db.session import dispose_engine, get_session_factory
from tr3ndly.db.types import utcnow
from tr3ndly.log import configure_logging
from tr3ndly.pipeline import RunResult, ensure_source_config, expire_stale, run_source
from tr3ndly.sources import SourceAdapter, build_adapters

logger = structlog.get_logger()

RUN_TIMEOUT = timedelta(minutes=30)
# After a failure, retry sooner than the normal poll interval.
FAILURE_RETRY = timedelta(minutes=15)


def http_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=settings.source_timeout_seconds,
        headers={"User-Agent": f"Tr3ndly/{__version__}"},
    )


async def sync_sources(
    sessions: async_sessionmaker[AsyncSession],
    adapters: dict[str, SourceAdapter],
    settings: Settings,
) -> None:
    """Record every known source and whether it is enabled, so health reflects config."""
    async with sessions() as session:
        for slug, adapter in adapters.items():
            await ensure_source_config(
                session, adapter.definition, enabled=slug in settings.enabled_sources
            )
        await session.commit()


async def fail_abandoned_runs(sessions: async_sessionmaker[AsyncSession], now: datetime) -> int:
    async with sessions() as session:
        result = await session.execute(
            update(SourceRun)
            .where(
                SourceRun.status == SourceRunStatus.RUNNING,
                SourceRun.started_at < now - RUN_TIMEOUT,
            )
            .values(
                status=SourceRunStatus.FAILED,
                finished_at=now,
                error="Worker stopped before the run finished",
            )
        )
        await session.commit()
        return result.rowcount or 0  # type: ignore[attr-defined]


async def is_due(
    sessions: async_sessionmaker[AsyncSession], adapter: SourceAdapter, now: datetime
) -> bool:
    async with sessions() as session:
        last = await session.scalar(
            select(SourceRun)
            .join(SourceConfig)
            .where(SourceConfig.slug == adapter.definition.slug)
            .order_by(SourceRun.started_at.desc())
            .limit(1)
        )
    if last is None:
        return True
    if last.status == SourceRunStatus.RUNNING:
        return False
    wait = adapter.definition.poll_interval
    if last.status == SourceRunStatus.FAILED:
        wait = min(wait, FAILURE_RETRY)
    return now - last.started_at >= wait


async def tick(
    sessions: async_sessionmaker[AsyncSession],
    adapters: dict[str, SourceAdapter],
    settings: Settings,
    client: httpx.AsyncClient,
    *,
    force: bool = False,
    only: str | None = None,
) -> list[RunResult]:
    now = utcnow()
    await fail_abandoned_runs(sessions, now)
    async with sessions() as session:
        expired_events, expired_opportunities = await expire_stale(session, now)
    if expired_events or expired_opportunities:
        logger.info("expired", events=expired_events, opportunities=expired_opportunities)

    results: list[RunResult] = []
    for slug in settings.enabled_sources:
        if only and slug != only:
            continue
        adapter = adapters.get(slug)
        if adapter is None:
            logger.warning("unknown_source", source=slug)
            continue
        if force or await is_due(sessions, adapter, now):
            results.append(
                await run_source(
                    sessions, adapter, client, min_timely_score=settings.min_timely_score
                )
            )
    return results


async def main(once: bool, only: str | None) -> int:
    settings = get_settings()
    configure_logging(settings.log_level)
    sessions = get_session_factory()
    adapters = build_adapters(settings)
    if only and only not in settings.enabled_sources:
        logger.error("source_not_enabled", source=only, enabled=settings.enabled_sources)
        return 2

    try:
        await sync_sources(sessions, adapters, settings)
        async with http_client(settings) as client:
            if once:
                results = await tick(sessions, adapters, settings, client, force=True, only=only)
                return 1 if any(r.status == SourceRunStatus.FAILED for r in results) else 0

            logger.info("worker_started", sources=settings.enabled_sources)
            while True:
                try:
                    await tick(sessions, adapters, settings, client)
                except Exception:  # noqa: BLE001 - one bad tick must not stop the worker
                    logger.exception("worker_tick_failed")
                await asyncio.sleep(settings.worker_tick_seconds)
    finally:
        await dispose_engine()


def cli() -> None:
    parser = argparse.ArgumentParser(description="Tr3ndly background worker")
    parser.add_argument("--once", action="store_true", help="run enabled sources now and exit")
    parser.add_argument("--source", help="limit --once to one source slug")
    args = parser.parse_args()
    try:
        raise SystemExit(asyncio.run(main(args.once, args.source)))
    except KeyboardInterrupt:
        logger.info("worker_stopped")


if __name__ == "__main__":
    cli()

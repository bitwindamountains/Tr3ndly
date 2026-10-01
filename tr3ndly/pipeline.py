"""Evidence-to-opportunity pipeline for one source run.

fetch → normalize → exact dedupe → detect events → eligibility gate → needs → concepts → score

Every run is recorded in source_runs with its stats or error. The pipeline never changes an
operator decision; it only creates eligible opportunities, adds evidence and score snapshots,
and retires events the source no longer reports.
"""

from dataclasses import asdict, dataclass
from datetime import datetime

import httpx
import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from tr3ndly.db.models import (
    EventCluster,
    EventClusterMember,
    EventStatus,
    Opportunity,
    OpportunityEvidence,
    OpportunityReason,
    OpportunityStatus,
    RawSignal,
    ScoreSnapshot,
    Sensitivity,
    SourceConfig,
    SourceRun,
    SourceRunStatus,
)
from tr3ndly.db.types import utcnow
from tr3ndly.intelligence import DETECTORS, DetectedEvent
from tr3ndly.intelligence.catalog import CATALOG_VERSION, NEED_LABELS, ProductConcept, concepts_for
from tr3ndly.intelligence.scoring import (
    SCORE_VERSION,
    SENSITIVITY_PENALTY,
    TimelyDimensions,
    demand_score,
    discovery_priority,
    uncertainty_penalty,
)
from tr3ndly.sources.base import NormalizedSignal, SourceAdapter, SourceDefinition

logger = structlog.get_logger()

# Statuses the pipeline may move to EXPIRED. Rejected and matched opportunities are left alone.
OPEN_STATUSES = (OpportunityStatus.ELIGIBLE, OpportunityStatus.DEFERRED, OpportunityStatus.ACCEPTED)
# Philippine locations only, for now.
GEOGRAPHY_SCORE = 100


@dataclass
class RunStats:
    fetched: int = 0
    new_signals: int = 0
    duplicate_signals: int = 0
    events_detected: int = 0
    events_below_threshold: int = 0
    events_created: int = 0
    events_updated: int = 0
    events_retired: int = 0
    opportunities_created: int = 0
    opportunities_rescored: int = 0


@dataclass(frozen=True)
class RunResult:
    run_id: str
    status: SourceRunStatus
    stats: RunStats
    error: str | None = None


async def ensure_source_config(
    session: AsyncSession, definition: SourceDefinition, enabled: bool
) -> SourceConfig:
    source = await session.scalar(select(SourceConfig).where(SourceConfig.slug == definition.slug))
    if source is None:
        source = SourceConfig(slug=definition.slug)
        session.add(source)
    source.display_name = definition.display_name
    source.access_method = definition.access_method
    source.terms_url = definition.terms_url
    source.enabled = enabled
    await session.flush()
    return source


async def run_source(
    sessions: async_sessionmaker[AsyncSession],
    adapter: SourceAdapter,
    client: httpx.AsyncClient,
    *,
    min_timely_score: int,
    now: datetime | None = None,
) -> RunResult:
    definition = adapter.definition
    async with sessions() as session:
        source = await ensure_source_config(session, definition, enabled=True)
        run = SourceRun(source_id=source.id, status=SourceRunStatus.RUNNING, started_at=utcnow())
        session.add(run)
        await session.commit()
        source_id, run_id = source.id, run.id

    stats = RunStats()
    log = logger.bind(source=definition.slug, run_id=run_id)
    try:
        items = await adapter.fetch(client)
        now = now or utcnow()
        signals = [signal for item in items for signal in adapter.normalize(item, now)]
        stats.fetched = len(signals)

        async with sessions() as session:
            stored = await _store_signals(session, source_id, run_id, signals, stats)
            detector = DETECTORS[definition.slug]
            events = detector(signals, now)
            stats.events_detected = len(events)
            kept_keys: set[str] = set()
            for event in events:
                if (
                    event.sensitivity == Sensitivity.BLOCKED
                    or _timely_dimensions(event, definition).score() < min_timely_score
                ):
                    stats.events_below_threshold += 1
                    continue
                kept_keys.add(event.dedupe_key)
                await _upsert_event(session, source_id, definition, event, stored, now, stats)
            await _retire_missing_events(session, source_id, kept_keys, now, stats)
            await session.commit()

        await _finish_run(sessions, run_id, SourceRunStatus.SUCCEEDED, stats)
        log.info("source_run_succeeded", **asdict(stats))
        return RunResult(run_id, SourceRunStatus.SUCCEEDED, stats)
    except Exception as error:  # noqa: BLE001 - every failure must be recorded on the run
        message = f"{type(error).__name__}: {error}"[:2000]
        await _finish_run(sessions, run_id, SourceRunStatus.FAILED, stats, message)
        log.error("source_run_failed", error=message)
        return RunResult(run_id, SourceRunStatus.FAILED, stats, message)


async def expire_stale(session: AsyncSession, now: datetime | None = None) -> tuple[int, int]:
    """Expire events and open opportunities whose window has passed."""
    now = now or utcnow()
    events = await session.execute(
        update(EventCluster)
        .where(EventCluster.status == EventStatus.ACTIVE, EventCluster.expires_at <= now)
        .values(status=EventStatus.EXPIRED)
    )
    opportunities = await session.execute(
        update(Opportunity)
        .where(Opportunity.status.in_(OPEN_STATUSES), Opportunity.expires_at <= now)
        .values(status=OpportunityStatus.EXPIRED)
    )
    await session.commit()
    return events.rowcount or 0, opportunities.rowcount or 0  # type: ignore[attr-defined]


async def _finish_run(
    sessions: async_sessionmaker[AsyncSession],
    run_id: str,
    status: SourceRunStatus,
    stats: RunStats,
    error: str | None = None,
) -> None:
    async with sessions() as session:
        run = await session.get(SourceRun, run_id)
        if run is None:
            return
        run.status = status
        run.finished_at = utcnow()
        run.stats = asdict(stats)
        run.error = error
        await session.commit()


async def _store_signals(
    session: AsyncSession,
    source_id: str,
    run_id: str,
    signals: list[NormalizedSignal],
    stats: RunStats,
) -> dict[str, RawSignal]:
    """Insert unseen signals; return the stored row for every fetched external id."""
    hashes = {signal.content_hash for signal in signals}
    existing = {
        row.content_hash: row
        for row in await session.scalars(
            select(RawSignal).where(
                RawSignal.source_id == source_id, RawSignal.content_hash.in_(hashes)
            )
        )
    }
    stored: dict[str, RawSignal] = {}
    for signal in signals:
        row = existing.get(signal.content_hash)
        if row is None:
            row = RawSignal(
                source_id=source_id,
                source_run_id=run_id,
                external_id=signal.external_id,
                canonical_url=signal.canonical_url,
                title=signal.title,
                permitted_summary=signal.summary,
                content_hash=signal.content_hash,
                observed_at=signal.observed_at,
                raw_payload=signal.facts,
            )
            session.add(row)
            existing[signal.content_hash] = row
            stats.new_signals += 1
        else:
            stats.duplicate_signals += 1
        stored[signal.external_id] = row
    await session.flush()
    return stored


def _timely_dimensions(event: DetectedEvent, definition: SourceDefinition) -> TimelyDimensions:
    return TimelyDimensions(
        # Scored right after fetching. Stale data is surfaced through source health instead.
        freshness=100,
        geography=GEOGRAPHY_SCORE,
        reach=event.reach,
        need_strength=event.need_strength,
        actionability=event.actionability,
        source_confidence=definition.source_confidence,
        sensitivity_penalty=SENSITIVITY_PENALTY[event.sensitivity],
    )


async def _upsert_event(
    session: AsyncSession,
    source_id: str,
    definition: SourceDefinition,
    event: DetectedEvent,
    stored: dict[str, RawSignal],
    now: datetime,
    stats: RunStats,
) -> None:
    dimensions = _timely_dimensions(event, definition)
    timely = dimensions.score()
    cluster = await session.scalar(
        select(EventCluster)
        .where(
            EventCluster.dedupe_key == event.dedupe_key, EventCluster.status == EventStatus.ACTIVE
        )
        .options(selectinload(EventCluster.members))
    )
    if cluster is None:
        cluster = EventCluster(
            source_id=source_id,
            dedupe_key=event.dedupe_key,
            status=EventStatus.ACTIVE,
            first_seen_at=now,
            members=[],
        )
        session.add(cluster)
        stats.events_created += 1
    else:
        stats.events_updated += 1
    cluster.event_type = event.event_type
    cluster.location = event.location
    cluster.title = event.title
    cluster.summary = event.summary
    cluster.consumer_needs = list(event.consumer_needs)
    cluster.sensitivity = event.sensitivity
    cluster.confidence = max(0, definition.source_confidence - 5 * event.lead_days)
    cluster.timely_score = timely
    cluster.rule_version = event.rule_version
    cluster.starts_at = event.starts_at
    cluster.expires_at = event.expires_at
    cluster.last_seen_at = now

    signal_rows = [stored[key] for key in event.signal_external_ids if key in stored]
    linked = {member.raw_signal_id for member in cluster.members}
    for row in signal_rows:
        if row.id not in linked:
            cluster.members.append(EventClusterMember(raw_signal_id=row.id))
    await session.flush()

    for concept in concepts_for(event.consumer_needs):
        await _upsert_opportunity(
            session, cluster, definition, event, concept, dimensions, signal_rows, stats
        )


async def _upsert_opportunity(
    session: AsyncSession,
    cluster: EventCluster,
    definition: SourceDefinition,
    event: DetectedEvent,
    concept: ProductConcept,
    dimensions: TimelyDimensions,
    signal_rows: list[RawSignal],
    stats: RunStats,
) -> None:
    opportunity = await session.scalar(
        select(Opportunity)
        .where(Opportunity.event_cluster_id == cluster.id, Opportunity.concept_key == concept.key)
        .options(selectinload(Opportunity.evidence), selectinload(Opportunity.scores))
    )
    if opportunity is None:
        opportunity = Opportunity(
            event_cluster_id=cluster.id,
            concept_key=concept.key,
            reason_type=OpportunityReason.TIMELY,
            status=OpportunityStatus.ELIGIBLE,
            is_demo=False,
            evidence=[],
            scores=[],
        )
        session.add(opportunity)
        stats.opportunities_created += 1

    need = NEED_LABELS.get(concept.need, concept.need)
    opportunity.product_concept = concept.name
    opportunity.category = concept.category
    opportunity.target_user = concept.target_user
    opportunity.location = event.location
    opportunity.why_now = f"{event.summary} This concept addresses {need}."
    opportunity.expires_at = event.expires_at
    opportunity.search_queries = list(concept.search_queries)
    opportunity.uncertainties = [
        "No affiliate listing has been matched yet.",
        *event.uncertainties,
        "Avoid these claims unless the listing supports them: "
        + "; ".join(concept.claims_to_avoid)
        + ".",
    ]

    seen = {item.raw_signal_id for item in opportunity.evidence}
    for row in signal_rows:
        if row.id not in seen:
            opportunity.evidence.append(
                OpportunityEvidence(
                    raw_signal_id=row.id,
                    source_name=definition.display_name,
                    source_url=_attribution_url(definition),
                    observed_at=row.observed_at,
                    summary=f"{row.title}. {row.permitted_summary or ''}".strip(),
                )
            )

    timely = dimensions.score()
    demand = demand_score(timely, None)
    uncertainty = uncertainty_penalty(event.lead_days, event.sensitivity)
    snapshot = ScoreSnapshot(
        demand=demand,
        execution=concept.execution,
        marketplace_fit_prior=concept.marketplace_fit_prior,
        uncertainty_penalty=uncertainty,
        discovery_priority=discovery_priority(
            demand, concept.execution, concept.marketplace_fit_prior, uncertainty
        ),
        timely_score=timely,
        trend_score=None,
        components={
            "timely": dimensions.as_dict(),
            "lead_days": event.lead_days,
            "sensitivity": event.sensitivity.value,
            "rule_version": event.rule_version,
            "catalog_version": CATALOG_VERSION,
        },
        version=SCORE_VERSION,
    )
    latest = max(opportunity.scores, key=lambda item: item.created_at, default=None)
    if latest is None or _score_key(latest) != _score_key(snapshot):
        opportunity.scores.append(snapshot)
        if latest is not None:
            stats.opportunities_rescored += 1
    await session.flush()


def _score_key(snapshot: ScoreSnapshot) -> tuple[object, ...]:
    return (
        snapshot.version,
        snapshot.demand,
        snapshot.execution,
        snapshot.marketplace_fit_prior,
        snapshot.uncertainty_penalty,
        snapshot.discovery_priority,
        snapshot.timely_score,
        snapshot.trend_score,
    )


def _attribution_url(definition: SourceDefinition) -> str | None:
    if definition.terms_url and definition.terms_url.startswith("https://open-meteo.com"):
        return "https://open-meteo.com/"
    return definition.terms_url


async def _retire_missing_events(
    session: AsyncSession,
    source_id: str,
    kept_keys: set[str],
    now: datetime,
    stats: RunStats,
) -> None:
    """The latest forecast is the truth: events it no longer supports end now."""
    statement = select(EventCluster).where(
        EventCluster.source_id == source_id, EventCluster.status == EventStatus.ACTIVE
    )
    if kept_keys:
        statement = statement.where(EventCluster.dedupe_key.not_in(kept_keys))
    stale = list(await session.scalars(statement))
    for cluster in stale:
        cluster.status = EventStatus.EXPIRED
        cluster.expires_at = min(cluster.expires_at, now)
        stats.events_retired += 1
    if stale:
        await session.execute(
            update(Opportunity)
            .where(
                Opportunity.event_cluster_id.in_([cluster.id for cluster in stale]),
                Opportunity.status.in_(OPEN_STATUSES),
            )
            .values(status=OpportunityStatus.EXPIRED, expires_at=now)
        )

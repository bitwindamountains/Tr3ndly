from datetime import timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.conftest import FIXTURE_NOW, mock_client
from tr3ndly.db.models import (
    DecisionEvent,
    DecisionType,
    EventCluster,
    EventStatus,
    Opportunity,
    OpportunityStatus,
    RawSignal,
    ScoreSnapshot,
    SourceRun,
    SourceRunStatus,
)
from tr3ndly.opportunities.listings import add_product_match, confirm_product_match
from tr3ndly.pipeline import expire_stale, run_source
from tr3ndly.schemas import ProductMatchCreate
from tr3ndly.sources.open_meteo import OpenMeteoAdapter

Sessions = async_sessionmaker[AsyncSession]


async def run(sessions: Sessions, forecast: Any, now=FIXTURE_NOW, status_code: int = 200):
    async with mock_client(forecast, status_code) as client:
        return await run_source(sessions, OpenMeteoAdapter(), client, min_timely_score=70, now=now)


async def count(sessions: Sessions, model: type) -> int:
    async with sessions() as session:
        return await session.scalar(select(func.count()).select_from(model)) or 0


async def test_first_run_creates_events_and_scored_opportunities(
    sessions: Sessions, forecast: list[dict[str, Any]]
) -> None:
    result = await run(sessions, forecast)

    assert result.status == SourceRunStatus.SUCCEEDED
    assert result.stats.fetched == 9
    assert result.stats.new_signals == 9
    assert result.stats.events_created == 2
    # Heat: fan, cooling towel, bottle, UV umbrella. Rain: umbrella, shoe covers, 2 bags, rack.
    assert result.stats.opportunities_created == 9

    async with sessions() as session:
        fan = await session.scalar(
            select(Opportunity).where(Opportunity.concept_key == "portable-rechargeable-fan")
        )
        assert fan is not None
        assert fan.status == OpportunityStatus.ELIGIBLE
        assert fan.location == "Metro Manila"
        assert fan.uncertainties[0] == "No affiliate listing has been matched yet."
        snapshot = await session.scalar(
            select(ScoreSnapshot).where(ScoreSnapshot.opportunity_id == fan.id)
        )
        assert snapshot is not None
        assert snapshot.version == "discovery-v2"
        assert snapshot.timely_score is not None
        assert snapshot.components["rule_version"] == "weather-rules-v1"


async def test_rerunning_the_same_forecast_is_idempotent(
    sessions: Sessions, forecast: list[dict[str, Any]]
) -> None:
    await run(sessions, forecast)
    again = await run(sessions, forecast, now=FIXTURE_NOW + timedelta(hours=3))

    assert again.stats.new_signals == 0
    assert again.stats.duplicate_signals == 9
    assert again.stats.events_created == 0
    assert again.stats.events_updated == 2
    assert again.stats.opportunities_created == 0
    assert again.stats.opportunities_rescored == 0
    assert await count(sessions, RawSignal) == 9
    assert await count(sessions, ScoreSnapshot) == 9


async def test_revised_forecast_rescores_without_touching_decisions(
    sessions: Sessions, forecast: list[dict[str, Any]]
) -> None:
    await run(sessions, forecast)
    async with sessions() as session:
        fan = await session.scalar(
            select(Opportunity).where(Opportunity.concept_key == "portable-rechargeable-fan")
        )
        assert fan is not None
        fan.status = OpportunityStatus.ACCEPTED
        session.add(
            DecisionEvent(
                opportunity_id=fan.id,
                decision=DecisionType.ACCEPTED,
                reason_code="useful_opportunity",
                score_version="discovery-v2",
            )
        )
        await session.commit()
        fan_id = fan.id

    forecast[0]["daily"]["apparent_temperature_max"][1] = 42.5
    revised = await run(sessions, forecast, now=FIXTURE_NOW + timedelta(hours=3))

    assert revised.stats.new_signals == 1
    assert revised.stats.opportunities_rescored == 4
    async with sessions() as session:
        fan = await session.get(Opportunity, fan_id)
        assert fan is not None
        assert fan.status == OpportunityStatus.ACCEPTED
        snapshots = await session.scalar(
            select(func.count())
            .select_from(ScoreSnapshot)
            .where(ScoreSnapshot.opportunity_id == fan_id)
        )
        assert snapshots == 2


async def test_events_the_forecast_drops_are_retired(
    sessions: Sessions, forecast: list[dict[str, Any]]
) -> None:
    await run(sessions, forecast)
    forecast[1]["daily"]["precipitation_sum"] = [2.0, 3.0, 4.0]
    later = FIXTURE_NOW + timedelta(hours=3)
    result = await run(sessions, forecast, now=later)

    assert result.stats.events_retired == 1
    async with sessions() as session:
        rain = await session.scalar(
            select(EventCluster).where(EventCluster.event_type == "HEAVY_RAIN")
        )
        assert rain is not None
        assert rain.status == EventStatus.EXPIRED
        statuses = set(
            await session.scalars(
                select(Opportunity.status).where(Opportunity.event_cluster_id == rain.id)
            )
        )
        assert statuses == {OpportunityStatus.EXPIRED}


async def test_events_below_threshold_create_nothing(
    sessions: Sessions, forecast: list[dict[str, Any]]
) -> None:
    async with mock_client(forecast) as client:
        result = await run_source(
            sessions, OpenMeteoAdapter(), client, min_timely_score=99, now=FIXTURE_NOW
        )

    assert result.stats.events_detected == 2
    assert result.stats.events_below_threshold == 2
    assert await count(sessions, Opportunity) == 0


async def test_failed_fetch_is_recorded_on_the_run(sessions: Sessions) -> None:
    result = await run(sessions, {"error": True}, status_code=400)

    assert result.status == SourceRunStatus.FAILED
    assert result.error is not None and "HTTPStatusError" in result.error
    async with sessions() as session:
        stored = await session.get(SourceRun, result.run_id)
        assert stored is not None
        assert stored.status == SourceRunStatus.FAILED
        assert stored.finished_at is not None


async def test_expire_stale_closes_open_opportunities_only(
    sessions: Sessions, forecast: list[dict[str, Any]]
) -> None:
    await run(sessions, forecast)
    async with sessions() as session:
        rejected = await session.scalar(
            select(Opportunity).where(Opportunity.concept_key == "cooling-towel")
        )
        assert rejected is not None
        rejected.status = OpportunityStatus.REJECTED
        await session.commit()

        events, opportunities = await expire_stale(session, FIXTURE_NOW + timedelta(days=5))

    assert events == 2
    assert opportunities == 8
    async with sessions() as session:
        towel = await session.scalar(
            select(Opportunity).where(Opportunity.concept_key == "cooling-towel")
        )
        assert towel is not None and towel.status == OpportunityStatus.REJECTED


async def test_gate_drops_marginal_events_far_ahead_in_smaller_cities(
    sessions: Sessions, forecast: list[dict[str, Any]]
) -> None:
    # Cebu: barely-qualifying rain two days out. Manila keeps its strong same-day heat.
    forecast[1]["daily"]["precipitation_sum"] = [8.0, 5.0, 21.0]
    result = await run(sessions, forecast)

    assert result.stats.events_detected == 2
    assert result.stats.events_below_threshold == 1
    assert result.stats.events_created == 1
    async with sessions() as session:
        types = set(await session.scalars(select(EventCluster.event_type)))
    assert types == {"HEAT"}


async def test_retirement_keeps_decisions_and_a_returning_event_reuses_them(
    sessions: Sessions, forecast: list[dict[str, Any]]
) -> None:
    await run(sessions, forecast)
    async with sessions() as session:
        decided: dict[str, str] = {}
        for key, status in (
            ("compact-umbrella", OpportunityStatus.ACCEPTED),
            ("waterproof-shoe-covers", OpportunityStatus.REJECTED),
        ):
            opportunity = await session.scalar(
                select(Opportunity).where(Opportunity.concept_key == key)
            )
            assert opportunity is not None
            opportunity.status = status
            decided[key] = opportunity.id
        await session.commit()

    rain = forecast[1]["daily"]["precipitation_sum"]
    forecast[1]["daily"]["precipitation_sum"] = [2.0, 3.0, 4.0]
    dropped = await run(sessions, forecast, now=FIXTURE_NOW + timedelta(hours=3))
    assert dropped.stats.events_retired == 1
    async with sessions() as session:
        umbrella = await session.get(Opportunity, decided["compact-umbrella"])
        covers = await session.get(Opportunity, decided["waterproof-shoe-covers"])
        assert umbrella is not None and umbrella.status == OpportunityStatus.ACCEPTED
        assert umbrella.expires_at > FIXTURE_NOW + timedelta(hours=3)
        assert covers is not None and covers.status == OpportunityStatus.REJECTED
        bag = await session.scalar(
            select(Opportunity).where(Opportunity.concept_key == "waterproof-dry-bag")
        )
        assert bag is not None and bag.status == OpportunityStatus.EXPIRED

    forecast[1]["daily"]["precipitation_sum"] = rain
    returned = await run(sessions, forecast, now=FIXTURE_NOW + timedelta(hours=6))

    assert returned.stats.events_created == 1
    # Five rain concepts; the accepted and rejected ones are reused, not duplicated.
    assert returned.stats.opportunities_created == 3
    async with sessions() as session:
        active = await session.scalar(
            select(EventCluster).where(
                EventCluster.event_type == "HEAVY_RAIN", EventCluster.status == EventStatus.ACTIVE
            )
        )
        assert active is not None
        for key, status in (
            ("compact-umbrella", OpportunityStatus.ACCEPTED),
            ("waterproof-shoe-covers", OpportunityStatus.REJECTED),
        ):
            rows = list(
                await session.scalars(select(Opportunity).where(Opportunity.concept_key == key))
            )
            assert len(rows) == 1
            assert rows[0].id == decided[key]
            assert rows[0].status == status
            assert rows[0].event_cluster_id == active.id


async def test_a_matched_opportunity_keeps_its_publish_score_across_runs(
    sessions: Sessions, forecast: list[dict[str, Any]]
) -> None:
    await run(sessions, forecast)
    async with sessions() as session:
        fan = await session.scalar(
            select(Opportunity).where(Opportunity.concept_key == "portable-rechargeable-fan")
        )
        assert fan is not None
        fan.status = OpportunityStatus.ACCEPTED
        await session.commit()
        match = await add_product_match(
            session,
            fan.id,
            ProductMatchCreate(
                marketplace="shopee",
                product_url="https://shopee.ph/p/1",
                affiliate_url="https://s.shopee.ph/x",
                listing_title="Handheld fan",
                price_php=Decimal("349"),
                commission_rate_pct=Decimal("8"),
                verified_facts=["USB-C charging"],
            ),
            now=FIXTURE_NOW,
        )
        await confirm_product_match(session, match.id, now=FIXTURE_NOW)
        fan_id = fan.id

    again = await run(sessions, forecast, now=FIXTURE_NOW + timedelta(hours=3))

    assert again.stats.opportunities_rescored == 0
    async with sessions() as session:
        versions = list(
            await session.scalars(
                select(ScoreSnapshot.version)
                .where(ScoreSnapshot.opportunity_id == fan_id)
                .order_by(ScoreSnapshot.created_at)
            )
        )
        fan = await session.get(Opportunity, fan_id)
    assert versions == ["discovery-v2", "publish-v1"]
    assert fan is not None and fan.status == OpportunityStatus.MATCHED

from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.conftest import mock_client
from tr3ndly.db.models import EventCluster, Opportunity
from tr3ndly.intelligence.calendar_rules import detect_calendar_events
from tr3ndly.intelligence.events import DetectedEvent
from tr3ndly.pipeline import run_source
from tr3ndly.sources.ph_calendar import PhCalendarAdapter, occasions_between

# 08:00 in Manila on Oct 8, 2026: 10.10 is two days away, payday (Oct 15) is a week away.
OCT_8 = datetime(2026, 10, 8, 0, 0, tzinfo=UTC)


def events_at(now: datetime) -> dict[str, DetectedEvent]:
    signals = PhCalendarAdapter().normalize(None, now)
    return {event.dedupe_key: event for event in detect_calendar_events(signals, now)}


def test_occasion_dates_follow_the_calendar() -> None:
    found = {
        (kind, ends)
        for kind, _, _, ends, _ in occasions_between(date(2026, 1, 1), date(2026, 12, 31))
    }

    assert ("mothers_day", date(2026, 5, 10)) in found  # second Sunday of May
    assert ("fathers_day", date(2026, 6, 21)) in found  # third Sunday of June
    assert ("payday", date(2026, 2, 28)) in found  # the 30th falls back to month end
    assert ("payday", date(2026, 1, 30)) in found
    assert ("double_day", date(2026, 11, 11)) in found
    assert ("christmas", date(2026, 12, 24)) in found


def test_events_surface_inside_their_lead_window_only() -> None:
    events = events_at(OCT_8)

    assert set(events) == {"calendar:double_day:2026-10-10"}
    sale = events["calendar:double_day:2026-10-10"]
    assert sale.title == "10.10 sale is in 2 days"
    assert sale.lead_days == 2
    assert sale.freshness == 100
    assert sale.need_strength == 90  # a major year-end sale
    assert sale.consumer_needs == ("sale_day_upgrades",)

    # Payday surfaces three days ahead.
    assert "calendar:payday:2026-10-15" in events_at(datetime(2026, 10, 12, tzinfo=UTC))


def test_a_season_stays_open_until_its_last_day() -> None:
    events = events_at(datetime(2026, 12, 20, tzinfo=UTC))

    christmas = events["calendar:christmas:2026-12-24"]
    assert christmas.lead_days == 0
    assert christmas.title == "Christmas gift season runs until Dec 24"


async def test_calendar_run_creates_nationwide_opportunities(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with mock_client({}) as client:
        result = await run_source(
            sessions, PhCalendarAdapter(), client, min_timely_score=70, now=OCT_8
        )

    assert result.stats.events_created == 1
    assert result.stats.events_below_threshold == 0
    assert result.stats.opportunities_created == 3  # air fryer, earbuds, robot vacuum
    async with sessions() as session:
        cluster = await session.scalar(select(EventCluster))
        assert cluster is not None and cluster.location == "Philippines"
        keys = set(await session.scalars(select(Opportunity.concept_key)))
    assert keys == {"air-fryer", "wireless-earbuds", "robot-vacuum"}

"""Philippine commerce calendar: sale days, paydays, and gifting and school seasons.

A computed source. Nothing is downloaded, so `fetch` returns one placeholder and `normalize`
lists the occasions ahead of the run date. Which occasions become events, and when, is decided
by `tr3ndly.intelligence.calendar_rules`.
"""

import calendar
from datetime import date, datetime, timedelta
from typing import Any

import httpx

from tr3ndly.geo import MANILA
from tr3ndly.sources.base import NormalizedSignal, SourceDefinition

# Far enough ahead to cover the longest lead window in the calendar rules.
HORIZON_DAYS = 45
NATIONWIDE = "Philippines"

DEFINITION = SourceDefinition(
    slug="ph-calendar",
    display_name="PH commerce calendar",
    access_method="computed",
    terms_url=None,
    attribution="Dates computed by Tr3ndly",
    attribution_url=None,
    poll_interval=timedelta(hours=12),
    # Dates are certain; whether a marketplace runs a campaign that day is not.
    source_confidence=90,
)


class PhCalendarAdapter:
    definition = DEFINITION

    async def fetch(self, client: httpx.AsyncClient) -> list[None]:
        return [None]

    def normalize(self, item: Any, fetched_at: datetime) -> list[NormalizedSignal]:
        today = fetched_at.astimezone(MANILA).date()
        signals: list[NormalizedSignal] = []
        for kind, label, starts, ends, extra in occasions_between(
            today, today + timedelta(days=HORIZON_DAYS)
        ):
            signals.append(
                NormalizedSignal(
                    external_id=f"{kind}:{ends}",
                    title=label,
                    summary=_describe(label, starts, ends),
                    # The date list is computed, so it is "observed" when the run happens.
                    observed_at=fetched_at,
                    facts={
                        "occasion": kind,
                        "label": label,
                        "location": NATIONWIDE,
                        "starts": str(starts),
                        "date": str(ends),
                        **extra,
                    },
                )
            )
        return signals


Occasion = tuple[str, str, date, date, dict[str, Any]]


def occasions_between(first: date, last: date) -> list[Occasion]:
    """Occasions whose last day falls in [first, last], including seasons already underway."""
    found: list[Occasion] = []
    for year in range(first.year, last.year + 1):
        for month in range(1, 13):
            double_day = date(year, month, month)
            found.append(
                (
                    "double_day",
                    f"{month}.{month} sale",
                    double_day,
                    double_day,
                    {"major": month >= 9},
                )
            )
            month_end = calendar.monthrange(year, month)[1]
            for day in (15, min(30, month_end)):
                payday = date(year, month, day)
                found.append(("payday", "Payday", payday, payday, {}))
        found.append(("valentines", "Valentine's Day", date(year, 2, 14), date(year, 2, 14), {}))
        mothers = _nth_weekday(year, 5, calendar.SUNDAY, 2)
        found.append(("mothers_day", "Mother's Day", mothers, mothers, {}))
        fathers = _nth_weekday(year, 6, calendar.SUNDAY, 3)
        found.append(("fathers_day", "Father's Day", fathers, fathers, {}))
        # Public schools usually open in mid-June; DepEd sets the exact date each year.
        found.append(("back_to_school", "Back to school", date(year, 6, 1), date(year, 6, 16), {}))
        found.append(
            ("christmas", "Christmas gift season", date(year, 12, 1), date(year, 12, 24), {})
        )
    return sorted(
        (item for item in found if first <= item[3] <= last), key=lambda item: (item[3], item[0])
    )


def _nth_weekday(year: int, month: int, weekday: int, nth: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (nth - 1))


def _describe(label: str, starts: date, ends: date) -> str:
    if starts == ends:
        return f"{label} on {ends:%b} {ends.day}."
    return f"{label} from {starts:%b} {starts.day} to {ends:%b} {ends.day}."

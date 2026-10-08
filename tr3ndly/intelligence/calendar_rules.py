"""Deterministic calendar → event rules.

Each occasion surfaces a fixed number of days before it starts, so the operator can match a
listing and post ahead of the day, and closes at the end of its last day (Manila time).
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from tr3ndly.db.models import Sensitivity
from tr3ndly.geo import MANILA
from tr3ndly.intelligence.events import DetectedEvent
from tr3ndly.sources.base import NormalizedSignal

RULE_VERSION = "calendar-rules-v1"
NATIONWIDE_REACH = 100
# A certain date is worth preparing for, so freshness only starts to fall after two days out.
FRESHNESS_LOSS_PER_EXTRA_DAY = 5

SALE_CAVEAT = (
    "Check which marketplaces actually run a campaign and what the listing's price is that day; "
    "do not quote discounts or vouchers you have not seen."
)
GIFT_CAVEAT = "Use gift-idea framing only; make no claims about what the recipient needs."


@dataclass(frozen=True)
class _Rule:
    event_type: str
    needs: tuple[str, ...]
    need_strength: int
    actionability: int
    lead_window_days: int
    summary: str
    caveat: str


RULES: dict[str, _Rule] = {
    "double_day": _Rule(
        "SALE_DAY",
        ("sale_day_upgrades",),
        need_strength=70,
        actionability=80,
        lead_window_days=5,
        summary="Shoppers wait for double-day sales to buy bigger-ticket items.",
        caveat=SALE_CAVEAT,
    ),
    "payday": _Rule(
        "PAYDAY",
        ("sale_day_upgrades",),
        need_strength=65,
        actionability=75,
        lead_window_days=3,
        summary="Spending rises around the 15th and 30th, when many employees are paid.",
        caveat="Pay dates vary by employer; many are paid on the 15th and 30th. " + SALE_CAVEAT,
    ),
    "valentines": _Rule(
        "GIFTING",
        ("gift_giving",),
        need_strength=80,
        actionability=85,
        lead_window_days=13,
        summary="Shoppers look for gifts ahead of the day.",
        caveat=GIFT_CAVEAT,
    ),
    "mothers_day": _Rule(
        "GIFTING",
        ("gift_giving",),
        need_strength=80,
        actionability=85,
        lead_window_days=10,
        summary="Shoppers look for gifts ahead of the day.",
        caveat=GIFT_CAVEAT,
    ),
    "fathers_day": _Rule(
        "GIFTING",
        ("gift_giving",),
        need_strength=75,
        actionability=85,
        lead_window_days=10,
        summary="Shoppers look for gifts ahead of the day.",
        caveat=GIFT_CAVEAT,
    ),
    "christmas": _Rule(
        "GIFTING",
        ("gift_giving",),
        need_strength=90,
        actionability=85,
        lead_window_days=7,
        summary="The peak gift-buying season in the Philippines.",
        caveat=GIFT_CAVEAT,
    ),
    "back_to_school": _Rule(
        "BACK_TO_SCHOOL",
        ("school_supplies",),
        need_strength=85,
        actionability=85,
        lead_window_days=10,
        summary="Families buy school bags and supplies before classes open.",
        caveat="DepEd sets the school opening date each year; confirm it before posting.",
    ),
}
# The big year-end campaigns.
MAJOR_SALE_STRENGTH = 90


def detect_calendar_events(signals: list[NormalizedSignal], now: datetime) -> list[DetectedEvent]:
    today = now.astimezone(MANILA).date()
    events: list[DetectedEvent] = []
    for signal in signals:
        rule = RULES.get(signal.facts["occasion"])
        if rule is None:
            continue
        starts = date.fromisoformat(signal.facts["starts"])
        ends = date.fromisoformat(signal.facts["date"])
        if not starts - timedelta(days=rule.lead_window_days) <= today <= ends:
            continue
        lead_days = max(0, (starts - today).days)
        need_strength = rule.need_strength
        if signal.facts.get("major"):
            need_strength = MAJOR_SALE_STRENGTH
        label = signal.facts["label"]
        events.append(
            DetectedEvent(
                dedupe_key=f"calendar:{signal.facts['occasion']}:{ends}",
                event_type=rule.event_type,
                location=signal.facts["location"],
                title=f"{label} {_when(starts, ends, today)}",
                summary=f"{signal.summary} {rule.summary}",
                consumer_needs=rule.needs,
                sensitivity=Sensitivity.LOW,
                starts_at=datetime.combine(starts, time.min, MANILA),
                expires_at=datetime.combine(ends + timedelta(days=1), time.min, MANILA),
                freshness=max(0, 100 - FRESHNESS_LOSS_PER_EXTRA_DAY * max(0, lead_days - 2)),
                need_strength=need_strength,
                actionability=rule.actionability,
                reach=NATIONWIDE_REACH,
                lead_days=lead_days,
                signal_external_ids=(signal.external_id,),
                uncertainties=(rule.caveat,),
                rule_version=RULE_VERSION,
            )
        )
    return events


def _when(starts: date, ends: date, today: date) -> str:
    if starts <= today:
        return "is on now" if starts == ends else f"runs until {ends:%b} {ends.day}"
    days = (starts - today).days
    return "is tomorrow" if days == 1 else f"is in {days} days"

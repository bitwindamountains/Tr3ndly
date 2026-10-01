"""Deterministic weather → event rules.

These rules turn forecast facts into timely events and consumer needs without a model call.
Forecast-based events never claim hazards: anything that might be hazardous is raised to a
higher sensitivity and tells the operator to confirm with PAGASA.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

from tr3ndly.db.models import Sensitivity
from tr3ndly.geo import LOCATIONS_BY_NAME, MANILA
from tr3ndly.sources.base import NormalizedSignal

RULE_VERSION = "weather-rules-v1"

HEAT_FEELS_LIKE_C = 38.0
HEAT_DANGER_FEELS_LIKE_C = 42.0
RAIN_MM = 20.0
RAIN_MIN_PROBABILITY = 60.0
RAIN_HAZARD_MM = 50.0


@dataclass(frozen=True)
class DetectedEvent:
    dedupe_key: str
    event_type: str
    location: str
    title: str
    summary: str
    consumer_needs: tuple[str, ...]
    sensitivity: Sensitivity
    starts_at: datetime
    expires_at: datetime
    need_strength: int
    actionability: int
    reach: int
    lead_days: int
    signal_external_ids: tuple[str, ...]
    uncertainties: tuple[str, ...]
    rule_version: str = RULE_VERSION


@dataclass(frozen=True)
class _Rule:
    event_type: str
    needs: tuple[str, ...]
    actionability: int


HEAT = _Rule("HEAT", ("personal_cooling", "hydration", "sun_protection"), actionability=85)
HEAVY_RAIN = _Rule("HEAVY_RAIN", ("rain_protection", "dry_storage", "indoor_drying"), 80)


def detect_weather_events(signals: list[NormalizedSignal], now: datetime) -> list[DetectedEvent]:
    today = now.astimezone(MANILA).date()
    by_location: dict[str, list[NormalizedSignal]] = defaultdict(list)
    for signal in signals:
        by_location[signal.facts["location"]].append(signal)

    events: list[DetectedEvent] = []
    for location, location_signals in by_location.items():
        upcoming = [signal for signal in location_signals if _day(signal.facts) >= today]
        heat_days = [s for s in upcoming if _is_hot(s.facts)]
        rain_days = [s for s in upcoming if _is_rainy(s.facts)]
        if heat_days:
            events.append(_heat_event(location, heat_days, today))
        if rain_days:
            events.append(_rain_event(location, rain_days, today))
    return events


def _is_hot(facts: dict[str, Any]) -> bool:
    value = facts.get("apparent_temperature_max")
    return value is not None and value >= HEAT_FEELS_LIKE_C


def _is_rainy(facts: dict[str, Any]) -> bool:
    amount = facts.get("precipitation_sum")
    probability = facts.get("precipitation_probability_max")
    if amount is None or amount < RAIN_MM:
        return False
    return probability is None or probability >= RAIN_MIN_PROBABILITY


def _heat_event(location: str, days: list[NormalizedSignal], today: date) -> DetectedEvent:
    peak = max(s.facts["apparent_temperature_max"] for s in days)
    danger = peak >= HEAT_DANGER_FEELS_LIKE_C
    uncertainties = [_forecast_caveat(days, today)]
    if danger:
        uncertainties.append(
            "Danger-level heat index is forecast. Frame products as comfort only; "
            "make no health or safety claims."
        )
    return _event(
        HEAT,
        location,
        days,
        today,
        title=f"Hot conditions forecast in {location}",
        summary=(
            f"Feels-like highs of up to {peak:.0f}°C are forecast for {_span(days)}, "
            "a practical near-term need for personal cooling and hydration."
        ),
        need_strength=_scale(peak, HEAT_FEELS_LIKE_C, 44.0),
        sensitivity=Sensitivity.MEDIUM if danger else Sensitivity.LOW,
        uncertainties=uncertainties,
    )


def _rain_event(location: str, days: list[NormalizedSignal], today: date) -> DetectedEvent:
    peak = max(s.facts["precipitation_sum"] for s in days)
    hazard = peak >= RAIN_HAZARD_MM
    uncertainties = [_forecast_caveat(days, today)]
    if hazard:
        uncertainties.append(
            "Possibly hazardous rainfall. Confirm with PAGASA bulletins first, "
            "and do not use flood or disaster framing."
        )
    return _event(
        HEAVY_RAIN,
        location,
        days,
        today,
        title=f"Heavy rain forecast in {location}",
        summary=(
            f"Up to {peak:.0f} mm of rain in a day is forecast for {_span(days)}, "
            "a practical need for staying dry on commutes and drying laundry indoors."
        ),
        need_strength=_scale(peak, RAIN_MM, 60.0),
        sensitivity=Sensitivity.MEDIUM if hazard else Sensitivity.LOW,
        uncertainties=uncertainties,
    )


def _event(
    rule: _Rule,
    location: str,
    days: list[NormalizedSignal],
    today: date,
    *,
    title: str,
    summary: str,
    need_strength: int,
    sensitivity: Sensitivity,
    uncertainties: list[str],
) -> DetectedEvent:
    dates = sorted(_day(s.facts) for s in days)
    place = LOCATIONS_BY_NAME.get(location)
    slug = place.slug if place else location.lower().replace(" ", "-")
    return DetectedEvent(
        dedupe_key=f"weather:{rule.event_type}:{slug}",
        event_type=rule.event_type,
        location=location,
        title=title,
        summary=summary,
        consumer_needs=rule.needs,
        sensitivity=sensitivity,
        starts_at=datetime.combine(dates[0], time.min, MANILA),
        # The window closes at the end of the last qualifying day, Manila time.
        expires_at=datetime.combine(dates[-1] + timedelta(days=1), time.min, MANILA),
        need_strength=need_strength,
        actionability=rule.actionability,
        reach=place.reach if place else 50,
        lead_days=(dates[0] - today).days,
        signal_external_ids=tuple(s.external_id for s in days),
        uncertainties=tuple(uncertainties),
    )


def _day(facts: dict[str, Any]) -> date:
    return date.fromisoformat(facts["date"])


def _span(days: list[NormalizedSignal]) -> str:
    dates = sorted(_day(s.facts) for s in days)
    first, last = dates[0], dates[-1]
    if first == last:
        return f"{first:%b} {first.day}"
    return f"{first:%b} {first.day}–{last:%b} {last.day}"


def _forecast_caveat(days: list[NormalizedSignal], today: date) -> str:
    lead = min((_day(s.facts) - today).days for s in days)
    if lead <= 0:
        return "Based on today's forecast, not observed conditions."
    return f"Based on a forecast {lead} day{'s' if lead > 1 else ''} out; forecasts can change."


def _scale(value: float, start: float, full: float) -> int:
    """50 at the rule threshold, rising linearly to 100 at `full`."""
    ratio = (value - start) / (full - start)
    return int(round(max(50, min(100, 50 + 50 * ratio))))

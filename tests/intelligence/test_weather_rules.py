from datetime import UTC, datetime
from typing import Any

from tests.conftest import FIXTURE_NOW
from tr3ndly.db.models import Sensitivity
from tr3ndly.geo import PH_LOCATIONS
from tr3ndly.intelligence.weather_rules import detect_weather_events
from tr3ndly.sources.base import NormalizedSignal
from tr3ndly.sources.open_meteo import OpenMeteoAdapter


def signals_for(forecast: list[dict[str, Any]]) -> list[NormalizedSignal]:
    adapter = OpenMeteoAdapter()
    return [
        signal
        for item in zip(PH_LOCATIONS, forecast, strict=True)
        for signal in adapter.normalize(item, FIXTURE_NOW)
    ]


def test_detects_heat_and_rain_events_from_the_fixture(forecast: list[dict[str, Any]]) -> None:
    events = {
        event.dedupe_key: event
        for event in detect_weather_events(signals_for(forecast), FIXTURE_NOW)
    }

    assert set(events) == {"weather:HEAT:metro-manila", "weather:HEAVY_RAIN:cebu-city"}
    heat = events["weather:HEAT:metro-manila"]
    assert heat.signal_external_ids == ("metro-manila:2026-10-02", "metro-manila:2026-10-03")
    assert heat.consumer_needs == ("personal_cooling", "hydration", "sun_protection")
    assert heat.sensitivity == Sensitivity.LOW
    assert heat.lead_days == 0
    # Expires at midnight Manila after the last hot day (Oct 3), i.e. 16:00 UTC on Oct 3.
    assert heat.expires_at.astimezone(UTC) == datetime(2026, 10, 3, 16, 0, tzinfo=UTC)

    rain = events["weather:HEAVY_RAIN:cebu-city"]
    assert rain.lead_days == 1
    assert rain.sensitivity == Sensitivity.LOW
    assert "1 day out" in rain.uncertainties[0]


def test_danger_heat_and_hazardous_rain_raise_sensitivity(forecast: list[dict[str, Any]]) -> None:
    forecast[0]["daily"]["apparent_temperature_max"][0] = 43.0
    forecast[1]["daily"]["precipitation_sum"][1] = 75.0
    events = {
        event.event_type: event
        for event in detect_weather_events(signals_for(forecast), FIXTURE_NOW)
    }

    assert events["HEAT"].sensitivity == Sensitivity.MEDIUM
    assert any("no health or safety claims" in text for text in events["HEAT"].uncertainties)
    assert events["HEAVY_RAIN"].sensitivity == Sensitivity.MEDIUM
    assert any("PAGASA" in text for text in events["HEAVY_RAIN"].uncertainties)


def test_rain_needs_a_likely_probability(forecast: list[dict[str, Any]]) -> None:
    forecast[1]["daily"]["precipitation_probability_max"] = [55, 40, 40]
    events = detect_weather_events(signals_for(forecast), FIXTURE_NOW)

    assert all(event.event_type != "HEAVY_RAIN" for event in events)


def test_past_days_are_ignored(forecast: list[dict[str, Any]]) -> None:
    # Oct 4 in Manila: the two hot days are already in the past.
    later = datetime(2026, 10, 3, 17, 0, tzinfo=UTC)
    events = detect_weather_events(signals_for(forecast), later)

    assert all(event.event_type != "HEAT" for event in events)

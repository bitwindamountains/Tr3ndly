"""Turns normalized signals into events, needs, product concepts, and scores."""

from collections.abc import Callable
from datetime import datetime

from tr3ndly.intelligence.calendar_rules import detect_calendar_events
from tr3ndly.intelligence.events import DetectedEvent
from tr3ndly.intelligence.weather_rules import detect_weather_events
from tr3ndly.sources.base import NormalizedSignal

Detector = Callable[[list[NormalizedSignal], datetime], list[DetectedEvent]]

# Which detector interprets each source's signals. A future AI classifier plugs in here.
DETECTORS: dict[str, Detector] = {
    "open-meteo": detect_weather_events,
    "ph-calendar": detect_calendar_events,
}

__all__ = ["DETECTORS", "DetectedEvent", "Detector"]

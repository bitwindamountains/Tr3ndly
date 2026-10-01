"""Source adapters. Each one fetches and normalizes; nothing here persists or calls AI."""

from tr3ndly.config import Settings
from tr3ndly.sources.base import NormalizedSignal, SourceAdapter, SourceDefinition
from tr3ndly.sources.open_meteo import OpenMeteoAdapter


def build_adapters(settings: Settings) -> dict[str, SourceAdapter]:
    """Every known adapter, keyed by slug. Whether it runs depends on ENABLED_SOURCES."""
    adapters: list[SourceAdapter] = [OpenMeteoAdapter(api_key=settings.open_meteo_api_key)]
    return {adapter.definition.slug: adapter for adapter in adapters}


__all__ = [
    "NormalizedSignal",
    "OpenMeteoAdapter",
    "SourceAdapter",
    "SourceDefinition",
    "build_adapters",
]

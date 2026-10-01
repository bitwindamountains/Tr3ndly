from datetime import datetime, timedelta
from typing import Any

import httpx

from tr3ndly.geo import PH_LOCATIONS, MonitoredLocation
from tr3ndly.sources.base import NormalizedSignal, SourceDefinition, with_retries

FREE_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
COMMERCIAL_ENDPOINT = "https://customer-api.open-meteo.com/v1/forecast"
DAILY_FIELDS = (
    "apparent_temperature_max",
    "temperature_2m_max",
    "precipitation_sum",
    "precipitation_probability_max",
)

DEFINITION = SourceDefinition(
    slug="open-meteo",
    display_name="Open-Meteo forecast",
    access_method="official_api",
    terms_url="https://open-meteo.com/en/terms",
    attribution="Weather data by Open-Meteo.com (CC BY 4.0)",
    attribution_url="https://open-meteo.com/",
    poll_interval=timedelta(hours=3),
    # A forecast, not an official warning.
    source_confidence=70,
)

LocationForecast = tuple[MonitoredLocation, dict[str, Any]]


class OpenMeteoAdapter:
    definition = DEFINITION

    def __init__(
        self,
        api_key: str | None = None,
        locations: tuple[MonitoredLocation, ...] = PH_LOCATIONS,
        forecast_days: int = 3,
    ) -> None:
        self.api_key = api_key
        self.locations = locations
        self.forecast_days = forecast_days

    async def fetch(self, client: httpx.AsyncClient) -> list[LocationForecast]:
        params: dict[str, str | int] = {
            "latitude": ",".join(str(item.latitude) for item in self.locations),
            "longitude": ",".join(str(item.longitude) for item in self.locations),
            "daily": ",".join(DAILY_FIELDS),
            "timezone": "Asia/Manila",
            "forecast_days": self.forecast_days,
        }
        endpoint = FREE_ENDPOINT
        if self.api_key:
            endpoint = COMMERCIAL_ENDPOINT
            params["apikey"] = self.api_key

        async def request() -> Any:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()

        payload = await with_retries(request)
        # One coordinate returns an object; several return a list in request order.
        forecasts = payload if isinstance(payload, list) else [payload]
        if len(forecasts) != len(self.locations):
            raise ValueError(
                f"Open-Meteo returned {len(forecasts)} forecasts for {len(self.locations)} places"
            )
        return list(zip(self.locations, forecasts, strict=True))

    def normalize(self, item: LocationForecast, fetched_at: datetime) -> list[NormalizedSignal]:
        location, forecast = item
        daily = forecast.get("daily") or {}
        days: list[str] = daily.get("time") or []
        signals: list[NormalizedSignal] = []
        for index, day in enumerate(days):
            facts: dict[str, Any] = {"location": location.name, "date": day}
            for name in DAILY_FIELDS:
                values = daily.get(name) or []
                facts[name] = values[index] if index < len(values) else None
            if facts["apparent_temperature_max"] is None and facts["precipitation_sum"] is None:
                continue
            signals.append(
                NormalizedSignal(
                    external_id=f"{location.slug}:{day}",
                    title=f"{location.name} forecast for {day}",
                    summary=_describe(facts),
                    observed_at=fetched_at,
                    facts=facts,
                )
            )
        return signals


def _describe(facts: dict[str, Any]) -> str:
    parts: list[str] = []
    if facts["apparent_temperature_max"] is not None:
        parts.append(f"feels-like high {facts['apparent_temperature_max']:.1f}°C")
    if facts["temperature_2m_max"] is not None:
        parts.append(f"air temperature high {facts['temperature_2m_max']:.1f}°C")
    if facts["precipitation_sum"] is not None:
        rain = f"rain {facts['precipitation_sum']:.1f} mm"
        if facts["precipitation_probability_max"] is not None:
            rain += f" ({facts['precipitation_probability_max']:.0f}% chance)"
        parts.append(rain)
    return "Forecast: " + ", ".join(parts) + "."

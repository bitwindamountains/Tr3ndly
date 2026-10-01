from typing import Any

import httpx
import pytest

from tests.conftest import FIXTURE_NOW, mock_client
from tr3ndly.geo import PH_LOCATIONS
from tr3ndly.sources.open_meteo import COMMERCIAL_ENDPOINT, FREE_ENDPOINT, OpenMeteoAdapter


async def test_fetch_pairs_each_forecast_with_its_location(forecast: list[dict[str, Any]]) -> None:
    async with mock_client(forecast) as client:
        items = await OpenMeteoAdapter().fetch(client)
        request = client.requests[0]  # type: ignore[attr-defined]

    assert [location for location, _ in items] == list(PH_LOCATIONS)
    assert str(request.url).startswith(FREE_ENDPOINT)
    assert request.url.params["timezone"] == "Asia/Manila"
    assert "apikey" not in request.url.params


async def test_api_key_switches_to_commercial_endpoint(forecast: list[dict[str, Any]]) -> None:
    async with mock_client(forecast) as client:
        await OpenMeteoAdapter(api_key="secret").fetch(client)
        request = client.requests[0]  # type: ignore[attr-defined]

    assert str(request.url).startswith(COMMERCIAL_ENDPOINT)
    assert request.url.params["apikey"] == "secret"


async def test_fetch_rejects_a_short_response(forecast: list[dict[str, Any]]) -> None:
    async with mock_client(forecast[:2]) as client:
        with pytest.raises(ValueError, match="2 forecasts for 3 places"):
            await OpenMeteoAdapter().fetch(client)


async def test_client_errors_are_not_retried(forecast: list[dict[str, Any]]) -> None:
    async with mock_client({"error": True}, status_code=400) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await OpenMeteoAdapter().fetch(client)
        assert len(client.requests) == 1  # type: ignore[attr-defined]


def test_normalize_emits_one_signal_per_day(forecast: list[dict[str, Any]]) -> None:
    adapter = OpenMeteoAdapter()
    signals = adapter.normalize((PH_LOCATIONS[0], forecast[0]), FIXTURE_NOW)

    assert [signal.external_id for signal in signals] == [
        "metro-manila:2026-10-02",
        "metro-manila:2026-10-03",
        "metro-manila:2026-10-04",
    ]
    first = signals[0]
    assert first.facts["apparent_temperature_max"] == 39.2
    assert first.summary.startswith("Forecast: feels-like high 39.2°C")
    assert first.observed_at == FIXTURE_NOW


def test_content_hash_changes_only_when_the_forecast_changes(
    forecast: list[dict[str, Any]],
) -> None:
    adapter = OpenMeteoAdapter()
    item = (PH_LOCATIONS[0], forecast[0])
    first = adapter.normalize(item, FIXTURE_NOW)[0]
    refetched = adapter.normalize(item, FIXTURE_NOW.replace(hour=3))[0]
    forecast[0]["daily"]["apparent_temperature_max"][0] = 41.0
    revised = adapter.normalize(item, FIXTURE_NOW)[0]

    assert first.content_hash == refetched.content_hash
    assert first.content_hash != revised.content_hash

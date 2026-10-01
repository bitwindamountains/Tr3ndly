from datetime import UTC, datetime

from fastapi.testclient import TestClient


def test_today_returns_explicit_demo_data(client: TestClient) -> None:
    response = client.get("/today")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "demo"
    assert payload["source_health"] == "demo"
    assert payload["signals"] == []
    assert len(payload["opportunities"]) == 1
    assert payload["opportunities"][0]["score"]["version"] == "discovery-v0.1"
    assert datetime.fromisoformat(payload["generated_at"]).tzinfo == UTC

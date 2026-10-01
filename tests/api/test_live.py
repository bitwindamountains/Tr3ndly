from collections import Counter

from fastapi.testclient import TestClient


def test_today_in_live_mode_hides_demo_cards_and_shows_signals(live_client: TestClient) -> None:
    payload = live_client.get("/today").json()

    assert payload["mode"] == "live"
    assert payload["source_health"] == "healthy"
    assert [source["state"] for source in payload["sources"]] == ["healthy"]
    assert all(item["id"] != "demo_opp_fan" for item in payload["opportunities"])

    headlines = [signal["headline"] for signal in payload["signals"]]
    assert headlines == [
        "Hot conditions forecast in Metro Manila",
        "Heavy rain forecast in Cebu City",
    ]
    assert "personal cooling" in payload["signals"][0]["consumer_needs"]

    # Diversity: at most two cards per event, ranked by discovery priority.
    locations = Counter(item["location"] for item in payload["opportunities"])
    assert locations == {"Metro Manila": 2, "Cebu City": 2}
    priorities = [item["score"]["discovery_priority"] for item in payload["opportunities"]]
    assert priorities == sorted(priorities, reverse=True)
    assert (
        payload["opportunities"][0]["expires_at"].endswith("Z")
        or "+00:00" in (payload["opportunities"][0]["expires_at"])
    )


def test_live_opportunity_detail_carries_traceable_evidence(live_client: TestClient) -> None:
    first = live_client.get("/today").json()["opportunities"][0]
    detail = live_client.get(f"/opportunities/{first['id']}").json()

    assert detail["status"] == "eligible"
    assert detail["decidable"] is True
    assert detail["score"]["version"] == "discovery-v1"
    assert detail["score"]["timely_score"] >= 65
    assert detail["evidence"][0]["source_name"] == "Open-Meteo forecast"
    assert detail["evidence"][0]["source_url"] == "https://open-meteo.com/"


def test_operations_endpoints_report_runs(live_client: TestClient) -> None:
    sources = live_client.get("/operations/sources").json()
    runs = live_client.get("/operations/runs").json()

    assert sources[0]["slug"] == "open-meteo"
    assert sources[0]["last_success_at"] is not None
    assert runs[0]["status"] == "succeeded"
    assert runs[0]["stats"]["opportunities_created"] == 9


def test_today_filters_by_location_and_lists_all_locations(live_client: TestClient) -> None:
    payload = live_client.get("/today", params={"location": "Cebu City"}).json()

    assert payload["locations"] == ["Cebu City", "Metro Manila"]
    assert {item["location"] for item in payload["opportunities"]} == {"Cebu City"}
    assert [signal["location"] for signal in payload["signals"]] == ["Cebu City"]
    assert live_client.get("/today", params={"reason_type": "trend"}).json()["opportunities"] == []

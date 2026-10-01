from fastapi.testclient import TestClient


def test_opportunity_detail_and_decision(client: TestClient) -> None:
    detail = client.get("/opportunities/demo_opp_fan")
    assert detail.status_code == 200
    assert detail.json()["decisions"] == []

    decision = client.post(
        "/opportunities/demo_opp_fan/decision",
        json={"decision": "accepted", "reason_code": "useful_opportunity"},
    )
    assert decision.status_code == 201
    assert decision.json()["decision"] == "accepted"
    assert decision.json()["score_version"] == "discovery-v0.1"

    refreshed = client.get("/opportunities/demo_opp_fan")
    assert refreshed.json()["status"] == "accepted"
    assert len(refreshed.json()["decisions"]) == 1


def test_decision_rejects_unknown_opportunity(client: TestClient) -> None:
    response = client.post(
        "/opportunities/missing/decision",
        json={"decision": "rejected", "reason_code": "not_a_fit"},
    )
    assert response.status_code == 404

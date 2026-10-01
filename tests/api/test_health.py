from fastapi.testclient import TestClient

from tr3ndly import __version__


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Tr3ndly API",
        "environment": "development",
        "version": __version__,
    }

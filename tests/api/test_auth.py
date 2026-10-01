from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from tr3ndly.config import Settings, get_settings

TOKEN = "operator-token-for-tests-0123456789"


@pytest.fixture
def secured(client: TestClient) -> Iterator[TestClient]:
    app.dependency_overrides[get_settings] = lambda: Settings(operator_token=TOKEN)
    yield client
    app.dependency_overrides.pop(get_settings, None)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/today"),
        ("get", "/opportunities/demo_opp_fan"),
        ("post", "/opportunities/demo_opp_fan/decision"),
        ("get", "/operations/sources"),
        ("get", "/operations/runs"),
    ],
)
def test_every_route_but_health_requires_the_token(
    secured: TestClient, method: str, path: str
) -> None:
    missing = secured.request(method, path)
    wrong = secured.request(method, path, headers={"Authorization": "Bearer nope"})

    assert missing.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"
    assert wrong.status_code == 401


def test_correct_token_is_accepted(secured: TestClient) -> None:
    response = secured.get("/today", headers={"Authorization": f"Bearer {TOKEN}"})
    assert response.status_code == 200


def test_health_stays_open(secured: TestClient) -> None:
    assert secured.get("/health").status_code == 200

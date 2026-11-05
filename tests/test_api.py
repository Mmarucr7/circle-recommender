from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from circle_recommender.api.app import create_app


def assert_error_shape(body: dict[str, object], code: str) -> None:
    assert set(body) == {"error"}
    error = body["error"]
    assert isinstance(error, dict)
    assert set(error) == {"code", "message", "details"}
    assert error["code"] == code


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_recommendations_response_shape(client: TestClient) -> None:
    response = client.get("/users/7/recommendations", params={"limit": 3})
    body = response.json()

    assert response.status_code == 200
    assert set(body) == {"user_id", "reference_time", "strategy", "recommendations"}
    assert body["user_id"] == 7
    assert body["reference_time"].startswith("2026-09-21T00:00:00")
    assert body["strategy"] == "personalized"
    assert [item["rank"] for item in body["recommendations"]] == [1, 2, 3]
    first = body["recommendations"][0]
    assert set(first) == {"rank", "circle", "explanation", "reasons"}
    assert set(first["circle"]) == {
        "id",
        "name",
        "description",
        "format",
        "location",
        "member_count",
        "topics",
        "cover_image_url",
    }
    assert first["circle"]["topics"][0] == {"slug": "leadership-skills", "label": "Leadership skills"}
    assert all(set(reason) == {"code", "detail"} for reason in first["reasons"])


def test_virtual_circles_have_no_location(client: TestClient) -> None:
    body = client.get("/users/42/recommendations").json()

    for item in body["recommendations"]:
        if item["circle"]["format"] == "virtual":
            assert item["circle"]["location"] is None


def test_default_limit_is_ten(client: TestClient) -> None:
    assert len(client.get("/users/42/recommendations").json()["recommendations"]) == 10


def test_debug_mode_adds_breakdown_and_filtered_circles(client: TestClient) -> None:
    body = client.get("/users/23/recommendations", params={"debug": "true"}).json()

    assert set(body["debug"]) == {"confidence", "weights", "filtered_out", "diversified_out"}
    filtered = {entry["circle_id"]: entry["reasons"] for entry in body["debug"]["filtered_out"]}
    assert "FULL" in filtered[20]
    assert "INACTIVE" in filtered[21]
    item_debug = body["recommendations"][0]["debug"]
    assert set(item_debug) == {"score", "features", "contributions", "dedupe_cluster_id"}
    assert item_debug["score"] == pytest.approx(sum(item_debug["contributions"].values()), abs=1e-4)


def test_unknown_user_returns_404(client: TestClient) -> None:
    response = client.get("/users/9999/recommendations")

    assert response.status_code == 404
    assert_error_shape(response.json(), "user_not_found")


def test_unknown_route_uses_the_same_error_shape(client: TestClient) -> None:
    response = client.get("/nope")

    assert response.status_code == 404
    assert_error_shape(response.json(), "not_found")


@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/users/7/recommendations", {"limit": 0}),
        ("/users/7/recommendations", {"limit": 51}),
        ("/users/7/recommendations", {"limit": "ten"}),
        ("/users/abc/recommendations", {}),
        ("/users/0/recommendations", {}),
        ("/users/7/recommendations", {"debug": "maybe"}),
    ],
)
def test_invalid_parameters_return_422(client: TestClient, path: str, params: dict[str, str | int]) -> None:
    response = client.get(path, params=params)

    assert response.status_code == 422
    body = response.json()
    assert_error_shape(body, "validation_error")
    assert body["error"]["details"]


def test_missing_database_returns_503(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path / "missing.db")).get("/users/7/recommendations")

    assert response.status_code == 503
    assert_error_shape(response.json(), "database_not_ready")

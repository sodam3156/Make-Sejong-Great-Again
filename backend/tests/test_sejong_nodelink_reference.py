from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.sejong_nodelink_reference import sejong_nodelink_status
from backend.reference_api import app


def test_verified_sejong_nodelink_status_contract():
    status = sejong_nodelink_status()

    assert status["regionPrefix"] == "413"
    assert status["nodeCount"] == 8768
    assert status["linkCount"] == 11893
    assert status["sourceSha256"] == (
        "adfb23b31592d264cfbc48458ae0fdb5daee707e8c7ba4dbced53c7c544c1a48"
    )
    assert status["usableForCalibration"] is False
    assert status["runtimeActivation"] == "spatial_display_only"

    names = {row["name"] for row in status["targetIntersections"]}
    assert names == {"성금교차로", "청사교차로", "세종교차로"}
    assert all(len(row["node_ids"]) == 4 for row in status["targetIntersections"])
    assert all(row["node_type"] == "101" for row in status["targetIntersections"])

    routes = status["directedCorridorRoutes"]
    assert len(routes) == 4
    assert all(row["road_name"] == "절재로" for row in routes)
    assert all(row["length_m"] > 0 for row in routes)


def test_sejong_nodelink_endpoint_is_read_only():
    client = TestClient(app)

    response = client.get("/api/reference/sejong-nodelink-status")
    assert response.status_code == 200
    assert response.json()["nodeCount"] == 8768
    assert response.json()["usableForCalibration"] is False
    assert client.post("/api/reference/sejong-nodelink-status").status_code == 405

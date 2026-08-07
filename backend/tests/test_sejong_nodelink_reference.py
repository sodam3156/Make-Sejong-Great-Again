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


def test_observed_corridor_geometry_is_directly_consumable():
    status = sejong_nodelink_status()
    geometry = status["displayGeometry"]

    assert geometry["type"] == "FeatureCollection"
    assert geometry["crs"]["properties"]["name"] == "EPSG:4326"
    assert geometry["source"]["regionPrefix"] == "413"

    points = [
        row for row in geometry["features"]
        if row["geometry"]["type"] == "Point"
    ]
    lines = [
        row for row in geometry["features"]
        if row["geometry"]["type"] == "LineString"
    ]
    assert len(points) == 3
    assert len(lines) == 2
    assert {row["properties"]["intersectionName"] for row in points} == {
        "성금교차로",
        "청사교차로",
        "세종교차로",
    }
    assert {row["properties"]["routeName"] for row in lines} == {
        "성금→청사",
        "청사→세종",
    }
    assert all(row["properties"]["roadName"] == "절재로" for row in lines)


def test_model_alignment_does_not_request_roundabout_data_for_actual_corridor():
    alignment = sejong_nodelink_status()["modelAlignment"]

    assert alignment["originalModelScope"] == "synthetic_three_roundabout_corridor"
    assert alignment["intersectionFormEncodedInNodeLink"] is False
    assert alignment["roundaboutDataRequiredForCurrentCorridor"] is False
    assert alignment["requiredPresentationLabel"] == "신호 미모델링 합성 큐 회랑"
    assert alignment["status"] == "SPATIAL_REFERENCE_ONLY_MODEL_MECHANICS_UNALIGNED"


def test_sejong_nodelink_endpoint_is_read_only():
    client = TestClient(app)

    response = client.get("/api/reference/sejong-nodelink-status")
    assert response.status_code == 200
    body = response.json()
    assert body["nodeCount"] == 8768
    assert body["usableForCalibration"] is False
    assert body["modelAlignment"]["roundaboutDataRequiredForCurrentCorridor"] is False
    assert len(body["displayGeometry"]["features"]) == 5
    assert client.post("/api/reference/sejong-nodelink-status").status_code == 405

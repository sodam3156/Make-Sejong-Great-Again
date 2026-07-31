from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.reference_data import (
    router,
    similar_intersections,
    traffic_reference_schedule,
)


def test_reference_schedule_is_data_derived_and_mean_one():
    schedule = traffic_reference_schedule("cheonan", "weekday")

    assert schedule["sourceRegion"] == "Cheonan"
    assert schedule["usableForCalibration"] is False
    assert schedule["runtimeActivation"] == "disabled"
    assert len(schedule["rows"]) == 24
    assert abs(sum(row["demandMultiplier"] for row in schedule["rows"]) / 24 - 1.0) < 1e-6
    assert schedule["peakSummary"]["morningHour"] == 8
    assert schedule["peakSummary"]["eveningHour"] == 17
    assert schedule["consumerContract"]["stepMinutes"] == 60


def test_similar_intersections_exposes_actual_shortlist_with_limits():
    result = similar_intersections(limit=3, min_daily_volume=90_000)

    assert result["sourceRegion"] == "Cheonan"
    assert result["runtimeActivation"] == "disabled"
    assert len(result["rows"]) == 3
    assert [row["rank"] for row in result["rows"]] == [1, 2, 3]
    assert all(row["median_daily_volume"] >= 90_000 for row in result["rows"])
    assert all(row["limitation"] == "topology not verified" for row in result["rows"])


def test_runtime_product_endpoints_are_read_only():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    schedule = client.get(
        "/api/reference/traffic-reference-schedule",
        params={"source": "kict_national_road", "day_type": "weekend"},
    )
    assert schedule.status_code == 200
    assert len(schedule.json()["rows"]) == 24
    assert schedule.json()["consumerContract"]["multiplierField"] == "demandMultiplier"

    candidates = client.get(
        "/api/reference/similar-intersections",
        params={"limit": 5, "min_daily_volume": 70_000},
    )
    assert candidates.status_code == 200
    assert 1 <= len(candidates.json()["rows"]) <= 5

    assert client.post("/api/reference/traffic-reference-schedule").status_code == 405
    assert client.post("/api/reference/similar-intersections").status_code == 405

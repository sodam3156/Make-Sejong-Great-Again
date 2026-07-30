from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.reference_data import (
    movement_fixture,
    router,
    signal_cycle_fixture,
    source_status,
    traffic_hourly_profile,
    vehicle_composition,
)


def test_reference_service_returns_non_runtime_provenance():
    status = source_status()
    assert status["runtimeActivation"] == "disabled"
    assert len(status["availableSources"]) == 7
    assert {slot["slot"] for slot in status["replacementSlots"]} == {
        "sejong_corridor_geometry",
        "sejong_time_resolved_turning_counts",
        "sejong_signal_plan",
        "live_signal_snapshot",
    }

    profile = traffic_hourly_profile("cheonan", "weekday")
    assert profile["usableForCalibration"] is False
    assert len(profile["profile"]["hours"]) == 24
    assert abs(sum(profile["profile"]["normalized_share"]) - 1.0) < 1e-5

    composition = vehicle_composition()
    assert len(composition["classOrder"]) == 12
    assert all(abs(sum(row["normalized_class_shares"]) - 1.0) < 1e-5 for row in composition["rows"])

    movement = movement_fixture()
    assert len(movement["movement"]) == 4
    assert movement["sourceClass"] == "external_fixture"

    signal = signal_cycle_fixture("4", "evening_cycle_sec")
    assert len(signal["rows"]) == 1
    assert signal["rows"][0]["median"] == 150.0


def test_reference_router_is_read_only_and_queryable():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    status = client.get("/api/reference/source-status")
    assert status.status_code == 200
    assert status.json()["runtimeActivation"] == "disabled"

    profile = client.get(
        "/api/reference/traffic-hourly-profile",
        params={"source": "kict_national_road", "day_type": "weekend"},
    )
    assert profile.status_code == 200
    assert len(profile.json()["profile"]["normalized_share"]) == 24

    signal = client.get(
        "/api/reference/signal-cycle-fixture",
        params={"operation_code": "2", "cycle_field": "morning_cycle_sec"},
    )
    assert signal.status_code == 200
    assert len(signal.json()["rows"]) == 1

    assert client.post("/api/reference/source-status").status_code == 405

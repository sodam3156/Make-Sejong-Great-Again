from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.sejong_observed_constraints import (
    router,
    sejong_hdmap_status,
    sejong_historical_signal_plan,
    sejong_observed_input_status,
    sejong_probe_exclusion,
)


def test_hdmap_package_provenance_and_continuous_corridor_coverage():
    data = sejong_hdmap_status()

    assert data["runtime_activation"] == "disabled"
    assert data["usable_for_calibration"] is False
    assert {row["name"] for row in data["target_intersections"]} == {
        "성금교차로",
        "청사교차로",
        "세종교차로",
    }
    assert {row["package_id"] for row in data["source_packages"]} == {
        "hdmap-happycity-sec02-2017",
        "hdmap-sangsang-sec001-2021",
    }
    assert {row["sha256"] for row in data["source_packages"]} == {
        "ce84bedbc62fbbdb452ac1bfa96fd32865600660ad30951020d53d11634e18b4",
        "ab196fd408b05a17d667b81010c78c80c762db5c6664646e2401ee2d1b5da542",
    }
    assert all(
        row["coverage_status"] == "CONTINUOUS_CENTERLINE_COVERAGE"
        and row["nearest_hdmap_link_max_distance_m"] < 20
        for row in data["corridor_coverage"]
    )


def test_hdmap_does_not_claim_approved_lane_or_storage_inputs():
    data = sejong_hdmap_status()

    assert data["decision"] == "OFFICIAL_GEOMETRY_AVAILABLE_BUT_RUNTIME_MAPPING_BLOCKED"
    assert "automatic replacement of current queue-storage constants" in data["forbidden_use"]
    for row in data["target_intersections"]:
        assert "approved approach lane count" in row["not_yet_derived"]
        assert "approved storage length" in row["not_yet_derived"]
    excluded = data["excluded_packages"][0]
    assert excluded["sha256"] == "96f7ba48a47c5e4d4a35e226081a9b8c7821aaa52ccca90fab1d8b420de97303"
    assert excluded["minimum_corridor_distance_m"] > 460
    assert excluded["decision"] == "EXCLUDE_FROM_SIMULATION_AND_TARGET_GEOMETRY"


def test_historical_signal_vectors_are_exact_but_not_current_operation():
    data = sejong_historical_signal_plan()
    rows = {row["intersection"]: row for row in data["rows"]}

    assert data["runtime_activation"] == "disabled"
    assert data["usable_for_calibration"] is False
    assert rows["성금교차로"]["timing_vector_sec"] == [45, 45, 25, 45]
    assert rows["성금교차로"]["nominal_cycle_candidate_sec"] == 160
    assert rows["청사교차로"]["timing_vector_sec"] == [46, 20, 31, 23, 20]
    assert rows["청사교차로"]["nominal_cycle_candidate_sec"] == 140
    assert rows["세종교차로"]["timing_vector_sec"] == [45, 35, 35, 45]
    assert rows["세종교차로"]["nominal_cycle_candidate_sec"] == 160
    assert all(row["timing_decision_method"] == "고정시간제어" for row in rows.values())
    assert data["interpretation"]["current_2026_operation_claim"] is False
    assert data["interpretation"]["effective_green_available"] is False
    assert data["interpretation"]["offset_available"] is False


def test_public_probe_samples_are_explicitly_excluded():
    data = sejong_probe_exclusion()
    rows = {row["source_id"]: row for row in data["sources"]}

    assert data["runtime_activation"] == "excluded"
    assert data["usable_for_calibration"] is False
    assert rows["sejong-b0-public-sample-20210913"]["within_100m_count"] == 0
    assert rows["sejong-pvd-public-sample"]["within_300m_count"] == 0
    assert all(row["decision"] == "EXCLUDE_NO_TARGET_LINK_OVERLAP" for row in rows.values())
    assert data["decision"] == "NO_LOCAL_PROBE_INPUT_FOR_TARGET_SIMULATION"


def test_aggregate_gate_preserves_synthetic_runtime_and_hard_blockers():
    data = sejong_observed_input_status()
    statuses = {row["input"]: row["status"] for row in data["inputs"]}
    decisions = {row["item"]: row["decision"] for row in data["completed_decisions"]}

    assert data["current_runtime_dataset"] == "synthetic-v0"
    assert data["runtime_change_in_this_package"] is False
    assert data["field_calibration_status"] == "HARD_BLOCKED"
    assert statuses["same-date 5/15-minute approach and turning counts"] == "MISSING_HARD_BLOCKER"
    assert statuses["current effective signal plan with TOD, offset and clearance"] == "MISSING_HARD_BLOCKER"
    assert decisions["monthly traffic to 5/15-minute conversion"] == "DO_NOT_BUILD_FOR_RUNTIME"
    assert decisions["Busan queue and LOS API"] == "DEFER_EXTERNAL_FIXTURE"
    assert data["decision"] == "SAFE_EVIDENCE_PIPELINE_COMPLETE_RUNTIME_ACTIVATION_STOPPED"


def test_reference_endpoints_are_read_only():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    paths = [
        "/api/reference/sejong-hdmap-status",
        "/api/reference/sejong-historical-signal-plan",
        "/api/reference/sejong-probe-exclusion",
        "/api/reference/sejong-observed-input-status",
    ]
    for path in paths:
        assert client.get(path).status_code == 200
        assert client.post(path).status_code == 405

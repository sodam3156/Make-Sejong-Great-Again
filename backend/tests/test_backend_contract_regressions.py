"""Regression tests for the frozen RainFlow backend contract.

These tests intentionally exercise the public API for workflow, fallback, and
persistence behavior.  Direct ``build_run`` calls are limited to deterministic
timeline assertions that do not need storage.
"""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.app import main as backend_main
from backend.app.storage import RunStore


FROZEN_SCREEN_STATES = {
    "normal",
    "rain_warning",
    "spillback",
    "policy_compare",
    "safety_review",
    "operator_approval",
    "recovery_compare",
}


@pytest.fixture(autouse=True)
def isolated_run_store(tmp_path, monkeypatch):
    """Keep replay files and audit JSONL out of the repository."""
    store = RunStore(tmp_path / "logs")
    monkeypatch.setattr(backend_main, "STORE", store)
    backend_main.RUNS.clear()
    yield store
    backend_main.RUNS.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(backend_main.app)


def _create_live_run(client: TestClient, *, seed: int = 42) -> dict[str, Any]:
    response = client.post(
        "/api/simulations",
        json={
            "scenario_id": "rain_spillback_a",
            "seed": seed,
            "force_source": "live_simulation",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _get_run(client: TestClient, run_id: str) -> dict[str, Any]:
    response = client.get(f"/api/simulations/{run_id}")
    assert response.status_code == 200, response.text
    return response.json()


def _policy(run: dict[str, Any], policy_id: str) -> dict[str, Any]:
    return next(
        policy for policy in run["policies"]
        if policy["policy_id"] == policy_id
    )


def test_live_rain_timeline_emits_all_seven_frozen_states():
    run = backend_main.build_run("rain_spillback_a", 42)

    emitted_states = {entry["screen_state"] for entry in run["timeline"]}

    assert emitted_states == FROZEN_SCREEN_STATES


def test_guard_detail_does_not_duplicate_approach_suffix():
    run = backend_main.build_run("rain_spillback_a", 42)
    details = [
        violation["detail"]
        for policy in run["policies"]
        for violation in policy["guard"]["violations"]
    ]

    assert details, "가드 위반 문구를 검증할 후보가 필요하다"
    assert all("진입로 진입로" not in detail for detail in details)


def test_dry_base_never_emits_rain_or_recovery_states():
    run = backend_main.build_run("dry_base", 42)

    assert {entry["screen_state"] for entry in run["timeline"]} == {"normal"}
    assert {entry["rain_level"] for entry in run["timeline"]} == {"dry"}


def test_before_approval_applied_result_is_no_action(client: TestClient):
    created = _create_live_run(client)
    run = _get_run(client, created["run_id"])

    no_action = _policy(run, "no_action")

    assert run["approval"]["status"] == "pending"
    assert run["recovery_compare"]["applied"] == no_action["kpi"]


def test_reject_keeps_no_action_applied(client: TestClient):
    created = _create_live_run(client)
    run = _get_run(client, created["run_id"])
    policy_id = run["decision"]["recommended_policy_id"]

    response = client.post(
        "/api/approvals",
        json={
            "run_id": run["run_id"],
            "policy_id": policy_id,
            "decision": "reject",
            "reason": "regression test",
        },
    )

    assert response.status_code == 200, response.text
    updated = _get_run(client, run["run_id"])
    assert updated["approval"]["status"] == "rejected"
    assert updated["workflow_state"] == "HUMAN_REJECTED"
    assert updated["recovery_compare"]["applied"] == _policy(
        updated, "no_action"
    )["kpi"]
    assert updated["recovery_compare"]["applied_policy_id"] == "no_action"


def test_approve_safe_candidate_applies_it_and_reaches_evaluated(
    client: TestClient,
):
    created = _create_live_run(client)
    run = _get_run(client, created["run_id"])
    policy_id = run["decision"]["recommended_policy_id"]
    candidate = _policy(run, policy_id)

    assert policy_id != "no_action"
    assert candidate["guard"]["passed"] is True

    response = client.post(
        "/api/approvals",
        json={
            "run_id": run["run_id"],
            "policy_id": policy_id,
            "decision": "approve",
            "expected_candidate_hash": candidate["candidate_hash"],
            "reason": "regression test",
        },
    )

    assert response.status_code == 200, response.text
    updated = _get_run(client, run["run_id"])
    assert updated["approval"]["status"] == "approved"
    assert updated["workflow_state"] == "EVALUATED"
    assert updated["state_history"][-1]["state"] == "EVALUATED"
    assert updated["recovery_compare"]["applied"] == candidate["kpi"]
    assert updated["recovery_compare"]["applied_policy_id"] == policy_id


@pytest.mark.parametrize(
    ("data_quality", "expected_code"),
    [
        (
            {
                "data_age_sec": 121,
                "sensor_available": True,
                "device_status": "ok",
            },
            "DATA_STALE",
        ),
        (
            {
                "data_age_sec": 0,
                "sensor_available": True,
                "device_status": "fault",
            },
            "DEVICE_FAULT",
        ),
    ],
)
def test_stale_data_or_device_fault_blocks_approval(
    client: TestClient,
    data_quality: dict[str, Any],
    expected_code: str,
):
    created = _create_live_run(client)
    run = _get_run(client, created["run_id"])
    policy_id = run["decision"]["recommended_policy_id"]
    candidate = _policy(run, policy_id)

    response = client.post(
        "/api/approvals",
        json={
            "run_id": run["run_id"],
            "policy_id": policy_id,
            "decision": "approve",
            "expected_candidate_hash": candidate["candidate_hash"],
            "data_quality": data_quality,
        },
    )

    assert response.status_code == 409, response.text
    assert expected_code in {
        violation["code"]
        for violation in response.json()["detail"]["violations"]
    }
    updated = _get_run(client, run["run_id"])
    assert updated["approval"]["status"] == "pending"
    assert updated["recovery_compare"]["applied"] == _policy(
        updated, "no_action"
    )["kpi"]


def test_candidate_hash_tampering_blocks_approval(client: TestClient):
    created = _create_live_run(client)
    run = _get_run(client, created["run_id"])
    policy_id = run["decision"]["recommended_policy_id"]
    original_hash = _policy(run, policy_id)["candidate_hash"]

    stored_policy = _policy(backend_main.RUNS[run["run_id"]], policy_id)
    stored_policy["kpi"]["total_travel_time_sec"] += 1

    response = client.post(
        "/api/approvals",
        json={
            "run_id": run["run_id"],
            "policy_id": policy_id,
            "decision": "approve",
            "expected_candidate_hash": original_hash,
        },
    )

    assert response.status_code == 409, response.text
    assert "CANDIDATE_HASH_MISMATCH" in {
        violation["code"]
        for violation in response.json()["detail"]["violations"]
    }


@pytest.mark.parametrize(
    ("force_source", "expected_source"),
    [
        ("cached_simulation", "cached_simulation"),
        ("fixture", "fixture"),
    ],
)
def test_forced_fallback_modes_label_result_source(
    client: TestClient,
    force_source: str,
    expected_source: str,
):
    response = client.post(
        "/api/simulations",
        json={
            "scenario_id": "rain_spillback_a",
            "seed": 42,
            "force_source": force_source,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["result_source"] == expected_source
    run = _get_run(client, response.json()["run_id"])
    assert run["result_source"] == expected_source


def test_persisted_run_loads_after_in_memory_cache_is_cleared(
    client: TestClient,
    isolated_run_store: RunStore,
):
    created = _create_live_run(client)
    run_id = created["run_id"]

    assert isolated_run_store.load(run_id) is not None
    backend_main.RUNS.clear()

    restored = _get_run(client, run_id)

    assert restored["run_id"] == run_id
    assert restored["result_source"] == "live_simulation"
    assert run_id in backend_main.RUNS


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/api/health", "get"),
        ("/api/simulations", "post"),
        ("/api/simulations/{run_id}", "get"),
        ("/api/approvals", "post"),
    ],
)
def test_frozen_openapi_success_responses_reference_named_schemas(
    path: str,
    method: str,
):
    operation = backend_main.app.openapi()["paths"][path][method]
    response_schema = operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]

    assert response_schema.get("$ref"), (
        f"{method.upper()} {path} must expose a named 200 response schema"
    )

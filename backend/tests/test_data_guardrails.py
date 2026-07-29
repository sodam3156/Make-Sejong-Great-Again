"""Regression tests for dataset selection and stored-result rollback guards."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from backend.app import main as backend_main
from backend.app.storage import RunStore


@pytest.fixture(autouse=True)
def isolated_run_store(tmp_path, monkeypatch):
    store = RunStore(tmp_path / "logs")
    monkeypatch.setattr(backend_main, "STORE", store)
    backend_main.RUNS.clear()
    yield
    backend_main.RUNS.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(backend_main.app)


def test_default_run_declares_synthetic_dataset(client: TestClient):
    created = client.post(
        "/api/simulations",
        json={"scenario_id": "rain_spillback_a", "seed": 42},
    )

    assert created.status_code == 200, created.text
    run = client.get(created.json()["url"]).json()
    assert run["dataset"] == {
        "dataset_id": "synthetic-v0",
        "data_class": "synthetic",
        "schema_version": "rainflow-dataset-v1",
        "adapter_version": "builtin-synthetic-v1",
        "default": True,
    }
    assert run["reproducibility"]["input"]["dataset_id"] == "synthetic-v0"


def test_uninstalled_dataset_is_rejected_before_execution(client: TestClient):
    response = client.post(
        "/api/simulations",
        json={
            "scenario_id": "rain_spillback_a",
            "seed": 42,
            "dataset_id": "sejong-real-v1",
        },
    )

    assert response.status_code == 422
    with pytest.raises(ValueError, match="dataset adapter not installed"):
        backend_main.build_run(
            "rain_spillback_a",
            42,
            dataset_id="sejong-real-v1",
        )


def test_stored_a_fixture_cannot_masquerade_as_scenario_b(client: TestClient):
    response = client.post(
        "/api/simulations",
        json={
            "scenario_id": "rain_spillback_b",
            "seed": 42,
            "force_source": "fixture",
        },
    )

    assert response.status_code == 503


def test_auto_fallback_fails_when_no_compatible_scenario_exists(
    client: TestClient,
    monkeypatch,
):
    def fail_simulation(*args, **kwargs):
        raise RuntimeError("simulator unavailable")

    monkeypatch.setattr(backend_main, "run_simulation", fail_simulation)
    response = client.post(
        "/api/simulations",
        json={"scenario_id": "rain_spillback_b", "seed": 42},
    )

    assert response.status_code == 503
    assert "no compatible stored result" in response.json()["detail"]


def test_current_fixture_id_is_loadable(client: TestClient):
    fixture = json.loads(
        backend_main.FIXTURE_PATH.read_text(encoding="utf-8")
    )

    response = client.get(f"/api/simulations/{fixture['run_id']}")

    assert response.status_code == 200
    assert response.json()["run_id"] == fixture["run_id"]


def test_compatible_fixture_replay_preserves_result_checksum(
    client: TestClient,
):
    created = client.post(
        "/api/simulations",
        json={
            "scenario_id": "rain_spillback_a",
            "seed": 42,
            "force_source": "fixture",
        },
    )

    assert created.status_code == 200, created.text
    run = client.get(created.json()["url"]).json()
    assert backend_main.result_checksum(run) == (
        run["reproducibility"]["result_checksum"]
    )
    assert run["reproducibility"]["replay_mode"] == "stored-result"


def test_incident_scenario_exposes_effective_and_nominal_storage():
    run = backend_main.build_run("rain_spillback_b", 42)
    l23 = next(
        link for link in run["network"]["links"]
        if link["link_id"] == "L23"
    )

    assert run["scenario"]["incident_type"] == "L23_partial_space_occupancy"
    assert l23["storage_veh"] == pytest.approx(14.4)
    assert l23["nominal_storage_veh"] == 18


def test_health_declares_default_dataset(client: TestClient):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["dataset_id"] == "synthetic-v0"

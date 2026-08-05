"""Dataset identity and fallback boundary regression tests."""
from __future__ import annotations

import copy

import pytest
from fastapi.testclient import TestClient

from backend.app import main as backend_main


def test_default_dataset_metadata_is_recorded():
    run = backend_main.build_run("rain_spillback_a", 42)

    assert run["dataset"] == {
        "dataset_id": "synthetic-v0",
        "data_class": "synthetic",
        "schema_version": "rainflow-dataset-v1",
        "adapter_version": "builtin-synthetic-v1",
        "default": True,
    }
    assert run["reproducibility"]["input"]["dataset_id"] == "synthetic-v0"


def test_dataset_identity_is_covered_by_result_checksum():
    run = backend_main.build_run("rain_spillback_a", 42)
    changed = copy.deepcopy(run)
    changed["dataset"]["dataset_id"] = "another-dataset"

    assert backend_main.result_checksum(changed) != (
        run["reproducibility"]["result_checksum"]
    )


def test_uninstalled_dataset_is_rejected_before_simulation():
    client = TestClient(backend_main.app)

    response = client.post(
        "/api/simulations",
        json={
            "scenario_id": "rain_spillback_a",
            "seed": 42,
            "dataset_id": "sejong-real-v1",
        },
    )

    assert response.status_code == 422


def test_fallback_rejects_a_stored_dataset_mismatch(monkeypatch):
    fixture = backend_main.load_fixture()
    fixture["dataset"]["dataset_id"] = "another-dataset"
    monkeypatch.setattr(backend_main, "load_fixture", lambda _path: fixture)

    with pytest.raises(ValueError, match="stored result dataset mismatch"):
        backend_main._fallback_run(
            "rain_spillback_a",
            42,
            {
                "data_age_sec": 0,
                "sensor_available": True,
                "device_status": "ok",
            },
            "fixture",
            "synthetic-v0",
        )


def test_health_declares_the_default_dataset():
    assert backend_main.health()["dataset_id"] == "synthetic-v0"

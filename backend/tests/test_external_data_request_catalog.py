"""Regression tests for external-data request and handoff boundaries."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.validate_external_data_request_catalog import validate_catalog

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/governance/external_data_request_catalog.json"


def load_catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def request_by_id(catalog: dict, request_id: str) -> dict:
    return next(item for item in catalog["requests"] if item["request_id"] == request_id)


def test_current_catalog_passes_and_remains_pending():
    catalog = load_catalog()
    result = validate_catalog(catalog)
    assert result.ok, result.errors
    assert all(not item["response_received"] for item in catalog["requests"])


def test_pending_request_cannot_claim_response_received():
    catalog = load_catalog()
    item = request_by_id(catalog, "IR-CORRIDOR-LATEST")
    item["response_received"] = True
    result = validate_catalog(catalog)
    assert (
        "IR-CORRIDOR-LATEST: pending status cannot claim response_received"
        in result.errors
    )


def test_disclosed_status_requires_response_received():
    catalog = load_catalog()
    item = request_by_id(catalog, "IR-TRAFFIC-2025")
    item["current_status"] = "disclosed"
    result = validate_catalog(catalog)
    assert (
        "IR-TRAFFIC-2025: terminal response status requires response_received"
        in result.errors
    )


def test_traffic_request_requires_time_and_direction_checks():
    catalog = load_catalog()
    item = request_by_id(catalog, "IR-TRAFFIC-2026")
    item["acceptance_checks"].remove("direction_semantics")
    result = validate_catalog(catalog)
    assert any(
        error.startswith("IR-TRAFFIC-2026: missing traffic acceptance checks")
        for error in result.errors
    )


def test_signal_model_request_requires_phase_and_green_checks():
    catalog = load_catalog()
    item = request_by_id(catalog, "IR-SIGNAL-OPS-2026")
    item["acceptance_checks"].remove("effective_green")
    result = validate_catalog(catalog)
    assert any(
        error.startswith("IR-SIGNAL-OPS-2026: missing signal acceptance checks")
        for error in result.errors
    )


def test_corridor_geometry_requires_storage_inputs():
    catalog = load_catalog()
    item = request_by_id(catalog, "IR-CORRIDOR-LATEST")
    item["acceptance_checks"].remove("usable_queue_length")
    result = validate_catalog(catalog)
    assert any(
        error.startswith("IR-CORRIDOR-LATEST: missing geometry acceptance checks")
        for error in result.errors
    )


def test_sensitive_public_field_is_rejected():
    catalog = load_catalog()
    catalog["portal_password"] = "must-never-be-committed"
    result = validate_catalog(catalog)
    assert any(error.startswith("forbidden sensitive public fields") for error in result.errors)


def test_request_storage_path_must_match_id():
    catalog = load_catalog()
    item = request_by_id(catalog, "IR-SIGNAL-CHANGE-2026")
    item["storage_path"] = "data/public/information_requests/wrong/"
    result = validate_catalog(catalog)
    assert (
        "IR-SIGNAL-CHANGE-2026: storage_path does not match request_id"
        in result.errors
    )


def test_external_response_never_activates_model_automatically():
    catalog = load_catalog()
    catalog["model_activation_policy"] = "automatic"
    result = validate_catalog(catalog)
    assert (
        "external responses must never activate model inputs automatically"
        in result.errors
    )


def test_input_is_not_mutated():
    catalog = load_catalog()
    before = copy.deepcopy(catalog)
    validate_catalog(catalog)
    assert catalog == before

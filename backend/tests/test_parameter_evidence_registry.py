"""Regression tests for parameter evidence and approval boundaries."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.validate_parameter_evidence_registry import validate_registry

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data/governance/parameter_evidence_registry.json"


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def entry_by_id(registry: dict, parameter_id: str) -> dict:
    return next(
        entry for entry in registry["entries"] if entry["parameter_id"] == parameter_id
    )


def test_current_registry_passes_without_approving_values():
    registry = load_registry()
    result = validate_registry(registry)
    assert result.ok, result.errors
    assert all(entry["approved_value"] is None for entry in registry["entries"])


def test_registry_does_not_change_runtime_parameters():
    registry = load_registry()
    assert registry["model_parameter_change_in_this_registry"] is False
    assert entry_by_id(registry, "simulation.BASE_DEMAND")["current_value"] == {
        "R1_N": 0.9,
        "R1_W": 0.35,
        "R2_S": 0.4,
        "R3_E": 0.35,
    }


def test_observed_derived_candidate_cannot_be_activated():
    registry = load_registry()
    candidate = entry_by_id(
        registry, "traffic.monthly_direction_share_mapping_candidate"
    )
    candidate["runtime_active"] = True
    result = validate_registry(registry)
    assert (
        "traffic.monthly_direction_share_mapping_candidate: observed-derived candidate cannot be runtime active"
        in result.errors
    )


def test_evidence_gap_cannot_have_a_fabricated_value():
    registry = load_registry()
    gap = entry_by_id(registry, "traffic.same_date_intraday_absolute_demand")
    gap["current_value"] = 123
    result = validate_registry(registry)
    assert (
        "traffic.same_date_intraday_absolute_demand: evidence gap current_value must be null"
        in result.errors
    )


def test_unreviewed_entry_cannot_be_marked_approved():
    registry = load_registry()
    entry = entry_by_id(registry, "guard.safety_and_fairness_thresholds")
    entry["lifecycle_status"] = "approved"
    entry["approved_value"] = entry["current_value"]
    result = validate_registry(registry)
    assert (
        "guard.safety_and_fairness_thresholds: approved lifecycle requires named approved review"
        in result.errors
    )


def test_active_provisional_entry_is_limited_to_synthetic_demo():
    registry = load_registry()
    entry = entry_by_id(registry, "policy.metering_and_gating")
    entry["allowed_usage"] = ["policy_comparison"]
    result = validate_registry(registry)
    assert (
        "policy.metering_and_gating: active provisional value must allow synthetic_demo_only"
        in result.errors
    )


def test_inverted_evidence_range_is_rejected():
    registry = load_registry()
    entry = entry_by_id(registry, "simulation.RAIN_CAPACITY_FACTOR")
    entry["evidence_range"] = {
        "non_dry_capacity_multiplier_lower": 0.96,
        "non_dry_capacity_multiplier_upper": 0.84,
    }
    result = validate_registry(registry)
    assert (
        "simulation.RAIN_CAPACITY_FACTOR: evidence lower bound exceeds upper bound"
        in result.errors
    )


def test_duplicate_parameter_ids_are_rejected():
    registry = load_registry()
    registry["entries"].append(copy.deepcopy(registry["entries"][0]))
    result = validate_registry(registry)
    assert any(error.startswith("duplicate parameter_id values") for error in result.errors)


def test_registry_only_change_cannot_claim_parameter_change():
    registry = load_registry()
    registry["model_parameter_change_in_this_registry"] = True
    result = validate_registry(registry)
    assert "registry-only PR must not declare a model parameter change" in result.errors

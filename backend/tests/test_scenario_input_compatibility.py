"""Regression tests for temporal and usage compatibility of scenario evidence."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.validate_scenario_input_compatibility import validate_manifest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "data/observed/derived/scenario_input_manifest.example.json"


def load_example() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_current_observation_constrained_manifest_passes():
    result = validate_manifest(load_example())
    assert result.ok, result.errors
    assert result.status == "PASS"
    assert any("direction-share context only" in warning for warning in result.warnings)


def test_reanalysis_proxy_cannot_be_promoted_to_observed_input():
    manifest = load_example()
    manifest["weather"]["source_class"] = "reanalysis_proxy"
    result = validate_manifest(manifest)
    assert not result.ok
    assert "direct weather input must have source_class=observed" in result.errors
    assert "reanalysis proxy may only be used for screening and sensitivity" in result.errors


def test_historical_traffic_outside_scenario_period_fails():
    manifest = load_example()
    manifest["traffic"]["source_period_start"] = "2017-01-01"
    manifest["traffic"]["source_period_end"] = "2017-12-31"
    result = validate_manifest(manifest)
    assert "traffic source period does not contain scenario_date" in result.errors


def test_monthly_traffic_cannot_map_absolute_demand():
    manifest = load_example()
    manifest["claims"]["traffic_parameter_mapping"] = True
    result = validate_manifest(manifest)
    assert "monthly traffic cannot directly map absolute model demand" in result.errors
    assert "weather-only status conflicts with traffic parameter mapping" in result.errors


def test_2023_signal_reference_cannot_be_labeled_current_2026_plan():
    manifest = load_example()
    manifest["claims"]["current_signal_plan"] = True
    result = validate_manifest(manifest)
    assert "signal reference year does not match the claimed current year" in result.errors


def test_field_replay_claim_requires_matched_traffic_and_signal():
    manifest = load_example()
    manifest["claims"]["field_replay"] = True
    result = validate_manifest(manifest)
    assert "field replay requires same-date calibrated traffic" in result.errors
    assert "field replay requires an explicit signal-plan input" in result.errors


def test_dry_reference_before_0600_requires_prior_day_data():
    manifest = load_example()
    manifest["dry_reference"]["analysis_start_kst"] = "2022-07-27T05:00:00+09:00"
    result = validate_manifest(manifest)
    assert (
        "dry-reference start is earlier than the verified preceding-six-hour window"
        in result.errors
    )


def test_input_object_is_not_mutated():
    manifest = load_example()
    before = copy.deepcopy(manifest)
    validate_manifest(manifest)
    assert manifest == before

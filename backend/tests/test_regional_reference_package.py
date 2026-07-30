from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "data" / "observed" / "regional_reference"
VALIDATOR_PATH = ROOT / "scripts" / "validate_regional_reference_package.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("regional_reference_validator", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_committed_regional_reference_package_passes():
    assert load_validator().validate_package(PACKAGE_ROOT) == []


def test_reference_profiles_are_normalized_and_not_calibration_inputs():
    for name in (
        "cheonan_profiles.json",
        "kict_expressway_profiles.json",
        "kict_national_road_profiles.json",
    ):
        data = json.loads((PACKAGE_ROOT / name).read_text(encoding="utf-8"))
        assert data["runtime_activation"] == "disabled"
        for profile in data["profiles"].values():
            assert profile["source_class"] == "regional_reference"
            assert profile["usable_for_calibration"] is False
            assert profile["hours"] == list(range(24))
            assert abs(sum(profile["normalized_share"]) - 1.0) < 1e-5


def test_backend_handoff_keeps_future_sejong_data_as_reviewed_replacements():
    handoff = json.loads((PACKAGE_ROOT / "backend_handoff.json").read_text(encoding="utf-8"))
    assert handoff["runtime_activation"] == "disabled"
    assert "synthetic-v0" in handoff["activation_rule"]
    assert {slot["slot"] for slot in handoff["replacement_slots"]} == {
        "sejong_corridor_geometry",
        "sejong_time_resolved_turning_counts",
        "sejong_signal_plan",
        "live_signal_snapshot",
    }

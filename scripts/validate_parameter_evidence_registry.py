#!/usr/bin/env python3
"""Validate RainFlow parameter evidence and approval boundaries.

The registry mirrors current values and evidence gaps. Passing this validator
means provenance labels are internally consistent; it does not approve any
parameter for operational or field use.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ALLOWED_CLASSIFICATIONS = {
    "observed",
    "observed_derived_candidate",
    "transferred_provisional",
    "synthetic_provisional",
    "evidence_gap",
}
ALLOWED_LIFECYCLE = {
    "evidence_ready_pending_merge",
    "candidate_review_required",
    "active_synthetic_provisional",
    "blocked_missing_data",
    "approved",
    "rejected",
}
ALLOWED_REVIEW_STATUS = {"not_started", "pending", "approved", "rejected"}


@dataclass(frozen=True)
class RegistryResult:
    status: str
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ok"] = self.ok
        return payload


def _nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def validate_registry(registry: dict[str, Any]) -> RegistryResult:
    errors: list[str] = []
    warnings: list[str] = []

    if registry.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if registry.get("default_dataset") != "synthetic-v0":
        errors.append("default_dataset must remain synthetic-v0")
    if registry.get("model_parameter_change_in_this_registry") is not False:
        errors.append("registry-only PR must not declare a model parameter change")

    entries = registry.get("entries")
    if not isinstance(entries, list) or not entries:
        return RegistryResult("FAIL", [*errors, "entries must be a non-empty list"], warnings)

    ids: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        prefix = f"entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        parameter_id = entry.get("parameter_id")
        if not isinstance(parameter_id, str) or not parameter_id.strip():
            errors.append(f"{prefix}.parameter_id must be a non-empty string")
            continue
        ids.append(parameter_id)
        by_id[parameter_id] = entry

        classification = entry.get("classification")
        lifecycle = entry.get("lifecycle_status")
        runtime_active = entry.get("runtime_active")
        provisional = entry.get("provisional")
        review = entry.get("independent_review")

        if classification not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"{parameter_id}: invalid classification {classification!r}")
        if lifecycle not in ALLOWED_LIFECYCLE:
            errors.append(f"{parameter_id}: invalid lifecycle_status {lifecycle!r}")
        if not isinstance(runtime_active, bool):
            errors.append(f"{parameter_id}: runtime_active must be boolean")
        if not isinstance(provisional, bool):
            errors.append(f"{parameter_id}: provisional must be boolean")
        if not _nonempty_strings(entry.get("allowed_usage")):
            errors.append(f"{parameter_id}: allowed_usage must be a non-empty string list")
        if not _nonempty_strings(entry.get("prohibited_usage")):
            errors.append(f"{parameter_id}: prohibited_usage must be a non-empty string list")
        if not isinstance(entry.get("confidence"), dict):
            errors.append(f"{parameter_id}: confidence must be an object")
        if not isinstance(review, dict):
            errors.append(f"{parameter_id}: independent_review must be an object")
            review = {}
        review_status = review.get("status")
        if review_status not in ALLOWED_REVIEW_STATUS:
            errors.append(f"{parameter_id}: invalid independent review status")

        if classification == "evidence_gap":
            if runtime_active is not False:
                errors.append(f"{parameter_id}: evidence gap cannot be runtime active")
            if entry.get("current_value") is not None:
                errors.append(f"{parameter_id}: evidence gap current_value must be null")
            if lifecycle != "blocked_missing_data":
                errors.append(f"{parameter_id}: evidence gap must be blocked_missing_data")

        if classification in {"observed", "observed_derived_candidate"}:
            if not _nonempty_strings(entry.get("source_refs")):
                errors.append(f"{parameter_id}: observed evidence requires source_refs")

        if classification == "observed_derived_candidate" and runtime_active:
            errors.append(f"{parameter_id}: observed-derived candidate cannot be runtime active")

        if lifecycle == "approved":
            if review_status != "approved" or not review.get("reviewer"):
                errors.append(f"{parameter_id}: approved lifecycle requires named approved review")
            if entry.get("approved_value") is None:
                errors.append(f"{parameter_id}: approved lifecycle requires approved_value")
        elif entry.get("approved_value") is not None:
            errors.append(f"{parameter_id}: unapproved entry must have approved_value=null")

        if runtime_active and classification in {
            "synthetic_provisional",
            "transferred_provisional",
        }:
            if provisional is not True:
                errors.append(f"{parameter_id}: active provisional value must be provisional=true")
            if entry.get("target_dataset") != "synthetic-v0":
                errors.append(f"{parameter_id}: active provisional value must target synthetic-v0")
            if "synthetic_demo_only" not in entry.get("allowed_usage", []):
                errors.append(f"{parameter_id}: active provisional value must allow synthetic_demo_only")
            warnings.append(f"{parameter_id} remains active only in synthetic-v0")

        evidence_range = entry.get("evidence_range")
        if evidence_range is not None:
            if not isinstance(evidence_range, dict):
                errors.append(f"{parameter_id}: evidence_range must be an object")
            else:
                lowers = [value for key, value in evidence_range.items() if key.endswith("_lower")]
                uppers = [value for key, value in evidence_range.items() if key.endswith("_upper")]
                if len(lowers) == 1 and len(uppers) == 1:
                    try:
                        if float(lowers[0]) > float(uppers[0]):
                            errors.append(f"{parameter_id}: evidence lower bound exceeds upper bound")
                    except (TypeError, ValueError):
                        errors.append(f"{parameter_id}: evidence bounds must be numeric")

    if len(ids) != len(set(ids)):
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        errors.append(f"duplicate parameter_id values: {duplicates}")

    required_runtime = {
        "simulation.BASE_DEMAND",
        "simulation.APPROACH_CAP",
        "simulation.LINKS_storage",
        "simulation.RAIN_CAPACITY_FACTOR",
        "simulation.jam_and_capacity_drop",
        "scenario.surge_and_incident",
        "policy.metering_and_gating",
        "guard.safety_and_fairness_thresholds",
        "simulation.recovery_criteria",
    }
    missing_runtime = sorted(required_runtime - set(by_id))
    if missing_runtime:
        errors.append(f"missing critical runtime registry entries: {missing_runtime}")

    required_gaps = {
        "traffic.same_date_intraday_absolute_demand",
        "signal.actual_operating_plan",
    }
    missing_gaps = sorted(required_gaps - set(by_id))
    if missing_gaps:
        errors.append(f"missing critical evidence-gap entries: {missing_gaps}")

    expected_values = {
        "simulation.BASE_DEMAND": {"R1_N": 0.9, "R1_W": 0.35, "R2_S": 0.4, "R3_E": 0.35},
        "simulation.RAIN_CAPACITY_FACTOR": {"dry": 1.0, "light": 0.95, "moderate": 0.89, "heavy": 0.84},
        "simulation.LINKS_storage": {"L12": 22, "L23": 18, "BYPASS": 60},
    }
    for parameter_id, expected in expected_values.items():
        entry = by_id.get(parameter_id)
        if entry and entry.get("current_value") != expected:
            errors.append(f"{parameter_id}: registry value does not match frozen runtime value")

    inputs = registry.get("required_external_inputs_before_real_parameter_calibration")
    if not isinstance(inputs, list) or not inputs:
        errors.append("required external input list must not be empty")

    return RegistryResult("PASS" if not errors else "FAIL", errors, warnings)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    result = validate_registry(registry)
    rendered = json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the Sejong observed-constraint evidence package.

This validator intentionally fails if evidence is promoted to runtime calibration or if
excluded sources are presented as target-corridor observations.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FILES = {
    "hdmap": "sejong_hdmap_status_20260731.json",
    "signal": "sejong_historical_signal_plan_2023.json",
    "probe": "sejong_probe_exclusion_20260731.json",
    "gate": "sejong_observed_input_gate_20260731.json",
}
TARGETS = {"성금교차로", "청사교차로", "세종교차로"}
EXPECTED_HD_MAP_HASHES = {
    "hdmap-happycity-sec02-2017": "ce84bedbc62fbbdb452ac1bfa96fd32865600660ad30951020d53d11634e18b4",
    "hdmap-sangsang-sec001-2021": "ab196fd408b05a17d667b81010c78c80c762db5c6664646e2401ee2d1b5da542",
}
EXPECTED_SIGNAL = {
    "성금교차로": ([45, 45, 25, 45], 160),
    "청사교차로": ([46, 20, 31, 23, 20], 140),
    "세종교차로": ([45, 35, 35, 45], 160),
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    missing = [filename for filename in FILES.values() if not (root / filename).exists()]
    if missing:
        return [f"missing required evidence file: {filename}" for filename in missing]

    hdmap = load(root / FILES["hdmap"])
    signal = load(root / FILES["signal"])
    probe = load(root / FILES["probe"])
    gate = load(root / FILES["gate"])

    if hdmap.get("runtime_activation") != "disabled" or hdmap.get("usable_for_calibration") is not False:
        errors.append("HD-map evidence must remain runtime-disabled and non-calibrating")
    packages = {row.get("package_id"): row for row in hdmap.get("source_packages", [])}
    if set(packages) != set(EXPECTED_HD_MAP_HASHES):
        errors.append("unexpected included HD-map package set")
    for package_id, digest in EXPECTED_HD_MAP_HASHES.items():
        if packages.get(package_id, {}).get("sha256") != digest:
            errors.append(f"HD-map source digest mismatch: {package_id}")
    excluded = hdmap.get("excluded_packages", [])
    if len(excluded) != 1 or excluded[0].get("decision") != "EXCLUDE_FROM_SIMULATION_AND_TARGET_GEOMETRY":
        errors.append("2020 central-park package exclusion must be preserved")
    elif float(excluded[0].get("minimum_corridor_distance_m", 0)) < 400:
        errors.append("excluded HD-map package distance evidence unexpectedly small")

    target_rows = hdmap.get("target_intersections", [])
    if {row.get("name") for row in target_rows} != TARGETS:
        errors.append("HD-map target intersection set is incomplete")
    for row in target_rows:
        if row.get("coverage_status") != "COVERED_FOR_GEOMETRY_QA":
            errors.append(f"target not covered for geometry QA: {row.get('name')}")
        if not row.get("not_yet_derived"):
            errors.append(f"review blockers removed from target: {row.get('name')}")
        if "approved storage length" not in row.get("not_yet_derived", []):
            errors.append(f"storage-length approval blocker missing: {row.get('name')}")
    routes = hdmap.get("corridor_coverage", [])
    if {row.get("route") for row in routes} != {"성금→청사", "청사→세종"}:
        errors.append("corridor coverage rows incomplete")
    for row in routes:
        if row.get("coverage_status") != "CONTINUOUS_CENTERLINE_COVERAGE":
            errors.append(f"corridor coverage not continuous: {row.get('route')}")
        if float(row.get("nearest_hdmap_link_max_distance_m", 999)) > 20:
            errors.append(f"corridor-to-HD-map maximum distance too large: {row.get('route')}")

    if signal.get("runtime_activation") != "disabled" or signal.get("usable_for_calibration") is not False:
        errors.append("historical signal evidence must remain runtime-disabled")
    if signal.get("source", {}).get("sha256") != "1e6e80391c0d5523cd8909b4028ba6061067b2af6690ccf1ee5f9aa2fe87ac10":
        errors.append("signal source digest mismatch")
    rows = {row.get("intersection"): row for row in signal.get("rows", [])}
    if set(rows) != TARGETS:
        errors.append("historical signal target set incomplete")
    for name, (vector, total) in EXPECTED_SIGNAL.items():
        row = rows.get(name, {})
        if row.get("timing_vector_sec") != vector or row.get("nominal_cycle_candidate_sec") != total:
            errors.append(f"historical signal vector mismatch: {name}")
        if row.get("timing_decision_method") != "고정시간제어":
            errors.append(f"unexpected signal-control type: {name}")
    interpretation = signal.get("interpretation", {})
    if interpretation.get("current_2026_operation_claim") is not False:
        errors.append("historical signal data cannot claim 2026 current operation")
    if any(interpretation.get(field) is not False for field in (
        "effective_green_available", "yellow_all_red_decomposition_available", "offset_available", "tod_plan_available"
    )):
        errors.append("unavailable signal-plan fields were promoted")

    if probe.get("runtime_activation") != "excluded" or probe.get("usable_for_calibration") is not False:
        errors.append("probe samples must remain excluded")
    probe_rows = {row.get("source_id"): row for row in probe.get("sources", [])}
    brt = probe_rows.get("sejong-b0-public-sample-20210913", {})
    pvd = probe_rows.get("sejong-pvd-public-sample", {})
    if brt.get("within_100m_count") != 0 or brt.get("decision") != "EXCLUDE_NO_TARGET_LINK_OVERLAP":
        errors.append("B0 target-corridor exclusion evidence changed")
    if pvd.get("within_300m_count") != 0 or pvd.get("decision") != "EXCLUDE_NO_TARGET_LINK_OVERLAP":
        errors.append("PVD target-corridor exclusion evidence changed")

    if gate.get("current_runtime_dataset") != "synthetic-v0" or gate.get("runtime_change_in_this_package") is not False:
        errors.append("observed-input gate must preserve synthetic-v0")
    if gate.get("field_calibration_status") != "HARD_BLOCKED":
        errors.append("field calibration must remain hard-blocked")
    input_statuses = {row.get("input"): row.get("status") for row in gate.get("inputs", [])}
    for required in (
        "same-date 5/15-minute approach and turning counts",
        "current effective signal plan with TOD, offset and clearance",
    ):
        if input_statuses.get(required) != "MISSING_HARD_BLOCKER":
            errors.append(f"hard blocker missing or weakened: {required}")
    decisions = {row.get("item"): row.get("decision") for row in gate.get("completed_decisions", [])}
    if decisions.get("monthly traffic to 5/15-minute conversion") != "DO_NOT_BUILD_FOR_RUNTIME":
        errors.append("monthly traffic disaggregation exclusion must be preserved")
    if gate.get("decision") != "SAFE_EVIDENCE_PIPELINE_COMPLETE_RUNTIME_ACTIVATION_STOPPED":
        errors.append("unexpected final activation decision")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("data/observed/sejong_constraints"),
    )
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("PASS: Sejong evidence is internally consistent and runtime activation is blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

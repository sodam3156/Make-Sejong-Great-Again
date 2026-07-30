#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

DATA_FILES = {
    "cheonan_profiles.json",
    "cheonan_candidate_intersections.json",
    "cheonan_name_join_qa.json",
    "kict_expressway_profiles.json",
    "kict_national_road_profiles.json",
    "kict_near_sejong_stations.json",
    "kict_vehicle_composition.json",
    "jeju_adapter_summaries.json",
    "incheon_signal_cycle_summary_a.json",
    "incheon_signal_cycle_summary_b.json",
}
ALLOWED_SOURCE_CLASSES = {"regional_reference", "external_fixture"}
REPLACEMENT_SLOTS = {
    "sejong_corridor_geometry",
    "sejong_time_resolved_turning_counts",
    "sejong_signal_plan",
    "live_signal_snapshot",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_disabled(obj: dict, label: str, errors: list[str]) -> None:
    if obj.get("runtime_activation") != "disabled":
        errors.append(f"{label}: runtime activation must remain disabled")


def check_profiles(obj: dict, label: str, errors: list[str]) -> None:
    check_disabled(obj, label, errors)
    if set(obj.get("profiles", {})) != {"weekday", "weekend"}:
        errors.append(f"{label}: weekday/weekend profiles required")
        return
    for day_type, profile in obj["profiles"].items():
        if profile.get("source_class") != "regional_reference":
            errors.append(f"{label}/{day_type}: invalid source class")
        if profile.get("usable_for_calibration") is not False:
            errors.append(f"{label}/{day_type}: calibration must remain disabled")
        if profile.get("hours") != list(range(24)):
            errors.append(f"{label}/{day_type}: hours must be 0..23")
        shares = profile.get("normalized_share", [])
        if len(shares) != 24 or abs(sum(shares) - 1.0) > 1e-5:
            errors.append(f"{label}/{day_type}: normalized shares must contain 24 values summing to 1")
        for band in ("p25_share", "p75_share"):
            if len(profile.get(band, [])) != 24:
                errors.append(f"{label}/{day_type}: {band} must contain 24 values")


def validate_package(root: Path) -> list[str]:
    errors: list[str] = []
    required = DATA_FILES | {
        "regional_reference_manifest.json",
        "backend_handoff.json",
        "qa_report.json",
    }
    for name in sorted(required):
        if not (root / name).exists():
            errors.append(f"missing required file: {name}")
    if errors:
        return errors

    manifest = load(root / "regional_reference_manifest.json")
    handoff = load(root / "backend_handoff.json")
    qa = load(root / "qa_report.json")

    if manifest.get("dataset_id") != "regional-reference-v1":
        errors.append("manifest: unexpected dataset_id")
    check_disabled(manifest, "manifest", errors)
    if set(manifest.get("committed_outputs", [])) != DATA_FILES:
        errors.append("manifest: committed output list does not match package")
    if manifest.get("missing_source_ids"):
        errors.append("manifest: committed package cannot record missing sources")
    sources = manifest.get("sources", [])
    if len(sources) != 7:
        errors.append(f"manifest: expected 7 source records, got {len(sources)}")
    for source in sources:
        if source.get("source_class") not in ALLOWED_SOURCE_CLASSES:
            errors.append(f"manifest: invalid source_class for {source.get('source_id')}")
        digest = source.get("sha256", "")
        if source.get("available") is not True or len(digest) != 64:
            errors.append(f"manifest: source unavailable or SHA invalid for {source.get('source_id')}")

    check_profiles(load(root / "cheonan_profiles.json"), "cheonan_profiles", errors)
    check_profiles(load(root / "kict_expressway_profiles.json"), "kict_expressway_profiles", errors)
    check_profiles(load(root / "kict_national_road_profiles.json"), "kict_national_road_profiles", errors)

    candidates = load(root / "cheonan_candidate_intersections.json")
    check_disabled(candidates, "cheonan_candidates", errors)
    rows = candidates.get("candidates", [])
    if [row.get("rank") for row in rows] != list(range(1, 11)):
        errors.append("cheonan_candidates: top-10 ranks must be contiguous")
    for row in rows:
        if row.get("source_class") != "regional_reference" or row.get("usable_for_calibration") is not False:
            errors.append("cheonan_candidates: provenance boundary violated")
            break
        if row.get("limitation") != "topology not verified":
            errors.append("cheonan_candidates: topology limitation missing")
            break

    name_qa = load(root / "cheonan_name_join_qa.json")
    if len(name_qa.get("unmatched", [])) != 3 or name_qa.get("ambiguous") != []:
        errors.append("cheonan_name_join_qa: expected 3 unmatched and 0 ambiguous")

    stations = load(root / "kict_near_sejong_stations.json")
    check_disabled(stations, "kict_stations", errors)
    station_rows = stations.get("stations", [])
    distances = [row.get("distance_km") for row in station_rows]
    if len(station_rows) != 10 or distances != sorted(distances):
        errors.append("kict_stations: expected 10 distance-sorted stations")
    if any(row.get("usable_for_calibration") is not False for row in station_rows):
        errors.append("kict_stations: calibration boundary violated")

    vehicle = load(root / "kict_vehicle_composition.json")
    check_disabled(vehicle, "kict_vehicle", errors)
    if len(vehicle.get("rows", [])) != 4 or len(vehicle.get("class_order", [])) != 12:
        errors.append("kict_vehicle: expected 4 profiles and 12 classes")
    for row in vehicle.get("rows", []):
        if len(row.get("normalized_class_shares", [])) != 12 or abs(sum(row["normalized_class_shares"]) - 1.0) > 1e-5:
            errors.append("kict_vehicle: class shares must sum to 1")

    jeju = load(root / "jeju_adapter_summaries.json")
    check_disabled(jeju, "jeju", errors)
    if jeju.get("source_class") != "external_fixture" or jeju.get("usable_for_calibration") is not False:
        errors.append("jeju: external fixture boundary violated")
    if len(jeju.get("summaries", {}).get("movement", [])) != 4 or len(jeju.get("summaries", {}).get("vehicle", [])) != 7:
        errors.append("jeju: expected 4 movement and 7 vehicle summary rows")

    signal_rows = []
    for name in ("incheon_signal_cycle_summary_a.json", "incheon_signal_cycle_summary_b.json"):
        signal = load(root / name)
        check_disabled(signal, name, errors)
        if signal.get("source_class") != "external_fixture" or signal.get("usable_for_calibration") is not False:
            errors.append(f"{name}: external fixture boundary violated")
        signal_rows.extend(signal.get("rows", []))
    if len(signal_rows) != 30 or {row.get("operation_code") for row in signal_rows} != set("012345"):
        errors.append("incheon signal summaries: expected 30 rows across operation codes 0..5")
    if any(not isinstance(row.get("median"), (int, float)) for row in signal_rows):
        errors.append("incheon signal summaries: nonnumeric median remains")

    check_disabled(handoff, "backend_handoff", errors)
    slots = {row.get("slot") for row in handoff.get("replacement_slots", [])}
    if slots != REPLACEMENT_SLOTS:
        errors.append(f"backend_handoff: unexpected replacement slots {sorted(slots)}")
    if "synthetic-v0" not in handoff.get("activation_rule", ""):
        errors.append("backend_handoff: activation rule must preserve synthetic-v0")

    if qa.get("cheonan", {}).get("daily_sum_mismatch_rows") != 0:
        errors.append("qa: Cheonan daily/hourly mismatch remains")
    if qa.get("jeju", {}).get("intersection_set_difference") != 0:
        errors.append("qa: Jeju intersection sets differ")
    if qa.get("incheon", {}).get("cycle_parse_failures") != 0:
        errors.append("qa: Incheon cycle parse failures remain")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("data/observed/regional_reference"))
    args = parser.parse_args()
    errors = validate_package(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("PASS: regional reference package is consistent and runtime-disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

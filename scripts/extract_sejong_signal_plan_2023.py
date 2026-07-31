#!/usr/bin/env python3
"""Extract the three target intersections from the 2023 Sejong signal standard CSV."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

TARGETS = {"성금교차로", "청사교차로", "세종교차로"}
EXPECTED_SOURCE_SHA256 = "1e6e80391c0d5523cd8909b4028ba6061067b2af6690ccf1ee5f9aa2fe87ac10"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(source: Path, output: Path) -> None:
    digest = sha256(source)
    if digest != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"unexpected signal CSV SHA-256: {digest}")

    rows = []
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["교차로명"].strip() not in TARGETS:
                continue
            vector = [int(value) for value in row["신호등화시간"].split("+")]
            rows.append({
                "intersection": row["교차로명"].strip(),
                "installed_year_month": row["설치년월"].strip(),
                "phase_method": row["신호현시 방식"].strip(),
                "lighting_sequence": row["신호등화순서"].strip(),
                "timing_vector_sec": vector,
                "nominal_cycle_candidate_sec": sum(vector),
                "control_method": row["신호제어방식"].strip(),
                "timing_decision_method": row["신호시간결정방식"].strip(),
            })
    if {row["intersection"] for row in rows} != TARGETS:
        raise ValueError("target signal rows missing")

    value = {
        "dataset_id": "sejong-historical-signal-plan-2023-v1",
        "source": {
            "filename": source.name,
            "sha256": digest,
            "official_reference_date": "2023-05-10",
            "source_class": "official_historical_signal_standard",
            "official_url": "https://www.data.go.kr/data/15113728/fileData.do",
        },
        "runtime_activation": "disabled",
        "usable_for_calibration": False,
        "rows": sorted(rows, key=lambda row: row["intersection"]),
        "interpretation": {
            "timing_vector": "official published lighting-time vector",
            "nominal_cycle_candidate": "arithmetic sum only; not verified as a current TOD cycle",
            "effective_green_available": False,
            "yellow_all_red_decomposition_available": False,
            "offset_available": False,
            "tod_plan_available": False,
            "current_2026_operation_claim": False,
        },
        "allowed_use": ["historical fixed-time scenario after movement and phase mapping review", "signal parser and user-interface display"],
        "forbidden_use": ["2026 current operation", "effective-green calibration", "field replay", "automatic runtime activation"],
        "decision": "HISTORICAL_SIGNAL_AVAILABLE_CURRENT_OPERATION_BLOCKED",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.source, args.output)


if __name__ == "__main__":
    main()

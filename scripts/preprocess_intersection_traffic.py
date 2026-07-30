#!/usr/bin/env python3
"""Preprocess the three RainFlow intersections from the public monthly CSV.

The script does not invent 5/15-minute demand or map public direction labels to
model approach IDs. It produces a traceable subset, aggregate/robust direction
shares, data-quality flags, and a mapping template whose unresolved semantics
remain explicit.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

SOURCE_PATH = Path(
    "data/public/2026-07-29/"
    "세종특별자치시_교차로 방향별 교통 통행량_20230420.csv"
)
SCRIPT_VERSION = "traffic-preprocess-v1"
TARGETS = {
    "성금사거리": "성금교차로",
    "청사교차로": "청사교차로",
    "세종교차로": "세종교차로",
}
DIRECTIONS = (
    ("동", "east"),
    ("서", "west"),
    ("남", "south"),
    ("북", "north"),
)
EXPECTED_MONTHS = tuple(
    [f"2022-{month:02d}" for month in range(5, 13)]
    + [f"2023-{month:02d}" for month in range(1, 4)]
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_source(path: Path) -> tuple[list[dict[str, str]], str, str]:
    raw = path.read_bytes()
    decode_errors: list[str] = []
    for encoding in ("utf-8-sig", "cp949"):
        try:
            text = raw.decode(encoding)
            rows = list(csv.DictReader(text.splitlines()))
            return rows, encoding, sha256_bytes(raw)
        except UnicodeDecodeError as exc:
            decode_errors.append(f"{encoding}: {exc}")
    raise RuntimeError("source decoding failed: " + " | ".join(decode_errors))


def parse_int(value: str | None, *, field: str, context: str) -> int:
    if value is None or value.strip() == "":
        raise RuntimeError(f"missing {field}: {context}")
    try:
        parsed = int(value)
    except ValueError as exc:
        raise RuntimeError(f"non-integer {field}: {context}: {value!r}") from exc
    if parsed < 0:
        raise RuntimeError(f"negative {field}: {context}: {parsed}")
    return parsed


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def rounded_share(numerator: float, denominator: float) -> float:
    if denominator == 0:
        raise RuntimeError("zero denominator while calculating direction share")
    return round(numerator / denominator, 6)


def robust_flags(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["canonical_intersection_name"]].append(row)

    for intersection, group in sorted(grouped.items()):
        for _, direction in DIRECTIONS:
            values = [float(row[f"{direction}_veh"]) for row in group]
            centre = float(median(values))
            deviations = [abs(value - centre) for value in values]
            mad = float(median(deviations))
            if mad == 0:
                continue
            for row, value in zip(group, values, strict=True):
                robust_z = 0.6745 * (value - centre) / mad
                extreme_ratio = value / centre if centre else 0.0
                if abs(robust_z) <= 3.5 and extreme_ratio >= 0.05:
                    continue
                severity = (
                    "LIKELY_DATA_ERROR"
                    if extreme_ratio < 0.05 or extreme_ratio > 20.0
                    else "REVIEW_REQUIRED"
                )
                flags.append(
                    {
                        "canonical_intersection_name": intersection,
                        "month": row["month"],
                        "direction": direction,
                        "value_veh": int(value),
                        "monthly_median_veh": round(centre, 1),
                        "median_absolute_deviation": round(mad, 1),
                        "robust_z": round(robust_z, 3),
                        "value_to_median_ratio": round(extreme_ratio, 4),
                        "severity": severity,
                        "handling": (
                            "EXCLUDE_FROM_SINGLE_MONTH_CALIBRATION_UNTIL_VERIFIED"
                            if severity == "LIKELY_DATA_ERROR"
                            else "RETAIN_RAW_BUT_TEST_WITH_ROBUST_SHARE"
                        ),
                    }
                )
    return sorted(
        flags,
        key=lambda row: (
            row["severity"] != "LIKELY_DATA_ERROR",
            row["canonical_intersection_name"],
            row["month"],
            row["direction"],
        ),
    )


def preprocess(output_dir: Path) -> dict[str, Any]:
    source_rows, source_encoding, source_sha256 = read_source(SOURCE_PATH)
    subset: list[dict[str, Any]] = []

    for row in source_rows:
        source_name = (row.get("교차로명") or "").strip()
        if source_name not in TARGETS:
            continue
        month = (row.get("수집년월") or "").strip()
        context = f"{source_name}/{month}"
        values = {
            direction: parse_int(row.get(korean), field=korean, context=context)
            for korean, direction in DIRECTIONS
        }
        total = parse_int(row.get("교통량 합계"), field="교통량 합계", context=context)
        calculated = sum(values.values())
        if calculated != total:
            raise RuntimeError(
                f"direction sum mismatch {context}: {calculated} != {total}"
            )
        subset.append(
            {
                "source_intersection_name": source_name,
                "canonical_intersection_name": TARGETS[source_name],
                "month": month,
                **{f"{direction}_veh": values[direction] for _, direction in DIRECTIONS},
                "total_veh": total,
                "row_sum_check": "PASS",
                "usage_class": "historical_monthly_observation",
            }
        )

    subset.sort(key=lambda row: (row["canonical_intersection_name"], row["month"]))
    if len(subset) != 33:
        raise RuntimeError(f"target row count {len(subset)} != 33")

    for source_name, canonical_name in TARGETS.items():
        months = tuple(
            row["month"]
            for row in subset
            if row["canonical_intersection_name"] == canonical_name
        )
        if months != EXPECTED_MONTHS:
            raise RuntimeError(
                f"month coverage mismatch for {source_name}: {months!r}"
            )

    flags = robust_flags(subset)
    flag_keys = {
        (row["canonical_intersection_name"], row["month"], row["direction"]): row
        for row in flags
    }

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in subset:
        grouped[row["canonical_intersection_name"]].append(row)

    share_rows: list[dict[str, Any]] = []
    rain_month_rows: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []

    for intersection, group in sorted(grouped.items()):
        total = sum(row["total_veh"] for row in group)
        direction_totals = {
            direction: sum(row[f"{direction}_veh"] for row in group)
            for _, direction in DIRECTIONS
        }
        monthly_share_medians = {
            direction: median(
                [row[f"{direction}_veh"] / row["total_veh"] for row in group]
            )
            for _, direction in DIRECTIONS
        }
        median_share_sum = sum(monthly_share_medians.values())
        share_row: dict[str, Any] = {
            "canonical_intersection_name": intersection,
            "months": len(group),
            "period_start": min(row["month"] for row in group),
            "period_end": max(row["month"] for row in group),
            "total_veh": total,
            "recommended_share_method": "normalized_median_monthly_share",
            "model_input_status": "NOT_READY_DIRECTION_SEMANTICS_PENDING",
        }
        for _, direction in DIRECTIONS:
            share_row[f"{direction}_aggregate_share"] = rounded_share(
                direction_totals[direction], total
            )
            share_row[f"{direction}_median_monthly_share_normalized"] = rounded_share(
                monthly_share_medians[direction], median_share_sum
            )
        share_rows.append(share_row)

        august = next(row for row in group if row["month"] == "2022-08")
        august_row: dict[str, Any] = {
            "canonical_intersection_name": intersection,
            "month": "2022-08",
            "total_veh": august["total_veh"],
            "usage_status": "MONTHLY_CONTEXT_ONLY_NOT_DAY_OR_15MIN_DEMAND",
        }
        for _, direction in DIRECTIONS:
            august_row[f"{direction}_veh"] = august[f"{direction}_veh"]
            august_row[f"{direction}_share"] = rounded_share(
                august[f"{direction}_veh"], august["total_veh"]
            )
            quality = flag_keys.get((intersection, "2022-08", direction))
            august_row[f"{direction}_quality"] = (
                quality["severity"] if quality else "NO_ROBUST_FLAG"
            )
        rain_month_rows.append(august_row)

        for korean, direction in DIRECTIONS:
            mapping_rows.append(
                {
                    "canonical_intersection_name": intersection,
                    "source_direction_label": korean,
                    "normalized_direction": direction,
                    "source_direction_semantics": (
                        "UNCONFIRMED_TRAVEL_DIRECTION_OR_APPROACH_SIDE"
                    ),
                    "model_approach_id": "",
                    "mapping_status": "PENDING",
                    "reason": (
                        "Public metadata does not define whether 동/서/남/북 is "
                        "travel direction, origin approach, or detector placement."
                    ),
                }
            )

    raw_dir = output_dir / "raw_subset"
    processed_dir = output_dir / "processed"
    write_csv(
        raw_dir / "intersection_monthly_direction_202205_202303.csv",
        [
            "source_intersection_name",
            "canonical_intersection_name",
            "month",
            "east_veh",
            "west_veh",
            "south_veh",
            "north_veh",
            "total_veh",
            "row_sum_check",
            "usage_class",
        ],
        subset,
    )
    write_csv(
        processed_dir / "intersection_direction_share.csv",
        list(share_rows[0].keys()),
        share_rows,
    )
    write_csv(
        processed_dir / "rain_month_direction_context_202208.csv",
        list(rain_month_rows[0].keys()),
        rain_month_rows,
    )
    write_csv(
        processed_dir / "traffic_quality_flags.csv",
        list(flags[0].keys()) if flags else ["severity"],
        flags,
    )
    write_csv(
        processed_dir / "intersection_direction_map.csv",
        list(mapping_rows[0].keys()),
        mapping_rows,
    )

    likely_errors = [row for row in flags if row["severity"] == "LIKELY_DATA_ERROR"]
    manifest = {
        "script_version": SCRIPT_VERSION,
        "source": {
            "path": str(SOURCE_PATH),
            "sha256": source_sha256,
            "encoding_used": source_encoding,
            "source_rows": len(source_rows),
            "target_rows": len(subset),
            "period": [EXPECTED_MONTHS[0], EXPECTED_MONTHS[-1]],
        },
        "targets": TARGETS,
        "validation": {
            "target_row_count": len(subset),
            "direction_sum_failures": 0,
            "month_coverage": "PASS",
            "quality_flag_count": len(flags),
            "likely_data_error_count": len(likely_errors),
        },
        "critical_findings": {
            "likely_data_errors": likely_errors,
            "direction_mapping_status": "PENDING_SEMANTICS_CONFIRMATION",
            "time_resolution": "MONTHLY_ONLY",
            "model_input_status": "NOT_READY",
        },
        "allowed_use": [
            "historical intersection scale comparison",
            "direction-share range and sensitivity design",
            "data-quality review",
        ],
        "prohibited_use": [
            "2026 current traffic volume",
            "day-specific or 5/15-minute demand",
            "direct model-approach mapping before direction semantics are confirmed",
            "single-month calibration using a flagged value without verification",
        ],
    }
    (output_dir / "traffic_source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="traffic_reference_output")
    args = parser.parse_args()
    preprocess(Path(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

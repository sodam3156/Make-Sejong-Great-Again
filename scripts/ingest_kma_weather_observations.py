#!/usr/bin/env python3
"""Validate minimized KMA station-239 weather evidence and regenerate inputs.

The committed compact gzip contains only precipitation fields needed for
weather-scenario QA. Original API responses are not committed; their exact
SHA-256 values remain in the observation manifest. This script never estimates
traffic capacity, demand, signal, fairness, or safety parameters.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

STATION_ID = 239
RAIN_DATE = "2022-08-10"
DRY_DATE = "2022-07-27"
VERSION = "kma-observation-compact-v1"
COMPACT_FIELDS = [
    "timestamp_kst", "station_id", "scenario_role", "rain_detection",
    "precip_1m_increment_mm", "precip_15m_mm", "precip_60m_mm", "precip_day_mm",
]
SOURCE_MEMBERS = [
    {"name": "kma_asos_239_20220810_hourly.txt", "sha256": "b9f14f511bbb6558df4fb964d42615358fcedcb54c3cd73885f9beab0eda72a8", "bytes": 9783},
    {"name": "kma_aws_239_20220727_part1.txt", "sha256": "022ef5c4f947333ed2e7b4336a09ae73e9f8d20e8fd614523f5eefcc00bb0064", "bytes": 130178},
    {"name": "kma_aws_239_20220727_part2.txt", "sha256": "558950ea7c4d3195f738711ca7aee12e70f54cc7a6fc4c54a6ff80e96e158e07", "bytes": 60757},
    {"name": "kma_aws_239_20220810_part1.csv", "sha256": "bfb0e37abd6f177138ac7dc82ef7d1b2be9c6240eb729bd7f30f2de662c729a8", "bytes": 116964},
    {"name": "kma_aws_239_20220810_part2.csv", "sha256": "63485566a6fef260d30b8e01dcfe0a823ef69baf1d336b6e9d0083664943e575", "bytes": 26945},
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_compact(path: Path) -> dict[str, list[dict[str, Any]]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != COMPACT_FIELDS:
            raise RuntimeError(f"unexpected compact columns: {reader.fieldnames}")
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for source in reader:
            row = {
                "timestamp": datetime.fromisoformat(source["timestamp_kst"]),
                "station_id": int(source["station_id"]),
                "scenario_role": source["scenario_role"],
                "rain_detection": float(source["rain_detection"]),
                "precip_1m_increment_mm": float(source["precip_1m_increment_mm"]),
                "precip_15m_mm": float(source["precip_15m_mm"]),
                "precip_60m_mm": float(source["precip_60m_mm"]),
                "precip_day_mm": float(source["precip_day_mm"]),
            }
            grouped[row["scenario_role"]].append(row)
    return grouped


def require_day(rows: list[dict[str, Any]], date_kst: str, role: str) -> None:
    if len(rows) != 1440:
        raise RuntimeError(f"{role}: expected 1,440 rows, got {len(rows)}")
    start = datetime.fromisoformat(date_kst + "T00:00:00+09:00")
    end = datetime.fromisoformat(date_kst + "T23:59:00+09:00")
    if rows[0]["timestamp"] != start or rows[-1]["timestamp"] != end:
        raise RuntimeError(f"{role}: incomplete day coverage")
    if {row["station_id"] for row in rows} != {STATION_ID}:
        raise RuntimeError(f"{role}: non-{STATION_ID} station row")
    for left, right in zip(rows, rows[1:]):
        if right["timestamp"] - left["timestamp"] != timedelta(minutes=1):
            raise RuntimeError(f"{role}: minute gap {left['timestamp']} -> {right['timestamp']}")


def validate_rolling(rows: list[dict[str, Any]]) -> None:
    for window, field in ((15, "precip_15m_mm"), (60, "precip_60m_mm")):
        for index, row in enumerate(rows):
            derived = round(sum(item["precip_1m_increment_mm"] for item in rows[max(0, index-window+1):index+1]), 1)
            if abs(derived - row[field]) > 0.051:
                raise RuntimeError(f"{field} mismatch at {row['timestamp']}: {row[field]} vs {derived}")


def load_asos(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 24 or {int(row["station_id"]) for row in rows} != {STATION_ID}:
        raise RuntimeError("ASOS must contain 24 station-239 hourly rows")
    return rows


def aggregate(rows: list[dict[str, Any]], role: str, minutes: int) -> list[dict[str, Any]]:
    bins: dict[datetime, float] = defaultdict(float)
    for row in rows:
        start = row["timestamp"].replace(minute=(row["timestamp"].minute // minutes) * minutes)
        bins[start] += row["precip_1m_increment_mm"]
    return [{
        "scenario_date": start.date().isoformat(),
        "scenario_role": role,
        "resolution_minutes": minutes,
        "interval_start_kst": start.isoformat(),
        "precipitation_mm": f"{amount:.1f}",
        "intensity_equivalent_mm_h": f"{amount * 60 / minutes:.1f}",
        "station_id": STATION_ID,
        "source_class": "observed",
        "source_system": "KMA_AWS_MINUTE_DERIVED",
        "model_input_status": "OBSERVED_WEATHER_INPUT_ONLY_NO_TRAFFIC_PARAMETER_MAPPING",
    } for start, amount in sorted(bins.items())]


def csv_bytes(fields: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader(); writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def write_gzip(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as zipped:
            zipped.write(csv_bytes(fields, rows))


def process(compact: Path, asos_path: Path, output_root: Path) -> dict[str, Any]:
    grouped = load_compact(compact)
    if set(grouped) != {"rain", "dry_reference"}:
        raise RuntimeError(f"unexpected scenario roles: {sorted(grouped)}")
    rain, dry = grouped["rain"], grouped["dry_reference"]
    require_day(rain, RAIN_DATE, "rain")
    require_day(dry, DRY_DATE, "dry_reference")
    validate_rolling(rain); validate_rolling(dry)

    rain_total = round(sum(row["precip_1m_increment_mm"] for row in rain), 1)
    dry_total = round(sum(row["precip_1m_increment_mm"] for row in dry), 1)
    if rain_total != 139.3 or rain[-1]["precip_day_mm"] != 139.3:
        raise RuntimeError(f"unexpected rain total: {rain_total}, {rain[-1]['precip_day_mm']}")
    if dry_total != 0.0 or any(any(row[field] != 0.0 for field in ("rain_detection", "precip_1m_increment_mm", "precip_15m_mm", "precip_60m_mm", "precip_day_mm")) for row in dry):
        raise RuntimeError("dry reference contains precipitation")

    asos = load_asos(asos_path)
    asos_total = float(asos[-1]["precip_day_mm"])
    if asos_total != 139.3 or abs(asos_total - rain_total) > 0.1:
        raise RuntimeError("AWS/ASOS daily cross-check failed")

    scenario_rows: list[dict[str, Any]] = []
    for minutes in (5, 15):
        scenario_rows += aggregate(rain, "rain", minutes)
        scenario_rows += aggregate(dry, "dry_reference", minutes)
    scenario_fields = ["scenario_date", "scenario_role", "resolution_minutes", "interval_start_kst", "precipitation_mm", "intensity_equivalent_mm_h", "station_id", "source_class", "source_system", "model_input_status"]
    scenario_path = output_root / "processed/kma_weather_scenario_inputs.csv.gz"
    write_gzip(scenario_path, scenario_fields, scenario_rows)

    wet = [row for row in rain if row["precip_1m_increment_mm"] > 0]
    max15 = max(row["precip_15m_mm"] for row in rain)
    max60 = max(row["precip_60m_mm"] for row in rain)
    rain5, rain15 = aggregate(rain, "rain", 5), aggregate(rain, "rain", 15)
    max5 = max(float(row["precipitation_mm"]) for row in rain5)
    max15i = max(float(row["precipitation_mm"]) for row in rain15)
    manifest = {
        "schema_version": 3,
        "processor_version": VERSION,
        "station": {"provider": "Korea Meteorological Administration", "station_id": STATION_ID, "station_name": "Sejong"},
        "evidence_storage": {
            "committed_compact_precipitation": str(compact),
            "compact_sha256": sha256_file(compact),
            "original_api_responses_committed": False,
            "original_response_hashes": SOURCE_MEMBERS,
            "reason": "Data minimization: retain exact source hashes and only precipitation fields needed for reproducible scenario QA."
        },
        "rain_observation": {
            "date_kst": RAIN_DATE, "aws_minute_rows": 1440, "asos_hourly_rows": 24, "minute_gaps": 0,
            "aws_daily_precipitation_mm": rain_total, "asos_daily_precipitation_mm": asos_total, "aws_asos_abs_difference_mm": 0.0,
            "first_positive_minute_kst": wet[0]["timestamp"].isoformat(), "last_positive_minute_kst": wet[-1]["timestamp"].isoformat(),
            "max_1m_increment_mm": max(row["precip_1m_increment_mm"] for row in rain),
            "max_15m_rolling_mm": max15, "max_15m_rolling_timestamp_kst": next(row["timestamp"].isoformat() for row in rain if row["precip_15m_mm"] == max15),
            "max_60m_rolling_mm": max60, "max_60m_rolling_timestamp_kst": next(row["timestamp"].isoformat() for row in rain if row["precip_60m_mm"] == max60),
            "max_asos_hourly_mm": max(float(row["precip_hour_mm"] or 0) for row in asos),
            "max_5m_interval_mm": max5, "max_5m_interval_start_kst": next(row["interval_start_kst"] for row in rain5 if float(row["precipitation_mm"]) == max5),
            "max_15m_interval_mm": max15i, "max_15m_interval_start_kst": next(row["interval_start_kst"] for row in rain15 if float(row["precipitation_mm"]) == max15i),
            "status": "OBSERVED_COMPLETE"
        },
        "dry_reference_observation": {
            "date_kst": DRY_DATE, "aws_minute_rows": 1440, "minute_gaps": 0, "aws_daily_precipitation_mm": 0.0,
            "all_precipitation_fields_zero": True,
            "status": "OBSERVED_DRY_DAY_CONFIRMED_CONDITIONAL_ON_ANALYSIS_START_AT_OR_AFTER_06:00_KST",
            "limitation": "Analysis starts before 06:00 require 2022-07-26 data for the preceding-six-hour test."
        },
        "outputs": {"scenario_intervals_gzip": str(scenario_path), "rain_hourly": str(asos_path)},
        "usage": {"allowed": "Observed weather time-series input and weather-source QA.", "not_allowed_without_separate_review": "Traffic capacity, demand, signal, fairness, or safety parameters."},
        "overall_status": "KMA_OBSERVED_RAIN_COMPLETE_DRY_DAY_CONDITIONALLY_CONFIRMED"
    }
    manifest_path = output_root / "observed/kma_observation_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compact", default="data/observed/weather_reference/observed/normalized/kma_aws_239_precipitation_compact.csv.gz")
    parser.add_argument("--asos", default="data/observed/weather_reference/observed/normalized/kma_asos_239_20220810_hourly.csv")
    parser.add_argument("--output-root", default="data/observed/weather_reference")
    args = parser.parse_args()
    print(json.dumps(process(Path(args.compact), Path(args.asos), Path(args.output_root)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

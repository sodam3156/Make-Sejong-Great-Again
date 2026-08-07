#!/usr/bin/env python3
"""Validate compact KMA station-239 evidence and generate weather scenario inputs.

The committed compact JSON stores the 1,440 observed rain-minute increments and a
run-length representation of the verified all-zero dry day. Original API response
hashes are retained for provenance. This script only creates weather time-series
inputs; it never estimates traffic capacity, demand, signal, fairness, or safety
parameters.
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
VERSION = "kma-observation-compact-json-v2"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_close(name: str, actual: float, expected: float, tolerance: float = 0.051) -> None:
    if abs(actual - expected) > tolerance:
        raise RuntimeError(f"{name}: {actual} != {expected}")


def build_minute_rows(compact: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    if compact.get("processor_version") != VERSION:
        raise RuntimeError("unexpected compact processor version")
    station = compact.get("station", {})
    if station.get("station_id") != STATION_ID:
        raise RuntimeError("compact data is not station 239")

    rain = compact["rain"]
    if rain["date_kst"] != RAIN_DATE or rain["row_count"] != 1440 or rain["missing_rows"] != 0:
        raise RuntimeError("rain coverage metadata is incomplete")
    if rain.get("encoding") != "zero_default_sparse_index_value":
        raise RuntimeError("unexpected rain increment encoding")
    increments = [0.0] * 1440
    seen_indices: set[int] = set()
    for index_value in rain["positive_increments_index_value_mm"]:
        if not isinstance(index_value, list) or len(index_value) != 2:
            raise RuntimeError("invalid sparse rain increment entry")
        index, value = int(index_value[0]), float(index_value[1])
        if index < 0 or index >= 1440 or index in seen_indices or value <= 0:
            raise RuntimeError("invalid sparse rain increment index/value")
        seen_indices.add(index)
        increments[index] = value
    if any(value < 0 for value in increments):
        raise RuntimeError("rain increments must be non-negative")
    require_close("rain daily total", round(sum(increments), 1), 139.3, 0.001)

    dry = compact["dry_reference"]
    if dry["date_kst"] != DRY_DATE or dry["row_count"] != 1440 or dry["missing_rows"] != 0:
        raise RuntimeError("dry coverage metadata is incomplete")
    for field, run in dry["zero_run"].items():
        if float(run["value"]) != 0.0 or int(run["count"]) != 1440:
            raise RuntimeError(f"dry zero-run invalid for {field}")

    result: dict[str, list[dict[str, Any]]] = {}
    for role, start_text, values in (
        ("rain", rain["start_kst"], increments),
        ("dry_reference", dry["start_kst"], [0.0] * 1440),
    ):
        start = datetime.fromisoformat(start_text)
        result[role] = [
            {"timestamp": start + timedelta(minutes=index), "precip_1m_increment_mm": value}
            for index, value in enumerate(values)
        ]
    return result


def rolling(rows: list[dict[str, Any]], window: int) -> list[float]:
    values = [float(row["precip_1m_increment_mm"]) for row in rows]
    totals: list[float] = []
    running = 0.0
    for index, value in enumerate(values):
        running += value
        if index >= window:
            running -= values[index - window]
        totals.append(round(running, 1))
    return totals


def load_asos(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 24 or {int(row["station_id"]) for row in rows} != {STATION_ID}:
        raise RuntimeError("ASOS must contain 24 station-239 hourly rows")
    if rows[0]["timestamp_kst"] != "2022-08-10T00:00:00+09:00" or rows[-1]["timestamp_kst"] != "2022-08-10T23:00:00+09:00":
        raise RuntimeError("ASOS hourly coverage is incomplete")
    return rows


def aggregate(rows: list[dict[str, Any]], role: str, minutes: int) -> list[dict[str, Any]]:
    bins: dict[datetime, float] = defaultdict(float)
    for row in rows:
        timestamp: datetime = row["timestamp"]
        start = timestamp.replace(minute=(timestamp.minute // minutes) * minutes)
        bins[start] += float(row["precip_1m_increment_mm"])
    return [
        {
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
        }
        for start, amount in sorted(bins.items())
    ]


def csv_bytes(fields: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def write_gzip(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as zipped:
            zipped.write(csv_bytes(fields, rows))


def process(compact_path: Path, asos_path: Path, expected_manifest_path: Path, output_dir: Path) -> dict[str, Any]:
    compact = load_json(compact_path)
    minute = build_minute_rows(compact)
    rain = minute["rain"]
    dry = minute["dry_reference"]

    rain15 = rolling(rain, 15)
    rain60 = rolling(rain, 60)
    checks = compact["rain"]["source_checks"]
    require_close("max 15m", max(rain15), float(checks["max_api_15m_mm"]), 0.001)
    require_close("max 60m", max(rain60), float(checks["max_api_60m_mm"]), 0.001)
    if rain[rain15.index(max(rain15))]["timestamp"].isoformat() != checks["max_api_15m_timestamp_kst"]:
        raise RuntimeError("max 15m timestamp mismatch")
    if rain[rain60.index(max(rain60))]["timestamp"].isoformat() != checks["max_api_60m_timestamp_kst"]:
        raise RuntimeError("max 60m timestamp mismatch")

    asos = load_asos(asos_path)
    asos_total = float(asos[-1]["precip_day_mm"])
    require_close("AWS/ASOS daily cross-check", sum(row["precip_1m_increment_mm"] for row in rain), asos_total, 0.051)

    scenario_rows: list[dict[str, Any]] = []
    for minutes in (5, 15):
        scenario_rows.extend(aggregate(rain, "rain", minutes))
        scenario_rows.extend(aggregate(dry, "dry_reference", minutes))
    fields = [
        "scenario_date", "scenario_role", "resolution_minutes", "interval_start_kst",
        "precipitation_mm", "intensity_equivalent_mm_h", "station_id", "source_class",
        "source_system", "model_input_status",
    ]
    scenario_path = output_dir / "kma_weather_scenario_inputs.csv.gz"
    write_gzip(scenario_path, fields, scenario_rows)

    rain5 = aggregate(rain, "rain", 5)
    rain15_intervals = aggregate(rain, "rain", 15)
    positive = [row for row in rain if row["precip_1m_increment_mm"] > 0]
    generated = {
        "processor_version": VERSION,
        "compact_sha256": sha256_file(compact_path),
        "rain_observation": {
            "date_kst": RAIN_DATE,
            "aws_minute_rows": 1440,
            "asos_hourly_rows": 24,
            "minute_gaps": 0,
            "daily_precipitation_mm": round(sum(row["precip_1m_increment_mm"] for row in rain), 1),
            "first_positive_minute_kst": positive[0]["timestamp"].isoformat(),
            "last_positive_minute_kst": positive[-1]["timestamp"].isoformat(),
            "max_1m_increment_mm": max(row["precip_1m_increment_mm"] for row in rain),
            "max_15m_rolling_mm": max(rain15),
            "max_60m_rolling_mm": max(rain60),
            "max_asos_hourly_mm": max(float(row["precip_hour_mm"] or 0) for row in asos),
            "max_5m_interval_mm": max(float(row["precipitation_mm"]) for row in rain5),
            "max_15m_interval_mm": max(float(row["precipitation_mm"]) for row in rain15_intervals),
        },
        "dry_reference_observation": {
            "date_kst": DRY_DATE,
            "aws_minute_rows": 1440,
            "minute_gaps": 0,
            "daily_precipitation_mm": 0.0,
            "status": "CONDITIONALLY_CONFIRMED_FOR_ANALYSIS_START_AT_OR_AFTER_06:00_KST",
        },
        "scenario_output": str(scenario_path),
        "scenario_rows": len(scenario_rows),
        "usage_limit": "WEATHER_INPUT_ONLY_NO_TRAFFIC_PARAMETER_MAPPING",
    }

    expected = load_json(expected_manifest_path)
    expected_rain = expected["rain_observation"]
    comparisons = {
        "aws_minute_rows": (generated["rain_observation"]["aws_minute_rows"], expected_rain["aws_minute_rows"]),
        "asos_hourly_rows": (generated["rain_observation"]["asos_hourly_rows"], expected_rain["asos_hourly_rows"]),
        "daily_precipitation_mm": (generated["rain_observation"]["daily_precipitation_mm"], expected_rain["aws_daily_precipitation_mm"]),
        "max_15m_rolling_mm": (generated["rain_observation"]["max_15m_rolling_mm"], expected_rain["max_15m_rolling_mm"]),
        "max_60m_rolling_mm": (generated["rain_observation"]["max_60m_rolling_mm"], expected_rain["max_60m_rolling_mm"]),
        "max_5m_interval_mm": (generated["rain_observation"]["max_5m_interval_mm"], expected_rain["max_5m_interval_mm"]),
        "max_15m_interval_mm": (generated["rain_observation"]["max_15m_interval_mm"], expected_rain["max_15m_interval_mm"]),
    }
    for key, (actual, expected_value) in comparisons.items():
        if actual != expected_value:
            raise RuntimeError(f"manifest mismatch for {key}: {actual} != {expected_value}")
    if expected["dry_reference_observation"]["aws_minute_rows"] != 1440 or expected["dry_reference_observation"]["aws_daily_precipitation_mm"] != 0.0:
        raise RuntimeError("dry manifest mismatch")

    report_path = output_dir / "kma_validation_report.json"
    report_path.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return generated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compact", default="data/observed/weather_reference/observed/normalized/kma_aws_239_precipitation_compact.json")
    parser.add_argument("--asos", default="data/observed/weather_reference/observed/normalized/kma_asos_239_20220810_hourly.csv")
    parser.add_argument("--expected-manifest", default="data/observed/weather_reference/observed/kma_observation_manifest.json")
    parser.add_argument("--output-dir", default="weather_reference_output/kma_observed")
    args = parser.parse_args()
    result = process(Path(args.compact), Path(args.asos), Path(args.expected_manifest), Path(args.output_dir))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

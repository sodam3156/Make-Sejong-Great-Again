#!/usr/bin/env python3
"""Validate temporal, regional, and usage compatibility of scenario evidence.

This gate does not estimate or approve traffic, signal, safety, or fairness
parameters. It only prevents evidence from being presented or consumed beyond
its documented temporal resolution, spatial role, and usage class.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

DIRECT_WEATHER_USAGE = "DIRECT_WEATHER_TIME_SERIES_INPUT"
TRAFFIC_CONTEXT_USAGE = "DIRECTION_SHARE_CONTEXT_ONLY"
SPATIAL_IDENTITY_USAGE = "SPATIAL_IDENTITY_AND_CONNECTIVITY_ONLY"
HISTORICAL_SIGNAL_USAGE = "HISTORICAL_CLASSIFICATION_ONLY"
WEATHER_ONLY_STATUS = "OBSERVED_WEATHER_INPUT_ONLY_NO_TRAFFIC_PARAMETER_MAPPING"


@dataclass(frozen=True)
class ValidationResult:
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


def _require_mapping(parent: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be an object")
        return {}
    return value


def _parse_date(value: Any, field: str, errors: list[str]) -> date | None:
    if not isinstance(value, str):
        errors.append(f"{field} must be an ISO date string")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{field} must use YYYY-MM-DD")
        return None


def _parse_datetime(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{field} must be an ISO datetime string")
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{field} must be a valid ISO datetime")
        return None
    if parsed.utcoffset() is None:
        errors.append(f"{field} must include an explicit UTC offset")
        return None
    return parsed


def _parse_clock(value: Any, field: str, errors: list[str]) -> time | None:
    if not isinstance(value, str):
        errors.append(f"{field} must be an HH:MM string")
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        errors.append(f"{field} must use HH:MM")
        return None


def validate_manifest(manifest: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    scenario_date = _parse_date(manifest.get("scenario_date"), "scenario_date", errors)
    analysis_start = _parse_datetime(
        manifest.get("analysis_start_kst"), "analysis_start_kst", errors
    )
    if scenario_date and analysis_start and analysis_start.date() != scenario_date:
        errors.append("analysis_start_kst date must equal scenario_date")

    region = _require_mapping(manifest, "region", errors)
    weather = _require_mapping(manifest, "weather", errors)
    traffic = _require_mapping(manifest, "traffic", errors)
    signal = _require_mapping(manifest, "signal", errors)
    spatial = _require_mapping(manifest, "spatial", errors)
    claims = _require_mapping(manifest, "claims", errors)
    dry_reference = _require_mapping(manifest, "dry_reference", errors)

    # Regional compatibility: make the accepted station-to-target distance explicit.
    try:
        actual_distance = float(region.get("weather_station_max_target_distance_km"))
        allowed_distance = float(region.get("weather_station_allowed_distance_km"))
        if actual_distance < 0 or allowed_distance <= 0:
            raise ValueError
        if actual_distance > allowed_distance:
            errors.append(
                "weather station exceeds the manifest's allowed target distance"
            )
    except (TypeError, ValueError):
        errors.append("region weather-station distance fields must be positive numbers")

    # Weather may be a direct input only when it is an observation on the scenario date.
    weather_date = _parse_date(weather.get("observation_date"), "weather.observation_date", errors)
    weather_class = weather.get("source_class")
    weather_usage = weather.get("usage_class")
    weather_system = weather.get("source_system")
    if weather_usage == DIRECT_WEATHER_USAGE:
        if weather_class != "observed":
            errors.append("direct weather input must have source_class=observed")
        if not isinstance(weather_system, str) or not weather_system.startswith("KMA_"):
            errors.append("direct observed weather input must identify a KMA source system")
        if scenario_date and weather_date and weather_date != scenario_date:
            errors.append("direct weather observation date must equal scenario_date")
    if weather_class == "reanalysis_proxy" and weather_usage != "SCREENING_AND_SENSITIVITY_ONLY":
        errors.append("reanalysis proxy may only be used for screening and sensitivity")

    # Monthly direction totals are contextual evidence, not an intraday demand trace.
    traffic_start = _parse_date(
        traffic.get("source_period_start"), "traffic.source_period_start", errors
    )
    traffic_end = _parse_date(
        traffic.get("source_period_end"), "traffic.source_period_end", errors
    )
    if traffic_start and traffic_end and traffic_start > traffic_end:
        errors.append("traffic source period start must not be after its end")
    if scenario_date and traffic_start and traffic_end:
        if not (traffic_start <= scenario_date <= traffic_end):
            errors.append("traffic source period does not contain scenario_date")

    traffic_resolution = traffic.get("resolution")
    traffic_usage = traffic.get("usage_class")
    same_date_traffic = traffic.get("same_date_observation") is True
    if traffic_resolution == "monthly_direction_total":
        if traffic_usage != TRAFFIC_CONTEXT_USAGE:
            errors.append("monthly direction totals must be direction-share context only")
        if same_date_traffic:
            errors.append("monthly direction totals cannot be marked as same-date observations")
        if claims.get("same_date_traffic_calibration") is True:
            errors.append("monthly traffic cannot support same-date traffic calibration")
        if claims.get("traffic_parameter_mapping") is True:
            errors.append("monthly traffic cannot directly map absolute model demand")
        warnings.append(
            "monthly traffic supports direction-share context only; scenario remains observation-constrained synthetic"
        )
    elif traffic_usage == "DIRECT_TRAFFIC_CALIBRATION":
        if traffic_resolution not in {"5min", "15min", "hourly"}:
            errors.append("direct traffic calibration requires 5min, 15min, or hourly data")
        if not same_date_traffic:
            errors.append("direct traffic calibration requires a same-date observation")

    # Historical signal classification cannot be promoted to a current operating plan.
    reference_year = signal.get("reference_year")
    claimed_current_year = signal.get("claimed_current_year")
    if not isinstance(reference_year, int):
        errors.append("signal.reference_year must be an integer")
    if signal.get("usage_class") == HISTORICAL_SIGNAL_USAGE and signal.get("included_as_model_input") is True:
        errors.append("historical signal classification cannot be used as a signal-plan input")
    if claims.get("current_signal_plan") is True:
        if not isinstance(claimed_current_year, int):
            errors.append("current signal-plan claim requires signal.claimed_current_year")
        elif reference_year != claimed_current_year:
            errors.append("signal reference year does not match the claimed current year")

    # Newer node/link data may identify geometry, but not rewrite historical operations.
    if spatial.get("usage_class") != SPATIAL_IDENTITY_USAGE:
        errors.append("spatial reference is limited to identity and connectivity")
    if spatial.get("used_for_historical_operating_state") is True:
        errors.append("spatial reference cannot infer a historical operating state")

    # The current evidence package is weather-input-only.
    if manifest.get("model_input_status") == WEATHER_ONLY_STATUS:
        if claims.get("traffic_parameter_mapping") is True:
            errors.append("weather-only status conflicts with traffic parameter mapping")
        if signal.get("included_as_model_input") is True:
            errors.append("weather-only status conflicts with a signal-plan input")
    elif manifest.get("model_input_status") != "MATCHED_OBSERVED_REPLAY_CANDIDATE":
        errors.append("unrecognized model_input_status")

    if claims.get("field_replay") is True:
        if weather_usage != DIRECT_WEATHER_USAGE:
            errors.append("field replay requires direct observed weather")
        if traffic_usage != "DIRECT_TRAFFIC_CALIBRATION" or not same_date_traffic:
            errors.append("field replay requires same-date calibrated traffic")
        if signal.get("included_as_model_input") is not True:
            errors.append("field replay requires an explicit signal-plan input")

    # The dry-day bundle begins at midnight, so its preceding-six-hour proof is
    # valid only for analysis starts at or after 06:00 unless the prior day is added.
    dry_start = _parse_datetime(
        dry_reference.get("analysis_start_kst"),
        "dry_reference.analysis_start_kst",
        errors,
    )
    minimum_clock = _parse_clock(
        dry_reference.get("minimum_start_for_local_day_6h_check"),
        "dry_reference.minimum_start_for_local_day_6h_check",
        errors,
    )
    if dry_start and minimum_clock and dry_reference.get("prior_day_data_available") is not True:
        if dry_start.timetz().replace(tzinfo=None) < minimum_clock:
            errors.append(
                "dry-reference start is earlier than the verified preceding-six-hour window"
            )

    status = "PASS" if not errors else "FAIL"
    return ValidationResult(status=status, errors=errors, warnings=warnings)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = validate_manifest(manifest)
    rendered = json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

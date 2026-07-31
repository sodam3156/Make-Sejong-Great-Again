"""Read-only service and router for regional reference data.

These endpoints expose evidence and adapter fixtures only. They never mutate simulation
inputs or activate observed calibration.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "data" / "observed" / "regional_reference"
router = APIRouter(prefix="/api/reference", tags=["reference-data"])


def _load(name: str) -> dict[str, Any]:
    path = PACKAGE_ROOT / name
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def source_status() -> dict[str, Any]:
    manifest = _load("regional_reference_manifest.json")
    handoff = _load("backend_handoff.json")
    qa = _load("qa_report.json")
    return {
        "datasetId": manifest["dataset_id"],
        "runtimeActivation": "disabled",
        "availableSources": [
            {
                "sourceId": row["source_id"],
                "sourceClass": row["source_class"],
                "sourceRegion": row["source_region"],
                "filename": row["filename"],
                "sha256": row["sha256"],
            }
            for row in manifest["sources"]
            if row["available"]
        ],
        "replacementSlots": [
            {
                "slot": row["slot"],
                "status": row["status"],
                "requiredFields": row["required_fields"],
            }
            for row in handoff["replacement_slots"]
        ],
        "qa": qa,
        "limitations": manifest["limitations"],
    }


PROFILE_FILES = {
    "cheonan": "cheonan_profiles.json",
    "kict_expressway": "kict_expressway_profiles.json",
    "kict_national_road": "kict_national_road_profiles.json",
}


def traffic_hourly_profile(source: str, day_type: str) -> dict[str, Any]:
    if source not in PROFILE_FILES:
        raise KeyError(source)
    data = _load(PROFILE_FILES[source])
    if day_type not in data["profiles"]:
        raise KeyError(day_type)
    profile = data["profiles"][day_type]
    return {
        "datasetId": data["dataset_id"],
        "source": source,
        "dayType": day_type,
        "sourceClass": profile["source_class"],
        "sourceRegion": profile["source_region"],
        "usableForCalibration": False,
        "runtimeActivation": "disabled",
        "profile": profile,
        "limitations": [
            "Reference temporal shape only.",
            "Do not convert to absolute Sejong BASE_DEMAND without observed turning counts and review.",
        ],
    }


def _period_for_hour(hour: int) -> str:
    if hour <= 5:
        return "overnight"
    if hour <= 9:
        return "morning_peak"
    if hour <= 15:
        return "daytime"
    if hour <= 19:
        return "evening_peak"
    return "late_evening"


def traffic_reference_schedule(source: str, day_type: str) -> dict[str, Any]:
    """Convert an observed reference profile into a directly consumable 24-hour schedule.

    The multiplier has a daily mean of 1.0. It is suitable for UI playback and an
    explicitly reviewed demand-shape adapter, but it is not an absolute Sejong demand.
    """
    wrapped = traffic_hourly_profile(source, day_type)
    profile = wrapped["profile"]
    hours = profile["hours"]
    shares = profile["normalized_share"]
    p25 = profile["p25_share"]
    p75 = profile["p75_share"]
    daily_mean_share = 1.0 / 24.0

    rows = [
        {
            "hour": hour,
            "period": _period_for_hour(hour),
            "normalizedShare": share,
            "demandMultiplier": share / daily_mean_share,
            "p25Multiplier": low / daily_mean_share,
            "p75Multiplier": high / daily_mean_share,
        }
        for hour, share, low, high in zip(hours, shares, p25, p75, strict=True)
    ]

    morning_rows = [row for row in rows if 6 <= row["hour"] <= 10]
    evening_rows = [row for row in rows if 15 <= row["hour"] <= 19]
    peak_row = max(rows, key=lambda row: row["demandMultiplier"])
    morning_peak = max(morning_rows, key=lambda row: row["demandMultiplier"])
    evening_peak = max(evening_rows, key=lambda row: row["demandMultiplier"])

    return {
        "datasetId": wrapped["datasetId"],
        "scheduleId": f"{source}-{day_type}-reference-schedule-v1",
        "source": source,
        "dayType": day_type,
        "sourceClass": wrapped["sourceClass"],
        "sourceRegion": wrapped["sourceRegion"],
        "usableForCalibration": False,
        "runtimeActivation": "disabled",
        "dailyMeanMultiplier": 1.0,
        "peakSummary": {
            "overallHour": peak_row["hour"],
            "overallMultiplier": peak_row["demandMultiplier"],
            "morningHour": morning_peak["hour"],
            "morningMultiplier": morning_peak["demandMultiplier"],
            "eveningHour": evening_peak["hour"],
            "eveningMultiplier": evening_peak["demandMultiplier"],
        },
        "rows": rows,
        "consumerContract": {
            "timeZone": "Asia/Seoul",
            "stepMinutes": 60,
            "multiplierField": "demandMultiplier",
            "allowedUse": "reference playback or separately reviewed temporal-shape adapter",
            "forbiddenUse": "absolute Sejong demand calibration or automatic simulator activation",
        },
        "limitations": wrapped["limitations"],
    }


def similar_intersections(limit: int = 10, min_daily_volume: float | None = None) -> dict[str, Any]:
    data = _load("cheonan_candidate_intersections.json")
    rows = data["candidates"]
    if min_daily_volume is not None:
        rows = [row for row in rows if row["median_daily_volume"] >= min_daily_volume]
    rows = rows[:limit]
    return {
        "datasetId": data["dataset_id"],
        "sourceClass": "regional_reference",
        "sourceRegion": "Cheonan",
        "usableForCalibration": False,
        "runtimeActivation": "disabled",
        "selectionFeatures": [
            "approach_count",
            "median_daily_volume",
            "maximum_approach_share",
            "morning_peak_hour",
            "evening_peak_hour",
        ],
        "rows": rows,
        "limitations": [
            "First-stage data shortlist only.",
            "Road spacing, signal coordination, lane-group geometry and corridor topology are not verified.",
        ],
    }


def vehicle_composition() -> dict[str, Any]:
    data = _load("kict_vehicle_composition.json")
    return {
        "datasetId": data["dataset_id"],
        "sourceClass": data["source_class"],
        "sourceRegion": data["source_region"],
        "usableForCalibration": False,
        "runtimeActivation": "disabled",
        "classOrder": data["class_order"],
        "rows": data["rows"],
        "limitations": ["Nearby-road reference range; not Sejong intersection vehicle mix."],
    }


def movement_fixture() -> dict[str, Any]:
    data = _load("jeju_adapter_summaries.json")
    return {
        "datasetId": data["dataset_id"],
        "sourceClass": "external_fixture",
        "sourceRegion": "Jeju",
        "usableForCalibration": False,
        "runtimeActivation": "disabled",
        "movement": data["summaries"]["movement"],
        "vehicle": data["summaries"]["vehicle"],
        "limitations": ["Parser and visualization fixture only; not a Sejong calibration input."],
    }


def signal_cycle_fixture(operation_code: str | None = None, cycle_field: str | None = None) -> dict[str, Any]:
    rows = _load("incheon_signal_cycle_summary_a.json")["rows"] + _load("incheon_signal_cycle_summary_b.json")["rows"]
    if operation_code is not None:
        rows = [row for row in rows if row["operation_code"] == operation_code]
    if cycle_field is not None:
        rows = [row for row in rows if row["cycle_field"] == cycle_field]
    return {
        "datasetId": "incheon-signal-cycle-fixture-v1",
        "sourceClass": "external_fixture",
        "sourceRegion": "Incheon",
        "usableForCalibration": False,
        "runtimeActivation": "disabled",
        "rows": rows,
        "limitations": ["Signal parser and TOD visualization fixture only; not the Sejong signal plan."],
    }


@router.get("/source-status", summary="참조자료 확보·QA·교체 슬롯 상태")
def get_source_status() -> dict[str, Any]:
    try:
        return source_status()
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=503, detail="reference package unavailable") from error


@router.get("/traffic-hourly-profile", summary="지역 참조 24시간 수요형상")
def get_traffic_hourly_profile(
    source: Literal["cheonan", "kict_expressway", "kict_national_road"] = "cheonan",
    day_type: Literal["weekday", "weekend"] = "weekday",
) -> dict[str, Any]:
    return traffic_hourly_profile(source, day_type)


@router.get("/traffic-reference-schedule", summary="툴 소비용 실제자료 기반 24시간 수요 배율")
def get_traffic_reference_schedule(
    source: Literal["cheonan", "kict_expressway", "kict_national_road"] = "cheonan",
    day_type: Literal["weekday", "weekend"] = "weekday",
) -> dict[str, Any]:
    return traffic_reference_schedule(source, day_type)


@router.get("/similar-intersections", summary="천안 실측자료 기반 유사 교차로 1차 후보")
def get_similar_intersections(
    limit: int = Query(default=10, ge=1, le=10),
    min_daily_volume: float | None = Query(default=None, ge=0),
) -> dict[str, Any]:
    return similar_intersections(limit=limit, min_daily_volume=min_daily_volume)


@router.get("/vehicle-composition", summary="세종 인접도로 차종 구성 참조")
def get_vehicle_composition() -> dict[str, Any]:
    return vehicle_composition()


@router.get("/movement-fixture", summary="회전·차종 adapter 기능검증 자료")
def get_movement_fixture() -> dict[str, Any]:
    return movement_fixture()


@router.get("/signal-cycle-fixture", summary="신호주기·TOD parser 기능검증 자료")
def get_signal_cycle_fixture(
    operation_code: str | None = Query(default=None, pattern="^[0-5]$"),
    cycle_field: str | None = Query(default=None),
) -> dict[str, Any]:
    return signal_cycle_fixture(operation_code, cycle_field)

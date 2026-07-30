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

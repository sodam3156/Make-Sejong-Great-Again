"""Read-only UTIC adapter contracts and probe metadata endpoints."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

from .utic_signal import RESERVATION_REQUIRED_FIELDS

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "data" / "observed" / "regional_reference" / "utic_signal_service_contract.json"
router = APIRouter(prefix="/api/reference", tags=["reference-data"])


@lru_cache(maxsize=1)
def _official_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


@router.get(
    "/utic-reservation-contract",
    summary="UTIC 예약계획 응답 계약과 온라인 프로브 상태",
)
def utic_reservation_contract() -> dict:
    return {
        "adapter": "utic_reservation_plan_v1",
        "sourceClass": "external_live_fixture",
        "sourceRegion": "Daegu",
        "usableForCalibration": False,
        "runtimeActivation": "disabled",
        "requiredSourceFields": sorted(RESERVATION_REQUIRED_FIELDS),
        "onlineProbe": {
            "status": "success",
            "resultCode": "0",
            "resultMessage": "NORMAL_SERVICE",
            "pageNo": 1,
            "numOfRows": 100,
            "totalCount": 63890,
            "totalPages": 639,
            "sourceSnapshotCollectedAt": "2026-07-27 10:05:32",
            "recordsCommitted": False,
        },
        "qaRules": [
            "Reject nonzero resultCode.",
            "Reject records missing required fields.",
            "Preserve reservation control code 0 as undocumented.",
            "Never activate simulator inputs from this adapter.",
        ],
        "limitations": [
            "Reservation-plan records are not a Sejong signal plan.",
            "They are not live phase state or remaining-time data.",
            "The online response body is not committed until locally sanitized.",
        ],
    }


@router.get(
    "/utic-signal-service-contract",
    summary="도로교통공단 공식 UTIC 신호 서비스 명세",
)
def utic_signal_service_contract() -> dict:
    try:
        return _official_contract()
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=503, detail="UTIC signal service contract unavailable") from error

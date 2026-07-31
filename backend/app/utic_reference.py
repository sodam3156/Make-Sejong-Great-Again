"""Read-only UTIC adapter contract and probe metadata endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from .utic_signal import REQUIRED_FIELDS

router = APIRouter(prefix="/api/reference", tags=["reference-data"])


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
        "requiredSourceFields": sorted(REQUIRED_FIELDS),
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

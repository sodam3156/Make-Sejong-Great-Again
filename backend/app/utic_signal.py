"""Normalize UTIC reservation-plan responses for read-only adapter tests."""
from __future__ import annotations

from typing import Any

REQUIRED_FIELDS = {
    "REGION_CD",
    "INT_NO",
    "INT_NM",
    "RESRV_NO",
    "RESRV_CONTRL_CD",
    "RESRV_STRT_HH",
    "RESRV_STRT_MI",
    "RESRV_END_HH",
    "RESRV_END_MI",
    "COLLCT_DTIME",
}


def _as_int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be integer-compatible") from error


def normalize_reservation_response(payload: list[dict[str, Any]]) -> dict[str, Any]:
    if not payload or not isinstance(payload[0], dict):
        raise ValueError("response must be a non-empty JSON array")

    metadata = payload[0]
    if str(metadata.get("resultCode")) != "0":
        raise ValueError(f"service error: {metadata.get('resultMsg', 'unknown')}")

    rows: list[dict[str, Any]] = []
    for index, source in enumerate(payload[1:], start=1):
        missing = REQUIRED_FIELDS - set(source)
        if missing:
            raise ValueError(f"record {index} missing fields: {sorted(missing)}")

        code = str(source["RESRV_CONTRL_CD"])
        start_hour = _as_int(source["RESRV_STRT_HH"], "RESRV_STRT_HH")
        start_minute = _as_int(source["RESRV_STRT_MI"], "RESRV_STRT_MI")
        end_hour = _as_int(source["RESRV_END_HH"], "RESRV_END_HH")
        end_minute = _as_int(source["RESRV_END_MI"], "RESRV_END_MI")
        rows.append(
            {
                "regionCode": str(source["REGION_CD"]),
                "intersectionNo": str(source["INT_NO"]),
                "intersectionName": str(source["INT_NM"]),
                "reservationNo": str(source["RESRV_NO"]),
                "reservationControlCode": code,
                "startHour": start_hour,
                "startMinute": start_minute,
                "endHour": end_hour,
                "endMinute": end_minute,
                "collectedAt": str(source["COLLCT_DTIME"]),
                "activeWindowConfigured": any(
                    (start_hour, start_minute, end_hour, end_minute)
                ),
                "qaFlags": ["UNDOCUMENTED_CONTROL_CODE_0"] if code == "0" else [],
            }
        )

    return {
        "sourceClass": "external_live_fixture",
        "usableForCalibration": False,
        "runtimeActivation": "disabled",
        "response": {
            "pageNo": _as_int(metadata.get("pageNo", 0), "pageNo"),
            "numOfRows": _as_int(metadata.get("numOfRows", 0), "numOfRows"),
            "totalCount": _as_int(metadata.get("totCount", 0), "totCount"),
            "totalPages": _as_int(metadata.get("totPage", 0), "totPage"),
            "resultCode": str(metadata.get("resultCode")),
            "resultMessage": str(metadata.get("resultMsg")),
        },
        "rows": rows,
        "limitations": [
            "Reservation-plan adapter data is not a Sejong signal plan.",
            "It is not live phase state or remaining-time data.",
            "No simulator input or threshold may be activated from this output.",
        ],
    }

"""Normalize UTIC signal-plan responses for read-only adapter tests."""
from __future__ import annotations

from typing import Any

RESERVATION_REQUIRED_FIELDS = {
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

# Backward-compatible alias for the first adapter revision.
REQUIRED_FIELDS = RESERVATION_REQUIRED_FIELDS

OPERATING_PLAN_REQUIRED_FIELDS = {
    "REGION_CD",
    "INT_NO",
    "INT_NM",
    "INT_PLAN_NO",
    "INT_PLAN_IDX_NO",
    "OPER_PLAN_HH",
    "OPER_PLAN_MI",
    "INT_OPER_CYCLE_VAL",
    "INT_OPER_OFFSET_VAL",
    "COLLCT_DTIME",
    *(f"A_RING_{index}_PHASE_VAL" for index in range(1, 9)),
    *(f"B_RING_{index}_PHASE_VAL" for index in range(1, 9)),
}

SIGNAL_MAP_REQUIRED_FIELDS = {
    "REGION_CD",
    "INT_NO",
    "INT_NM",
    "RING_NO",
    "PLAN_TP",
    "STEP_NO",
    "MIN_TM",
    "MAX_TM",
    "EOP",
    *(f"CAR{index}" for index in range(1, 9)),
    *(f"PED{index}" for index in range(1, 9)),
}

PLAN_TYPE_LABELS = {
    "0": "GENERAL",
    "1": "TIME_DIFFERENCE_1",
    "2": "TIME_DIFFERENCE_2",
    "3": "TIME_DIFFERENCE_3",
    "4": "TIME_DIFFERENCE_4",
    "5": "TIME_DIFFERENCE_5",
    "6": "PEDESTRIAN_MAP",
}


def _as_int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be integer-compatible") from error


def _metadata(payload: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not payload or not isinstance(payload[0], dict):
        raise ValueError("response must be a non-empty JSON array")
    metadata = payload[0]
    if str(metadata.get("resultCode")) != "0":
        raise ValueError(f"service error: {metadata.get('resultMsg', 'unknown')}")
    return metadata, payload[1:]


def _response_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "pageNo": _as_int(metadata.get("pageNo", 0), "pageNo"),
        "numOfRows": _as_int(metadata.get("numOfRows", 0), "numOfRows"),
        "totalCount": _as_int(metadata.get("totCount", 0), "totCount"),
        "totalPages": _as_int(metadata.get("totPage", 0), "totPage"),
        "resultCode": str(metadata.get("resultCode")),
        "resultMessage": str(metadata.get("resultMsg")),
    }


def _ensure_fields(source: dict[str, Any], required: set[str], index: int) -> None:
    missing = required - set(source)
    if missing:
        raise ValueError(f"record {index} missing fields: {sorted(missing)}")


def normalize_reservation_response(payload: list[dict[str, Any]]) -> dict[str, Any]:
    metadata, source_rows = _metadata(payload)
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(source_rows, start=1):
        _ensure_fields(source, RESERVATION_REQUIRED_FIELDS, index)
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
                "activeWindowConfigured": any((start_hour, start_minute, end_hour, end_minute)),
                "qaFlags": ["UNDOCUMENTED_CONTROL_CODE_0"] if code == "0" else [],
            }
        )
    return {
        "sourceClass": "external_live_fixture",
        "usableForCalibration": False,
        "runtimeActivation": "disabled",
        "response": _response_metadata(metadata),
        "rows": rows,
        "limitations": [
            "Reservation-plan adapter data is not a Sejong signal plan.",
            "It is not live phase state or remaining-time data.",
            "No simulator input or threshold may be activated from this output.",
        ],
    }


def normalize_operating_plan_response(payload: list[dict[str, Any]]) -> dict[str, Any]:
    """Normalize getPlanCROPInfo cycle, offset and A/B ring phase values."""
    metadata, source_rows = _metadata(payload)
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(source_rows, start=1):
        _ensure_fields(source, OPERATING_PLAN_REQUIRED_FIELDS, index)
        cycle = _as_int(source["INT_OPER_CYCLE_VAL"], "INT_OPER_CYCLE_VAL")
        ring_a = [
            _as_int(source[f"A_RING_{phase}_PHASE_VAL"], f"A_RING_{phase}_PHASE_VAL")
            for phase in range(1, 9)
        ]
        ring_b = [
            _as_int(source[f"B_RING_{phase}_PHASE_VAL"], f"B_RING_{phase}_PHASE_VAL")
            for phase in range(1, 9)
        ]
        qa_flags: list[str] = []
        if sum(ring_a) not in (0, cycle):
            qa_flags.append("A_RING_PHASE_SUM_CYCLE_MISMATCH")
        if sum(ring_b) not in (0, cycle):
            qa_flags.append("B_RING_PHASE_SUM_CYCLE_MISMATCH")
        rows.append(
            {
                "regionCode": str(source["REGION_CD"]),
                "intersectionNo": str(source["INT_NO"]),
                "intersectionName": str(source["INT_NM"]),
                "planNo": str(source["INT_PLAN_NO"]),
                "planIndexNo": str(source["INT_PLAN_IDX_NO"]),
                "startHour": _as_int(source["OPER_PLAN_HH"], "OPER_PLAN_HH"),
                "startMinute": _as_int(source["OPER_PLAN_MI"], "OPER_PLAN_MI"),
                "cycleSec": cycle,
                "offsetSec": _as_int(source["INT_OPER_OFFSET_VAL"], "INT_OPER_OFFSET_VAL"),
                "ringAPhaseSec": ring_a,
                "ringBPhaseSec": ring_b,
                "ringASumSec": sum(ring_a),
                "ringBSumSec": sum(ring_b),
                "collectedAt": str(source["COLLCT_DTIME"]),
                "qaFlags": qa_flags,
            }
        )
    return {
        "sourceClass": "external_live_fixture",
        "usableForCalibration": False,
        "runtimeActivation": "disabled",
        "response": _response_metadata(metadata),
        "rows": rows,
        "limitations": [
            "Operating plans are from UTIC-supported external cities, not the Sejong corridor.",
            "Phase values require crossDetailInfo and SIGNALMAP before movement semantics can be assigned.",
            "No simulator input or threshold may be activated from this output.",
        ],
    }


def normalize_signal_map_response(payload: list[dict[str, Any]]) -> dict[str, Any]:
    """Normalize getSigMapCRInfo signal-map steps for parser and visualization tests."""
    metadata, source_rows = _metadata(payload)
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(source_rows, start=1):
        _ensure_fields(source, SIGNAL_MAP_REQUIRED_FIELDS, index)
        plan_type = str(source["PLAN_TP"])
        rows.append(
            {
                "regionCode": str(source["REGION_CD"]),
                "intersectionNo": str(source["INT_NO"]),
                "intersectionName": str(source["INT_NM"]),
                "ringNo": _as_int(source["RING_NO"], "RING_NO"),
                "planType": plan_type,
                "planTypeLabel": PLAN_TYPE_LABELS.get(plan_type, "UNKNOWN"),
                "stepNo": _as_int(source["STEP_NO"], "STEP_NO"),
                "vehicleSignals": [
                    _as_int(source[f"CAR{signal}"], f"CAR{signal}") for signal in range(1, 9)
                ],
                "pedestrianSignals": [
                    _as_int(source[f"PED{signal}"], f"PED{signal}") for signal in range(1, 9)
                ],
                "minimumSec": _as_int(source["MIN_TM"], "MIN_TM"),
                "maximumSec": _as_int(source["MAX_TM"], "MAX_TM"),
                "endOfPhase": _as_int(source["EOP"], "EOP"),
                "qaFlags": [] if plan_type in PLAN_TYPE_LABELS else ["UNDOCUMENTED_PLAN_TYPE"],
            }
        )
    return {
        "sourceClass": "external_live_fixture",
        "usableForCalibration": False,
        "runtimeActivation": "disabled",
        "response": _response_metadata(metadata),
        "rows": rows,
        "limitations": [
            "SIGNALMAP records are external-city function-test data, not a Sejong signal map.",
            "Signal-number movement semantics require the crossDetailInfo workbook.",
            "No simulator input or threshold may be activated from this output.",
        ],
    }

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.utic_signal import (
    normalize_operating_plan_response,
    normalize_signal_map_response,
)
from backend.reference_api import app


def metadata(count: str = "1") -> dict[str, str]:
    return {
        "totCount": count,
        "pageNo": "1",
        "resultCode": "0",
        "numOfRows": "10",
        "totPage": "1",
        "resultMsg": "NORMAL_SERVICE",
    }


def operating_plan_payload() -> list[dict[str, str]]:
    row = {
        "REGION_CD": "L02",
        "INT_NO": "5033",
        "INT_NM": "fixture-intersection",
        "INT_PLAN_NO": "1",
        "INT_PLAN_IDX_NO": "1",
        "OPER_PLAN_HH": "6",
        "OPER_PLAN_MI": "0",
        "INT_OPER_CYCLE_VAL": "180",
        "INT_OPER_OFFSET_VAL": "10",
        "COLLCT_DTIME": "2022-11-19 01:00:37",
    }
    values = [77, 25, 38, 40, 0, 0, 0, 0]
    for ring in ("A", "B"):
        for phase, value in enumerate(values, start=1):
            row[f"{ring}_RING_{phase}_PHASE_VAL"] = str(value)
    return [metadata(), row]


def signal_map_payload() -> list[dict[str, str]]:
    row = {
        "REGION_CD": "L02",
        "INT_NO": "5033",
        "INT_NM": "fixture-intersection",
        "RING_NO": "1",
        "PLAN_TP": "0",
        "STEP_NO": "10",
        "MIN_TM": "30",
        "MAX_TM": "30",
        "EOP": "1",
    }
    for signal in range(1, 9):
        row[f"CAR{signal}"] = "0"
        row[f"PED{signal}"] = "0"
    return [metadata(), row]


def test_operating_plan_normalizer_checks_cycle_and_ring_sums():
    result = normalize_operating_plan_response(operating_plan_payload())
    row = result["rows"][0]

    assert row["cycleSec"] == 180
    assert row["offsetSec"] == 10
    assert row["ringASumSec"] == 180
    assert row["ringBSumSec"] == 180
    assert row["qaFlags"] == []
    assert result["usableForCalibration"] is False
    assert result["runtimeActivation"] == "disabled"


def test_signal_map_normalizer_exposes_eight_vehicle_and_pedestrian_channels():
    result = normalize_signal_map_response(signal_map_payload())
    row = result["rows"][0]

    assert row["planTypeLabel"] == "GENERAL"
    assert len(row["vehicleSignals"]) == 8
    assert len(row["pedestrianSignals"]) == 8
    assert row["minimumSec"] == 30
    assert result["runtimeActivation"] == "disabled"


def test_official_service_contract_endpoint_contains_real_operations_and_hashes():
    client = TestClient(app)
    response = client.get("/api/reference/utic-signal-service-contract")

    assert response.status_code == 200
    body = response.json()
    operations = {service["operation"] for service in body["services"]}
    assert {
        "crossInfo",
        "crossDetailInfo",
        "getPlanCRHDInfo",
        "getPlanCRWDInfo",
        "getPlanCRRSInfo",
        "getPlanCROPInfo",
        "getSigMapCRInfo",
    } <= operations
    assert len(body["source_documents"]) == 3
    assert all(len(document["sha256"]) == 64 for document in body["source_documents"])
    assert body["code_definitions"]["RESRV_CONTRL_CD"]["0"] == "UNDOCUMENTED"
    assert body["tool_use"]["usable_for_calibration"] is False
    assert body["tool_use"]["runtime_activation"] == "disabled"
    assert client.post("/api/reference/utic-signal-service-contract").status_code == 405

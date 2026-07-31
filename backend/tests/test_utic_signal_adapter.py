from __future__ import annotations

import pytest

from backend.app.utic_signal import normalize_reservation_response


def sample_payload() -> list[dict[str, str]]:
    return [
        {
            "totCount": "2",
            "pageNo": "1",
            "resultCode": "0",
            "numOfRows": "100",
            "totPage": "1",
            "resultMsg": "NORMAL_SERVICE",
        },
        {
            "REGION_CD": "L29",
            "INT_NO": "100",
            "INT_NM": "fixture-intersection-a",
            "RESRV_NO": "1",
            "RESRV_CONTRL_CD": "0",
            "RESRV_STRT_HH": "0",
            "RESRV_STRT_MI": "0",
            "RESRV_END_HH": "0",
            "RESRV_END_MI": "0",
            "COLLCT_DTIME": "2026-07-27 10:05:32",
        },
        {
            "REGION_CD": "L29",
            "INT_NO": "101",
            "INT_NM": "fixture-intersection-b",
            "RESRV_NO": "1",
            "RESRV_CONTRL_CD": "2",
            "RESRV_STRT_HH": "0",
            "RESRV_STRT_MI": "30",
            "RESRV_END_HH": "4",
            "RESRV_END_MI": "30",
            "COLLCT_DTIME": "2026-07-27 10:05:32",
        },
    ]


def test_normalizes_reservation_contract_without_runtime_activation():
    result = normalize_reservation_response(sample_payload())

    assert result["sourceClass"] == "external_live_fixture"
    assert result["usableForCalibration"] is False
    assert result["runtimeActivation"] == "disabled"
    assert result["response"] == {
        "pageNo": 1,
        "numOfRows": 100,
        "totalCount": 2,
        "totalPages": 1,
        "resultCode": "0",
        "resultMessage": "NORMAL_SERVICE",
    }
    assert len(result["rows"]) == 2


def test_preserves_undocumented_zero_and_detects_active_window():
    rows = normalize_reservation_response(sample_payload())["rows"]

    assert rows[0]["qaFlags"] == ["UNDOCUMENTED_CONTROL_CODE_0"]
    assert rows[0]["activeWindowConfigured"] is False
    assert rows[1]["qaFlags"] == []
    assert rows[1]["activeWindowConfigured"] is True
    assert (rows[1]["startHour"], rows[1]["startMinute"]) == (0, 30)
    assert (rows[1]["endHour"], rows[1]["endMinute"]) == (4, 30)


def test_rejects_service_error_and_incomplete_records():
    failed = sample_payload()
    failed[0]["resultCode"] = "30"
    failed[0]["resultMsg"] = "SERVICE_ERROR"
    with pytest.raises(ValueError, match="service error"):
        normalize_reservation_response(failed)

    incomplete = sample_payload()
    del incomplete[1]["INT_NO"]
    with pytest.raises(ValueError, match="missing fields"):
        normalize_reservation_response(incomplete)

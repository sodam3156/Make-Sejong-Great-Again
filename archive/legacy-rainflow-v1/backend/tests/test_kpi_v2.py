"""QA-canonical unit tests for rainflow-kpi-v2 and rainflow-guard-v2."""
from __future__ import annotations

import pytest

from backend.app.main import build_run
from backend.app.safety import evaluate_guard
from backend.app.simulation import (
    DT,
    DURATION,
    KPI_DEFINITION_VERSION,
    PARAMETER_SET_VERSION,
    SimResult,
    _accumulate_spillback,
    _advance_recovery_window,
    _clearance_proxy,
    run_simulation,
)


def _result(delays: dict[str, float]) -> SimResult:
    result = SimResult("rain_spillback_a", 42, "no_action")
    result.approach_p95_delay = delays
    return result


def test_spillback_counts_corridor_wall_clock_not_link_seconds():
    result = _result({})

    _accumulate_spillback(result, {"L12": True, "L23": True})

    assert result.spillback_time_sec == DT
    assert result.spillback_link_seconds == {"L12": DT, "L23": DT}


def test_spillback_never_exceeds_run_duration():
    result = run_simulation("rain_spillback_a", 42, "no_action")

    assert 0 <= result.spillback_time_sec <= DURATION


def test_recovery_requires_sixty_continuous_seconds():
    started = None
    recovered = None
    for t in range(2700, 2755, DT):  # 55 seconds of calm
        started, recovered = _advance_recovery_window(started, t=t, calm=True)
        assert recovered is None

    started, recovered = _advance_recovery_window(started, t=2755, calm=False)
    assert (started, recovered) == (None, None)

    for t in range(2760, 2820, DT):  # full 60-second calm window
        started, recovered = _advance_recovery_window(started, t=t, calm=True)

    assert recovered == 2760


def test_unrecovered_run_is_censored_not_reported_as_observed_recovery():
    result = run_simulation("rain_spillback_a", 42, "no_action")

    assert result.recovery_time_sec == 900
    assert result.recovery_observed is False


def test_bypass_time_is_included_in_headline_vehicle_seconds():
    result = run_simulation("rain_spillback_a", 42, "corridor_gating")

    assert result.diverted_vehicles > 0
    assert result.diversion_freeflow_seconds > 0
    assert result.total_travel_time_sec == round(
        result.modeled_vehicle_seconds + result.diversion_freeflow_seconds,
        0,
    )


def test_clearance_proxy_reflects_metered_service():
    unmetered = _clearance_proxy(queue_veh=10, effective_service=1.0)
    metered = _clearance_proxy(queue_veh=10, effective_service=0.45)

    assert metered > unmetered


def test_fairness_uses_baseline_in_numerator_and_floor_only_in_denominator():
    baseline = _result({"R1_N": 10.0})
    candidate = _result({"R1_N": 20.0})

    guard = evaluate_guard(candidate, baseline)

    violation = next(
        item for item in guard["violations"]
        if item["code"] == "FAIRNESS_P95_EXCEEDED"
    )
    assert violation["observed_pct"] == pytest.approx(33.3)


def test_missing_fairness_input_is_invalid_not_zero():
    baseline = _result({"R1_N": 10.0})
    candidate = _result({})

    guard = evaluate_guard(candidate, baseline)

    assert "FAIRNESS_INPUT_INVALID" in {
        item["code"] for item in guard["violations"]
    }


def test_run_declares_v2_parameter_kpi_and_guard_versions():
    run = build_run("rain_spillback_a", 42)
    reproducibility = run["reproducibility"]

    assert reproducibility["parameter_set_version"] == PARAMETER_SET_VERSION
    assert reproducibility["kpi_definition_version"] == KPI_DEFINITION_VERSION
    assert reproducibility["guard_version"] == "rainflow-guard-v2"
    assert len(reproducibility["result_checksum"]) == 64

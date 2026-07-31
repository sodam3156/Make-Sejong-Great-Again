"""Exact-boundary regression tests for provisional policy and guard rules."""
from __future__ import annotations

import math

import pytest

from backend.app.policies import metering_factors
from backend.app.safety import (
    DATA_STALE_LIMIT_SEC,
    DIVERSION_DELAY_LIMIT_SEC,
    FAIRNESS_P95_LIMIT_PCT,
    evaluate_guard,
    operational_violations,
)
from backend.app.simulation import ALL_APPROACHES, SimResult


def _result(
    *,
    delay: float = 100.0,
    diversion: float = 0.0,
    hard_brakes: int = 0,
) -> SimResult:
    result = SimResult("rain_spillback_a", 1, "corridor_gating")
    result.approach_p95_delay = {"R1_N": delay}
    result.diversion_delay_sec = diversion
    result.hard_brakes = hard_brakes
    return result


def _codes(guard: dict) -> set[str]:
    return {violation["code"] for violation in guard["violations"]}


def test_corridor_gating_starts_only_above_occupancy_threshold():
    at_limit = metering_factors(
        "corridor_gating",
        in_rain=True,
        link_occupancy={"L12": 0.80, "L23": 0.0},
        approaches=ALL_APPROACHES,
    )
    above_limit = metering_factors(
        "corridor_gating",
        in_rain=True,
        link_occupancy={"L12": math.nextafter(0.80, math.inf), "L23": 0.0},
        approaches=ALL_APPROACHES,
    )
    at_full_occupancy = metering_factors(
        "corridor_gating",
        in_rain=True,
        link_occupancy={"L12": 1.0, "L23": 0.0},
        approaches=ALL_APPROACHES,
    )

    assert at_limit["R1_N"] == 1.0
    assert above_limit["R1_N"] < 1.0
    assert at_full_occupancy["R1_N"] == pytest.approx(0.35)


def test_fairness_exact_limit_passes_and_small_value_above_fails():
    baseline = _result(delay=100.0)
    exact_delay = 100.0 * (1.0 + FAIRNESS_P95_LIMIT_PCT / 100.0)

    exact = evaluate_guard(_result(delay=exact_delay), baseline)
    above = evaluate_guard(
        _result(delay=exact_delay + 1e-9),
        baseline,
    )

    assert "FAIRNESS_P95_EXCEEDED" not in _codes(exact)
    assert "FAIRNESS_P95_EXCEEDED" in _codes(above)


def test_diversion_exact_limit_passes_and_small_value_above_fails():
    baseline = _result()

    exact = evaluate_guard(
        _result(diversion=DIVERSION_DELAY_LIMIT_SEC),
        baseline,
    )
    above = evaluate_guard(
        _result(diversion=DIVERSION_DELAY_LIMIT_SEC + 1e-9),
        baseline,
    )

    assert "DIVERSION_DELAY_EXCEEDED" not in _codes(exact)
    assert "DIVERSION_DELAY_EXCEEDED" in _codes(above)


def test_hard_brake_proxy_equality_passes_and_one_more_fails():
    baseline = _result(hard_brakes=7)

    exact = evaluate_guard(_result(hard_brakes=7), baseline)
    above = evaluate_guard(_result(hard_brakes=8), baseline)

    assert "HARD_BRAKE_PROXY_DEGRADED" not in _codes(exact)
    assert "HARD_BRAKE_PROXY_DEGRADED" in _codes(above)


def test_stale_exact_limit_passes_and_first_value_above_fails():
    exact = operational_violations(
        {
            "data_age_sec": DATA_STALE_LIMIT_SEC,
            "sensor_available": True,
            "device_status": "ok",
        }
    )
    above = operational_violations(
        {
            "data_age_sec": math.nextafter(
                DATA_STALE_LIMIT_SEC, math.inf
            ),
            "sensor_available": True,
            "device_status": "ok",
        }
    )

    assert "DATA_STALE" not in {
        violation["code"] for violation in exact
    }
    assert "DATA_STALE" in {
        violation["code"] for violation in above
    }

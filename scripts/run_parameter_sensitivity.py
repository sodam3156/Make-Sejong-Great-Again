"""Run a reproducible, internal-only OAT sensitivity sweep.

This runner is evidence about the behavior of the provisional synthetic queue
model.  It is not independent validation, field calibration, a safety
certification, or evidence of an effect on real Sejong traffic.

Example:

    python scripts/run_parameter_sensitivity.py \
        --output-prefix /tmp/rainflow_parameter_sensitivity \
        --verify-repeat

The command writes ``.json``, ``.csv``, and ``.sha256`` files.  The JSON and
CSV contain the input, row, result-set, environment, source, and Git
fingerprints needed to repeat or compare a run.  The sidecar hashes the exact
JSON and CSV bytes because a file cannot contain its own SHA-256 digest.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import math
import platform
import statistics
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.app import policies, safety, simulation  # noqa: E402

RUNNER_VERSION = "rainflow-internal-oat-v1"
VALIDATION_STATUS = "internal_exploratory_non_independent"
CLAIM_BOUNDARY = (
    "Provisional synthetic-model sensitivity only. This is not independent "
    "validation, field calibration, a safety certification, or evidence of "
    "real Sejong traffic performance."
)
SCENARIOS = ("rain_spillback_a", "rain_spillback_b")
SEEDS = tuple(range(1, 11))
POLICY_IDS = ("no_action", "fixed_metering", "corridor_gating")


@dataclass(frozen=True)
class ParameterSpec:
    parameter: str
    category: str
    nominal: float
    low: float
    high: float
    unit: str
    scope: str


PARAMETERS = (
    ParameterSpec(
        "heavy_capacity_factor", "rain_demand", 0.84, 0.80, 0.88, "ratio",
        "both scenarios during the heavy-rain phase",
    ),
    ParameterSpec(
        "moderate_capacity_factor", "rain_demand", 0.89, 0.85, 0.93, "ratio",
        "both scenarios during the moderate-rain transition",
    ),
    ParameterSpec(
        "scenario_a_surge", "rain_demand", 1.10, 1.05, 1.15, "ratio",
        "rain_spillback_a only",
    ),
    ParameterSpec(
        "scenario_b_surge", "rain_demand", 1.18, 1.10, 1.25, "ratio",
        "rain_spillback_b only",
    ),
    ParameterSpec(
        "l12_storage", "queue", 22.0, 18.0, 26.0, "vehicle",
        "L12 synthetic storage",
    ),
    ParameterSpec(
        "l23_storage", "queue", 18.0, 14.0, 22.0, "vehicle",
        "L23 synthetic storage before the scenario-B incident multiplier",
    ),
    ParameterSpec(
        "bypass_storage", "queue", 60.0, 40.0, 80.0, "vehicle",
        "BYPASS synthetic storage",
    ),
    ParameterSpec(
        "jam_occupancy", "queue", 0.95, 0.85, 0.99, "ratio",
        "capacity-drop activation occupancy",
    ),
    ParameterSpec(
        "capacity_drop", "queue", 0.70, 0.50, 0.90, "ratio",
        "downstream discharge multiplier after jam activation",
    ),
    ParameterSpec(
        "fixed_meter_factor", "policy", 0.45, 0.35, 0.55, "ratio",
        "fixed-metering negative-control entry multiplier",
    ),
    ParameterSpec(
        "gating_start_occupancy", "policy", 0.80, 0.70, 0.90, "ratio",
        "corridor-gating activation occupancy",
    ),
    ParameterSpec(
        "gating_min_factor", "policy", 0.35, 0.25, 0.45, "ratio",
        "corridor-gating minimum entry multiplier",
    ),
    ParameterSpec(
        "recovery_occupancy_limit", "recovery", 0.50, 0.40, 0.60, "ratio",
        "maximum L12/L23 occupancy for a calm recovery sample",
    ),
    ParameterSpec(
        "recovery_queue_limit", "recovery", 5.0, 3.0, 7.0, "vehicle",
        "maximum external queue for a calm recovery sample",
    ),
    ParameterSpec(
        "recovery_hold_seconds", "recovery", 60.0, 30.0, 120.0, "second",
        "continuous calm period required for observed recovery",
    ),
    ParameterSpec(
        "fairness_p95_limit_pct", "guard", 15.0, 10.0, 20.0, "percent",
        "candidate P95 delay worsening limit",
    ),
    ParameterSpec(
        "fairness_noise_floor_seconds", "guard", 30.0, 15.0, 60.0, "second",
        "fairness percentage denominator floor",
    ),
    ParameterSpec(
        "diversion_delay_limit_seconds", "guard", 180.0, 120.0, 240.0,
        "second", "candidate-minus-baseline diversion delay limit",
    ),
    ParameterSpec(
        "data_stale_limit_seconds", "guard", 120.0, 60.0, 180.0, "second",
        "operational guard at a fixed 120-second data-age stress input",
    ),
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes().replace(b"\r\n", b"\n"))


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _git_identity() -> dict[str, Any]:
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    return {
        "commit_sha": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(status),
        "status_porcelain_sha256": _sha256_bytes(
            status.replace("\r\n", "\n").encode("utf-8")
        ),
        "dirty_paths": [
            line[3:] for line in status.splitlines() if len(line) >= 4
        ],
    }


def _source_identity() -> dict[str, Any]:
    relative_paths = (
        "backend/app/simulation.py",
        "backend/app/policies.py",
        "backend/app/safety.py",
        "scripts/run_parameter_sensitivity.py",
    )
    files = {
        relative: _sha256_file(ROOT / relative)
        for relative in relative_paths
    }
    return {
        "files": files,
        "combined_sha256": _sha256_json(files),
        "versions": {
            "simulator_version": simulation.SIMULATOR_VERSION,
            "parameter_set_version": simulation.PARAMETER_SET_VERSION,
            "kpi_definition_version": simulation.KPI_DEFINITION_VERSION,
            "guard_version": safety.RULE_VERSION,
            "runner_version": RUNNER_VERSION,
        },
    }


def _environment_identity() -> dict[str, Any]:
    details = {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "byteorder": sys.byteorder,
    }
    return {
        **details,
        "fingerprint_sha256": _sha256_json(details),
    }


def _parameterized_metering(
    *,
    original,
    fixed_factor: float | None = None,
    gating_start: float | None = None,
    gating_floor: float | None = None,
):
    def metering_factors(
        policy_id: str,
        *,
        in_rain: bool,
        link_occupancy: dict[str, float],
        approaches: tuple[str, ...] | list[str],
    ) -> dict[str, float]:
        if policy_id not in policies.POLICIES:
            raise ValueError(f"unknown policy_id: {policy_id}")

        if policy_id == "fixed_metering" and fixed_factor is not None:
            meter = original(
                policy_id,
                in_rain=in_rain,
                link_occupancy=link_occupancy,
                approaches=approaches,
            )
            if in_rain:
                meter["R2_S"] = fixed_factor
                meter["R1_W"] = fixed_factor
            return meter

        if (
            policy_id == "corridor_gating"
            and (gating_start is not None or gating_floor is not None)
        ):
            meter = {approach: 1.0 for approach in approaches}
            start = 0.80 if gating_start is None else gating_start
            floor = 0.35 if gating_floor is None else gating_floor
            for link_id, upstreams in (
                ("L23", ("R2_N", "R2_S")),
                ("L12", ("R1_N", "R1_W")),
            ):
                occupancy = link_occupancy[link_id]
                if occupancy > start:
                    span = 1.0 - start
                    factor = max(
                        floor,
                        1.0
                        - (occupancy - start)
                        / span
                        * (1.0 - floor),
                    )
                    for approach in upstreams:
                        meter[approach] = min(meter[approach], factor)
            return meter

        return original(
            policy_id,
            in_rain=in_rain,
            link_occupancy=link_occupancy,
            approaches=approaches,
        )

    return metering_factors


def _assert_nominal_metering_parity() -> None:
    clones = (
        _parameterized_metering(
            original=policies.metering_factors,
            fixed_factor=0.45,
        ),
        _parameterized_metering(
            original=policies.metering_factors,
            gating_start=0.80,
        ),
        _parameterized_metering(
            original=policies.metering_factors,
            gating_floor=0.35,
        ),
    )
    approaches = tuple(simulation.ALL_APPROACHES)
    for cloned in clones:
        for policy_id in policies.POLICIES:
            for in_rain in (False, True):
                for l12 in (0.0, 0.80, 0.81, 0.95, 1.0):
                    for l23 in (0.0, 0.80, 0.81, 0.95, 1.0):
                        kwargs = {
                            "in_rain": in_rain,
                            "link_occupancy": {"L12": l12, "L23": l23},
                            "approaches": approaches,
                        }
                        expected = policies.metering_factors(
                            policy_id, **kwargs
                        )
                        actual = cloned(policy_id, **kwargs)
                        same = (
                            actual.keys() == expected.keys()
                            and all(
                                math.isclose(
                                    actual[key],
                                    expected[key],
                                    rel_tol=0.0,
                                    abs_tol=1e-12,
                                )
                                for key in expected
                            )
                        )
                        if not same:
                            raise RuntimeError(
                                "nominal metering clone diverges from "
                                f"production: {policy_id=} {in_rain=} "
                                f"{l12=} {l23=}"
                            )


def _case_definitions() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = [
        {
            "case_id": "nominal",
            "parameter": "all",
            "category": "nominal",
            "position": "nominal",
            "value": None,
            "nominal": None,
            "unit": None,
            "scope": "all production provisional values",
        }
    ]
    for spec in PARAMETERS:
        for position in ("low", "high"):
            cases.append(
                {
                    "case_id": f"{spec.parameter}__{position}",
                    "parameter": spec.parameter,
                    "category": spec.category,
                    "position": position,
                    "value": getattr(spec, position),
                    "nominal": spec.nominal,
                    "unit": spec.unit,
                    "scope": spec.scope,
                }
            )
    return cases


@contextmanager
def _applied_case(case: dict[str, Any]) -> Iterator[dict[str, Any]]:
    original = {
        "rain_capacity_factor": copy.deepcopy(simulation.RAIN_CAPACITY_FACTOR),
        "links": copy.deepcopy(simulation.LINKS),
        "scenarios": copy.deepcopy(simulation.SCENARIOS),
        "jam_occupancy": simulation.JAM_OCC,
        "capacity_drop": simulation.CAPACITY_DROP,
        "recovery_occupancy_limit": simulation.RECOVERY_OCCUPANCY_LIMIT,
        "recovery_queue_limit": simulation.RECOVERY_QUEUE_LIMIT,
        "recovery_hold_seconds": simulation.RECOVERY_HOLD_SEC,
        "metering_factors": simulation.metering_factors,
        "fairness_p95_limit_pct": safety.FAIRNESS_P95_LIMIT_PCT,
        "fairness_noise_floor_seconds": safety.P95_NOISE_FLOOR_SEC,
        "diversion_delay_limit_seconds": safety.DIVERSION_DELAY_LIMIT_SEC,
        "data_stale_limit_seconds": safety.DATA_STALE_LIMIT_SEC,
    }
    quality = {
        "data_age_sec": 0.0,
        "sensor_available": True,
        "device_status": "ok",
    }
    try:
        parameter = case["parameter"]
        value = case["value"]
        if parameter == "heavy_capacity_factor":
            simulation.RAIN_CAPACITY_FACTOR["heavy"] = value
        elif parameter == "moderate_capacity_factor":
            simulation.RAIN_CAPACITY_FACTOR["moderate"] = value
        elif parameter == "scenario_a_surge":
            simulation.SCENARIOS["rain_spillback_a"]["surge"] = value
        elif parameter == "scenario_b_surge":
            simulation.SCENARIOS["rain_spillback_b"]["surge"] = value
        elif parameter == "l12_storage":
            simulation.LINKS["L12"] = value
        elif parameter == "l23_storage":
            simulation.LINKS["L23"] = value
        elif parameter == "bypass_storage":
            simulation.LINKS["BYPASS"] = value
        elif parameter == "jam_occupancy":
            simulation.JAM_OCC = value
        elif parameter == "capacity_drop":
            simulation.CAPACITY_DROP = value
        elif parameter in {
            "fixed_meter_factor",
            "gating_start_occupancy",
            "gating_min_factor",
        }:
            simulation.metering_factors = _parameterized_metering(
                original=original["metering_factors"],
                fixed_factor=(
                    value if parameter == "fixed_meter_factor" else None
                ),
                gating_start=(
                    value
                    if parameter == "gating_start_occupancy"
                    else None
                ),
                gating_floor=(
                    value if parameter == "gating_min_factor" else None
                ),
            )
        elif parameter == "recovery_occupancy_limit":
            simulation.RECOVERY_OCCUPANCY_LIMIT = value
        elif parameter == "recovery_queue_limit":
            simulation.RECOVERY_QUEUE_LIMIT = value
        elif parameter == "recovery_hold_seconds":
            simulation.RECOVERY_HOLD_SEC = value
        elif parameter == "fairness_p95_limit_pct":
            safety.FAIRNESS_P95_LIMIT_PCT = value
        elif parameter == "fairness_noise_floor_seconds":
            safety.P95_NOISE_FLOOR_SEC = value
        elif parameter == "diversion_delay_limit_seconds":
            safety.DIVERSION_DELAY_LIMIT_SEC = value
        elif parameter == "data_stale_limit_seconds":
            safety.DATA_STALE_LIMIT_SEC = value
            quality["data_age_sec"] = 120.0
        elif parameter != "all":
            raise ValueError(f"unhandled OAT parameter: {parameter}")
        yield quality
    finally:
        simulation.RAIN_CAPACITY_FACTOR = original["rain_capacity_factor"]
        simulation.LINKS = original["links"]
        simulation.SCENARIOS = original["scenarios"]
        simulation.JAM_OCC = original["jam_occupancy"]
        simulation.CAPACITY_DROP = original["capacity_drop"]
        simulation.RECOVERY_OCCUPANCY_LIMIT = original[
            "recovery_occupancy_limit"
        ]
        simulation.RECOVERY_QUEUE_LIMIT = original["recovery_queue_limit"]
        simulation.RECOVERY_HOLD_SEC = original["recovery_hold_seconds"]
        simulation.metering_factors = original["metering_factors"]
        safety.FAIRNESS_P95_LIMIT_PCT = original["fairness_p95_limit_pct"]
        safety.P95_NOISE_FLOOR_SEC = original[
            "fairness_noise_floor_seconds"
        ]
        safety.DIVERSION_DELAY_LIMIT_SEC = original[
            "diversion_delay_limit_seconds"
        ]
        safety.DATA_STALE_LIMIT_SEC = original["data_stale_limit_seconds"]


def _pct(candidate: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    return round((candidate - baseline) / baseline * 100.0, 1)


def _result_payload(
    result: simulation.SimResult,
    baseline: simulation.SimResult,
    guard: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "kpi": {
            "spillback_time_sec": result.spillback_time_sec,
            "recovery_time_sec": result.recovery_time_sec,
            "recovery_observed": result.recovery_observed,
            "total_travel_time_sec": result.total_travel_time_sec,
            "worst_approach_delay_sec": result.worst_approach_delay_sec,
        },
        "diagnostics": {
            "spillback_events": result.spillback_events,
            "spillback_link_seconds": result.spillback_link_seconds,
            "modeled_vehicle_seconds": result.modeled_vehicle_seconds,
            "completed_trips": result.completed_trips,
            "diversion_delay_sec": result.diversion_delay_sec,
            "diverted_vehicles": result.diverted_vehicles,
            "diversion_vehicle_seconds": result.diversion_vehicle_seconds,
            "diversion_freeflow_seconds": result.diversion_freeflow_seconds,
            "hard_brake_proxy": result.hard_brakes,
            "approach_p95_delay": result.approach_p95_delay,
        },
        "delta_vs_no_action": {
            "spillback_time_pct": _pct(
                result.spillback_time_sec, baseline.spillback_time_sec
            ),
            "total_travel_time_pct": _pct(
                result.total_travel_time_sec, baseline.total_travel_time_sec
            ),
            "worst_approach_delay_pct": _pct(
                result.worst_approach_delay_sec,
                baseline.worst_approach_delay_sec,
            ),
        },
        "guard": guard,
    }
    payload["result_sha256"] = _sha256_json(payload)
    return payload


def _run_case(case: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with _applied_case(case) as quality:
        for scenario_id in SCENARIOS:
            for seed in SEEDS:
                results = {
                    policy_id: simulation.run_simulation(
                        scenario_id, seed, policy_id
                    )
                    for policy_id in POLICY_IDS
                }
                baseline = results["no_action"]
                policies_payload: dict[str, Any] = {}
                for policy_id in POLICY_IDS:
                    guard = (
                        {
                            "passed": True,
                            "violations": [],
                            "rule_version": safety.RULE_VERSION,
                            "note": "baseline_not_guarded",
                        }
                        if policy_id == "no_action"
                        else safety.evaluate_guard(
                            results[policy_id], baseline, quality
                        )
                    )
                    policies_payload[policy_id] = _result_payload(
                        results[policy_id], baseline, guard
                    )

                gating = policies_payload["corridor_gating"]
                acceptance = {
                    "spillback_reduction_at_least_30_pct": (
                        gating["delta_vs_no_action"]["spillback_time_pct"]
                        <= -30.0
                    ),
                    "travel_time_reduction_at_least_10_pct": (
                        gating["delta_vs_no_action"]["total_travel_time_pct"]
                        <= -10.0
                    ),
                    "guard_passed": gating["guard"]["passed"],
                }
                acceptance["all_passed"] = all(acceptance.values())
                row = {
                    "case_id": case["case_id"],
                    "parameter": case["parameter"],
                    "category": case["category"],
                    "position": case["position"],
                    "value": case["value"],
                    "nominal": case["nominal"],
                    "unit": case["unit"],
                    "scope": case["scope"],
                    "scenario_id": scenario_id,
                    "seed": seed,
                    "data_quality": copy.deepcopy(quality),
                    "policies": policies_payload,
                    "acceptance": acceptance,
                }
                row["row_sha256"] = _sha256_json(row)
                rows.append(row)
    return rows


def _run_sweep(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for case in cases for row in _run_case(case)]


def _mean(values: list[float]) -> float:
    return round(statistics.fmean(values), 3)


def _summaries(
    cases: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summaries = []
    for case in cases:
        for scenario_id in SCENARIOS:
            selected = [
                row for row in rows
                if row["case_id"] == case["case_id"]
                and row["scenario_id"] == scenario_id
            ]
            spillback = [
                row["policies"]["corridor_gating"]["delta_vs_no_action"][
                    "spillback_time_pct"
                ]
                for row in selected
            ]
            travel = [
                row["policies"]["corridor_gating"]["delta_vs_no_action"][
                    "total_travel_time_pct"
                ]
                for row in selected
            ]
            summaries.append(
                {
                    "case_id": case["case_id"],
                    "parameter": case["parameter"],
                    "position": case["position"],
                    "value": case["value"],
                    "scenario_id": scenario_id,
                    "seed_count": len(selected),
                    "gating_spillback_delta_pct": {
                        "min": min(spillback),
                        "mean": _mean(spillback),
                        "max": max(spillback),
                    },
                    "gating_travel_time_delta_pct": {
                        "min": min(travel),
                        "mean": _mean(travel),
                        "max": max(travel),
                    },
                    "gating_guard_pass_count": sum(
                        row["policies"]["corridor_gating"]["guard"]["passed"]
                        for row in selected
                    ),
                    "fixed_guard_pass_count": sum(
                        row["policies"]["fixed_metering"]["guard"]["passed"]
                        for row in selected
                    ),
                    "gating_acceptance_pass_count": sum(
                        row["acceptance"]["all_passed"]
                        for row in selected
                    ),
                    "gating_recovery_observed_count": sum(
                        row["policies"]["corridor_gating"]["kpi"][
                            "recovery_observed"
                        ]
                        for row in selected
                    ),
                    "baseline_recovery_observed_count": sum(
                        row["policies"]["no_action"]["kpi"][
                            "recovery_observed"
                        ]
                        for row in selected
                    ),
                }
            )
    return summaries


def _guard_boundary_probes() -> list[dict[str, Any]]:
    def result(
        *,
        delay: float = 100.0,
        diversion: float = 0.0,
        hard_brakes: int = 0,
    ) -> simulation.SimResult:
        value = simulation.SimResult(
            "rain_spillback_a", 1, "corridor_gating"
        )
        value.approach_p95_delay = {"R1_N": delay}
        value.diversion_delay_sec = diversion
        value.hard_brakes = hard_brakes
        return value

    baseline = result()
    exact_fairness_delay = 100.0 * (
        1.0 + safety.FAIRNESS_P95_LIMIT_PCT / 100.0
    )
    probes: list[tuple[str, dict[str, Any], bool, str | None]] = [
        (
            "fairness_exact_limit",
            safety.evaluate_guard(
                result(delay=exact_fairness_delay), baseline
            ),
            True,
            None,
        ),
        (
            "fairness_above_limit",
            safety.evaluate_guard(
                result(delay=exact_fairness_delay + 1e-9),
                baseline,
            ),
            False,
            "FAIRNESS_P95_EXCEEDED",
        ),
        (
            "diversion_exact_limit",
            safety.evaluate_guard(
                result(diversion=safety.DIVERSION_DELAY_LIMIT_SEC), baseline
            ),
            True,
            None,
        ),
        (
            "diversion_above_limit",
            safety.evaluate_guard(
                result(
                    diversion=safety.DIVERSION_DELAY_LIMIT_SEC + 1e-9
                ),
                baseline,
            ),
            False,
            "DIVERSION_DELAY_EXCEEDED",
        ),
        (
            "hard_brake_equal",
            safety.evaluate_guard(
                result(hard_brakes=baseline.hard_brakes), baseline
            ),
            True,
            None,
        ),
        (
            "hard_brake_above",
            safety.evaluate_guard(
                result(hard_brakes=baseline.hard_brakes + 1), baseline
            ),
            False,
            "HARD_BRAKE_PROXY_DEGRADED",
        ),
        (
            "stale_exact_limit",
            {
                "passed": not safety.operational_violations(
                    {
                        "data_age_sec": safety.DATA_STALE_LIMIT_SEC,
                        "sensor_available": True,
                        "device_status": "ok",
                    }
                ),
                "violations": safety.operational_violations(
                    {
                        "data_age_sec": safety.DATA_STALE_LIMIT_SEC,
                        "sensor_available": True,
                        "device_status": "ok",
                    }
                ),
            },
            True,
            None,
        ),
        (
            "stale_above_limit",
            {
                "passed": False,
                "violations": safety.operational_violations(
                    {
                        "data_age_sec": math.nextafter(
                            safety.DATA_STALE_LIMIT_SEC, math.inf
                        ),
                        "sensor_available": True,
                        "device_status": "ok",
                    }
                ),
            },
            False,
            "DATA_STALE",
        ),
    ]
    output = []
    for probe_id, guard, expected_pass, expected_code in probes:
        codes = [item["code"] for item in guard["violations"]]
        actual_pass = bool(guard["passed"])
        matched = (
            actual_pass == expected_pass
            and (expected_code is None or expected_code in codes)
        )
        output.append(
            {
                "probe_id": probe_id,
                "expected_pass": expected_pass,
                "expected_code": expected_code,
                "actual_pass": actual_pass,
                "actual_codes": codes,
                "matched": matched,
            }
        )
    if not all(probe["matched"] for probe in output):
        raise RuntimeError("one or more guard boundary probes failed")
    return output


def _csv_bytes(
    rows: list[dict[str, Any]],
    *,
    input_sha256: str,
    results_sha256: str,
    git_commit_sha: str,
    environment_sha256: str,
) -> bytes:
    fields = [
        "validation_status",
        "case_id",
        "parameter",
        "category",
        "position",
        "value",
        "nominal",
        "unit",
        "scenario_id",
        "seed",
        "policy_id",
        "spillback_time_sec",
        "recovery_time_sec",
        "recovery_observed",
        "total_travel_time_sec",
        "worst_approach_delay_sec",
        "spillback_delta_pct",
        "travel_time_delta_pct",
        "guard_passed",
        "guard_codes",
        "acceptance_all_passed",
        "result_sha256",
        "row_sha256",
        "input_sha256",
        "results_sha256",
        "git_commit_sha",
        "environment_sha256",
    ]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fields,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        for policy_id in POLICY_IDS:
            policy = row["policies"][policy_id]
            writer.writerow(
                {
                    "validation_status": VALIDATION_STATUS,
                    "case_id": row["case_id"],
                    "parameter": row["parameter"],
                    "category": row["category"],
                    "position": row["position"],
                    "value": row["value"],
                    "nominal": row["nominal"],
                    "unit": row["unit"],
                    "scenario_id": row["scenario_id"],
                    "seed": row["seed"],
                    "policy_id": policy_id,
                    "spillback_time_sec": policy["kpi"][
                        "spillback_time_sec"
                    ],
                    "recovery_time_sec": policy["kpi"][
                        "recovery_time_sec"
                    ],
                    "recovery_observed": policy["kpi"][
                        "recovery_observed"
                    ],
                    "total_travel_time_sec": policy["kpi"][
                        "total_travel_time_sec"
                    ],
                    "worst_approach_delay_sec": policy["kpi"][
                        "worst_approach_delay_sec"
                    ],
                    "spillback_delta_pct": policy["delta_vs_no_action"][
                        "spillback_time_pct"
                    ],
                    "travel_time_delta_pct": policy["delta_vs_no_action"][
                        "total_travel_time_pct"
                    ],
                    "guard_passed": policy["guard"]["passed"],
                    "guard_codes": "|".join(
                        item["code"] for item in policy["guard"]["violations"]
                    ),
                    "acceptance_all_passed": (
                        row["acceptance"]["all_passed"]
                        if policy_id == "corridor_gating"
                        else ""
                    ),
                    "result_sha256": policy["result_sha256"],
                    "row_sha256": row["row_sha256"],
                    "input_sha256": input_sha256,
                    "results_sha256": results_sha256,
                    "git_commit_sha": git_commit_sha,
                    "environment_sha256": environment_sha256,
                }
            )
    return buffer.getvalue().encode("utf-8")


def _write_outputs(
    prefix: Path,
    *,
    payload: dict[str, Any],
    csv_content: bytes,
) -> dict[str, Any]:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = prefix.with_suffix(".json")
    csv_path = prefix.with_suffix(".csv")
    checksum_path = prefix.with_suffix(".sha256")

    json_content = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    json_path.write_bytes(json_content)
    csv_path.write_bytes(csv_content)
    exact_hashes = {
        json_path.name: _sha256_bytes(json_content),
        csv_path.name: _sha256_bytes(csv_content),
    }
    checksum_content = "".join(
        f"{digest}  {filename}\n"
        for filename, digest in sorted(exact_hashes.items())
    ).encode("utf-8")
    checksum_path.write_bytes(checksum_content)
    return {
        "json": str(json_path),
        "csv": str(csv_path),
        "sha256": str(checksum_path),
        "exact_file_sha256": exact_hashes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-prefix",
        type=Path,
        required=True,
        help="path without extension; .json/.csv/.sha256 are written",
    )
    parser.add_argument(
        "--verify-repeat",
        action="store_true",
        help="repeat the complete sweep and require byte-identical logical rows",
    )
    args = parser.parse_args()

    _assert_nominal_metering_parity()
    cases = _case_definitions()
    git_identity = _git_identity()
    source_identity = _source_identity()
    environment = _environment_identity()
    design = {
        "runner_version": RUNNER_VERSION,
        "validation_status": VALIDATION_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "method": "one-at-a-time; nominal once, then one low/high change",
        "scenarios": list(SCENARIOS),
        "seeds": list(SEEDS),
        "policies": list(POLICY_IDS),
        "parameters": [asdict(spec) for spec in PARAMETERS],
        "cases": cases,
        "fixed_stress_inputs": {
            "data_stale_limit_seconds_cases": {
                "data_age_sec": 120.0,
                "sensor_available": True,
                "device_status": "ok",
            }
        },
        "acceptance_observation_only": {
            "gating_spillback_delta_pct_lte": -30.0,
            "gating_total_travel_time_delta_pct_lte": -10.0,
            "gating_guard_passed": True,
            "note": (
                "These are internal spike criteria, not field acceptance or "
                "a safety approval."
            ),
        },
        "source_identity": source_identity,
        "git_identity": git_identity,
    }
    input_sha256 = _sha256_json(design)

    rows = _run_sweep(cases)
    results_sha256 = _sha256_json(rows)
    repeat = {
        "requested": args.verify_repeat,
        "matched": None,
        "repeat_results_sha256": None,
    }
    if args.verify_repeat:
        repeated_rows = _run_sweep(cases)
        repeated_sha = _sha256_json(repeated_rows)
        repeat = {
            "requested": True,
            "matched": repeated_sha == results_sha256,
            "repeat_results_sha256": repeated_sha,
        }
        if not repeat["matched"]:
            raise RuntimeError(
                "repeat sweep diverged: "
                f"{results_sha256} != {repeated_sha}"
            )

    guard_probes = _guard_boundary_probes()
    summaries = _summaries(cases, rows)
    csv_content = _csv_bytes(
        rows,
        input_sha256=input_sha256,
        results_sha256=results_sha256,
        git_commit_sha=git_identity["commit_sha"],
        environment_sha256=environment["fingerprint_sha256"],
    )
    payload_without_integrity = {
        "schema_version": "rainflow-parameter-sensitivity-evidence-v1",
        "validation_status": VALIDATION_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "design": design,
        "environment": environment,
        "repeat_verification": repeat,
        "guard_boundary_probes": guard_probes,
        "summary": summaries,
        "rows": rows,
        "limitations": [
            "All demand, storage, queue, rain, and policy inputs remain synthetic.",
            "OAT does not measure interactions among two or more changed values.",
            "The same project code authors produced this run; it is not independent review.",
            "No Sejong detector, controller, vehicle trajectory, or field outcome is used.",
            "Scenario-B's hard-coded 0.80 incident storage multiplier is not swept.",
            "The hard-brake value is a queue-blocking proxy, not a measured deceleration.",
            "A passing internal spike criterion must not be presented as field safety or efficacy.",
        ],
    }
    logical_payload_sha256 = _sha256_json(payload_without_integrity)
    payload = {
        **payload_without_integrity,
        "integrity": {
            "input_sha256": input_sha256,
            "results_sha256": results_sha256,
            "guard_boundary_probes_sha256": _sha256_json(guard_probes),
            "logical_json_payload_sha256": logical_payload_sha256,
            "csv_file_sha256": _sha256_bytes(csv_content),
        },
    }
    outputs = _write_outputs(
        args.output_prefix.resolve(),
        payload=payload,
        csv_content=csv_content,
    )
    print(
        json.dumps(
            {
                "validation_status": VALIDATION_STATUS,
                "case_count": len(cases),
                "scenario_seed_row_count": len(rows),
                "csv_policy_row_count": len(rows) * len(POLICY_IDS),
                "input_sha256": input_sha256,
                "results_sha256": results_sha256,
                "repeat_verification": repeat,
                "outputs": outputs,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""RainFlow Sejong offline-first FastAPI backend.

The four paths frozen on 2026-07-28 remain unchanged:

* ``GET /api/health``
* ``POST /api/simulations``
* ``GET /api/simulations/{run_id}``
* ``POST /api/approvals``

All traffic numbers are synthetic and provisional.  KPI calculation and safety
decisions are deterministic Python code; the explanation layer is rule based.
"""
from __future__ import annotations

import copy
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from .decision import SCORING_VERSION, build_rule_based_decision
from .domain import (
    ApprovalRequest,
    ApprovalResult,
    HealthResponse,
    RunResult,
    SimulationCreatedResponse,
    SimulationRequest,
)
from .policies import POLICIES, POLICY_LABELS, POLICY_VERSION
from .safety import (
    RULE_VERSION,
    candidate_hash,
    evaluate_guard,
    operational_violations,
)
from .simulation import (
    DURATION,
    DRY_PREP_END,
    KPI_DEFINITION_VERSION,
    LINKS,
    PARAMETER_SET_VERSION,
    RAIN_END,
    SCENARIOS,
    SIMULATOR_VERSION,
    SimResult,
    run_simulation,
)
from .storage import RunStore

BACKEND_DIR = Path(__file__).resolve().parent.parent
FIXTURE_PATH = BACKEND_DIR / "fixtures" / "demo_run.json"
CACHED_FIXTURE_PATH = BACKEND_DIR / "fixtures" / "cached_run.json"
FREEZE_META_PATH = BACKEND_DIR / "fixtures" / "demo_freeze_meta.json"
LOGS_DIR = BACKEND_DIR / "logs"
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
KST = timezone(timedelta(hours=9))

VERSION = "0.2.0"
NETWORK_VERSION = "sejong-corridor-v0"
DATASET_ID = "synthetic-v0"
DATASET_SCHEMA_VERSION = "rainflow-dataset-v1"
DATASET_ADAPTER_VERSION = "builtin-synthetic-v1"
SCREEN_STATES = [
    "normal",
    "rain_warning",
    "spillback",
    "policy_compare",
    "safety_review",
    "operator_approval",
    "recovery_compare",
]

app = FastAPI(
    title="RainFlow Sejong",
    version=VERSION,
    description=(
        "합성 데이터 기반 우천 연속 회전교차로 디지털 트윈. "
        "실제 세종시 교통 성과나 실제 신호 제어를 의미하지 않습니다."
    ),
)
RUNS: dict[str, dict[str, Any]] = {}
STORE = RunStore(LOGS_DIR)


def load_fixture(path: Path = FIXTURE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_freeze_meta() -> dict[str, Any]:
    if not FREEZE_META_PATH.exists():
        return {
            "freeze_id": "unfrozen",
            "git_commit_sha": "unfrozen",
            "source_tree_checksum": "unfrozen",
        }
    return json.loads(FREEZE_META_PATH.read_text(encoding="utf-8"))


def _now() -> str:
    return datetime.now(KST).isoformat()


def _kpi(result: SimResult) -> dict[str, float | bool]:
    return {
        "spillback_time_sec": result.spillback_time_sec,
        "recovery_time_sec": result.recovery_time_sec,
        "recovery_observed": result.recovery_observed,
        "total_travel_time_sec": result.total_travel_time_sec,
        "worst_approach_delay_sec": result.worst_approach_delay_sec,
    }


def _pct(candidate: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    return round((candidate - baseline) / baseline * 100, 1)


def result_checksum(run: dict[str, Any]) -> str:
    """Hash the deterministic result shared by live, fixture, and the screen."""
    canonical = {
        "dataset": run["dataset"],
        "scenario": run["scenario"],
        "screen_states": run["screen_states"],
        "network": run["network"],
        "timeline": run["timeline"],
        "policies": run["policies"],
        "decision": run["decision"],
        "versions": {
            key: run["reproducibility"][key]
            for key in (
                "simulator_version",
                "parameter_set_version",
                "kpi_definition_version",
                "guard_version",
                "network_version",
                "policy_version",
                "scoring_version",
            )
        },
    }

    def normalize(value: Any) -> Any:
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, dict):
            return {
                key: normalized
                for key, item in value.items()
                if (normalized := normalize(item)) is not None
            }
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    encoded = json.dumps(
        normalize(canonical),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _improvement(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, float]:
    return {
        "spillback_time_pct": _pct(
            float(candidate["spillback_time_sec"]),
            float(baseline["spillback_time_sec"]),
        ),
        "recovery_time_pct": _pct(
            float(candidate["recovery_time_sec"]),
            float(baseline["recovery_time_sec"]),
        ),
        "total_travel_time_pct": _pct(
            float(candidate["total_travel_time_sec"]),
            float(baseline["total_travel_time_sec"]),
        ),
        "worst_approach_delay_pct": _pct(
            float(candidate["worst_approach_delay_sec"]),
            float(baseline["worst_approach_delay_sec"]),
        ),
    }


def _explain(policy_id: str, result: SimResult, baseline: SimResult, guard: dict) -> str:
    if policy_id == "no_action":
        return (
            f"기존 양보운전 유지. spillback 누적 {result.spillback_time_sec:.0f}초, "
            f"총 통행시간 {result.total_travel_time_sec:.0f}초가 비교 기준선이 된다."
        )
    spillback_delta = _pct(result.spillback_time_sec, baseline.spillback_time_sec)
    travel_delta = _pct(result.total_travel_time_sec, baseline.total_travel_time_sec)
    text = (
        f"{POLICY_LABELS[policy_id]} 적용 시 무대응 대비 spillback 누적 "
        f"{spillback_delta:+.1f}%, 총 통행시간 {travel_delta:+.1f}%."
    )
    if guard["passed"]:
        return text + " 모든 안전·공정성 가드를 통과했다."
    codes = ", ".join(violation["code"] for violation in guard["violations"])
    return text + f" 가드 위반({codes})으로 적용 불가."


def _screen_state_at(scenario_id: str, t_sec: int) -> str:
    if scenario_id == "dry_base":
        return "normal"
    if t_sec < DRY_PREP_END:
        return "normal"
    if t_sec < 1260:
        return "rain_warning"
    if t_sec < 1620:
        return "spillback"
    if t_sec < 1800:
        return "policy_compare"
    if t_sec < 1980:
        return "safety_review"
    if t_sec < RAIN_END:
        return "operator_approval"
    return "recovery_compare"


def _timeline(scenario_id: str, baseline: SimResult) -> list[dict[str, Any]]:
    notes = {
        "normal": "건조 기준 상태",
        "rain_warning": "강우 용량 저하 감지",
        "spillback": "연결도로 저장한계와 상류 역류 확인",
        "policy_compare": "동일 수요·seed에서 세 정책 KPI 비교",
        "safety_review": "결정론적 안전·공정성 규칙 검사",
        "operator_approval": "가드 통과 후보의 운영자 결정 대기",
        "recovery_compare": "무대응과 승인 정책의 회복 결과 비교",
    }
    timeline = []
    for entry in baseline.timeline:
        state = _screen_state_at(scenario_id, int(entry["t_sec"]))
        timeline.append(
            {
                **entry,
                "screen_state": state,
                "note": notes[state],
            }
        )
    return timeline


def _policy_record(
    policy_id: str,
    result: SimResult,
    baseline: SimResult,
    guard: dict[str, Any],
) -> dict[str, Any]:
    record = {
        "policy_id": policy_id,
        "label": POLICY_LABELS[policy_id],
        "kpi": _kpi(result),
        "extra": {
            "spillback_events": result.spillback_events,
            "spillback_link_seconds": result.spillback_link_seconds,
            "completed_trips": result.completed_trips,
            "diversion_delay_sec": result.diversion_delay_sec,
            "diverted_vehicles": result.diverted_vehicles,
            "diversion_vehicle_seconds": result.diversion_vehicle_seconds,
            "diversion_freeflow_seconds": result.diversion_freeflow_seconds,
            "modeled_vehicle_seconds": result.modeled_vehicle_seconds,
            "safety_proxy_hard_brakes": result.hard_brakes,
            "approach_p95_delay": result.approach_p95_delay,
        },
        "delta_vs_no_action": {
            "spillback_time_pct": _pct(
                result.spillback_time_sec,
                baseline.spillback_time_sec,
            ),
            "total_travel_time_pct": _pct(
                result.total_travel_time_sec,
                baseline.total_travel_time_sec,
            ),
            "worst_approach_delay_pct": _pct(
                result.worst_approach_delay_sec,
                baseline.worst_approach_delay_sec,
            ),
        },
        "guard": guard,
        "explanation": _explain(policy_id, result, baseline, guard),
    }
    record["candidate_hash"] = candidate_hash(record)
    return record


def _make_run_id(
    source: str,
    scenario_id: str,
    seed: int,
    data_quality: dict[str, Any],
    dataset_id: str,
    source_tree_checksum: str,
) -> str:
    payload = json.dumps(
        {
            "scenario_id": scenario_id,
            "seed": seed,
            "data_quality": data_quality,
            "dataset_id": dataset_id,
            "simulator_version": SIMULATOR_VERSION,
            "parameter_set_version": PARAMETER_SET_VERSION,
            "kpi_definition_version": KPI_DEFINITION_VERSION,
            "guard_version": RULE_VERSION,
            "policy_version": POLICY_VERSION,
            "network_version": NETWORK_VERSION,
            "scoring_version": SCORING_VERSION,
            "source_tree_checksum": source_tree_checksum,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    suffix = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10]
    prefix = {
        "live_simulation": "live",
        "cached_simulation": "cached",
        "fixture": "fixture",
    }[source]
    return f"{prefix}-{scenario_id}-s{seed}-{suffix}"


def _state_history(safety_passed: bool) -> list[dict[str, Any]]:
    states = ["CREATED", "PREDICTED", "AI_REVIEWED"]
    states.append("SAFETY_PASSED" if safety_passed else "SAFETY_REJECTED")
    return [
        {"sequence": sequence, "state": state}
        for sequence, state in enumerate(states, start=1)
    ]


def _attach_decision(policy_records: list[dict[str, Any]]) -> dict[str, Any]:
    decision = build_rule_based_decision(policy_records)
    assessments = {
        assessment["policy_id"]: assessment
        for assessment in decision["policy_assessments"]
    }
    for policy in policy_records:
        assessment = assessments[policy["policy_id"]]
        policy["rank"] = assessment["rank"]
        policy["score"] = assessment["score"]
    return decision


def build_run(
    scenario_id: str,
    seed: int,
    data_quality: dict[str, Any] | None = None,
    freeze_meta: dict[str, Any] | None = None,
    dataset_id: str = DATASET_ID,
) -> dict[str, Any]:
    """Build one deterministic live result.

    ``generated_at`` and ``elapsed_ms`` are operational metadata.  The
    timeline, KPI, policy order, hashes, guards, and decision are deterministic
    for the same input and seed.
    """
    if scenario_id not in SCENARIOS:
        raise ValueError(f"unknown scenario_id: {scenario_id}")
    if dataset_id != DATASET_ID:
        raise ValueError(
            f"dataset adapter not installed: {dataset_id}; use {DATASET_ID}"
        )
    quality = copy.deepcopy(data_quality or {
        "data_age_sec": 0.0,
        "sensor_available": True,
        "device_status": "ok",
    })
    frozen_source = copy.deepcopy(freeze_meta or load_freeze_meta())
    started = time.perf_counter()
    results = {
        policy_id: run_simulation(scenario_id, seed, policy_id)
        for policy_id in POLICIES
    }
    baseline = results["no_action"]
    guards = {
        policy_id: evaluate_guard(results[policy_id], baseline, quality)
        for policy_id in POLICIES
        if policy_id != "no_action"
    }
    guards["no_action"] = {
        "passed": True,
        "violations": [],
        "rule_version": RULE_VERSION,
        "note": "기준선. 가드 판정 대상 아님",
    }
    policy_records = [
        _policy_record(policy_id, results[policy_id], baseline, guards[policy_id])
        for policy_id in POLICIES
    ]
    decision = _attach_decision(policy_records)
    recommended_policy_id = decision["recommended_policy_id"]
    recommended = next(
        policy for policy in policy_records
        if policy["policy_id"] == recommended_policy_id
    )
    baseline_kpi = _kpi(baseline)
    safety_passed = any(
        policy["policy_id"] != "no_action" and policy["guard"]["passed"]
        for policy in policy_records
    )
    workflow_state = "SAFETY_PASSED" if safety_passed else "SAFETY_REJECTED"
    run_id = _make_run_id(
        "live_simulation",
        scenario_id,
        seed,
        quality,
        dataset_id,
        frozen_source["source_tree_checksum"],
    )

    run = {
        "run_id": run_id,
        "result_source": "live_simulation",
        "provisional": True,
        "generated_at": _now(),
        "network_version": NETWORK_VERSION,
        "dataset": {
            "dataset_id": dataset_id,
            "data_class": "synthetic",
            "schema_version": DATASET_SCHEMA_VERSION,
            "adapter_version": DATASET_ADAPTER_VERSION,
            "default": True,
        },
        "note": (
            "결정론적 큐 모델 계산 결과. 합성 데이터이며 실제 세종시 "
            "실측 성과나 실제 도로 제어 결과가 아니다."
        ),
        "scenario": {
            "scenario_id": scenario_id,
            "seed": seed,
            "rain_level": SCENARIOS[scenario_id]["rain_level"],
            "duration_sec": DURATION,
            "phases": {
                "dry_prep_sec": DRY_PREP_END,
                "rain_peak_sec": RAIN_END - DRY_PREP_END,
                "recovery_sec": DURATION - RAIN_END,
            },
            "incident": SCENARIOS[scenario_id]["incident"],
            "data_quality": quality,
        },
        "screen_states": SCREEN_STATES,
        "network": {
            "roundabouts": ["R1", "R2", "R3"],
            "links": [
                {
                    "link_id": "L12",
                    "from": "R1",
                    "to": "R2",
                    "storage_veh": LINKS["L12"],
                },
                {
                    "link_id": "L23",
                    "from": "R2",
                    "to": "R3",
                    "storage_veh": LINKS["L23"],
                },
                {
                    "link_id": "BYPASS",
                    "from": "R1",
                    "to": "R3",
                    "storage_veh": LINKS["BYPASS"],
                },
            ],
            "approaches": list(baseline.approach_p95_delay),
        },
        "timeline": _timeline(scenario_id, baseline),
        "policies": policy_records,
        "decision": decision,
        "safety_guards": {
            "provisional": True,
            "rule_version": RULE_VERSION,
            "rules": [
                {"code": "FAIRNESS_P95_EXCEEDED", "threshold_pct": 15.0},
                {"code": "DIVERSION_DELAY_EXCEEDED", "threshold_sec": 180.0},
                {"code": "HARD_BRAKE_PROXY_DEGRADED"},
                {"code": "DATA_STALE", "threshold_sec": 120.0},
                {"code": "DEVICE_FAULT"},
                {"code": "CANDIDATE_HASH_MISMATCH"},
                {"code": "OPERATOR_NOT_APPROVED"},
            ],
        },
        "approval": {
            "status": "pending",
            "policy_id": recommended_policy_id,
        },
        # Before approval, the applied trace is deliberately the no-action
        # baseline.  The candidate outcome remains an explicitly predicted
        # optional field.
        "recovery_compare": {
            "no_action": baseline_kpi,
            "applied": copy.deepcopy(baseline_kpi),
            "improvement": _improvement(baseline_kpi, baseline_kpi),
            "predicted_if_approved": {
                "policy_id": recommended_policy_id,
                "kpi": copy.deepcopy(recommended["kpi"]),
                "improvement": _improvement(recommended["kpi"], baseline_kpi),
            },
        },
        "workflow_state": workflow_state,
        "state_history": _state_history(safety_passed),
        "reproducibility": {
            "input": {
                "scenario_id": scenario_id,
                "seed": seed,
                "data_quality": quality,
                "dataset_id": dataset_id,
            },
            "freeze_id": frozen_source["freeze_id"],
            "git_commit_sha": frozen_source["git_commit_sha"],
            "source_tree_checksum": frozen_source["source_tree_checksum"],
            "simulator_version": SIMULATOR_VERSION,
            "parameter_set_version": PARAMETER_SET_VERSION,
            "kpi_definition_version": KPI_DEFINITION_VERSION,
            "guard_version": RULE_VERSION,
            "network_version": NETWORK_VERSION,
            "policy_version": POLICY_VERSION,
            "rule_version": RULE_VERSION,
            "scoring_version": SCORING_VERSION,
            "candidate_hashes": {
                policy["policy_id"]: policy["candidate_hash"]
                for policy in policy_records
            },
        },
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
    }
    run["reproducibility"]["result_checksum"] = result_checksum(run)
    return run


def _fallback_run(
    scenario_id: str,
    seed: int,
    data_quality: dict[str, Any],
    source: str,
    dataset_id: str = DATASET_ID,
) -> dict[str, Any]:
    cache_path = CACHED_FIXTURE_PATH if CACHED_FIXTURE_PATH.exists() else FIXTURE_PATH
    run = load_fixture(cache_path if source == "cached_simulation" else FIXTURE_PATH)
    run = copy.deepcopy(run)
    stored_dataset_id = run.get("dataset", {}).get("dataset_id")
    if stored_dataset_id != dataset_id:
        raise ValueError(
            "stored result dataset mismatch: "
            f"requested {dataset_id}, stored {stored_dataset_id or 'missing'}"
        )
    stored_reproducibility = copy.deepcopy(run.get("reproducibility", {}))
    run["run_id"] = _make_run_id(
        source,
        scenario_id,
        seed,
        data_quality,
        dataset_id,
        stored_reproducibility.get("source_tree_checksum", "unfrozen"),
    )
    run["result_source"] = source
    run["generated_at"] = _now()
    run["note"] = (
        f"{run.get('note', '')} 요청 {scenario_id}/seed {seed}의 실시간 계산 대신 "
        f"{cache_path.name if source == 'cached_simulation' else FIXTURE_PATH.name}을 재생한다."
    ).strip()
    for policy in run["policies"]:
        policy["candidate_hash"] = candidate_hash(policy)
    decision = _attach_decision(run["policies"])
    recommended_policy_id = decision["recommended_policy_id"]
    run["decision"] = decision
    run["approval"] = {
        "status": "pending",
        "policy_id": recommended_policy_id,
    }
    baseline = next(
        policy["kpi"] for policy in run["policies"]
        if policy["policy_id"] == "no_action"
    )
    recommended = next(
        policy["kpi"] for policy in run["policies"]
        if policy["policy_id"] == recommended_policy_id
    )
    run["recovery_compare"] = {
        "no_action": copy.deepcopy(baseline),
        "applied": copy.deepcopy(baseline),
        "improvement": _improvement(baseline, baseline),
        "predicted_if_approved": {
            "policy_id": recommended_policy_id,
            "kpi": copy.deepcopy(recommended),
            "improvement": _improvement(recommended, baseline),
        },
    }
    safety_passed = any(
        policy["policy_id"] != "no_action" and policy["guard"]["passed"]
        for policy in run["policies"]
    )
    run["workflow_state"] = "SAFETY_PASSED" if safety_passed else "SAFETY_REJECTED"
    run["state_history"] = _state_history(safety_passed)
    run["reproducibility"] = {
        "input": {
            "scenario_id": scenario_id,
            "seed": seed,
            "data_quality": data_quality,
            "dataset_id": dataset_id,
        },
        "simulator_version": "stored-result",
        "freeze_id": stored_reproducibility.get("freeze_id", "unfrozen"),
        "git_commit_sha": stored_reproducibility.get(
            "git_commit_sha", "unfrozen"
        ),
        "source_tree_checksum": stored_reproducibility.get(
            "source_tree_checksum", "unfrozen"
        ),
        "parameter_set_version": stored_reproducibility.get(
            "parameter_set_version", PARAMETER_SET_VERSION
        ),
        "kpi_definition_version": stored_reproducibility.get(
            "kpi_definition_version", KPI_DEFINITION_VERSION
        ),
        "guard_version": stored_reproducibility.get(
            "guard_version", RULE_VERSION
        ),
        "network_version": run.get("network_version", NETWORK_VERSION),
        "policy_version": POLICY_VERSION,
        "rule_version": RULE_VERSION,
        "scoring_version": SCORING_VERSION,
        "candidate_hashes": {
            policy["policy_id"]: policy["candidate_hash"]
            for policy in run["policies"]
        },
        "result_checksum": stored_reproducibility.get("result_checksum"),
        "stored_scenario_id": run.get("scenario", {}).get("scenario_id"),
    }
    run["elapsed_ms"] = 0.0
    return run


def _save_and_audit(run: dict[str, Any], requested_input: dict[str, Any]) -> None:
    STORE.save(run)
    STORE.audit(
        "simulation_created",
        {
            "run_id": run["run_id"],
            "result_source": run["result_source"],
            "workflow_state": run["workflow_state"],
            "input": requested_input,
            "versions": {
                key: run["reproducibility"].get(key)
                for key in (
                    "simulator_version",
                    "parameter_set_version",
                    "kpi_definition_version",
                    "guard_version",
                    "network_version",
                    "policy_version",
                    "rule_version",
                    "scoring_version",
                )
            },
            "candidate_hashes": run["reproducibility"]["candidate_hashes"],
            "policy_results": [
                {
                    "policy_id": policy["policy_id"],
                    "rank": policy.get("rank"),
                    "score": policy.get("score"),
                    "kpi": policy["kpi"],
                    "guard": policy["guard"],
                }
                for policy in run["policies"]
            ],
            "replay_file": f"runs/{run['run_id']}.json",
        },
    )


def _load_run(run_id: str) -> dict[str, Any] | None:
    if run_id in RUNS:
        return RUNS[run_id]
    try:
        persisted = STORE.load(run_id)
    except ValueError:
        return None
    if persisted is not None:
        RUNS[run_id] = persisted
        return persisted
    if run_id == "fixture-day1-001":
        return load_fixture()
    return None


def _append_state(run: dict[str, Any], state: str) -> None:
    history = run.setdefault("state_history", [])
    if history and history[-1].get("state") == state:
        return
    history.append({"sequence": len(history) + 1, "state": state})
    run["workflow_state"] = state


def _deduplicate_violations(violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for violation in violations:
        key = (str(violation.get("code")), str(violation.get("detail")))
        if key not in seen:
            seen.add(key)
            unique.append(violation)
    return unique


def _revalidate_candidate(
    run: dict[str, Any],
    policy: dict[str, Any],
    request: ApprovalRequest,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    stored_hash = policy.get("candidate_hash")
    recomputed_stored_hash = candidate_hash(policy)
    if stored_hash != recomputed_stored_hash:
        violations.append(
            {
                "code": "CANDIDATE_HASH_MISMATCH",
                "detail": "저장 후보 내용이 시뮬레이션 완료 뒤 변경됨",
            }
        )
    if (
        request.expected_candidate_hash is not None
        and request.expected_candidate_hash != stored_hash
    ):
        violations.append(
            {
                "code": "CANDIDATE_HASH_MISMATCH",
                "detail": "운영자가 확인한 후보 해시와 서버 후보 해시가 다름",
            }
        )

    recorded_rule_version = run.get("reproducibility", {}).get("rule_version")
    if recorded_rule_version and recorded_rule_version != RULE_VERSION:
        violations.append(
            {
                "code": "RULE_VERSION_MISMATCH",
                "detail": (
                    f"실행 규칙 {recorded_rule_version}과 현재 승인 규칙 "
                    f"{RULE_VERSION}이 다름"
                ),
            }
        )

    original_quality = (
        run.get("reproducibility", {})
        .get("input", {})
        .get("data_quality", {})
    )
    current_quality = (
        request.data_quality.model_dump(mode="json")
        if request.data_quality is not None
        else original_quality
    )
    violations.extend(operational_violations(current_quality))

    if not policy.get("guard", {}).get("passed", False):
        violations.extend(policy.get("guard", {}).get("violations", []))

    if run.get("result_source") == "live_simulation":
        scenario = run["scenario"]
        baseline = run_simulation(
            scenario["scenario_id"],
            int(scenario["seed"]),
            "no_action",
        )
        candidate = run_simulation(
            scenario["scenario_id"],
            int(scenario["seed"]),
            policy["policy_id"],
        )
        fresh_guard = (
            {
                "passed": True,
                "violations": [],
                "rule_version": RULE_VERSION,
                "note": "기준선. 가드 판정 대상 아님",
            }
            if policy["policy_id"] == "no_action"
            else evaluate_guard(candidate, baseline, original_quality)
        )
        fresh_policy = _policy_record(
            policy["policy_id"],
            candidate,
            baseline,
            fresh_guard,
        )
        if fresh_policy["candidate_hash"] != stored_hash:
            violations.append(
                {
                    "code": "CANDIDATE_HASH_MISMATCH",
                    "detail": "같은 입력·seed 재계산 후보가 저장 후보와 다름",
                }
            )
        if not fresh_guard["passed"]:
            violations.extend(fresh_guard["violations"])

    return _deduplicate_violations(violations)


def _set_applied_policy(run: dict[str, Any], policy: dict[str, Any]) -> None:
    baseline = next(
        candidate["kpi"]
        for candidate in run["policies"]
        if candidate["policy_id"] == "no_action"
    )
    run["recovery_compare"]["applied"] = copy.deepcopy(policy["kpi"])
    run["recovery_compare"]["improvement"] = _improvement(policy["kpi"], baseline)
    run["recovery_compare"]["applied_policy_id"] = policy["policy_id"]


@app.get(
    "/api/health",
    response_model=HealthResponse,
    summary="오프라인 서비스 준비 상태",
)
def health() -> dict[str, Any]:
    return {
        "status": "ok" if FIXTURE_PATH.exists() else "degraded",
        "version": VERSION,
        "fixture_available": FIXTURE_PATH.exists(),
        "cached_fixture_available": CACHED_FIXTURE_PATH.exists(),
        "llm": "rule_based_fallback",
        "runs_in_memory": len(RUNS),
        "persisted_runs": STORE.count(),
        "result_source": "fixture",
        "dataset_id": DATASET_ID,
    }


@app.post(
    "/api/simulations",
    response_model=SimulationCreatedResponse,
    summary="동일 입력으로 세 정책 비교 실행",
)
def create_simulation(request: SimulationRequest) -> dict[str, Any]:
    scenario_id = request.scenario_id.value
    dataset_id = request.dataset_id
    quality = request.data_quality.model_dump(mode="json")
    requested_input = request.model_dump(mode="json")
    try:
        if request.force_source == "fixture":
            run = _fallback_run(
                scenario_id,
                request.seed,
                quality,
                "fixture",
                dataset_id,
            )
        elif request.force_source == "cached_simulation":
            run = _fallback_run(
                scenario_id,
                request.seed,
                quality,
                "cached_simulation",
                dataset_id,
            )
        else:
            run = build_run(
                scenario_id,
                request.seed,
                quality,
                dataset_id=dataset_id,
            )
    except Exception as error:
        if request.force_source == "live_simulation":
            raise HTTPException(
                status_code=503,
                detail="live simulation failed and fallback was disabled",
            ) from error
        STORE.audit(
            "simulation_fallback",
            {
                "scenario_id": scenario_id,
                "seed": request.seed,
                "dataset_id": dataset_id,
                "error_type": type(error).__name__,
                "error": str(error),
            },
        )
        run = _fallback_run(
            scenario_id,
            request.seed,
            quality,
            "cached_simulation",
            dataset_id,
        )

    RUNS[run["run_id"]] = run
    _save_and_audit(run, requested_input)
    return {
        "run_id": run["run_id"],
        "status": "completed",
        "result_source": run["result_source"],
        "url": f"/api/simulations/{run['run_id']}",
        "workflow_state": run["workflow_state"],
    }


@app.get(
    "/api/simulations/{run_id}",
    response_model=RunResult,
    summary="저장된 실행·타임라인·KPI·가드 조회",
)
def get_simulation(run_id: str) -> dict[str, Any]:
    run = _load_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run_id not found")
    return run


@app.post(
    "/api/approvals",
    response_model=ApprovalResult,
    summary="가드 재검사 후 운영자 승인·거절·보류",
)
def create_approval(request: ApprovalRequest) -> dict[str, Any]:
    run = _load_run(request.run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run_id not found")
    policy_id = request.policy_id.value
    policy = next(
        (
            candidate
            for candidate in run["policies"]
            if candidate["policy_id"] == policy_id
        ),
        None,
    )
    if policy is None:
        raise HTTPException(status_code=422, detail="unknown policy_id")

    current_status = run.get("approval", {}).get("status", "pending")
    if current_status == "approved":
        if (
            request.decision == "approve"
            and run["approval"].get("policy_id") == policy_id
        ):
            return run["approval"]
        raise HTTPException(
            status_code=409,
            detail={
                "message": "이미 승인 완료된 실행은 다른 상태로 전이할 수 없다",
                "code": "INVALID_STATE_TRANSITION",
            },
        )
    if current_status == "rejected" and request.decision != "reject":
        raise HTTPException(
            status_code=409,
            detail={
                "message": "거절 완료된 실행은 reset 또는 새 실행이 필요하다",
                "code": "INVALID_STATE_TRANSITION",
            },
        )

    if request.decision == "approve":
        violations = _revalidate_candidate(run, policy, request)
        if violations:
            STORE.audit(
                "approval_blocked",
                {
                    "run_id": request.run_id,
                    "policy_id": policy_id,
                    "operator": request.operator,
                    "violations": violations,
                },
            )
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "승인 직전 재검사를 통과하지 못한 후보는 적용할 수 없다",
                    "violations": violations,
                },
            )
        status = "approved"
        _append_state(run, "HUMAN_APPROVED")
        _set_applied_policy(run, policy)
        _append_state(run, "TWIN_APPLIED")
        _append_state(run, "EVALUATED")
    elif request.decision == "reject":
        status = "rejected"
        baseline_policy = next(
            candidate
            for candidate in run["policies"]
            if candidate["policy_id"] == "no_action"
        )
        _set_applied_policy(run, baseline_policy)
        _append_state(run, "HUMAN_REJECTED")
    else:
        status = "held"
        baseline_policy = next(
            candidate
            for candidate in run["policies"]
            if candidate["policy_id"] == "no_action"
        )
        _set_applied_policy(run, baseline_policy)
        _append_state(run, "HUMAN_HELD")

    run["approval"] = {
        "status": status,
        "policy_id": policy_id,
        "operator": request.operator,
        "decided_at": _now(),
        "reason": request.reason,
        "result_source": run["result_source"],
        "workflow_state": run["workflow_state"],
    }
    RUNS[run["run_id"]] = run
    STORE.save(run)
    STORE.audit(
        "approval_decided",
        {
            "run_id": request.run_id,
            "policy_id": policy_id,
            "candidate_hash": policy.get("candidate_hash"),
            "status": status,
            "workflow_state": run["workflow_state"],
            "operator": request.operator,
            "reason": request.reason,
            "result_source": run["result_source"],
        },
    )
    return run["approval"]


# Additive diagnostic endpoints do not alter the frozen four-path contract.
@app.get("/api/scenarios", summary="동결 시나리오 목록")
def list_scenarios() -> dict[str, Any]:
    return {
        "result_source": "fixture",
        "scenarios": [
            {
                "scenario_id": scenario_id,
                **definition,
                "default_seed": 42,
                "provisional": True,
            }
            for scenario_id, definition in SCENARIOS.items()
        ],
    }


@app.get("/api/audit/{run_id}", summary="실행 재현 파일과 감사 이벤트")
def get_audit(run_id: str) -> dict[str, Any]:
    run = _load_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run_id not found")
    return {
        "run_id": run_id,
        "result_source": run["result_source"],
        "replay": run,
        "events": STORE.audit_for_run(run_id),
    }


if FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )

"""RainFlow Sejong FastAPI 백엔드.

동결 API 4종: GET /api/health, POST /api/simulations, GET /api/simulations/{run_id}, POST /api/approvals
실패 시 fixture 폴백. 모든 실행은 backend/logs/audit.jsonl에 감사 기록을 남긴다.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .simulation import POLICIES, SCENARIOS, run_simulation, SimResult, LINKS
from .safety import evaluate_guard

BACKEND_DIR = Path(os.environ.get("RAINFLOW_BASE_DIR", Path(__file__).resolve().parent.parent))  # PyInstaller 번들 경로 재해석용. 미설정 시 기존 동작과 동일
FIXTURE_PATH = BACKEND_DIR / "fixtures" / "demo_run.json"
AUDIT_PATH = BACKEND_DIR / "logs" / "audit.jsonl"
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
KST = timezone(timedelta(hours=9))

VERSION = "0.1.0"
POLICY_LABELS = {"no_action": "무대응", "fixed_metering": "고정 미터링", "corridor_gating": "연속 게이팅"}
SCREEN_STATES = [
    "normal", "rain_warning", "spillback", "policy_compare",
    "safety_review", "operator_approval", "recovery_compare",
]

app = FastAPI(title="RainFlow Sejong", version=VERSION)
RUNS: dict[str, dict] = {}


def audit(event: str, payload: dict) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": datetime.now(KST).isoformat(), "event": event, **payload}
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class SimulationRequest(BaseModel):
    scenario_id: str = Field(examples=["rain_spillback_a"])
    seed: int = 42


class ApprovalRequest(BaseModel):
    run_id: str
    policy_id: str
    decision: str = Field(pattern="^(approve|reject)$")
    operator: str = "demo_operator"
    reason: str = ""


def _kpi(r: SimResult) -> dict:
    return {
        "spillback_time_sec": r.spillback_time_sec,
        "recovery_time_sec": r.recovery_time_sec,
        "total_travel_time_sec": r.total_travel_time_sec,
        "worst_approach_delay_sec": r.worst_approach_delay_sec,
    }


def _pct(cand: float, base: float) -> float:
    if base == 0:
        return 0.0
    return round((cand - base) / base * 100, 1)


def _explain(policy_id: str, r: SimResult, base: SimResult, guard: dict) -> str:
    # 규칙 기반 설명. LLM 없이 동일 응답 구조 유지 (docs/12 AI 원칙)
    if policy_id == "no_action":
        return (
            f"기존 양보운전 유지. spillback 누적 {r.spillback_time_sec:.0f}초, "
            f"총 통행시간 {r.total_travel_time_sec:.0f}초가 비교 기준선이 된다."
        )
    sp = _pct(r.spillback_time_sec, base.spillback_time_sec)
    tt = _pct(r.total_travel_time_sec, base.total_travel_time_sec)
    text = (
        f"{POLICY_LABELS[policy_id]} 적용 시 무대응 대비 spillback 누적 {sp:+.1f}%, "
        f"총 통행시간 {tt:+.1f}%."
    )
    if guard["passed"]:
        text += " 모든 안전·공정성 가드를 통과했다."
    else:
        codes = ", ".join(v["code"] for v in guard["violations"])
        text += f" 가드 위반({codes})으로 적용 불가."
    return text


def _screen_state_at(t: int, first_spill: int | None) -> str:
    if t < 900:
        return "normal"
    if first_spill is None or t < first_spill:
        return "rain_warning"
    if t < 2700:
        return "spillback"
    return "recovery_compare"


def build_run(scenario_id: str, seed: int) -> dict:
    t0 = time.perf_counter()
    results = {p: run_simulation(scenario_id, seed, p) for p in POLICIES}
    base = results["no_action"]
    guards = {p: evaluate_guard(results[p], base) for p in POLICIES}
    guards["no_action"] = {"passed": True, "violations": [], "note": "기준선. 가드 판정 대상 아님"}

    first_spill = None
    for entry in base.timeline:
        if any(l["spillback"] for l in entry["links"]):
            first_spill = entry["t_sec"]
            break

    timeline = []
    for entry in base.timeline:
        timeline.append({**entry, "screen_state": _screen_state_at(entry["t_sec"], first_spill)})

    passed = [p for p in ("corridor_gating", "fixed_metering") if guards[p]["passed"]]
    best = passed[0] if passed else "no_action"
    applied = results[best]

    run_id = f"live-{scenario_id}-s{seed}"
    run = {
        "run_id": run_id,
        "result_source": "live_simulation",
        "provisional": True,
        "generated_at": datetime.now(KST).isoformat(),
        "network_version": "sejong-corridor-v0",
        "note": "결정론적 큐 모델 계산 결과. 합성 데이터이며 실제 세종시 실측 성과가 아니다.",
        "scenario": {
            "scenario_id": scenario_id,
            "seed": seed,
            "rain_level": SCENARIOS[scenario_id]["rain_level"],
            "duration_sec": 3600,
            "incident": SCENARIOS[scenario_id]["incident"],
        },
        "screen_states": SCREEN_STATES,
        "network": {
            "roundabouts": ["R1", "R2", "R3"],
            "links": [{"link_id": l, "storage_veh": s} for l, s in LINKS.items()],
            "approaches": list(base.approach_p95_delay.keys()),
        },
        "timeline": timeline,
        "policies": [
            {
                "policy_id": p,
                "label": POLICY_LABELS[p],
                "kpi": _kpi(results[p]),
                "extra": {
                    "spillback_events": results[p].spillback_events,
                    "completed_trips": results[p].completed_trips,
                    "diversion_delay_sec": results[p].diversion_delay_sec,
                    "safety_proxy_hard_brakes": results[p].hard_brakes,
                    "approach_p95_delay": results[p].approach_p95_delay,
                },
                "delta_vs_no_action": {
                    "spillback_time_pct": _pct(results[p].spillback_time_sec, base.spillback_time_sec),
                    "total_travel_time_pct": _pct(results[p].total_travel_time_sec, base.total_travel_time_sec),
                    "worst_approach_delay_pct": _pct(results[p].worst_approach_delay_sec, base.worst_approach_delay_sec),
                },
                "guard": guards[p],
                "explanation": _explain(p, results[p], base, guards[p]),
            }
            for p in POLICIES
        ],
        "approval": {"status": "pending", "policy_id": best},
        "recovery_compare": {
            "no_action": _kpi(base),
            "applied": _kpi(applied),
            "improvement": {
                "spillback_time_pct": _pct(applied.spillback_time_sec, base.spillback_time_sec),
                "recovery_time_pct": _pct(applied.recovery_time_sec, base.recovery_time_sec),
                "total_travel_time_pct": _pct(applied.total_travel_time_sec, base.total_travel_time_sec),
                "worst_approach_delay_pct": _pct(applied.worst_approach_delay_sec, base.worst_approach_delay_sec),
            },
        },
        "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
    }
    return run


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": VERSION,
        "fixture_available": FIXTURE_PATH.exists(),
        "llm": "unavailable",
        "runs_in_memory": len(RUNS),
    }


@app.post("/api/simulations")
def create_simulation(req: SimulationRequest):
    try:
        run = build_run(req.scenario_id, req.seed)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:  # 폴백: 계산 실패 시 fixture 반환 (docs/10 규칙)
        audit("simulation_fallback", {"error": str(e), "scenario_id": req.scenario_id, "seed": req.seed})
        run = load_fixture()
        run["result_source"] = "fixture"
    RUNS[run["run_id"]] = run
    audit(
        "simulation_created",
        {
            "run_id": run["run_id"],
            "scenario_id": req.scenario_id,
            "seed": req.seed,
            "result_source": run["result_source"],
            "guard_summary": {p["policy_id"]: p["guard"]["passed"] for p in run["policies"]},
        },
    )
    return {
        "run_id": run["run_id"],
        "status": "completed",
        "result_source": run["result_source"],
        "url": f"/api/simulations/{run['run_id']}",
    }


@app.get("/api/simulations/{run_id}")
def get_simulation(run_id: str):
    if run_id in RUNS:
        return RUNS[run_id]
    if run_id == "fixture-day1-001":
        return load_fixture()
    raise HTTPException(status_code=404, detail="run_id not found")


@app.post("/api/approvals")
def create_approval(req: ApprovalRequest):
    run = RUNS.get(req.run_id) or (load_fixture() if req.run_id == "fixture-day1-001" else None)
    if run is None:
        raise HTTPException(status_code=404, detail="run_id not found")
    policy = next((p for p in run["policies"] if p["policy_id"] == req.policy_id), None)
    if policy is None:
        raise HTTPException(status_code=422, detail="unknown policy_id")

    if req.decision == "approve" and not policy["guard"]["passed"]:
        audit("approval_rejected_by_guard", {"run_id": req.run_id, "policy_id": req.policy_id,
                                             "violations": policy["guard"]["violations"]})
        raise HTTPException(
            status_code=409,
            detail={
                "message": "안전·공정성 가드를 위반한 후보는 승인할 수 없다",
                "violations": policy["guard"]["violations"],
            },
        )

    status = "approved" if req.decision == "approve" else "rejected"
    run["approval"] = {
        "status": status,
        "policy_id": req.policy_id,
        "operator": req.operator,
        "decided_at": datetime.now(KST).isoformat(),
        "reason": req.reason,
    }
    audit("approval_decided", {"run_id": req.run_id, "policy_id": req.policy_id,
                               "status": status, "operator": req.operator, "reason": req.reason})
    return run["approval"]


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

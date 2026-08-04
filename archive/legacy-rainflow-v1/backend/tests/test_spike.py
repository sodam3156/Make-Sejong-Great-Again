"""이슈 #9 스파이크 통과 기준 검증 테스트."""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.simulation import run_simulation
from backend.app.main import app, build_run, FIXTURE_PATH

ROOT = Path(__file__).resolve().parent.parent.parent
client = TestClient(app)


def test_reproducibility_same_seed():
    a = build_run("rain_spillback_a", 42)
    b = build_run("rain_spillback_a", 42)
    a.pop("generated_at"); b.pop("generated_at")
    a.pop("elapsed_ms"); b.pop("elapsed_ms")
    assert a == b


def test_different_seed_differs():
    a = run_simulation("rain_spillback_a", 1, "no_action")
    b = run_simulation("rain_spillback_a", 2, "no_action")
    assert a.total_travel_time_sec != b.total_travel_time_sec


def test_dry_base_no_spillback():
    r = run_simulation("dry_base", 42, "no_action")
    assert r.spillback_time_sec == 0


@pytest.mark.parametrize("scenario", ["rain_spillback_a", "rain_spillback_b"])
def test_rain_causes_spillback(scenario):
    r = run_simulation(scenario, 42, "no_action")
    assert r.spillback_time_sec > 0
    assert r.spillback_events >= 1


@pytest.mark.parametrize("scenario", ["rain_spillback_a", "rain_spillback_b"])
@pytest.mark.parametrize("seed", range(1, 11))
def test_spike_pass_criteria_10_seeds(scenario, seed):
    """스파이크 통과 기준: gating이 spillback 30%↓, TTT 10%↓, 공정성·안전 가드 통과."""
    run = build_run(scenario, seed)
    policies = {p["policy_id"]: p for p in run["policies"]}
    gating = policies["corridor_gating"]
    assert gating["delta_vs_no_action"]["spillback_time_pct"] <= -30.0
    assert gating["delta_vs_no_action"]["total_travel_time_pct"] <= -10.0
    assert gating["guard"]["passed"] is True


def test_fixed_metering_fails_fairness_guard():
    run = build_run("rain_spillback_a", 42)
    metering = next(p for p in run["policies"] if p["policy_id"] == "fixed_metering")
    assert metering["guard"]["passed"] is False
    codes = {v["code"] for v in metering["guard"]["violations"]}
    assert "FAIRNESS_P95_EXCEEDED" in codes


def test_api_flow_and_guard_rejection():
    r = client.post("/api/simulations", json={"scenario_id": "rain_spillback_a", "seed": 42})
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    assert r.json()["result_source"] == "live_simulation"

    detail = client.get(f"/api/simulations/{run_id}").json()
    assert detail["result_source"] == "live_simulation"
    assert set(detail["recovery_compare"]["no_action"]) == {
        "spillback_time_sec",
        "recovery_time_sec",
        "recovery_observed",
        "total_travel_time_sec",
        "worst_approach_delay_sec",
    }

    # 가드 위반 후보 승인은 409로 거부
    rej = client.post("/api/approvals", json={"run_id": run_id, "policy_id": "fixed_metering",
                                              "decision": "approve"})
    assert rej.status_code == 409

    # 가드 통과 후보는 승인 가능
    ok = client.post("/api/approvals", json={"run_id": run_id, "policy_id": "corridor_gating",
                                             "decision": "approve", "reason": "test"})
    assert ok.status_code == 200
    assert ok.json()["status"] == "approved"


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_fixture_matches_contract_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "contracts" / "rainflow.schema.json").read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(fixture, schema)


def test_live_run_matches_contract_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "contracts" / "rainflow.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(build_run("rain_spillback_a", 42), schema)
    jsonschema.validate(build_run("rain_spillback_b", 7), schema)
    jsonschema.validate(build_run("dry_base", 42), schema)

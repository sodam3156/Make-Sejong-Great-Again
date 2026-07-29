"""Generate one QA-canonical run into fixture, script, screen, and evidence."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.app.main import (  # noqa: E402
    DATASET_ID,
    _append_state,
    _set_applied_policy,
    app,
    build_run,
)

FROZEN_AT = "2026-07-29T20:25:09+09:00"
FREEZE_ID = "freeze-20260729-202509-kst"
SCENARIO_ID = "rain_spillback_a"
SEED = 42
SOURCE_FILES = (
    "backend/app/decision.py",
    "backend/app/domain.py",
    "backend/app/main.py",
    "backend/app/policies.py",
    "backend/app/safety.py",
    "backend/app/simulation.py",
    "backend/README.template.md",
    "contracts/rainflow.schema.json",
    "docs/09_RAINFLOW_SEJONG.md",
    "docs/16_DEMO_SCRIPT.template.md",
    "docs/evidence/provisional_parameters.md",
    "frontend/index.html",
    "scripts/generate_contract_artifacts.py",
)


def _json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _source_git_sha() -> str:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", *SOURCE_FILES],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _source_tree_checksum() -> str:
    digest = hashlib.sha256()
    for relative in SOURCE_FILES:
        path = ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        # Git stores these text sources with LF, while Windows checkouts may
        # materialize CRLF. Keep the freeze identity stable across platforms.
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
        digest.update(b"\0")
    return digest.hexdigest()


def _freeze_meta() -> dict[str, Any]:
    return {
        "freeze_id": FREEZE_ID,
        "frozen_at": FROZEN_AT,
        "git_commit_sha": _source_git_sha(),
        "source_tree_checksum": _source_tree_checksum(),
        "scenario_id": SCENARIO_ID,
        "seed": SEED,
    }


def _completed_run(
    result_source: str,
    run_id: str,
    freeze_meta: dict[str, Any],
) -> dict[str, Any]:
    run = build_run(SCENARIO_ID, SEED, freeze_meta=freeze_meta)
    source_live_run_id = run["run_id"]
    recommended_id = run["decision"]["recommended_policy_id"]
    recommended = next(
        policy
        for policy in run["policies"]
        if policy["policy_id"] == recommended_id
    )
    if not recommended["guard"]["passed"]:
        raise RuntimeError("the generated demo recommendation did not pass the guard")

    run["run_id"] = run_id
    run["result_source"] = result_source
    run["generated_at"] = FROZEN_AT
    run["elapsed_ms"] = 0.0
    run["note"] = (
        "rainflow-kpi-v2로 재동결한 provisional 합성 데모 결과. "
        "실제 세종시 실측 성과나 실제 도로 제어 결과가 아니다."
    )
    run["reproducibility"]["source_live_run_id"] = source_live_run_id
    _append_state(run, "HUMAN_APPROVED")
    _set_applied_policy(run, recommended)
    _append_state(run, "TWIN_APPLIED")
    _append_state(run, "EVALUATED")
    run["approval"] = {
        "status": "approved",
        "policy_id": recommended_id,
        "operator": "demo_operator",
        "requested_at": FROZEN_AT,
        "decided_at": FROZEN_AT,
        "reason": "QA v2 가드 통과 후보 중 규칙 기반 안전 점수가 가장 높음",
        "result_source": result_source,
        "workflow_state": run["workflow_state"],
    }
    return run


def _policy(run: dict[str, Any], policy_id: str) -> dict[str, Any]:
    return next(
        policy for policy in run["policies"]
        if policy["policy_id"] == policy_id
    )


def _number(value: float | int) -> str:
    numeric = float(value)
    return str(int(numeric)) if numeric.is_integer() else f"{numeric:.1f}"


def _link(step: dict[str, Any], link_id: str) -> dict[str, Any]:
    return next(item for item in step["links"] if item["link_id"] == link_id)


def _guard_worsen(policy: dict[str, Any], approach: str) -> str:
    violation = next(
        item
        for item in policy["guard"]["violations"]
        if item["code"] == "FAIRNESS_P95_EXCEEDED"
        and item["detail"].startswith(approach)
    )
    return _number(violation["observed_pct"])


def _render_demo_script(run: dict[str, Any]) -> str:
    template = (
        ROOT / "docs" / "16_DEMO_SCRIPT.template.md"
    ).read_text(encoding="utf-8")
    timeline = run["timeline"]
    t0 = timeline[0]
    rain = next(
        step for step in reversed(timeline)
        if step["screen_state"] == "rain_warning"
    )
    spill = next(
        step for step in timeline
        if any(link["spillback"] for link in step["links"])
    )
    no_action = _policy(run, "no_action")
    fixed = _policy(run, "fixed_metering")
    gating = _policy(run, "corridor_gating")
    values = {
        "FREEZE_ID": run["reproducibility"]["freeze_id"],
        "SOURCE_RUN_ID": run["reproducibility"]["source_live_run_id"],
        "RESULT_CHECKSUM": run["reproducibility"]["result_checksum"],
        "T0_L12_OCC_PCT": _number(_link(t0, "L12")["occupancy_ratio"] * 100),
        "T0_L23_OCC_PCT": _number(_link(t0, "L23")["occupancy_ratio"] * 100),
        "T0_BYPASS_OCC_PCT": _number(_link(t0, "BYPASS")["occupancy_ratio"] * 100),
        "RAIN_L23_OCC_PCT": _number(_link(rain, "L23")["occupancy_ratio"] * 100),
        "RAIN_L23_QUEUE": _number(_link(rain, "L23")["queue_veh"]),
        "RAIN_SAMPLE_T": _number(rain["t_sec"]),
        "SPILL_L23_OCC_PCT": _number(_link(spill, "L23")["occupancy_ratio"] * 100),
        "SPILL_L23_QUEUE": _number(_link(spill, "L23")["queue_veh"]),
        "SPILL_SAMPLE_T": _number(spill["t_sec"]),
        "NO_ACTION_SPILLBACK": _number(no_action["kpi"]["spillback_time_sec"]),
        "FIXED_SPILLBACK": _number(fixed["kpi"]["spillback_time_sec"]),
        "GATING_SPILLBACK": _number(gating["kpi"]["spillback_time_sec"]),
        "FIXED_SPILLBACK_DELTA": _number(
            fixed["delta_vs_no_action"]["spillback_time_pct"]
        ),
        "FIXED_SPILLBACK_DELTA_ABS": _number(
            abs(fixed["delta_vs_no_action"]["spillback_time_pct"])
        ),
        "GATING_SPILLBACK_DELTA": _number(
            gating["delta_vs_no_action"]["spillback_time_pct"]
        ),
        "FIXED_R1W_WORSEN": _guard_worsen(fixed, "R1_W"),
        "FIXED_R2S_WORSEN": _guard_worsen(fixed, "R2_S"),
        "GATING_DIVERSION_DELAY": _number(
            gating["extra"]["diversion_delay_sec"]
        ),
        "NO_ACTION_TTT": _number(no_action["kpi"]["total_travel_time_sec"]),
        "GATING_RECOVERY": _number(gating["kpi"]["recovery_time_sec"]),
        "GATING_TTT": _number(gating["kpi"]["total_travel_time_sec"]),
        "GATING_TTT_DELTA": _number(
            gating["delta_vs_no_action"]["total_travel_time_pct"]
        ),
        "GATING_TTT_DELTA_ABS": _number(
            abs(gating["delta_vs_no_action"]["total_travel_time_pct"])
        ),
        "GATING_DELAY_DELTA": _number(
            gating["delta_vs_no_action"]["worst_approach_delay_pct"]
        ),
    }
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    if "{{" in template or "}}" in template:
        raise RuntimeError("unresolved demo script placeholder")
    return template


def _render_backend_readme(run: dict[str, Any]) -> str:
    template = (
        ROOT / "backend" / "README.template.md"
    ).read_text(encoding="utf-8")
    no_action = _policy(run, "no_action")
    fixed = _policy(run, "fixed_metering")
    gating = _policy(run, "corridor_gating")
    values = {
        "SOURCE_RUN_ID": run["reproducibility"]["source_live_run_id"],
        "RESULT_CHECKSUM": run["reproducibility"]["result_checksum"],
        "NO_ACTION_SPILLBACK": _number(no_action["kpi"]["spillback_time_sec"]),
        "NO_ACTION_TTT": _number(no_action["kpi"]["total_travel_time_sec"]),
        "FIXED_SPILLBACK_DELTA": _number(
            fixed["delta_vs_no_action"]["spillback_time_pct"]
        ),
        "FIXED_TTT_DELTA": _number(
            fixed["delta_vs_no_action"]["total_travel_time_pct"]
        ),
        "GATING_SPILLBACK_DELTA": _number(
            gating["delta_vs_no_action"]["spillback_time_pct"]
        ),
        "GATING_TTT_DELTA": _number(
            gating["delta_vs_no_action"]["total_travel_time_pct"]
        ),
    }
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    if "{{" in template or "}}" in template:
        raise RuntimeError("unresolved backend README placeholder")
    return template


def _percentile(values: list[float], proportion: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * proportion
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return round(
        ordered[lower] * (1 - weight) + ordered[upper] * weight,
        1,
    )


def _seed_matrix(freeze_meta: dict[str, Any]) -> dict[str, Any]:
    scenarios: dict[str, Any] = {}
    for scenario_id in ("rain_spillback_a", "rain_spillback_b"):
        rows = []
        for seed in range(1, 11):
            run = build_run(scenario_id, seed, freeze_meta=freeze_meta)
            gating = _policy(run, "corridor_gating")
            rows.append(
                {
                    "seed": seed,
                    "run_id": run["run_id"],
                    "result_checksum": run["reproducibility"]["result_checksum"],
                    "spillback_time_pct": gating["delta_vs_no_action"][
                        "spillback_time_pct"
                    ],
                    "total_travel_time_pct": gating["delta_vs_no_action"][
                        "total_travel_time_pct"
                    ],
                    "guard_passed": gating["guard"]["passed"],
                }
            )
        scenarios[scenario_id] = {
            "runs": rows,
            "summary": {
                metric: {
                    "median": round(statistics.median(row[metric] for row in rows), 1),
                    "p10": _percentile([row[metric] for row in rows], 0.10),
                    "p90": _percentile([row[metric] for row in rows], 0.90),
                }
                for metric in ("spillback_time_pct", "total_travel_time_pct")
            },
            "guard_failure_seeds": [
                row["seed"] for row in rows if not row["guard_passed"]
            ],
        }
    return {
        "freeze_id": FREEZE_ID,
        "git_commit_sha": freeze_meta["git_commit_sha"],
        "source_tree_checksum": freeze_meta["source_tree_checksum"],
        "dataset_id": DATASET_ID,
        "parameter_set_version": "rainflow-provisional-v2",
        "kpi_definition_version": "rainflow-kpi-v2",
        "guard_version": "rainflow-guard-v2",
        "provisional": True,
        "scenarios": scenarios,
    }


def render_artifacts() -> dict[Path, str]:
    freeze_meta = _freeze_meta()
    fixture = _completed_run("fixture", "fixture-qa-v2-001", freeze_meta)
    cached = _completed_run("cached_simulation", "cached-qa-v2-001", freeze_meta)
    openapi = copy.deepcopy(app.openapi())
    artifacts = {
        ROOT / "backend" / "fixtures" / "demo_freeze_meta.json": _json(
            freeze_meta
        ),
        ROOT / "backend" / "fixtures" / "demo_run.json": _json(fixture),
        ROOT / "backend" / "fixtures" / "cached_run.json": _json(cached),
        ROOT / "frontend" / "demo_run.js": (
            "window.DEMO_RUN = "
            + json.dumps(fixture, ensure_ascii=False, indent=2, sort_keys=True)
            + ";\n"
        ),
        ROOT / "backend" / "README.md": _render_backend_readme(fixture),
        ROOT / "docs" / "16_DEMO_SCRIPT.md": _render_demo_script(fixture),
        ROOT / "docs" / "evidence" / "demo_kpi_seed_matrix_20260729.json": _json(
            _seed_matrix(freeze_meta)
        ),
        ROOT / "contracts" / "openapi.json": _json(openapi),
    }
    manifest = {
        "freeze_id": FREEZE_ID,
        "frozen_at": FROZEN_AT,
        "source": {
            **freeze_meta,
            "run_id": fixture["reproducibility"]["source_live_run_id"],
            "fixture_run_id": fixture["run_id"],
            "result_checksum": fixture["reproducibility"]["result_checksum"],
            "provisional": True,
        },
        "artifacts": {
            str(path.relative_to(ROOT)).replace("\\", "/"): _sha256_text(content)
            for path, content in artifacts.items()
        },
    }
    artifacts[
        ROOT / "docs" / "evidence" / "demo_freeze_20260729.json"
    ] = _json(manifest)
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if committed artifacts differ from generated content",
    )
    args = parser.parse_args()
    artifacts = render_artifacts()
    mismatches = []
    for path, content in artifacts.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                mismatches.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(path.relative_to(ROOT))
    if mismatches:
        print(
            "out-of-date generated artifacts: " + ", ".join(mismatches),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Generate the verified demo fixture, frontend copy, cache, and OpenAPI snapshot."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.app.main import (  # noqa: E402
    _append_state,
    _set_applied_policy,
    app,
    build_run,
)

FROZEN_AT = "2026-07-28T23:00:00+09:00"


def _completed_run(result_source: str, run_id: str) -> dict:
    run = build_run("rain_spillback_a", 42)
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
        "검증된 결정론적 큐 모델에서 동결한 합성 데모 결과. "
        "실제 세종시 실측 성과나 실제 도로 제어 결과가 아니다."
    )
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
        "reason": "가드 통과 후보 중 규칙 기반 안전 점수가 가장 높음",
        "result_source": result_source,
        "workflow_state": run["workflow_state"],
    }
    return run


def _json(data: object) -> str:
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def render_artifacts() -> dict[Path, str]:
    fixture = _completed_run("fixture", "fixture-day1-001")
    cached = _completed_run("cached_simulation", "cached-day1-001")
    openapi = copy.deepcopy(app.openapi())
    return {
        ROOT / "backend" / "fixtures" / "demo_run.json": _json(fixture),
        ROOT / "backend" / "fixtures" / "cached_run.json": _json(cached),
        ROOT / "frontend" / "demo_run.js": (
            "window.DEMO_RUN = "
            + json.dumps(fixture, ensure_ascii=False, indent=2, sort_keys=True)
            + ";\n"
        ),
        ROOT / "contracts" / "openapi.json": _json(openapi),
    }


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
        print("out-of-date generated artifacts:", ", ".join(mismatches), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

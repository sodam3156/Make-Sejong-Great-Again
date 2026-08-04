"""Generate the deterministic offline fixture shared by backend and Unity."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.app.domain import MissionEvaluationRequestV1  # noqa: E402
from backend.app.game import evaluate_mission, mission_catalog  # noqa: E402

OUTPUTS = (
    ROOT / "backend" / "fixtures" / "game_missions.json",
    ROOT
    / "unity"
    / "RainFlowGame"
    / "Assets"
    / "StreamingAssets"
    / "fixture"
    / "game_missions.json",
)

WINNING_POLICY = {
    "schema_version": "policy-design-v1",
    "trigger_occupancy_pct": 65,
    "metering_strength_pct": 90,
    "diversion_strength": 10,
}
MISSION_REGIONS = {
    "rain_commute": "seonggeum_cheongsa",
    "rain_incident": "cheongsa_sejong",
    "corridor_final": "eojin_corridor",
}


def render() -> str:
    evaluations = {}
    for mission_id, region_id in MISSION_REGIONS.items():
        request = MissionEvaluationRequestV1.model_validate(
            {
                "region_id": region_id,
                "seed": 42,
                "policy_design": WINNING_POLICY,
                "progress": {},
            }
        )
        evaluations[mission_id] = evaluate_mission(mission_id, request)
    payload = {
        "fixture_version": "game-fixture-v1",
        "catalog": mission_catalog(),
        "evaluations": evaluations,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> None:
    rendered = render()
    for output in OUTPUTS:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(output.relative_to(ROOT))


if __name__ == "__main__":
    main()

from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest
from fastapi.testclient import TestClient

from backend.app import game
from backend.app.domain import MissionEvaluationRequestV1
from backend.app.main import app
from scripts.build_game_map import OUTPUT as MAP_OUTPUT, render as render_game_map
from scripts.generate_game_fixture import OUTPUTS as GAME_FIXTURE_OUTPUTS, render as render_game_fixture

ROOT = Path(__file__).resolve().parent.parent.parent
CLIENT = TestClient(app)
WINNING_POLICY = {
    "schema_version": "policy-design-v1",
    "trigger_occupancy_pct": 65,
    "metering_strength_pct": 90,
    "diversion_strength": 10,
}


def _request(region_id: str, **progress) -> dict:
    return {
        "region_id": region_id,
        "seed": 42,
        "policy_design": WINNING_POLICY,
        "progress": progress,
    }


def test_mission_catalog_exposes_two_starting_regions_and_three_bots():
    response = CLIENT.get("/api/missions")
    assert response.status_code == 200
    body = response.json()
    starts = [region for region in body["regions"] if region["starting_region"]]
    assert {region["region_id"] for region in starts} == {
        "seonggeum_cheongsa",
        "cheongsa_sejong",
    }
    assert [mission["bot_tier"] for mission in body["missions"]] == [
        "luna",
        "terra",
        "sol",
    ]
    assert [mission["bot_candidate_budget"] for mission in body["missions"]] == [
        9,
        36,
        128,
    ]
    assert body["reality_level"] == "game"
    assert "실제 부동산 가격 예측" in body["out_of_scope"]


def test_same_game_request_is_fully_deterministic():
    payload = _request("seonggeum_cheongsa")
    first = CLIENT.post("/api/missions/rain_commute/evaluate", json=payload)
    second = CLIENT.post("/api/missions/rain_commute/evaluate", json=payload)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


@pytest.mark.parametrize(
    ("mission_id", "region_id", "tier"),
    [
        ("rain_commute", "seonggeum_cheongsa", "luna"),
        ("rain_incident", "cheongsa_sejong", "terra"),
        ("corridor_final", "eojin_corridor", "sol"),
    ],
)
def test_each_bot_is_beatable_with_a_known_safe_policy(mission_id, region_id, tier):
    response = CLIENT.post(
        f"/api/missions/{mission_id}/evaluate",
        json=_request(region_id),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["opponent"]["tier"] == tier
    assert body["player"]["guard"]["passed"] is True
    assert body["progression"]["opponent_score_margin"] >= 0.1
    assert body["success"] is True


def test_starting_region_choice_does_not_change_hidden_mechanics():
    left = CLIENT.post(
        "/api/missions/rain_commute/evaluate",
        json=_request("seonggeum_cheongsa"),
    ).json()
    right = CLIENT.post(
        "/api/missions/rain_commute/evaluate",
        json=_request("cheongsa_sejong"),
    ).json()
    assert left["player"] == right["player"]
    assert left["opponent"] == right["opponent"]
    assert left["satisfaction"] == right["satisfaction"]


@pytest.mark.parametrize(
    ("progress", "expected_mode", "expected_demand"),
    [
        ({"attempts": 3, "last_score_margin": -5}, "support", 0.95),
        (
            {"last_score_margin": 5, "last_completion_time_sec": 90},
            "challenge",
            1.05,
        ),
        ({"attempts": 1, "last_score_margin": 0}, "standard", 1.0),
    ],
)
def test_adaptive_event_is_selected_before_evaluation(
    progress, expected_mode, expected_demand
):
    response = CLIENT.post(
        "/api/missions/rain_commute/evaluate",
        json=_request("seonggeum_cheongsa", **progress),
    )
    assert response.status_code == 200
    event = response.json()["adaptive_event"]
    assert event["mode"] == expected_mode
    assert event["demand_multiplier"] == expected_demand
    if expected_mode == "support":
        assert response.json()["advice"][0]["precise"] is True
    if expected_mode == "challenge":
        assert event["rain_extension_sec"] == 300


def test_equipment_gates_fine_control_ranges():
    locked = _request("seonggeum_cheongsa")
    locked["policy_design"] = {
        "trigger_occupancy_pct": 80,
        "metering_strength_pct": 55,
        "diversion_strength": 15,
    }
    response = CLIENT.post("/api/missions/rain_commute/evaluate", json=locked)
    assert response.status_code == 422

    unlocked = copy.deepcopy(locked)
    unlocked["progress"] = {
        "equipment": ["smart_controller", "dynamic_guidance"]
    }
    response = CLIENT.post("/api/missions/rain_commute/evaluate", json=unlocked)
    assert response.status_code == 200


def test_guard_failure_is_a_hard_failure_with_no_reward(monkeypatch):
    monkeypatch.setattr(
        game,
        "evaluate_guard",
        lambda candidate, baseline: {
            "passed": False,
            "violations": [{"code": "TEST_GUARD", "detail": "blocked"}],
            "rule_version": "test",
        },
    )
    game._run_bot_cached.cache_clear()
    request = MissionEvaluationRequestV1.model_validate(
        _request("seonggeum_cheongsa")
    )
    result = game.evaluate_mission("rain_commute", request)
    assert result["success"] is False
    assert result["progression"]["credits_earned"] == 0
    assert result["player"]["guard"]["violations"][0]["code"] == "TEST_GUARD"
    game._run_bot_cached.cache_clear()


def test_building_growth_changes_next_demand_and_is_not_purchased():
    response = CLIENT.post(
        "/api/missions/rain_commute/evaluate",
        json=_request("seonggeum_cheongsa", building_level=2),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["adaptive_event"]["effective_demand_multiplier"] == 1.05
    assert body["progression"]["building_level_after"] >= 2
    assert body["progression"]["next_demand_bonus_pct"] >= 5


def test_game_response_matches_additive_json_contracts():
    policy_schema = json.loads(
        (ROOT / "contracts" / "policy_design.schema.json").read_text(encoding="utf-8")
    )
    mission_schema = json.loads(
        (ROOT / "contracts" / "mission.schema.json").read_text(encoding="utf-8")
    )
    response = CLIENT.post(
        "/api/missions/rain_commute/evaluate",
        json=_request("seonggeum_cheongsa"),
    )
    assert response.status_code == 200
    body = response.json()
    jsonschema.validate(body["player"]["policy_design"], policy_schema)
    resolver = jsonschema.RefResolver(
        base_uri=(ROOT / "contracts").as_uri() + "/",
        referrer=mission_schema,
        store={policy_schema["$id"]: policy_schema},
    )
    jsonschema.validate(body, mission_schema, resolver=resolver)


def test_unknown_mission_and_wrong_region_are_explicit_errors():
    missing = CLIENT.post(
        "/api/missions/not-real/evaluate",
        json=_request("seonggeum_cheongsa"),
    )
    assert missing.status_code == 404
    wrong_region = CLIENT.post(
        "/api/missions/corridor_final/evaluate",
        json=_request("seonggeum_cheongsa"),
    )
    assert wrong_region.status_code == 422


def test_generated_unity_map_and_fixtures_are_current():
    expected_fixture = render_game_fixture()
    for output in GAME_FIXTURE_OUTPUTS:
        assert output.read_text(encoding="utf-8") == expected_fixture

    expected_map = render_game_map()
    assert MAP_OUTPUT.read_text(encoding="utf-8") == expected_map
    map_payload = json.loads(expected_map)
    assert len(map_payload["roads"]) >= 100
    assert len(expected_map.encode("utf-8")) < 300_000

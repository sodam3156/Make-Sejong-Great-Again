"""플레이 가능 그래프의 구조·안전 불변식 검증.

이 맵 위에서 신호를 설계하므로, 상충 행렬이 틀리면 게임 전체가 틀린다.
`python -m pytest backend/tests -q`
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
MAP_PATH = ROOT / "backend/content/map_eojin_playable.json"
BUILDER = ROOT / "scripts/build_playable_map.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_playable_map", BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def game_map() -> dict:
    return json.loads(MAP_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def builder():
    return _load_builder()


# --- 구조 -------------------------------------------------------------------


def test_every_intersection_has_legs_movements_and_a_default_plan(game_map):
    assert game_map["intersections"], "교차로가 하나도 없다"
    for intersection in game_map["intersections"]:
        assert len(intersection["approaches"]) >= 2, intersection["name"]
        assert intersection["movements"], f"{intersection['name']}에 회전 이동이 없다"
        assert intersection["defaultPlan"]["stages"], f"{intersection['name']}에 기본 계획이 없다"


def test_start_intersections_exist_and_open_their_own_neighbourhood(game_map):
    ids = {intersection["id"] for intersection in game_map["intersections"]}
    starts = game_map["startIntersectionIds"]
    assert len(starts) == 3, "docs/20이 요구하는 시작점은 3개다"
    assert set(starts) <= ids
    by_start = game_map["initiallyOpenLinkIdsByStart"]
    assert set(by_start) == set(starts)
    link_ids = {link["id"] for link in game_map["links"]}
    for start, opened in by_start.items():
        assert opened, f"{start}에서 열려 있는 도로가 없다"
        assert set(opened) <= link_ids
        # 시작점 한 곳이 지도 전체를 열어 버리면 확장할 것이 남지 않는다.
        assert len(opened) < len(link_ids), f"{start}가 지도를 전부 연다"


def test_all_identifier_references_resolve(game_map):
    link_ids = {link["id"] for link in game_map["links"]}
    intersection_ids = {item["id"] for item in game_map["intersections"]}
    for link in game_map["links"]:
        for side in ("fromIntersectionId", "toIntersectionId"):
            if link["kind"] == "street":
                assert link[side] in intersection_ids, link["id"]
        assert link["storageVeh"] >= 4 and link["saturationVehPerSec"] > 0

    for intersection in game_map["intersections"]:
        approach_ids = {approach["id"] for approach in intersection["approaches"]}
        movement_ids = {movement["id"] for movement in intersection["movements"]}
        for approach in intersection["approaches"]:
            assert approach["fromLinkId"] in link_ids
        for movement in intersection["movements"]:
            assert movement["approachId"] in approach_ids
            assert movement["toLinkId"] in link_ids
            assert movement["turn"] in {"through", "left", "right", "uturn"}
        for crossing in intersection["crossings"]:
            assert set(crossing["conflictingMovementIds"]) <= movement_ids
            assert crossing["walkSec"] > 0
        for left, right in intersection["conflictingMovementPairs"]:
            assert left in movement_ids and right in movement_ids

    for building in game_map["buildings"]:
        assert building["linkId"] in link_ids
        assert building["baseVehiclePerCityHour"] > 0


# --- 상충 행렬 ---------------------------------------------------------------


def test_four_leg_intersection_has_the_textbook_sixteen_crossing_conflicts(game_map):
    """4지 교차로의 교차상충점은 16개다. 이 수가 틀리면 상충 규칙이 틀린 것이다."""
    four_leg = [ix for ix in game_map["intersections"] if len(ix["approaches"]) == 4]
    assert four_leg, "4지 교차로가 하나도 없다"
    for intersection in four_leg:
        assert len(intersection["movements"]) == 12, intersection["name"]
        assert len(intersection["conflictingMovementPairs"]) == 16, intersection["name"]


def test_opposing_through_movements_never_conflict(game_map):
    for intersection in game_map["intersections"]:
        count = len(intersection["approaches"])
        if count != 4:
            continue
        conflicts = {tuple(pair) for pair in intersection["conflictingMovementPairs"]}
        through = {
            (movement["fromLegIndex"], movement["toLegIndex"]): movement["id"]
            for movement in intersection["movements"]
            if movement["turn"] == "through"
        }
        for (source, target), left in through.items():
            opposite = through.get((target, source))
            if opposite is None:
                continue
            assert (left, opposite) not in conflicts and (opposite, left) not in conflicts, (
                f"{intersection['name']}: 마주보는 직진이 상충으로 잡혔다"
            )


def test_left_turn_conflicts_with_the_opposing_through(game_map):
    """좌회전의 대표 상충은 맞은편 직진이다. 이걸 놓치면 안전 판정이 무의미하다."""
    checked = 0
    for intersection in game_map["intersections"]:
        if len(intersection["approaches"]) != 4:
            continue
        conflicts = {tuple(pair) for pair in intersection["conflictingMovementPairs"]}
        lefts = {
            movement["fromLegIndex"]: movement
            for movement in intersection["movements"]
            if movement["turn"] == "left"
        }
        throughs = {
            movement["fromLegIndex"]: movement
            for movement in intersection["movements"]
            if movement["turn"] == "through"
        }
        for source, left in lefts.items():
            facing = throughs.get((source + 2) % 4)
            if facing is None:
                continue
            pair = tuple(sorted((left["id"], facing["id"])))
            assert pair in conflicts, (
                f"{intersection['name']}: 좌회전 {left['id']} 와 "
                f"맞은편 직진 {facing['id']} 의 상충이 누락됐다"
            )
            checked += 1
    assert checked, "좌회전·맞은편 직진 쌍을 하나도 확인하지 못했다"


def test_opposing_left_turns_are_compatible(game_map):
    """마주보는 좌회전은 서로 좌측으로 비껴가므로 상충하지 않는다.

    실제 신호 운영에서 양방향 좌회전을 한 현시에 함께 주는 근거이기도 하다.
    여기서 상충으로 잡히면 설계 공간이 근거 없이 좁아진다.
    """
    checked = 0
    for intersection in game_map["intersections"]:
        if len(intersection["approaches"]) != 4:
            continue
        conflicts = {tuple(pair) for pair in intersection["conflictingMovementPairs"]}
        lefts = {
            movement["fromLegIndex"]: movement
            for movement in intersection["movements"]
            if movement["turn"] == "left"
        }
        for source, left in lefts.items():
            facing = lefts.get((source + 2) % 4)
            if facing is None:
                continue
            pair = tuple(sorted((left["id"], facing["id"])))
            assert pair not in conflicts, (
                f"{intersection['name']}: 마주보는 좌회전이 상충으로 잡혔다"
            )
            checked += 1
    assert checked, "마주보는 좌회전 쌍을 하나도 확인하지 못했다"


def test_crossing_traffic_conflicts_are_symmetric_and_not_self_paired(game_map):
    for intersection in game_map["intersections"]:
        for left, right in intersection["conflictingMovementPairs"]:
            assert left != right
        pairs = [tuple(pair) for pair in intersection["conflictingMovementPairs"]]
        assert len(pairs) == len(set(pairs)), f"{intersection['name']}: 중복 상충쌍"
        assert all(pair == tuple(sorted(pair)) for pair in pairs), "상충쌍이 정렬되지 않았다"


# --- 기본 계획 안전성 (hard safety) -------------------------------------------


def test_default_plan_never_greens_two_conflicting_vehicle_movements(game_map):
    """기본 계획은 어떤 단계에서도 상충 이동을 동시에 통과시키지 않는다."""
    for intersection in game_map["intersections"]:
        conflicts = {tuple(pair) for pair in intersection["conflictingMovementPairs"]}
        for stage in intersection["defaultPlan"]["stages"]:
            green = stage["allowedVehicleMovements"]
            for index, left in enumerate(green):
                for right in green[index + 1 :]:
                    assert tuple(sorted((left, right))) not in conflicts, (
                        f"{intersection['name']} {stage['stageId']}: "
                        f"{left} 와 {right} 가 동시에 녹색이다"
                    )


def test_default_plan_never_greens_a_crossing_against_conflicting_vehicles(game_map):
    """보행 녹색과 그 횡단을 지나는 차량 녹색이 겹치면 hard safety 위반이다."""
    for intersection in game_map["intersections"]:
        blocking = {
            crossing["id"]: set(crossing["conflictingMovementIds"])
            for crossing in intersection["crossings"]
        }
        for stage in intersection["defaultPlan"]["stages"]:
            green = set(stage["allowedVehicleMovements"])
            for crossing_id in stage["allowedPedestrianCrossings"]:
                overlap = blocking[crossing_id] & green
                assert not overlap, (
                    f"{intersection['name']} {stage['stageId']}: "
                    f"보행 {crossing_id} 와 차량 {sorted(overlap)} 가 동시에 녹색이다"
                )


def test_default_plan_serves_every_movement_at_least_once(game_map):
    """어떤 이동도 영원히 녹색을 못 받으면 그 방향 차량은 빠져나갈 수 없다."""
    for intersection in game_map["intersections"]:
        served = {
            movement
            for stage in intersection["defaultPlan"]["stages"]
            for movement in stage["allowedVehicleMovements"]
        }
        expected = {movement["id"] for movement in intersection["movements"]}
        assert served == expected, (
            f"{intersection['name']}: 녹색을 못 받는 이동 {sorted(expected - served)}"
        )


def test_default_plan_cycle_length_is_operable(game_map):
    plan_min, plan_max = 30, 240
    for intersection in game_map["intersections"]:
        plan = intersection["defaultPlan"]
        cycle = sum(
            stage["durationSec"] + plan["yellowSec"] + plan["allRedSec"]
            for stage in plan["stages"]
        )
        assert plan_min <= cycle <= plan_max, f"{intersection['name']} 주기 {cycle}초"
        for stage in plan["stages"]:
            assert 5 <= stage["durationSec"] <= 120


# --- 상충 판정 규칙 자체 ------------------------------------------------------


def test_chord_rule_matches_a_hand_checked_four_leg_intersection(builder):
    """원 위의 현 교차 판정이 표준 4지 교차로에서 맞는지 직접 확인한다."""
    entry, exit_, cross = builder._entry_slot, builder._exit_slot, builder._chords_cross
    size = 8

    def movement(source: int, target: int) -> tuple[int, int]:
        return (entry(source, 4), exit_(target, 4))

    north, east, south, west = 0, 1, 2, 3
    # 마주보는 직진은 상충하지 않는다.
    assert not cross(movement(north, south), movement(south, north), size)
    # 직교하는 직진은 상충한다.
    assert cross(movement(north, south), movement(east, west), size)
    # 직진과 맞은편 좌회전은 상충한다. 좌회전 상충의 대표 사례다.
    assert cross(movement(north, south), movement(south, west), size)
    # 마주보는 좌회전은 서로 좌측으로 비껴가므로 상충하지 않는다.
    assert not cross(movement(north, east), movement(south, west), size)
    # 우회전끼리는 상충하지 않는다.
    assert not cross(movement(north, west), movement(south, east), size)
    # 직교하는 직진과 그 흐름을 가로지르는 좌회전은 상충한다.
    assert cross(movement(east, west), movement(north, east), size)


def test_turn_classification_is_right_hand_traffic(builder):
    assert builder._turn_of(0, 2, 4) == "through"
    assert builder._turn_of(0, 1, 4) == "left"
    assert builder._turn_of(0, 3, 4) == "right"


# --- 결정론 ------------------------------------------------------------------


def test_generator_is_deterministic():
    """같은 입력이면 같은 바이트가 나와야 mapVersion을 신뢰할 수 있다."""
    original = MAP_PATH.read_bytes()
    result = subprocess.run(
        [sys.executable, str(BUILDER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, result.stderr
    assert MAP_PATH.read_bytes() == original, "생성기를 다시 돌리니 결과가 달라졌다"


def test_reality_level_separates_public_data_from_synthetic_values(game_map):
    """docs/00: 실제 자료와 합성값의 구분을 화면에 표시할 수 있어야 한다."""
    reality = game_map["realityLevel"]
    assert reality["geometry"].startswith("public_")
    assert reality["adjacency"].startswith("public_")
    for field in ("turnMovements", "signalTiming", "demand"):
        assert reality[field] == "synthetic_generated", field

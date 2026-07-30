"""절재로 회랑 정본 식별 회귀 테스트.

2026-07-29 13:28 KST 실제 세종 도로망 A안 결정을 지킨다.
- 표시명은 공식 교차로명 원문만 쓴다
- R1/R2/R3 같은 내부 키는 사용자에게 보이는 문자열에 노출하지 않는다
- 무엇이 확인된 값이고 무엇이 모형 가정인지 응답에 남긴다
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from backend.app import main as backend_main
from backend.app.simulation import approach_display_name

ROOT = Path(__file__).resolve().parents[2]
INTERNAL_KEY = re.compile(r"\b(R1|R2|R3|L12|L23|BYPASS)\b")
# 사용자에게 그대로 읽히는 문자열 필드. 여기에 내부 키가 새면 화면·발표에 노출된다.
DISPLAY_FIELDS = {
    "display_name",
    "from_display_name",
    "to_display_name",
    "corridor_label",
    "road_name",
    "detail",
    "note",
    "summary",
    "reason",
    "label",
}


def _display_strings(node, field=None):
    """응답 트리에서 사용자 표시용 문자열만 모은다."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _display_strings(value, key)
    elif isinstance(node, list):
        for item in node:
            yield from _display_strings(item, field)
    elif isinstance(node, str) and field in DISPLAY_FIELDS:
        yield field, node


def test_corridor_identity_uses_official_names_and_node_ids():
    network = backend_main.build_run("rain_spillback_a", 42)["network"]

    assert network["road_name"] == "절재로"
    assert [item["display_name"] for item in network["intersections"]] == [
        "성금교차로",
        "청사교차로",
        "세종교차로",
    ]
    # 표시명은 국토교통부 표준노드 ID와 연결돼 있어야 한다.
    for item in network["intersections"]:
        assert len(item["standard_node_ids"]) == 4
        assert all(nid.startswith("413") for nid in item["standard_node_ids"])


def test_no_internal_key_leaks_into_user_visible_text():
    run = backend_main.build_run("rain_spillback_a", 42)

    leaks = [
        (field, text)
        for field, text in _display_strings(run)
        if INTERNAL_KEY.search(text)
    ]
    assert leaks == [], f"내부 키가 표시 문자열에 노출됐다: {leaks}"


def test_frozen_fixture_and_demo_script_carry_no_internal_key():
    fixture = json.loads(
        (ROOT / "backend" / "fixtures" / "demo_run.json").read_text(encoding="utf-8")
    )
    leaks = [
        (field, text)
        for field, text in _display_strings(fixture)
        if INTERNAL_KEY.search(text)
    ]
    assert leaks == [], f"동결 fixture 표시 문자열에 내부 키가 남았다: {leaks}"

    script = (ROOT / "docs" / "16_DEMO_SCRIPT.md").read_text(encoding="utf-8")
    assert not INTERNAL_KEY.search(script), "데모 대사에 내부 키가 남았다"


def test_verification_boundary_is_declared():
    verification = backend_main.build_run("rain_spillback_a", 42)["network"][
        "verification"
    ]

    # 확인한 것과 확인하지 않은 것을 응답이 스스로 밝혀야 한다.
    assert verification["intersection_identity"] == "verified"
    assert verification["intersection_form"] == "unverified"
    assert verification["link_capacity"] == "synthetic"


def test_model_assumed_bypass_is_not_claimed_as_real_road():
    links = backend_main.build_run("rain_spillback_a", 42)["network"]["links"]
    bypass = next(link for link in links if link["link_id"] == "BYPASS")

    assert bypass["real_road"] is False
    assert "실제 도로 아님" in bypass["display_name"]


def test_approach_display_name_maps_direction():
    assert approach_display_name("R1_W") == "성금교차로 서측 진입로"
    assert approach_display_name("R2_S") == "청사교차로 남측 진입로"
    # 알 수 없는 키는 그대로 돌려주어 판정이 조용히 틀리지 않게 한다.
    assert approach_display_name("UNKNOWN") == "UNKNOWN"

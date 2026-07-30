"""절재로 회랑 표시명 회귀 테스트.

2026-07-29 13:28 KST 실제 세종 도로망 A안 결정을 지킨다.
- 화면·발표·문서·시뮬레이션 결과에는 공식 교차로명만 쓴다
- R1/R2/R3 같은 내부 키는 사용자에게 보이는 문자열에 노출하지 않는다
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from backend.app import main as backend_main

ROOT = Path(__file__).resolve().parents[2]
INTERNAL_KEY = re.compile(r"\b(R1|R2|R3|R1_N|R1_W|R2_N|R2_S|R3_N|R3_E|L12|L23|BYPASS)\b")
# 사용자에게 그대로 읽히는 문자열 필드. 여기에 내부 키가 새면 화면·발표에 노출된다.
DISPLAY_FIELDS = {
    "display_name",
    "detail",
    "note",
    "summary",
    "reason",
    "label",
    "model_limitations",
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


def test_corridor_uses_official_names_and_node_ids():
    network = backend_main.build_run("rain_spillback_a", 42)["network"]

    assert [j["display_name"] for j in network["junctions"]] == [
        "성금교차로",
        "청사교차로",
        "세종교차로",
    ]
    for junction in network["junctions"]:
        assert len(junction["node_ids"]) == 4
        assert all(nid.startswith("413") for nid in junction["node_ids"])


def test_no_internal_key_leaks_into_user_visible_text():
    run = backend_main.build_run("rain_spillback_a", 42)

    leaks = [
        (field, text)
        for field, text in _display_strings(run)
        if INTERNAL_KEY.search(text)
    ]
    assert leaks == [], f"내부 키가 표시 문자열에 노출됐다: {leaks}"


def test_approach_labels_are_official_and_not_duplicated():
    run = backend_main.build_run("rain_spillback_a", 42)

    assert run["network"]["approaches"] == [
        "성금교차로 북측 진입로",
        "성금교차로 서측 진입로",
        "청사교차로 남측 진입로",
        "세종교차로 동측 진입로",
    ]
    # 표시명이 이미 "진입로"로 끝나므로 가드 문구가 이를 덧붙이면 안 된다.
    details = [
        violation["detail"]
        for policy in run["policies"]
        for violation in policy["guard"]["violations"]
    ]
    assert details, "가드 위반 사례가 없어 문구를 검증할 수 없다"
    for detail in details:
        assert "진입로 진입로" not in detail, f"진입로가 중복됐다: {detail}"


def test_frozen_artifacts_carry_no_internal_key():
    for relative in (
        "backend/fixtures/demo_run.json",
        "backend/fixtures/cached_run.json",
    ):
        payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        leaks = [
            (field, text)
            for field, text in _display_strings(payload)
            if INTERNAL_KEY.search(text)
        ]
        assert leaks == [], f"{relative} 표시 문자열에 내부 키가 남았다: {leaks}"
        assert "진입로 진입로" not in json.dumps(payload, ensure_ascii=False)

    script = (ROOT / "docs" / "16_DEMO_SCRIPT.md").read_text(encoding="utf-8")
    assert not INTERNAL_KEY.search(script), "데모 대사에 내부 키가 남았다"
    assert "진입로 진입로" not in script

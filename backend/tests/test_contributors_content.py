"""기여자 화면 콘텐츠 검증.

docs/23_TITLE_SCREEN_BACKLOG.md T6: 팀 명단·공개 데이터 출처·오픈소스 고지는 손으로 옮겨 적지
않고 `scripts/build_contributors_content.py`가 실제 원본 파일을 읽어 만든다. 이 테스트는 커밋된
`backend/content/credits.json`이 그 빌더를 지금 다시 돌린 결과와 바이트까지 같은지 확인해
누군가 손으로 값을 고쳐 원본과 어긋나는 것을 잡아낸다.

`python -m pytest backend/tests -q`
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
CONTENT_PATH = ROOT / "backend/content/credits.json"
BUILDER = ROOT / "scripts/build_contributors_content.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_contributors_content", BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder():
    return _load_builder()


@pytest.fixture(scope="module")
def credits_content() -> dict:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def test_committed_file_matches_a_fresh_build_from_source_files(builder, credits_content):
    """손으로 옮겨 적은 값이 원본 파일과 어긋나면 이 테스트가 실패한다."""
    assert builder.build() == credits_content


def test_top_level_sections_present(credits_content):
    assert credits_content["schemaVersion"] == 1
    assert "team" in credits_content
    assert "publicDataSources" in credits_content
    assert "openSourceNotices" in credits_content


def test_team_is_msga_with_five_members(credits_content):
    """archive/legacy-rainflow-v1/docs/18_GAME_SLICE_EXECUTION_PLAN.md의 확정된 팀명·팀원 5인."""
    team = credits_content["team"]
    assert team["name"] == "MSGA (Make Sejong Great Again)"
    assert team["members"] == ["백서준", "최영", "손시우", "김경은", "여하윤"]


def test_public_data_sources_cover_all_seven_official_sources(credits_content):
    entries = credits_content["publicDataSources"]["entries"]
    assert [entry["order"] for entry in entries] == list(range(1, 8))
    for entry in entries:
        assert entry["name"].strip()
        # 항목 6(nodelink_202607291508.csv)만 원본 문서에 하이퍼링크가 없다.
        if entry["order"] != 6:
            assert entry["url"], f"{entry['name']}에 출처 URL이 없다"


def test_open_source_notices_cover_abstreet_and_osm_with_matching_pin(credits_content):
    lock = json.loads((ROOT / "third_party/abstreet.lock.json").read_text(encoding="utf-8"))
    entries = {entry["name"]: entry for entry in credits_content["openSourceNotices"]["entries"]}

    assert set(entries) == {"A/B Street", "OpenStreetMap data"}

    abstreet = entries["A/B Street"]
    assert abstreet["pinnedCommit"] == lock["pinnedCommit"]
    assert abstreet["upstreamUrl"] == lock["upstream"]
    assert abstreet["forkUrl"] == lock["fork"]
    assert abstreet["licenseSpdx"] == lock["license"]["spdx"]

    osm = entries["OpenStreetMap data"]
    assert osm["copyrightUrl"] and osm["attributionGuidanceUrl"]

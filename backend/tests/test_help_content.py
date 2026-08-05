"""도움말 콘텐츠 구조 검증.

본문(첫 3분 안내·조작법·용어)은 코드가 아니라 이 JSON에 있어야 한다
(docs/23_TITLE_SCREEN_BACKLOG.md T5). `python -m pytest backend/tests -q`
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
HELP_PATH = ROOT / "backend/content/help.json"

EXPECTED_TERM_IDS = {"queue", "spillback", "conflict", "saturation"}


@pytest.fixture(scope="module")
def help_content() -> dict:
    return json.loads(HELP_PATH.read_text(encoding="utf-8"))


def test_top_level_sections_present(help_content):
    assert help_content["schemaVersion"] == 1
    assert "firstThreeMinutes" in help_content
    assert "controls" in help_content
    assert "terms" in help_content


def test_first_three_minutes_has_the_seven_canonical_steps_in_order(help_content):
    """docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 6.1절과 정확히 같은 7단계여야 한다."""
    steps = help_content["firstThreeMinutes"]["steps"]
    assert len(steps) == 7
    for index, step in enumerate(steps, start=1):
        assert step["order"] == index
        assert step["text"].strip()


def test_controls_entries_have_action_keys_and_description(help_content):
    entries = help_content["controls"]["entries"]
    assert entries, "조작법 항목이 비어 있다"
    for entry in entries:
        assert entry["action"].strip()
        assert entry["keys"], f"{entry['action']}에 키가 없다"
        assert entry["description"].strip()


def test_terms_cover_exactly_the_four_required_words(help_content):
    """docs/23_TITLE_SCREEN_BACKLOG.md T5가 요구하는 용어 4개: 대기행렬·spillback·상충·포화도."""
    entries = help_content["terms"]["entries"]
    ids = {entry["id"] for entry in entries}
    assert ids == EXPECTED_TERM_IDS
    for entry in entries:
        assert entry["term"].strip()
        assert entry["definition"].strip()
        assert entry["source"].strip(), f"{entry['id']}에 출처가 없다"

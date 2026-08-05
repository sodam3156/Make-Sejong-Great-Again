"""Build the title screen credits content from the actual source-of-record files.

docs/23_TITLE_SCREEN_BACKLOG.md T6 요구사항: "THIRD_PARTY_NOTICES.md와
third_party/abstreet.lock.json을 실제로 읽어 구성한다. 손으로 복사한 사본을 만들지 않는다."

이 스크립트가 사람이 손으로 옮겨 적는 대신 아래 세 원본을 파싱해 하나의 콘텐츠 파일로 만든다.

- 팀명·팀원: archive/legacy-rainflow-v1/docs/18_GAME_SLICE_EXECUTION_PLAN.md
  (현재 docs/에는 팀 구성이 없다 — 리셋 전 문서에만 있다. 게임 규칙이 아니라 제출용 팀 정보라
  docs/00 "archive는 현재 결정을 덮어쓸 수 없다"의 대상이 아니다.)
- 공개 데이터 출처: archive/legacy-rainflow-v1/docs/evidence/public_data_inventory_20260729.md
  3절 "공식 출처" (data/public/2026-07-29/README.md가 이 문서를 근거로 지정한다)
- 오픈소스 고지: THIRD_PARTY_NOTICES.md, third_party/abstreet.lock.json

Deterministic: same input files -> byte-identical output.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEAM_SRC = ROOT / "archive/legacy-rainflow-v1/docs/18_GAME_SLICE_EXECUTION_PLAN.md"
PUBLIC_DATA_SRC = ROOT / "archive/legacy-rainflow-v1/docs/evidence/public_data_inventory_20260729.md"
NOTICES_SRC = ROOT / "THIRD_PARTY_NOTICES.md"
LOCK_SRC = ROOT / "third_party/abstreet.lock.json"
OUTPUT = ROOT / "backend/content/credits.json"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_team() -> dict:
    text = _read(TEAM_SRC)
    name_match = re.search(r"팀명:\s*\*\*(.+?)\*\*", text)
    members_match = re.search(r"팀원:\s*(.+)", text)
    if not name_match or not members_match:
        raise ValueError(f"팀명/팀원 줄을 {TEAM_SRC}에서 찾지 못했다")

    members = [member.strip() for member in members_match.group(1).split(",")]
    return {
        "title": "팀",
        "name": name_match.group(1).strip(),
        "members": members,
        "source": str(TEAM_SRC.relative_to(ROOT)) + " 팀명과 BM 절",
    }


_LIST_ITEM = re.compile(r"^(\d+)\.\s+(.*)$")
_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _parse_official_source_line(order: int, content: str) -> dict:
    link = _MD_LINK.search(content)
    if link:
        name = link.group(1).strip()
        url = link.group(2).strip()
        rest = content[link.end():].lstrip()
        rest = rest.lstrip(":—-").strip()
        note = rest or None
        return {"order": order, "name": name, "url": url, "note": note}

    # 항목 6처럼 링크 없이 백틱 파일명 + 설명만 있는 경우.
    backtick = re.search(r"`([^`]+)`", content)
    if backtick:
        name = backtick.group(1).strip()
        rest = content[backtick.end():].lstrip()
        rest = rest.lstrip(":—-").strip()
        note = rest or None
        return {"order": order, "name": name, "url": None, "note": note}

    return {"order": order, "name": content.strip(), "url": None, "note": None}


def build_public_data_sources() -> dict:
    text = _read(PUBLIC_DATA_SRC)
    section_match = re.search(r"## 3\. 공식 출처\n(.*?)\n##", text, re.DOTALL)
    if not section_match:
        raise ValueError(f"'## 3. 공식 출처' 절을 {PUBLIC_DATA_SRC}에서 찾지 못했다")

    entries = []
    for line in section_match.group(1).splitlines():
        item = _LIST_ITEM.match(line.strip())
        if not item:
            continue
        order = int(item.group(1))
        entries.append(_parse_official_source_line(order, item.group(2)))

    if not entries:
        raise ValueError("공식 출처 목록이 비어 있다")

    return {
        "title": "공개 데이터 출처",
        "entries": entries,
        "source": str(PUBLIC_DATA_SRC.relative_to(ROOT)) + " 3절",
    }


def _parse_notice_sections(text: str) -> dict:
    sections = {}
    for block in re.split(r"^## ", text, flags=re.MULTILINE)[1:]:
        lines = block.splitlines()
        heading = lines[0].strip()
        bullets = {}
        notes = []
        for line in lines[1:]:
            stripped = line.strip()
            if not stripped:
                continue
            bullet = re.match(r"^-\s*([^:]+):\s*(.+)$", stripped)
            if bullet:
                bullets[bullet.group(1).strip()] = bullet.group(2).strip()
            else:
                notes.append(stripped)
        sections[heading] = {"bullets": bullets, "note": " ".join(notes).strip()}
    return sections


def build_open_source_notices() -> dict:
    notices = _parse_notice_sections(_read(NOTICES_SRC))
    lock = json.loads(_read(LOCK_SRC))

    abstreet = notices.get("A/B Street")
    if abstreet is None:
        raise ValueError(f"'## A/B Street' 절을 {NOTICES_SRC}에서 찾지 못했다")

    notices_upstream = abstreet["bullets"].get("Upstream")
    notices_fork = abstreet["bullets"].get("TATS fork")
    notices_pin = (abstreet["bullets"].get("Pinned source") or "").strip("`")

    if notices_upstream != lock["upstream"]:
        raise ValueError(
            f"upstream 불일치: {NOTICES_SRC}={notices_upstream} vs {LOCK_SRC}={lock['upstream']}"
        )
    if notices_fork != lock["fork"]:
        raise ValueError(
            f"fork 불일치: {NOTICES_SRC}={notices_fork} vs {LOCK_SRC}={lock['fork']}"
        )
    if notices_pin != lock["pinnedCommit"]:
        raise ValueError(
            f"pinned commit 불일치: {NOTICES_SRC}={notices_pin} vs {LOCK_SRC}={lock['pinnedCommit']}"
        )

    osm = notices.get("OpenStreetMap data")
    if osm is None:
        raise ValueError(f"'## OpenStreetMap data' 절을 {NOTICES_SRC}에서 찾지 못했다")

    entries = [
        {
            "name": "A/B Street",
            "license": abstreet["bullets"].get("License"),
            "licenseSpdx": lock["license"]["spdx"],
            "upstreamUrl": lock["upstream"],
            "forkUrl": lock["fork"],
            "pinnedCommit": lock["pinnedCommit"],
            "pinnedCommitUrl": lock["pinnedCommitUrl"],
            "note": abstreet["note"],
        },
        {
            "name": "OpenStreetMap data",
            "license": "Open Database License (ODbL)",
            "copyrightUrl": osm["bullets"].get("Copyright and licence"),
            "attributionGuidanceUrl": osm["bullets"].get("Attribution guidance"),
            "note": osm["note"],
        },
    ]

    return {
        "title": "오픈소스 고지",
        "entries": entries,
        "source": f"{NOTICES_SRC.relative_to(ROOT)}, {LOCK_SRC.relative_to(ROOT)}",
    }


def build() -> dict:
    return {
        "schemaVersion": 1,
        "team": build_team(),
        "publicDataSources": build_public_data_sources(),
        "openSourceNotices": build_open_source_notices(),
    }


def main() -> None:
    payload = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(
        (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    print(
        f"{OUTPUT.relative_to(ROOT)}: "
        f"팀원 {len(payload['team']['members'])}명 · "
        f"공개 데이터 출처 {len(payload['publicDataSources']['entries'])}개 · "
        f"오픈소스 고지 {len(payload['openSourceNotices']['entries'])}개 · "
        f"{OUTPUT.stat().st_size:,} bytes"
    )


if __name__ == "__main__":
    main()

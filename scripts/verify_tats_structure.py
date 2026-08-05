"""Fail CI when legacy RainFlow product paths leak back into the active root."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = (
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "docs/00_TATS_SOURCE_OF_TRUTH.md",
    "docs/01_ABSTREET_ENGINE_DECISION.md",
    "docs/19_TATS_UI_UX_DIRECTION_V1.md",
    "docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md",
    "ai-context/PROJECT_STACK.yaml",
    "contracts/game-v2/contract-status.json",
    "unity/TATSGame/Packages/manifest.json",
    "unity/TATSGame/ProjectSettings/ProjectVersion.txt",
    "unity/TATSGame/Assets/StreamingAssets/map/eojin_map.json",
    "archive/legacy-rainflow-v1/MANIFEST.md",
    "third_party/abstreet.lock.json",
)

FORBIDDEN_ACTIVE_PATHS = (
    "frontend",
    "launcher",
    "release",
    "unity/RainFlowGame",
    "rainflow-sejong.spec",
    "Dockerfile",
    "compose.yaml",
    "contracts/rainflow.schema.json",
    "contracts/policy_design.schema.json",
)

JSON_FILES = (
    "contracts/game-v2/contract-status.json",
    "unity/TATSGame/Packages/manifest.json",
    "unity/TATSGame/Assets/PM/pm_backlog.json",
    "unity/TATSGame/Assets/StreamingAssets/map/eojin_map.json",
    "third_party/abstreet.lock.json",
)

MARKDOWN_FILES = (
    "README.md",
    "docs/00_TATS_SOURCE_OF_TRUTH.md",
    "docs/01_ABSTREET_ENGINE_DECISION.md",
    "docs/19_TATS_UI_UX_DIRECTION_V1.md",
    "docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md",
    "docs/21_PM_AUTOMATION_RUNBOOK.md",
    "backend/README.md",
    "contracts/game-v2/README.md",
    "unity/TATSGame/README.md",
    "data/public/2026-07-29/README.md",
    "THIRD_PARTY_NOTICES.md",
)


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).exists():
            errors.append(f"missing required path: {relative}")
    for relative in FORBIDDEN_ACTIVE_PATHS:
        if (ROOT / relative).exists():
            errors.append(f"legacy path must stay archived: {relative}")
    for relative in JSON_FILES:
        path = ROOT / relative
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {relative}: {exc}")
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for relative in MARKDOWN_FILES:
        markdown = ROOT / relative
        for target in link_pattern.findall(markdown.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local_target = target.split("#", 1)[0]
            resolved = (markdown.parent / local_target).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                errors.append(f"broken local link in {relative}: {target}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "TATS" not in readme or "archive/legacy-rainflow-v1" not in readme:
        errors.append("README must identify TATS and the legacy quarantine")
    engine_lock = json.loads(
        (ROOT / "third_party/abstreet.lock.json").read_text(encoding="utf-8")
    )
    if engine_lock.get("pinnedCommit") != "0964f29315820c91b171b585eb51e300164e9197":
        errors.append("A/B Street engine pin changed without updating the decision record")
    if engine_lock.get("decisionStatus") != "architecture_approved_spike_deferred":
        errors.append("A/B Street spike must remain deferred until an owner decision")
    assets = ROOT / "unity/TATSGame/Assets"
    for path in assets.rglob("*"):
        if path.name.endswith(".meta"):
            continue
        meta = path.with_name(f"{path.name}.meta")
        if not meta.exists():
            errors.append(f"Unity asset is missing .meta: {path.relative_to(ROOT)}")
    if errors:
        print("TATS structure verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("TATS structure verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

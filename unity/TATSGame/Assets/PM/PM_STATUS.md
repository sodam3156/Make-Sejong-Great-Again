# TATS PM Status

Generated: 2026-08-04 KST

## Current decision

The active repository is now TATS-only. RainFlow backend, contracts, frontend, release tooling, documentation, and Unity OnGUI code are quarantined under `archive/legacy-rainflow-v1/` and excluded from the active build path.

## Active source of truth

1. `docs/19_TATS_UI_UX_DIRECTION_V1.md`
2. `docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md`
3. approved Manyfast `V9 UX·Unity 구현본`
4. `contracts/game-v2/`

## Approved engine decision

- Architecture: A/B Street headless simulation behind a TATS game-v2 adapter, with Unity as the game client
- Fork: https://github.com/sodam3156/abstreet
- Pinned commit: `0964f29315820c91b171b585eb51e300164e9197`
- License: Apache-2.0
- Sejong technical spike: deferred pending a later owner decision

## P0 gates

1. Approve the target player, first-three-minute loop, and hard-safety versus soft-risk boundary.
2. Approve the Manyfast V9 core map, signal editor, and impact preview.
3. Decide whether to start the deferred Sejong A/B Street technical spike.
4. Freeze the seven game-v2 logical contracts as JSON Schema/OpenAPI.
5. Import `unity/TATSGame` with Unity 6000.3.20f1 and create the UI Toolkit shell.
6. Complete one real server-authoritative loop without runtime fixture continuation.

## Operating records

- Codex automation: `automation-3` (`TATS 2시간 PM 대리`)
- Notion board: https://app.notion.com/p/3b25d8c25aa4813ebb67c1f92c7828a1
- Discord state: `%LOCALAPPDATA%\MSGA\pm-automation\discord-state.json`

See `pm_backlog.json` for stable task IDs and acceptance criteria.

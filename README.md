# TATS — Totally Accurate Traffic Simulator

세종의 실제 도로 형상을 본뜬 지도에서 교차로 신호를 직접 설계하고, 진단 오버레이로 원인을 확인한 뒤 도시를 성장시키며 AI 기록과 겨루는 Unity 게임입니다.

## 지금의 정본

1. [`docs/19_TATS_UI_UX_DIRECTION_V1.md`](docs/19_TATS_UI_UX_DIRECTION_V1.md) — 제품·화면 방향
2. [`docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md`](docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md) — Manyfast·Unity 구현 인계
3. [`docs/00_TATS_SOURCE_OF_TRUTH.md`](docs/00_TATS_SOURCE_OF_TRUTH.md) — 저장소 경계와 개발 규칙
4. [`docs/01_ABSTREET_ENGINE_DECISION.md`](docs/01_ABSTREET_ENGINE_DECISION.md) — A/B Street 엔진 채택·fork·pin 결정
5. [`contracts/game-v2/README.md`](contracts/game-v2/README.md) — 서버 권위 게임 계약 작업 목록

과거 RainFlow 운영자 승인형 프로토타입은 [`archive/legacy-rainflow-v1`](archive/legacy-rainflow-v1)로 격리했습니다. 역사·알고리즘 참고용이며 현재 제품 코드나 빌드 입력으로 사용하지 않습니다.

## 첫 사용자 가치

`지도 관찰 → 진단 → 신호 한 단계 편집 → 영향 미리보기 → 안전 적용 → 결과 관찰 → 첫 도로 개방`

완료 기준은 3분 안에 위 흐름을 Unity에서 한 번 끝내고, UI가 결과·안전·포인트를 임의 계산하지 않는 것입니다.

## 현재 구조

| 경로 | 역할 |
|---|---|
| `unity/TATSGame` | Unity 6.3 LTS UI Toolkit 클라이언트 정본 |
| `contracts/game-v2` | SignalPlan·ImpactPreview·Overlay·성장·AI 비교 계약 |
| `backend` | A/B Street headless를 격리하는 game-v2 adapter 경계 |
| `third_party/abstreet.lock.json` | fork·기준 commit·라이선스 pin |
| `data/public` | 실제 도로 형상 참고용 공개자료 스냅샷 |
| `docs/19`, `docs/20` | 제품·UX 정본 |
| `archive/legacy-rainflow-v1` | 현재 빌드에서 제외한 과거 구현 |

## 협업 규칙

- `main`에 직접 push하지 않습니다.
- 최신 `main`에서 `feature/<담당자>-<작업명>` 브랜치를 만들고 작업별 PR 하나로 합칩니다.
- Unity 파일은 대응하는 `.meta`와 함께 올립니다.
- `archive/` 코드를 현재 경로로 복사하려면 새 계약과 수용 조건을 먼저 연결합니다.
- 서버가 계산해야 하는 교통량·포인트·안전·비용을 Unity에서 임의 구현하지 않습니다.

## 바로 다음 게이트

1. 대표가 타깃 플레이어·첫 3분·hard safety/soft risk 경계를 승인합니다.
2. Manyfast V9 핵심 화면을 승인합니다.
3. 보류한 세종 A/B Street 기술 스파이크의 착수 여부를 결정합니다.
4. 스파이크를 재개할 경우 결과를 반영해 `game-v2` adapter 계약을 고정합니다.
5. `unity/TATSGame`에서 UI Toolkit 셸과 첫 Play Mode 증거를 만듭니다.

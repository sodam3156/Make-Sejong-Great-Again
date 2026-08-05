# TATS game-v2 계약 작업공간

이 디렉터리는 최신 UX가 요구하는 **논리 계약의 정본 후보**다. 현재는 필드 의미를 동결하는 단계이며 endpoint·JSON 이름을 확정한 것으로 간주하지 않는다.

A/B Street headless 엔진 채택은 승인됐지만 Unity는 upstream API를 직접 호출하지 않는다. 모든 A/B Street 응답은 이 계약의 adapter를 통하며, 세종 기술 스파이크는 대표 결정 전까지 보류한다.

## 필수 모델

| 모델 | 책임 |
|---|---|
| `SignalPlan` | 교차로 단계 순서·시간·허용 이동·우선순위·적용 tick |
| `ImpactPreview` | 대기열·보행자·안전·감점·도로 차단 가능성 변화 |
| `OverlaySnapshot` | 하나의 master tick에 대응하는 진단 값·단위·심각도·관련 대상 |
| `BuildingInspector` | 개별 건물 생산량·레벨·비용·외형·비활성 사유 |
| `RoadUnlockInspector` | 연결 조건·비용·신규 건물과 예상 수요 |
| `AlgorithmSkill` | 선행 조건·해금·입력·기대 효과·trade-off·콘텐츠 버전 |
| `AiComparisonSnapshot` | 동일 조건의 플레이어·Luna·Terra·Sol 기록 비교 |

## 공통 필수값

- `schemaVersion`, `masterTick`, `mapVersion`, `gameRuleVersion`
- 값의 단위와 집계 구간
- `Loading`, `Ready`, `Empty`, `Error`, `Stale`를 구분할 수 있는 상태
- mutation 명령의 idempotency key와 stale tick 거부 정보
- 합성값·공개 도로 형상·게임 밸런스 값의 출처 구분

## 불변식

- UI는 결과를 계산하지 않는다.
- 직접 편집과 AI 초안은 같은 `SignalPlan` 스키마와 적용 절차를 사용한다.
- 위험 계획은 충돌 흐름과 결과를 먼저 보여주며 hard safety 위반은 차단한다.
- 연결 중단 시 mutation은 실패하고 runtime fixture로 성공처럼 진행하지 않는다.

세부 필드는 `docs/19_TATS_UI_UX_DIRECTION_V1.md` 11절과 `docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md` 9절을 따른다.

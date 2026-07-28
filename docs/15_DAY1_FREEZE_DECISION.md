# Day 1 동결 결정 기록

결정 시각: 2026-07-28 밤. 결정 권한: 준(PM). `docs/10_TEAM_PARALLEL_EXECUTION.md`의 계약 변경 원칙에 따라 이 시점 이후 기존 ID 변경은 준·최영 공동 승인이 필요하다.

## 1. 제출 변형안 확정

제출 변형안은 **RainFlow Sejong 단일**로 확정한다. `docs/12_TECH_STACK_AND_BACKEND_SCOPE.md`의 합성 5개 신호교차로 MVP는 참조 설계로만 유지하고 제출 범위에서 제외한다. 기술 스택(FastAPI, Pydantic v2, 결정론적 큐 시뮬레이터, PyInstaller)과 AI 역할 제한, 안전 원칙은 docs/12를 그대로 승계한다.

## 2. 시나리오 ID 동결

`dry_base`, `rain_spillback_a`, `rain_spillback_b` 3종으로 동결한다. `docs/07_BACKLOG.md`와 이슈 #3의 정상·혼잡·사고 명칭은 화면 표기 문구로만 사용하고 데이터 계약에는 쓰지 않는다.

## 3. 계약 파일 위치

| 파일 | 역할 |
|---|---|
| `contracts/rainflow.schema.json` | demo_run 결과 JSON 계약. ID·KPI 이름·단위 변경 금지 |
| `backend/fixtures/demo_run.json` | 7개 화면 상태를 전부 그릴 수 있는 완결 fixture. 수치는 전부 provisional |

프론트와 백엔드는 이 두 파일만을 진실원본으로 사용한다. 화면용 수치를 별도 계산하지 않는다.

## 4. 시뮬레이션 엔진 결정

Day 1~2는 `docs/10`의 폴백 규칙에 따라 **결정론적 큐 모델**을 정식 경로로 사용한다. SUMO·TraCI는 큐 모델이 3분 데모를 완주한 뒤의 선택적 업그레이드로 미룬다. 이슈 #9의 스파이크 통과 기준(재현성, spillback 재현, 가드, 정책 비교)은 큐 모델로 먼저 검증한다.

## 5. provisional 수치 원칙

fixture와 시뮬레이터의 모든 임계값·수요·용량 수치는 시우 검증 전까지 `provisional: true`로 표시한다. 합성 데이터이며 실제 세종시 실측 성과가 아니다. 목표 개선율을 코드에 하드코딩하지 않는다.

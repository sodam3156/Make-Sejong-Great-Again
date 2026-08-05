# TATS 저장소 정본과 경계

상태: 2026-08-04 저장소 리셋 기준

## 결론

현재 제품은 RainFlow 운영자 승인 대시보드가 아니라 **플레이어가 직접 신호를 설계하는 지도 중심 Unity 게임**이다. 충돌하는 과거 구현은 삭제하지 않고 `archive/legacy-rainflow-v1/`에 격리한다.

## 정본 우선순위

1. `docs/19_TATS_UI_UX_DIRECTION_V1.md`
2. `docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md`
3. 승인된 Manyfast `V9 UX·Unity 구현본`
4. `docs/01_ABSTREET_ENGINE_DECISION.md`
5. `contracts/game-v2/`
6. `ai-context/PROJECT_STACK.yaml`

`archive/` 안의 문서·계약·코드는 현재 결정을 덮어쓸 수 없다.

## 유지하는 사용자 가치

- 실제 도로를 본뜬 지도와 친근한 도시 표현
- 교차로별 단계 순서·지속시간·차량·보행자 우선순위 직접 편집
- 한 번에 하나인 7종 진단 오버레이
- 영향 미리보기와 안전 전환
- 도로 개방·개별 건물 Level 1~3 성장
- 선택한 알고리즘 그대로 생성하는 AI 초안과 Luna·Terra·Sol 기록 비교
- 결정론, 서버 권위, 합성값·현실값 구분, 로컬 저장

## 현재 제품에서 제외한 것

- `no_action`, `fixed_metering`, `corridor_gating` 정책 카드 선택
- 운영자 승인 대시보드와 정적 HTML 제품 경로
- 우천 회랑 복구를 제출 제품의 중심 서사로 사용하는 것
- runtime 연결 실패 뒤 fixture로 계속 플레이하는 것
- 로그인·회원가입·클라우드 계정
- 실제 세종 신호 제어 또는 실측 개선 효과 주장

## 구현 경계

| 계층 | 책임 | 금지 |
|---|---|---|
| Unity | 입력, 지도 표현, 상태 표시, 로컬 초안 | 점수·안전·비용·교통 결과 계산 |
| A/B Street fork | 지도·교통 simulation의 원시 상태와 headless 실행 | TATS 성장·안전·경제 규칙 결정 |
| Backend adapter | A/B Street 형식 격리, tick, 검증, 영향 예측, 적용, 성장, AI 기록 | Unity에 upstream API 직접 노출 |
| Contracts | 필드 의미·단위·버전·오류 상태 | 구현 편의를 위한 의미 변경 |
| Content | 알고리즘 설명, 건물·도로 비용과 외형 ID | 코드에 밸런스 값 산재 |

## 첫 3분 수용 조건

- Day 1 03:00 정지 상태에서 시작한다.
- 신호 현시를 읽고 교차로 한 단계의 시간 또는 우선순위를 바꾼다.
- 영향 미리보기에서 대기열·보행자·위험 변화를 확인한다.
- 서버 검증과 안전 전환 후 지도에서 결과를 관찰한다.
- 세 번째 도시 시간 정산에서 기본 포인트와 증가 근거를 읽는다.
- 첫 연결 도로를 구매한다.
- 연결이 끊기면 즉시 정지하고 마지막 tick을 표시하며 변경 명령을 막는다.

## 레거시 재사용 규칙

1. 필요한 아이디어나 알고리즘을 `archive/legacy-rainflow-v1/`에서 찾는다.
2. 새 TATS 수용 조건과 `game-v2` 계약에 대응시킨다.
3. RainFlow 이름·API·상태 머신 의존성을 제거한 작은 단위로 다시 구현한다.
4. 테스트와 소유자를 붙인 PR로 가져온다.

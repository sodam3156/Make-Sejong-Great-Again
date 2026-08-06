# TATSGame Unity project shell

최신 제품의 Unity 정본 경로다. Unity `6000.3.20f1`과 UI Toolkit을 사용한다.

현재는 레거시 코드를 제거한 뒤 Unity UI Toolkit으로 만든 **fixture 기반 통합 플레이 프로토타입**이다. `game-v2` 계약이 확정되기 전까지 교통·포인트·안전 결과를 계산하지 않고, 화면 상태와 서버 표시값만 mock ViewModel로 재현한다.

## 현재 통합 흐름

`시작 교차로·AI 선택 → 첫 3분 안내 → 지도 관찰 → 진단 → 신호 편집 → 영향 미리보기 → 안전 적용 → 건물 성장 → AI 기록 비교`

- 기준 해상도: `1920×1080`
- 픽셀 월드 작업 캔버스: `480×270`을 4배 확대하는 구성
- 시작 상태: `Day 1 03:00`, 정지, 신호 현시 오버레이 활성
- 캐릭터·오리 보행자·건물·차량: UXML의 `art-slot-*` 요소에 최종 스프라이트를 교체하는 구조
- 실행 씬: `Assets/Scenes/Main.unity`

## 구현 순서

1. `GameHud`, `MapInteractionLayer`, `ContextInspector`, `ToolDock` 셸 — 완료
2. 화면 상태와 mock ViewModel — 완료
3. 선택·단일 진단 오버레이·SignalPlan 로컬 초안 — 완료
4. ImpactPreview와 연결 중단 pause — 완료
5. 스킬북·건물·도로·AI 비교 — 완료
6. 제목/첫 3분/플레이 기능을 하나의 흐름으로 연결 — 완료
7. 최종 픽셀아트 스프라이트 교체와 UX 조정 — 대기
8. 실제 server adapter 연결과 Play Mode 검증 — 대기

## 금지

- `RainFlowGameController.OnGUI` 복원
- 정책 카드 3개를 핵심 조작으로 사용
- UI에서 교통 결과·포인트·안전·비용 계산
- backend 연결 실패 후 fixture로 runtime 진행

과거 Unity 구현은 `archive/legacy-rainflow-v1/unity/RainFlowGame/`에 있다.

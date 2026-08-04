# TATSGame Unity project shell

최신 제품의 Unity 정본 경로다. Unity `6000.3.20f1`과 UI Toolkit을 사용한다.

현재는 레거시 코드를 제거한 **깨끗한 프로젝트 셸**이다. Manyfast V9 핵심 화면 승인과 `game-v2` 계약 확정 전에는 최종 스타일이나 서버 연결을 대량 구현하지 않는다.

## 구현 순서

1. `GameHud`, `MapInteractionLayer`, `ContextInspector`, `ToolDock` 셸
2. 화면 상태와 mock ViewModel
3. 선택·단일 진단 오버레이·SignalPlan 로컬 초안
4. ImpactPreview와 연결 중단 pause
5. 스킬북·건물·도로·AI 비교
6. 실제 server adapter 연결과 Play Mode 검증

## 금지

- `RainFlowGameController.OnGUI` 복원
- 정책 카드 3개를 핵심 조작으로 사용
- UI에서 교통 결과·포인트·안전·비용 계산
- backend 연결 실패 후 fixture로 runtime 진행

과거 Unity 구현은 `archive/legacy-rainflow-v1/unity/RainFlowGame/`에 있다.

# RainFlow v1 레거시 격리본

이 디렉터리는 2026-08-04 TATS 저장소 리셋 때 루트에서 분리한 과거 프로토타입이다.

## 포함 범위

- FastAPI RainFlow backend와 동결 계약
- 정책 카드·운영자 승인형 정적 frontend
- RainFlow Unity 세로 조각과 OnGUI 화면
- Windows launcher·release·Docker·PyInstaller 경로
- `docs/00`~`docs/18`, 과거 evidence와 시각 자료
- 과거 CI와 계약/fixture 생성 스크립트

## 사용 규칙

- 현재 빌드·CI·자동화의 입력으로 사용하지 않는다.
- 이 안에서 직접 기능 개발하지 않는다.
- 재사용할 코드는 TATS 계약과 수용 조건을 연결해 현재 경로에 새로 구현한다.
- 원래 위치는 이 디렉터리 아래에 그대로 보존되어 있어 개별 복원이 가능하다.

격리 기준 커밋: `8831c2f` (`codex/ai-traffic-game-slice`)


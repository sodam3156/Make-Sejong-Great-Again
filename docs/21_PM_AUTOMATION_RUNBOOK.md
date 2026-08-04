# TATS 2시간 PM 운영 런북

기준 시각: 2026-08-04 21:15 KST

- Codex 자동화: `automation-3` (`TATS 2시간 PM 대리`, 2시간 주기, ACTIVE)
- Notion 운영 보드: https://app.notion.com/p/3b25d8c25aa4813ebb67c1f92c7828a1
- 로컬 프로젝트: `C:\Users\USER\Documents\세종AX해커톤_MSGA`

## 목적

2시간마다 제품·Unity·백엔드·GitHub·Notion의 실제 상태를 점검하고, 다음 사용자 가치에 직접 연결되는 작업만 갱신한다.

`관심 지역 선택 → 신호 설계 → 영향 미리보기 → 안전 적용 → 결과 관찰 → 첫 정산/도로 개방 → AI 기록 비교`

## 매 실행 순서

1. `docs/19_TATS_UI_UX_DIRECTION_V1.md`, `docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md`와 최신 Notion 제품 정본을 읽는다.
2. 제품/게임 디자인, Unity/QA, GitHub/CI 전문 에이전트를 최대 3개 병렬로 실행한다.
3. Git 상태·원격 SHA·PR/Issue/CI, Unity 프로젝트 구조·컴파일/테스트 증거, Notion 담당자 페이지 변경 시각을 확인한다.
4. `unity/TATSGame/Assets/PM/pm_backlog.json`과 `PM_STATUS.md`를 동일한 작업 ID로 갱신한다.
5. 기존 Notion `TATS 2시간 PM 운영 보드` 한 페이지만 갱신한다. 유사 페이지를 새로 만들지 않는다.
6. 팀원 행동이 필요한 항목은 `scripts/pm/Send-DiscordTaskAlert.ps1`로 알린다.
7. 변경·검증 증거와 실패 사유를 자동화 메모리에 남긴다.

## Discord 전송 규칙

- 비밀값은 사용자 환경 변수 `SEJONG_AX_DISCORD_WEBHOOK`에서만 읽는다.
- 메시지는 반드시 `[책임자]`로 시작한다.
- `task_key`가 처음 발견되거나 `ChangeToken`이 바뀌면 한 번 전송한다.
- 같은 `task_key`와 `ChangeToken`은 중복 전송하지 않는다.
- 마지막 전송 뒤 4시간 동안 변경이 없으면 한 번 재알림한다. 이후에도 4시간 간격을 지킨다.
- 해결된 작업은 `-Resolve`로 상태를 닫는다.
- 상태와 감사 로그는 `%LOCALAPPDATA%\MSGA\pm-automation`에 저장하며 webhook 값은 기록하지 않는다.

## 현재 P0 게이트

1. **준:** 이미 정리된 타깃 플레이어·첫 3분 MVP를 기준으로 hard safety 차단/soft risk 동의 경계를 승인한다.
2. **준:** 보류한 세종 A/B Street 기술 스파이크의 착수 여부를 추후 결정한다.
3. **준·최영:** 승인된 A/B Street headless 경계를 반영해 `game-v2` 계약과 OpenAPI를 동결한다.
4. **김경은·여하윤:** Unity 6000.3.20f1에서 UI Toolkit 셸과 Play Mode 증거를 남긴다.
5. **준:** 저장소 리셋 변경의 단일 PR·CI 진행 여부를 결정한다.

## 비용·시간·재시도 상한

- 전문 에이전트: 실행당 최대 3개
- 전체 실행 시간: 최대 40분
- 외부 소스 재시도: 소스당 최대 1회
- Discord 전송: 최대 2회, 요청당 15초 제한
- 빌드/테스트가 20분을 넘으면 중단하고 마지막 로그와 재현 명령만 기록한다.

## 중단 조건

- Notion 권한 오류가 나면 Notion 쓰기만 중단하고 로컬·GitHub·Unity 점검은 계속한다.
- Unity 버전 불일치나 컴파일 실패는 성공으로 간주하지 않는다.
- 비밀 환경 변수가 없으면 Discord 전송을 중단하고 감사 로그에 원인만 남긴다.
- 사용자 변경이 있는 파일은 덮어쓰지 않고 새 PM 산출물만 갱신한다.

## 롤백

1. Codex 자동화 `TATS 2시간 PM 대리` (`automation-3`)를 일시 중지한다.
2. `%LOCALAPPDATA%\MSGA\pm-automation\discord-state.json`을 별도 보관한 뒤 제거하면 알림 상태만 초기화된다.
3. Unity PM 산출물은 `unity/TATSGame/Assets/PM/`만 제거하면 게임 코드에 영향 없이 되돌릴 수 있다.
4. Notion 운영 보드는 삭제하지 않고 제목에 `[중단]`을 붙여 감사 이력을 보존한다.

## 검증 명령

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/pm/Send-DiscordTaskAlert.ps1 `
  -TaskKey 'test|pm|dedupe' -Owner '담당 미정' -Summary '중복 억제 시험' `
  -Action '아무 작업도 하지 않음' -Evidence 'dry-run' -DryRun
```

## 근거

- `docs/00_TATS_SOURCE_OF_TRUTH.md`
- `docs/01_ABSTREET_ENGINE_DECISION.md`
- `docs/19_TATS_UI_UX_DIRECTION_V1.md`
- `docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md`
- `contracts/game-v2/`
- `third_party/abstreet.lock.json`
- `ai-context/PROJECT_STACK.yaml`

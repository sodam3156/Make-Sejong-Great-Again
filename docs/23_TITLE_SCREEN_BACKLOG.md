# TATS 시작 화면 구현 원장

> 상태: 2026-08-05 개설 · 실행 주체: 클라우드 자동화 `TATS 시작 화면 구현 (2시간)`
>
> 이 파일이 자동화의 유일한 작업 지시서다. 사람이 순서를 바꾸거나 항목을 지워도 된다.

## 자동화가 매 실행마다 지켜야 할 것

자동화는 2시간마다 **기억이 전혀 없는 새 세션**으로 깨어난다. 아래를 그대로 따른다.

### 1. 브랜치 — 팀 공용 브랜치에 직접 커밋하지 않는다

팀원 4명이 `codex/ai-traffic-game-slice`에서 동시에 작업 중이다.

```bash
git fetch origin
git checkout -B automation/title-screen origin/automation/title-screen \
  || git checkout -B automation/title-screen origin/codex/ai-traffic-game-slice
git merge --no-edit origin/codex/ai-traffic-game-slice
```

병합 충돌이 나면 **해결하지 말고 즉시 중단**한다. 충돌 파일 목록만 보고하고 끝낸다.
사람이 푼다.

### 2. 맥락 파악 — 이 순서로 읽는다

정본에 없는 게임 규칙을 임의로 지어내지 않는다. 필요한데 정의가 없으면 구현하지 말고
"계약 미정"으로 보고한다.

1. [`00_TATS_SOURCE_OF_TRUTH.md`](00_TATS_SOURCE_OF_TRUTH.md) — 정본 경계와 금지 사항
2. [`20_TATS_UX_FRONTEND_HANDOFF_V1.md`](20_TATS_UX_FRONTEND_HANDOFF_V1.md) — 8.3절 화면 상태, 9절 데이터 계약
3. [`22_TATS_BACKEND_DESIGN_V1.md`](22_TATS_BACKEND_DESIGN_V1.md) — API·계약·시간 모델
4. [`../unity/TATSGame/README.md`](../unity/TATSGame/README.md) — Unity 셸 규칙과 금지 사항

### 3. 범위 — 한 실행에 체크 안 된 첫 항목 **하나만**

두 개 이상 손대지 않는다. 전부 체크돼 있으면 아무것도 만들지 말고 "완료됨"만 보고하고 끝낸다.

### 4. 검증 — 못 한 검증을 했다고 하지 않는다

```bash
python -m pytest backend/tests -q
python scripts/verify_tats_structure.py
```

둘 다 통과해야 커밋한다. **클라우드에는 Unity Editor가 없어 C#은 컴파일 검증이 불가능하다.**
Unity 코드를 쓸 때는 아래를 지킨다.

- EditMode 테스트를 함께 쓴다 (사람이 로컬에서 돌린다)
- 검증하지 못했다는 사실을 커밋 메시지와 이 파일의 진행 기록에 남긴다
- "동작 확인함" 같은 표현을 쓰지 않는다

### 5. 마무리

1. 구현한 항목을 `- [x]`로 바꾸고 아래 진행 기록에 한 줄 추가한다
2. 커밋하고 `automation/title-screen`에 푸시한다
3. 무엇을 만들었고 무엇을 **검증하지 못했는지** 보고한다

---

## 백로그

- [x] **T1 TitleScreen 셸** — UXML/USS/presenter, 메뉴 5개(새로 시작·이어하기·환경설정·도움말·기여자),
      키보드 상하/Enter/Esc 이동, 포커스 표시, 1440×900과 1280×720. 서버 연결 없이 뜬다.
- [ ] **T2 새로 시작** — 시작 교차로 3곳과 상대 AI(Luna·Terra·Sol) 선택 화면.
      백엔드 `POST /api/game-sessions`와 `GameSessionSnapshot` 계약.
      교차로 목록은 `backend/content/map_eojin_playable.json`의 `startIntersectionIds`에서 읽는다.
- [ ] **T3 이어하기** — 로컬 GameSave 슬롯 목록, 버전·마지막 tick·도시 시각 표시.
      백엔드 `POST /api/game-sessions/{id}/resume`의 검증 성공·실패 두 상태.
      검증 실패 시 임의 병합 없이 이유와 재시도·종료만 제공한다 (M16).
- [ ] **T4 환경설정** — 해상도, 기본 배속, 마스터·효과음 볼륨, 언어.
      로컬 파일에 원자적 저장(임시 파일 → rename)하고 이전 정상본 1개를 남긴다.
      게임 규칙에 영향을 주는 값은 넣지 않는다.
- [ ] **T5 도움말** — 첫 3분 안내, 조작법, 용어(대기행렬·spillback·상충·포화도).
      본문은 코드가 아니라 `backend/content/help.json`에 두고 `GET /api/content/help`로 제공한다.
- [ ] **T6 기여자** — 팀 MSGA 명단, 공개 데이터 출처, 오픈소스 고지.
      `THIRD_PARTY_NOTICES.md`와 `third_party/abstreet.lock.json`을 실제로 읽어 구성한다.
      손으로 복사한 사본을 만들지 않는다.
- [ ] **T7 연결 상태와 종료** — 시작 화면의 서버 연결 표시(연결됨·재시도·끊김),
      끊긴 상태에서 `새로 시작`·`이어하기` 비활성화와 사유 표시, 종료 확인.
      연결이 없으면 fixture로 진행하지 않는다.
- [ ] **T8 접근성 마무리** — 키보드 포커스 순서가 읽기 순서와 일치, 클릭 영역 44×44px 이상,
      본문 대비 4.5:1 이상, 모든 기능에 아이콘·이름·한 줄 설명.

## 범위 밖

- 지도·신호 편집·오버레이 등 인게임 화면 (별도 담당자 작업이다)
- 로그인·회원가입·클라우드 프로필 — 만들지 않는다
- 결제·상점 — 제출 빌드에 넣지 않는다
- 최종 아트와 스타일 — Manyfast V9 승인 전에는 회색 박스로 둔다

## 진행 기록

| 날짜 | 항목 | 결과 | 검증하지 못한 것 |
|---|---|---|---|
| 2026-08-05 | — | 원장 개설 | — |
| 2026-08-05 | T1 | `Assets/UI/TitleScreen/TitleScreen.{uxml,uss}`, `Assets/Scripts/UI/TitleScreen/{TitleScreenMenuItem,TitleScreenPresenter,TitleScreenView}.cs`, EditMode 테스트 `TitleScreenPresenterTests.cs` 추가. 메뉴 5개는 순서대로 새로 시작·이어하기·환경설정·도움말·기여자. 상하 화살표로 포커스 이동(마지막에서 순환), Enter로 활성화 이벤트 발행, Esc는 §12.1 계약에 따라 닫을 오버레이가 없어 입력만 흡수. 1440×900/1280×720 대응은 % 기반 flex 레이아웃으로 구현. 씬에 `TitleScreenView`를 붙이는 작업(UIDocument/PanelSettings 연결)은 Unity Editor가 필요해 사람 몫으로 남김. | C# 컴파일 자체를 확인 못함(클라우드에 Unity Editor 없음). EditMode 테스트 작성만 하고 Test Runner로 실행 못함 — asmdef의 `optionalUnityReferences: TestAssemblies` 참조와 `EditorWindow` 기반 이벤트 디스패치가 실제로 동작하는지 미검증. `TitleScreen.uxml.meta`/`TitleScreen.uss.meta`의 `ScriptedImporter.script` GUID(`76c8bcbf6cd1f4880a6f6a5686000eb2`, fileID 13804/13805)는 기억에 의존한 값이라 Unity가 실제로 인식하는지 미검증 — 처음 프로젝트를 열 때 콘솔 경고가 뜨는지 확인 필요. 1440×900/1280×720에서 실제로 잘리지 않는지 화면으로 확인 못함.

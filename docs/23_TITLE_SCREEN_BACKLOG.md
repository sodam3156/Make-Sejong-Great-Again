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
- [x] **T2 새로 시작** — 시작 교차로 3곳과 상대 AI(Luna·Terra·Sol) 선택 화면.
      백엔드 `POST /api/game-sessions`와 `GameSessionSnapshot` 계약.
      교차로 목록은 `backend/content/map_eojin_playable.json`의 `startIntersectionIds`에서 읽는다.
- [x] **T3 이어하기** — 로컬 GameSave 슬롯 목록, 버전·마지막 tick·도시 시각 표시.
      백엔드 `POST /api/game-sessions/{id}/resume`의 검증 성공·실패 두 상태.
      검증 실패 시 임의 병합 없이 이유와 재시도·종료만 제공한다 (M16).
- [x] **T4 환경설정** — 해상도, 기본 배속, 마스터·효과음 볼륨, 언어.
      로컬 파일에 원자적 저장(임시 파일 → rename)하고 이전 정상본 1개를 남긴다.
      게임 규칙에 영향을 주는 값은 넣지 않는다.
- [x] **T5 도움말** — 첫 3분 안내, 조작법, 용어(대기행렬·spillback·상충·포화도).
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
| 2026-08-05 | T1 | `Assets/UI/TitleScreen/TitleScreen.{uxml,uss}`, `Assets/Scripts/UI/TitleScreen/{TitleScreenMenuItem,TitleScreenPresenter,TitleScreenView}.cs`, EditMode 테스트 `TitleScreenPresenterTests.cs` 추가. 메뉴 5개는 순서대로 새로 시작·이어하기·환경설정·도움말·기여자. 상하 화살표로 포커스 이동(마지막에서 순환), Enter로 활성화 이벤트 발행, Esc는 §12.1 계약에 따라 닫을 오버레이가 없어 입력만 흡수. 1440×900/1280×720 대응은 % 기반 flex 레이아웃으로 구현. 씬에 `TitleScreenView`를 붙이는 작업(UIDocument/PanelSettings 연결)은 Unity Editor가 필요해 사람 몫으로 남김. | C# 컴파일 자체를 확인 못함(클라우드에 Unity Editor 없음). EditMode 테스트 작성만 하고 Test Runner로 실행 못함 — asmdef의 `optionalUnityReferences: TestAssemblies` 참조와 `EditorWindow` 기반 이벤트 디스패치가 실제로 동작하는지 미검증. `TitleScreen.uxml.meta`/`TitleScreen.uss.meta`의 `ScriptedImporter.script` GUID(`76c8bcbf6cd1f4880a6f6a5686000eb2`, fileID 13804/13805)는 기억에 의존한 값이라 Unity가 실제로 인식하는지 미검증 — 처음 프로젝트를 열 때 콘솔 경고가 뜨는지 확인 필요. 1440×900/1280×720에서 실제로 잘리지 않는지 화면으로 확인 못함. |
| 2026-08-05 | T2 | `Assets/UI/NewGame/NewGameScreen.{uxml,uss}`, `Assets/Scripts/UI/NewGame/{NewGameOpponent,NewGameStartOption,NewGameSelection,NewGameContent,NewGamePresenter,NewGameView}.cs`, EditMode 테스트 `NewGamePresenterTests.cs` 추가. 시작 교차로 3곳(ix_04 성금교차로·ix_09 청사교차로·ix_07 어진교차로, `backend/content/map_eojin_playable.json`의 `startIntersectionIds` 순서 그대로)과 상대 AI(Luna·Terra·Sol) 중 하나씩 라디오 방식으로 고르고 `시작` 버튼으로 확정한다. 상하 화살표로 8개 항목(교차로 3·상대 3·뒤로·시작)을 순환 이동, Enter로 선택/확정, Esc는 §12.1에 따라 `Back` 이벤트만 발행. `시작` 버튼은 둘 다 고르기 전엔 `SetEnabled(false)`. **범위를 의도적으로 좁힘**: `POST /api/game-sessions` 호출과 `GameSessionSnapshot` 처리는 만들지 않았다 — 저장소에 세션 API 백엔드 구현 자체가 없고(`backend/`엔 `content/map_eojin_playable.json`과 테스트뿐), `GameSessionSnapshot`은 `contracts/game-v2/contract-status.json`이 나열하는 7개 필수 모델에도 없어 필드 계약이 정의돼 있지 않다 → **계약 미정으로 보고**. presenter는 확정된 `(startNodeId, opponentModel)`만 `Confirmed` 이벤트로 넘기고, 실제 세션 생성 연결은 계약이 정해진 뒤 후속 작업으로 남긴다. 교차로 목록도 지금은 커밋 시점 JSON 값을 Unity 코드에 그대로 옮긴 mock이다 — Unity가 `backend/content/map_eojin_playable.json`을 런타임에 읽는 경로 자체가 아직 없다(`unity/TATSGame/README.md` 구현 순서상 실제 server adapter 연결은 마지막 단계). 씬에 `NewGameView`를 붙이고 시작 화면과 전환을 연결하는 작업은 Unity Editor가 필요해 사람 몫으로 남김. | C# 컴파일 자체를 확인 못함(클라우드에 Unity Editor 없음). EditMode 테스트 작성만 하고 Test Runner로 실행 못함 — T1과 같은 이유. `NewGameScreen.uxml.meta`/`.uss.meta`의 `ScriptedImporter.script` GUID는 T1이 쓴 값을 그대로 재사용했고 그 값 자체가 T1에서도 미검증 상태다. 새로 만든 폴더·스크립트 meta의 GUID는 무작위 생성값이라 다른 파일과 안 겹치는지만 텍스트로 확인했고(중복 없음) Unity가 열었을 때 정상 인식하는지는 못 봤다. `SetEnabled(false)`인 `시작` 버튼이 키보드 포커스 순환에 그대로 남아 있는 것이 UI Toolkit에서 실제로 어떻게 보이는지(포커스 링 표시, 클릭 차단) 미검증. 1440×900/1280×720에서 잘리지 않는지 화면으로 확인 못함. |
| 2026-08-05 | T3 | `Assets/UI/Continue/ContinueScreen.{uxml,uss}`, `Assets/Scripts/UI/Continue/{GameSaveDto,GameSaveSlot,GameSaveSlotListResult,GameSaveSlotStore,ContinuePresenter,ContinueView}.cs`, EditMode 테스트 `ContinuePresenterTests.cs`·`GameSaveSlotStoreTests.cs` 추가. `GameSaveSlotStore`가 로컬 디렉터리(`Application.persistentDataPath/saves`, Unity 쪽 구현 결정 — 문서에 경로 규정 없음)의 `*.json` 파일을 `docs/22_TATS_BACKEND_DESIGN_V1.md` 10절 GameSave 계약(`schemaVersion, startNodeId, opponentModel, resumeToken{tick,...}, commandLog[], lastConfirmedTick`)대로 파싱해 슬롯 목록을 만든다. 슬롯 버튼에 버전·마지막 tick·도시 시각(`Day {tick // 86400} · {(tick % 86400)을 HH:MM으로}`, 22절 2행 공식 그대로, 19절 64행 "Day N · HH:MM" 문구 고정 규칙 그대로)을 표시한다. 상하 화살표로 슬롯·뒤로·이어하기 순환 이동, Enter로 슬롯 선택 후 `이어하기`로 확정하면 `ResumeRequested` 이벤트 발행. **범위를 의도적으로 좁힘**: 실제 `POST /api/game-sessions/{id}/resume` 호출은 만들지 않았다 — 저장소에 세션·resume API 백엔드 구현이 없다(T2와 같은 근거, `backend/README.md`). 대신 검증 성공·실패 두 상태(M15 재개 준비·M16 재개 실패)는 `ContinuePresenter.ReportResumeSucceeded()`/`ReportResumeFailed(reason)`을 밖에서 불러줘야 반영되는 형태로 만들어 뒀다 — 아직 그걸 호출하는 코드는 없다. M16대로 재개 실패 화면은 재시도·종료만 제공하고 Esc는 흡수해 실수로 종료되지 않게 했다. 슬롯 파일이 하나도 없을 때(빈 상태)와 전부 손상됐을 때(오류 상태)를 구분해 안내 문구를 다르게 보여준다. 씬 연결은 Unity Editor가 필요해 사람 몫으로 남김 — T1·T2와 같은 이유. | C# 컴파일 자체를 확인 못함(클라우드에 Unity Editor 없음). `Tats.Game.asmdef`에 `Unity.Newtonsoft.Json` 참조를 새로 추가했는데(레거시 `archive/legacy-rainflow-v1/unity/RainFlowGame/Assets/Scripts/RainFlow.Game.asmdef`에서 쓰던 이름을 그대로 가져옴) 현재 Unity 프로젝트에서 실제로 이 이름이 풀리는지 못 봤다 — 패키지는 `manifest.json`에 있지만(`com.unity.nuget.newtonsoft-json`) asmdef 참조 이름이 버전마다 다를 수 있다. `GameSaveSlotStoreTests.cs`는 UnityEngine·UIElements 없이 순수 System.IO만 쓰지만 여전히 Editor Test Runner로 실행 못함. `ContinuePresenterTests.cs`는 T1·T2와 같은 EditorWindow 방식이라 같은 미검증 사유가 적용된다(asmdef `TestAssemblies` 참조, 실제 panel 이벤트 전달). `ContinueScreen.uxml.meta`/`.uss.meta`의 `ScriptedImporter.script` GUID는 T1·T2가 쓴 값을 재사용했고 그 값 자체가 아직 미검증이다. 새 폴더·스크립트 meta의 GUID는 무작위 생성값이라 저장소 안에서 중복이 없는지만 텍스트로 확인했다(`grep`으로 전수 검사, 중복 없음). 저장 디렉터리 경로(`Application.persistentDataPath/saves`)와 "슬롯 하나 = 파일 하나" 구성은 문서 어디에도 없는 구현 결정이라, 다른 팀원이 GameSave를 실제로 쓰기 시작하면 경로 충돌 여부를 다시 확인해야 한다. `Directory.GetFiles`/`File.ReadAllText` 예외 처리 경로(파일 잠금·권한 오류 등)도 실기기에서 확인 못함. 1440×900/1280×720에서 슬롯이 여러 개일 때 목록이 잘리지 않는지 화면으로 확인 못함. |
| 2026-08-05 | T4 | `Assets/UI/Settings/SettingsScreen.{uxml,uss}`, `Assets/Scripts/UI/Settings/{GameSettings,GameSettingsLoadResult,GameSettingsStore,SettingsPresenter,SettingsView}.cs`, EditMode 테스트 `SettingsPresenterTests.cs`·`GameSettingsStoreTests.cs` 추가. 값 4종은 해상도(`docs/20` 111행이 정의하는 1440×900/1280×720 두 값만), 기본 배속(`docs/20` 8.3절 `SimulationSpeed` 중 Paused를 뺀 X1/X3/X5, 146행 "기본값은 1배속"과 일치), 마스터·효과음 볼륨(0~100%, 10% 단위), 언어. **언어는 계약 미정으로 좁혀 구현**: 저장소 어디에도 지원 언어 목록이 없어(전 문서·콘텐츠가 한국어뿐) "한국어" 한 값만 두었고, 추가 언어 선택지는 만들지 않았다. `GameSettingsStore.Save()`는 임시 파일(`settings.json.tmp`)에 쓴 뒤 기존 파일이 있으면 `File.Replace`로 원자적으로 교체하면서 이전 내용을 `settings.json.bak`으로 옮긴다(백업은 항상 최근 1개). `Load()`는 원본 → 백업 → 기본값 순으로 폴백하고, 스키마 검증 실패(범위 밖 볼륨, 정의되지 않은 enum 값)도 손상으로 취급한다. 상하 화살표로 7개 항목(해상도·배속·마스터볼륨·효과음볼륨·언어·뒤로·저장) 순환 이동, 좌우 화살표(또는 값 버튼 클릭·Enter)로 값 변경, Enter는 `뒤로`/`저장`에 포커스가 있을 때만 그 동작을 실행한다. Esc는 T3의 슬롯 목록 화면과 같은 방식으로 저장하지 않은 값을 폐기하고 `Back` 이벤트를 발행한다 — `저장`을 눌러야만 파일에 쓴다. 저장 파일 위치는 `Application.persistentDataPath/settings.json`으로 고정했다 — T3와 같은 이유로 문서에 경로 규정이 없는 Unity 쪽 구현 결정이다. 씬 연결은 Unity Editor가 필요해 사람 몫으로 남김 — T1~T3와 같은 이유. | C# 컴파일 자체를 확인 못함(클라우드에 Unity Editor 없음). `CycleEnum<T>() where T : struct, Enum`의 제네릭 Enum 제약(C# 7.3+)이 현재 프로젝트의 언어 버전에서 실제로 컴파일되는지 못 봤다. `File.Replace(string,string,string)`가 이 Unity 런타임(Mono/IL2CPP)에서 실제로 원자적 교체+백업을 수행하는지, 특히 백업 대상 파일이 없는 최초 저장(이 경우 `File.Move`로 분기)과의 두 경로 전환이 실제로 맞물리는지 실행해서 확인 못함. `GameSettingsStoreTests.cs`는 순수 System.IO만 쓰지만 T3와 같은 이유로 Editor Test Runner로 실행 못함 — 특히 `Save_Twice_KeepsExactlyOneBackupOfPreviousVersion` 테스트가 기대하는 `File.Replace`의 백업 동작이 실제로 그 문자열 그대로 맞는지 검증 못함. `SettingsPresenterTests.cs`는 T1~T3와 같은 EditorWindow 방식이라 같은 미검증 사유가 적용된다. `SettingsScreen.uxml.meta`/`.uss.meta`의 `ScriptedImporter.script` GUID는 T1~T3가 쓴 값을 재사용했고 그 값 자체가 아직 미검증이다. 새 폴더·스크립트·테스트 meta의 GUID는 무작위 생성값이라 저장소 안에서 중복이 없는지만 텍스트로 확인했다(`grep`으로 전수 검사, 중복 없음). 좌우 화살표를 값 변경에 쓰는 키보드 배정은 문서 어디에도 없는 이번 구현의 결정이라, 다른 화면과 일관되는지(특히 T8 접근성 마무리에서) 사람이 다시 검토해야 한다. 저장 파일 경로(`Application.persistentDataPath/settings.json`)가 T3의 `saves/` 서브디렉터리와 충돌하지 않는지는 이름만 보고 판단했고 실기기에서 확인 못함. 1440×900/1280×720에서 화면이 잘리지 않는지 화면으로 확인 못함. |
| 2026-08-05 | T5 | `backend/content/help.json`(정본 콘텐츠, `python -m pytest backend/tests -q`에 새 파일 `backend/tests/test_help_content.py` 5개 포함해 통과) 추가. 세 절: 첫 3분 안내(`docs/20` 6.1절 7단계를 순서·문구 그대로 옮김), 조작법(T1~T4가 이미 구현한 상하/좌우 화살표·Enter·Esc 배정을 문서화 — 새 규칙을 만들지 않음), 용어 4개(대기행렬·spillback·상충·포화도 — 각 정의는 `docs/22_TATS_BACKEND_DESIGN_V1.md` 3.1·3.2·4.2·6절의 실제 규칙 문장을 풀어쓴 것이고 각 항목에 `source` 필드로 근거 절을 남겼다, 새 게임 규칙을 지어내지 않았다). `GET /api/content/help`는 **범위를 의도적으로 좁혀** 만들지 않았다 — T2·T3·T4와 같은 근거로 `backend/README.md`에 세션·콘텐츠 API 서버 구현 자체가 없고, `docs/22` 9절 API 표에는 `GET /api/content/algorithms`만 있어 `help` 엔드포인트는 정본에 없다. 대신 Unity 쪽은 `Assets/UI/Help/HelpScreen.{uxml,uss}`, `Assets/Scripts/UI/Help/{HelpContentDto,HelpContentLoadResult,HelpContentStore,HelpSection,HelpPresenter,HelpView}.cs`, EditMode 테스트 `HelpContentStoreTests.cs`·`HelpPresenterTests.cs`를 추가해 `Assets/StreamingAssets/content/help.json`(backend 원본과 바이트까지 동일한 사본)을 `Application.streamingAssetsPath`에서 읽는다 — `unity/TATSGame/README.md`가 말하는 `backend/content/map_eojin_playable.json`(시뮬레이션 원본)과 `StreamingAssets/map/eojin_map.json`(표시용 사본)의 관계를 그대로 빌려온 것이고, 이 사본 방식 자체는 문서에 없는 이번 구현의 결정이다. 화면은 탭 3개(첫 3분 안내·조작법·용어) + 뒤로 버튼으로 상하 화살표 순환, Enter로 탭 전환/뒤로 활성화, Esc는 T1~T4와 같은 방식으로 뒤로. 탭 전환에 Enter를 재사용하는 것은 이 화면이 읽기 전용이라 T4의 좌우-값변경 규칙을 그대로 가져오지 않은 이번 구현의 결정이다. help.json을 못 읽으면(파일 없음·파싱 실패·필수 섹션 누락) 본문 대신 오류 문구를 보여준다. 씬 연결은 Unity Editor가 필요해 사람 몫으로 남김 — T1~T4와 같은 이유. **브랜치 메모**: 지시서의 `origin/codex/ai-traffic-game-slice`는 더 이상 존재하지 않는다(PR #50로 `main`에 병합된 뒤 삭제됨) — 대신 `origin/main`을 병합했고 충돌 없이 fast하게 합쳐졌다(자동 병합, `automation/title-screen`의 T1~T4 커밋만 새로 남고 `main` 쪽에 추가 변경 없음). | C# 컴파일 자체를 확인 못함(클라우드에 Unity Editor 없음). `HelpContentStoreTests.cs`는 순수 System.IO·Newtonsoft만 쓰지만 T3·T4와 같은 이유로 Editor Test Runner로 실행 못함. `HelpPresenterTests.cs`는 T1~T4와 같은 EditorWindow 방식이라 같은 미검증 사유가 적용되고, 특히 `errorLabel.style.display.value`로 인라인 스타일을 읽는 방식이 실제 UI Toolkit 런타임에서 `resolvedStyle`과 같은 값을 주는지 확인 못했다. `HelpScreen.uxml.meta`/`.uss.meta`의 `ScriptedImporter.script` GUID는 T1~T4가 쓴 값을 재사용했고 그 값 자체가 아직 미검증이다. 새 폴더·스크립트·테스트·`StreamingAssets/content` meta의 GUID는 무작위 생성값이라 저장소 안에서 중복이 없는지만 텍스트로 확인했다(전수 검사, 최상위 `guid:` 74개 전부 고유— 중복 없음). `Application.streamingAssetsPath`에서 JSON을 동기 `File.ReadAllText`로 읽는 방식이 이 프로젝트의 실제 빌드 타깃(특히 Android처럼 StreamingAssets가 압축 APK 안에 있어 `File.*` API로 직접 못 여는 플랫폼)에서 동작하는지 확인 못했다 — README·매니페스트 어디에도 빌드 타깃이 정해져 있지 않다. `backend/content/help.json`과 `Assets/StreamingAssets/content/help.json`을 앞으로 계속 손으로 동기화해야 하는데 이를 강제하는 스크립트나 테스트가 없다(빌드 시 자동 복사 파이프라인 없음) — 다른 사람이 backend 쪽만 고치면 Unity 사본이 조용히 낡는다. 1440×900/1280×720에서 용어 4개가 모두 들어간 긴 목록이 스크롤 없이/있이 잘리지 않는지 화면으로 확인 못함. |

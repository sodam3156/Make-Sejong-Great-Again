# 18. AI 교통복구 게임 세로 조각 실행 계획 (2026-08-04)

이 문서는 `docs/17_GAME_DESIGN_V1.md`의 기획을 8월 5일부터 9일까지의 구현 작업으로
구체화한다. 기획 결정권은 손시우, 방향 결정권은 준에게 있다는 전제는 그대로다.

작성 근거는 2026-08-04 시점의 저장소 실측이다. 추정치가 아니라 실행한 결과다.

## 1. 착수 시점의 실제 상태

### 1.1 체크아웃 분기

같은 저장소가 세 곳에 있고 내용이 서로 다르다.

| 경로 | 브랜치 | 테스트 | 게임 코드 |
|---|---|---|---|
| `Documents/Make-Sejong-Great-Again` | `docs/a-plan-canon-alignment` | 77개 중 1개 실패 | 없음 |
| `Documents/모두의 창업 사업계획서 작성` 워크트리 | `claude/traffic-recovery-game-planning-*` | 74개 통과 | 없음 |
| `Documents/세종AX해커톤_MSGA/Make-Sejong-Great-Again` | `codex/ai-traffic-game-slice` | 89개 통과 | 전체 있음, 미커밋 |

8월 5일 작업은 **세 번째 체크아웃만** 정본으로 삼는다. 최영·김경은·여하윤이
각자 다른 사본에서 시작하면 병합 불가능한 상태가 된다.

### 1.2 미커밋 자산

추적되지 않는 파일 26개에 세로 조각 전체가 들어 있다.

```
backend/app/game.py                     632줄
backend/tests/test_game_mode.py         226줄
backend/fixtures/game_missions.json    1981줄
contracts/mission.schema.json            99줄
contracts/policy_design.schema.json
scripts/build_game_map.py
scripts/generate_game_fixture.py
docs/17_GAME_DESIGN_V1.md
unity/RainFlowGame/**                  2077줄 (C# 10개 파일)
```

`git clean -fd` 한 번이면 전부 사라진다. 다른 모든 작업보다 먼저 커밋한다.

### 1.3 동결 계약 상태 — 회귀 없음

`policies.py`는 손대지 않았고 `simulation.py`에 선택 인자를 추가하는 방식으로
게임 제어법칙을 넣었다. 기본값이 legacy 경로를 그대로 타므로 동결 결과가 보존된다.

검증 결과.

```
result_checksum   c9088907640696c315685619ce18ae1529ceb8bc1e993bb36c0f080b7ce4ed89
                  → 동결본과 현재가 완전히 동일

변경된 필드        source_tree_checksum  65d5d7c1... → b7b538c9...
                  source_live_run_id    ...3e5be2d480 → ...d8151109a7
```

`result_checksum`은 `source_tree_checksum`을 포함하지 않으므로, 이 값이 유지된다는
것은 timeline·KPI·정책·가드·decision이 한 글자도 안 바뀌었다는 기계적 증거다.
docs/15 동결 결정이 요구하는 준·최영 공동 승인은 이 증거를 근거로 진행한다.

앞으로도 `simulation.py`, `policies.py`, `main.py`, `domain.py`, `decision.py`,
`frontend/index.html`을 수정할 때마다 이 검사를 반복한다.

```bash
python scripts/generate_contract_artifacts.py && python -m pytest backend/tests -q
```

`result_checksum`이 `c9088907...`에서 벗어나면 리팩터링이 아니라 동작 변경이다.
즉시 멈추고 원인을 찾는다.

## 2. 최우선 결함 — 성공한 플레이어가 잠긴다

### 2.1 측정 결과

각 상태에서 가능한 정책을 전수 평가해 성공 가능 정책 수를 셌다.

| 미션 / 적응형 / 건물 / 장비 | 후보 풀 | 성공 가능 | 최고 margin |
|---|---:|---:|---:|
| Luna / 표준 / lv1 / 없음 | 231 | 49 | +3.286 |
| Terra / 표준 / lv2 / 없음 | 231 | 1 | +0.120 |
| Sol / 표준 / lv1 / 없음 | 231 | 3 | +0.330 |
| Sol / 표준 / lv3 / 없음 | 231 | **0** | +0.042 |
| Sol / 도전 / lv1 / 없음 | 231 | **0** | +0.000 |
| Sol / 도전 / lv3 / 장비 2종 | 735 | **0** | +0.000 |

수용 조건 `Luna·Terra·Sol을 이길 수 있는 정책이 최소 하나씩 존재`가
플레이어가 실제로 도달하는 상태에서 성립하지 않는다.

### 2.2 잠금 구조

```
플레이어가 잘함
      ↓
건물 Lv 상승 + 도전 모드 발동
      ↓
수요 배율 1.0 → 1.2474
      ↓
달성 가능한 margin 상한이 0으로 압축
      ↓
success = False  →  크레딧 0, 건물 성장 0
      ↓
같은 미션을 몇 번을 다시 해도 통과 불가
```

접근성 100점에 guard를 통과한 플레이어가 Sol에게 2.347점 차로 져서 실패한다.
보상 루프가 플레이어를 처벌한다.

### 2.3 원인 세 가지

**원인 1 — 문서와 구현의 불일치.**
`docs/17`은 건물 성장 조건을 `접근성 70 이상 → Level 2`,
`접근성 85 이상이며 AI보다 5점 이상 → Level 3`으로 정의한다.
구현은 `game.py`의 `success`에 `margin >= 0.1`을 넣고, 그 `success`가
Level 2 승급과 크레딧 지급 전체를 막는다. Level 2에는 없어야 할 AI 승리 요건이
사실상 모든 보상에 걸려 있다.

**원인 2 — 설계공간 붕괴.**
`_game_metering_factors`는 계단 함수다.

```python
factor = max(0.35, 1.0 - 0.65 * strength)
if link_occupancy[link_id] >= trigger:
    meter[approach] = min(meter[approach], factor)
```

`factor`가 `strength`에만 의존하고 점유율이 임계를 얼마나 넘었는지는 반영하지
않는다. 그래서 `trigger` 값이 달라도 같은 시뮬레이션 결과를 내는 정책이 대량으로
생긴다. 최적해가 큰 동치류가 되고, 무작위 표본 128개면 거의 확실히 걸린다.

참고로 동결된 `corridor_gating`은 램프 함수다.

```python
factor = max(0.35, 1.0 - (occupancy - 0.80) / 0.20 * 0.65)
```

게임 제어법칙은 동결 정책의 상위집합이 아니다. 플레이어는 데모가 추천하는
정책을 어떤 파라미터로도 재현할 수 없다.

**원인 3 — 봇이 플레이어와 같은 풀을 쓴다.**
`_candidate_pool`이 플레이어 장비에 따라 커진다. 장비를 사면 풀이 231에서 735로
늘고 봇의 표본 128개는 그대로다. 표본 비율은 55%에서 17%로 떨어지지만 봇이 뽑는
후보의 질은 유지되므로, 장비 구매가 플레이어에게 우위를 주지 못한다.

### 2.4 수정 방향 — 방향 1 적용됨 (2026-08-04)

준이 방향 1을 채택했고 적용을 마쳤다. 적용 후 같은 방식으로 재측정한 결과다.

| 상태 | 풀 | success | AI 승리 | 신규 Lv3 | 최고 margin |
|---|---:|---:|---:|---:|---:|
| Luna / 표준 / lv1 | 231 | 139 | 49 | 0 | +3.286 |
| Terra / 표준 / lv2 | 231 | 124 | 1 | 0 | +0.120 |
| Sol / 표준 / lv1 | 231 | 125 | 3 | 0 | +0.330 |
| Sol / 표준 / lv3 | 231 | 120 | 0 | 0 | +0.042 |
| Sol / 도전 / lv3 / 장비 2종 | 735 | 391 | 0 | 0 | +0.000 |

진행 잠금은 사라졌다. 모든 도달 가능 상태에서 성공 가능 정책이 100개 이상이다.
회귀 방지 테스트 `test_progression_is_never_locked_in_a_reachable_state`와
`test_mission_success_does_not_require_beating_the_bot`을 추가했다. 테스트 93개 통과.

남은 두 숫자는 **개발을 먼저 진행하고 플레이테스트에서 조정한다** (2026-08-04 준 결정).
숫자만 보고 미리 고치지 않는다. 8/6 1차 플레이테스트와 8/7 밸런싱 세션에서 실제로 만져보고
손시우가 정한다. 아래 측정치는 그때 쓸 입력값이다.

**남은 문제 1 — 건물 Level 3이 도달 불가능하다.**
승급 조건이 `접근성 85 이상 AND margin >= 5`인데, 측정한 모든 상태에서 달성 가능한
최고 margin이 가장 쉬운 Luna에서도 +3.286이다. 신규 Lv3 승급이 전 구간 0건이다.
`docs/17`의 `5점` 임계가 실제 점수 범위와 맞지 않는다. 관측 범위에 맞추려면
`margin >= 3` 부근이 후보다.

**남은 문제 2 — AI 승리가 Terra·Sol에서 거의 불가능하다.**
Terra 231개 중 1개, Sol 231개 중 3개, 도전 모드에서는 0개다. 진행을 막지는 않지만
준이 정한 두 축 중 하나인 `AI를 이긴다` 판타지가 사실상 전달되지 않는다.
아래 방향 2가 이 문제를 직접 겨냥한다.

### 2.4.1 채택하지 않은 나머지 방향

세 가지를 제안한다. 1번은 문서 정합성 회복이라 거의 확정에 가깝고,
2번과 3번은 밸런스 취향이 갈린다.

**방향 1. 미션 성공에서 AI 승리를 분리한다. (권장, 최소 diff)**

```
success        = guard 통과 AND 접근성 임계 충족
AI 승리        = 별도 배지 + 랭킹 표시
Level 2        = 접근성 70 이상
Level 3        = 접근성 85 이상 AND margin >= 5
```

`docs/17`이 원래 정의한 그대로다. 잘 설계한 플레이어는 항상 성장하고, AI를 이기는
것은 추가 도전이 된다. `game.py`의 `success` 식과 `achieved_level` 게이트만
고치면 되고 시뮬레이터는 안 건드린다.

**방향 2. 봇 풀을 플레이어 풀의 부분집합으로 고정한다.**

봇은 항상 거친 격자(`trigger` 10% 단위, `strength` 20% 단위, `diversion` 10 단위)
에서만 뽑는다. 장비를 산 플레이어만 미세 격자에 접근할 수 있으므로 장비 구매가
실제 우위가 된다. 지금의 역전 현상이 사라진다.

**방향 3. 제어법칙에 램프를 복원한다.**

`factor`를 `(occupancy - trigger)`에 비례하게 만들면 `trigger`가 실제 의미를 갖고
설계공간 붕괴가 풀린다. 동결 정책과 같은 법칙이 되므로 데모·게임 정합성도
올라간다. 다만 전 미션 밸런스 재조정이 필요하므로 8월 6일 플레이테스트 전에
결정해야 한다.

### 2.5 부수 문제 — 만족도 포화

`traffic_satisfaction = 50 + score`이고 상한이 100이다. corridor_final에서 점수가
50을 넘으므로 접근성이 항상 100으로 포화된다. 결과적으로 3단계에서 부동산
가치지수와 건물 성장 연출이 변화를 못 보여준다. 점수를 만족도로 옮기는 곡선을
손시우가 다시 정의해야 한다.

## 3. 그 외 결함

| 위치 | 내용 | 조치 |
|---|---|---|
| `game.py::_evaluate_design` | 봇 후보마다 동일한 no_action baseline을 재계산. Sol 평가에서 128회 낭비 | baseline을 루프 밖으로 이동. Sol 0.94초 → 약 0.5초 |
| `game.py::_evaluate_design` | `region` 인자가 함수 안에서 전혀 안 쓰임 | 인자 제거 |
| `game.py::_run_bot_cached` | `region_id`가 캐시 키에 있으나 결과에 영향 없음. 지역마다 캐시가 쪼개져 2배 계산 | 캐시 키에서 제거 |
| `test_game_mode.py` | `test_same_game_request_is_fully_deterministic`이 두 번째 호출에서 `lru_cache`를 맞음. 결정론이 아니라 캐시를 검증 중 | 호출 사이에 `cache_clear()` 삽입 |
| `game.py::_pedestrian_satisfaction` | 임계 10% 악화에서 60점. guard는 15%까지 허용. 10~15% 구간은 guard 통과인데 미션 실패 | 의도면 문서화, 아니면 계수 조정 |
| `simulation.py` | 도전 모드에서 `effective_rain_end`가 늘어 `recovery_time_sec` 절대값이 작아짐 | 랭킹에서 난이도가 다른 기록의 회복시간을 직접 비교하지 않는다 |

## 4. 테스트 보강

현재 `test_game_mode.py` 15개는 결정론, 장비 게이팅, 가드 실패, 스키마 계약,
오류 경로를 덮는다. 빠진 것은 하나이고 그게 2장의 결함을 놓친 이유다.

**추가할 테스트 — 최난도 도달 상태의 승리 가능성**

`test_each_bot_is_beatable_with_a_known_safe_policy`는 기본 진행 상태에서만
검사한다. 실제로 잘하는 플레이어가 도달하는 상태를 검사해야 한다.

```python
@pytest.mark.parametrize(
    ("mission_id", "region_id", "building_level", "progress_extra"),
    [
        ("rain_commute", "seonggeum_cheongsa", 1, {}),
        ("rain_incident", "cheongsa_sejong", 2, {}),
        ("corridor_final", "eojin_corridor", 3,
         {"last_score_margin": 5.0, "last_completion_time_sec": 90.0}),
    ],
)
def test_every_reachable_state_has_at_least_one_winning_policy(
    mission_id, region_id, building_level, progress_extra
):
    """플레이어가 실제로 도달하는 상태에서 승리 가능한 정책이 존재하는지 전수 확인."""
    ...
```

전수 평가는 상태당 약 2초, 세 상태 합쳐 6초 안팎이다. 느린 테스트로 분리할
필요도 없다. 이 테스트가 있었다면 2장의 결함이 구현 시점에 잡혔다.

**Unity 쪽.** 런타임 C# 2077줄에 EditMode 테스트가 `GameSaveServiceTests` 96줄
하나뿐이다. `RainFlowGameController`가 698줄로 가장 크고 가장 위험하다.
컴파일이 통과한 다음 최소한 다음 두 개를 추가한다.

- 백엔드 응답 JSON을 `GameContracts`로 역직렬화했을 때 필드 누락이 없는지
- 백엔드 연결 실패 시 fixture 모드로 전환되고 루프가 계속되는지

## 5. 최대 위험 — Unity 컴파일 미검증

C# 2077줄이 한 번도 컴파일된 적이 없다.

```
ProjectVersion.txt        m_EditorVersion: 6000.3.20f1
설치 확인됨               Unity Hub 3.19.5
설치 안 됨                C:\Program Files\Unity\Hub\Editor\   (경로 자체가 없음)
```

기획 노트가 이미 2026-08-04에 이 불일치를 경고했고, 지금도 그대로다.
Editor 다운로드가 54.03%에서 멈춰 있었다.

**8월 5일 오전에 다른 무엇보다 먼저 해결한다.** Editor 설치와 첫 컴파일 사이에서
나오는 오류의 양을 아무도 모르는 상태다. 2077줄이 무손실로 컴파일될 확률은 낮고,
발견이 늦을수록 대응 시간이 사라진다.

설치 시 `Windows Build Support (IL2CPP)`를 반드시 포함한다. 빠지면 8월 8일
패키징 단계에서 다시 막힌다.

**폴백 기준.** 8월 6일 정오까지 Unity EditMode 테스트가 통과하지 않으면,
그 시점에 준이 웹 프론트 폴백을 결정한다. 백엔드 API가 양쪽에 동일하므로
`frontend/index.html`에 게임 화면을 붙이는 경로는 남아 있다. 이 판단 시점을
미리 정해 두는 것 자체가 계획의 일부다.

## 6. 일정

기존 `docs/17` 일정을 유지하되 검증 게이트를 명시한다.
게이트를 통과하지 못하면 다음 날로 넘어가지 않는다.

### 8월 4일 (오늘) — 자산 보존

| 담당 | 작업 | 게이트 |
|---|---|---|
| 최영 | `codex/ai-traffic-game-slice`의 미커밋 26개 파일 커밋·푸시 | 원격에 존재 |
| 최영 | 소스 커밋과 아티팩트 재생성 커밋을 2단계로 분리 | `_source_git_sha()`가 `HEAD^`를 보므로 순서가 중요 |
| 준 | 나머지 두 체크아웃 폐기 또는 정본 브랜치로 정렬 | 팀 전원이 같은 브랜치를 봄 |
| 준 | 준·최영 공동 승인 기록 (`result_checksum` 불변 증거 첨부) | docs/15 절차 충족 |

커밋 순서.

```bash
git add backend/ contracts/ scripts/ docs/17_GAME_DESIGN_V1.md unity/ .gitignore README.md
git commit -m "feat: AI 교통복구 게임 세로 조각 백엔드와 Unity 소스"
python scripts/generate_contract_artifacts.py
git add -u && git commit -m "chore: 게임 모드 추가 후 동결 아티팩트 재생성"
python -m pytest backend/tests -q
```

### 8월 5일 — 밸런스 결함 수정과 Unity 컴파일

| 담당 | 작업 | 게이트 |
|---|---|---|
| 김경은 | Unity Editor 6000.3.20f1 + IL2CPP 설치, 프로젝트 import, 첫 컴파일 | 컴파일 오류 0 |
| 손시우 | Reality Boundary, 미션·이벤트표, 건물 성장표, AI 조언 문구 확정 | 최영·여하윤이 그 값으로 바로 착수 가능 |
| 최영 | 3장 성능·죽은 코드 정리 | Sol 평가 0.6초 이하 |
| 여하윤 | 정책 편집기·AI 조언 UI를 백엔드 응답 스키마에 맞춤 | `mission.schema.json` 검증 통과 |

### 8월 6일 — 루프 연결과 1차 플레이테스트

| 담당 | 작업 | 게이트 |
|---|---|---|
| 김경은 | 지역 선택부터 Luna 대결까지 Unity에서 연결 | 실제 백엔드로 1회 완주 |
| 최영 | 적응형 지원·표준·도전 고지 문구를 실행 전에 노출 | 난이도 변경이 실행 전에 보임 |
| 손시우 | 1차 플레이테스트 | Luna를 초보가 AI 추천값만으로 통과 |
| 손시우 | 2.4절 밸런스 2건을 실제로 만져보고 1차 판단 | 조정 방향 기록 |
| 준 | 정오 시점 Unity 폴백 판단 | 5장 기준 적용 |

### 8월 7일 — 3단계 완성

| 담당 | 작업 | 게이트 |
|---|---|---|
| 최영 | Terra·Sol, 건물 성장, 가치·보상, 로컬 랭킹 연결 | Lv1→Lv3 진행이 수요·외형에 반영 |
| 김경은 | 원·중·근거리 카메라와 동물 밀도 | 건물 레벨에 따라 밀도 변화 |
| 손시우 | 전체 진행 속도·난이도 승인, **2.4절 밸런스 2건 최종 확정** | 승급이 다음 미션을 잠그지 않음. Level 3이 도달 가능해지고 AI 승리가 노려볼 만해짐 |

### 8월 8일 — 패키징

| 담당 | 작업 | 게이트 |
|---|---|---|
| 김경은 | Unity Windows 빌드 + `Backend/RainFlowSejong.exe` 동봉 | `BackendProcessManager`가 8765~8767에서 기동 성공 |
| 최영 | 인터넷·Python 없는 PC에서 전체 루프 | 3단계 완주 |
| 최영 | 백엔드 강제 종료 시 fixture 전환 | 루프가 끊기지 않음 |
| 손시우 | 게임·UX 최종 승인 | |
| 준 | 발표 방향·사업화 메시지 승인 | 현재 기능과 B2C2G 조건 분리 |

### 8월 9일 — 동결

치명 버그와 밸런스 이상만 수정한다. 새 기능 없음.

## 7. 수용 조건 판정표

`docs/17`의 수용 조건을 검증 방법과 함께 다시 쓴다.

| 조건 | 검증 방법 | 현재 |
|---|---|---|
| 같은 입력·seed는 항상 같은 결과 | `cache_clear()` 후 2회 호출 비교 | 테스트 수정 필요 |
| AI 조언마다 근거와 trade-off 표시 | `advice[].reason`, `.tradeoff` 필수 | 충족 |
| 난이도 변경은 실행 전에 고지 | `adaptive_event.reason`을 실행 전 화면에 표시 | Unity 미검증 |
| 도달 가능 상태에서 미션 성공이 가능 | `test_progression_is_never_locked_in_a_reachable_state` | 충족 |
| 각 AI를 이길 수 있는 정책이 최소 하나 | 기본 진행 상태 3미션 검사 | 충족 (Terra 1개, Sol 3개로 매우 희소) |
| 건물 Level 3 도달 가능 | 신규 승급 관측 | **불충족** (2.4 남은 문제 1) |
| 건물 성장 후 수요와 외형이 실제로 변화 | `next_demand_bonus_pct` + Unity 외형 | 백엔드만 충족 |
| 실제 정책·부동산 예측 오인 표현 없음 | `reality_note`, `out_of_scope` | 충족 |
| 저장 후 진행·랭킹·건물 상태 복구 | `GameSaveService` EditMode 테스트 | 컴파일 미검증 |
| 인터넷 없는 Windows PC에서 전체 루프 | 8월 8일 게이트 | 미검증 |
| 기존 백엔드 테스트 전부 통과 | `pytest backend/tests` | 89개 통과 |

충족 6, 불충족 1, 미검증 2다. 불충족 1개가 게임의 핵심 루프를 막고 있고,
미검증 2개가 모두 Unity 컴파일에 달려 있다.

## 8. 결정 현황

### 확정됨 (2026-08-04, 준)

| 항목 | 결정 |
|---|---|
| 정본 체크아웃 | `codex/ai-traffic-game-slice`. 나머지 두 사본은 사용하지 않는다 |
| 동결 아티팩트 재생성 | 승인. `result_checksum` 불변을 근거로 함 |
| Unity 클라이언트 | Unity로 간다. 폴백 판단 시점은 8월 6일 정오 |
| 진행 잠금 밸런스 | 방향 1 채택. 미션 성공에서 AI 승리 요건 분리 |
| 남은 밸런스 2건 | **개발을 먼저 하고 플레이테스트에서 조정한다.** 미리 숫자를 고치지 않는다 |

### 의사결정 경계

준은 **디자인 컨셉과 전체 방향**만 정하고 디테일은 위임한다.

| 준이 정하는 것 | 위임되는 것 |
|---|---|
| 핵심 판타지와 목표 사용자 | 미션·이벤트·난이도 수치 (손시우) |
| 아트 컨셉과 톤 (친근한 동물 표현, 정보 밀도 3단계) | 스프라이트·팔레트·레이아웃 실행 (김경은) |
| MVP 범위와 무엇을 안 만드는가 | UX 흐름·문구·튜토리얼 (손시우) |
| 사업화 방향과 대외 메시지 | 정책 변수·점수·보상·가치 산식 (손시우) |
| 최종 빌드 승인 | 화면 구성과 컴포넌트 (여하윤) |

준의 재승인이 필요한 것은 핵심 루프 변경, 하루 이상 일정 증가, 실제 돈·정부 데이터 기능 추가뿐이다.

### 팀명과 BM (2026-08-04 확정)

- 아이템명: `<내가 해도 지금보단 잘하겠다.>` TATS (Totally Accurate Traffic Simulator)
- 팀명: **MSGA (Make Sejong Great Again)**
- 팀원: 백서준, 최영, 손시우, 김경은, 여하윤
- 모든 제출물 마감: **8월 10일**

BM은 **초기 무료 배포 후 확장팩 판매**다.

- 본편을 무료로 풀어 플레이어 기반과 플레이 기록을 쌓고, 이후 지역·시나리오·미션 확장팩을 판매한다
- **해커톤 제출 빌드에는 결제 요소를 넣지 않는다.** 인게임 크레딧은 신호 장비와 동물 스킨에만 쓰이고 현금과 교환되지 않는다. `game.py`의 `out_of_scope`가 이미 그렇게 선언하고 있다
- 확장팩은 같은 엔진 위에 지역과 미션을 얹는 구조라, 이번 세로 조각이 그대로 확장 기반이 된다. `MISSIONS`와 `REGIONS` 딕셔너리에 항목을 더하는 형태다
- 장기 B2C2G(랭커 기록을 정책 후보 탐색 데이터로 제공)는 **별도 경로**다. 4장 세 조건(현실성·검증·데이터 권리)을 충족하기 전까지 수익 모델로 설명하지 않는다

### 남은 항목

- 팀원 명단 기입. 백월 제출 텍스트에 남은 유일한 빈칸이다
- 지역 선택이 연출만 바꾸고 난이도는 동일하다는 사실을 발표에서 어떻게 말할지. 코드 주석과 테스트가 이미 그렇게 고정해 두었으므로 난이도 분기처럼 설명하면 사실과 다르다

4번은 코드 주석이 이미 명시하고 테스트도 그렇게 고정해 두었다.
`두 지역 중 선택`을 난이도 분기처럼 설명하면 사실과 다르다.

# TATS 백엔드 기능 설계 V1 — 8/9 코드 동결 기준

> 상태: 2026-08-05 작성 · 대상: 백엔드 담당 · 코드 동결 2026-08-09 22:00
>
> 상위 정본: [`00_TATS_SOURCE_OF_TRUTH.md`](00_TATS_SOURCE_OF_TRUTH.md) · [`19`](19_TATS_UI_UX_DIRECTION_V1.md) · [`20`](20_TATS_UX_FRONTEND_HANDOFF_V1.md) · [`contracts/game-v2`](../contracts/game-v2/README.md)
>
> 이 문서는 UI·아트를 다루지 않는다. 서버가 계산해야 할 것과 Unity에 넘길 계약만 정의한다.

---

## 0. 이 설계의 세 가지 판단

| 판단 | 내용 | 근거 |
|---|---|---|
| **A/B Street는 8/9 빌드에 넣지 않는다** | 교통 코어를 Python으로 직접 구현하고, `TrafficCore` 인터페이스 뒤에 격리해 나중에 교체 가능하게 둔다 | `docs/01`이 "세종 지도 import와 신호 변경 E2E 기술 스파이크"를 **대표 승인 전까지 착수하지 않음**으로 동결. 스파이크를 하지 않는 것이 현재 결정 준수다. Rust 빌드·OSM import·headless API 학습을 4일에 끼워 넣으면 나머지 전부가 무너진다 |
| **플레이 가능 그래프는 지도에서 자동 추출하지 않고 손으로 만든다** | `eojin_map.json`(도로 884개)은 **표시 전용**으로 두고, 시뮬레이션용 그래프(교차로·이동·횡단·건물)를 별도 콘텐츠 JSON으로 만든다 | OSM 표준노드링크에서 위상적으로 올바른 신호 교차로 망을 자동 생성하는 것은 4일 작업이 아니다. 그래프가 15~20 교차로면 손으로 만드는 게 더 빠르고 확실하다 |
| **mutation 경로는 `POST /commands` 하나뿐** | 신호 적용·도로 개방·건물 승급·배속 변경이 전부 같은 command 타입 | 멱등성·stale tick·권위 검증을 한 곳에서만 구현하면 된다. `contracts/game-v2` 불변식 "직접 편집과 AI 초안은 같은 적용 절차"가 코드 구조로 강제된다 |

**준에게 확인이 필요한 것은 첫 번째 하나뿐이다.** `PROJECT_STACK.yaml`은 backend를 "A/B Street headless sidecar"로 적고 있으므로, 8/9 빌드가 자체 코어로 나간다는 사실을 명시적으로 승인받아야 한다. 나머지 둘은 구현 내부 판단이다.

---

## 1. 아키텍처

```text
Unity TATSGame  ──HTTP(127.0.0.1)──▶  FastAPI (game-v2 adapter)
  입력·표현·로컬 GameSave                │
                                        ├── session.py    권위 상태·명령 로그·재생·checksum
                                        ├── clock.py      masterTick ↔ 도시 시각 ↔ 배속
                                        ├── traffic.py    TrafficCore (교체 가능 경계)
                                        ├── signals.py    SignalPlan 검증·충돌·안전 전환
                                        ├── economy.py    포인트·도로 개방·건물 성장
                                        ├── overlays.py   진단 7종
                                        ├── algorithms.py AI 초안 3종 (순수 함수)
                                        └── airecords.py  Luna·Terra·Sol 사전 생성 기록
                                                │
                                        content/ 밸런스·지도·알고리즘·AI 기록 (버전됨)
```

레거시 `archive/legacy-rainflow-v1/`은 **import하지 않는다**. 큐·용량저하·spillback 수식과 가드 봉투 구조는 아이디어로만 가져와 새 이름으로 다시 쓴다 (`docs/00` 레거시 재사용 규칙 3항).

### 1.1 파일 배치

```text
backend/
  app/  main.py contracts.py session.py clock.py traffic.py
        signals.py economy.py overlays.py algorithms.py airecords.py errors.py
  content/  map_eojin.json  rules.json  algorithms.json  ai-records/*.json
  tests/
scripts/  build_playable_map.py  generate_ai_records.py  export_contracts.py
contracts/game-v2/  *.schema.json  openapi.json   ← 생성물
```

`scripts/verify_tats_structure.py`의 금지 경로(`frontend`, `launcher`, `release`, `contracts/policy_design.schema.json` 등)를 되살리지 않는다.

### 1.2 계약 단일 출처

`contracts.py`의 Pydantic 모델이 유일한 정본이고, `scripts/export_contracts.py`가 거기서 JSON Schema 7종과 OpenAPI를 뽑는다. 스키마를 손으로 쓰지 않는다.

```python
class Base(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
```

Python은 snake_case, JSON은 camelCase(`masterTick`, `schemaVersion`)로 자동 변환된다.

---

## 2. 시간 — 게으른 tick

### 2.1 정의

- `masterTick` = Day 1 00:00:00 이후 경과한 **도시 초 정수**. 게임 시작은 `10800` (Day 1 03:00).
- 도시 시각 = `day = tick // 86400`, `timeOfDay = tick % 86400`. 별도 변환 상태를 두지 않는다.
- 물리 스텝 = **1 도시 초**. `masterTick`과 `trafficSimTime`이 같은 수라 단위 혼동 버그가 원천적으로 안 생긴다.
- 배속: `Paused=0`, `X1=60`, `X3=180`, `X5=300` 도시초/실제초. (1배속 실제 1분 = 도시 1시간)

### 2.2 백그라운드 루프를 만들지 않는다

스레드·asyncio 루프 없이, **요청이 올 때 그만큼 앞으로 감는다.**

```python
def advance(session, now):
    elapsed = min(now - session.last_advance_wall, MAX_ADVANCE_REAL_SEC)  # 1.0초
    if now - session.last_advance_wall > STALL_REAL_SEC:                  # 3.0초
        session.connection = "Reconnecting"; session.speed = "Paused"     # M14 자동 정지
    target = session.tick + int(elapsed * CITY_SEC_PER_REAL[session.speed])
    while session.tick < target:
        step_one_city_second(session)
    session.last_advance_wall = now
```

이 한 가지 선택으로 따라오는 것:

- **연결이 끊기면 도시 시간이 자동으로 멈춘다.** polling이 없으면 tick이 안 올라간다. 별도 heartbeat 구현이 필요 없다.
- 경쟁 조건·락이 없다. 요청 하나가 상태를 독점한다.
- 렉으로 30초가 통째로 밀려도 도시 시간이 순간이동하지 않는다 (`MAX_ADVANCE_REAL_SEC` 클램프).
- Unity는 5~10Hz로 `GET /snapshot`을 폴링한다. 그게 곧 게임 루프다.

**결정론과의 관계:** 실제 시각은 "명령이 몇 번째 tick에 꽂히는가"만 정한다. 명령 로그에 `appliedAtTick`이 기록되므로, 같은 로그를 재생하면 결과가 완전히 같다. RNG는 tick 루프 안에서만, 고정된 순서로 소비한다 — 요청 처리 경로에서는 절대 뽑지 않는다.

---

## 3. 교통 코어 (`traffic.py`)

### 3.1 그래프 모델

| 개체 | 필드 | 설명 |
|---|---|---|
| `Intersection` | `id`, `approaches[]`, `movements[]`, `crossings[]`, `defaultPlanId` | 신호 교차로 |
| `Approach` | `id`, `fromLinkId`, `directionId` | 한 교차로의 진입 방향 |
| `Movement` | `id`, `approachId`, `toLinkId`, `turn` | 진입→진출 이동 하나 |
| `Crossing` | `id`, `conflictingMovementIds[]`, `walkSec` | 보행 횡단 하나 |
| `Link` | `id`, `fromId`, `toId`, `storageVeh`, `unlockState` | 방향 있는 도로 구간 |
| `Building` | `id`, `type`, `level`, `linkId`, `baseVehiclePerHour`, `basePedPerHour` | 수요 발생원 |

`conflictingMovementIds`는 **콘텐츠에 손으로 적는다**. 기하학에서 자동 판정하지 않는다 — 교차로 15개 × 이동 8개면 표가 금방 끝나고, 자동 판정은 틀렸을 때 디버깅이 지옥이다.

### 3.2 1 도시 초 스텝

```text
1. 수요       각 건물 → 인접 링크 접근 큐. arrivals = flow/3600 × 시간대곡선 × level배율 × jitter(rng)
2. 유입 포기  접근 큐 > giveUpThreshold 면 신규 도착을 버리고 abandonedVehicles++
3. 현시       교차로별 tickInCycle로 현재 stage 결정 → green movement 집합
4. 배출       served = min(queue, satFlowPerSec × rainFactor)
              하류 링크 점유율 ≥ jamRatio 면 served = 0  (spillback 차단)
              배출분은 하류 접근 큐로 이동, sink면 completedVehicles++
5. 보행       green crossing이면 배출, 아니면 wait += 1
              wait > maxPedWaitSec 면 이탈 → abandonedPedestrians++
              횡단 완료 시 completedPedestrians++
6. 안전       활성 stage의 충돌 이동 쌍 → riskScore 누적
              60틱마다 p = f(riskScore)로 사고 판정 → 링크 차단 blockUntilTick
7. 정산       tick % 3600 == 0 이면 시간대 정산 (5절)
```

- `completedFlow = completedVehicles + completedPedestrians`. **목적지 도착 시 한 번만** 센다. 이게 AI 비교의 주 지표다.
- 내부는 float, checksum은 `round(x * 1000)` 정수로 정규화한다.
- rainFactor는 시나리오 레이어 값(맑음 1.00 / 약우 0.95 / 강우 0.89 / 폭우 0.84).

### 3.3 교체 경계

```python
class TrafficCore(Protocol):
    def step(self, state: WorldState, plans: dict[str, SignalPlan], rng: Random) -> StepEvents: ...
    def measure(self, state: WorldState) -> Measurements: ...   # 오버레이·미리보기 입력
```

A/B Street를 나중에 붙일 때 이 두 함수만 갈아끼운다. `session.py`, `economy.py`, `overlays.py`는 손대지 않는다.

---

## 4. SignalPlan — 검증·미리보기·안전 전환 (`signals.py`)

### 4.1 계약

```text
SignalPlan
  schemaVersion, planId, intersectionId, status
  stages[]  { stageId, order, durationSec,
              allowedVehicleMovements[], allowedPedestrianCrossings[], priorityTarget }
  yellowSec, allRedSec, pedestrianClearanceSec       ← 서버 계산값, 클라이언트 입력 아님
  cycleSec, offsetSec, affectedIntersectionIds[]
  effectiveTrafficSimTime, masterTick
```

`status = Draft | Validating | Scheduled | SafeTransition | Active | Rejected`
`priorityTarget = None | Vehicle | Pedestrian | Emergency`

`cycleSec = Σ(durationSec + yellowSec + allRedSec)`. 클라이언트가 보낸 `cycleSec`은 무시하고 서버가 다시 계산해 응답에 넣는다 (UI는 계산하지 않는다).

### 4.2 위험 2단계

이게 이 게임의 안전 규칙 전부다.

| 단계 | 조건 | 처리 |
|---|---|---|
| **Hard — 거절** | 단계 0개 · `durationSec ∉ [5,120]` · `cycleSec ∉ [30,240]` · 존재하지 않는 movement/crossing id · **한 stage에서 보행 횡단과 그 횡단의 `conflictingMovementIds`가 동시에 green** · 어떤 이동도 green이 아닌 stage | `422 INVALID_SIGNAL_PLAN` + 위반 목록. 적용 불가 |
| **Soft — 경고 후 사용자 선택** | 차량 이동 간 충돌 쌍이 동시에 green · 접근속도 대비 황색 부족 · 직전 적용 후 `minReplanIntervalSec` 미만 재적용 | `ImpactPreview.riskLevel = High` + `expectedPenalty` + `conflictMovementPairs`. `acknowledgeRisk: true`로만 적용 |

보행자를 차에 밀어 넣는 계획은 막고, 차끼리 위험한 계획은 대가를 보여주고 허용한다. `docs/20` 6.2 "위험 계획은 차단하지 않는다"와 `contracts/game-v2` "hard safety 위반은 차단한다"를 둘 다 만족하는 유일한 선이다.

### 4.3 ImpactPreview — 상태를 바꾸지 않는다

```python
def preview(session, draft) -> ImpactPreview:
    fork = session.world.copy()                       # deepcopy
    fork_rng = Random(session.seed ^ session.tick)     # 세션 RNG를 소비하지 않는다
    run(fork, plans_with(draft), PREVIEW_HORIZON_SEC)  # 300 도시초
    base = session.cached_base_projection or run(session.world.copy(), plans, 300)
    return diff(base, fork)
```

**미리보기가 세션 RNG를 건드리면 결정론이 깨진다.** 별도 RNG를 쓰고, 원본 world는 복사본만 만진다.

응답: `queueDeltaByDirection[]`, `pedestrianWaitDeltaSec`, `pedestrianAbandonmentDelta`, `safetyScoreDelta`, `riskLevel`, `conflictMovementPairs[]`, `expectedPenalty`, `possibleRoadBlockIds[]`, `basePlanId`, `draftPlanId`, `trafficSimTimeRange`, `masterTick`.

### 4.4 안전 전환

적용은 즉시가 아니라 예약이다.

```text
현재 stage 종료 → yellowSec → allRedSec → pedestrianClearanceSec → 새 계획 Active
scheduledTick = 현재 주기 종료 tick + yellow + allRed + pedClearance
```

`yellowSec`, `allRedSec`, `pedestrianClearanceSec`는 접근 제한속도와 횡단 길이에서 서버가 계산한다 (`rules.json`의 계수). 응답에 `scheduledTick`과 남은 전환 단계를 넣어 M09가 그릴 수 있게 한다.

---

## 5. 경제 (`economy.py`)

### 5.1 시간대 정산 — 매 도시 1시간

```text
획득 = 10 + max(0, 이번 시간 completedFlow − 비교기준)
```

- 감소해도 이미 가진 포인트를 깎지 않는다. 증가분만 `+0`이 된다.
- **Day 1 비교기준**: 세션 생성 시 기본 신호 계획으로 24시간을 headless 실행해 시간대별 completedFlow 24개를 미리 뽑아 둔다 (86,400 스텝, 1~2초). 이 기준선은 **세션 시작 시점 지도**를 쓴다 — 플레이어가 도로를 열면 기준선보다 유리해지는데, 그게 성장 보상의 의도다.
- **Day 2 이후 비교기준**: 플레이어 본인의 전날 같은 시간대 실적.
- 응답은 `currentFlow`, `baselineFlow`, `baselineSource`, `delta`, `basePoints`, `bonusPoints`, `earnedPoints`를 **분리해서** 준다. UI가 빼기를 하지 않는다.

### 5.2 도로 개방

```text
RoadUnlockInspector
  roadId, unlockState, connectedNodeIds
  unlockCost, currentPoints, canPurchase, disabledReason
  expectedNewBuildingIds[]
  expectedVehicleDemandPerCityHour, expectedPedestrianDemandPerCityHour
```

- 개방 조건: 이미 열린 영역과 인접할 것. 아니면 `disabledReason = NOT_CONNECTED`.
- 비용은 `rules.json`의 곡선 `cost(n) = base × growth^n` (n = 이미 산 개수). 코드에 숫자를 박지 않는다.
- **첫 도로를 실제 3분 안에 살 수 있게** 초기 비용을 잡는다. 1배속 3분 = 도시 3시간 = 정산 3회 = 기본 30포인트 + 보너스. 따라서 첫 비용 ≈ **35~40포인트**가 출발값이다.
- 거절 사유 enum: `INSUFFICIENT_POINTS`, `NOT_CONNECTED`, `ALREADY_UNLOCKED`, `BLOCKED_BY_INCIDENT`.

### 5.3 건물

```text
BuildingInspector
  buildingId, buildingType, level
  vehicleFlowPerCityHour, pedestrianFlowPerCityHour, hourlyDemandProfile
  adjacentRoadIds, nextLevelVehicleDelta, nextLevelPedestrianDelta
  upgradeCost, canUpgrade, disabledReason
  currentVisualId, nextVisualId
```

- 건물별 Level 1→2→3을 **포인트로 산다**. 성과 기반 자동 승급이 아니다 (레거시와 다른 지점).
- 수요 배율: Lv2 = `1.2×`, Lv3 = `1.5×`.
- 포인트가 줄거나 실적이 나빠져도 이미 산 Level을 내리지 않는다.
- `visualId`는 서버가 콘텐츠에서 읽어 넘긴다. Unity가 규칙으로 유추하지 않는다.

---

## 6. 진단 오버레이 7종 (`overlays.py`)

한 엔드포인트, `overlayType` 파라미터. 전부 **같은 tick의 world를 다르게 투영한 것뿐**이라 각 15줄 안쪽이다.

| overlayType | mapElementId | value / unit | severity 기준 |
|---|---|---|---|
| `Traffic` | linkId | completedFlow, saturation / `veh_per_hour`, `ratio` | 포화도 |
| `Queue` | approachId | queueVeh / `veh` | giveUpThreshold 대비 |
| `PedestrianAbandonment` | crossingId | avgWaitSec, abandonCount / `sec`, `count` | maxPedWait 대비 |
| `SignalPhase` | intersectionId | 현재/다음 stage, 남은 초 / `sec` | 없음 (정보) |
| `SafetyRisk` | intersectionId | riskScore / `score` | 사고 확률 구간 |
| `BuildingInflow` | buildingId | vehiclePerHour, pedPerHour / `per_city_hour` | 생산량 분위 |
| `RoadUnlock` | roadId | unlockCost / `points` | 구매 가능 여부 |

공통 필드는 계약대로 `overlayType, masterTick, cityClockRange, trafficSimTimeRange, mapElementId, directionId, value, unit, severity, relatedIntersectionIds, relatedBuildingIds`.

---

## 7. 스킬북과 AI 초안 (`algorithms.py`)

LLM 없음. 알고리즘 3종은 **현재 측정값을 받아 SignalPlan을 내는 순수 함수**다.

| algorithmId | 정의 | trade-off |
|---|---|---|
| `fixed_time` | 모든 stage 균등 배분 | 안정적, 수요 편차에 둔감 |
| `proportional_green` | stage별 수요 비율로 녹색시간 배분 (Webster 단순화) | 주 접근로 유리, 소수 방향 대기 증가 |
| `pedestrian_priority` | 보행 대기 임계 초과 횡단의 stage를 앞당기고 연장 | 보행 이탈 감소, 차량 지체 증가 |

- 응답에 `algorithmId`, 사용한 입력, 바꾼 stage·시간·우선순위, 기대 효과, 부작용을 담는다.
- 선택하지 않은 알고리즘을 섞지 않는다 — 함수가 하나뿐이라 구조적으로 불가능하다.
- **AI 초안도 직접 편집과 완전히 같은 경로를 탄다**: `draft → preview → commands(ApplySignalPlan)`. 별도 적용 API를 만들지 않는다.
- `AlgorithmSkill`(선행조건·해금비용·scope·기대효과·contentVersion)은 `content/algorithms.json`에서 그대로 읽어 넘긴다.

---

## 8. AI 기록 — Luna·Terra·Sol (`airecords.py`)

### 8.1 사전 생성

런타임에 AI를 돌리지 않는다. `scripts/generate_ai_records.py`가 **같은 엔진으로** 3 시작노드 × 3 모델 = 9개를 미리 실행해 JSON으로 떨군다.

- 봇은 플레이어와 같은 지도·seed·수요·경제·사고 규칙에서 출발한다. 공짜 개방이나 사전 확장 권한 없음.
- **도시 시간 10분마다 전역 행동 1개**만 제출한다. 행동은 `신호계획 적용` / `도로 개방` / `건물 승급` 중 하나.
- 난이도는 한 봇의 3개 노브다: 탐색 예산(9 / 36 / 128 후보), 안전 여유, 반응 지연.
- 기록에 담을 것: 일자·시간대별 completedFlow, 포인트, 개방 도로, 건물 Level, 사고·안전, 모든 행동과 `appliedAtTick`, seed, 버전 3종, checksum.

### 8.2 릴리스 게이트

9개 전부 없거나 재생 검증(행동 로그 재생 결과 == 저장된 최종 결과)이 실패하면 **빌드를 내지 않는다**. 런타임에서 다른 버전 기록으로 대체하지 않는다. `AI_RECORD_MISSING`은 사용자 폴백이 아니라 릴리스 실패다.

### 8.3 비교 응답

`AiComparisonSnapshot`: `recordId, model, startNodeId, cityDay, mapVersion, gameRuleVersion, seed, playerCompletedFlow, aiCompletedFlow, completedFlowGap, playerSafetyScore, aiSafetyScore, accidents, playerPoints, aiPoints, unlockedRoadIds, buildingLevels, actionTimeline[], masterTick`.

---

## 9. API

모든 응답 봉투에 `schemaVersion, masterTick, mapVersion, gameRuleVersion, contentVersion, asyncState`가 들어간다.

| 경로 | 하는 일 |
|---|---|
| `GET /api/health` | 버전 3종 + 프로세스 상태 |
| `POST /api/game-sessions` | `{startNodeId, opponentModel, seed?}` → 세션 생성 + Day1 기준선 계산 + 첫 snapshot |
| `GET /api/game-sessions/{id}/snapshot` | **시간을 감고** 현재 상태 반환. 게임 루프의 심장 |
| `POST /api/game-sessions/{id}/commands` | **유일한 mutation.** 아래 4종 |
| `POST /api/game-sessions/{id}/signal-plans/preview` | ImpactPreview (상태 불변) |
| `POST /api/game-sessions/{id}/signal-plans/draft` | 알고리즘 기반 AI 초안 (상태 불변) |
| `GET /api/game-sessions/{id}/overlays/{overlayType}` | OverlaySnapshot |
| `GET /api/game-sessions/{id}/inspect/{kind}/{targetId}` | Intersection / Building / RoadUnlock Inspector |
| `GET /api/game-sessions/{id}/ai-comparison?day=N` | AiComparisonSnapshot |
| `POST /api/game-sessions/{id}/resume` | 명령 로그 재생 + 검증 |
| `GET /api/content/algorithms` | AlgorithmSkill[] |

**command 4종** (discriminated union on `type`):
`ApplySignalPlan{plan, acknowledgeRisk}` · `UnlockRoad{roadId}` · `UpgradeBuilding{buildingId}` · `SetSpeed{speed}`

공통 요청 필드: `clientCommandId`(UUID), `expectedTick`.
공통 응답(`CommandReceipt`): `clientCommandId, accepted, acceptedTick, scheduledTick, resultingStateVersion, rejection{code, message, disabledReason}`.

- **멱등**: `clientCommandId`를 이미 본 적 있으면 재적용하지 않고 같은 receipt를 그대로 돌려준다.
- **stale tick**: `currentTick − expectedTick > 300`(도시초)이면 `409 STALE_TICK` + 현재 tick + snapshot 버전. 정확 일치를 요구하지 않는다 — 클라이언트는 항상 조금 뒤처져 있다.

**오류 코드 enum** (안정, 문자열):
`BACKEND_UNAVAILABLE`, `STALE_TICK`, `INVALID_SIGNAL_PLAN`, `RISK_NOT_ACKNOWLEDGED`, `INSUFFICIENT_POINTS`, `NOT_CONNECTED`, `ALREADY_UNLOCKED`, `MAX_LEVEL`, `BLOCKED_BY_INCIDENT`, `VERSION_MISMATCH`, `AI_RECORD_MISSING`, `RESUME_VALIDATION_FAILED`, `SESSION_NOT_FOUND`.

---

## 10. 저장과 재개 — 서버가 서명한 체크포인트

서버는 DB를 만들지 않는다. 세션은 프로세스 메모리의 `dict[str, GameSession]`이고, **영속화 책임은 Unity의 로컬 GameSave**다.

매 도시 1시간 정산마다 서버가 snapshot 응답에 `resumeToken`을 함께 넣는다.

```text
resumeToken = { worldState, tick, seed, mapVersion, gameRuleVersion, contentVersion, stateChecksum }
GameSave    = { schemaVersion, startNodeId, opponentModel,
                resumeToken,                    ← 서버가 마지막으로 준 것
                commandLog[],                   ← resumeToken 이후 명령만
                lastConfirmedTick }
```

`worldState`는 큐·신호·포인트·개방·건물 Level 전부를 담아도 수 KB다. Unity는 이걸 **계산하지 않고 보관만** 한다.

**재개 절차**: `POST /resume`에 GameSave를 보낸다 → 서버가 `resumeToken.stateChecksum`을 재계산해 자기가 서명한 상태인지 확인한다 → 그 상태를 적재하고 `commandLog`를 `appliedAtTick`대로 재생하며 `lastConfirmedTick`까지 감는다.

- 일치 → `ResumeReady` + 새 sessionId. 해당 tick부터 재개.
- token 변조·버전 차이·재생 후 checksum 불일치 → `RESUME_VALIDATION_FAILED` + 원인. **임의 병합 금지.**

재생 구간이 **최대 1 도시 시간(3600 tick)으로 고정**된다. 배속과 플레이 시간에 무관하게 1초 안에 끝난다. 명령 로그 전체를 처음부터 재생하는 방식은 5배속 90분에서 160만 tick이 되어 쓸 수 없다.

`stateChecksum`: 상태를 정규화(float → `round(x*1000)` 정수, None 제거, `sort_keys`)한 JSON의 sha256. 손상·버전 오류 검출용이며 DRM이 아니다.

**runtime fixture 폴백은 어디에도 만들지 않는다.** mock은 테스트와 컴포넌트 개발 전용이며 제품 코드 경로에 존재하지 않는다.

---

## 11. 보안·운영

- FastAPI는 `127.0.0.1`에만 bind. 기본 포트 8765, 충돌 시 8766·8767.
- 프로세스 기동 시 session secret을 만들고 command API에서 검증한다. URL·로그에 비밀값을 남기지 않는다.
- 계정·사용자 DB·클라우드 프로필을 만들지 않는다. 로컬 sessionId는 진행 식별용이며 개인정보가 아니다.
- 감사 로그: 버전·seed·tick·명령·검증·적용·오류. 이름·이메일·기기 식별자는 수집하지 않는다. 크기 제한과 회전을 둔다.

---

## 12. 4일 실행 순서

매일 22:00 게이트. 실패하면 신규 기능을 멈추고 마지막 성공 지점에서 고친다.

| 날짜 | 만드는 것 | 게이트 |
|---|---|---|
| **8/5 (D-4)** | `contracts.py` 7모델 · `clock.py` · `session.py` · `traffic.py` 스텝 · `content/map_eojin.json` 손작성 · `POST /game-sessions` · `GET /snapshot` | 시간이 흐르고 차가 큐에 쌓이며 신호에 맞춰 빠진다 |
| **8/6 (D-3)** | `signals.py` 검증·충돌·preview·안전 전환 · `commands` 멱등/stale · `economy.py` 시간대 정산 | **첫 3분 수용조건 완주**: 03:00 시작 → 한 단계 편집 → 미리보기 → 적용 → 3회 정산 |
| **8/7 (D-2)** | 도로 개방 · 건물 Lv1~3 · 오버레이 7종 · 알고리즘 3종 · `export_contracts.py` | 첫 도로 구매까지 3분 내 도달 · 건물 승급이 인접 수요와 `visualId`를 함께 바꿈 |
| **8/8 (D-1)** | AI 기록 9개 생성·검증 · 비교 API · resume 재생 · PyInstaller 번들 | 인터넷·Python 없는 외부 Windows PC 2대 × 2회 완주 |
| **8/9 (D-0)** | 치명적 버그만. ZIP·체크섬·태그·실행 매뉴얼 | **22:00 동결** |

### 12.1 늦으면 자르는 순서

Sol → 알고리즘 2종(`fixed_time`만 남김) → 오버레이 4종(`Queue`·`SignalPhase`·`RoadUnlock`만 남김) → 건물 Lv3 → AI 비교 상세(격차 숫자만).

**끝까지 지키는 최소선**: Luna 1개 · 시작 노드 1개 · 신호 편집→미리보기→안전 적용 · 시간대 정산 · 도로 1개 개방 · 연결 끊김 즉시 정지.

---

## 13. 테스트 — 이것만

프레임워크를 늘리지 않는다. pytest 하나, 아래 8개면 이 설계의 위험을 전부 덮는다.

1. **결정론**: 같은 seed + 같은 명령 로그 2회 재생 → `stateChecksum` 동일
2. **미리보기 무해성**: preview 100회 호출 후에도 세션 checksum 불변
3. **멱등**: 같은 `clientCommandId` 3회 → 1회만 적용, receipt 동일
4. **stale tick**: 오래된 `expectedTick` → 409, 상태 불변
5. **hard 거절**: 보행 횡단과 충돌 이동 동시 green → 422, 적용 안 됨
6. **soft 통과**: 차량 충돌 계획은 `acknowledgeRisk` 없으면 거절, 있으면 적용 + 감점 기록
7. **정산 규칙**: 유동량 감소 시 포인트가 깎이지 않고 보너스만 `+0`
8. **첫 3분**: 세션 생성 → 편집 → 적용 → 3시간 진행 → 첫 도로 구매가 도시 3시간 안에 성립

`generate_ai_records.py`는 생성 직후 재생 검증을 자체 수행한다 (8.2절 게이트).

---

## 14. 지침 대조

| 지침 (정본 출처) | 이 설계에서 지켜지는 곳 |
|---|---|
| Unity가 교통·포인트·안전·비용을 계산하지 않는다 | 모든 파생값을 서버가 계산해 응답에 넣음. `cycleSec`·`yellowSec`조차 서버 계산 (4.1) |
| 직접 편집과 AI 초안이 같은 SignalPlan·같은 적용 경로 | `draft`는 초안만 만들고 적용은 `commands` 하나뿐 (7절, 9절) |
| 위험 계획은 결과를 먼저 보여주고, hard safety는 차단 | 2단계 위험 표 (4.2) |
| 연결 중단 시 mutation 실패, fixture 진행 금지 | polling이 곧 tick이라 자동 정지 (2.2), fixture 경로 미구현 (10절) |
| 한 번에 오버레이 하나 | 오버레이는 상태가 아니라 조회. 서버는 요청받은 하나만 계산 (6절) |
| 결정론·동일 seed 재현 | RNG는 tick 루프 전용, 명령 로그 재생 검증 (2.2, 10절, 13-1) |
| Day 1 기준선 / Day 2 전날 비교, 감소해도 차감 없음 | 5.1 |
| 목적지 도착 차량+보행자를 한 번만 집계 | 3.2 |
| 첫 도로를 약 3분 안에 | 초기 비용 35~40포인트 근거 (5.2) |
| AI는 10분마다 전역 행동 1개, 같은 규칙 | 8.1 |
| 계정·로그인·클라우드 없음 | 10절, 11절 |
| 실측 개선 효과·실제 신호제어 주장 금지 | 합성값은 `content/`에 격리하고 응답에 출처 구분 필드 유지 |
| 밸런스 값을 코드에 산재시키지 않음 | 전부 `content/rules.json`, `gameRuleVersion`으로 버전됨 |

---

## 15. 미해결 — 시작 전 결정

1. **A/B Street 미통합 승인** (준). 8/9 빌드가 자체 Python 코어로 나가고, `TrafficCore` 뒤에서 나중에 교체한다는 사실.
2. **콘텐츠 수치** (손시우): `giveUpThreshold`, `maxPedWaitSec`, 사고 확률 곡선, 도로 비용 곡선, 건물 업그레이드 비용, 봇 3단계 노브. 기다리지 말고 `rules.json`에 `provisional: true`로 임시값을 넣고 진행한다.
3. **플레이 가능 그래프 규모** (준·손시우): 교차로 몇 개로 시작할지. 권장은 **시작 노드 3개 + 인접 12개 = 15개**. 이보다 크면 손으로 만드는 충돌표가 부담이 된다.

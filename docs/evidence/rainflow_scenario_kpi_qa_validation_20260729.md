# RainFlow Sejong — 근거·시나리오·KPI·공정성·QA 정본 v2

**기준일:** 2026-07-29 KST
**게시 대상:** GitHub Issue/`docs/evidence/` 및 Notion 기획·검증 페이지
**담당 범위:** 운영현황 팩트체크, provisional 수치 판정, KPI 계산 정의, 공정성·안전 규칙, QA 기대값
**범위 밖:** MVP 재설계, 실도로 제어, 현장 안전 인증, 세종 실측 성과 주장
**상태:** `조건부 승인` — 아래 P0 수정과 동기화 QA 전까지 대표 개선율 동결 금지

**코드 대조:** 최초 `main @ 9080e41`; 2026-07-29 `main @ 6d21d8e`에서 아래 5개 검토 파일의 Git blob이 모두 동일함을 재확인

검토한 GitHub `main` 파일 지문:

```text
backend/app/simulation.py        b8d9bdf248a719caf6ff8c203fe407e13d03f7c1
backend/app/safety.py            9c2643a1b3083af5442aa8ab7d12eaa3169b3d54
backend/tests/test_spike.py      619488e728f9ae20b0b4a7f6f2f31538edac2495
backend/fixtures/demo_run.json   75dec6933726fdbb4fc2ec2d334a0debf381ef72
docs/16_DEMO_SCRIPT.md           18bb553aa92283c93e6e2798efa0e92604a26cc5
```

## 0. 문서 사용법

판정 태그는 다음처럼 통일한다.

| 태그 | 의미 |
|---|---|
| `[사실]` | 기관이 작성한 공식 문서·데이터에서 직접 확인 |
| `[공식발언]` | 공식 회의록에 기록된 집행부·의원 발언. 자산대장·검사성적서와는 구분 |
| `[보도]` | 기관 보도자료 또는 언론 보도 |
| `[연구]` | 논문·학술발표가 지지하는 일반적 방향 또는 계산 근거 |
| `[계산]` | 확인된 입력을 이용한 산술. 원자료의 불확실성을 상속 |
| `[추론]` | 둘 이상의 근거를 연결한 해석 |
| `[가설]` | 실제 후보구간·운영수단 등에 대해 외부 검증이 필요한 명제 |
| `[가정]` | 합성 실험을 위해 팀이 정한 provisional 값 |
| `[미확인]` | 공개자료만으로 확정 불가 |

운영현황의 사실 게이트와 합성 실험의 검증 게이트를 섞지 않는다.

```text
세종 운영현황 → 공식 문서·기관 회신으로만 확정
RainFlow 시나리오 → 문헌 기반 민감도값 + 명시적 합성 가정
RainFlow 결과 → 동일 버전·동일 seed·수정된 KPI 계산의 실행 결과
현장 성과 → 현재 범위 밖
```

### 0.1 dataset_id·폴백 경계 반영 상태

- 현재 기본값은 `dataset_id=synthetic-v0`이며 실제 자료 어댑터는 설치하지 않았다.
- 요청·실행 결과·재현 입력·health 응답에 dataset identity를 기록한다.
- run 결과에는 `data_class=synthetic`, `schema_version=rainflow-dataset-v1`, `adapter_version=builtin-synthetic-v1`을 함께 남긴다.
- 미설치 dataset은 API 입력 검증에서 422로 거절하며 synthetic fixture로 위장해 폴백하지 않는다.
- 저장 fixture의 dataset과 요청 dataset이 다르면 폴백을 거절한다.
- dataset identity를 run ID와 result checksum에 포함하므로 식별자는 재생성되지만, KPI 값·가드 판정·정책 순위는 변경하지 않는다.
- `backend/tests/test_dataset_contract.py`와 생성물 동기화 테스트를 승인 게이트로 사용한다.

## 1. 운영현황 팩트 레지스터

| claim_id | 주장 | 판정 | 발표 허용 범위 | 금지되는 확장 |
|---|---|---|---|---|
| `F-REMOTE-01` | 2026년 7월 원격제어 장애가 해소됐다 | `[미확인]` | “2월 조사·개선계획 단계, 7월 현재 공개자료상 완료 여부 미확인” | “미복구”, “복구 완료”, 현재 온라인율·정상화율 추정 |
| `F-COUNT-345` | 2020년 온라인 신호제어 345개소 구축 | `[사실]` | 시점·단위와 함께 사용 | 2026년 현재 온라인 제어기 수로 사용 |
| `F-COUNT-346` | 346개 교차로 | `[공식발언]` | “2025년 의원 발언 기준” | 공식 자산대장 또는 366과 동일 모집단으로 취급 |
| `F-COUNT-366` | LH 인수 1~4생활권 온라인 제어기 약 366개 | `[공식발언]` | 2026-02-03 집행부의 근삿값 모수로만 사용 | 현재 정상·온라인·원격제어 가능 수로 사용 |
| `F-FAULT-236` | 1차 조사에서 236개 불량 | `[공식발언]` | 조사 시기와 함께 과거 조사 결과로 사용 | 하드웨어 고장 236개, 영구 오프라인 236개로 변환 |
| `F-FAULT-RATE` | 현재 장애율·복구율 | `[미확인]` | “유형별 건수와 현재 복구율 미공개” | `236÷366=64.5%`, “약 70%”, `130개 정상`, 복구율 `0%` |
| `F-SMART-14` | 1생활권 스마트교차로 14개소 구축·실증 | `[사실/보도]` | 2020년 구축·실증 규모 | 2026년 14개소 전부 상시 AI·실시간 적응제어 |
| `F-SMART-TOD` | 일부 지점·시간대 최적 TOD 적용 | `[연구]` | 적용 연구 사례로 사용 | 14개 전체의 현재 운영모드로 일반화 |
| `F-DATA-VDS` | VDS 교통량·속도·점유율 등 시스템 데이터 유형 존재 | `[사실]` | 시스템 설명 수준 | 특정 회랑의 5분 자료·대기행렬·품질 플래그가 공개됐다고 주장 |
| `F-DATA-LIVE` | 전국 실시간 신호 API 존재 | `[사실]` | API 존재·제공필드 설명 | 세종 대상 레코드·지연·완전성을 표본 호출 없이 보장 |
| `F-STANDARD-R29` | 공개 확인된 최신 표준은 R29 | `[사실]` | 표준판·공개일과 함께 사용 | 세종 모든 장비가 R29 또는 상호 호환된다고 주장 |
| `F-COMPAT-SEJONG` | 세종 장비별 호환성 | `[미확인]` | “자산·시험 매트릭스 필요” | 제조사·프로토콜·고장원인 추정 |

### 1.1 236과 366의 산술 충돌 처리

회의록에는 “약 70%가, 236개가 불량”과 “한 366개”가 함께 나온다. `236÷366=64.48%`이지만 분모 자체가 구두 근삿값이고 두 표현도 일치하지 않는다.

- 내부 검토 메모에서는 `[계산] 64.48%`로 남길 수 있다.
- 발표·부스·대표 표에서는 **64.5%와 70% 모두 장애율로 사용하지 않는다.**
- 공식 분모, 상태 정의, 조사 기준일을 받은 뒤에만 비율을 다시 계산한다.

## 2. 문제 정의와 주장 경계

### 2.1 방어 가능한 문제 정의

> 공개 공식자료는 세종 1~4생활권 온라인 신호제어망의 구축과 2026년 초 1차 불량조사를 확인하지만, 7월 현재 원격제어 정상화율·고장유형·스마트교차로 전체 운영모드·장비별 호환성은 공개하지 않는다. 따라서 RainFlow는 실제 세종 제어기나 실시간 신호망을 사용한다고 주장하지 않고, 우천 시 연속 교차로 회랑의 역류 위험과 정책별 피해 전가를 합성 시나리오로 비교하는 오프라인 의사결정 프로토타입으로 한정한다.

### 2.2 주장 사다리

| 단계 | 현재 허용 여부 | 근거 조건 |
|---|---|---|
| 세종에 온라인 신호제어 구축 이력이 있다 | 허용 | 2020년 행복청 자료 |
| 2026년 초 1차 조사에서 236개 불량이 언급됐다 | 허용 | 2026-02-03 공식 회의록 |
| 2026년 7월에도 236개가 그대로 고장이다 | 금지 | 최신 상태표 없음 |
| 특정 회랑에서 우천 spillback이 실제 발생한다 | 가설 | 실측 교통량·대기행렬·강우 동시자료 필요 |
| RainFlow 정책이 세종에서 실제 개선효과를 냈다 | 금지 | 현장실험·승인·검증 없음 |
| 합성 모델에서 특정 run의 KPI가 변했다 | QA 통과 후 허용 | 버전·seed·공식 계산 정의·결과 원본 필요 |

## 3. Provisional 시나리오 정본 v2

동결된 시나리오 ID와 정책 ID는 유지한다.

```text
scenario_id: dry_base | rain_spillback_a | rain_spillback_b
policy_id: no_action | fixed_metering | corridor_gating
```

### 3.1 공통 시간축

| 구간 | 시각 | 상태 | 판정 |
|---|---:|---|---|
| 준비 | `0~899초` | dry | `[가정]` |
| 우천 전이 | `900~1,139초` | moderate, 4분 | `[가정]` |
| 우천 첨두 | `1,140~2,699초` | heavy, 26분 | `[가정]` |
| 회복 관측 | `2,700~3,599초` | dry, 15분 | `[가정]` |

발표에서 “30분 내내 heavy rain”이라고 말하지 않는다. 구현상 우천 30분은 moderate 4분과 heavy 26분이다.

### 3.2 시나리오 값

| scenario_id | 용량계수 | 우천 중 수요 배율 | 공간 제약 | v2 판정 |
|---|---|---:|---|---|
| `dry_base` | dry `1.00` | `1.00` | 없음 | 기준선 승인 |
| `rain_spillback_a` | moderate `0.89` → heavy `0.84` | `1.10` | 없음 | 문헌 기반 계수 + 합성 수요 스트레스 |
| `rain_spillback_b` | moderate `0.89` → heavy `0.84` | `1.18` | L23 가용 저장공간 `×0.80` | 조건부 승인 |

강우 용량계수 권고값은 Ibijola et al. Table 5의 네 지점 우천/건조 진입용량비 평균을 다시 계산한 것이다.

| 강우 | 네 지점 평균 | 권고값 | 사용조건 |
|---|---:|---:|---|
| light | `0.953` | `0.95` | 해외 다차로 회전교차로 자료에서 계산한 민감도값 |
| moderate | `0.886` | `0.89` | 동일 |
| heavy | `0.843` | `0.84` | 동일 |

현재 코드의 heavy `0.83`은 논문 평균이 아니다. 유지하려면 “관측 범위 안에서 선택한 보수적 스트레스 가정”으로 표시해야 한다. v2 정본 권고는 `0.84`다.

### 3.3 가정값 레지스터

| 값 | 현재/권고 수치 | 근거 분류 | 발표 라벨 |
|---|---:|---|---|
| 수요 배율 A/B | `1.10 / 1.18` | `[가정]` | 첨두수요 스트레스 |
| 외부수요 합계 | 건조 기준 `1,440 veh/h` | `[계산]` from 합성 입력 | 합성 기본수요 |
| 저장공간 L12/L23/BYPASS | `22 / 18 / 60 veh` | `[가정]` | 가상 링크 |
| B의 L23 가용공간 | 목표 `18×0.80=14.4 veh` | `[가정]` | 부분 공간 점유 |
| 정체 점유율 | `0.95` | `[가정]` | 합성 정체 판정 |
| capacity drop | `0.70` | `[가정]` | 합성 방출손실 |
| fixed metering | `0.45` | `[가정]` | 공정성 음성대조군 |
| gating 시작·하한 | `0.80 / 0.35` | `[가정]` | 합성 정책 임계 |
| 회복 조건 | 점유율 `<0.50`, 모든 외부 큐 `<5 veh` | `[가정]` | 합성 회복규칙 |
| 공정성 한도·분모 하한 | `15% / 30초` | `[가정]` | 내부 harm budget |
| 우회 추가지체 한도 | `180초` | `[가정]` | 내부 전가피해 한도 |
| 입력 stale 한도 | `120초` | `[가정]` | 향후 현장연동용 provisional |

수요 `1.10/1.18`은 “비가 오면 교통량이 10%/18% 증가한다”는 뜻이 아니다. 세종 실측치도 아니다.

### 3.4 B 시나리오 구현 주의

현재 코드는 `int(18×0.80)=14`로 잘라 실제 가용공간을 `77.8%`, 즉 `22.2%` 감소시킨다.

- 권장: 소수 저장공간 `14.4 veh`를 허용해 “20% 감소”와 구현을 일치시킨다.
- 대안: 정수 `14 veh`를 유지하면 문구를 “22.2% 감소”로 고친다.
- 사건명은 `L23 일부 공간 점유`로 쓴다. 사고·차로폐쇄로 단정하지 않는다.

## 4. KPI 계산 정본 v2

동결된 필드명 4개는 유지하되 정의와 표시명을 아래처럼 고정한다.

### 4.1 `spillback_time_sec`

**정의:** L12 또는 L23 중 하나 이상이 저장한계에 도달한 회랑 wall-clock 시간.

```text
full_l(t) = vehicles_l(t) >= storage_l - 0.5
spillback_time_sec
  = Σ_t I[full_L12(t) OR full_L23(t)] × DT
```

- 허용범위: `0~3,600초`.
- 두 링크가 동시에 10초 동안 가득 차도 결과는 `10초`다.
- 링크별 노출량은 별도 진단값 `spillback_link_seconds`로 저장할 수 있다.

**P0 결함:** 현재 코드는 링크별 `DT`를 더해 중복합산한다. 3,600초 run에서 `3,885초`가 나오는 결과는 필드 정의상 유효하지 않다.

### 4.2 `recovery_time_sec`

**정의:** 우천 종료 `t=2,700초` 이후 회복조건이 **연속 60초** 유지되기 시작한 최초 시각까지의 시간.

```text
calm(t)
  = occ_L12 < 0.50
    AND occ_L23 < 0.50
    AND every external queue < 5 veh

recovery_time_sec = first_start_of_60s_continuous_calm - 2700
```

- 15분 관측창 안에 회복하지 못하면 `recovery_time_sec=900`과 `recovery_observed=false`를 함께 기록한다.
- 화면에는 `900초 회복`이 아니라 `관측창 15분 내 미회복`으로 표시한다.

**P0 결함:** 현재 코드는 한 시점만 calm이어도 회복으로 판정하고, 미회복과 정확히 900초 회복을 구분하지 않는다.

### 4.3 `total_travel_time_sec`

**정의:** 동일 관측창에서 모든 정책 영향 차량이 모형 안에서 보낸 누적 vehicle-seconds.

```text
N_system(t)
  = external queues + L12 + L23 + BYPASS

total_travel_time_sec
  = Σ_t N_system(t) × DT
    + unmodeled_bypass_freeflow_seconds
```

- 화면명은 `총 통행시간`보다 `모형 내 누적 체류시간`이 정확하다.
- 동일 시나리오·seed·수요·관측창끼리만 비교한다.
- 우회가 활성화되면 우회차량의 BYPASS 대기와 추가 자유주행시간을 포함해야 한다.

**P0 결함:** 현재 코드는 gating이 R1_N 차량을 BYPASS로 돌리지만 headline `total_travel_time_sec`에서 BYPASS 체류와 60초 추가 자유주행시간을 제외한다. 따라서 최신 fixture의 `−76.1%`는 정책 간 공정한 총시간 비교로 승인할 수 없다.

### 4.4 `worst_approach_delay_sec`

현재 집계형 큐 모델은 개별 차량 대기시간을 추적하지 않는다. v2에서는 다음 proxy로만 사용한다.

```text
clearance_proxy_a(t)
  = queue_a(t) / effective_service_a(t) × DT

approach_p95_proxy_a = P95_t(clearance_proxy_a(t))
worst_approach_delay_sec = max_a(approach_p95_proxy_a)
```

- `effective_service`는 강우, meter, 하류 저장공간 제약을 반영해야 한다.
- 화면명: `최악 진입로 P95 대기 proxy`.
- 실제 P95 차량지체라고 주장하려면 FIFO cohort 또는 차량별 도착·서비스 시각이 필요하다.

**P0 결함:** 현재 코드는 `cap×0.5` 상수를 써서 실제 meter와 하류 제약을 충분히 반영하지 않는다.

### 4.5 보조 지표

| 필드 | 처리 |
|---|---|
| `completed_trips` | 정책별 유입·우회·미완료 차량과 함께 보고 |
| `diversion_delay_sec` | baseline 대비 증분을 검사. 평균만으로 전가 피해를 숨기지 않음 |
| `hard_brakes` | `급제동 대리지표` 또는 `차단 진입 proxy`로만 표시 |
| TTC/PET | 현재 미계산. 명칭·위반코드·발표에서 사용 금지 |
| `recovery_observed` | 스키마에 추가 필요 |
| `result_source` | `live_simulation` 또는 `fixture` 필수 |

## 5. 공정성·안전 규칙 v2

### 5.1 비교쌍 고정

공정성 비교는 아래가 모두 같은 `no_action` 기준선과 candidate 사이에서만 한다.

```text
scenario_id
seed
git_commit_sha
parameter_set_version
kpi_definition_version
guard_version
network_version
duration_sec
```

### 5.2 진입로별 비악화 규칙

```text
worsen_pct_a
  = 100 × (candidate_p95_a - baseline_p95_a)
          / max(baseline_p95_a, 30 sec)

reject if any approach has worsen_pct_a > 15
```

- 평균값으로 특정 진입로의 피해를 상쇄하지 않는다.
- 모든 외부 진입로를 각각 검사한다.
- baseline 또는 candidate의 진입로 값이 누락되면 통과가 아니라 `invalid`다.
- `15%`와 `30초`는 공공 운영기준이 아닌 내부 provisional harm budget이다.

**P0 결함:** 현재 식은 분자를 `candidate - max(baseline,30)`으로 계산한다. 올바른 분자는 `candidate - baseline`이다.

### 5.3 우회 전가 공정성

- candidate와 baseline의 `diversion_delay_sec` 차이가 `180초`를 넘으면 거절한다.
- `180초`는 내부 provisional 한도다.
- 우회된 차량을 headline TTT에서 빼지 않는다.
- 우회량, 우회 완료량, 미완료량, 평균·P95 우회지체를 함께 남긴다.

### 5.4 안전·데이터 가드

| 규칙 | v2 처리 |
|---|---|
| candidate `hard_brake_proxy`가 baseline보다 증가 | 거절 가능. 단 TTC/PET 악화라고 부르지 않음 |
| `sensor_available=false` 또는 `data_age_sec>120` | 향후 현장모드에서 적용 차단·관찰모드 |
| `device_status=fault` | 적용 차단·기본상태 유지 |
| fixture가 `data_age_sec=0`, `device_status=ok` | 합성 입력 상태일 뿐 실제 센서·제어기 정상 증거가 아님 |
| 가드 실패 정책 승인 | 서버와 화면 모두 거절 |
| 사람 승인 없음 | 실제 적용 상태로 전환 금지 |

## 6. 대표 결과 공개 게이트

다음 조건이 모두 충족되기 전에는 단일 개선율을 대표 성과로 사용하지 않는다.

1. P0 KPI·공정성 결함 수정.
2. `parameter_set_version`, `kpi_definition_version`, `guard_version` 고정.
3. 같은 commit에서 live 결과와 fixture 재생성.
4. `dry_base`, A, B 각각 seed `1~10` 실행.
5. 시나리오별 중앙값·P10·P90·가드 실패 seed 수 보고.
6. JSON, README, 화면, 데모 대본, 슬라이드, 부스 문구가 같은 `run_id`를 인용.
7. `provisional=true`, `합성 결과`, `세종 실측 아님`을 인접 표기.

내부 기술 스파이크 통과선 `spillback 30% 감소`, `누적 체류시간 10% 감소`, 공정성 `15%`는 현장 목표나 공공 KPI가 아니다.

현재 `test_spike_pass_criteria_10_seeds`는 A만 seed 1~10으로 검사한다. B는 seed 42의 “spillback 발생”만 확인하므로 A/B 공통 검증 완료로 표시하면 안 된다.

## 7. 현재 수치·문구 사용 판정

| 수치·문구 | 현재 출처 | 판정 | 이유 |
|---|---|---|---|
| `0.87` 15분 내 R1 도달 확률 | `docs/16_DEMO_SCRIPT.md` | **삭제** | 계산 필드·다중 seed·확률모형 없음 |
| `−23% 평균 교차로 대기시간` | 부스/카피 | **삭제** | frozen KPI·run·계산식 없음 |
| `1,240→360초`, `−71%`, `−13.4%` | 과거 대본·구 fixture | **사용 금지** | 최신 fixture와 불일치 |
| `3,885초`, `−100%` | 최신 fixture | **사용 금지** | spillback wall-clock 중복합산 |
| `−76.1% total_travel_time` | 최신 fixture | **사용 금지** | 우회차량 시간 누락 |
| `−90.4% worst delay` | 최신 fixture | **proxy로도 보류** | proxy 서비스율 정의 미수정 |
| `recovery 900초` | 최신 fixture | **표시 수정** | 실제 회복과 미회복 censor 구분 없음 |
| `15% / 30초 / 180초 / 120초` | 가드 상수 | **내부 기준으로만 허용** | 외부 공식기준 아님 |
| `.95/.89/.84` | 문헌 표 재계산 | **근거 기반 provisional로 허용** | 세종 보정값 아님 |
| `1.10/1.18`, `22/18/60`, `.70`, `.80/.35/.45` | 팀 합성 입력 | **가정으로만 허용** | 문헌·현장값 아님 |

## 8. QA 케이스

### 8.1 사실·문구 QA

| ID | 입력·검사 | 기대 결과 |
|---|---|---|
| `FACT-001` | 345, 346, 366이 한 표에 등장 | 각 숫자에 시점·단위·발화주체가 붙고 증감 계산 없음 |
| `FACT-002` | `236÷366` 자동 계산 | 발표 표에는 출력하지 않고 내부 메모에 `[계산]`로만 저장 |
| `FACT-003` | “7월에도 장애가 남아 있다” | `미확인`으로 수정 |
| `FACT-004` | “14개 모두 AI 실시간 제어” | 구축·실증 및 일부 지점·시간대 TOD 문구로 수정 |
| `FACT-005` | “R29이므로 세종 장비 호환” | 자산·시험 매트릭스 미확인으로 거절 |
| `DATA-001` | 전국 실시간 API 설명 발견 | 세종 레코드 표본 호출 전 `사용 가능` 판정 금지 |
| `DATA-002` | VDS가 교통량·속도·점유율을 수집 | 특정 회랑의 주기·보유기간·품질 플래그 보유로 일반화 금지 |

### 8.2 시나리오·KPI 단위 QA

| ID | 입력·검사 | 기대 결과 |
|---|---|---|
| `PAR-001` | heavy factor가 `0.83` | “보수적 가정” 표시 또는 v2 권고 `0.84`로 변경 |
| `PAR-002` | B에서 `int(18×0.8)` | 결과 `14`, 실제 감소 `22.2%`를 검출 |
| `PAR-003` | A/B 수요 `1.10/1.18` | “비로 인한 수요 증가율” 문구를 실패 처리 |
| `KPI-001` | L12·L23이 동시에 10초 full | `spillback_time_sec=10`, `20`이면 실패 |
| `KPI-002` | 3,600초 run | `0≤spillback_time_sec≤3,600` |
| `KPI-003` | calm 55초 후 1 step 위반 | 회복 미판정 |
| `KPI-004` | 15분 내 회복 없음 | `recovery_time_sec=900`, `recovery_observed=false`, 화면은 `미회복` |
| `KPI-005` | gating이 차량을 BYPASS로 전환 | BYPASS 체류·추가 자유주행시간이 TTT에 포함 |
| `KPI-006` | 개별 차량 wait 기록 없음 | 표시명에 `proxy` 필수 |
| `KPI-007` | 실제 meter가 `0.45` | 해당 진입로 effective service에 meter가 반영 |

### 8.3 공정성·안전·재현 QA

| ID | 입력·검사 | 기대 결과 |
|---|---|---|
| `FAIR-001` | baseline `10초`, candidate `20초` | `(20-10)/30=33.3%`, 15% 초과로 거절 |
| `FAIR-002` | 한 진입로만 16% 악화, 나머지 개선 | 평균과 무관하게 거절 |
| `FAIR-003` | candidate의 한 진입로 값 누락 | 통과가 아니라 `invalid` |
| `FAIR-004` | 우회차량 headline TTT 제외 | 실패 |
| `SAFE-001` | hard-brake proxy 증가 | proxy 악화로 기록; `TTC/PET 악화` 문구는 실패 |
| `SAFE-002` | fixture의 `device_status=ok` | 실제 현장 장비 정상 주장 금지 |
| `RUN-001` | 같은 scenario·seed·버전 2회 | 타임라인·KPI·candidate hash 동일 |
| `RUN-002` | seed 1~10 검증 | A와 B 모두 동일 매트릭스 실행 |
| `AUTH-001` | 가드 실패 candidate 승인 요청 | 서버·UI 모두 거절, 상태 불변 |
| `AUTH-002` | 사람 승인 없음 | `TWIN_APPLIED` 또는 실제 적용 표기 금지 |

### 8.4 문서·화면 동기화 QA

| ID | 검사 | 기대 결과 |
|---|---|---|
| `SYNC-001` | `0.87`, `−23%` 전체 검색 | 0건 |
| `SYNC-002` | 구 fixture 수치 `1240`, `360`, `−71`, `−13.4` 전체 검색 | 역사 문서 외 발표 경로 0건 |
| `SYNC-003` | 최신 fixture 수치 인용 | 동일 `run_id`, seed, commit, 버전, `provisional` 인접 표기 |
| `SYNC-004` | README·화면·대본·슬라이드·부스 | KPI 이름·단위·값·source 일치 |
| `SYNC-005` | fallback 실행 | `result_source=fixture`가 화면과 로그에 노출 |

## 9. 외부 확인 Action Plan

### 9.1 요청해야 할 자료

| 우선 | 확인 공백 | 요청 필드·문서 | 확정 기준 |
|---:|---|---|---|
| P0 | 현재 복구 상태 | 기준일, 조사모수, 수리완료, 기능검증완료, 잔여불량, 온라인·부분기능·원격불가 상태 수 | 기관 회신 또는 상태표 |
| P0 | 345·346·366 집계 차이 | 교차로 ID↔제어기 ID 대조, 생활권, 설치·인수일, 관리범위, 집계 기준일 | 비식별 자산 대조표 |
| P0 | 236개 유형 | 판정기준, HW·전원·통신·동기·서버·프로토콜·기타 유형별 수, 중복 여부 | 조사 결과표·점검보고서 |
| P1 | 스마트교차로 14개소 | 위치, 가동상태, 운영시간, TOD/감응/적응/운영자지원 모드, fallback, 마지막 데이터 시각 | 운영현황표 |
| P1 | 후보구간 데이터 | 5/15분 방향별 교통량·속도·점유율·대기행렬, 결측·통신장애 flag, VMS·신호 운영이력, 보유기간 | 데이터사전 + 우천/건조 평일 표본 |
| P1 | 장비 호환성 | 제조사, 모델, 설치연도, 적용 R판, 펌웨어 계열, 통신·부가장치 프로토콜 계열, 연동시험 결과 | 비보안 호환성 매트릭스 |

제어기 IP, 계정, 망 구성, 인증키, 상세 취약점은 요청하지 않는다.

### 9.2 회신 상태값

기관이 전체 답을 주기 어려우면 각 행에 아래 하나만 표시하도록 요청한다.

```text
확인 | 미보유 | 비공개 | 타 기관 소관
```

### 9.3 1차 연락

- 세종 교통정보시스템 안내: `044-300-6664`, `044-300-7937`
- 요청 제목: `[사실확인 요청] 세종 온라인 신호제어기 집계·복구현황·스마트교차로 운영범위`
- 통화 핵심문:

> 세종 AX 해커톤 발표에서 공개자료의 수치를 잘못 섞지 않기 위한 사실확인입니다. 보안정보나 제어기 접속정보는 요청하지 않습니다. 345·346·약 366의 집계기준, 236개 1차 조사 결과의 유형·최근 기준일, 스마트교차로 14개소의 현재 운영모드, 제공 가능한 교통데이터 항목을 담당하는 부서와 이메일을 안내받을 수 있을까요? 전체 답변이 어렵다면 자료 보유 여부와 문서명만 확인해 주셔도 됩니다.

### 9.4 회신 수령 후 처리

1. 원문 파일·메일을 날짜와 발신기관이 보이게 보존한다.
2. 각 답을 `[사실]`, `[공식발언]`, `[미확인]`으로 다시 분류한다.
3. `as_of_date`가 없는 상태 수치는 발표에 반영하지 않는다.
4. 자산 수는 시설단위·생활권·관리범위가 같은 경우에만 비율 계산한다.
5. 인용 허용 여부를 확인하고, 불허 시 내부 검증자료로만 쓴다.
6. GitHub claim register와 Notion 팩트시트를 같은 날 함께 갱신한다.

## 10. 팀 전달용 P0 결정문

> 시나리오 ID와 KPI 필드명은 유지합니다. 강우 용량계수 정본은 `1.00/0.95/0.89/0.84`이며 세종 보정값이 아닌 문헌 기반 provisional 민감도값입니다. 수요·저장공간·capacity drop·정책·가드 임계값은 모두 합성 가정으로 표시합니다. 현재 코드는 spillback 중복합산, 회복 censor 부재, 우회차량의 headline TTT 누락, worst-delay proxy 정의, fairness 분자 계산을 수정해야 합니다. 따라서 과거 대본의 `0.87`, `−71%`, `−13.4%`뿐 아니라 최신 fixture의 `3,885초`, `−100%`, `−76.1%`, `−90.4%`도 대표 성과로 사용하지 않습니다. 수정된 동일 커밋에서 A/B×10 seeds와 fixture·대본·화면 동기화 QA가 끝난 뒤에만 합성 run 결과를 승인합니다.

## 11. 실행 결과 필수 메타데이터

```text
run_id
scenario_id
seed
git_commit_sha
parameter_set_version
kpi_definition_version
guard_version
policy_version
network_version
simulator_version
result_source
provisional
recovery_observed
generated_at
```

권고 버전:

```text
parameter_set_version = rainflow-provisional-v2
kpi_definition_version = rainflow-kpi-v2
guard_version = rainflow-guard-v2
```

## 12. 출처 목록

### 12.1 세종 운영현황·데이터·표준

1. [행복청, 2020년 온라인 신호제어 345개소](https://naacc.go.kr/flexer/doc_view.jsp?file_save=89619B60C2D643ACAF07C40299C26426.hwp&subpath=file%2Freport%2F20200819)
2. [세종시의회, 2025-12-15 346개 교차로 관련 의원 발언](https://council.sejong.go.kr/cms/mntsViewer.do?mntsId=6667)
3. [세종시의회, 2026-02-03 약 366개·236개 집행부 답변](https://council.sejong.go.kr/cms/mntsMmbrSimpleViewer.do?mntsId=6693&var08=MBR000064)
4. [세종시의회, 2026-07-16 교통신호체계 최적화 업무보고](https://council.sejong.go.kr/cms/mntsViewer.do?mntsId=6785)
5. [정책브리핑, 스마트교차로 14개소·스마트횡단보도 10개소](https://www.korea.kr/multi/visualNewsView.do?newsId=148877347)
6. [대한교통학회, 스마트교차로 선정 지점·시간대 최적 TOD 적용](https://kst.or.kr/bbs/board.php?bo_table=tugo_programbook88&wr_id=97)
7. [세종 교통정보시스템 구성·수집정보](https://bis.sejong.go.kr/web/information/information_system.view)
8. [세종특별자치시 신호등 조회 API](https://www.data.go.kr/data/15098435/openapi.do)
9. [행안부·한국지역정보개발원 전국 실시간 신호정보 API](https://www.data.go.kr/data/15157604/openapi.do)
10. [전국신호등표준데이터](https://www.data.go.kr/data/15028198/standard.do)
11. [한국도로교통공단, 교통신호제어기 표준규격 R29](https://www.koroad.or.kr/main/board/21/89982/board_view.do?bdNoticeYn=N&bdOpenYn=Y&cp=1&listType=list)
12. [한국컴퓨터정보학회, 교통신호제어기 외부장치 호환성 연구](https://journal.kci.go.kr/jksci/archive/articlePdf?artiId=ART003048174)

### 12.2 시나리오·운영전략 근거

13. [Lee et al., 2018, 우천 시 회전교차로 gap acceptance](https://onlinelibrary.wiley.com/doi/10.1155/2018/2726732)
14. [Ibijola et al., 2018, 강우별 회전교차로 진입용량](https://opentransportationjournal.com/VOLUME/12/PAGE/192/FULLTEXT/)
15. [FHWA, Roundabouts: An Informational Guide](https://www.fhwa.dot.gov/publications/research/safety/00067/000678.pdf)
16. [Akçelik, 2005, Roundabout Metering Signals](https://onlinepubs.trb.org/Onlinepubs/circulars/ec083/27_Akcelikpaper.pdf)

### 12.3 팀 정본·현재 구현

17. [Day 1 동결 결정](https://github.com/sodam3156/Make-Sejong-Great-Again/blob/main/docs/15_DAY1_FREEZE_DECISION.md)
18. [Provisional 파라미터](https://github.com/sodam3156/Make-Sejong-Great-Again/blob/main/docs/evidence/provisional_parameters.md)
19. [현재 시뮬레이터](https://github.com/sodam3156/Make-Sejong-Great-Again/blob/main/backend/app/simulation.py)
20. [현재 공정성·안전 가드](https://github.com/sodam3156/Make-Sejong-Great-Again/blob/main/backend/app/safety.py)
21. [현재 fixture](https://github.com/sodam3156/Make-Sejong-Great-Again/blob/main/backend/fixtures/demo_run.json)
22. [현재 데모 대본](https://github.com/sodam3156/Make-Sejong-Great-Again/blob/main/docs/16_DEMO_SCRIPT.md)
23. [현재 스파이크 테스트](https://github.com/sodam3156/Make-Sejong-Great-Again/blob/main/backend/tests/test_spike.py)

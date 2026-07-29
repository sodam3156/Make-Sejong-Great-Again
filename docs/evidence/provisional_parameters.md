# Provisional 수치표 (QA v2 반영)

> **검증 상태 업데이트 — 2026-07-29**
>
> 시우 검증 결과와 발표 사용 게이트는
> [`rainflow_scenario_kpi_qa_validation_20260729.md`](./rainflow_scenario_kpi_qa_validation_20260729.md)를 따른다.
> 이 문서의 현재 구현값이 곧 외부 근거 또는 승인값을 뜻하지 않는다.
> P0 KPI·공정성 결함과 fixture 재동결은 PR #26에서 반영됐다. 그러나 결과는 계속 `synthetic-v0`·`provisional`이며 사람 검토 전에는 세종 실측 성과로 사용할 수 없다.

## 목적

이 문서는 RainFlow Sejong 큐 모델과 fixture에 들어 있는 provisional 파라미터의 단일 출처(single source of truth)다. 아래 표의 모든 값은 `backend/app/simulation.py`, `backend/app/safety.py`, `backend/README.md`, `backend/fixtures/demo_run.json`, `docs/09_RAINFLOW_SEJONG.md`에 존재하는 값을 옮겨 적은 것이며, 이 문서에서 새로 계산하거나 추정한 수치는 없다. `docs/15_DAY1_FREEZE_DECISION.md` 5항 원칙대로 전부 합성 데이터이고 세종시 실측값이 아니다.

## 표1. 시나리오 수치표

출처: `backend/app/simulation.py` `SCENARIOS`, `RAIN_CAPACITY_FACTOR`, `rain_level_at()`

| scenario_id | rain_level (첨두) | 수요 서지 배율(surge) | 사고 여부(incident) | 우천 첨두 용량 배율 | 근거 유형 |
|---|---|---|---|---|---|
| dry_base | dry | 1.00 | false | 1.00 (dry는 배율 적용 없음) | 순수 가정 |
| rain_spillback_a | heavy | 1.10 | false | 0.84 (heavy 배율) | QA v2 문헌 평균 기반 provisional |
| rain_spillback_b | heavy | 1.18 | true | 0.84 (heavy 배율) + L23 가용공간 20% 축소(14.4대) | 문헌 기반 provisional(용량 배율) / 순수 가정(공간·surge) |

보조: 우천 진행 중 단계별 용량 배율은 dry 1.00 / light 0.95 / moderate 0.89 / heavy 0.84이며(`RAIN_CAPACITY_FACTOR`), `rain_level_at()`에 따라 dry_prep_end(900초) 이후 240초 동안 moderate를 거쳐 첨두(peak)로 전환되고 rain_end(2700초) 이후 dry로 복귀한다. 이 계단식 진행 구간 배분(240초) 자체는 순수 가정이다.

## 표2. 운전자·용량 파라미터 매핑

출처: `docs/09_RAINFLOW_SEJONG.md` "초기 민감도"·"1차 근거" 절, `backend/app/simulation.py`

| 파라미터 | 문헌 근거 범위 (docs/09) | 근거 문헌 | 현재 큐 모델 구현 여부 |
|---|---|---|---|
| 임계간격(critical gap) 증가 | 1.08배 ~ 1.13배 | 한국 회전교차로 우천 진입행태 연구, DOI: 10.1155/2018/2726732 | 미구현. 큐 모델은 진입간격을 직접 모델링하지 않고 `APPROACH_CAP × RAIN_CAPACITY_FACTOR`로 뭉뚱그려 용량만 낮춘다 |
| 후속차두(follow-up headway) 증가 | 1.06배 ~ 1.12배 | 강우와 회전교차로 진입행태 연구 (opentransportationjournal.com Vol.12 p.192) | 미구현. 같은 이유로 후속차두를 별도 변수로 두지 않음 |
| 진입용량 저하 | 0.84배 ~ 0.95배 | QA v2 문헌 평균 재계산 | 구현됨. `RAIN_CAPACITY_FACTOR = {"dry": 1.00, "light": 0.95, "moderate": 0.89, "heavy": 0.84}`로 반영 |
| 연결도로 저장공간 및 상류 차단(spillback) 메커니즘 | 정성적 근거만 (수치 범위 없음) | FHWA 연속 회전교차로 분석 (FHWA 000678.pdf) | 구현됨. `LINKS = {"L12": 22, "L23": 18, "BYPASS": 60}` (storage_veh)와 spillback/capacity drop(JAM_OCC=0.95, CAPACITY_DROP=0.70) 로직 |
| 유입계량(metering) 효과·혼잡 전가 | 정성적 근거만 (수치 범위 없음) | 회전교차로 미터링 연구 (TRB onlinepubs ec083 27_Akcelikpaper.pdf) | 구현됨(정책 비교용). `fixed_metering` 정책이 `R2_S`, `R1_W` 유입을 0.45로 고정 감축. 이 0.45 값 자체는 문헌에서 가져온 수치가 아니라 "공정성 가드 교육용 위반 사례 재현" 목적의 순수 가정(`backend/README.md` 표 명시) |
| SUMO 차량 파라미터(speedFactor, tau, minGap) | SUMO 문서 참조용 | SUMO 도로망/차량 파라미터 문서 | 미구현. docs/15에 따라 Day 1~2는 SUMO·TraCI 대신 큐 모델을 정식 경로로 쓰므로 해당 파라미터는 아직 코드에 없음 |

## 표3. 안전·공정성 가드 임계값

출처: `backend/app/safety.py`, `backend/app/simulation.py`

| 가드 코드 | 임계값 | 현재 코드 위치 (파일:상수명) | 시우 검증 필요 |
|---|---|---|---|
| FAIRNESS_P95_EXCEEDED | 진입로 P95 지체 기준 대비 +15% 초과 시 거절 (노이즈 하한 30초 적용) | `backend/app/safety.py:FAIRNESS_P95_LIMIT_PCT`(=15.0), `backend/app/safety.py:P95_NOISE_FLOOR_SEC`(=30.0) | 예 |
| DIVERSION_DELAY_EXCEEDED | 우회도로 전가 지체가 기준 대비 180초 초과 시 거절 | `backend/app/safety.py:DIVERSION_DELAY_LIMIT_SEC`(=180.0) | 예 |
| HARD_BRAKE_PROXY_DEGRADED | 진입 차단 proxy가 기준선보다 커지면 거절 | `backend/app/safety.py:evaluate_guard()` | QA v2 반영 |
| 회복 판정 기준 | 우천 종료 후 링크 점유율<0.5·모든 외부 큐<5대를 60초 연속 만족 | `backend/app/simulation.py:_advance_recovery_window()` | QA v2 반영, 미회복 censor 별도 표시 |

보조로 함께 검증이 필요한 관련 상수: `backend/app/simulation.py`의 `JAM_OCC`(0.95, 포화 정체 판정), `CAPACITY_DROP`(0.70, capacity drop 배율), `corridor_gating` 정책의 게이팅 임계(하류 점유 0.80 초과 시 상류 유입 비례 감축, 하한 0.35)도 문헌 대조가 되지 않은 순수 가정 값이다(`backend/README.md` 파라미터 근거 표 참조).

## 검증 절차 제안

1. 문헌 대조: docs/09 1차 근거 4건(DOI 10.1155/2018/2726732, opentransportationjournal Vol.12 p.192, FHWA 000678.pdf, TRB ec083 27_Akcelikpaper.pdf)을 원문 확인하여 임계간격 1.08~1.13배, 후속차두 1.06~1.12배, 용량 0.83~0.95배 범위가 실제로 그 문헌에서 도출됐는지, 세종시 회전교차로 기하구조에 그대로 적용 가능한지 확인한다.
2. 민감도 스윕: `RAIN_CAPACITY_FACTOR`의 4단계 값과 게이팅 임계(0.80, 하한 0.35), fixed_metering 배율(0.45)을 문헌 범위 안에서 스윕하며 `backend/tests/test_spike.py`의 스파이크 통과 기준(spillback 30%↓, 모형 내 누적 체류시간 10%↓, 진입로 15% 악화 금지, 재현성)이 유지되는지 확인한다.
3. 가드 임계값(FAIRNESS_P95 15%, DIVERSION_DELAY 180초)과 회복 판정(점유<0.5, 대기<5대) 기준이 세종시 실제 운영 기준이나 관계기관 협의 결과와 부합하는지 별도로 검토한다.
4. 수치를 교체할 때는 `backend/README.md`의 "파라미터 근거" 표와 "검증된 스파이크 결과" 표, `backend/fixtures/demo_run.json`의 provisional 값을 반드시 같은 커밋에서 동기화한다. 세 위치 중 하나만 바뀌면 화면 표기와 백엔드 계약이 어긋난다.

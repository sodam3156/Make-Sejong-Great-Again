# P0 이슈 구현·추적 정합성 점검 — 2026-07-30

## 결론

GitHub 이슈 [#1](https://github.com/sodam3156/Make-Sejong-Great-Again/issues/1), [#2](https://github.com/sodam3156/Make-Sejong-Great-Again/issues/2), [#3](https://github.com/sodam3156/Make-Sejong-Great-Again/issues/3), [#5](https://github.com/sodam3156/Make-Sejong-Great-Again/issues/5), [#6](https://github.com/sodam3156/Make-Sejong-Great-Again/issues/6)은 **닫지 않는다**. 이슈 문구를 그대로 충족하고 자동 테스트로 확인되는 8개 조건만 체크 후보이며, 나머지 19개는 미체크 상태로 유지해 제출 범위 밖 항목과 구현·테스트 보강 항목으로 분리한다.

| 이슈 | 체크 후보 | 전체 | 이슈 상태 |
|---|---:|---:|---|
| #1 Data | 2 | 5 | OPEN 유지 |
| #2 Optimization | 2 | 5 | OPEN 유지 |
| #3 Simulation | 2 | 5 | OPEN 유지 |
| #5 Workflow | 1 | 6 | OPEN 유지 |
| #6 Safety | 1 | 6 | OPEN 유지 |
| 합계 | **8** | **27** | 종결 조건 미충족 |

검증 기준 원격 SHA는 `origin/main`의 `8e9d8242544a4d4ad6b5ef5e4ca74374b89942e7`, 로컬 릴리스 태그 `v0.2.0-day3-rc2`의 코드 SHA는 `15bab0cd08d0a734b169f554f9776611992419d3`이다. 이 문서 작성 시점의 미커밋 파일은 아래 판단의 완료 증거로 사용하지 않았다.

- 최종 Windows ZIP SHA-256:
  `44458b041bf6cbe5b392dd6ec68efb8f0d71088349423eb6b0c5b1668265ad42`
- 전체 릴리스 테스트: `87 passed`, 경고 0건
- 실제 API 게이트: 181.047초, `pass: true`
- fixture 폴백 게이트: 181.125초, `pass: true`

## 조건별 판정

`체크 후보`는 현재 이슈 체크박스에 SHA와 테스트 결과를 붙여 체크할 수 있다는 뜻이다. `미체크`에는 일부 코드가 있더라도 이슈 문구 전체를 충족하지 않거나 직접 테스트가 없는 경우도 포함한다.

| 이슈 | 원문 완료 조건 | 판정 | 코드·테스트 증거 또는 남은 작업 |
|---|---|---|---|
| #1 | Intersection, Observation, SignalPlan 모델 정의 | 미체크 | 제출 정본은 `contracts/rainflow.schema.json`의 RainFlow 결과 계약이다. 세 모델의 독립 정의는 없으며, 5개 신호교차로 모델은 `docs/15_DAY1_FREEZE_DECISION.md`에서 제출 범위 밖 레거시 설계로 분리됐다. |
| #1 | Proposal, Decision, Evaluation 모델 정의 | 미체크 | `PolicyResult`, 규칙 기반 `decision`, 승인 결과는 있으나 원문과 같은 세 독립 모델 계약은 없다. 유지하려면 모델·스키마·왕복 테스트를 별도 작업으로 추가한다. |
| #1 | 예제 JSON 검증 통과 | **체크 후보** | `backend/tests/test_spike.py::test_fixture_matches_contract_schema`, `::test_live_run_matches_contract_schema`가 fixture와 세 live run을 JSON Schema로 검증한다. |
| #1 | 타임존을 Asia/Seoul로 고정 | 미체크 | `backend/app/main.py`와 `backend/app/storage.py`는 UTC+09:00 고정 오프셋을 사용하지만 `Asia/Seoul` 식별자와 직렬화 수용 테스트가 없다. |
| #1 | 데이터 신선도와 장비 상태 필드 포함 | **체크 후보** | `backend/app/domain.py::DataQualityInput`의 `data_age_sec`, `sensor_available`, `device_status`; `backend/tests/test_backend_contract_regressions.py::test_stale_data_or_device_fault_blocks_approval`. |
| #2 | 기준 유지안 포함 3개 이상 후보 | **체크 후보** | `backend/app/policies.py::POLICIES`가 `no_action`, `fixed_metering`, `corridor_gating`을 동결하고, 스키마가 `policies.minItems = 3`을 요구한다. live schema 검증과 `backend/tests/test_decision.py`가 세 후보 결정을 검사한다. |
| #2 | 주기·분할·오프셋 변경폭 제한 | 미체크 | 현재 후보는 신호계획이 아니라 큐 모델 미터링 정책이다. 주기·분할·오프셋 필드와 제한 가드는 제출 범위에 없다. |
| #2 | 평균 지체·최대 대기행렬·정지율 계산 | 미체크 | 동결 KPI는 `spillback_time_sec`, `recovery_time_sec`, `total_travel_time_sec`, `worst_approach_delay_sec`이다. 원문의 세 KPI를 계산하지 않는다. |
| #2 | 보행 평균대기 계산 | 미체크 | 보행 입력·상태·KPI가 없다. |
| #2 | KPI 정의와 단위 테스트 | **체크 후보** | `backend/tests/test_kpi_v2.py`가 spillback 벽시계, 60초 연속 복구, 검열값, 차량초, clearance proxy, 공정성 계산, 버전을 검사한다. |
| #3 | 정상·출퇴근 혼잡·사고 차로폐쇄 시나리오 | 미체크 | 동결 ID는 `dry_base`, `rain_spillback_a`, `rain_spillback_b`이며 `docs/15_DAY1_FREEZE_DECISION.md`는 원문 명칭을 화면 문구로만 사용한다고 명시한다. 계약 변경 또는 이슈 재정의 전에는 체크하지 않는다. |
| #3 | 고정 시드 지원 | **체크 후보** | `backend/app/domain.py::SimulationRequest.seed`, `backend/app/simulation.py::run_simulation`; `backend/tests/test_spike.py::test_reproducibility_same_seed`와 `::test_different_seed_differs`. |
| #3 | 교통량·속도·대기행렬·신호현시 이벤트 생성 | 미체크 | 합성 도착량·대기행렬·점유율은 있으나 속도 및 신호현시 이벤트 계약이 없다. |
| #3 | 센서 결측 또는 통신지연 이벤트 1개 포함 | 미체크 | 결측·지연 입력은 승인 가드에서 처리하지만 시나리오 타임라인 이벤트로 생성하지 않는다. |
| #3 | 같은 입력에서 같은 결과 재현 | **체크 후보** | `backend/tests/test_spike.py::test_reproducibility_same_seed`, `backend/tests/test_decision.py::test_output_is_byte_stable_and_input_order_independent`, 결과 `result_checksum`. |
| #5 | DRAFT → AI_REVIEWED → SAFETY_PASSED → HUMAN_APPROVED 상태 전이 | 미체크 | 현재 상태열은 `CREATED → PREDICTED → AI_REVIEWED → SAFETY_*` 뒤 승인 시 `HUMAN_APPROVED → TWIN_APPLIED → EVALUATED`이다. 원문의 정확한 상태열과 다르므로 이슈 재정의 또는 호환 상태가 필요하다. |
| #5 | 승인·거절·보류와 사유 기록 | 미체크 | 세 동작과 `reason` 저장 코드는 있으나 현재 회귀 테스트는 승인·거절만 직접 검사한다. 보류·사유 저장·재조회 테스트를 추가한 뒤 체크한다. |
| #5 | 데이터·모델·안전규칙 버전 기록 | **체크 후보** | `reproducibility`와 `simulation_created` 감사 이벤트에 dataset/simulator/parameter/KPI/guard/network/policy/rule/scoring 버전을 기록한다. `backend/tests/test_dataset_contract.py::test_default_dataset_metadata_is_recorded`, `backend/tests/test_kpi_v2.py::test_run_declares_v2_parameter_kpi_and_guard_versions`. |
| #5 | 모델 실패 시 기준 TOD 유지 | 미체크 | 외부 모델은 핵심 경로에 없고 `no_action`·cached·fixture 폴백은 있으나 기준 TOD 계약은 없다. 현 제출 계약에 맞춰 이슈를 재정의하거나 TOD 폴백을 별도 구현한다. |
| #5 | 센서 지연 시 섀도 모드 | 미체크 | stale 입력은 적용을 차단하지만 명시적 shadow 상태·동작 계약은 없다. |
| #5 | JSON 로그 내보내기 | 미체크 | `backend/app/storage.py::RunStore`와 `GET /api/audit/{run_id}`가 JSON/JSONL을 제공한다. 다만 감사 이벤트·replay export 내용을 직접 검증하는 테스트를 추가한 뒤 체크한다. |
| #6 | 상충 현시 차단 | 미체크 | 제출 후보에 신호현시 구조가 없어 상충행렬을 검사할 수 없다. |
| #6 | 보행 최소시간 강제 | 미체크 | 보행현시 입력과 최소시간 가드가 없다. |
| #6 | 최소 녹색·황색·전적색 시간 강제 | 미체크 | 신호 시간계획 입력과 해당 경계 가드가 없다. |
| #6 | 오래된 데이터·불량 제어기 상태에서 적용 차단 | **체크 후보** | `backend/app/safety.py::operational_violations`; `backend/tests/test_backend_contract_regressions.py::test_stale_data_or_device_fault_blocks_approval`가 stale/fault 각각 HTTP 409, pending 유지, `no_action` 적용을 확인한다. |
| #6 | 변경폭 초과 시 추가 검토 상태 전환 | 미체크 | 신호계획 변경폭과 추가 검토 상태가 없다. |
| #6 | 위험 후보 100% 차단 테스트 | 미체크 | 공정성·stale·fault·후보 해시 위반은 차단하지만 원문의 모든 위험 유형을 열거한 완전성 테스트가 없다. 신호현시·보행·시간 가드가 추가된 뒤 위험 후보 corpus 전체를 검사해야 한다. |

## 재현한 테스트

Windows Python 3.11 x64 개발 가상환경에서 다음 명령을 실행했다.

```powershell
.\.venv-build\Scripts\python.exe -m pytest -q `
  backend/tests/test_dataset_contract.py `
  backend/tests/test_decision.py `
  backend/tests/test_spike.py `
  backend/tests/test_kpi_v2.py `
  backend/tests/test_backend_contract_regressions.py
```

전체 릴리스 게이트 결과: **87 passed, 경고 0건**. `pytest.ini`가 경고를
오류로 처리하므로 이 결과는 TestClient 경고 제거도 함께 검증한다.

## GitHub 코멘트 공통 문구

아래 문구를 각 이슈의 조건별 표와 함께 게시할 수 있다.

> 구현 상태와 체크리스트를 조건 단위로 다시 대조했습니다. 검증 기준 원격 main은 `8e9d824`, 로컬 릴리스 태그 `v0.2.0-day3-rc2`는 `15bab0cd08d0a734b169f554f9776611992419d3`이며 전체 회귀 테스트 87건이 경고 없이 통과했습니다. 위 표의 **체크 후보**만 SHA·테스트 증거와 함께 체크하고, 나머지는 미체크로 유지해 제출 범위 밖 항목과 구현/테스트 보강 항목으로 분리합니다. 이 코멘트는 이슈 종결 요청이 아닙니다.

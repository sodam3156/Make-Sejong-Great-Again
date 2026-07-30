# RainFlow Sejong 백엔드

실제 세종 표준노드링크의 성금교차로→청사교차로→세종교차로 절재로 연결 관계를 화면에 제공하고, 그 위의 합성 큐 모델로 우천 spillback을 재현해 3개 정책을 같은 시드로 비교한 뒤 안전·공정성 가드와 운영자 승인을 거치는 FastAPI 백엔드다.

이슈 [#9](https://github.com/sodam3156/Make-Sejong-Great-Again/issues/9) 스파이크의 Day 1 폴백 경로 구현이다. `docs/15_DAY1_FREEZE_DECISION.md` 결정에 따라 SUMO·TraCI 대신 큐 모델을 정식 경로로 사용한다.

## 실행법

```bash
pip install fastapi uvicorn pytest httpx jsonschema
uvicorn backend.app.main:app --port 8000     # 저장소 루트에서 실행
```

- `GET /api/health` 상태 확인
- `POST /api/simulations` body `{"scenario_id": "rain_spillback_a", "seed": 42}` → 3정책 비교 실행
  - 선택 입력 `data_quality`로 데이터 경과시간·센서·장비 상태를 전달한다
  - 검증용 `force_source`는 `auto`, `live_simulation`, `cached_simulation`, `fixture` 중 하나다
- `GET /api/simulations/{run_id}` 계약(contracts/rainflow.schema.json) 형식 결과
- `POST /api/approvals` body `{"run_id": ..., "policy_id": "corridor_gating", "decision": "approve"}`
  - 승인 직전 후보 해시·규칙 버전·데이터 신선도·장비 상태·가드를 다시 검사한다
  - 가드 위반 후보 승인 시도는 409로 거부되고 사유가 감사 로그에 남는다
- 감사 로그: `backend/logs/audit.jsonl`
- 완결 재생 파일: `backend/logs/runs/{run_id}.json`
- 진단용 조회: `GET /api/audit/{run_id}`, `GET /api/scenarios`
- `frontend/`가 있으면 같은 서버가 정적 제공한다

테스트 (스파이크·계약·승인 재검증·폴백·재생 포함):

```bash
python -m pytest backend/tests -q
```

동결 fixture, 프론트 사본, 캐시와 OpenAPI를 같은 계산 결과에서 다시 만들고 확인한다.

```bash
python scripts/generate_contract_artifacts.py
python scripts/generate_contract_artifacts.py --check
```

## 파라미터 근거

전부 합성 provisional 값이다. 실제 세종시 실측이 아니다. 시우 검증 후 교체한다.

| 파라미터 | 값 | 근거 |
|---|---|---|
| 강우 용량 배율 | dry 1.00 / light 0.95 / moderate 0.89 / heavy 0.84 | QA v2 문헌 평균 기반 provisional 민감도 |
| 링크 저장공간 | 성금–청사 22대, 청사–세종 18대 | 실제 링크 길이가 아닌 합성 큐 모델의 저장공간 가정 |
| capacity drop | 포화 정체(occ≥0.95) 링크 선두 배출 ×0.70 | stop-and-go 방출 손실. spillback이 상류 처리량을 깎는 핵심 메커니즘 |
| 게이팅 임계 | 하류 점유 0.80 초과 시 상류 유입 비례 감축 (하한 0.35) | 저장공간 초과 전 선제 조절 |
| 고정 미터링 | 우천 중 부진입로(R1_W, R2_S) 유입 ×0.45 고정 | 공정성 가드 교육용 위반 사례 재현 |
| 공정성 한도 | 진입로 P95 지체 +15% | 이슈 #9 가드 기준 |
| 시드 재현 | `random.Random(f"{scenario_id}:{seed}")` | 동일 입력·시드 → 동일 결과 |

## QA v2 동결 결과 (seed 42, rain_spillback_a)

정본 source run `{{SOURCE_RUN_ID}}`, checksum `{{RESULT_CHECKSUM}}`, `provisional=true`. 화면의 지명·링크 관계는 2026-07-16 세종 표준노드링크(8,768노드·11,893링크) 참조이며, 아래 값은 이 합성 run에만 해당하고 세종 실측 성과가 아니다.

| 정책 | 회랑 spillback wall-clock | 모형 내 누적 체류시간 | 가드 |
|---|---|---|---|
| no_action | {{NO_ACTION_SPILLBACK}}초 | {{NO_ACTION_TTT}} vehicle-seconds | 기준선 |
| fixed_metering | {{FIXED_SPILLBACK_DELTA}}% | {{FIXED_TTT_DELTA}}% | **탈락** (성금교차로 서측·청사교차로 남측 P95 대기 proxy 내부 한도 초과) |
| corridor_gating | {{GATING_SPILLBACK_DELTA}}% | {{GATING_TTT_DELTA}}% | 통과 |

통과 기준(spillback 30%↓, 누적 체류시간 10%↓, 진입로 15% 악화 금지, 재현성)은 `backend/tests/test_spike.py`가 A/B 각각 seed 1~10에서 자동 검증한다.

## 한계

- SUMO·TraCI 미사용. 큐 모델은 차로 변경, 기하구조, 신호 상세를 표현하지 않는다. 안전 지표는 진입 차단 이벤트 기반 proxy이며 실제 차량 궤적 안전지표가 아니다.
- 회복 판정 상한이 우천 후 900초라 무대응 시나리오는 "관측창 내 회복 실패"로 기록된다.
- 실행 결과는 오프라인 JSON 재생 파일로 영속화한다. 다중 사용자 운영을 위한 SQLite 저장소는 제출 범위 밖이다.
- 수요·용량 수치는 합성이며 실측 보정 전이다. 개선율은 프로토타입 내부 비교값이지 실도로 성과 주장이 아니다.

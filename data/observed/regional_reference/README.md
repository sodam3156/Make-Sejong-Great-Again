# Regional reference package

이 디렉터리는 세종 성금–청사–세종교차로의 공식 시간대별 교통·신호·기하자료가 도착하기 전에 사용할 수 있는 **지역 참조자료와 외부도시 기능검증자료**를 보관합니다.

## 현재 산출물

- 천안 72개 교차로·243개 접근로·30일 관측에서 평일/주말 24시간 수요 프로파일
- 접근로 수, 방향 편중, 첨두 집중, 교통량을 이용한 천안 유사 교차로 1차 후보 10개
- KICT 좌표 3,983개 중 세종 관측지점 기준 인접 상시조사지점과 국도·고속국도 시간 프로파일
- KICT 차종 12분류 구성비
- 제주 직진·좌·우·유턴 및 차종 7분류 adapter 요약
- 인천 운영코드·시간대별 신호주기 parser 요약
- UTIC 예약계획 응답 계약 parser, 온라인 프로브 상태 endpoint, 비민감 fixture 생성 도구

## 자료 역할

| 분류 | 자료 | 허용 용도 | 금지 용도 |
|---|---|---|---|
| `regional_reference` | 천안 | 시간대 형상, 첨두시간, 유사 교차로 선별 | 세종 절대수요·회전비 보정 |
| `regional_reference` | KICT 인접 조사점 | 인접도로 시간대 분포와 차종범위 | 교차로 회전교통량으로 사용 |
| `external_fixture` | 제주 | movement/vehicle adapter와 시각화 검증 | 세종 교통량으로 대입 |
| `external_fixture` | 인천 | 주기·TOD parser와 화면 검증 | 세종 실제 신호계획으로 표시 |
| `external_live_fixture` | UTIC 대구 예약계획 | 응답 계약, 온라인 경로, 폴백 기능 검증 | 세종 신호계획·실시간 현시·모델 보정 |

모든 참조 파일은 `runtime_activation=disabled`이며 `usable_for_calibration=false`입니다. 현재 `synthetic-v0`의 `BASE_DEMAND`, 용량, 저장공간, 공정성·안전·제어 임계값은 변경하지 않습니다.

## 읽기 전용 API

```bash
uvicorn backend.reference_api:app --host 127.0.0.1 --port 8011
```

UTIC 응답 계약과 온라인 프로브 상태:

```text
GET /api/reference/utic-reservation-contract
```

이 endpoint는 자격증명이나 원시 응답 행을 반환하지 않습니다. 필요한 필드, 프로브 성공 여부, QA 규칙과 사용 한계만 제공합니다.

## UTIC 응답을 안전하게 fixture로 만드는 방법

PowerShell 전체 기록이나 요청 URL을 저장하지 말고 **JSON 응답 본문만** 파일로 저장합니다. 그다음:

```bash
python scripts/sanitize_utic_reservation_response.py \
  /path/to/utic_response_body.json \
  /path/to/utic_reservation_normalized.json
```

도구는 요청 URL·환경변수·인증 헤더 흔적이 포함된 입력을 거절하고, `backend/app/utic_signal.py`의 canonical 계약으로 정규화합니다. 생성물은 별도 QA와 SHA-256 기록 후에만 fixture 후보로 추가합니다.

## QA

```bash
python scripts/validate_regional_reference_package.py
python -m pytest backend/tests/test_regional_reference_package.py -q
python -m pytest backend/tests/test_utic_signal_adapter.py -q
```

주요 검사:

- 천안 일합계와 24개 시간값의 합 일치
- 평일·주말 24시간 정규화 비중 합계 1
- 미해결 천안 명칭 3건을 임의 매핑하지 않고 보존
- KICT 인접지점 거리 정렬과 차종비 정규화
- 제주 이동·차종 스키마 수 및 교차로 집합 일치
- 인천 신호주기 숫자 변환과 운영코드 0~5 보존
- UTIC 비정상 응답·필수 필드 누락 거절
- UTIC 예약제어 코드 `0`을 임의 해석하지 않고 QA 플래그로 보존
- 외부자료의 런타임 활성화 및 세종 보정 승격 차단

## 새 자료가 도착했을 때

원본을 덮어쓰지 말고 먼저 manifest에 등록합니다.

```bash
python scripts/register_regional_reference_update.py register-source \
  --manifest data/observed/regional_reference/regional_reference_manifest.json \
  --file /path/to/original.csv \
  --source-id sejong_turning_counts_202607 \
  --source-class observed \
  --region Sejong \
  --received-at 2026-07-31
```

정규화된 관측자료는 `backend_handoff.json`의 네 replacement slot 중 하나로 staging합니다.

1. `sejong_corridor_geometry`
2. `sejong_time_resolved_turning_counts`
3. `sejong_signal_plan`
4. `live_signal_snapshot`

```bash
python scripts/register_regional_reference_update.py attach-slot \
  --handoff data/observed/regional_reference/backend_handoff.json \
  --slot sejong_signal_plan \
  --input /path/to/canonical_signal_plan.json
```

이 명령은 필수 필드를 검사하고 `received_pending_qa`로만 기록합니다. 실제 시뮬레이터 활성화는 모델팀 검토와 독립 승인을 포함한 별도 PR에서 수행해야 합니다.

## 원자료 보존

대형 XLSX와 HWP는 Git에 복제하지 않습니다. `regional_reference_manifest.json`에 원본 파일명·바이트 크기·SHA-256을 기록해 수령자료와 파생자료의 연결을 보존합니다. 외부 API 응답은 자격증명과 요청 로그를 제외한 JSON 본문만 로컬에 보존하고, sanitizer를 거친 파생자료만 fixture 후보로 취급합니다.

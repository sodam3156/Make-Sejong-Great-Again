# 실제 자료 기반 참조 런타임 산출물

## 목적

현재 확보된 천안 스마트교차로 30일 관측과 KICT 인접도로 시간대별 자료를 단순 보관하지 않고, 프론트·백엔드가 즉시 조회할 수 있는 24시간 스케줄과 유사 교차로 후보로 제공합니다.

이 산출물은 외부지역 관측자료에서 직접 계산되며 임의 수요곡선을 새로 만들지 않습니다. 다만 세종의 절대 교통량이나 실제 신호운영을 보정하지 않으며 런타임 자동 활성화는 차단합니다.

## 1. 24시간 수요 배율 스케줄

`GET /api/reference/traffic-reference-schedule`

요청 예시:

```text
/api/reference/traffic-reference-schedule?source=cheonan&day_type=weekday
```

지원 자료:

- `cheonan`: 천안 72개 스마트교차로·243개 접근로·2026-07-01~07-30
- `kict_national_road`: 세종 인접 일반국도 상시조사 참조
- `kict_expressway`: 세종 인접 고속국도 상시조사 참조
- `weekday`, `weekend`

응답의 `demandMultiplier`는 해당 24시간 프로파일의 일평균을 1.0으로 둔 상대 배율입니다. 24개 배율의 평균은 1.0이며, `p25Multiplier`와 `p75Multiplier`는 원자료 분포 범위를 전달합니다.

직접 사용 가능 범위:

- 시간대 그래프와 KPI 설명
- 데모 재생속도·혼잡강도 시각화
- 별도 검토를 거친 시간형상 adapter 입력
- 천안·일반국도·고속국도 평일/주말 패턴 비교

금지 범위:

- 세종 `BASE_DEMAND` 절대값 자동 변경
- 세종 회전교통량 보정
- 동일 날짜 현장 재현 주장
- 런타임 자동 활성화

## 2. 유사 교차로 1차 후보

`GET /api/reference/similar-intersections`

요청 예시:

```text
/api/reference/similar-intersections?limit=5&min_daily_volume=70000
```

응답 필드:

- 후보 순위와 교차로명
- 접근로 수
- 일 중앙 교통량
- 최대 접근로 비중
- 오전·오후 첨두시각
- 좌표
- 1차 유사도 점수

이 목록은 천안 실제 관측자료에서 접근로 수·교통량·방향 편중·첨두시간을 이용해 선별했습니다. 교차로 간격, 신호 연동, 차로군, 회랑 위상은 아직 검증하지 않았으므로 `topology not verified`가 유지됩니다.

## 3. 호출

```bash
uvicorn backend.reference_api:app --host 127.0.0.1 --port 8011
```

조회:

```text
GET http://127.0.0.1:8011/api/reference/traffic-reference-schedule?source=cheonan&day_type=weekday
GET http://127.0.0.1:8011/api/reference/similar-intersections?limit=10
```

두 경로는 GET 전용이며 모든 응답에 다음 경계가 포함됩니다.

```json
{
  "usableForCalibration": false,
  "runtimeActivation": "disabled"
}
```

## 4. 추가 세종자료 수령 후

세종 시간대별 회전교통량이 도착하면 기존 endpoint를 덮어쓰지 않고 `sejong_time_resolved_turning_counts` replacement slot에 staging합니다. 검증 완료 전에는 천안·KICT 참조 스케줄과 세종 관측 스케줄을 별도 source로 동시에 유지합니다.

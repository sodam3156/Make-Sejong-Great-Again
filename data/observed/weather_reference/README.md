# 세종 회랑 기상 기준자료

- 생성 경로: `.github/workflows/weather-reference-probe.yml`
- 생성 스크립트: `scripts/fetch_weather_reference.py`
- 대상 좌표: 기상청 세종 지점 239 좌표 `36.48522, 127.24438`
- 분석 기준일: 우천 `2022-08-10`
- 비교 탐색범위: `2022-07-13~2022-09-07` (`±28일`)

## 파일

```text
weather_reference/
├─ proxy/
│  ├─ open_meteo_era5_sejong_20220712_20220907.json
│  ├─ weather_hourly_proxy_20220712_20220907.csv
│  └─ weather_daily_proxy_20220712_20220907.csv
├─ processed/
│  └─ dry_candidate_screening.csv
├─ weather_source_manifest.json
└─ README.md
```

## 자료 등급

이 폴더의 현재 수치자료는 **Open-Meteo를 통해 받은 ERA5 재분석 proxy**다. 기상청 세종 239 관측자료가 아니다.

허용 용도:

- KMA 원자료를 조회할 우천·건조 후보일 선별
- 강우 강도 민감도 범위 검토
- 데이터 파이프라인과 결측 검증 시험

금지 용도:

- “세종 지점 239 관측값”으로 표시
- 대상 교차로의 실측 강수량으로 표시
- 현장 보정 완료 또는 실제 개선율 산정에 사용
- KMA 일·시간·분 관측자료를 대체

## 현재 선별 결과

- `2022-08-10` ERA5 proxy 일강수량: `36.7 mm`
- 같은 날 ERA5 proxy 최대 시간강수량: `2.8 mm`
- 같은 달 수요일 후보 `08-03`, `08-17`, `08-24`, `08-31`: 모두 proxy 건조 조건 탈락
- 1순위 proxy 건조 후보: `2022-07-27` 수요일
  - 일강수량 `0.0 mm`
  - 시작 전 6시간 강수량 `0.0 mm`
  - 우천일과 14일 차이

`2022-07-27`은 **KMA 원자료 조회 우선 후보**일 뿐 최종 건조 대조일이 아니다.

## 품질검사

스크립트는 다음 조건을 만족하지 않으면 실패한다.

- 예상 시간·일 행 수 일치
- 강수량 `null` 0건
- 모든 강수량 필드 숫자형
- 시간자료 합과 일자료 합의 최대 차이 `0.11 mm` 이하

최초 시험에서는 강수 변수를 제공하지 않는 ERA5-Land 응답의 `null`을 `0.0`으로 바꾸는 오류가 발견됐다. 해당 결과는 폐기했고, 현재 스크립트는 ERA5를 명시하며 `null`을 발견하면 즉시 실패한다.

## 재현

```bash
python scripts/fetch_weather_reference.py --output-dir weather_reference_output
```

기상청 API허브 인증키가 저장소 Actions secret `KMA_API_AUTH_KEY`로 설정되면 공식 ASOS 시간자료도 별도 `observed/` 경로로 내려받는다. 인증키를 코드·문서·로그에 직접 기록하지 않는다.

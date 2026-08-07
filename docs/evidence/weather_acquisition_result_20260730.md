# 세종 회랑 기상자료 획득·검증 결과

- 담당: 시우 역할 범위(근거·KPI·팩트체크·QA)
- 공식 관측 반영일: 2026-07-31 KST
- 대상 PR: #41
- 기준지점: 기상청 세종 지점 `239`
- 상태: **KMA ASOS·AWS 관측 검증 및 5분·15분 날씨 입력 생성 완료**

## 공식 관측 결과

### 우천일 `2022-08-10`

- AWS 1분자료 `1,440`행, 누락 `0`
- ASOS 시간자료 `24`행
- AWS·ASOS 일강수량 모두 `139.3 mm` — 차이 `0.0 mm`
- 첫 양의 1분 강수 `01:58 KST`, 마지막 `21:31 KST`
- 최대 1분 증가량 `2.4 mm`
- 최대 15분 이동누적 `17.0 mm` (`20:09 KST` 표출)
- 최대 60분 이동누적 `32.9 mm` (`20:46 KST` 표출)
- 최대 ASOS 시간강수량 `29.2 mm` (`21:00 KST`)
- 정각 기준 5분 구간 최대 `9.3 mm`, 15분 구간 최대 `14.4 mm` (`20:00` 시작)

### 건조 대조일 `2022-07-27`

- AWS 1분자료 `1,440`행, 누락 `0`
- 강수감지 및 15분·60분·일 누적 필드 전 행 `0.0`
- 분석 시작이 `06:00 KST` 이후이면 직전 6시간도 같은 하루 자료 안에서 검증 가능
- `06:00 KST` 이전 분석에는 2022-07-26 자료가 추가로 필요

따라서 건조 대조일은 **분석 시작 06:00 이후 조건부 확정**이다.

## 저장·재현

```text
data/observed/weather_reference/
├─ observed/normalized/kma_aws_239_precipitation_compact.json
├─ observed/normalized/kma_asos_239_20220810_hourly.csv
├─ observed/kma_observation_manifest.json
├─ processed/dry_candidate_screening.csv
└─ weather_source_manifest.json
```

원본 API 응답은 로컬에서 검증하고 exact SHA-256을 manifest에 기록했다. 저장소에는 우천일의 1분 증가량 1,440개와 건조일의 1,440분 무강수 run-length 메타데이터만 최소화해 커밋한다. `scripts/ingest_kma_weather_observations.py`가 이를 재검증하고 Actions artifact로 5분·15분 입력 CSV.gz를 생성한다.

## ERA5와의 구분

ERA5 proxy의 2022-08-10 일강수량은 `36.7 mm`, 세종 239 KMA 관측은 `139.3 mm`다. ERA5는 후보 선별·민감도 참고용으로만 유지한다.

## 모델 반영 한계

이번 변경은 날씨 시계열 입력만 확정한다. 교통용량 감소계수, 접근로 수요, 신호 서비스율, 공정성·안전 임계값은 변경·승인하지 않는다. 동일 날짜 시간대별 교통자료와 별도 검토 없이는 강우–교통 반응 파라미터를 보정할 수 없다.

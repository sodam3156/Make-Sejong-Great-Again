# RainFlow 파라미터 근거 레지스트리·인계 규격

- 기준일: 2026-07-31 KST
- 담당 범위: 근거·KPI·팩트체크·QA
- 목적: 현재 코드값, 관측 근거, 후보 매핑, 미확보 입력과 승인 상태를 한 파일에서 기계적으로 검사
- 비목적: 모델 수치의 독립 승인 또는 실제 운영값 확정

## 1. 핵심 원칙

`data/governance/parameter_evidence_registry.json`은 다음 네 층을 분리한다.

1. **관측자료**: KMA 강우 시계열처럼 실제 측정된 값
2. **관측 파생 후보**: 월간 교통량에서 계산했지만 방향 의미와 모델 매핑 검토가 남은 값
3. **전이 provisional 값**: 외부 문헌 범위를 합성 큐 모델에 옮긴 우천 용량 배율
4. **순수 합성 provisional 값**: 수요, 접근용량, 저장공간, 서지, 사고, 정책 및 가드 임계값

관측자료가 존재한다는 사실과 해당 자료로 교통 파라미터를 보정할 수 있다는 주장은 별개다. 특히 KMA 강수량만으로 `RAIN_CAPACITY_FACTOR`를 확정하지 않는다.

## 2. 현재 런타임 상태

기본 데이터셋은 계속 `synthetic-v0`이며, 다음 값은 코드에서 실행되지만 모두 합성 데모 또는 전이 provisional 값이다.

- `BASE_DEMAND`
- `APPROACH_CAP`
- `LINKS` 저장공간
- `RAIN_CAPACITY_FACTOR`
- `JAM_OCC`, `CAPACITY_DROP`
- 시나리오 서지·사고 배율
- fixed metering·corridor gating 수치
- 공정성·우회지체·데이터 신선도 가드
- 회복 판정 기준

이 레지스트리 PR은 위 값을 바꾸지 않는다. 코드값과 레지스트리 값이 다르면 검증이 실패한다.

## 3. 관측자료 인계 상태

### KMA 세종 239 강우

- 분류: `observed`
- 허용: 날씨 시계열 입력 및 출처 QA
- 금지: 동일 시각 교통량 없이 용량감소계수 산정
- 상태: PR #41 병합 대기

### 월간 방향별 교통량

- 분류: `observed_derived_candidate`
- 후보 매핑: R1_N, R1_W, R2_S, R3_E
- 허용: 방향비중 맥락·민감도 설계
- 금지: `BASE_DEMAND` 대체, 동일 날짜 시간대 보정, R2_N·R3_N 외부수요 매핑
- 상태: PR #42 병합 및 방향 의미 검토 대기

## 4. 현재 명시적 데이터 공백

다음 두 항목은 숫자를 추정해서 채우지 않고 `evidence_gap`으로 기록한다.

- 선택 날짜·시간대의 5분/15분/시간별 절대 교통량
- 실제 신호계획: 주기, 현시, 유효녹색, 소거시간, 옵셋, TOD 계획

추가로 실제 저장공간과 서비스율을 산정하려면 차로 수, 유효 대기길이, 정지선, 방향별 차로운영 및 회전비가 필요하다.

## 5. 승인 규칙

- `observed_derived_candidate`는 런타임 활성화 금지
- `evidence_gap`은 값 입력 및 런타임 활성화 금지
- `approved` 상태에는 독립 검토자의 이름, `approved` 결론, 승인값이 모두 필요
- 미승인 항목의 `approved_value`는 반드시 `null`
- 런타임 provisional 값은 `synthetic-v0`와 `synthetic_demo_only`로 제한
- registry-only PR은 `model_parameter_change_in_this_registry=false`를 유지

## 6. 실행

```bash
python scripts/validate_parameter_evidence_registry.py \
  data/governance/parameter_evidence_registry.json

python -m pytest backend/tests/test_parameter_evidence_registry.py -q
```

검증 통과는 **표기와 인계 경계가 일관됨**을 뜻하며, 수치가 실제 교통 운영에 승인됐다는 뜻이 아니다.

## 7. 다음 전환 조건

실제 파라미터 보정 PR은 다음 순서를 따라야 한다.

1. 같은 날짜·분석시간의 교통량과 강우를 연결
2. 방향·회전 의미와 공간망 링크를 확인
3. 원자료·정규화본·manifest·결측률을 고정
4. 하한·기준·상한과 추정방법을 작성
5. 현재 합성값과 별도 dataset adapter로 구현
6. 독립 검토자가 승인 또는 기각을 기록
7. 승인 전에는 `synthetic-v0`를 기본값으로 유지

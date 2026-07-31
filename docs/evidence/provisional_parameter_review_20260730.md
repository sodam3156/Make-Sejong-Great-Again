# Provisional 파라미터 문헌 대조·민감도 검토 — 2026-07-30

## 판정

현재 큐 모델·안전 가드 값은 **내부 합성 provisional**이다. 이번 검토로
재현 가능한 민감도 스윕과 경계 테스트는 추가했지만, 세종 실측 보정,
독립 검토, 현장 효과 검증 또는 안전 인증을 완료했다고 표시하지 않는다.

증거 JSON의 고정 상태값은 `internal_exploratory_non_independent`다.

## 실행 설계와 무결성

- 릴리스 코드 SHA:
  `45f997bea2ef8ee3274948f5f1bf48d888385e46`
- Git tracked/untracked 상태: clean (`dirty: false`)
- 19개 provisional 파라미터
- nominal 1개 + 각 파라미터 low/high = 39케이스
- `rain_spillback_a`, `rain_spillback_b` × seed 1~10
- 논리 결과 780행, 정책 CSV 2,340행
- 전체 스윕 2회 결과 SHA 일치:
  `0809fbeed2392eef7bb225f6e4fb766b752006e463358a3098dd8799ae92cb56`
- 입력 설계 SHA:
  `f7783fa61c3c5a569f1c3dca1d3183046e82eb0d38c0406ae45bb5d4fb58ad55`
- JSON SHA-256:
  `a2cc224f4e998324ac71ff992f3c5bdb99a5980d8ed72a2f811f636bf6b5ac5e`
- CSV SHA-256:
  `4e8944ed2ed89cf2b6e661561c1886b8fe7b3725d5c762d5b906d7a89cf31e5e`

원시 산출물:

- `parameter_sensitivity_20260730.json`
- `parameter_sensitivity_20260730.csv`
- `parameter_sensitivity_20260730.sha256`

## 주요 민감도 결과

내부 관찰 기준은 corridor gating의 spillback `-30%` 이하, 누적 체류시간
`-10%` 이하, guard 통과다. 이는 현장 수용 기준이 아니다.

| 케이스 | A | B | 해석 |
|---|---|---|---|
| nominal | 10/10 통과, TTT 평균 -77.23% | 10/10 통과, TTT 평균 -69.05% | 내부 기준점 |
| `JAM_OCC=0.85` | 0/10, TTT 평균 -5.13% | 0/10, TTT 평균 -5.30% | 임계값 하나로 TTT 판정이 뒤집힘 |
| A 수요 surge `1.05` | 8/10 | B는 10/10 | 낮은 수요에서 spillback 기준이 seed에 따라 불안정 |
| heavy 용량계수 `0.88` | 회복 관측 10/10 | 회복 관측 7/10 | nominal B의 0/10에서 판정 변화 |
| stale 한도 `60초`, 입력 age `120초` | guard 0/10 | guard 0/10 | 운영 가드가 경계 의도대로 차단 |

선택 범위에서 BYPASS 저장공간, 회복 queue/hold, fairness noise floor,
diversion 한도는 KPI 또는 guard 판정에 영향을 주지 않았다. 특히 현재
시나리오의 corridor diversion은 60초로 고정되어 180초 한도에 도달하지
않는다. 이는 강건성 증거가 아니라 해당 입력·가드가 현재 시나리오에서
비활성 또는 도달 불가능할 가능성을 뜻한다.

## 경계 테스트

`backend/tests/test_provisional_boundaries.py`는 다음 exact/above 경계를
고정한다.

- corridor gating: 점유율 `0.80`에서는 미작동, 바로 위에서 작동,
  점유율 `1.0`에서 하한 `0.35`
- fairness: 정확히 `15%`는 통과, 바로 위는 차단
- diversion: 정확히 `180초`는 통과, 바로 위는 차단
- stale: 정확히 `120초`는 통과, 바로 위는 차단
- hard-brake proxy: baseline과 같으면 통과, 1회 많으면 차단

민감도 원시 산출물은 위 rc1 SHA에서 생성됐다. rc2
`15bab0cd08d0a734b169f554f9776611992419d3`는 안전 문구, 동결 생성기,
TestClient 호환 정책과 증거 수집기를 변경했으며 provisional 수치·임계값은
변경하지 않았다. rc2 전체 Windows Python 3.11 x64 테스트 결과는
`87 passed`, 경고 0건이다.

## 문헌 대조

- [Lee et al., 2018](https://onlinelibrary.wiley.com/doi/full/10.1155/2018/2726732)은
  국내 4개 회전교차로에서 우천 시 critical gap 증가를 보고한다. 우천 영향의
  방향성은 지지하지만 세종 회랑의 용량계수·수요배율을 보정하지는 않는다.
- [Ibijola et al., 2018](https://opentransportationjournal.com/VOLUME/12/PAGE/192/FULLTEXT/)의
  Durban 다차로 회전교차로 Table 5는 강우 강도에 따른 용량 감소를 보인다.
  다른 도시·기하·교통류에 그대로 옮길 수 없으므로 `0.84/0.89`를 세종
  확정값으로 정당화하지 않는다.
- [FHWA Roundabouts: An Informational Guide](https://www.fhwa.dot.gov/publications/research/safety/00067/000678.pdf)는
  95백분위 대기행렬, 저장공간 부족, 상류 잠김 검토의 필요성을 정성적으로
  지지한다. 저장공간 `22/18/60`, `JAM_OCC=0.95`,
  `CAPACITY_DROP=0.70`의 수치 근거는 아니다.
- [Akçelik, 2005](https://onlinepubs.trb.org/Onlinepubs/circulars/ec083/27_Akcelikpaper.pdf)는
  metering의 잠재적 편익, 다른 진입로로의 피해 전가, 저장공간 제약을
  정성적으로 지지한다. 미터링 `0.45`, gating `0.80/0.35`를 보정하지는
  않는다.

## 유지해야 할 표시

수요 `1.10/1.18`, 강우 용량계수, 저장공간 `22/18/60`,
`JAM_OCC=0.95`, `CAPACITY_DROP=0.70`, gating `0.80/0.35`,
미터링 `0.45`, fairness `15%/30초`, diversion `180초`, stale `120초`,
회복 `0.5/<5/60초`, hard-brake proxy는 모두 provisional로 유지한다.

화면·발표에는 다음 한계를 인접 표시한다.

> 실제 세종 실측·공공 안전기준이 아닌 합성 provisional 값이며,
> `JAM_OCC` 변화에서 내부 TTT 기준 통과 여부가 뒤집혔다.

## 독립 검토 상태

독립 검토자 이름, 검토 시각, 승인 또는 기각 서명은 아직 없다. 따라서 이
문서는 재현 가능한 **내부 탐색 검토**이며 독립 검증 완료 증거로 사용할 수
없다. 시우 또는 별도 검토자가 원시 JSON·CSV와 위 한계를 확인하고 승인/기각
결론을 기록하기 전까지 `provisional=true`를 유지한다.

# 기상자료 파이프라인 현재 상태

- 기준 PR: #41
- 기준일: 2026-07-30 KST
- 파이프라인 상태: ERA5 proxy 수집·검증·저장 완료
- 공식 관측 상태: 기상청 세종 239 ASOS 시간·분 자료 미획득

## 성공한 검증

- ERA5 시간자료 1,392행
- 일자료 58행
- 강수값 null 0건
- 시간합과 일합 최대 차이 0.0 mm
- 2022-08-10 우천 proxy와 전후 28일 건조 후보표 생성
- 최초 ERA5-Land null 오판 결과 폐기 및 회귀 방지

## GitHub Actions 상태 해석

`data: store weather reference screening output` 커밋은 workflow가 `GITHUB_TOKEN`으로 생성한 커밋이다. GitHub는 재귀 실행 방지를 위해 Actions가 만든 커밋에서 다른 workflow를 자동 실행하지 않을 수 있다. 따라서 해당 커밋의 `action_required` 표시는 데이터 검증 실패가 아니라 후속 실행 억제 상태다.

이 문서 커밋에서 저장소 `Verify`를 다시 실행해 사람 검토용 PR 상태를 갱신한다.

## 남은 차단요인

- 저장소 secret `KMA_API_AUTH_KEY` 없음
- 기상자료개방포털 1일 단위 분자료 원본과 QC 플래그 없음

이 두 항목이 해결되기 전에는 ERA5 proxy를 세종 관측값 또는 모델 보정값으로 승격하지 않는다.

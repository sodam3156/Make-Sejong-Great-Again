# UTIC 신호개방 데이터 온라인 프로브 — 2026-07-31

## 목적

UTIC 신호개방 데이터가 실제 외부 API 경로에서 응답하는지 확인하고, 저장소에는 자격증명과 원시 터미널 기록을 남기지 않은 채 응답 계약·QA·오프라인 fixture 전환 경로만 고정한다.

## 확인 결과

- 서비스: `PlanCrossRoadInfoService/getPlanCRRSInfo`
- 응답 종류: 교차로 예약계획정보
- 온라인 호출: 성공
- `resultCode`: `0`
- `resultMsg`: `NORMAL_SERVICE`
- 응답 메타데이터: 총 63,890건, 페이지당 100건, 총 639페이지
- 반환 지역코드 표본: `L29` — 대구
- 응답 수집시각 표본: `2026-07-27 10:05:32`

## 실제 구현

- `backend/app/utic_signal.py`
  - 응답 메타데이터와 예약계획 행을 canonical 필드로 정규화
  - 필수 필드 누락과 비정상 서비스 코드를 거절
  - `RESRV_CONTRL_CD=0`을 임의 해석하지 않고 `UNDOCUMENTED_CONTROL_CODE_0` QA 플래그로 보존
  - `usableForCalibration=false`, `runtimeActivation=disabled` 고정
- `scripts/sanitize_utic_reservation_response.py`
  - JSON 응답 본문만 입력받음
  - 요청 URL·환경변수·인증 헤더가 포함된 터미널 기록은 거절
  - 정규화된 비민감 fixture만 생성
- `backend/tests/test_utic_signal_adapter.py`
  - 정상 응답 정규화
  - 코드 0 QA 보존
  - 예약 시간창 판정
  - 서비스 오류·필수 필드 누락 거절

## 사용 범위

허용:

- UTIC 응답 계약 parser 검증
- 실제 온라인 API 경로 성공 증거
- 정제 fixture를 이용한 네트워크 차단 폴백 테스트
- 예약계획 화면·TOD 데이터 adapter 개발

금지:

- 대구 예약계획을 세종 신호계획으로 대체
- 실제 신호 점등상태나 잔여시간이라고 표시
- 세종 수요·용량·저장공간·공정성·안전 임계값 보정
- 자격증명 또는 등록 네트워크 정보를 저장소·로그·문서에 기록

## 남은 후속

1. 교차로 기반정보·현시구성·운영계획·평일/특수일 계획·SIGNALMAP 서비스 경로 확보
2. 로컬에서 원시 JSON 응답 본문을 저장한 뒤 sanitizer 실행
3. 정규화 fixture SHA-256 기록
4. 온라인 응답과 네트워크 차단 fixture를 각각 1회 완주
5. 프론트 화면에서 `external_fixture`, 지역, 수집시각, 한계 문구 표시

이 프로브는 외부 API adapter와 폴백 기능을 실증하지만, 세종 현장 신호운영이나 큐 모델 파라미터의 검증 근거는 아니다.

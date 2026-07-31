# UTIC 신호개방 데이터 adapter 인계

## 구현 범위

- 응답 종류: 교차로 예약계획정보
- 외부 지역: 대구
- 목적: 응답 계약·온라인 경로·오프라인 fixture 폴백 검증
- 런타임 활성화: 비활성
- 세종 보정 사용: 금지

## 백엔드 구성

- `backend/app/utic_signal.py`: 응답 정규화와 QA
- `backend/app/utic_reference.py`: 읽기 전용 계약 endpoint
- `scripts/sanitize_utic_reservation_response.py`: JSON 응답 본문의 비민감 fixture 변환
- `backend/tests/test_utic_signal_adapter.py`: 계약·오류·QA·읽기 전용 회귀검사

## 조회 endpoint

```text
GET /api/reference/utic-reservation-contract
```

반환 내용:

- required source fields
- 온라인 프로브 성공 상태
- 응답 메타데이터
- 코드 0 미정의 QA 규칙
- 허용·금지 사용 범위

자격증명, 등록 네트워크 정보, 원시 응답 행은 반환하지 않는다.

## 프론트 인계

화면에 사용할 수 있는 정보:

- `external_live_fixture` 배지
- 지역 `Daegu`
- 응답 종류 `reservation_plan`
- 온라인 경로 성공 여부
- 수집시각
- `실시간 현시 아님`, `세종 신호계획 아님` 한계문구

## 완료 조건

- 온라인 응답 JSON 본문을 로컬 파일로 저장
- sanitizer 실행
- 비민감 fixture SHA-256 기록
- 네트워크 연결 상태에서 parser 완주
- 네트워크 차단 상태에서 fixture 완주
- 두 경로의 결과 스키마 일치 확인

이 adapter는 실제 외부 API를 툴에서 사용할 수 있게 만드는 기능검증 구성요소이며, 시뮬레이션 파라미터나 세종 실제 신호운영을 승인하지 않는다.

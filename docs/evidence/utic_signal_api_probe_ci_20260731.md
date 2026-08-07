# UTIC adapter CI evidence — 2026-07-31

- PR: #46
- head: `9f8545f375eeb9ab2c882d5c1048126693547a4a`
- GitHub Actions workflow: `Verify`
- run: `30599407780`
- backend tests: success
- generated contract artifact verification: success

검증 대상:

- UTIC 예약계획 응답 canonical 정규화
- 비정상 서비스 응답 거절
- 필수 필드 누락 거절
- 미정의 예약제어 코드 `0` QA 보존
- 읽기 전용 `/api/reference/utic-reservation-contract`
- POST 요청 차단
- `usableForCalibration=false`
- `runtimeActivation=disabled`

이 CI 성공은 adapter 계약과 사용경계의 자동검증 증거이며, 세종 실제 신호운영 또는 모델 파라미터 검증을 의미하지 않는다.

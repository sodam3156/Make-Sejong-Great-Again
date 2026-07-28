# 최영 백엔드·Windows 로컬 검증 기록

검증일은 2026-07-28 KST다. 이 기록은 합성 RainFlow 프로토타입의 기술 검증이며 실제 세종 도로 성과나 현장 안전 인증이 아니다.

## 검증 대상

- 기준 원격 커밋: `main`의 `20de26c`
- 제출 변형안: RainFlow Sejong
- 동결 계약: 시나리오 3종, 정책 3종, KPI 4종, API 4경로
- 백엔드 버전: `0.2.0`
- 시뮬레이터: `rainflow-queue-v1`
- 정책: `rainflow-policy-v1`
- 안전 규칙: `rainflow-safety-v1`
- 순위 규칙: `rainflow-rule-v1`

## 자동 검증

- Linux Python 3.12: `42 passed`
- Windows Python 3.11.9: `42 passed`
- fixture·cached fixture JSON Schema 검증 통과
- fixture·프론트 사본·OpenAPI 생성물 동기화 검사 통과
- 동결 API 4경로의 OpenAPI 응답 모델 확인
- `git diff --check` 통과
- 저장소에서 Notion 토큰·`.env` 노출 없음 확인

## Windows x64 네이티브 빌드

- OS: Windows x64
- Python: 3.11.9
- PyInstaller: 6.21.0, onedir
- 실행본: `release/windows-x64/RainFlowSejong.exe`
- 제출 ZIP: `release/RainFlowSejong-windows-x64.zip`
- ZIP 크기: 13,720,890 bytes
- ZIP SHA256: `52a0d7f49b8c69cfadb62289f4c683276a83407ad2d8c6a4cc5c71214bbe67e7`
- 내부 `SHA256SUMS.txt`: 107개 파일 전부 검증 통과

## 실행 확인

현재 한글과 공백이 포함된 Windows 경로 및 ZIP을 별도 공백 경로에 다시 푼 사본에서 다음을 확인했다.

1. `start.bat` 실행 후 약 6초 안에 브라우저 주소 출력
2. `GET /api/health` → `status=ok`, 캐시와 fixture 준비 상태 정상
3. 정적 HTML과 `demo_run.js` → HTTP 200
4. `rain_spillback_a`와 `rain_spillback_b` 실행 → `live_simulation`, 7개 화면 상태 반환
5. 추천 정책 `corridor_gating` 승인 → `approved`, 최종 상태 `EVALUATED`
6. `start.bat` 재실행 → 같은 정상 서버와 포트 재사용
7. `stop.bat` → 기록된 RainFlow 프로세스만 종료하고 PID·포트 파일 정리
8. Python이 없는 PATH에서도 `RainFlowSejong.exe --check` 통과

## 개발 재현 경로

- `docker compose config --quiet` 통과
- Docker Desktop 데몬이 꺼져 있어 실제 이미지 빌드·컨테이너 실행은 이번 검증에서 수행하지 못했다.

## 남은 외부 검증

- 초기화된 외부 Windows x64 PC 두 대
- 각 PC에서 인터넷 차단 상태로 두 번 연속 실행
- 외부 PC에서 60초 기준, 한글·공백 경로, 재실행, 종료, 로그 보존 확인
- 제출 ZIP·소스·README·발표 수치·영상의 최종 버전 일치 확인

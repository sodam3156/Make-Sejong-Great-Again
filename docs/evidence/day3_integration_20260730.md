# Day 3 실제 연동 3분 완주 증거 — 2026-07-30

## 판정

태그가 고정된 Windows ZIP을 한글·공백 경로에 새로 압축 해제한 뒤,
브라우저 → 로컬 API → 합성 시뮬레이터 → 승인 API → 영속 실행 파일·감사 로그
경로를 1회 완주했다.

| 항목 | 결과 |
|---|---|
| 실행 시각 | 2026-07-30 17:12:03~17:15:01 KST |
| UI 자동재생 | 180.828초, `20/20` |
| 실행 ID | `live-rain_spillback_a-s42-f3727bcd00` |
| 결과 출처 | `live_simulation` |
| 최종 워크플로 | `EVALUATED` |
| 승인 | `corridor_gating`, `approved` |
| 시뮬레이터 | `rainflow-queue-v2` |
| LLM 상태 | `rule_based_fallback`; 알려진 AI 자격증명 환경변수 이름 0개 |
| 브라우저 네트워크 | localhost/127.0.0.1 이외 요청 차단, 허용된 외부 요청 0개 |
| 패키지 프로세스 소켓 | 실행 중 외부 목적지 established 연결 0개 |
| 재실행 | PID `26848`, 포트 `64828` 동일 재사용 |
| 종료 | 프로세스·PID/port 파일 제거, health 응답 불가 |
| 전체 자동 판정 | `pass: true` |

## 릴리스 정렬

- 릴리스 태그: `v0.2.0-day3-rc1`
- 태그 및 ZIP 내부 source commit:
  `45f997bea2ef8ee3274948f5f1bf48d888385e46`
- Windows ZIP SHA-256:
  `5a3bd4759290774837cda4dda6823876ed37d58e0c067eaa283d8622b9c7727b`
- 수치 모델 동결 source commit:
  `20ce47135281f1c93ebf84555ba94dae113c0418`
- 증거 매니페스트 SHA-256:
  `2a1a3d7386ac8c098a6eca5484ed2cc3174a5ec1fb2b4348a759a7d0d65fe4a7`

`RELEASE-METADATA.json`은 실행 코드의 태그 SHA와 수치 모델 동결 SHA를
별도 필드로 기록한다. Git commit SHA와 ZIP SHA-256은 서로 다른 종류의
식별자이므로 같은 문자열이라고 주장하지 않고, 위 메타데이터와 ZIP sidecar로
하나의 릴리스 후보에 결합했다.

## 재현 명령

Windows Python 3.11 x64와 Microsoft Edge를 사용했다. 브라우저 증거
수집기는 외부 호스트 요청을 abort하고 로컬 주소만 허용한다.

```powershell
.\.venv-build\Scripts\python.exe .\scripts\capture_day3_evidence.py `
  --base-url http://127.0.0.1:64828/ `
  --output-dir .\docs\evidence\day3_integration_20260730 `
  --repo . `
  --release-zip .\release\RainFlowSejong-windows-x64.zip `
  --browser-channel msedge `
  --expected-duration-seconds 180
```

실행 후 같은 압축 해제본의 `start.bat`을 다시 호출해 동일 PID·포트를
확인하고, `stop.bat` 이후 health 불통을 확인했다.

## 증거 인덱스

- `day3_integration_20260730/summary.json`: 전체 판정과 실행/모델/ZIP SHA
- `day3_integration_20260730/timeline-transitions.json`: 20개 상태 전환 시각
- `day3_integration_20260730/screenshots/`: 7개 의미 상태, 승인 완료, 최종
  `20/20` 화면
- `day3_integration_20260730/localhost.har`,
  `browser-requests.json`, `browser-responses.json`: 브라우저 HTTP 기록
- `day3_integration_20260730/run.json`, `audit.json`: 최종 API 응답과 감사 조회
- `day3_integration_20260730/packaged-runtime/backend/`: ZIP 실행본이 실제로
  저장한 run JSON과 `simulation_created`/`approval_decided` JSONL
- `day3_integration_20260730/packaged-runtime/logs/`: 패키지 서버 stdout/stderr
- `day3_integration_20260730/packaged-lifecycle.json`: 재실행·종료 판정
- `day3_integration_20260730/packaged-process-network-midrun.json`: 실행 중
  프로세스 소켓 스냅샷
- `day3_integration_20260730/llm-environment.json`: AI 자격증명 변수 이름 검사
- `day3_integration_20260730/SHA256SUMS.txt`: 위 증거 파일 30개의 SHA-256

증거 매니페스트는 해당 폴더에서 다음 명령으로 검증했다.

```bash
sha256sum -c SHA256SUMS.txt
```

결과: 30개 전부 `OK`.

## 주장 한계

- 이 실행은 실제 외부 LLM/API 호출 없이 로컬 규칙 기반 경로만 사용했다.
- 브라우저 요청 차단과 패키지 프로세스의 외부 소켓 0개를 확인했지만,
  물리 네트워크 어댑터를 끈 실행이라고 주장하지 않는다.
- clean Windows x64 외부 PC 2대 × 각 2회 검증은 별도 미완료다.
  `scripts/validate_external_windows.ps1`로만 수집하며, 이 개발 PC 실행으로
  대체하지 않는다.
- 데이터와 효과 수치는 실제 세종 실측이 아닌 provisional 합성값이다.

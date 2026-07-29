# 최영 — Windows 제출 ZIP 런처·스모크 게이트 검증

- 검증 시각: 2026-07-29 19:54 KST
- 누락 확인 기준: GitHub `main@6b9ee349`
- 로컬 구현 기준: `scripts/build_windows.ps1`
- 실행 환경: Windows x64, Windows PowerShell 5.1, Python 3.11.9

## 반영 내용

1. 추적 가능한 `scripts/launcher_assets/`에 필수 런처 5종을 둔다.
2. 빌드마다 `release/windows-x64`를 깨끗하게 다시 만들고 다음 파일을 명시 복사한다.
   - `start.bat`
   - `launch.ps1`
   - `stop.bat`
   - `stop.ps1`
   - `README.txt`
3. 최종 파일이 아닌 후보 ZIP을 만든 뒤 `scripts/smoke_windows_release.ps1`을 반드시 실행한다.
4. 새 한글·공백 임시 경로에서 다음 순서를 검증한다.
   - `start.bat`
   - `GET /api/health`: HTTP 200, `status=ok`
   - `start.bat` 재실행: 동일 PID·포트 재사용
   - `stop.bat`
   - 프로세스 종료, runtime PID·port 삭제, health 응답 종료
5. 모든 검증이 성공한 후보만 최종 ZIP으로 승격하고 `.sha256`을 생성한다.

`-SkipTests`는 백엔드 테스트만 생략하며 이 ZIP 스모크 게이트는 생략하지 않는다.
자동 검증에서는 브라우저와 오류 `pause`를 비활성화하고, 실패 정리는 압축 해제본
`RainFlowSejong.exe`와 실행 경로가 같은 프로세스만 대상으로 한다.
빌드는 선택한 Python 버전과 AMD64/x86_64·64비트 여부를 검증하고, 기존 빌드
가상환경이 다르면 x64 선택자로 다시 만든다. `stop.bat`도 현재 압축 해제 폴더의
실행파일 경로와 정확히 일치하는 기록 PID만 종료한다.

## 실행 결과

```text
42 passed, 1 warning in 1.36s

[1/4] start.bat -> health HTTP 200/status ok
[2/4] restart via start.bat -> same PID/port -> health 200
[3/4] stop.bat -> process and runtime files removed
[4/4] post-stop health endpoint is unavailable
Extracted ZIP smoke passed
```

- ZIP 루트 계약: 필수 8개 항목 8/8
  (`RainFlowSejong.exe`, `_internal/`, 런처 5종, `SHA256SUMS.txt`)
- ZIP 내부 SHA256 항목: 107/107 통과
- 종료 후 `RainFlowSejong` 잔존 프로세스: 0
- 후보 ZIP 잔존: 없음
- 최종 ZIP SHA256:
  `560aba932bbbd32468525fb0fb84f35e636b7a9fac09f0b8ee41d6c29d8c9f81`

빌드 게이트 실패 시 최종 ZIP과 `.sha256`이 존재하지 않는 것도 실패 실행에서 확인했다.

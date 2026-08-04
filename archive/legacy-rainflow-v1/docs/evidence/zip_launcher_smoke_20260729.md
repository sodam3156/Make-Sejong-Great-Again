# ZIP 런처 스모크 테스트 (2026-07-29)

감시 레지스터 C-021(`urgent:windows-release-zip-missing-launcher@6e56397`) 해소 검증.
`docs/RUNBOOK.md` 4절 계약(`start.bat`, `launch.ps1`, `stop.bat`, `stop.ps1`,
`README.txt`가 ZIP 최상위에 있어야 하고, 재실행 시 재사용/무충돌, `stop.bat`은
기록된 PID가 실제 `RainFlowSejong` 프로세스일 때만 종료)을 실제로 만족하는지
`scripts/build_windows.ps1`에 추가한 자동 검증 단계로 확인했다.

## 실행 환경

- 워크트리: `feat/backend` 기반 (`git worktree add ... feat/backend` 후
  `git merge origin/main --no-edit`, fast-forward, 충돌 없음)
- OS: Windows 11 (10.0.26200)
- Python: 3.11.15 (uv 관리 CPython, `.venv-build`에 venv 생성)
- 명령: 저장소 루트에서 `powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1`
- 최종 종료 코드: `0`

## 빌드 단계 결과

| 단계 | 결과 |
|---|---|
| `.venv-build` 생성 + `requirements-build.txt` 설치 | 성공 |
| `pytest backend/tests -q` | 42 passed, 1 warning (starlette httpx 폐기 경고, 무해) |
| `launcher.run_rainflow --check` (소스 self-check) | `{"api_key_required": false, "contract_available": true, "fixture_available": true, "frontend_available": true, "status": "ok"}` |
| `PyInstaller --noconfirm --clean rainflow-sejong.spec` | 성공, `RainFlowSejong.exe` 생성 |
| 패키지 실행파일 self-check (`RainFlowSejong.exe --check`) | 위와 동일한 `status: ok` 응답 |
| `release/windows-x64` 배치 + `SHA256SUMS.txt` 생성 | 성공 |
| `release/RainFlowSejong-windows-x64.zip` 생성 | 성공, 15,950,754 bytes |

`release/windows-x64/` 최종 구성 (RUNBOOK 96~105행 계약과 일치):

```
RainFlowSejong.exe
_internal/
start.bat
launch.ps1
stop.bat
stop.ps1
README.txt
SHA256SUMS.txt
```

ZIP SHA256: `7086edd61046808ccae58689cbb06370ef892057a1aae82a73c841986520747d`

## 자동 ZIP 런처 스모크 테스트 (`scripts/build_windows.ps1` 신규 단계)

ZIP 생성 직후 스크립트가 `%TEMP%\rainflow-launcher-smoke-<timestamp>`에 압축을
해제하고 아래 4단계를 자동 실행한다. 실패 시 스크립트 전체가 `throw`로 non-zero
종료하도록 만들어 깨진 런처가 제출본에 포함될 수 없게 했다.

### [1/4] 최초 `start.bat` 실행

```
사용 포트: 57685
서버 준비 완료. 기본 브라우저를 엽니다: http://127.0.0.1:57685/
        /api/health = 200 on port 57685
```

- `runtime\rainflow.port` 생성 확인, 값 57685
- `GET http://127.0.0.1:57685/api/health` → 200 확인

### [2/4] 재실행 (무충돌 재사용 확인)

```
기존 서버(포트 57685)가 이미 응답하고 있어 재사용합니다.
서버 준비 완료. 기본 브라우저를 엽니다: http://127.0.0.1:57685/
        reused port 57685 without conflict
```

- 두 번째 `start.bat` 실행이 새 프로세스를 띄우지 않고 기존 서버(포트 57685)를
  그대로 재사용함을 확인 (RUNBOOK 109행 계약)
- 재실행 후에도 `/api/health` 200 재확인

### [3/4] `stop.bat` 실행

```
RainFlowSejong 서버(PID 1572)를 종료했습니다.
```

- `stop.ps1`이 `runtime\rainflow.pid`의 PID(1572)가 실제 `RainFlowSejong`
  프로세스인지 확인한 뒤에만 종료했음을 콘솔 출력으로 확인 (RUNBOOK 118행 계약)
- `stop.bat` 종료 코드 0
- `runtime\rainflow.pid`, `runtime\rainflow.port` 모두 삭제됨을 확인

### [4/4] 종료 후 상태 확인

- `stop.bat` 실행 1초 후 `GET http://127.0.0.1:57685/api/health` 요청이
  실패(연결 거부)함을 확인 → 서버가 실제로 내려갔음을 검증

### 최종 결과

```
ZIP launcher smoke test passed (unzip -> start.bat -> health 200 -> reuse -> stop.bat clean shutdown).
Run release\windows-x64\start.bat on a clean Windows x64 PC.
EXIT_CODE=0
```

## 확인한 런처 5종 동작

| 파일 | 인코딩/개행 | 동작 |
|---|---|---|
| `start.bat` | UTF-8(BOM 없음), **CRLF** | `launch.ps1`을 호출하는 래퍼. 실패 시 `pause`로 콘솔 유지 |
| `launch.ps1` | UTF-8, LF | 이전 서버 헬스 재사용 → OS에 빈 포트 요청(`TcpListener`) → `RainFlowSejong.exe` 백그라운드 실행 → PID/포트를 `runtime\`에 기록 → `/api/health` 최대 55초 폴링 → 성공 시 기본 브라우저 오픈 |
| `stop.bat` | UTF-8(BOM 없음), **CRLF** | `stop.ps1`을 호출하는 래퍼 |
| `stop.ps1` | UTF-8, LF | `runtime\rainflow.pid`의 PID가 실제 `RainFlowSejong` 프로세스일 때만 종료, 아니면 기록만 정리하고 종료하지 않음 |
| `README.txt` | UTF-8(BOM 없음) | 60초 실행법, 종료법, 포트 충돌 대처, SmartScreen 대응을 담은 일반 텍스트 |

`start.bat`/`stop.bat`은 `scripts/build_windows.ps1`이 ZIP에 넣기 직전 바이트
단위로 CRLF 여부를 검사하고, bare LF가 하나라도 있으면 빌드를 실패시킨다
(cmd.exe 파서를 깨뜨렸던 과거 사고 2회 재발 방지). `.gitattributes`에도
`eol=crlf`를 강제해 committer의 `core.autocrlf` 설정과 무관하게 저장소에서
체크아웃되는 두 `.bat` 파일이 항상 CRLF가 되도록 했다.

## 폴백/한계

- 이번 자동 스모크 테스트는 빌드 머신(경로에 한글/공백 없음)에서 수행했다.
  RUNBOOK 5절의 "한글과 공백이 있는 경로에서 `start.bat` 실행" 체크리스트
  항목은 `launch.ps1`/`stop.ps1`이 전부 `$PSScriptRoot`, `start.bat`/
  `stop.bat`이 `%~dp0` 기반으로 경로를 구성하므로 코드상 지원되지만, 별도의
  외부 PC 수동 검증(RUNBOOK 5절 체크리스트)은 이번 자동화 범위 밖이다.
- 브라우저 자동 오픈(`Start-Process $url`)은 스모크 테스트 중에도 그대로
  실행되어 빌드 머신에서 실제 브라우저 창이 두 번(최초 실행 + 재실행) 열렸다.
  이는 RUNBOOK이 규정한 실제 런처 동작이므로 의도된 부작용이다.

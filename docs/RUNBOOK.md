# RainFlow Sejong 실행·패키징 런북

이 문서는 개발 환경 재현과 Windows x64 오프라인 제출본 제작 절차를 정의한다. 제출본과 컨테이너 모두 외부 LLM, API 키, SUMO를 사용하지 않는다.

## 1. Docker로 개발 환경 실행

필수 도구는 Docker Desktop 또는 Docker Engine과 Compose v2뿐이다.

```bash
docker compose up --build
```

브라우저에서 `http://127.0.0.1:8000/`을 열고 상태 확인은 `http://127.0.0.1:8000/api/health`에서 한다. 컨테이너는 소스에 포함된 정적 프론트, 결정론적 시뮬레이터와 fixture만 사용한다. `.env`나 API 키는 필요하지 않다.

호스트의 8000 포트가 사용 중이면 다른 로컬 포트를 지정한다.

```bash
RAINFLOW_PORT=8087 docker compose up --build
```

PowerShell에서는 다음과 같이 실행한다.

```powershell
$env:RAINFLOW_PORT = "8087"
docker compose up --build
```

종료와 개발 로그 볼륨 제거:

```bash
docker compose down
docker compose down --volumes
```

`down --volumes`는 Docker의 `rainflow-logs` 개발 볼륨을 삭제하므로 로그 보존이 필요하면 첫 번째 명령만 사용한다.

## 2. 로컬 Python 실행

지원 버전은 Python 3.11 또는 3.12다.

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe -m launcher.run_rainflow --check
.\.venv\Scripts\python.exe -m launcher.run_rainflow
```

Linux/macOS:

```bash
./.venv/bin/python -m pip install -r requirements-dev.txt
./.venv/bin/python -m pytest backend/tests -q
./.venv/bin/python -m launcher.run_rainflow --check
./.venv/bin/python -m launcher.run_rainflow
```

기본 주소는 `http://127.0.0.1:8000/`이다. `--host`, `--port`, `RAINFLOW_HOST`, `RAINFLOW_PORT`로 개발 실행 주소를 바꿀 수 있다.

## 3. Windows x64 오프라인 번들 빌드

PyInstaller는 교차 컴파일을 지원하지 않으므로 Windows x64에서 빌드한다. Windows용 Python 3.11이 기본이며 3.12도 지원한다.

저장소 루트의 PowerShell에서:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

Python 3.12로 빌드하려면:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 -PythonVersion 3.12
```

빌드 스크립트는 다음을 자동 수행한다.

1. `.venv-build` 격리 환경 생성과 `requirements-build.txt` 설치
2. 백엔드 테스트와 소스 self-check 실행
3. `rainflow-sejong.spec`으로 onedir 실행본 생성
4. 패키지 실행파일 self-check 실행
5. `release/windows-x64`에 실행본 배치
6. `SHA256SUMS.txt`, `release/RainFlowSejong-windows-x64.zip`과 ZIP `.sha256` 생성

빌드 테스트를 생략하는 `-SkipTests`는 긴급 재빌드용이며 제출본에는 권장하지 않는다.

## 4. 제출본 구조와 실행

압축 해제 후 구조:

```text
RainFlowSejong.exe
_internal/
start.bat
launch.ps1
stop.bat
stop.ps1
README.txt
SHA256SUMS.txt
```

외부 PC에서는 `start.bat`만 실행한다. 런처는 다음 순서로 동작한다.

1. 이전 실행의 `/api/health`가 정상이면 기존 서버를 재사용한다.
2. 그렇지 않으면 `127.0.0.1`의 사용 가능한 포트를 운영체제에 요청한다.
3. 실행파일을 시작하고 최대 55초 동안 `/api/health`를 확인한다.
4. 정상 응답 뒤 기본 브라우저를 연다.
5. 출력은 `logs/`, 선택 포트와 PID는 `runtime/`에 기록한다.

경로는 `%~dp0`와 PowerShell의 `PSScriptRoot`를 사용하므로 한글과 공백이 포함된 압축 해제 경로를 지원한다. 서버는 `127.0.0.1`에만 바인딩한다.

런처의 stdout/stderr는 `logs/`에, 시뮬레이션·승인 감사 기록은 `_internal/backend/logs/`에 남는다. 문제를 전달할 때 두 위치를 함께 보존한다.
시연이 끝나면 `stop.bat`을 실행한다. 기록된 PID가 실제 `RainFlowSejong` 프로세스인지 확인한 뒤에만 종료하므로 PID 재사용으로 다른 프로세스를 종료하지 않는다.

## 5. 외부 PC 검증 체크리스트

초기화된 Windows x64 PC 두 대에서 각각 아래 절차를 두 번 연속 수행한다.

- [ ] Node.js, Python, SUMO가 설치되지 않은 상태에서 실행
- [ ] 인터넷을 끄고 API 키 환경변수 없이 실행
- [ ] 한글과 공백이 있는 경로에서 `start.bat` 실행
- [ ] 60초 이내 브라우저 화면 표시
- [ ] `GET /api/health`의 `status`가 `ok`
- [ ] 정상 → 강우 경고 → spillback → 정책 비교 → 안전 검토 → 운영자 승인 → 복구 비교 완주
- [ ] `start.bat` 재실행 시 기존 서버 재사용 또는 충돌 없는 새 실행
- [ ] `stop.bat` 실행 후 서버 종료와 runtime PID/port 파일 정리
- [ ] `logs/`의 오류 여부 확인

## 6. 문제 해결

`RainFlowSejong.exe is missing`이면 소스의 런처 템플릿만 복사한 상태다. `RainFlowSejong-windows-x64.zip` 전체를 다시 압축 해제한다.

브라우저가 자동으로 열리지 않아도 런처가 출력한 `http://127.0.0.1:<port>/` 주소를 직접 열 수 있다.

55초 안에 health check가 통과하지 않으면 `logs/server-*.out.log`와 `logs/server-*.err.log`를 보존한다. `runtime/rainflow.port`가 남아 있지만 서버가 종료된 경우 `start.bat` 재실행 시 오래된 값을 무시하고 새 포트를 선택한다.

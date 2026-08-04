# RainFlow Sejong 실행 매뉴얼

두 가지 실행 모드가 있다.

| 모드 | 준비물 | 파일 |
|---|---|---|
| dev 모드 (현재) | Python 3.9+ 및 `pip install fastapi uvicorn` | `start.bat` |
| exe 모드 (빌드 후) | 없음 (Python 불필요) | `build_windows.ps1`로 만든 `windows-x64\RainFlow.exe` |

## 60초 실행법 (dev 모드, 현재 제공 상태)

1. 압축을 풀거나 저장소를 받는다. 한글·공백이 섞인 폴더 경로에서도 동작한다.
2. `release\start.bat`을 더블클릭한다 (또는 `cmd`에서 `release\start.bat` 실행).
3. 콘솔에 사용 포트가 표시되고, `/api/health`가 응답할 때까지(최대 30초) 자동으로 기다린다.
4. 응답이 오면 기본 브라우저가 `http://127.0.0.1:<PORT>`로 자동으로 열린다.

사전에 Python과 의존성이 없으면:

```bat
pip install fastapi uvicorn
```

## 60초 실행법 (exe 모드, 빌드 후)

1. 개발 PC에서 한 번만: `powershell -ExecutionPolicy Bypass -File release\build_windows.ps1`
   - `release\windows-x64\RainFlow.exe`와 부속 파일이 생성된다.
2. `release\windows-x64\` 폴더 전체를 배포 대상 PC로 복사한다 (exe 하나만 옮기면 안 되고, 폴더째 옮겨야 한다. onedir 빌드라 같은 폴더 안의 라이브러리 파일들이 필요하다).
3. `RainFlow.exe`를 더블클릭하거나 `RainFlow.exe 8000`처럼 포트를 인자로 준다.
4. 콘솔 창이 열리고 서버가 기동한다. 브라우저에서 `http://127.0.0.1:8000`으로 접속한다 (exe 모드는 현재 자동으로 브라우저를 열지 않으므로 수동으로 접속한다).

## 종료법

- dev 모드: `start.bat`이 띄운 `RainFlow-Server-<PORT>`라는 이름의 최소화된 콘솔 창을 닫거나, 작업 관리자에서 해당 `python.exe`를 종료한다.
- exe 모드: `RainFlow.exe` 콘솔 창을 닫는다 (Ctrl+C도 가능).

## 포트 충돌 시 대처

- `start.bat`은 8000번부터 시작해 사용 중이면 8001~8010을 순서대로 시도한다.
- 이전 실행이 남긴 잔류 `python.exe`(uvicorn)가 같은 포트를 붙잡고 있으면 자동으로 종료하고 그 포트를 재사용한다.
- 그 외 프로그램(다른 서버 등)이 점유 중이면 다음 포트로 넘어간다.
- 8000~8010이 모두 다른 프로그램에 점유되어 있으면 오류 메시지를 띄운다. 이 경우 점유 중인 프로그램을 종료하거나, `release\logs\start_server.log`를 확인한 뒤 수동으로 `uvicorn backend.app.main:app --port <원하는 포트>`를 실행한다.
- exe 모드에서 포트 충돌 시: `RainFlow.exe <다른 포트 번호>`로 재실행한다.

## Windows SmartScreen 경고 대응 (exe 모드)

서명되지 않은 exe이므로 "Windows에서 PC를 보호했습니다" 경고가 뜰 수 있다.

1. 경고 창에서 **추가 정보**를 클릭한다.
2. **실행** 버튼을 클릭한다.

백신 프로그램이 오탐(false positive)으로 실행을 막는 경우, PyInstaller onedir 빌드 특성상 발생할 수 있는 알려진 현상이다. 예외 처리 후 다시 실행한다.

## dev 모드와 exe 모드 요약

| 항목 | dev 모드 (`start.bat`) | exe 모드 (`RainFlow.exe`) |
|---|---|---|
| Python 필요 여부 | 필요 | 불필요 |
| 인터넷 필요 여부 | 불필요 (의존성 사전 설치 시) | 불필요 |
| 브라우저 자동 실행 | O | X (수동 접속) |
| 로그 위치 | `release\logs\start_server.log` | 콘솔 창 출력 |
| 현재 제출 상태 | 제공 및 검증 완료 | 빌드 스크립트만 제공, 실제 빌드는 별도 수행 필요 |

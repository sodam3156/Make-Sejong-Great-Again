@echo off
REM ============================================================================
REM RainFlow Sejong - Windows 실행 스크립트 (dev 모드)
REM
REM 현재 이 스크립트는 로컬에 Python 3.9+ 및
REM   pip install fastapi uvicorn
REM 가 설치되어 있어야 동작한다 (dev 모드). PyInstaller로 빌드한 exe 모드에서는
REM Python 설치가 필요 없다 (release\build_windows.ps1, release\rainflow_entry.py 참고).
REM
REM 한글/공백이 섞인 경로에서도 동작하도록 모든 경로는 "%~dp0" 기반 + 따옴표 처리한다.
REM ============================================================================
setlocal enabledelayedexpansion
chcp 65001 >nul
title RainFlow Sejong - start.bat

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%.."
set "LOG_DIR=%SCRIPT_DIR%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
REM 서버(uvicorn) 표준출력/에러 로그와 이 스크립트 자체의 이벤트 로그를 분리한다.
REM 같은 파일에 동시에 쓰면(백그라운드 서버 + 전면 스크립트) 파일 잠금 충돌 경고가 뜰 수 있다.
set "SERVER_LOG=%LOG_DIR%\start_server.log"
set "EVENT_LOG=%LOG_DIR%\start_bat_events.log"
set "RUNNER=%LOG_DIR%\_run_server.bat"
set "HEALTH_TMP=%LOG_DIR%\_health_code.tmp"

echo [%date% %time%] start.bat 실행 시작 >> "%EVENT_LOG%"

REM --- 0. Python 존재 확인 -----------------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo [오류] Python을 찾을 수 없습니다. Python 3.9 이상을 설치한 뒤 다시 실행하세요.
    echo [오류] Python not found >> "%EVENT_LOG%"
    echo 로그 폴더: "%LOG_DIR%"
    pause
    exit /b 1
)

REM --- 1. 사용 가능한 포트 탐색 (8000 -> 8001..8010 순회) ----------------------
REM     같은 포트에서 응답이 없는 잔류 python/uvicorn 프로세스가 붙잡고 있으면
REM     정리하고 그 포트를 재사용한다. 그 외 프로세스가 점유 중이면 다음 포트로.
set "PORT="
for %%P in (8000 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010) do (
    if not defined PORT call :try_port %%P
)

if not defined PORT (
    echo [오류] 8000-8010 포트가 모두 사용 중입니다. 다른 프로그램을 종료한 뒤 재시도하세요.
    echo [오류] no free port in 8000-8010 >> "%EVENT_LOG%"
    pause
    exit /b 1
)

echo 사용 포트: %PORT%
echo [%date% %time%] PORT=%PORT% >> "%EVENT_LOG%"

REM --- 2. 백그라운드로 uvicorn 실행 (중첩 따옴표 문제를 피하려 러너 배치 생성) ---
> "%RUNNER%" echo @echo off
>> "%RUNNER%" echo cd /d "%REPO_ROOT%"
>> "%RUNNER%" echo python -m uvicorn backend.app.main:app --host 127.0.0.1 --port %PORT% ^>^> "%SERVER_LOG%" 2^>^&1

start "RainFlow-Server-%PORT%" /min "%RUNNER%"

REM --- 3. /api/health 최대 30초 폴링 -------------------------------------------
set "READY="
for /l %%I in (1,1,30) do (
    if not defined READY (
        set "HCODE="
        where curl >nul 2>nul
        if not errorlevel 1 (
            curl.exe -s -o nul -w "%%{http_code}" "http://127.0.0.1:!PORT!/api/health" > "%HEALTH_TMP%" 2>nul
        ) else (
            powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:!PORT!/api/health' -TimeoutSec 2).StatusCode } catch { '000' }" > "%HEALTH_TMP%" 2>nul
        )
        set /p HCODE=<"%HEALTH_TMP%"
        if "!HCODE!"=="200" (
            set "READY=1"
        ) else (
            ping -n 2 127.0.0.1 >nul
        )
    )
)
del /q "%HEALTH_TMP%" >nul 2>nul

if not defined READY (
    echo [오류] 30초 내에 서버가 응답하지 않았습니다.
    echo 로그 폴더를 확인하세요: "%LOG_DIR%" ^(start_server.log, start_bat_events.log^)
    echo [%date% %time%] health check timeout on port %PORT% >> "%EVENT_LOG%"
    pause
    exit /b 1
)

echo [%date% %time%] 서버 준비 완료 ^(포트 %PORT%^) >> "%EVENT_LOG%"
echo 서버 준비 완료. 기본 브라우저를 엽니다: http://127.0.0.1:%PORT%

REM --- 4. 성공 시 기본 브라우저로 열기 -----------------------------------------
start "" "http://127.0.0.1:%PORT%"

endlocal
exit /b 0

REM ============================================================================
:try_port
REM %1 = 검사할 포트 번호. 비어있으면 PORT에 설정, 잔류 python 프로세스가
REM      점유 중이면 종료 후 재사용, 다른 프로세스가 점유 중이면 건너뛴다.
set "CANDIDATE=%~1"
set "OWNER_PID="
for /f "tokens=5" %%A in ('netstat -ano -p tcp ^| findstr /r /c:":%CANDIDATE% .*LISTENING"') do (
    if not defined OWNER_PID set "OWNER_PID=%%A"
)

if not defined OWNER_PID (
    set "PORT=%CANDIDATE%"
    goto :eof
)

set "IS_PYTHON="
for /f "delims=" %%N in ('tasklist /fi "PID eq %OWNER_PID%" /nh /fo csv 2^>nul ^| findstr /i "python"') do (
    set "IS_PYTHON=1"
)

if defined IS_PYTHON (
    echo 잔류 프로세스 정리 중: PID=%OWNER_PID% 포트=%CANDIDATE%
    echo [%date% %time%] killing leftover PID %OWNER_PID% on port %CANDIDATE% >> "%EVENT_LOG%"
    taskkill /F /PID %OWNER_PID% >nul 2>nul
    ping -n 2 127.0.0.1 >nul
    set "PORT=%CANDIDATE%"
)
goto :eof

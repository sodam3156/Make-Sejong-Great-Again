@echo off
REM ============================================================================
REM RainFlow Sejong - one-click stop (calls stop.ps1)
REM Only terminates the server if the recorded PID is still RainFlowSejong.exe.
REM ============================================================================
setlocal
chcp 65001 >nul
title RainFlow Sejong - stop.bat

set "SCRIPT_DIR=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%stop.ps1"
set "RESULT=%ERRORLEVEL%"

if not "%RESULT%"=="0" (
    echo.
    echo [오류] 종료 처리 중 문제가 발생했습니다.
    pause
)

endlocal
exit /b %RESULT%

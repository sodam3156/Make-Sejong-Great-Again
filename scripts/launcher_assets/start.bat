@echo off
REM ============================================================================
REM RainFlow Sejong - one-click start (calls launch.ps1)
REM Double-click this file. No Python or internet connection required.
REM ============================================================================
setlocal
chcp 65001 >nul
title RainFlow Sejong - start.bat

set "SCRIPT_DIR=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%launch.ps1"
set "RESULT=%ERRORLEVEL%"

if not "%RESULT%"=="0" (
    echo.
    echo [오류] 실행에 실패했습니다. 위 메시지와 logs 폴더를 확인하세요.
    pause
)

endlocal
exit /b %RESULT%

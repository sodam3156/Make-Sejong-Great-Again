@echo off
setlocal

set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%POWERSHELL_EXE%" (
    echo [RainFlow Sejong] Windows PowerShell was not found.
    echo This launcher supports Windows x64 with Windows PowerShell 5.1.
    if /I not "%RAINFLOW_NONINTERACTIVE%"=="1" pause
    exit /b 2
)

"%POWERSHELL_EXE%" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0launch.ps1"
set "LAUNCH_EXIT=%ERRORLEVEL%"

if not "%LAUNCH_EXIT%"=="0" (
    echo.
    echo [RainFlow Sejong] Startup failed. Check the logs folder next to start.bat.
    if /I not "%RAINFLOW_NONINTERACTIVE%"=="1" pause
)

exit /b %LAUNCH_EXIT%

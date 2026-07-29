@echo off
setlocal

set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%POWERSHELL_EXE%" (
    echo [RainFlow Sejong] Windows PowerShell was not found.
    if /I not "%RAINFLOW_NONINTERACTIVE%"=="1" pause
    exit /b 2
)

"%POWERSHELL_EXE%" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0stop.ps1"
exit /b %ERRORLEVEL%

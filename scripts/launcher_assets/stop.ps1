# RainFlow Sejong - offline launcher stop script
#
# Implements docs/RUNBOOK.md section 4 (line 118): only terminate the process
# recorded in runtime/rainflow.pid after confirming it is actually a
# RainFlowSejong process. This prevents killing an unrelated process that
# happens to have reused the same PID after the original server exited.

$ErrorActionPreference = "Stop"

$ScriptDir = $PSScriptRoot
$RuntimeDir = Join-Path $ScriptDir "runtime"
$PortFile = Join-Path $RuntimeDir "rainflow.port"
$PidFile = Join-Path $RuntimeDir "rainflow.pid"

if (-not (Test-Path -LiteralPath $PidFile)) {
    Write-Host "실행 중인 서버 기록이 없습니다 (runtime/rainflow.pid 없음)."
    exit 0
}

$recordedPid = (Get-Content -LiteralPath $PidFile -Raw).Trim()

if (-not ($recordedPid -match '^\d+$')) {
    Write-Host "runtime/rainflow.pid 값이 올바르지 않습니다. 기록을 정리합니다."
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $PortFile -Force -ErrorAction SilentlyContinue
    exit 0
}

$targetProcess = Get-Process -Id ([int]$recordedPid) -ErrorAction SilentlyContinue

if (-not $targetProcess) {
    Write-Host "PID $recordedPid 프로세스가 이미 종료되어 있습니다. 기록을 정리합니다."
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $PortFile -Force -ErrorAction SilentlyContinue
    exit 0
}

if ($targetProcess.ProcessName -ne "RainFlowSejong") {
    Write-Host "[경고] PID $recordedPid 는 RainFlowSejong 프로세스가 아닙니다 (실제: $($targetProcess.ProcessName)). 종료하지 않습니다."
    Write-Host "다른 프로그램이 이 PID를 재사용했을 수 있습니다. runtime/rainflow.pid 기록만 정리합니다."
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $PortFile -Force -ErrorAction SilentlyContinue
    exit 0
}

Stop-Process -Id ([int]$recordedPid) -Force
Write-Host "RainFlowSejong 서버(PID $recordedPid)를 종료했습니다."

Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $PortFile -Force -ErrorAction SilentlyContinue

exit 0

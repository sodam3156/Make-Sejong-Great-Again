# RainFlow Sejong - offline launcher
#
# Implements the run contract documented in docs/RUNBOOK.md section 4:
#   1. If a previous run's /api/health is still healthy, reuse it.
#   2. Otherwise ask the OS for a free 127.0.0.1 port.
#   3. Start RainFlowSejong.exe and poll /api/health for up to 55 seconds.
#   4. On success, open the default browser.
#   5. Launcher stdout/stderr goes to logs/, the chosen port and PID go to runtime/.
#
# Uses $PSScriptRoot for all paths so extraction folders containing Korean
# characters or spaces work correctly. The server only ever binds 127.0.0.1.

$ErrorActionPreference = "Stop"

$ScriptDir = $PSScriptRoot
$ExePath = Join-Path $ScriptDir "RainFlowSejong.exe"
$LogDir = Join-Path $ScriptDir "logs"
$RuntimeDir = Join-Path $ScriptDir "runtime"
$PortFile = Join-Path $RuntimeDir "rainflow.port"
$PidFile = Join-Path $RuntimeDir "rainflow.pid"
$HealthTimeoutSeconds = 55

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null

function Test-RainflowHealth {
    param([int]$Port, [int]$TimeoutSec = 2)
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec $TimeoutSec
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Open-Browser {
    param([int]$Port)
    $url = "http://127.0.0.1:$Port/"
    Write-Host "서버 준비 완료. 기본 브라우저를 엽니다: $url"
    Start-Process $url | Out-Null
}

if (-not (Test-Path -LiteralPath $ExePath -PathType Leaf)) {
    Write-Host "[오류] RainFlowSejong.exe를 찾을 수 없습니다: $ExePath"
    Write-Host "[오류] RainFlowSejong-windows-x64.zip 전체를 다시 압축 해제했는지 확인하세요."
    exit 1
}

# --- 1. Reuse an already-running, healthy server -----------------------------
if (Test-Path -LiteralPath $PortFile) {
    $existingPort = (Get-Content -LiteralPath $PortFile -Raw).Trim()
    if ($existingPort -match '^\d+$' -and (Test-RainflowHealth -Port ([int]$existingPort))) {
        Write-Host "기존 서버(포트 $existingPort)가 이미 응답하고 있어 재사용합니다."
        Open-Browser -Port ([int]$existingPort)
        exit 0
    }
}

# --- 2. Ask the OS for a free 127.0.0.1 port ----------------------------------
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
$listener.Start()
$Port = $listener.LocalEndpoint.Port
$listener.Stop()

Write-Host "사용 포트: $Port"

# --- 3. Start RainFlowSejong.exe in the background ----------------------------
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutLog = Join-Path $LogDir "server-$timestamp.out.log"
$ErrLog = Join-Path $LogDir "server-$timestamp.err.log"

$env:RAINFLOW_HOST = "127.0.0.1"
$env:RAINFLOW_PORT = "$Port"

$process = Start-Process -FilePath $ExePath `
    -WorkingDirectory $ScriptDir `
    -RedirectStandardOutput $OutLog `
    -RedirectStandardError $ErrLog `
    -WindowStyle Hidden `
    -PassThru

Set-Content -LiteralPath $PortFile -Value "$Port" -NoNewline -Encoding ascii
Set-Content -LiteralPath $PidFile -Value "$($process.Id)" -NoNewline -Encoding ascii

# --- 4. Poll /api/health for up to 55 seconds ---------------------------------
$ready = $false
for ($i = 0; $i -lt $HealthTimeoutSeconds; $i++) {
    if (Test-RainflowHealth -Port $Port) {
        $ready = $true
        break
    }
    if ($process.HasExited) {
        Write-Host "[오류] 서버 프로세스가 예기치 않게 종료되었습니다 (종료 코드: $($process.ExitCode))."
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $ready) {
    Write-Host "[오류] $HealthTimeoutSeconds 초 안에 서버가 응답하지 않았습니다."
    Write-Host "로그를 확인하세요: $OutLog / $ErrLog"
    exit 1
}

# --- 5. Open the default browser ----------------------------------------------
Open-Browser -Port $Port
exit 0

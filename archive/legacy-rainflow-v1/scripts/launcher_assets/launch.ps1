[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Executable = Join-Path $PSScriptRoot "RainFlowSejong.exe"
$RuntimeDirectory = Join-Path $PSScriptRoot "runtime"
$LogDirectory = Join-Path $PSScriptRoot "logs"
$PortFile = Join-Path $RuntimeDirectory "rainflow.port"
$PidFile = Join-Path $RuntimeDirectory "rainflow.pid"

function Test-RainFlowHealth {
    param([int]$Port)

    try {
        $Health = Invoke-RestMethod `
            -UseBasicParsing `
            -Uri "http://127.0.0.1:$Port/api/health" `
            -Method Get `
            -TimeoutSec 1
        return $Health.status -eq "ok"
    }
    catch {
        return $false
    }
}

function Wait-RainFlowHealth {
    param(
        [int]$Port,
        [datetime]$Deadline,
        $Process
    )

    while ((Get-Date) -lt $Deadline) {
        if (Test-RainFlowHealth -Port $Port) {
            return $true
        }
        if ($null -ne $Process -and $Process.HasExited) {
            return $false
        }
        Start-Sleep -Milliseconds 250
    }
    return $false
}

function Get-FreeLoopbackPort {
    $Listener = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Loopback,
        0
    )
    try {
        $Listener.Start()
        return ([System.Net.IPEndPoint]$Listener.LocalEndpoint).Port
    }
    finally {
        $Listener.Stop()
    }
}

function Open-RainFlowBrowser {
    param([int]$Port)

    $Url = "http://127.0.0.1:$Port/"
    if (
        [Environment]::GetEnvironmentVariable(
            "RAINFLOW_NO_BROWSER",
            [EnvironmentVariableTarget]::Process
        ) -eq "1"
    ) {
        Write-Host "[RainFlow Sejong] Browser suppressed for automated validation: $Url"
        return
    }

    try {
        Start-Process $Url
        Write-Host "[RainFlow Sejong] Browser opened: $Url"
    }
    catch {
        Write-Host "[RainFlow Sejong] Server is ready. Open this address: $Url"
    }
}

if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
    [Console]::Error.WriteLine(
        "RainFlowSejong.exe is missing. Use the complete release ZIP, not the source template alone."
    )
    exit 2
}

New-Item -ItemType Directory -Path $RuntimeDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null

# Re-running start.bat reuses a healthy server instead of creating duplicates.
if (Test-Path -LiteralPath $PortFile -PathType Leaf) {
    $ExistingPortText = (Get-Content -LiteralPath $PortFile -Raw).Trim()
    $ExistingPort = 0
    if (
        [int]::TryParse($ExistingPortText, [ref]$ExistingPort) -and
        $ExistingPort -ge 1 -and
        $ExistingPort -le 65535
    ) {
        if (Test-RainFlowHealth -Port $ExistingPort) {
            Open-RainFlowBrowser -Port $ExistingPort
            exit 0
        }

        # A second launch during initial extraction waits for the first process.
        if (Test-Path -LiteralPath $PidFile -PathType Leaf) {
            $ExistingPidText = (Get-Content -LiteralPath $PidFile -Raw).Trim()
            $ExistingPid = 0
            if ([int]::TryParse($ExistingPidText, [ref]$ExistingPid)) {
                $ExistingProcess = Get-Process -Id $ExistingPid -ErrorAction SilentlyContinue
                if ($null -ne $ExistingProcess) {
                    $ExistingDeadline = (Get-Date).AddSeconds(15)
                    if (
                        Wait-RainFlowHealth `
                            -Port $ExistingPort `
                            -Deadline $ExistingDeadline `
                            -Process $ExistingProcess
                    ) {
                        Open-RainFlowBrowser -Port $ExistingPort
                        exit 0
                    }
                }
            }
        }
    }
}

Remove-Item -LiteralPath $PortFile -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue

$OverallDeadline = (Get-Date).AddSeconds(55)
$LastStdoutLog = $null
$LastStderrLog = $null

for ($Attempt = 1; $Attempt -le 3; $Attempt++) {
    $Port = Get-FreeLoopbackPort
    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $LastStdoutLog = Join-Path $LogDirectory "server-$Timestamp-$Attempt.out.log"
    $LastStderrLog = Join-Path $LogDirectory "server-$Timestamp-$Attempt.err.log"

    Set-Content -LiteralPath $PortFile -Value $Port -Encoding Ascii

    $ServerProcess = Start-Process `
        -FilePath $Executable `
        -ArgumentList @("--host", "127.0.0.1", "--port", "$Port") `
        -WorkingDirectory $PSScriptRoot `
        -RedirectStandardOutput $LastStdoutLog `
        -RedirectStandardError $LastStderrLog `
        -WindowStyle Hidden `
        -PassThru
    Set-Content -LiteralPath $PidFile -Value $ServerProcess.Id -Encoding Ascii

    if (
        Wait-RainFlowHealth `
            -Port $Port `
            -Deadline $OverallDeadline `
            -Process $ServerProcess
    ) {
        Open-RainFlowBrowser -Port $Port
        exit 0
    }

    if (-not $ServerProcess.HasExited) {
        # Startup timed out while this exact process was still alive. Stop it
        # before deleting its PID record so stop.bat is never orphaned.
        Stop-Process -Id $ServerProcess.Id -Force -ErrorAction SilentlyContinue
        $ServerProcess.WaitForExit(5000) | Out-Null
        break
    }

    # A bind race exits quickly; choose another free port while time remains.
    if ((Get-Date) -ge $OverallDeadline) {
        break
    }
}

Remove-Item -LiteralPath $PortFile -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue

Write-Error (
    "The server did not become healthy within 55 seconds. " +
    "Check '$LastStdoutLog' and '$LastStderrLog'."
)
exit 1

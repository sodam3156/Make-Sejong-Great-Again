[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RuntimeDirectory = Join-Path $PSScriptRoot "runtime"
$PortFile = Join-Path $RuntimeDirectory "rainflow.port"
$PidFile = Join-Path $RuntimeDirectory "rainflow.pid"
$Executable = Join-Path $PSScriptRoot "RainFlowSejong.exe"

if (-not (Test-Path -LiteralPath $PidFile -PathType Leaf)) {
    Remove-Item -LiteralPath $PortFile -Force -ErrorAction SilentlyContinue
    Write-Host "[RainFlow Sejong] No recorded server process is running."
    exit 0
}

$PidText = (Get-Content -LiteralPath $PidFile -Raw).Trim()
$ServerPid = 0
if (-not [int]::TryParse($PidText, [ref]$ServerPid)) {
    Remove-Item -LiteralPath $PidFile, $PortFile -Force -ErrorAction SilentlyContinue
    Write-Error "The recorded server PID is invalid; stale runtime files were removed."
    exit 1
}

$ServerProcess = Get-Process -Id $ServerPid -ErrorAction SilentlyContinue
if ($null -eq $ServerProcess) {
    Remove-Item -LiteralPath $PidFile, $PortFile -Force -ErrorAction SilentlyContinue
    Write-Host "[RainFlow Sejong] The recorded process already stopped."
    exit 0
}

$ActualExecutablePath = $null
try {
    $ActualExecutablePath = $ServerProcess.Path
}
catch {
    # Refuse to terminate when Windows does not allow executable-path inspection.
}

if (
    $ServerProcess.ProcessName -ne "RainFlowSejong" -or
    $null -eq $ActualExecutablePath -or
    -not [string]::Equals(
        [System.IO.Path]::GetFullPath($ActualExecutablePath),
        [System.IO.Path]::GetFullPath($Executable),
        [System.StringComparison]::OrdinalIgnoreCase
    )
) {
    Write-Error (
        "PID $ServerPid is not this release folder's RainFlowSejong.exe. " +
        "No process was stopped; the runtime record was preserved for inspection."
    )
    exit 1
}

Stop-Process -Id $ServerPid -Force
$ServerProcess.WaitForExit(5000) | Out-Null
Remove-Item -LiteralPath $PidFile, $PortFile -Force -ErrorAction SilentlyContinue
Write-Host "[RainFlow Sejong] Server stopped."

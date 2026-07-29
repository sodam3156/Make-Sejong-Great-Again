[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ZipPath,

    [ValidateRange(10, 300)]
    [int]$LauncherTimeoutSeconds = 70
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($env:OS -ne "Windows_NT") {
    throw "The extracted Windows release smoke test must run on Windows."
}

$ResolvedZipPath = (Resolve-Path -LiteralPath $ZipPath).Path
$RequiredRootFiles = @(
    "RainFlowSejong.exe",
    "start.bat",
    "launch.ps1",
    "stop.bat",
    "stop.ps1",
    "README.txt",
    "SHA256SUMS.txt"
)
$CommandProcessor = Join-Path $env:SystemRoot "System32\cmd.exe"
$SmokeParent = Join-Path (
    [System.IO.Path]::GetTempPath()
) ("rainflow-release-smoke-" + [guid]::NewGuid().ToString("N"))
# Build a Korean path prefix from code points so Windows PowerShell 5.1 can
# parse this UTF-8-without-BOM script while the smoke still covers Unicode paths.
$UnicodePathPrefix = -join @(
    [char]0xD55C,
    [char]0xAE00,
    [char]0x0020,
    [char]0xACBD,
    [char]0xB85C
)
$ExtractRoot = Join-Path $SmokeParent "$UnicodePathPrefix with spaces"
$RuntimeDirectory = Join-Path $ExtractRoot "runtime"
$PortFile = Join-Path $RuntimeDirectory "rainflow.port"
$ProcessIdFile = Join-Path $RuntimeDirectory "rainflow.pid"
$ExtractedExecutable = Join-Path $ExtractRoot "RainFlowSejong.exe"
$StartBatch = Join-Path $ExtractRoot "start.bat"
$StopBatch = Join-Path $ExtractRoot "stop.bat"
$ServerProcessIdForCleanup = $null
$PreviousNoBrowser = [Environment]::GetEnvironmentVariable(
    "RAINFLOW_NO_BROWSER",
    [EnvironmentVariableTarget]::Process
)
$PreviousNonInteractive = [Environment]::GetEnvironmentVariable(
    "RAINFLOW_NONINTERACTIVE",
    [EnvironmentVariableTarget]::Process
)

function Invoke-BatchLauncher {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BatchPath,

        [Parameter(Mandatory = $true)]
        [int]$TimeoutSeconds
    )

    $QuotedBatchPath = '"' + $BatchPath + '"'
    $LauncherProcess = Start-Process `
        -FilePath $CommandProcessor `
        -ArgumentList @("/d", "/c", $QuotedBatchPath) `
        -WorkingDirectory $ExtractRoot `
        -WindowStyle Hidden `
        -PassThru

    if (-not $LauncherProcess.WaitForExit($TimeoutSeconds * 1000)) {
        Stop-Process -Id $LauncherProcess.Id -Force -ErrorAction SilentlyContinue
        throw (
            "Launcher timed out after $TimeoutSeconds seconds: " +
            [System.IO.Path]::GetFileName($BatchPath)
        )
    }

    return $LauncherProcess.ExitCode
}

function Read-RuntimeInteger {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Label,

        [Parameter(Mandatory = $true)]
        [int]$Minimum,

        [Parameter(Mandatory = $true)]
        [int]$Maximum
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Smoke test: runtime $Label file was not created."
    }

    $ValueText = (Get-Content -LiteralPath $Path -Raw).Trim()
    $ParsedValue = 0
    if (
        -not [int]::TryParse($ValueText, [ref]$ParsedValue) -or
        $ParsedValue -lt $Minimum -or
        $ParsedValue -gt $Maximum
    ) {
        throw "Smoke test: runtime $Label value is invalid: '$ValueText'."
    }

    return $ParsedValue
}

function Get-RainFlowHealth {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,

        [int]$TimeoutSeconds = 2
    )

    try {
        $Response = Invoke-WebRequest `
            -UseBasicParsing `
            -Uri "http://127.0.0.1:$Port/api/health" `
            -Method Get `
            -TimeoutSec $TimeoutSeconds
        $Body = $Response.Content | ConvertFrom-Json
        return [pscustomobject]@{
            StatusCode = [int]$Response.StatusCode
            Status = [string]$Body.status
        }
    }
    catch {
        return $null
    }
}

function Assert-RainFlowHealth {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,

        [Parameter(Mandatory = $true)]
        [string]$Phase
    )

    $Health = Get-RainFlowHealth -Port $Port
    if (
        $null -eq $Health -or
        $Health.StatusCode -ne 200 -or
        $Health.Status -ne "ok"
    ) {
        $Observed = if ($null -eq $Health) {
            "no response"
        }
        else {
            "HTTP $($Health.StatusCode), status '$($Health.Status)'"
        }
        throw "Smoke test: health check failed after $Phase ($Observed)."
    }
}

function Get-ProcessExecutablePath {
    param([System.Diagnostics.Process]$Process)

    try {
        return $Process.Path
    }
    catch {
        return $null
    }
}

try {
    [Environment]::SetEnvironmentVariable(
        "RAINFLOW_NO_BROWSER",
        "1",
        [EnvironmentVariableTarget]::Process
    )
    [Environment]::SetEnvironmentVariable(
        "RAINFLOW_NONINTERACTIVE",
        "1",
        [EnvironmentVariableTarget]::Process
    )

    New-Item -ItemType Directory -Path $ExtractRoot -Force | Out-Null
    Expand-Archive -LiteralPath $ResolvedZipPath -DestinationPath $ExtractRoot -Force

    foreach ($RequiredFile in $RequiredRootFiles) {
        if (-not (Test-Path -LiteralPath (Join-Path $ExtractRoot $RequiredFile) -PathType Leaf)) {
            throw "Smoke test: extracted ZIP root is missing $RequiredFile."
        }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $ExtractRoot "_internal") -PathType Container)) {
        throw "Smoke test: extracted ZIP root is missing the _internal directory."
    }

    Write-Host "  [1/4] start.bat -> health HTTP 200/status ok"
    $FirstStartExitCode = Invoke-BatchLauncher `
        -BatchPath $StartBatch `
        -TimeoutSeconds $LauncherTimeoutSeconds
    if ($FirstStartExitCode -ne 0) {
        throw "Smoke test: first start.bat exited with code $FirstStartExitCode."
    }

    $FirstPort = Read-RuntimeInteger `
        -Path $PortFile `
        -Label "port" `
        -Minimum 1 `
        -Maximum 65535
    $FirstServerProcessId = Read-RuntimeInteger `
        -Path $ProcessIdFile `
        -Label "PID" `
        -Minimum 1 `
        -Maximum ([int]::MaxValue)
    $ServerProcessIdForCleanup = $FirstServerProcessId
    $FirstServerProcess = Get-Process `
        -Id $FirstServerProcessId `
        -ErrorAction SilentlyContinue
    if (
        $null -eq $FirstServerProcess -or
        $FirstServerProcess.ProcessName -ne "RainFlowSejong"
    ) {
        throw "Smoke test: the recorded PID is not a running RainFlowSejong process."
    }
    Assert-RainFlowHealth -Port $FirstPort -Phase "first start"

    Write-Host "  [2/4] restart via start.bat -> same PID/port -> health 200"
    $SecondStartExitCode = Invoke-BatchLauncher `
        -BatchPath $StartBatch `
        -TimeoutSeconds $LauncherTimeoutSeconds
    if ($SecondStartExitCode -ne 0) {
        throw "Smoke test: second start.bat exited with code $SecondStartExitCode."
    }

    $SecondPort = Read-RuntimeInteger `
        -Path $PortFile `
        -Label "port" `
        -Minimum 1 `
        -Maximum 65535
    $SecondServerProcessId = Read-RuntimeInteger `
        -Path $ProcessIdFile `
        -Label "PID" `
        -Minimum 1 `
        -Maximum ([int]::MaxValue)
    if ($SecondPort -ne $FirstPort) {
        throw "Smoke test: restart changed the port ($FirstPort -> $SecondPort)."
    }
    if ($SecondServerProcessId -ne $FirstServerProcessId) {
        throw (
            "Smoke test: restart created a duplicate process " +
            "($FirstServerProcessId -> $SecondServerProcessId)."
        )
    }
    Assert-RainFlowHealth -Port $SecondPort -Phase "restart"

    Write-Host "  [3/4] stop.bat -> process and runtime files removed"
    $StopExitCode = Invoke-BatchLauncher `
        -BatchPath $StopBatch `
        -TimeoutSeconds 20
    if ($StopExitCode -ne 0) {
        throw "Smoke test: stop.bat exited with code $StopExitCode."
    }

    $ShutdownDeadline = (Get-Date).AddSeconds(10)
    do {
        $RemainingProcess = Get-Process `
            -Id $FirstServerProcessId `
            -ErrorAction SilentlyContinue
        if ($null -eq $RemainingProcess) {
            break
        }
        Start-Sleep -Milliseconds 200
    } while ((Get-Date) -lt $ShutdownDeadline)

    if ($null -ne $RemainingProcess) {
        throw "Smoke test: RainFlowSejong PID $FirstServerProcessId is still running after stop.bat."
    }
    $ServerProcessIdForCleanup = $null

    if (Test-Path -LiteralPath $ProcessIdFile) {
        throw "Smoke test: runtime\rainflow.pid remains after stop.bat."
    }
    if (Test-Path -LiteralPath $PortFile) {
        throw "Smoke test: runtime\rainflow.port remains after stop.bat."
    }

    Write-Host "  [4/4] post-stop health endpoint is unavailable"
    Start-Sleep -Milliseconds 500
    $PostStopHealth = Get-RainFlowHealth -Port $FirstPort
    if ($null -ne $PostStopHealth) {
        throw (
            "Smoke test: health endpoint still responds after stop " +
            "(HTTP $($PostStopHealth.StatusCode))."
        )
    }

    Write-Host (
        "Extracted ZIP smoke passed: start -> health 200 -> restart " +
        "(same PID/port) -> stop."
    )
}
finally {
    if (
        $null -eq $ServerProcessIdForCleanup -and
        (Test-Path -LiteralPath $ProcessIdFile -PathType Leaf)
    ) {
        $RecoveredProcessIdText = (Get-Content -LiteralPath $ProcessIdFile -Raw).Trim()
        $RecoveredProcessId = 0
        if (
            [int]::TryParse(
                $RecoveredProcessIdText,
                [ref]$RecoveredProcessId
            ) -and
            $RecoveredProcessId -gt 0
        ) {
            $ServerProcessIdForCleanup = $RecoveredProcessId
        }
    }

    if ($null -ne $ServerProcessIdForCleanup) {
        $CleanupProcess = Get-Process `
            -Id $ServerProcessIdForCleanup `
            -ErrorAction SilentlyContinue
        if ($null -ne $CleanupProcess) {
            $CleanupProcessPath = Get-ProcessExecutablePath -Process $CleanupProcess
            if (
                $CleanupProcess.ProcessName -eq "RainFlowSejong" -and
                $null -ne $CleanupProcessPath -and
                [string]::Equals(
                    [System.IO.Path]::GetFullPath($CleanupProcessPath),
                    [System.IO.Path]::GetFullPath($ExtractedExecutable),
                    [System.StringComparison]::OrdinalIgnoreCase
                )
            ) {
                Stop-Process `
                    -Id $ServerProcessIdForCleanup `
                    -Force `
                    -ErrorAction SilentlyContinue
                $CleanupProcess.WaitForExit(5000) | Out-Null
            }
        }
    }

    [Environment]::SetEnvironmentVariable(
        "RAINFLOW_NO_BROWSER",
        $PreviousNoBrowser,
        [EnvironmentVariableTarget]::Process
    )
    [Environment]::SetEnvironmentVariable(
        "RAINFLOW_NONINTERACTIVE",
        $PreviousNonInteractive,
        [EnvironmentVariableTarget]::Process
    )

    if (Test-Path -LiteralPath $SmokeParent) {
        Remove-Item `
            -LiteralPath $SmokeParent `
            -Recurse `
            -Force `
            -ErrorAction SilentlyContinue
    }
}

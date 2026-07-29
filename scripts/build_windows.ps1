[CmdletBinding()]
param(
    [ValidateSet("3.11", "3.12")]
    [string]$PythonVersion = "3.11",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($env:OS -ne "Windows_NT") {
    throw "PyInstaller Windows bundles must be built on Windows x64."
}

$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BuildVenv = Join-Path $RepositoryRoot ".venv-build"
$BuildPython = Join-Path $BuildVenv "Scripts\python.exe"
$SpecPath = Join-Path $RepositoryRoot "rainflow-sejong.spec"
$DistDirectory = Join-Path $RepositoryRoot "dist\RainFlowSejong"
$ReleaseDirectory = Join-Path $RepositoryRoot "release\windows-x64"
$ZipPath = Join-Path $RepositoryRoot "release\RainFlowSejong-windows-x64.zip"
$ZipChecksumPath = "$ZipPath.sha256"
$LauncherAssetsDirectory = Join-Path $PSScriptRoot "launcher_assets"
$LauncherAssetNames = @("start.bat", "launch.ps1", "stop.bat", "stop.ps1", "README.txt")

Push-Location $RepositoryRoot
try {
    if (-not (Test-Path -LiteralPath $BuildPython -PathType Leaf)) {
        & py "-$PythonVersion" -m venv $BuildVenv
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to create the Python $PythonVersion build environment."
        }
    }

    & $BuildPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "pip upgrade failed."
    }

    & $BuildPython -m pip install --requirement requirements-build.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Build dependency installation failed."
    }

    if (-not $SkipTests) {
        & $BuildPython -m pytest backend/tests -q
        if ($LASTEXITCODE -ne 0) {
            throw "Backend tests failed; the release was not built."
        }
    }

    & $BuildPython -m launcher.run_rainflow --check
    if ($LASTEXITCODE -ne 0) {
        throw "Source self-check failed; the release was not built."
    }

    & $BuildPython -m PyInstaller --noconfirm --clean $SpecPath
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed."
    }

    $BuiltExecutable = Join-Path $DistDirectory "RainFlowSejong.exe"
    if (-not (Test-Path -LiteralPath $BuiltExecutable -PathType Leaf)) {
        throw "PyInstaller did not produce $BuiltExecutable."
    }

    & $BuiltExecutable --check
    if ($LASTEXITCODE -ne 0) {
        throw "Packaged executable self-check failed."
    }

    New-Item -ItemType Directory -Path $ReleaseDirectory -Force | Out-Null

    foreach ($KnownArtifact in @("RainFlowSejong.exe", "_internal", "logs", "runtime", "SHA256SUMS.txt") + $LauncherAssetNames) {
        $ArtifactPath = Join-Path $ReleaseDirectory $KnownArtifact
        if (Test-Path -LiteralPath $ArtifactPath) {
            Remove-Item -LiteralPath $ArtifactPath -Recurse -Force
        }
    }

    Get-ChildItem -LiteralPath $DistDirectory | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $ReleaseDirectory -Recurse -Force
    }

    # --- Bundle the one-click launcher (docs/RUNBOOK.md section 4 contract) ---
    foreach ($AssetName in $LauncherAssetNames) {
        $SourceAssetPath = Join-Path $LauncherAssetsDirectory $AssetName
        if (-not (Test-Path -LiteralPath $SourceAssetPath -PathType Leaf)) {
            throw "Launcher asset missing from scripts/launcher_assets: $AssetName"
        }
        Copy-Item -LiteralPath $SourceAssetPath -Destination (Join-Path $ReleaseDirectory $AssetName) -Force
    }

    foreach ($BatchAsset in @("start.bat", "stop.bat")) {
        $BatchBytes = [System.IO.File]::ReadAllBytes((Join-Path $ReleaseDirectory $BatchAsset))
        for ($i = 0; $i -lt $BatchBytes.Length; $i++) {
            if ($BatchBytes[$i] -eq 10 -and ($i -eq 0 -or $BatchBytes[$i - 1] -ne 13)) {
                throw "$BatchAsset contains a bare LF line ending; cmd.exe requires CRLF (see C-021 incident history)."
            }
        }
    }

    $ChecksumPath = Join-Path $ReleaseDirectory "SHA256SUMS.txt"
    $ChecksumLines = Get-ChildItem -LiteralPath $ReleaseDirectory -File -Recurse |
        Where-Object { $_.FullName -ne $ChecksumPath } |
        Sort-Object FullName |
        ForEach-Object {
            $RelativePath = $_.FullName.Substring($ReleaseDirectory.Length + 1).Replace("\", "/")
            $Hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            "$Hash *$RelativePath"
        }
    [System.IO.File]::WriteAllLines(
        $ChecksumPath,
        [string[]]$ChecksumLines,
        [System.Text.UTF8Encoding]::new($false)
    )

    if (Test-Path -LiteralPath $ZipPath) {
        Remove-Item -LiteralPath $ZipPath -Force
    }
    Compress-Archive -Path (Join-Path $ReleaseDirectory "*") -DestinationPath $ZipPath -CompressionLevel Optimal
    $ZipHash = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
    [System.IO.File]::WriteAllText(
        $ZipChecksumPath,
        "$ZipHash *RainFlowSejong-windows-x64.zip`n",
        [System.Text.UTF8Encoding]::new($false)
    )

    Write-Host ""
    Write-Host "Windows release created:"
    Write-Host "  Directory: $ReleaseDirectory"
    Write-Host "  Archive:   $ZipPath"
    Write-Host "  SHA256:    $ZipChecksumPath"

    # --- ZIP launcher smoke test (C-021: unzip -> start.bat -> /api/health 200
    # -> re-run without conflict -> stop.bat clean shutdown). A failure here
    # must fail the build (non-zero exit) so a broken launcher never ships. ---
    Write-Host ""
    Write-Host "Running ZIP launcher smoke test..."

    function Get-RainflowHealthCode {
        param([int]$Port, [int]$TimeoutSec = 2)
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec $TimeoutSec
            return $response.StatusCode
        } catch {
            return $null
        }
    }

    $SmokeRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("rainflow-launcher-smoke-" + (Get-Date -Format "yyyyMMdd_HHmmss"))
    if (Test-Path -LiteralPath $SmokeRoot) {
        Remove-Item -LiteralPath $SmokeRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $SmokeRoot -Force | Out-Null

    try {
        Expand-Archive -LiteralPath $ZipPath -DestinationPath $SmokeRoot -Force

        $SmokeStartBat = Join-Path $SmokeRoot "start.bat"
        $SmokeStopBat = Join-Path $SmokeRoot "stop.bat"
        $SmokePortFile = Join-Path $SmokeRoot "runtime\rainflow.port"
        $SmokePidFile = Join-Path $SmokeRoot "runtime\rainflow.pid"

        foreach ($RequiredFile in @("RainFlowSejong.exe", "start.bat", "launch.ps1", "stop.bat", "stop.ps1", "README.txt", "SHA256SUMS.txt")) {
            if (-not (Test-Path -LiteralPath (Join-Path $SmokeRoot $RequiredFile))) {
                throw "Smoke test: extracted ZIP is missing required file $RequiredFile."
            }
        }

        Write-Host "  [1/4] first start.bat run..."
        & cmd.exe /c "`"$SmokeStartBat`""
        if ($LASTEXITCODE -ne 0) {
            throw "Smoke test: first start.bat run exited with code $LASTEXITCODE."
        }
        if (-not (Test-Path -LiteralPath $SmokePortFile)) {
            throw "Smoke test: runtime\rainflow.port was not created by start.bat."
        }
        $SmokePort = [int](Get-Content -LiteralPath $SmokePortFile -Raw).Trim()
        $FirstHealthCode = Get-RainflowHealthCode -Port $SmokePort
        if ($FirstHealthCode -ne 200) {
            throw "Smoke test: /api/health returned '$FirstHealthCode' instead of 200 after first start.bat run."
        }
        Write-Host "        /api/health = 200 on port $SmokePort"

        Write-Host "  [2/4] second start.bat run (must reuse without conflict)..."
        & cmd.exe /c "`"$SmokeStartBat`""
        if ($LASTEXITCODE -ne 0) {
            throw "Smoke test: second (reuse) start.bat run exited with code $LASTEXITCODE."
        }
        $SecondPort = [int](Get-Content -LiteralPath $SmokePortFile -Raw).Trim()
        if ($SecondPort -ne $SmokePort) {
            throw "Smoke test: re-running start.bat changed the port ($SmokePort -> $SecondPort) instead of reusing the running server."
        }
        $SecondHealthCode = Get-RainflowHealthCode -Port $SecondPort
        if ($SecondHealthCode -ne 200) {
            throw "Smoke test: /api/health returned '$SecondHealthCode' instead of 200 after re-running start.bat."
        }
        Write-Host "        reused port $SecondPort without conflict"

        Write-Host "  [3/4] stop.bat run..."
        & cmd.exe /c "`"$SmokeStopBat`""
        if ($LASTEXITCODE -ne 0) {
            throw "Smoke test: stop.bat exited with code $LASTEXITCODE."
        }
        if (Test-Path -LiteralPath $SmokePidFile) {
            throw "Smoke test: runtime\rainflow.pid still present after stop.bat."
        }
        if (Test-Path -LiteralPath $SmokePortFile) {
            throw "Smoke test: runtime\rainflow.port still present after stop.bat."
        }

        Write-Host "  [4/4] confirming server is actually down..."
        Start-Sleep -Seconds 1
        $PostStopHealthCode = Get-RainflowHealthCode -Port $SmokePort -TimeoutSec 2
        if ($null -ne $PostStopHealthCode) {
            throw "Smoke test: /api/health still responded ($PostStopHealthCode) after stop.bat; server did not shut down."
        }

        Write-Host "ZIP launcher smoke test passed (unzip -> start.bat -> health 200 -> reuse -> stop.bat clean shutdown)."
    } catch {
        # Best-effort cleanup of any leftover RainFlowSejong process from a failed smoke test.
        if (Test-Path -LiteralPath (Join-Path $SmokeRoot "runtime\rainflow.pid")) {
            $LeftoverPid = (Get-Content -LiteralPath (Join-Path $SmokeRoot "runtime\rainflow.pid") -Raw).Trim()
            if ($LeftoverPid -match '^\d+$') {
                $LeftoverProcess = Get-Process -Id ([int]$LeftoverPid) -ErrorAction SilentlyContinue
                if ($LeftoverProcess -and $LeftoverProcess.ProcessName -eq "RainFlowSejong") {
                    Stop-Process -Id ([int]$LeftoverPid) -Force -ErrorAction SilentlyContinue
                }
            }
        }
        throw
    } finally {
        if (Test-Path -LiteralPath $SmokeRoot) {
            Remove-Item -LiteralPath $SmokeRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    Write-Host "Run release\windows-x64\start.bat on a clean Windows x64 PC."
}
finally {
    Pop-Location
}

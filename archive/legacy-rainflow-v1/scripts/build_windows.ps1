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
if (-not [Environment]::Is64BitOperatingSystem) {
    throw "The windows-x64 release requires a 64-bit Windows operating system."
}

$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BuildVenv = Join-Path $RepositoryRoot ".venv-build"
$BuildPython = Join-Path $BuildVenv "Scripts\python.exe"
$SpecPath = Join-Path $RepositoryRoot "rainflow-sejong.spec"
$DistDirectory = Join-Path $RepositoryRoot "dist\RainFlowSejong"
$ReleaseDirectory = Join-Path $RepositoryRoot "release\windows-x64"
$ZipPath = Join-Path $RepositoryRoot "release\RainFlowSejong-windows-x64.zip"
$ZipChecksumPath = "$ZipPath.sha256"
$CandidateZipPath = Join-Path $RepositoryRoot "release\RainFlowSejong-windows-x64.candidate.zip"
$LauncherAssetsDirectory = Join-Path $PSScriptRoot "launcher_assets"
$LauncherAssetNames = @(
    "start.bat",
    "launch.ps1",
    "stop.bat",
    "stop.ps1",
    "README.txt"
)
$SmokeScriptPath = Join-Path $PSScriptRoot "smoke_windows_release.ps1"
$RequestedPythonVersionParts = $PythonVersion.Split(".")
$RequestedPythonSelector = "-$PythonVersion-64"

Push-Location $RepositoryRoot
try {
    foreach ($LauncherAssetName in $LauncherAssetNames) {
        $LauncherAssetPath = Join-Path $LauncherAssetsDirectory $LauncherAssetName
        if (-not (Test-Path -LiteralPath $LauncherAssetPath -PathType Leaf)) {
            throw "Required launcher source is missing: $LauncherAssetPath"
        }
    }
    if (-not (Test-Path -LiteralPath $SmokeScriptPath -PathType Leaf)) {
        throw "Windows release smoke gate is missing: $SmokeScriptPath"
    }

    foreach ($BatchAssetName in @("start.bat", "stop.bat")) {
        $BatchAssetPath = Join-Path $LauncherAssetsDirectory $BatchAssetName
        $BatchBytes = [System.IO.File]::ReadAllBytes($BatchAssetPath)
        for ($ByteIndex = 0; $ByteIndex -lt $BatchBytes.Length; $ByteIndex++) {
            if (
                $BatchBytes[$ByteIndex] -eq 10 -and
                ($ByteIndex -eq 0 -or $BatchBytes[$ByteIndex - 1] -ne 13)
            ) {
                throw "$BatchAssetName contains a bare LF; Windows batch files must use CRLF."
            }
        }
    }

    if (Test-Path -LiteralPath $BuildPython -PathType Leaf) {
        $ExistingPythonInfoOutput = & $BuildPython -c (
            "import platform, sys; " +
            "print(sys.version_info.major, sys.version_info.minor, " +
            "platform.machine(), 64 if sys.maxsize > 2**32 else 32)"
        )
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to inspect the existing build environment Python."
        }
        $ExistingPythonInfo = ([string]$ExistingPythonInfoOutput).Trim() -split "\s+"
        $ExistingPythonMatches = (
            $ExistingPythonInfo.Count -eq 4 -and
            $ExistingPythonInfo[0] -eq $RequestedPythonVersionParts[0] -and
            $ExistingPythonInfo[1] -eq $RequestedPythonVersionParts[1] -and
            $ExistingPythonInfo[2] -match "^(AMD64|x86_64)$" -and
            $ExistingPythonInfo[3] -eq "64"
        )
        if (-not $ExistingPythonMatches) {
            Write-Host (
                "Recreating .venv-build for Python $PythonVersion x64 " +
                "(existing: '$ExistingPythonInfoOutput')."
            )
            Remove-Item -LiteralPath $BuildVenv -Recurse -Force
        }
    }

    if (-not (Test-Path -LiteralPath $BuildPython -PathType Leaf)) {
        & py $RequestedPythonSelector -m venv $BuildVenv
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to create the Python $PythonVersion x64 build environment."
        }
    }

    $BuildPythonInfoOutput = & $BuildPython -c (
        "import platform, sys; " +
        "print(sys.version_info.major, sys.version_info.minor, " +
        "platform.machine(), 64 if sys.maxsize > 2**32 else 32)"
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to inspect the build Python version and architecture."
    }
    $BuildPythonInfo = ([string]$BuildPythonInfoOutput).Trim() -split "\s+"
    if (
        $BuildPythonInfo.Count -ne 4 -or
        $BuildPythonInfo[0] -ne $RequestedPythonVersionParts[0] -or
        $BuildPythonInfo[1] -ne $RequestedPythonVersionParts[1] -or
        $BuildPythonInfo[2] -notmatch "^(AMD64|x86_64)$" -or
        $BuildPythonInfo[3] -ne "64"
    ) {
        throw (
            "The windows-x64 release requires Python $PythonVersion on x64; " +
            "selected interpreter reports '$BuildPythonInfoOutput'."
        )
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

    if (Test-Path -LiteralPath $ReleaseDirectory) {
        Remove-Item -LiteralPath $ReleaseDirectory -Recurse -Force
    }
    New-Item -ItemType Directory -Path $ReleaseDirectory -Force | Out-Null

    Get-ChildItem -LiteralPath $DistDirectory | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $ReleaseDirectory -Recurse -Force
    }

    foreach ($LauncherAssetName in $LauncherAssetNames) {
        Copy-Item `
            -LiteralPath (Join-Path $LauncherAssetsDirectory $LauncherAssetName) `
            -Destination (Join-Path $ReleaseDirectory $LauncherAssetName) `
            -Force
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

    foreach ($PreviousArchivePath in @($CandidateZipPath, $ZipPath, $ZipChecksumPath)) {
        if (Test-Path -LiteralPath $PreviousArchivePath) {
            Remove-Item -LiteralPath $PreviousArchivePath -Force
        }
    }

    try {
        Compress-Archive `
            -Path (Join-Path $ReleaseDirectory "*") `
            -DestinationPath $CandidateZipPath `
            -CompressionLevel Optimal

        Write-Host ""
        Write-Host "Running extracted ZIP lifecycle smoke gate..."
        & $SmokeScriptPath -ZipPath $CandidateZipPath

        Move-Item -LiteralPath $CandidateZipPath -Destination $ZipPath
    }
    finally {
        if (Test-Path -LiteralPath $CandidateZipPath) {
            Remove-Item -LiteralPath $CandidateZipPath -Force
        }
    }

    $ZipHash = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
    [System.IO.File]::WriteAllText(
        $ZipChecksumPath,
        "$ZipHash *RainFlowSejong-windows-x64.zip`n",
        [System.Text.UTF8Encoding]::new($false)
    )

    Write-Host ""
    Write-Host "Validated Windows release created:"
    Write-Host "  Directory: $ReleaseDirectory"
    Write-Host "  Archive:   $ZipPath"
    Write-Host "  SHA256:    $ZipChecksumPath"
    Write-Host "Run release\windows-x64\start.bat on a clean Windows x64 PC."
}
finally {
    Pop-Location
}

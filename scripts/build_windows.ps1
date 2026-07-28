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

    foreach ($KnownArtifact in @("RainFlowSejong.exe", "_internal", "logs", "runtime", "SHA256SUMS.txt")) {
        $ArtifactPath = Join-Path $ReleaseDirectory $KnownArtifact
        if (Test-Path -LiteralPath $ArtifactPath) {
            Remove-Item -LiteralPath $ArtifactPath -Recurse -Force
        }
    }

    Get-ChildItem -LiteralPath $DistDirectory | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $ReleaseDirectory -Recurse -Force
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
    Write-Host "Run release\windows-x64\start.bat on a clean Windows x64 PC."
}
finally {
    Pop-Location
}

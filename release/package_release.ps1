<#
.SYNOPSIS
    RainFlow Sejong 제출용 패키징 스크립트 (Windows x64).

.DESCRIPTION
    노션 제출 계약대로 다음 산출물을 release\out\ 에 생성한다.
      - RainFlow-demo-windows-x64-<Version>.zip (즉시 실행본: RainFlow.exe,
        start_exe.bat, README_RUN.md 등 release\windows-x64\ 전체)
      - source-<Version>.zip (git archive HEAD 기준 소스 스냅샷)
      - SHA256SUMS.txt (위 두 zip의 SHA256)

    단계:
      1) build_windows.ps1을 호출해 release\windows-x64\ 를 새로 빌드한다.
      2) release\windows-x64\ 에 README_RUN.md와 start_exe.bat을 복사해 넣는다.
      3) release\windows-x64\ 전체를 zip으로 압축한다.
      4) git archive로 소스 zip을 만든다.
      5) 두 zip의 SHA256을 계산해 SHA256SUMS.txt에 기록한다.
      6) 데모 zip을 임시 폴더에 풀어 RainFlow.exe / start_exe.bat / README_RUN.md
         존재를 검증한다.

.PARAMETER Version
    산출물 파일명에 들어가는 버전 태그. 기본값 "v0.1.0-day2".

.NOTES
    저장소 루트에서 실행: powershell -ExecutionPolicy Bypass -File release\package_release.ps1
#>

param(
    [string]$Version = "v0.1.0-day2"
)

$ErrorActionPreference = "Stop"

$ReleaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ReleaseDir
Set-Location $RepoRoot

Write-Host "저장소 루트: $RepoRoot" -ForegroundColor Cyan
Write-Host "버전: $Version" -ForegroundColor Cyan

$OutDir = Join-Path $ReleaseDir "out"
$WinX64Dir = Join-Path $ReleaseDir "windows-x64"

# --- (a) fresh 빌드 ------------------------------------------------------------
Write-Host "`n[1/6] build_windows.ps1로 fresh 빌드" -ForegroundColor Cyan
& (Join-Path $ReleaseDir "build_windows.ps1")
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
    throw "build_windows.ps1 실패 (exit $LASTEXITCODE)"
}
if (-not (Test-Path (Join-Path $WinX64Dir "RainFlow.exe"))) {
    throw "빌드 산출물을 찾을 수 없다: $WinX64Dir\RainFlow.exe"
}

# --- (b) README_RUN.md, start_exe.bat 포함 --------------------------------------
Write-Host "`n[2/6] README_RUN.md / start_exe.bat 포함" -ForegroundColor Cyan
Copy-Item -Path (Join-Path $ReleaseDir "README_RUN.md") -Destination $WinX64Dir -Force
Copy-Item -Path (Join-Path $ReleaseDir "start_exe.bat") -Destination $WinX64Dir -Force

# --- out 디렉토리 준비 -----------------------------------------------------------
if (Test-Path $OutDir) {
    Remove-Item -Recurse -Force $OutDir
}
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

# --- (c) 데모 zip 압축 -----------------------------------------------------------
Write-Host "`n[3/6] 데모 zip 압축" -ForegroundColor Cyan
$DemoZipName = "RainFlow-demo-windows-x64-$Version.zip"
$DemoZipPath = Join-Path $OutDir $DemoZipName
if (Test-Path $DemoZipPath) {
    Remove-Item -Force $DemoZipPath
}
Compress-Archive -Path (Join-Path $WinX64Dir "*") -DestinationPath $DemoZipPath -CompressionLevel Optimal
if (-not (Test-Path $DemoZipPath)) {
    throw "데모 zip 생성 실패: $DemoZipPath"
}
Write-Host "생성: $DemoZipPath"

# --- (d) 소스 zip (git archive) --------------------------------------------------
Write-Host "`n[4/6] git archive로 소스 zip 생성" -ForegroundColor Cyan
$SourceZipName = "source-$Version.zip"
$SourceZipPath = Join-Path $OutDir $SourceZipName
if (Test-Path $SourceZipPath) {
    Remove-Item -Force $SourceZipPath
}
git archive --format=zip -o $SourceZipPath HEAD
if ($LASTEXITCODE -ne 0) {
    throw "git archive 실패 (exit $LASTEXITCODE)"
}
if (-not (Test-Path $SourceZipPath)) {
    throw "소스 zip 생성 실패: $SourceZipPath"
}
Write-Host "생성: $SourceZipPath"

# --- (e) SHA256 체크섬 -----------------------------------------------------------
Write-Host "`n[5/6] SHA256 체크섬 계산" -ForegroundColor Cyan
$ChecksumPath = Join-Path $OutDir "SHA256SUMS.txt"
$DemoHash = (Get-FileHash -Path $DemoZipPath -Algorithm SHA256).Hash.ToLower()
$SourceHash = (Get-FileHash -Path $SourceZipPath -Algorithm SHA256).Hash.ToLower()

$ChecksumLines = @(
    "$DemoHash  $DemoZipName",
    "$SourceHash  $SourceZipName"
)
# Windows PowerShell 5.1의 Set-Content는 utf8NoBOM을 지원하지 않으므로
# .NET API로 직접 BOM 없는 UTF-8로 기록한다.
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($ChecksumPath, $ChecksumLines, $Utf8NoBom)
Write-Host "생성: $ChecksumPath"
$ChecksumLines | ForEach-Object { Write-Host "  $_" }

# --- (f) 압축 해제 검증 ------------------------------------------------------------
Write-Host "`n[6/6] 데모 zip 압축 해제 검증" -ForegroundColor Cyan
$VerifyDir = Join-Path ([System.IO.Path]::GetTempPath()) ("rainflow_pkg_verify_" + [System.Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $VerifyDir -Force | Out-Null
try {
    Expand-Archive -Path $DemoZipPath -DestinationPath $VerifyDir -Force

    $RequiredFiles = @("RainFlow.exe", "start_exe.bat", "README_RUN.md")
    $MissingFiles = @()
    foreach ($f in $RequiredFiles) {
        $p = Join-Path $VerifyDir $f
        if (-not (Test-Path $p)) {
            $MissingFiles += $f
        }
    }

    if ($MissingFiles.Count -gt 0) {
        throw "압축 해제 검증 실패, 누락된 파일: $($MissingFiles -join ', ')"
    }

    Write-Host "검증 통과: RainFlow.exe, start_exe.bat, README_RUN.md 모두 존재" -ForegroundColor Green
}
finally {
    Remove-Item -Recurse -Force $VerifyDir -ErrorAction SilentlyContinue
}

# --- 결과 요약 ----------------------------------------------------------------
Write-Host "`n===== 패키징 완료 =====" -ForegroundColor Green
Write-Host "데모 zip: $DemoZipPath ($((Get-Item $DemoZipPath).Length) bytes)"
Write-Host "소스 zip: $SourceZipPath ($((Get-Item $SourceZipPath).Length) bytes)"
Write-Host "체크섬: $ChecksumPath"
Write-Host "SHA256 (demo):   $DemoHash"
Write-Host "SHA256 (source): $SourceHash"

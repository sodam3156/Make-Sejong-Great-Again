<#
.SYNOPSIS
    RainFlow Sejong Windows x64 실행 파일 빌드 (PyInstaller onedir).

.DESCRIPTION
    개발 PC에서 실행하는 빌드 스크립트다. 결과물은 최종 사용자에게 Python 설치
    없이 실행 가능한 release\windows-x64\ 폴더로 복사된다. release\start.bat은
    dev 모드(Python 필요)이고, 이 스크립트로 빌드한 exe는 Python이 필요 없다.

.NOTES
    저장소 루트에서 실행: powershell -ExecutionPolicy Bypass -File release\build_windows.ps1
#>

$ErrorActionPreference = "Stop"

# 이 스크립트가 release\ 안에 있다는 가정 하에 저장소 루트를 계산한다.
$ReleaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ReleaseDir

Write-Host "저장소 루트: $RepoRoot"
Set-Location $RepoRoot

Write-Host "`n[1/4] PyInstaller 설치 확인" -ForegroundColor Cyan
pip install pyinstaller
if ($LASTEXITCODE -ne 0) {
    throw "pip install pyinstaller 실패 (exit $LASTEXITCODE)"
}

Write-Host "`n[2/4] PyInstaller onedir 빌드" -ForegroundColor Cyan
pyinstaller `
    --noconfirm `
    --onedir `
    --name RainFlow `
    --paths . `
    --add-data "backend/fixtures;backend/fixtures" `
    --add-data "frontend;frontend" `
    "release/rainflow_entry.py"
if ($LASTEXITCODE -ne 0) {
    throw "pyinstaller 빌드 실패 (exit $LASTEXITCODE)"
}

Write-Host "`n[3/4] 산출물을 release\windows-x64\ 로 복사" -ForegroundColor Cyan
$DistDir = Join-Path $RepoRoot "dist\RainFlow"
$OutDir = Join-Path $ReleaseDir "windows-x64"

if (-not (Test-Path $DistDir)) {
    throw "PyInstaller 산출물을 찾을 수 없다: $DistDir"
}

if (Test-Path $OutDir) {
    Remove-Item -Recurse -Force $OutDir
}
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
Copy-Item -Path (Join-Path $DistDir "*") -Destination $OutDir -Recurse -Force

Write-Host "`n[4/4] exe 존재 확인" -ForegroundColor Cyan
$ExePath = Join-Path $OutDir "RainFlow.exe"
if (-not (Test-Path $ExePath)) {
    throw "빌드 실패: $ExePath 를 찾을 수 없다"
}

Write-Host "`n빌드 완료: $ExePath" -ForegroundColor Green
Write-Host "실행: `"$ExePath`" [PORT]  (PORT 생략 시 8000)"

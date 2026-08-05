# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller onedir build for the offline Windows x64 submission bundle."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, copy_metadata


REPOSITORY_ROOT = Path(SPECPATH).resolve()
FIXTURE_DIR = REPOSITORY_ROOT / "backend" / "fixtures"
CONTRACT_DIR = REPOSITORY_ROOT / "contracts"
FRONTEND_DIR = REPOSITORY_ROOT / "frontend"

for required_path in (
    FIXTURE_DIR,
    CONTRACT_DIR / "rainflow.schema.json",
    FRONTEND_DIR / "index.html",
):
    if not required_path.exists():
        raise SystemExit(f"required packaging input is missing: {required_path}")

datas = [
    (str(FIXTURE_DIR), "backend/fixtures"),
    (str(CONTRACT_DIR), "contracts"),
    (str(FRONTEND_DIR), "frontend"),
]
for distribution in ("fastapi", "starlette", "pydantic", "uvicorn"):
    datas += copy_metadata(distribution)

hiddenimports = sorted(
    set(
        collect_submodules("fastapi")
        + collect_submodules("starlette")
        + collect_submodules("uvicorn")
    )
)

a = Analysis(
    [str(REPOSITORY_ROOT / "launcher" / "run_rainflow.py")],
    pathex=[str(REPOSITORY_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "httpx", "jsonschema"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RainFlowSejong",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="RainFlowSejong",
)

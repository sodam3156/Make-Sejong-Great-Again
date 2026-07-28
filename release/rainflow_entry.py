"""RainFlow Sejong - PyInstaller onedir 엔트리포인트.

release/build_windows.ps1로 빌드된 RainFlow.exe가 실행하는 진입점이다.
PyInstaller onedir 번들에서는 이 파일 및 그 부속 데이터(--add-data로 넣은
backend/fixtures, frontend)가 sys._MEIPASS 아래에 풀린다. backend.app.main이
평소 저장소 루트 기준 상대경로로 fixtures/frontend를 찾으므로, 번들 안에서도
같은 경로 구조를 찾을 수 있도록 RAINFLOW_BASE_DIR 환경변수로 backend 폴더
위치를 알려준다 (backend/app/main.py의 BACKEND_DIR 오버라이드, 기존 동작 불변).

사용법 (빌드된 exe):
    RainFlow.exe [PORT]
    PORT 생략 시 8000.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def resolve_base_dir() -> Path:
    """PyInstaller 번들이면 _MEIPASS 아래, 아니면 이 파일의 저장소 루트 기준 경로."""
    if hasattr(sys, "_MEIPASS"):
        # --add-data "backend/fixtures;backend/fixtures" --add-data "frontend;frontend"
        # 로 넣었으므로 _MEIPASS/backend, _MEIPASS/frontend 구조가 그대로 유지된다.
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # 개발 환경에서 이 스크립트를 직접 실행하는 경우: release/ 상위가 저장소 루트
    return Path(__file__).resolve().parent.parent


def main() -> None:
    base_dir = resolve_base_dir()
    os.environ["RAINFLOW_BASE_DIR"] = str(base_dir / "backend")

    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"[경고] 잘못된 포트 인자 '{sys.argv[1]}', 기본값 8000 사용")

    # backend.app.main을 여기서 import해야 위의 RAINFLOW_BASE_DIR이 모듈 로드 시점에 반영된다.
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))

    import uvicorn
    from backend.app.main import app

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()

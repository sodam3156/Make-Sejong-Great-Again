"""Start the RainFlow Sejong ASGI server without any external service.

This module is deliberately separate from ``backend.app`` so packaging and
process concerns do not leak into the frozen API implementation.
"""
from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the offline RainFlow Sejong server")
    parser.add_argument(
        "--host",
        default=os.environ.get("RAINFLOW_HOST", "127.0.0.1"),
        help="bind address (default: RAINFLOW_HOST or 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        default=os.environ.get("RAINFLOW_PORT", "8000"),
        type=_port,
        help="bind port (default: RAINFLOW_PORT or 8000)",
    )
    parser.add_argument(
        "--log-level",
        choices=("critical", "error", "warning", "info", "debug", "trace"),
        default=os.environ.get("RAINFLOW_LOG_LEVEL", "info").lower(),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify bundled fixture/frontend imports and exit without starting a server",
    )
    return parser


def _self_check() -> int:
    from backend.app.main import BACKEND_DIR, FIXTURE_PATH, FRONTEND_DIR, health

    status = health()
    report = {
        "status": status.get("status"),
        "fixture_available": FIXTURE_PATH.is_file(),
        "frontend_available": (FRONTEND_DIR / "index.html").is_file(),
        "contract_available": (
            BACKEND_DIR.parent / "contracts" / "rainflow.schema.json"
        ).is_file(),
        "api_key_required": False,
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if all(
        (
            report["status"] == "ok",
            report["fixture_available"],
            report["frontend_available"],
            report["contract_available"],
        )
    ) else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.check:
        return _self_check()

    import uvicorn
    from backend.app.main import app

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        access_log=True,
        server_header=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

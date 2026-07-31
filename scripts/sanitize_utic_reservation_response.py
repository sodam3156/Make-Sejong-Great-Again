#!/usr/bin/env python3
"""Convert a UTIC JSON response body into a secret-free normalized fixture."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.app.utic_signal import normalize_reservation_response

SENSITIVE_TRANSCRIPT_MARKERS = (
    "serviceKey=",
    "UTIC_SERVICE_KEY",
    "Authorization:",
)


def load_response_body(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8-sig")
    lowered = raw.lower()
    for marker in SENSITIVE_TRANSCRIPT_MARKERS:
        if marker.lower() in lowered:
            raise ValueError(
                "input appears to contain a request URL, environment variable, or "
                "authorization transcript; save only the JSON response body"
            )
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ValueError("UTIC response body must be a JSON array")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="JSON response body only")
    parser.add_argument("output", type=Path, help="normalized output JSON")
    args = parser.parse_args()

    normalized = normalize_reservation_response(load_response_body(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"PASS: wrote {len(normalized['rows'])} normalized UTIC rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

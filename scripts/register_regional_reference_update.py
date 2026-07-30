#!/usr/bin/env python3
"""Register future official data without activating simulator parameters.

The command records raw-file provenance and can stage one canonical Sejong replacement
slot. It never edits simulation.py, BASE_DEMAND, capacities, storage, or control guards.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_CLASSES = {"observed", "regional_reference", "external_fixture"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def register_source(args: argparse.Namespace) -> None:
    if args.source_class not in ALLOWED_CLASSES:
        raise SystemExit(f"unsupported source class: {args.source_class}")
    manifest = load(args.manifest)
    record = {
        "source_id": args.source_id,
        "filename": args.file.name,
        "available": True,
        "bytes": args.file.stat().st_size,
        "sha256": sha256_file(args.file),
        "source_class": args.source_class,
        "source_region": args.region,
        "received_at": args.received_at,
        "review_status": "received_pending_qa",
        "runtime_activation": "disabled",
    }
    incoming = manifest.setdefault("incoming_sources", [])
    incoming[:] = [row for row in incoming if row.get("source_id") != args.source_id]
    incoming.append(record)
    manifest["runtime_activation"] = "disabled"
    dump(args.manifest, manifest)
    print(json.dumps(record, ensure_ascii=False, indent=2))


def attach_slot(args: argparse.Namespace) -> None:
    handoff = load(args.handoff)
    slot = next((row for row in handoff.get("replacement_slots", []) if row.get("slot") == args.slot), None)
    if slot is None:
        raise SystemExit(f"unknown replacement slot: {args.slot}")
    payload = load(args.input)
    rows = payload if isinstance(payload, list) else payload.get("rows", [payload])
    if not rows or not all(isinstance(row, dict) for row in rows):
        raise SystemExit("canonical input must be an object, a list of objects, or {'rows': [...]}")
    required = set(slot.get("required_fields", []))
    missing = sorted({field for row in rows for field in required if field not in row})
    if missing:
        raise SystemExit(f"missing canonical fields: {', '.join(missing)}")
    output = args.output or args.handoff.parent / f"{args.slot}.candidate.json"
    staged = {
        "dataset_id": f"{args.slot}-candidate-v1",
        "source_class": "observed",
        "runtime_activation": "disabled",
        "review_status": "qa_pass_required",
        "rows": rows,
    }
    dump(output, staged)
    slot.update(
        {
            "status": "received_pending_qa",
            "candidate_path": output.name,
            "candidate_sha256": sha256_file(output),
        }
    )
    handoff["runtime_activation"] = "disabled"
    dump(args.handoff, handoff)
    print(f"staged {args.slot} at {output}; runtime remains disabled")


def write_status(args: argparse.Namespace) -> None:
    manifest = load(args.manifest)
    handoff = load(args.handoff)
    status = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime_activation": "disabled",
        "available_reference_sources": [row["source_id"] for row in manifest.get("sources", []) if row.get("available")],
        "incoming_sources": manifest.get("incoming_sources", []),
        "replacement_slots": [
            {"slot": row["slot"], "status": row["status"]}
            for row in handoff.get("replacement_slots", [])
        ],
    }
    dump(args.output, status)
    print(args.output)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    register = sub.add_parser("register-source")
    register.add_argument("--manifest", type=Path, required=True)
    register.add_argument("--file", type=Path, required=True)
    register.add_argument("--source-id", required=True)
    register.add_argument("--source-class", required=True)
    register.add_argument("--region", required=True)
    register.add_argument("--received-at", required=True)
    register.set_defaults(handler=register_source)

    attach = sub.add_parser("attach-slot")
    attach.add_argument("--handoff", type=Path, required=True)
    attach.add_argument("--slot", required=True)
    attach.add_argument("--input", type=Path, required=True)
    attach.add_argument("--output", type=Path)
    attach.set_defaults(handler=attach_slot)

    status = sub.add_parser("write-status")
    status.add_argument("--manifest", type=Path, required=True)
    status.add_argument("--handoff", type=Path, required=True)
    status.add_argument("--output", type=Path, required=True)
    status.set_defaults(handler=write_status)

    args = parser.parse_args()
    args.handler(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Small local persistence and structured audit log for offline replay."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

KST = timezone(timedelta(hours=9))


class RunStore:
    def __init__(self, logs_dir: Path) -> None:
        self.logs_dir = logs_dir
        self.runs_dir = logs_dir / "runs"
        self.audit_path = logs_dir / "audit.jsonl"

    def _ensure(self) -> None:
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_run_id(run_id: str) -> str:
        if not run_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in run_id):
            raise ValueError("invalid run_id")
        return run_id

    def save(self, run: dict[str, Any]) -> None:
        self._ensure()
        run_id = self._safe_run_id(str(run["run_id"]))
        target = self.runs_dir / f"{run_id}.json"
        temporary = self.runs_dir / f".{run_id}.tmp"
        temporary.write_text(
            json.dumps(run, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(target)

    def load(self, run_id: str) -> dict[str, Any] | None:
        self._ensure()
        target = self.runs_dir / f"{self._safe_run_id(run_id)}.json"
        if not target.exists():
            return None
        return json.loads(target.read_text(encoding="utf-8"))

    def count(self) -> int:
        self._ensure()
        return sum(1 for _ in self.runs_dir.glob("*.json"))

    def audit(self, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._ensure()
        record = {
            "ts": datetime.now(KST).isoformat(),
            "event": event,
            **payload,
        }
        with self.audit_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return record

    def audit_for_run(self, run_id: str) -> list[dict[str, Any]]:
        self._safe_run_id(run_id)
        if not self.audit_path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in self.audit_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("run_id") == run_id:
                records.append(record)
        return records

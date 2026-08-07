#!/usr/bin/env python3
"""Validate external public-data request and response-handoff requirements."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Any

EXPECTED_REQUEST_IDS = {
    "IR-TRAFFIC-2025",
    "IR-TRAFFIC-2026",
    "IR-SIGNAL-CHANGE-2026",
    "IR-SIGNAL-OPS-2026",
    "IR-CORRIDOR-LATEST",
}
PENDING_STATUSES = {
    "preparing",
    "department_assignment_pending",
    "processing",
    "transferred",
}
RESPONSE_STATUSES = {
    "disclosed",
    "partially_disclosed",
    "not_disclosed",
    "information_not_held",
    "withdrawn",
}
FORBIDDEN_PUBLIC_KEYS = {
    "receipt_number",
    "portal_password",
    "auth_key",
    "api_key",
    "controller_ip",
    "controller_account",
    "personal_phone",
    "personal_email",
}
TRAFFIC_CHECKS = {
    "sha256",
    "date_coverage",
    "time_resolution",
    "timezone",
    "intersection_identity",
    "direction_semantics",
    "units",
    "missing_rate",
}
SIGNAL_CHECKS = {
    "sha256",
    "effective_date",
    "intersection_identity",
    "cycle",
    "phase_order",
    "effective_green",
    "clearance",
    "offset",
}
GEOMETRY_CHECKS = {
    "lane_count",
    "usable_queue_length",
    "lane_use",
    "stop_line",
}


@dataclass(frozen=True)
class CatalogResult:
    status: str
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ok"] = self.ok
        return payload


def _walk_forbidden_keys(value: Any, path: str = "root") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_PUBLIC_KEYS:
                found.append(f"{path}.{key}")
            found.extend(_walk_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_walk_forbidden_keys(child, f"{path}[{index}]"))
    return found


def validate_catalog(catalog: dict[str, Any]) -> CatalogResult:
    errors: list[str] = []
    warnings: list[str] = []

    if catalog.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    try:
        date.fromisoformat(str(catalog.get("status_as_of")))
    except ValueError:
        errors.append("status_as_of must use YYYY-MM-DD")
    if catalog.get("model_activation_policy") != "never_automatic":
        errors.append("external responses must never activate model inputs automatically")

    forbidden_paths = _walk_forbidden_keys(catalog)
    if forbidden_paths:
        errors.append(f"forbidden sensitive public fields: {forbidden_paths}")

    allowed_statuses = set(catalog.get("allowed_statuses", []))
    if not PENDING_STATUSES | RESPONSE_STATUSES <= allowed_statuses:
        errors.append("allowed_statuses is incomplete")

    requests = catalog.get("requests")
    if not isinstance(requests, list) or not requests:
        return CatalogResult("FAIL", [*errors, "requests must be non-empty"], warnings)

    ids: list[str] = []
    for index, request in enumerate(requests):
        if not isinstance(request, dict):
            errors.append(f"requests[{index}] must be an object")
            continue
        request_id = request.get("request_id")
        if not isinstance(request_id, str):
            errors.append(f"requests[{index}].request_id must be a string")
            continue
        ids.append(request_id)
        status = request.get("current_status")
        received = request.get("response_received")
        checks = set(request.get("acceptance_checks", []))
        use_cases = set(request.get("use_cases", []))

        if status not in allowed_statuses:
            errors.append(f"{request_id}: invalid current_status {status!r}")
        if not isinstance(received, bool):
            errors.append(f"{request_id}: response_received must be boolean")
        if status in PENDING_STATUSES and received:
            errors.append(f"{request_id}: pending status cannot claim response_received")
        if status in RESPONSE_STATUSES and not received:
            errors.append(f"{request_id}: terminal response status requires response_received")
        if request.get("storage_path") != f"data/public/information_requests/{request_id}/":
            errors.append(f"{request_id}: storage_path does not match request_id")
        if not request.get("requested_products"):
            errors.append(f"{request_id}: requested_products must not be empty")
        if not checks:
            errors.append(f"{request_id}: acceptance_checks must not be empty")
        if not request.get("claim_limit_before_acceptance"):
            errors.append(f"{request_id}: claim limit is required")

        if any("traffic" in use_case or "demand" in use_case for use_case in use_cases):
            missing = sorted(TRAFFIC_CHECKS - checks)
            if missing:
                errors.append(f"{request_id}: missing traffic acceptance checks {missing}")

        # A dedicated signal-contract request must contain the full operating-plan
        # acceptance set. The corridor request asks for signal fields only when the
        # agency happens to hold them, so absence is a warning until a response is
        # received and its contents are classified.
        if "signal_model_contract_if_scope_changes" in use_cases:
            missing = sorted(SIGNAL_CHECKS - checks)
            if missing:
                errors.append(f"{request_id}: missing signal acceptance checks {missing}")
        elif "signal_model_if_provided" in use_cases and not SIGNAL_CHECKS <= checks:
            warnings.append(
                f"{request_id} has optional signal content; any received signal files require a separate full signal acceptance check"
            )

        if "lane_and_storage_geometry" in use_cases:
            missing = sorted(GEOMETRY_CHECKS - checks)
            if missing:
                errors.append(f"{request_id}: missing geometry acceptance checks {missing}")

        if status in PENDING_STATUSES:
            warnings.append(f"{request_id} remains pending; no response-derived claim is allowed")

    if len(ids) != len(set(ids)):
        errors.append("request_id values must be unique")
    missing_ids = sorted(EXPECTED_REQUEST_IDS - set(ids))
    extra_ids = sorted(set(ids) - EXPECTED_REQUEST_IDS)
    if missing_ids:
        errors.append(f"missing tracked requests: {missing_ids}")
    if extra_ids:
        errors.append(f"unregistered request ids: {extra_ids}")

    handoff = catalog.get("response_handoff_requirements")
    if not isinstance(handoff, dict):
        errors.append("response_handoff_requirements must be an object")
    else:
        for key in (
            "user_should_provide",
            "user_should_not_provide",
            "processing_after_receipt",
        ):
            if not isinstance(handoff.get(key), list) or not handoff[key]:
                errors.append(f"response_handoff_requirements.{key} must be non-empty")

    return CatalogResult("PASS" if not errors else "FAIL", errors, warnings)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    result = validate_catalog(catalog)
    rendered = json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

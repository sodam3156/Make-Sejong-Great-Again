"""Standalone read-only API for Sejong observed-constraint evidence.

Run with:
    uvicorn backend.sejong_constraints_api:app --host 127.0.0.1 --port 8012

This application cannot alter simulator parameters or approvals.
"""
from __future__ import annotations

from fastapi import FastAPI

from backend.app.sejong_observed_constraints import router

app = FastAPI(
    title="RainFlow Sejong Observed-Constraint API",
    version="0.1.0",
    description=(
        "Official historical geometry and signal evidence, exclusion decisions, "
        "and runtime activation blockers. Not a field-replay API."
    ),
)
app.include_router(router)


@app.get("/api/reference/sejong-constraints-health", summary="세종 관측 제약 근거 API 준비 상태")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "mode": "read_only",
        "runtime_activation": "disabled",
        "field_calibration": "hard_blocked",
    }

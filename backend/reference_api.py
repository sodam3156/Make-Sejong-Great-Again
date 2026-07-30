"""Standalone read-only API for regional reference and adapter fixture data.

Run with:
    uvicorn backend.reference_api:app --host 127.0.0.1 --port 8011

This app is deliberately separate from the simulation API and cannot change simulator
parameters or submit approvals.
"""
from __future__ import annotations

from fastapi import FastAPI

from backend.app.reference_data import router

app = FastAPI(
    title="RainFlow Regional Reference API",
    version="0.1.0",
    description=(
        "Read-only regional reference and external fixture data. "
        "Not a Sejong field replay or calibration API."
    ),
)
app.include_router(router)


@app.get("/api/reference/health", summary="참조자료 API 준비 상태")
def reference_health() -> dict[str, str]:
    return {
        "status": "ok",
        "mode": "read_only",
        "runtime_activation": "disabled",
    }

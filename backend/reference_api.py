"""Standalone read-only API for regional reference and adapter fixture data.

Run with:
    uvicorn backend.reference_api:app --host 127.0.0.1 --port 8011

This app is deliberately separate from the simulation API and cannot change simulator
parameters or submit approvals.
"""
from __future__ import annotations

from fastapi import FastAPI

from backend.app.reference_data import router as reference_router
from backend.app.sejong_nodelink_reference import router as sejong_nodelink_router
from backend.app.utic_reference import router as utic_router

app = FastAPI(
    title="RainFlow Regional Reference API",
    version="0.3.0",
    description=(
        "Read-only regional reference and external fixture data. "
        "Not a Sejong field replay or calibration API."
    ),
)
app.include_router(reference_router)
app.include_router(sejong_nodelink_router)
app.include_router(utic_router)


@app.get("/api/reference/health", summary="참조자료 API 준비 상태")
def reference_health() -> dict[str, str]:
    return {
        "status": "ok",
        "mode": "read_only",
        "runtime_activation": "disabled",
    }

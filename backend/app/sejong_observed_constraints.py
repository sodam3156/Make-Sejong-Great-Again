"""Read-only evidence API for Sejong observed-constraint inputs.

The endpoints expose official historical geometry and signal evidence plus explicit
exclusion and activation gates. They cannot mutate the simulator or activate a dataset.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "data" / "observed" / "sejong_constraints"

router = APIRouter(prefix="/api/reference", tags=["sejong-observed-constraints"])


def _load(filename: str) -> dict[str, Any]:
    path = PACKAGE_ROOT / filename
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Sejong observed-constraint evidence unavailable: {filename}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid evidence document: {filename}")
    return value


@lru_cache(maxsize=1)
def sejong_hdmap_status() -> dict[str, Any]:
    return _load("sejong_hdmap_status_20260731.json")


@lru_cache(maxsize=1)
def sejong_historical_signal_plan() -> dict[str, Any]:
    return _load("sejong_historical_signal_plan_2023.json")


@lru_cache(maxsize=1)
def sejong_probe_exclusion() -> dict[str, Any]:
    return _load("sejong_probe_exclusion_20260731.json")


@lru_cache(maxsize=1)
def sejong_observed_input_status() -> dict[str, Any]:
    return _load("sejong_observed_input_gate_20260731.json")


def _serve(loader: Any) -> dict[str, Any]:
    try:
        return loader()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail="Sejong evidence package unavailable") from error


@router.get("/sejong-hdmap-status", summary="세종 정밀도로지도 공간 커버리지와 활성화 차단 상태")
def get_sejong_hdmap_status() -> dict[str, Any]:
    return _serve(sejong_hdmap_status)


@router.get("/sejong-historical-signal-plan", summary="대상 교차로 2023년 역사적 신호 등화시간 벡터")
def get_sejong_historical_signal_plan() -> dict[str, Any]:
    return _serve(sejong_historical_signal_plan)


@router.get("/sejong-probe-exclusion", summary="B0·PVD 대상 회랑 미중첩 제외 근거")
def get_sejong_probe_exclusion() -> dict[str, Any]:
    return _serve(sejong_probe_exclusion)


@router.get("/sejong-observed-input-status", summary="관측 제약 입력 준비도와 런타임 하드 블로커")
def get_sejong_observed_input_status() -> dict[str, Any]:
    return _serve(sejong_observed_input_status)

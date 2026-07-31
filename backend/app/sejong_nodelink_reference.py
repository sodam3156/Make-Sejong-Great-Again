"""Read-only status endpoint for the officially distributed Sejong NODE/LINK extract."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

ROOT = Path(__file__).resolve().parents[2]
STATUS_PATH = (
    ROOT
    / "data"
    / "observed"
    / "regional_reference"
    / "sejong_nodelink_reverification_20260731.json"
)

router = APIRouter(prefix="/api/reference", tags=["reference-data"])


@lru_cache(maxsize=1)
def sejong_nodelink_status() -> dict[str, Any]:
    try:
        data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise RuntimeError("Sejong NODE/LINK status unavailable") from error

    return {
        "datasetId": data["dataset_id"],
        "sourceClass": data["source_class"],
        "sourceSha256": data["source_sha256"],
        "regionPrefix": data["filter"]["node_id_prefix"],
        "nodeCount": data["filter"]["node_count"],
        "linkCount": data["filter"]["link_count"],
        "targetIntersections": data["target_intersections"],
        "directedCorridorRoutes": data["directed_corridor_routes"],
        "usableFor": data["usable_for"],
        "notUsableFor": data["not_usable_for"],
        "runtimeActivation": data["runtime_activation"],
        "usableForCalibration": data["usable_for_calibration"],
    }


@router.get(
    "/sejong-nodelink-status",
    summary="세종 413 표준 NODE/LINK 추출·회랑 검증 상태",
)
def get_sejong_nodelink_status() -> dict[str, Any]:
    try:
        return sejong_nodelink_status()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

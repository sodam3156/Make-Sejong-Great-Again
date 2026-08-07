"""Read-only status and display geometry for the official Sejong NODE/LINK extract."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "data" / "observed" / "regional_reference"
STATUS_PATH = PACKAGE_ROOT / "sejong_nodelink_reverification_20260731.json"
DISPLAY_PATH = PACKAGE_ROOT / "sejong_corridor_display.geojson"

router = APIRouter(prefix="/api/reference", tags=["reference-data"])


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise RuntimeError(f"reference data unavailable: {path.name}") from error


@lru_cache(maxsize=1)
def sejong_nodelink_status() -> dict[str, Any]:
    data = _load_json(STATUS_PATH)
    display = _load_json(DISPLAY_PATH)

    return {
        "datasetId": data["dataset_id"],
        "sourceClass": data["source_class"],
        "sourceSha256": data["source_sha256"],
        "regionPrefix": data["filter"]["node_id_prefix"],
        "nodeCount": data["filter"]["node_count"],
        "linkCount": data["filter"]["link_count"],
        "targetIntersections": data["target_intersections"],
        "directedCorridorRoutes": data["directed_corridor_routes"],
        "displayGeometry": display,
        "usableFor": data["usable_for"],
        "notUsableFor": data["not_usable_for"],
        "runtimeActivation": data["runtime_activation"],
        "usableForCalibration": data["usable_for_calibration"],
        "modelAlignment": {
            "originalModelScope": "synthetic_three_roundabout_corridor",
            "currentObservedDisplayCorridor": "성금교차로-청사교차로-세종교차로",
            "intersectionFormEncodedInNodeLink": False,
            "status": "SPATIAL_REFERENCE_ONLY_MODEL_MECHANICS_UNALIGNED",
            "requiredPresentationLabel": "신호 미모델링 합성 큐 회랑",
            "roundaboutDataRequiredForCurrentCorridor": False,
            "roundaboutDataRequiredOnlyWhen": (
                "the project explicitly switches back to an actual or synthetic roundabout variant"
            ),
        },
        "limitations": display["limitations"],
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

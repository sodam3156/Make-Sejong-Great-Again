"""Build a small, deterministic Unity map from the public Sejong GeoJSON."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "public" / "2026-07-29" / "sejong_nodelink_link.geojson"
OUTPUT = (
    ROOT
    / "unity"
    / "RainFlowGame"
    / "Assets"
    / "StreamingAssets"
    / "map"
    / "eojin_map.json"
)

ORIGIN = (127.2785, 36.5040)
BBOX = (127.2550, 36.4950, 127.3020, 36.5130)
REGIONS = (
    ("seonggeum_cheongsa", "성금–청사 생활권", 127.2638, 36.5019),
    ("cheongsa_sejong", "청사–세종 생활권", 127.2826, 36.5048),
    ("eojin_corridor", "어진동 통합 회랑", 127.2734, 36.5035),
)


def _inside(point: list[float]) -> bool:
    lon, lat = point
    west, south, east, north = BBOX
    return west <= lon <= east and south <= lat <= north


def _meters(lon: float, lat: float) -> list[float]:
    origin_lon, origin_lat = ORIGIN
    x = (lon - origin_lon) * 111_320.0 * math.cos(math.radians(origin_lat))
    y = (lat - origin_lat) * 110_540.0
    return [round(x, 2), round(y, 2)]


def _deduplicate(points: list[list[float]]) -> list[list[float]]:
    result: list[list[float]] = []
    for point in points:
        projected = _meters(point[0], point[1])
        if not result or projected != result[-1]:
            result.append(projected)
    return result


def render() -> str:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    roads = []
    for feature in source["features"]:
        geometry = feature.get("geometry") or {}
        if geometry.get("type") != "LineString":
            continue
        coordinates = geometry.get("coordinates") or []
        if len(coordinates) < 2 or not any(_inside(point) for point in coordinates):
            continue
        points = _deduplicate(coordinates)
        if len(points) < 2:
            continue
        properties = feature.get("properties") or {}
        roads.append(
            {
                "road_id": str(properties.get("LINK_ID", "")),
                "name": str(properties.get("ROAD_NAME") or "이름 없는 도로"),
                "lanes": int(properties.get("LANES") or 1),
                "rank": str(properties.get("ROAD_RANK") or ""),
                "max_speed_kph": int(properties.get("MAX_SPD") or 0),
                "points": points,
            }
        )
    roads.sort(key=lambda road: road["road_id"])
    payload = {
        "map_version": "eojin-game-map-v1",
        "source": "국가교통정보센터 전국표준노드링크 2026-07-16",
        "reality_level": "game",
        "note": "실제 도로 형상을 단순화한 게임 지도이며 신호 현시와 수요는 합성값입니다.",
        "origin": {"longitude": ORIGIN[0], "latitude": ORIGIN[1]},
        "bounds": {
            "west": BBOX[0],
            "south": BBOX[1],
            "east": BBOX[2],
            "north": BBOX[3],
        },
        "regions": [
            {
                "region_id": region_id,
                "label": label,
                "position": _meters(lon, lat),
            }
            for region_id, label, lon, lat in REGIONS
        ],
        "roads": roads,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"{OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

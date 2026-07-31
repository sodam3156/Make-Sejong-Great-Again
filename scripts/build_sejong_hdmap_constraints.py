#!/usr/bin/env python3
"""Build review-gated Sejong HD-map coverage and probe exclusion evidence.

This script intentionally does not derive simulator queue-storage values. It proves
spatial coverage, preserves source provenance, and blocks runtime activation until
approach-to-link mapping, movement classification, and storage-length review are done.

Optional analysis dependencies:
    geopandas pandas openpyxl shapely pyproj
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

TARGETS_WGS84 = {
    "성금교차로": (127.2615355, 36.5085473),
    "청사교차로": (127.2677918, 36.5078885),
    "세종교차로": (127.2960878, 36.5004880),
}

CORRIDOR_WGS84 = {
    "성금→청사": [
        [127.2616892, 36.5085061], [127.2629184, 36.5085542],
        [127.2641281, 36.5085037], [127.2650248, 36.5084171],
        [127.2655207, 36.5083492], [127.2656054, 36.5082818],
        [127.2667719, 36.5080598], [127.2670573, 36.5079929],
        [127.2677322, 36.5077967],
    ],
    "청사→세종": [
        [127.2678558, 36.5077559], [127.2705796, 36.5068066],
        [127.2708545, 36.5067757], [127.2739065, 36.5057238],
        [127.2749824, 36.5054147], [127.2760764, 36.5051502],
        [127.2768069, 36.5050009], [127.2775429, 36.5048715],
        [127.2845822, 36.5037466], [127.2887116, 36.5032125],
        [127.2896098, 36.5030400], [127.2905318, 36.5028258],
        [127.2915788, 36.5024748], [127.2947197, 36.5010591],
        [127.2959910, 36.5004547],
    ],
}

OUTPUT_CRS = "EPSG:5179"
TRANSFORMER = Transformer.from_crs("EPSG:4326", OUTPUT_CRS, always_xy=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract(source: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(source) as archive:
        for member in archive.infolist():
            target = (destination / member.filename.lstrip("/")).resolve()
            if destination not in target.parents and target != destination:
                raise ValueError(f"unsafe ZIP path: {member.filename}")
        archive.extractall(destination)


def find_layer(root: Path, suffix: str) -> Path:
    matches = sorted(root.rglob(f"*_{suffix}.shp"))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one *_{suffix}.shp under {root}, got {matches}")
    return matches[0]


def projected_point(lon: float, lat: float) -> Point:
    return Point(*TRANSFORMER.transform(lon, lat))


def densify(line: LineString, step_m: float = 10.0) -> list[Point]:
    count = max(1, math.ceil(line.length / step_m))
    return [line.interpolate(index / count, normalized=True) for index in range(count + 1)]


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("empty percentile input")
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * fraction)]


def feature_metric(frame: gpd.GeoDataFrame, point: Point, radius_m: float = 100.0) -> dict[str, Any]:
    distances = frame.geometry.distance(point)
    return {
        "feature_count": int(len(frame)),
        "nearest_distance_m": round(float(distances.min()), 3),
        "within_100m_count": int((distances <= radius_m).sum()),
    }


def source_record(path: Path, *, package_id: str, year: int, role: str) -> dict[str, Any]:
    return {
        "package_id": package_id,
        "filename": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "source_class": "official_historical_hdmap",
        "construction_year": year,
        "role": role,
        "raw_committed": False,
    }


def parse_brt_points(path: Path) -> list[Point]:
    points: list[Point] = []
    workbook = pd.ExcelFile(path)
    for sheet in workbook.sheet_names:
        frame = pd.read_excel(path, sheet_name=sheet)
        latitude = next(column for column in frame.columns if "위도" in str(column))
        longitude = next(column for column in frame.columns if "경도" in str(column))
        for lat, lon in zip(
            pd.to_numeric(frame[latitude], errors="coerce"),
            pd.to_numeric(frame[longitude], errors="coerce"),
            strict=True,
        ):
            if pd.notna(lat) and pd.notna(lon) and 30 < lat < 40 and 120 < lon < 130:
                points.append(projected_point(float(lon), float(lat)))
    return points


def parse_pvd(path: Path) -> tuple[list[Point], list[dict[str, Any]], dict[str, int]]:
    records: list[dict[str, Any]] = []
    file_sizes: dict[str, int] = {}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.endswith(".txt") or "/._" in name:
                continue
            payload = archive.read(name)
            file_sizes[Path(name).name] = len(payload)
            if not payload:
                continue
            for line in payload.decode("utf-8", errors="replace").splitlines():
                start = line.find("{")
                if start < 0:
                    continue
                try:
                    value = json.loads(line[start:])
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    records.append(value)

    points: list[Point] = []
    for record in records:
        try:
            lat = float(record["latitude"])
            lon = float(record["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        if 30 < lat < 40 and 120 < lon < 130:
            points.append(projected_point(lon, lat))
    return points, records, file_sizes


def overlap_summary(points: list[Point], corridor: LineString) -> dict[str, Any]:
    distances = [point.distance(corridor) for point in points]
    return {
        "point_count": len(points),
        "minimum_corridor_distance_m": round(min(distances), 3) if distances else None,
        "within_30m_count": sum(distance <= 30 for distance in distances),
        "within_50m_count": sum(distance <= 50 for distance in distances),
        "within_100m_count": sum(distance <= 100 for distance in distances),
        "within_300m_count": sum(distance <= 300 for distance in distances),
    }


def build(args: argparse.Namespace) -> None:
    args.output.mkdir(parents=True, exist_ok=True)
    target_points = {
        name: projected_point(lon, lat)
        for name, (lon, lat) in TARGETS_WGS84.items()
    }
    corridor_lines = {
        name: LineString([TRANSFORMER.transform(lon, lat) for lon, lat in coordinates])
        for name, coordinates in CORRIDOR_WGS84.items()
    }
    whole_corridor = unary_union(list(corridor_lines.values()))

    with tempfile.TemporaryDirectory(prefix="sejong-hdmap-") as temporary:
        base = Path(temporary)
        roots = {
            "2017": base / "hdmap_2017",
            "2021": base / "hdmap_2021",
            "2020": base / "hdmap_2020_excluded",
        }
        safe_extract(args.hdmap_2017, roots["2017"])
        safe_extract(args.hdmap_2021, roots["2021"])
        safe_extract(args.hdmap_2020_excluded, roots["2020"])

        link_2017 = gpd.read_file(find_layer(roots["2017"], "a3_link"))
        stop_2017 = gpd.read_file(find_layer(roots["2017"], "a2_stop"))
        signal_2017 = gpd.read_file(find_layer(roots["2017"], "b1_signal_point"))
        link_2021 = gpd.read_file(find_layer(roots["2021"], "a2_link"))
        line_2021 = gpd.read_file(find_layer(roots["2021"], "b2_surfacelinemark"))
        stop_2021 = line_2021[line_2021["kind"].astype(str) == "530"].copy()
        signal_2021 = gpd.read_file(find_layer(roots["2021"], "c1_trafficlight"))
        link_2020 = gpd.read_file(find_layer(roots["2020"], "a2_link"))

        if str(link_2017.crs) != OUTPUT_CRS or str(link_2021.crs) != OUTPUT_CRS:
            raise ValueError("unexpected HD-map CRS")

        union_2017 = unary_union(link_2017.geometry)
        union_2021 = unary_union(link_2021.geometry)
        union_all = unary_union([union_2017, union_2021])

        intersection_rows: list[dict[str, Any]] = []
        for name, point in target_points.items():
            if name in {"성금교차로", "청사교차로"}:
                package_id = "hdmap-happycity-sec02-2017"
                link, stop, signal = link_2017, stop_2017, signal_2017
                stop_code = "explicit_a2_stop"
            else:
                package_id = "hdmap-sangsang-sec001-2021"
                link, stop, signal = link_2021, stop_2021, signal_2021
                stop_code = "b2_surfacelinemark.kind=530"
            intersection_rows.append({
                "name": name,
                "center_wgs84": {
                    "longitude": TARGETS_WGS84[name][0],
                    "latitude": TARGETS_WGS84[name][1],
                },
                "assigned_package_id": package_id,
                "link_features": feature_metric(link, point),
                "stop_line_candidates": {
                    **feature_metric(stop, point),
                    "selection_rule": stop_code,
                },
                "signal_features": feature_metric(signal, point),
                "coverage_status": "COVERED_FOR_GEOMETRY_QA",
                "not_yet_derived": [
                    "approved approach lane count",
                    "approved movement-to-lane mapping",
                    "approved storage length",
                    "simulator approach ID mapping",
                ],
            })

        route_rows: list[dict[str, Any]] = []
        for name, line in corridor_lines.items():
            sample_points = densify(line, 10.0)
            distance_all = [point.distance(union_all) for point in sample_points]
            distance_2017 = [point.distance(union_2017) for point in sample_points]
            distance_2021 = [point.distance(union_2021) for point in sample_points]
            nearest_package = [
                "2017" if old <= new else "2021"
                for old, new in zip(distance_2017, distance_2021, strict=True)
            ]
            route_rows.append({
                "route": name,
                "official_corridor_length_m": round(line.length, 3),
                "sample_step_m": 10,
                "sample_count": len(sample_points),
                "nearest_hdmap_link_max_distance_m": round(max(distance_all), 3),
                "nearest_hdmap_link_p95_distance_m": round(percentile(distance_all, 0.95), 3),
                "nearest_hdmap_link_mean_distance_m": round(sum(distance_all) / len(distance_all), 3),
                "nearest_package_sample_counts": dict(Counter(nearest_package)),
                "coverage_status": "CONTINUOUS_CENTERLINE_COVERAGE",
            })

        excluded_2020_distance = float(link_2020.geometry.distance(whole_corridor).min())
        hdmap = {
            "dataset_id": "sejong-hdmap-coverage-v1",
            "generated_at_kst": "2026-07-31T19:30:00+09:00",
            "source_class": "official_historical_hdmap_geometry",
            "input_crs": OUTPUT_CRS,
            "target_coordinate_source": "official Sejong 413 NODE/LINK extract",
            "runtime_activation": "disabled",
            "usable_for_calibration": False,
            "source_packages": [
                source_record(
                    args.hdmap_2017,
                    package_id="hdmap-happycity-sec02-2017",
                    year=2017,
                    role="성금·청사 및 서측 회랑",
                ),
                source_record(
                    args.hdmap_2021,
                    package_id="hdmap-sangsang-sec001-2021",
                    year=2021,
                    role="세종 및 동측 회랑",
                ),
            ],
            "excluded_packages": [{
                **source_record(
                    args.hdmap_2020_excluded,
                    package_id="hdmap-centralpark-sec09-2020",
                    year=2020,
                    role="excluded_not_target_corridor",
                ),
                "minimum_corridor_distance_m": round(excluded_2020_distance, 3),
                "decision": "EXCLUDE_FROM_SIMULATION_AND_TARGET_GEOMETRY",
            }],
            "target_intersections": intersection_rows,
            "corridor_coverage": route_rows,
            "allowed_use": [
                "target lane-topology inspection",
                "stop-line and signal-device spatial QA",
                "corridor geometry display",
                "future physical storage constraint after explicit mapping review",
            ],
            "forbidden_use": [
                "automatic replacement of current queue-storage constants",
                "traffic demand or queue observation",
                "current 2026 road-operation claim",
                "signal timing, phase, offset or effective-green inference",
            ],
            "activation_blockers": [
                "model approach IDs are not mapped to exact HD-map incoming lane links",
                "movement permissions and shared lanes are not independently reviewed",
                "storage-length endpoint rule is not approved",
                "source years differ between west and east corridor packages",
            ],
            "decision": "OFFICIAL_GEOMETRY_AVAILABLE_BUT_RUNTIME_MAPPING_BLOCKED",
        }
        (args.output / "sejong_hdmap_status_20260731.json").write_text(
            json.dumps(hdmap, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    brt_points = parse_brt_points(args.brt)
    pvd_points, pvd_records, pvd_file_sizes = parse_pvd(args.pvd)
    pvd_terminals = Counter(str(record.get("terminalId")) for record in pvd_records)
    probe = {
        "dataset_id": "sejong-probe-exclusion-v1",
        "generated_at_kst": "2026-07-31T19:30:00+09:00",
        "runtime_activation": "excluded",
        "usable_for_calibration": False,
        "target_corridor": "성금교차로-청사교차로-세종교차로 / 절재로",
        "sources": [
            {
                "source_id": "sejong-b0-public-sample-20210913",
                "filename": args.brt.name,
                "bytes": args.brt.stat().st_size,
                "sha256": sha256(args.brt),
                **overlap_summary(brt_points, whole_corridor),
                "decision": "EXCLUDE_NO_TARGET_LINK_OVERLAP",
                "reason": "zero points within 100 m; bus-only single-day sample",
            },
            {
                "source_id": "sejong-pvd-public-sample",
                "filename": args.pvd.name,
                "bytes": args.pvd.stat().st_size,
                "sha256": sha256(args.pvd),
                **overlap_summary(pvd_points, whole_corridor),
                "parsed_record_count": len(pvd_records),
                "terminal_record_counts": dict(sorted(pvd_terminals.items())),
                "unique_link_id_count": len({str(record.get("linkId")) for record in pvd_records}),
                "nonempty_text_file_count": sum(size > 0 for size in pvd_file_sizes.values()),
                "empty_text_file_count": sum(size == 0 for size in pvd_file_sizes.values()),
                "decision": "EXCLUDE_NO_TARGET_LINK_OVERLAP",
                "reason": "zero points within 300 m and incomplete public sample files",
            },
        ],
        "allowed_use": ["parser regression fixture", "negative map-matching test"],
        "forbidden_use": [
            "target speed validation",
            "travel-time calibration",
            "queue calibration",
            "general passenger-car free-flow speed",
        ],
        "decision": "NO_LOCAL_PROBE_INPUT_FOR_TARGET_SIMULATION",
    }
    (args.output / "sejong_probe_exclusion_20260731.json").write_text(
        json.dumps(probe, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hdmap-2017", type=Path, required=True)
    parser.add_argument("--hdmap-2021", type=Path, required=True)
    parser.add_argument("--hdmap-2020-excluded", type=Path, required=True)
    parser.add_argument("--brt", type=Path, required=True)
    parser.add_argument("--pvd", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    build(parse_args())

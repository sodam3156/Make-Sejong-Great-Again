from __future__ import annotations

import heapq
import json
from pathlib import Path


def _route(features, starts, goals):
    adjacency = {}
    by_id = {}
    for feature in features:
        p = feature["properties"]
        by_id[str(p["LINK_ID"])] = p
        if p.get("ROAD_NAME") != "절재로":
            continue
        adjacency.setdefault(str(p["F_NODE"]), []).append((str(p["T_NODE"]), float(p["LENGTH"]), str(p["LINK_ID"])))
    queue = []
    best = {}
    for start in starts:
        heapq.heappush(queue, (0.0, start, []))
        best[start] = 0.0
    goals = set(goals)
    while queue:
        dist, node, links = heapq.heappop(queue)
        if dist != best.get(node):
            continue
        if node in goals:
            fields = ["LINK_ID", "F_NODE", "T_NODE", "LENGTH", "ROAD_NAME", "ROAD_RANK", "LANES", "MAX_SPD", "ROAD_TYPE", "CONNECT"]
            return {
                "distance_m": dist,
                "links": [{key: by_id[link_id].get(key) for key in fields} for link_id in links],
            }
        for nxt, length, link_id in adjacency.get(node, []):
            cand = dist + length
            if cand < best.get(nxt, float("inf")):
                best[nxt] = cand
                heapq.heappush(queue, (cand, nxt, links + [link_id]))
    return None


def test_dump_target_route_link_details_for_taxi_join():
    root = Path(__file__).resolve().parents[2]
    data = json.loads((root / "data/public/2026-07-29/sejong_nodelink_link.geojson").read_text(encoding="utf-8"))
    groups = {
        "seonggeum": ["4130092501", "4130092502", "4130092503", "4130092504"],
        "cheongsa": ["4130102901", "4130102902", "4130102903", "4130102904"],
        "sejong": ["4130138001", "4130138002", "4130138003", "4130138004"],
    }
    result = {
        "seonggeum_to_cheongsa": _route(data["features"], groups["seonggeum"], groups["cheongsa"]),
        "cheongsa_to_seonggeum": _route(data["features"], groups["cheongsa"], groups["seonggeum"]),
        "cheongsa_to_sejong": _route(data["features"], groups["cheongsa"], groups["sejong"]),
        "sejong_to_cheongsa": _route(data["features"], groups["sejong"], groups["cheongsa"]),
    }
    raise AssertionError("TARGET_ROUTE_LINK_DETAILS=" + json.dumps(result, ensure_ascii=False, sort_keys=True))

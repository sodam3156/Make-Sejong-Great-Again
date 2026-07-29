"""세종특별자치시 표준노드링크 공간망 추출.

국가교통정보센터(ITS) 전국 표준노드링크 원본(MOCT_NODE.shp / MOCT_LINK.shp)에서
세종특별자치시 지역코드(413)로 시작하는 NODE_ID/LINK_ID 레코드만 추려
WGS84(EPSG:4326) GeoJSON 두 개(노드/링크)로 변환한다.

## 지역코드(413) 확인 근거
표준노드링크 NODE_ID/LINK_ID의 앞 3자리는 지역코드다. 이 코드를 추측하지 않고
전국 원본에서 직접 확인했다: NODE_NAME이 정확히 "성금교차로" · "청사교차로" ·
"세종교차로"인 레코드를 전수 검색한 결과 총 12건(교차로마다 접근로별 4개 노드)이
나왔고, 전부 NODE_ID가 "413"으로 시작했다(예: 성금교차로 4130092501~504,
청사교차로 4130102901~904, 세종교차로 4130138001~004). 이 12개 노드의 좌표를
WGS84로 변환한 결과도 모두 세종 도심(정부세종청사 인근, 경도 127.26~127.30 /
위도 36.50~36.51)에 위치해 지리적으로도 일치함을 확인했다.
region 413로 필터링한 노드 8,768건은 전부 bbox(경도 127.05~127.55, 위도
36.40~36.80) 내부에 있어(예외 0건) 지역코드 확인이 정확함을 재확인했다.

## 원본 데이터 출처
- 페이지: https://www.its.go.kr/nodelink/nodelinkRef ("전국표준노드링크" 자료실,
  로그인/회원가입 불필요 — 직접 HTTP GET으로 내려받힘)
- 다운로드 URL: https://www.its.go.kr/opendata/nodelinkFileSDownload/DF_218/0
- 버전: "[2026-07-16]NODELINKDATA.zip" — 2026-07-16까지 반영된 전국표준노드링크
  및 회전제한정보, 링크부가정보
- 크기: 269,698,831 bytes (257.20MB)
- SHA-256: adfb23b31592d264cfbc48458ae0fdb5daee707e8c7ba4dbced53c7c544c1a48
- 좌표계(MOCT_NODE.prj / MOCT_LINK.prj 원문 그대로 사용, EPSG 코드 추정 없이
  WKT를 직접 파싱): PROJCS["ITRF2000_Central_Belt_60", GEOGCS 기준타원체
  GRS_1980, Transverse_Mercator, False_Easting 200000, False_Northing 600000,
  Central_Meridian 127.0, Latitude_Of_Origin 38.0, Scale_Factor 1.0, Meter 단위]
  (국가 "중부원점" 좌표계와 동일 파라미터)
- DBF 인코딩: CP949 (.cpg 파일 내용 "949")

전국 원본 ZIP은 용량(약 257MB) 때문에 이 저장소에 포함하지 않는다. scratchpad
등 임시 경로에만 보관한다. 다시 실행하려면 위 다운로드 URL에서 같은 파일을
재취득한 뒤 --zip 또는 --extract-dir 인자로 그 경로를 넘기면 된다.

## 결정론성
이 스크립트는 결정론적이다: 동일한 원본 SHP 입력이 주어지면 항상 동일한
GeoJSON을 생성한다(NODE_ID/LINK_ID 오름차순 정렬, 좌표는 소수 7자리로 반올림,
현재 시각 등 비결정 값을 출력에 넣지 않는다).

## 한계
- 표준노드링크 스펙은 회전교차로(로터리)를 별도 NODE_TYPE으로 구분하지 않는다
  (공식 노드유형: 교차로/교량시종점/고가도로시종점/도로시종점/지하차도시종점/
  터널시종점/행정경계/IC-JC). 추출한 절재로 회랑 3개 교차로(성금·청사·세종)는
  모두 NODE_TYPE="101"(교차로)이며 교차로마다 접근로 방향별로 4개의 개별
  노드로 표현된다 — 회전 여부는 이 속성만으로 판별할 수 없다.
- 지역코드(413) 기준으로만 필터링하므로, 세종시 경계에 걸쳐 있지만 LINK_ID가
  인접 시군(공주시·청주시·연기군 등) 코드로 등록된 경계 링크는 포함되지 않는다
  (전국 데이터 기준 그런 경계 링크가 85건 존재 — 세종로/금벽로/조치원로/
  당진영덕고속도로 등). 세종 노드 집합과 접하지만 LINK_ID 소속 지역코드가
  다른 링크이므로, 코드상 "세종 소관"으로 등록된 링크만 포함하는 이 스크립트의
  범위에서는 제외했다.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import shapefile
from pyproj import CRS, Transformer

ROOT = Path(__file__).resolve().parent.parent

REGION_CODE = "413"  # 세종특별자치시 — 위 docstring 참고(추측 아님, 속성값으로 확인)

# 이번 작업 세션에서 내려받은 원본 위치(세션이 끝나면 사라지는 임시 경로).
# 재실행 시에는 --zip 또는 --extract-dir 로 실제 위치를 넘길 것.
_SESSION_SCRATCH_ZIP = Path(
    "C:/Users/USER/AppData/Local/Temp/claude/"
    "C--Users-USER-Documents-sejong-jiphyeonjeon--claude-worktrees-"
    "standard-nodelink-spatial-troubleshoot-e8170c/"
    "433ba7cb-83f3-4a45-bd2f-998165e8aa76/scratchpad/"
    "NODELINKDATA_2026-07-16.zip"
)

SOURCE_URL = "https://www.its.go.kr/opendata/nodelinkFileSDownload/DF_218/0"
SOURCE_PAGE = "https://www.its.go.kr/nodelink/nodelinkRef"

DEFAULT_OUT_DIR = ROOT / "data" / "public" / "2026-07-29"
NODE_OUT_NAME = "sejong_nodelink_node.geojson"
LINK_OUT_NAME = "sejong_nodelink_link.geojson"

COORD_PRECISION = 7  # ~1cm급 정밀도


def _resolve_extract_dir(zip_path: Path | None, extract_dir: Path | None) -> Path:
    """SHP들이 들어있는 디렉터리를 결정한다. 필요하면 zip을 임시 폴더에 푼다."""
    if extract_dir is not None:
        if not (extract_dir / "MOCT_NODE.shp").exists():
            raise FileNotFoundError(
                f"{extract_dir} 안에 MOCT_NODE.shp가 없다. --extract-dir 경로를 확인하라."
            )
        return extract_dir

    if zip_path is None:
        env_dir = os.environ.get("SEJONG_NODELINK_DIR")
        if env_dir and (Path(env_dir) / "MOCT_NODE.shp").exists():
            return Path(env_dir)
        env_zip = os.environ.get("SEJONG_NODELINK_ZIP")
        zip_path = Path(env_zip) if env_zip else _SESSION_SCRATCH_ZIP

    if not zip_path.exists():
        raise FileNotFoundError(
            f"원본 ZIP을 찾을 수 없다: {zip_path}\n"
            f"'{SOURCE_PAGE}' 에서 최신 전국표준노드링크 ZIP을 다시 받아\n"
            f"'{SOURCE_URL}' 형태의 다운로드 URL을 --zip 인자로 넘기거나,\n"
            "이미 압축을 푼 폴더가 있으면 --extract-dir 로 넘겨라."
        )

    work_dir = Path(tempfile.mkdtemp(prefix="sejong_nodelink_"))
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(work_dir)

    candidates = list(work_dir.rglob("MOCT_NODE.shp"))
    if not candidates:
        raise FileNotFoundError(f"{zip_path} 안에서 MOCT_NODE.shp를 찾지 못했다.")
    return candidates[0].parent


def _build_transformer(shp_dir: Path) -> Transformer:
    prj_text = (shp_dir / "MOCT_NODE.prj").read_text(encoding="utf-8")
    src_crs = CRS.from_wkt(prj_text)
    return Transformer.from_crs(src_crs, CRS.from_epsg(4326), always_xy=True)


def _round_pt(lon: float, lat: float) -> list[float]:
    return [round(lon, COORD_PRECISION), round(lat, COORD_PRECISION)]


def extract_nodes(shp_dir: Path, transformer: Transformer) -> list[dict[str, Any]]:
    sf = shapefile.Reader(str(shp_dir / "MOCT_NODE"), encoding="cp949")
    features = []
    for shaperec in sf.iterShapeRecords():
        rec = shaperec.record
        node_id = rec["NODE_ID"]
        if not node_id.startswith(REGION_CODE):
            continue
        x, y = shaperec.shape.points[0]
        lon, lat = transformer.transform(x, y)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": _round_pt(lon, lat)},
                "properties": rec.as_dict(),
            }
        )
    features.sort(key=lambda f: f["properties"]["NODE_ID"])
    return features


def extract_links(shp_dir: Path, transformer: Transformer) -> list[dict[str, Any]]:
    sf = shapefile.Reader(str(shp_dir / "MOCT_LINK"), encoding="cp949")
    features = []
    for shaperec in sf.iterShapeRecords():
        rec = shaperec.record
        link_id = rec["LINK_ID"]
        if not link_id.startswith(REGION_CODE):
            continue
        shape = shaperec.shape
        parts = list(shape.parts) + [len(shape.points)]
        lines = []
        for i in range(len(parts) - 1):
            seg = shape.points[parts[i] : parts[i + 1]]
            lines.append([_round_pt(*transformer.transform(x, y)) for x, y in seg])
        if len(lines) == 1:
            geometry = {"type": "LineString", "coordinates": lines[0]}
        else:
            geometry = {"type": "MultiLineString", "coordinates": lines}
        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": rec.as_dict(),
            }
        )
    features.sort(key=lambda f: f["properties"]["LINK_ID"])
    return features


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, default=None, help="전국표준노드링크 ZIP 경로")
    parser.add_argument(
        "--extract-dir", type=Path, default=None,
        help="이미 압축을 푼 폴더(MOCT_NODE.shp가 들어있는 폴더) 경로",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    shp_dir = _resolve_extract_dir(args.zip, args.extract_dir)
    transformer = _build_transformer(shp_dir)

    node_features = extract_nodes(shp_dir, transformer)
    link_features = extract_links(shp_dir, transformer)

    # --- 내장 검증 (assert 3개) ---
    assert len(node_features) > 0, "추출된 세종 노드가 0건이다 — 지역코드 필터를 확인하라."
    assert len(link_features) > 0, "추출된 세종 링크가 0건이다 — 지역코드 필터를 확인하라."
    names = {f["properties"]["NODE_NAME"] for f in node_features}
    has_seonggeum = any("성금" in n for n in names)
    has_cheongsa = any("청사교차로" in n for n in names)
    has_sejong_x = any("세종교차로" in n for n in names)
    assert has_seonggeum and has_cheongsa and has_sejong_x, (
        "성금/청사교차로/세종교차로 중 하나 이상이 추출 결과에 없다 "
        f"(성금={has_seonggeum}, 청사교차로={has_cheongsa}, 세종교차로={has_sejong_x})."
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    node_path = args.out_dir / NODE_OUT_NAME
    link_path = args.out_dir / LINK_OUT_NAME

    with node_path.open("w", encoding="utf-8") as f:
        json.dump(
            {"type": "FeatureCollection", "features": node_features},
            f, ensure_ascii=False, indent=1,
        )
    with link_path.open("w", encoding="utf-8") as f:
        json.dump(
            {"type": "FeatureCollection", "features": link_features},
            f, ensure_ascii=False, indent=1,
        )

    print(f"nodes: {len(node_features)} -> {node_path}")
    print(f"links: {len(link_features)} -> {link_path}")
    for target in ("성금교차로", "청사교차로", "세종교차로"):
        for f in node_features:
            if f["properties"]["NODE_NAME"] == target:
                lon, lat = f["geometry"]["coordinates"]
                print(f"  {target}: NODE_ID={f['properties']['NODE_ID']} lon={lon} lat={lat}")


if __name__ == "__main__":
    main()

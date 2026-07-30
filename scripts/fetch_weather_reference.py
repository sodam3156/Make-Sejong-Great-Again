#!/usr/bin/env python3
"""Fetch reproducible weather screening data for the RainFlow reference dates.

This script deliberately separates:

1. ``proxy`` data: Open-Meteo ERA5-Land hourly reanalysis, used only to screen
   dry-date candidates when KMA observations are not yet available.
2. ``observed`` data: KMA ASOS station 239 exports, which remain the required
   source for final calibration and must not be substituted by the proxy.

The script has no third-party Python dependencies.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LAT = 36.48522
LON = 127.24438
STATION_ID = 239
START_DATE = "2022-08-01"
END_DATE = "2022-08-31"
RAIN_DATE = "2022-08-10"
DRY_CANDIDATES = ("2022-08-03", "2022-08-17", "2022-08-24", "2022-08-31")


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "RainFlow-evidence-fetch/1.0"})
    with urlopen(request, timeout=60) as response:
        body = response.read()
    if not body:
        raise RuntimeError(f"empty response: {url}")
    return body


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fetch_open_meteo(output_dir: Path) -> dict[str, Any]:
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": "precipitation",
        "daily": "precipitation_sum",
        "timezone": "Asia/Seoul",
        "models": "era5_land",
    }
    url = "https://archive-api.open-meteo.com/v1/archive?" + urlencode(params)
    raw = fetch_bytes(url)
    payload = json.loads(raw)

    raw_path = output_dir / "proxy" / "open_meteo_era5_land_sejong_202208.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(raw)

    hourly_rows = [
        {
            "timestamp_kst": timestamp,
            "precipitation_mm": precipitation,
            "source_class": "reanalysis_proxy",
            "source_model": "ERA5-Land",
        }
        for timestamp, precipitation in zip(
            payload["hourly"]["time"], payload["hourly"]["precipitation"], strict=True
        )
    ]
    hourly_path = output_dir / "proxy" / "weather_hourly_proxy_202208.csv"
    write_csv(
        hourly_path,
        ["timestamp_kst", "precipitation_mm", "source_class", "source_model"],
        hourly_rows,
    )

    daily_rows = [
        {
            "date_kst": date,
            "precipitation_sum_mm": precipitation,
            "source_class": "reanalysis_proxy",
            "source_model": "ERA5-Land",
        }
        for date, precipitation in zip(
            payload["daily"]["time"], payload["daily"]["precipitation_sum"], strict=True
        )
    ]
    daily_path = output_dir / "proxy" / "weather_daily_proxy_202208.csv"
    write_csv(
        daily_path,
        ["date_kst", "precipitation_sum_mm", "source_class", "source_model"],
        daily_rows,
    )

    hourly_by_time = {
        datetime.fromisoformat(row["timestamp_kst"]): float(row["precipitation_mm"] or 0.0)
        for row in hourly_rows
    }
    daily_by_date = {
        row["date_kst"]: float(row["precipitation_sum_mm"] or 0.0) for row in daily_rows
    }

    candidate_rows: list[dict[str, Any]] = []
    for candidate in DRY_CANDIDATES:
        midnight = datetime.fromisoformat(candidate)
        prior_hours = [midnight - timedelta(hours=offset) for offset in range(1, 7)]
        prior_total = sum(hourly_by_time.get(hour, 0.0) for hour in prior_hours)
        day_total = daily_by_date.get(candidate)
        candidate_rows.append(
            {
                "date_kst": candidate,
                "daily_precipitation_mm": day_total,
                "preceding_6h_precipitation_mm": round(prior_total, 3),
                "proxy_dry_pass": bool(day_total == 0.0 and prior_total == 0.0),
                "final_status": "SCREEN_ONLY_KMA_CONFIRMATION_REQUIRED",
            }
        )

    candidates_path = output_dir / "processed" / "dry_candidate_screening.csv"
    write_csv(
        candidates_path,
        [
            "date_kst",
            "daily_precipitation_mm",
            "preceding_6h_precipitation_mm",
            "proxy_dry_pass",
            "final_status",
        ],
        candidate_rows,
    )

    rain_daily = daily_by_date.get(RAIN_DATE)
    return {
        "request_url": url,
        "raw_file": str(raw_path),
        "raw_sha256": sha256_bytes(raw),
        "hourly_rows": len(hourly_rows),
        "daily_rows": len(daily_rows),
        "rain_date": RAIN_DATE,
        "rain_date_proxy_precipitation_mm": rain_daily,
        "dry_candidate_screening": candidate_rows,
    }


def fetch_kma_hourly_if_authorized(output_dir: Path) -> dict[str, Any]:
    auth_key = os.environ.get("KMA_API_AUTH_KEY", "").strip()
    if not auth_key:
        return {
            "status": "NOT_FETCHED",
            "reason": "KMA_API_AUTH_KEY not supplied",
            "required_source": "KMA ASOS station 239 observation",
        }

    params = {
        "tm1": "202208010000",
        "tm2": "202208312300",
        "stn": str(STATION_ID),
        "help": "1",
        "authKey": auth_key,
    }
    url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php?" + urlencode(params)
    raw = fetch_bytes(url)
    path = output_dir / "observed" / "kma_asos_239_hourly_202208.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {
        "status": "FETCHED",
        "file": str(path),
        "sha256": sha256_bytes(raw),
        "note": "Official hourly observation. Minute export is still required for final minute-level calibration.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="weather_reference_output")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    proxy = fetch_open_meteo(output_dir)
    kma = fetch_kma_hourly_if_authorized(output_dir)
    manifest = {
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "station": {
            "provider": "Korea Meteorological Administration",
            "station_id": STATION_ID,
            "station_name": "Sejong",
            "latitude": LAT,
            "longitude": LON,
        },
        "classification": {
            "proxy": "Date screening and sensitivity only; never a Sejong observed value.",
            "observed": "Required for calibration and claims about the selected date.",
        },
        "proxy": proxy,
        "kma_hourly": kma,
        "final_dry_date_status": "PENDING_KMA_OBSERVATION",
    }
    manifest_path = output_dir / "weather_source_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

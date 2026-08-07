#!/usr/bin/env python3
"""Fetch reproducible weather screening data for RainFlow reference dates.

Source classes are deliberately separated:

1. ``reanalysis_proxy``: Open-Meteo ERA5 hourly reanalysis. This may screen
   candidate dates and define sensitivity ranges, but it is not a KMA station
   observation and must never be presented as one.
2. ``observed``: KMA ASOS station 239 data. This remains mandatory for final
   dry-date confirmation and any calibration or claim about the selected day.

The script has no third-party Python dependencies. Missing precipitation values
are fatal: they are never converted to zero.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LAT = 36.48522
LON = 127.24438
STATION_ID = 239
RAIN_DATE = date(2022, 8, 10)
# The selection rule expands to ±28 days when no same-month/same-weekday dry
# candidate exists. One extra leading day is fetched for the preceding-6h test.
ANALYSIS_START_DATE = RAIN_DATE - timedelta(days=28)
ANALYSIS_END_DATE = RAIN_DATE + timedelta(days=28)
FETCH_START_DATE = ANALYSIS_START_DATE - timedelta(days=1)
FETCH_END_DATE = ANALYSIS_END_DATE
PROXY_MODEL = "ERA5"


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "RainFlow-evidence-fetch/1.2"})
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


def require_numeric_series(name: str, values: Any, expected_rows: int) -> list[float]:
    if not isinstance(values, list):
        raise RuntimeError(f"{name} is not a list")
    if len(values) != expected_rows:
        raise RuntimeError(f"{name} row count {len(values)} != {expected_rows}")
    null_indices = [index for index, value in enumerate(values) if value is None]
    if null_indices:
        sample = ",".join(str(index) for index in null_indices[:10])
        raise RuntimeError(
            f"{name} contains {len(null_indices)} null values; first indices: {sample}"
        )
    try:
        return [float(value) for value in values]
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{name} contains a non-numeric value") from exc


def fetch_open_meteo(output_dir: Path) -> dict[str, Any]:
    fetch_days = (FETCH_END_DATE - FETCH_START_DATE).days + 1
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": FETCH_START_DATE.isoformat(),
        "end_date": FETCH_END_DATE.isoformat(),
        "hourly": "precipitation",
        "daily": "precipitation_sum",
        "timezone": "Asia/Seoul",
        # ERA5 supplies precipitation. ERA5-Land does not expose this variable
        # through the historical API and must not be used for this extraction.
        "models": "era5",
    }
    url = "https://archive-api.open-meteo.com/v1/archive?" + urlencode(params)
    raw = fetch_bytes(url)
    payload = json.loads(raw)

    hourly_times = payload.get("hourly", {}).get("time")
    daily_dates = payload.get("daily", {}).get("time")
    expected_hourly_rows = fetch_days * 24
    expected_daily_rows = fetch_days
    if not isinstance(hourly_times, list) or len(hourly_times) != expected_hourly_rows:
        raise RuntimeError("unexpected hourly timestamp series")
    if not isinstance(daily_dates, list) or len(daily_dates) != expected_daily_rows:
        raise RuntimeError("unexpected daily date series")

    hourly_values = require_numeric_series(
        "hourly.precipitation",
        payload.get("hourly", {}).get("precipitation"),
        expected_hourly_rows,
    )
    daily_values = require_numeric_series(
        "daily.precipitation_sum",
        payload.get("daily", {}).get("precipitation_sum"),
        expected_daily_rows,
    )

    date_tag = f"{FETCH_START_DATE:%Y%m%d}_{FETCH_END_DATE:%Y%m%d}"
    raw_path = output_dir / "proxy" / f"open_meteo_era5_sejong_{date_tag}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(raw)

    hourly_rows = [
        {
            "timestamp_kst": timestamp,
            "precipitation_mm": precipitation,
            "source_class": "reanalysis_proxy",
            "source_model": PROXY_MODEL,
        }
        for timestamp, precipitation in zip(hourly_times, hourly_values, strict=True)
    ]
    hourly_path = output_dir / "proxy" / f"weather_hourly_proxy_{date_tag}.csv"
    write_csv(
        hourly_path,
        ["timestamp_kst", "precipitation_mm", "source_class", "source_model"],
        hourly_rows,
    )

    daily_rows = [
        {
            "date_kst": day,
            "precipitation_sum_mm": precipitation,
            "source_class": "reanalysis_proxy",
            "source_model": PROXY_MODEL,
        }
        for day, precipitation in zip(daily_dates, daily_values, strict=True)
    ]
    daily_path = output_dir / "proxy" / f"weather_daily_proxy_{date_tag}.csv"
    write_csv(
        daily_path,
        ["date_kst", "precipitation_sum_mm", "source_class", "source_model"],
        daily_rows,
    )

    hourly_by_time = {
        datetime.fromisoformat(row["timestamp_kst"]): float(row["precipitation_mm"])
        for row in hourly_rows
    }
    daily_by_date = {
        date.fromisoformat(row["date_kst"]): float(row["precipitation_sum_mm"])
        for row in daily_rows
    }

    # Independent sanity check: sum hourly values by local calendar date and
    # compare with the daily series returned in the same API response.
    hourly_sum_by_date: dict[date, float] = defaultdict(float)
    for timestamp, precipitation in hourly_by_time.items():
        hourly_sum_by_date[timestamp.date()] += precipitation
    daily_hourly_differences = {
        day: round(abs(daily_by_date[day] - hourly_sum_by_date[day]), 6)
        for day in daily_by_date
    }
    max_daily_hourly_difference = max(daily_hourly_differences.values())
    if max_daily_hourly_difference > 0.11:
        raise RuntimeError(
            "daily/hourly precipitation mismatch exceeds 0.11 mm: "
            f"{max_daily_hourly_difference}"
        )

    candidate_rows: list[dict[str, Any]] = []
    current = ANALYSIS_START_DATE
    while current <= ANALYSIS_END_DATE:
        if current != RAIN_DATE:
            midnight = datetime.combine(current, datetime.min.time())
            prior_hours = [midnight - timedelta(hours=offset) for offset in range(1, 7)]
            prior_total = sum(hourly_by_time[hour] for hour in prior_hours)
            day_total = daily_by_date[current]
            proxy_dry_pass = bool(day_total == 0.0 and prior_total == 0.0)
            candidate_rows.append(
                {
                    "date_kst": current.isoformat(),
                    "weekday": current.strftime("%A"),
                    "same_weekday_as_rain": current.weekday() == RAIN_DATE.weekday(),
                    "same_month_as_rain": current.month == RAIN_DATE.month,
                    "distance_days": abs((current - RAIN_DATE).days),
                    "daily_precipitation_mm": round(day_total, 3),
                    "preceding_6h_precipitation_mm": round(prior_total, 3),
                    "proxy_dry_pass": proxy_dry_pass,
                    "final_status": "SCREEN_ONLY_KMA_CONFIRMATION_REQUIRED",
                }
            )
        current += timedelta(days=1)

    candidate_rows.sort(
        key=lambda row: (
            not row["proxy_dry_pass"],
            not row["same_weekday_as_rain"],
            not row["same_month_as_rain"],
            row["distance_days"],
            row["date_kst"],
        )
    )
    ranked_rows = candidate_rows[:15]
    candidates_path = output_dir / "processed" / "dry_candidate_screening.csv"
    write_csv(
        candidates_path,
        [
            "date_kst",
            "weekday",
            "same_weekday_as_rain",
            "same_month_as_rain",
            "distance_days",
            "daily_precipitation_mm",
            "preceding_6h_precipitation_mm",
            "proxy_dry_pass",
            "final_status",
        ],
        ranked_rows,
    )

    rain_hours = [
        value
        for timestamp, value in hourly_by_time.items()
        if timestamp.date() == RAIN_DATE
    ]
    proxy_passes = [row for row in candidate_rows if row["proxy_dry_pass"]]
    selected_proxy_candidate = proxy_passes[0] if proxy_passes else None
    return {
        "source_class": "reanalysis_proxy",
        "source_model": PROXY_MODEL,
        "usage_limit": "screening_and_sensitivity_only",
        "request_url": url,
        "raw_file": str(raw_path),
        "raw_sha256": sha256_bytes(raw),
        "analysis_window": {
            "start_date": ANALYSIS_START_DATE.isoformat(),
            "end_date": ANALYSIS_END_DATE.isoformat(),
            "selection_priority": [
                "zero daily and preceding-6h proxy precipitation",
                "same weekday as rain date",
                "same month as rain date",
                "smallest absolute day distance",
            ],
        },
        "hourly_rows": len(hourly_rows),
        "daily_rows": len(daily_rows),
        "null_precipitation_values": 0,
        "daily_hourly_max_abs_difference_mm": max_daily_hourly_difference,
        "rain_date": RAIN_DATE.isoformat(),
        "rain_date_proxy_precipitation_mm": round(daily_by_date[RAIN_DATE], 3),
        "rain_date_proxy_max_hourly_mm": round(max(rain_hours), 3),
        "proxy_dry_pass_count": len(proxy_passes),
        "selected_proxy_candidate": selected_proxy_candidate,
        "ranked_dry_candidate_screening": ranked_rows,
    }


def fetch_kma_hourly_if_authorized(output_dir: Path) -> dict[str, Any]:
    auth_key = os.environ.get("KMA_API_AUTH_KEY", "").strip()
    if not auth_key:
        return {
            "status": "NOT_FETCHED",
            "reason": "KMA_API_AUTH_KEY not supplied",
            "required_source": "KMA ASOS station 239 observation",
            "next_action": "Add the key as a repository Actions secret; never commit it.",
        }

    params = {
        "tm1": f"{FETCH_START_DATE:%Y%m%d}0000",
        "tm2": f"{FETCH_END_DATE:%Y%m%d}2300",
        "stn": str(STATION_ID),
        "help": "1",
        "authKey": auth_key,
    }
    url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php?" + urlencode(params)
    raw = fetch_bytes(url)
    path = output_dir / "observed" / "kma_asos_239_hourly_reference_window.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {
        "status": "FETCHED",
        "file": str(path),
        "sha256": sha256_bytes(raw),
        "note": (
            "Official hourly observation. The KMA one-day minute export remains "
            "required for final minute-level calibration."
        ),
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
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
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

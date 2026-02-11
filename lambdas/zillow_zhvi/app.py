"""
Zillow ZHVI Lambda

Downloads the City-level Zillow Home Value Index (ZHVI) CSV, filters for NJ cities
matching our 104 towns, and upserts monthly values into the zhvi_values table.

Schedule: Monthly, 18th at 08:00 UTC
Source: https://files.zillowstatic.com/research/public_csvs/zhvi/City_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv

Uses the City-level file (~5MB) instead of ZIP-level (~91MB) for efficiency.
Not all 104 towns appear in Zillow data - those are simply skipped.
"""

import csv
import io
import logging
import urllib.request

from shared.config import ZILLOW_NAME_TO_ID
from shared.logging_utils import lambda_handler_wrapper
from shared.supabase_client import upsert

logger = logging.getLogger(__name__)

ZHVI_CITY_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zhvi/"
    "City_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)


def parse_date_columns(headers: list[str]) -> list[str]:
    """Extract date column headers (YYYY-MM-DD format)."""
    date_cols = []
    for h in headers:
        if len(h) == 10 and h[4] == "-" and h[7] == "-":
            date_cols.append(h)
    return date_cols


@lambda_handler_wrapper
def handler(event, context):
    logger.info("Downloading Zillow ZHVI City-level CSV")
    req = urllib.request.Request(ZHVI_CITY_URL, headers={"User-Agent": "MiniAppETL/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = resp.read().decode("utf-8")

    logger.info(f"Downloaded {len(text)} bytes")

    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    date_cols = parse_date_columns(headers)
    logger.info(f"Found {len(date_cols)} date columns (from {date_cols[0]} to {date_cols[-1]})")

    rows = []
    matched_towns = set()
    skipped_nj = []

    for record in reader:
        state = record.get("StateName", "")
        if state != "NJ" and state != "New Jersey":
            continue

        city = record.get("RegionName", "").strip()
        town_id = ZILLOW_NAME_TO_ID.get(city.lower())

        if not town_id:
            skipped_nj.append(city)
            continue

        matched_towns.add(town_id)

        for date_col in date_cols:
            value = record.get(date_col, "").strip()
            if not value:
                continue
            try:
                zhvi_value = float(value)
            except ValueError:
                continue

            rows.append({
                "town_id": town_id,
                "date": date_col,
                "zhvi_value": zhvi_value,
                "home_type": "all_homes",
            })

    logger.info(f"Matched {len(matched_towns)} towns, {len(rows)} data points")
    if skipped_nj:
        logger.info(f"Unmatched NJ cities in Zillow: {sorted(set(skipped_nj))}")

    result = upsert("zhvi_values", rows, on_conflict="town_id,date,home_type")

    return {
        "towns_matched": len(matched_towns),
        "towns_matched_list": sorted(matched_towns),
        "data_points": len(rows),
        "date_range": f"{date_cols[0]} to {date_cols[-1]}" if date_cols else "none",
        "unmatched_nj_cities": sorted(set(skipped_nj)),
        "upserted": result["inserted"],
    }

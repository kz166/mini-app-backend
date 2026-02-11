"""
Redfin Market Data Lambda

Streams the Redfin city-level market data TSV.gz (~1.4GB compressed), filters for
NJ cities matching our 104 towns, and upserts into the market_data table.

Schedule: Monthly, 5th at 08:00 UTC
Source: https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/city/us/city_market_tracker.tsv000.gz

Streams line-by-line to avoid loading entire file into memory.
"""

import csv
import gzip
import io
import logging
import urllib.request

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.config import REDFIN_NAME_TO_ID
from shared.supabase_client import upsert
from shared.logging_utils import lambda_handler_wrapper

logger = logging.getLogger(__name__)

REDFIN_URL = (
    "https://redfin-public-data.s3.us-west-2.amazonaws.com/"
    "redfin_market_tracker/city/us/city_market_tracker.tsv000.gz"
)

# Redfin column name -> our DB column name
COLUMN_MAP = {
    "median_sale_price": "median_sale_price",
    "median_list_price": "median_list_price",
    "median_ppsf": "median_ppsf",
    "homes_sold": "homes_sold",
    "new_listings": "new_listings",
    "inventory": "inventory",
    "months_of_supply": "months_of_supply",
    "median_dom": "median_dom",
    "avg_sale_to_list": "avg_sale_to_list",
    "sold_above_list_pct": "sold_above_list_pct",
    "price_drops_pct": "price_drops_pct",
    "off_market_in_two_weeks_pct": "off_market_in_two_weeks_pct",
}


def safe_float(val: str) -> float | None:
    if not val or val == "":
        return None
    try:
        return float(val)
    except ValueError:
        return None


def safe_int(val: str) -> int | None:
    if not val or val == "":
        return None
    try:
        return int(float(val))
    except ValueError:
        return None


@lambda_handler_wrapper
def handler(event, context):
    logger.info("Streaming Redfin city market tracker TSV.gz")

    req = urllib.request.Request(REDFIN_URL, headers={"User-Agent": "MiniAppETL/1.0"})
    resp = urllib.request.urlopen(req, timeout=600)

    # Read into memory then decompress (Lambda has enough memory at 3008MB)
    logger.info("Downloading compressed data...")
    compressed = resp.read()
    resp.close()
    logger.info(f"Downloaded {len(compressed) / 1024 / 1024:.1f} MB compressed")

    decompressed = gzip.decompress(compressed)
    del compressed  # Free memory
    logger.info(f"Decompressed to {len(decompressed) / 1024 / 1024:.1f} MB")

    text_stream = io.StringIO(decompressed.decode("utf-8"))
    del decompressed  # Free memory

    reader = csv.DictReader(text_stream, delimiter="\t")

    rows = []
    matched_towns = set()
    unmatched_nj = set()
    total_nj_lines = 0

    for record in reader:
        state_code = record.get("state_code", "")
        if state_code != "NJ":
            continue

        total_nj_lines += 1
        city = record.get("city", "").strip()
        town_id = REDFIN_NAME_TO_ID.get(city.lower())

        if not town_id:
            unmatched_nj.add(city)
            continue

        matched_towns.add(town_id)
        period_begin = record.get("period_begin", "")
        period_end = record.get("period_end", "")
        property_type = record.get("property_type", "")

        if not period_begin or not property_type:
            continue

        row = {
            "town_id": town_id,
            "period_begin": period_begin,
            "period_end": period_end,
            "property_type": property_type,
        }

        # Numeric fields
        for redfin_col, db_col in COLUMN_MAP.items():
            val = record.get(redfin_col, "")
            if db_col in ("homes_sold", "new_listings", "inventory", "median_dom"):
                row[db_col] = safe_int(val)
            else:
                row[db_col] = safe_float(val)

        rows.append(row)

    logger.info(
        f"NJ lines: {total_nj_lines}, Matched: {len(rows)} rows "
        f"across {len(matched_towns)} towns"
    )
    if unmatched_nj:
        logger.info(f"Unmatched NJ cities in Redfin: {sorted(unmatched_nj)}")

    result = upsert(
        "market_data", rows, on_conflict="town_id,period_begin,property_type"
    )

    return {
        "nj_lines_total": total_nj_lines,
        "towns_matched": len(matched_towns),
        "rows_upserted": len(rows),
        "unmatched_nj_cities": sorted(unmatched_nj),
        "upsert_result": result,
    }

"""
Redfin Market Data Lambda

Streams the Redfin city-level market data TSV.gz (~934MB compressed), filters for
NJ cities matching our 104 towns, and upserts into the market_data table.

Schedule: Monthly, 5th at 08:00 UTC
Source: https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv000.gz

Streams line-by-line to avoid loading entire file into memory.
"""

import csv
import gzip
import io
import logging
import urllib.request

from shared.config import REDFIN_NAME_TO_ID
from shared.logging_utils import lambda_handler_wrapper
from shared.supabase_client import upsert

logger = logging.getLogger(__name__)

REDFIN_URL = (
    "https://redfin-public-data.s3.us-west-2.amazonaws.com/"
    "redfin_market_tracker/city_market_tracker.tsv000.gz"
)

# Redfin column name (UPPERCASE) -> our DB column name
COLUMN_MAP = {
    "MEDIAN_SALE_PRICE": "median_sale_price",
    "MEDIAN_LIST_PRICE": "median_list_price",
    "MEDIAN_PPSF": "median_ppsf",
    "HOMES_SOLD": "homes_sold",
    "NEW_LISTINGS": "new_listings",
    "INVENTORY": "inventory",
    "MONTHS_OF_SUPPLY": "months_of_supply",
    "MEDIAN_DOM": "median_dom",
    "AVG_SALE_TO_LIST": "avg_sale_to_list",
    "SOLD_ABOVE_LIST": "sold_above_list_pct",
    "PRICE_DROPS": "price_drops_pct",
    "OFF_MARKET_IN_TWO_WEEKS": "off_market_in_two_weeks_pct",
}

INT_COLUMNS = {"homes_sold", "new_listings", "inventory", "median_dom"}


def safe_float(val: str) -> float | None:
    if not val or val == "" or val == "NA":
        return None
    try:
        return float(val)
    except ValueError:
        return None


def safe_int(val: str) -> int | None:
    if not val or val == "" or val == "NA":
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

    # Stream-decompress to avoid holding entire file in memory
    logger.info("Streaming download + gzip decompression...")
    gz_stream = gzip.GzipFile(fileobj=resp)
    text_stream = io.TextIOWrapper(gz_stream, encoding="utf-8")
    reader = csv.DictReader(text_stream, delimiter="\t")

    deduped = {}
    matched_towns = set()
    unmatched_nj = set()
    total_nj_lines = 0

    for record in reader:
        state_code = record.get("STATE_CODE", "")
        if state_code != "NJ":
            continue

        total_nj_lines += 1
        city = record.get("CITY", "").strip()
        town_id = REDFIN_NAME_TO_ID.get(city.lower())

        if not town_id:
            unmatched_nj.add(city)
            continue

        matched_towns.add(town_id)
        period_begin = record.get("PERIOD_BEGIN", "")
        period_end = record.get("PERIOD_END", "")
        property_type = record.get("PROPERTY_TYPE", "")

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
            if db_col in INT_COLUMNS:
                row[db_col] = safe_int(val)
            else:
                row[db_col] = safe_float(val)

        key = (town_id, period_begin, property_type)
        deduped[key] = row

    rows = list(deduped.values())

    logger.info(
        f"NJ lines: {total_nj_lines}, Matched: {len(rows)} rows "
        f"(deduped from {len(deduped)} keys) across {len(matched_towns)} towns"
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

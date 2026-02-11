"""
FRED Mortgage Rates Lambda

Fetches weekly 30-year and 15-year fixed mortgage rates from FRED (Federal Reserve
Economic Data) and upserts them into the mortgage_rates table.

Schedule: Weekly, Friday 08:00 UTC
Source: https://fred.stlouisfed.org/graph/fredgraph.csv

FRED Series:
  - MORTGAGE30US: 30-Year Fixed Rate
  - MORTGAGE15US: 15-Year Fixed Rate
"""

import csv
import io
import logging
import urllib.request
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.supabase_client import upsert
from shared.logging_utils import lambda_handler_wrapper

logger = logging.getLogger(__name__)

FRED_30YR_URL = (
    "https://fred.stlouisfed.org/graph/fredgraph.csv"
    "?id=MORTGAGE30US&cosd=2020-01-01"
)
FRED_15YR_URL = (
    "https://fred.stlouisfed.org/graph/fredgraph.csv"
    "?id=MORTGAGE15US&cosd=2020-01-01"
)


def fetch_fred_csv(url: str) -> dict[str, float]:
    """Fetch FRED CSV and return {date_str: rate} dict."""
    req = urllib.request.Request(url, headers={"User-Agent": "MiniAppETL/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8")

    rates = {}
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        date_str = row["DATE"]
        value = row.get("MORTGAGE30US") or row.get("MORTGAGE15US") or row.get("VALUE", "")
        # FRED uses "." for missing values
        if value and value != ".":
            try:
                rates[date_str] = float(value)
            except ValueError:
                continue
    return rates


@lambda_handler_wrapper
def handler(event, context):
    logger.info("Fetching 30-year mortgage rates from FRED")
    rates_30yr = fetch_fred_csv(FRED_30YR_URL)
    logger.info(f"Got {len(rates_30yr)} 30-year rate records")

    logger.info("Fetching 15-year mortgage rates from FRED")
    rates_15yr = fetch_fred_csv(FRED_15YR_URL)
    logger.info(f"Got {len(rates_15yr)} 15-year rate records")

    # Merge into rows by date
    all_dates = sorted(set(rates_30yr.keys()) | set(rates_15yr.keys()))
    rows = []
    for date_str in all_dates:
        row = {"date": date_str}
        if date_str in rates_30yr:
            row["rate_30yr"] = rates_30yr[date_str]
        if date_str in rates_15yr:
            row["rate_15yr"] = rates_15yr[date_str]
        rows.append(row)

    logger.info(f"Upserting {len(rows)} mortgage rate records")
    result = upsert("mortgage_rates", rows, on_conflict="date")

    return {
        "dates_fetched": len(all_dates),
        "rates_30yr_count": len(rates_30yr),
        "rates_15yr_count": len(rates_15yr),
        "upserted": result["inserted"],
    }

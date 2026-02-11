"""
NJ Tax Rates Lambda

Accepts a manual JSON payload with tax rate data for NJ municipalities.
NJ Division of Taxation publishes rates annually as PDF/Excel, so this Lambda
is triggered manually after the data is extracted.

Schedule: Manual trigger only

Expected event payload format:
{
  "year": 2024,
  "rates": [
    {
      "town_id": "fort_lee",
      "general_tax_rate": 2.368,
      "effective_tax_rate": 1.679,
      "equalization_ratio": 70.90,
      "avg_residential_tax": 12345
    },
    ...
  ]
}

Alternatively, you can pass a flat list under "rates" keyed by town name:
{
  "year": 2024,
  "rates_by_name": {
    "Fort Lee": {"general_tax_rate": 2.368, "effective_tax_rate": 1.679, ...},
    ...
  }
}
"""

import logging

from shared.config import TOWNS, TOWNS_BY_ID
from shared.logging_utils import lambda_handler_wrapper
from shared.supabase_client import upsert

logger = logging.getLogger(__name__)

# name_en (lowered) -> town_id
NAME_TO_ID = {t["name_en"].lower(): t["id"] for t in TOWNS}


@lambda_handler_wrapper
def handler(event, context):
    year = event.get("year")
    if not year:
        raise ValueError("Missing 'year' in event payload")

    rows = []

    # Format 1: Direct list with town_id
    if "rates" in event:
        for entry in event["rates"]:
            town_id = entry.get("town_id")
            if town_id not in TOWNS_BY_ID:
                logger.warning(f"Unknown town_id: {town_id}, skipping")
                continue

            rows.append({
                "town_id": town_id,
                "year": year,
                "general_tax_rate": entry.get("general_tax_rate"),
                "effective_tax_rate": entry.get("effective_tax_rate"),
                "equalization_ratio": entry.get("equalization_ratio"),
                "avg_residential_tax": entry.get("avg_residential_tax"),
            })

    # Format 2: Dict keyed by town name
    elif "rates_by_name" in event:
        for name, data in event["rates_by_name"].items():
            town_id = NAME_TO_ID.get(name.lower())
            if not town_id:
                logger.warning(f"Unknown town name: {name}, skipping")
                continue

            rows.append({
                "town_id": town_id,
                "year": year,
                "general_tax_rate": data.get("general_tax_rate"),
                "effective_tax_rate": data.get("effective_tax_rate"),
                "equalization_ratio": data.get("equalization_ratio"),
                "avg_residential_tax": data.get("avg_residential_tax"),
            })
    else:
        raise ValueError("Event must contain 'rates' or 'rates_by_name'")

    logger.info(f"Upserting {len(rows)} tax rate records for year {year}")
    result = upsert("tax_rates", rows, on_conflict="town_id,year")

    return {
        "year": year,
        "towns_processed": len(rows),
        "upserted": result["inserted"],
    }

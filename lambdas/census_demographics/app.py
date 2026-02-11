"""
Census Demographics Lambda

Fetches ACS 5-Year demographic data for all 104 towns from the Census Bureau API.
Queries by county subdivision wildcard for Bergen (003), Hudson (017), and Essex (013).

Schedule: Annual, October 1st (ACS data typically released Sept/Oct)
Source: https://api.census.gov/data/2023/acs/acs5

Census Variables:
  B01003_001E  Total population
  B19013_001E  Median household income
  B25077_001E  Median home value
  B01002_001E  Median age
  B03002_003E  White alone (not Hispanic)
  B03002_006E  Asian alone (not Hispanic)
  B03002_012E  Hispanic or Latino
  B03002_004E  Black alone (not Hispanic)
  B08303_001E  Total commuters (for avg commute calculation)
  B08013_001E  Aggregate travel time to work
"""

import json
import logging
import urllib.error
import urllib.request

from shared.config import BERGEN_FIPS, ESSEX_FIPS, FIPS_TO_ID, HUDSON_FIPS, STATE_FIPS
from shared.logging_utils import lambda_handler_wrapper
from shared.supabase_client import upsert

logger = logging.getLogger(__name__)

ACS_BASE = "https://api.census.gov/data/{year}/acs/acs5"

VARIABLES = (
    "NAME,"
    "B01003_001E,"  # population
    "B19013_001E,"  # median_income
    "B25077_001E,"  # median_home_value
    "B01002_001E,"  # median_age
    "B03002_003E,"  # white_alone_not_hispanic
    "B03002_006E,"  # asian_alone_not_hispanic
    "B03002_012E,"  # hispanic_or_latino
    "B03002_004E,"  # black_alone_not_hispanic
    "B08013_001E,"  # aggregate_travel_time
    "B08303_001E"  # total_commuters
)


def fetch_county(year: int, county_fips: str) -> list[dict]:
    """Fetch ACS data for all county subdivisions in a county."""
    url = (
        f"{ACS_BASE.format(year=year)}"
        f"?get={VARIABLES}"
        f"&for=county+subdivision:*"
        f"&in=state:{STATE_FIPS}&in=county:{county_fips}"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "MiniAppETL/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        logger.error(f"Census API error for county {county_fips}: {e.code}")
        return []

    if len(data) < 2:
        return []

    headers = data[0]
    rows = []
    for row in data[1:]:
        record = dict(zip(headers, row, strict=False))
        county_sub = record.get("county subdivision", "")
        fips_key = county_fips + county_sub
        town_id = FIPS_TO_ID.get(fips_key)

        if not town_id:
            continue

        # Parse numeric values (Census returns strings, "-666666666" for missing)
        def parse_int(val):
            if val is None or val == "" or int(val) < 0:
                return None
            return int(val)

        def parse_float(val):
            if val is None or val == "":
                return None
            f = float(val)
            return None if f < 0 else f

        population = parse_int(record.get("B01003_001E"))
        median_income = parse_int(record.get("B19013_001E"))
        median_home_value = parse_int(record.get("B25077_001E"))
        median_age = parse_float(record.get("B01002_001E"))

        # Ethnicity percentages
        white = parse_int(record.get("B03002_003E"))
        asian = parse_int(record.get("B03002_006E"))
        hispanic = parse_int(record.get("B03002_012E"))
        black = parse_int(record.get("B03002_004E"))

        ethnic_white_pct = None
        ethnic_asian_pct = None
        ethnic_hispanic_pct = None
        ethnic_black_pct = None
        ethnic_other_pct = None

        if population and population > 0:
            if white is not None:
                ethnic_white_pct = round(white / population * 100, 1)
            if asian is not None:
                ethnic_asian_pct = round(asian / population * 100, 1)
            if hispanic is not None:
                ethnic_hispanic_pct = round(hispanic / population * 100, 1)
            if black is not None:
                ethnic_black_pct = round(black / population * 100, 1)

            known = sum(x for x in [white, asian, hispanic, black] if x is not None)
            ethnic_other_pct = round((population - known) / population * 100, 1)

        # Average commute time
        commute_time_avg = None
        agg_travel = parse_float(record.get("B08013_001E"))
        total_commuters = parse_int(record.get("B08303_001E"))
        if agg_travel and total_commuters and total_commuters > 0:
            commute_time_avg = round(agg_travel / total_commuters, 1)

        rows.append(
            {
                "town_id": town_id,
                "year": year,
                "population": population,
                "median_income": median_income,
                "median_home_value": median_home_value,
                "median_age": median_age,
                "ethnic_white_pct": ethnic_white_pct,
                "ethnic_asian_pct": ethnic_asian_pct,
                "ethnic_hispanic_pct": ethnic_hispanic_pct,
                "ethnic_black_pct": ethnic_black_pct,
                "ethnic_other_pct": ethnic_other_pct,
                "commute_time_avg": commute_time_avg,
            }
        )

    return rows


@lambda_handler_wrapper
def handler(event, context):
    # Allow overriding the ACS year via event payload
    year = event.get("year", 2023) if isinstance(event, dict) else 2023

    logger.info(f"Fetching Census ACS {year} data for 3 counties")

    all_rows = []
    for county_name, county_fips in [
        ("Bergen", BERGEN_FIPS),
        ("Hudson", HUDSON_FIPS),
        ("Essex", ESSEX_FIPS),
    ]:
        rows = fetch_county(year, county_fips)
        logger.info(f"{county_name} County: {len(rows)} towns matched")
        all_rows.extend(rows)

    logger.info(f"Total: {len(all_rows)} town demographic records")
    result = upsert("town_demographics", all_rows, on_conflict="town_id,year")

    return {
        "year": year,
        "towns_fetched": len(all_rows),
        "upserted": result["inserted"],
    }

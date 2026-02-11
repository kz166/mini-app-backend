# Data Sources

All data sources are free and require no API keys.

## FRED - Mortgage Rates

- **URL**: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US&cosd=2020-01-01`
- **Format**: CSV (DATE, VALUE)
- **Series**: MORTGAGE30US (30-year), MORTGAGE15US (15-year)
- **Refresh**: Weekly (every Thursday, we fetch Friday)
- **Size**: ~50 KB

## Zillow ZHVI - Home Values

- **URL**: `https://files.zillowstatic.com/research/public_csvs/zhvi/City_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv`
- **Format**: CSV with date columns (YYYY-MM-DD)
- **Filter**: StateName = "NJ", match RegionName to our town list
- **Refresh**: Monthly (published mid-month, we fetch 18th)
- **Size**: ~5 MB (city-level)
- **Note**: Not all 104 towns appear in Zillow data. Small boroughs (Rockleigh, Teterboro, etc.) are often missing.

## Redfin - Market Data

- **URL**: `https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/city/us/city_market_tracker.tsv000.gz`
- **Format**: Gzipped TSV
- **Filter**: state_code = "NJ", match city name to our town list
- **Refresh**: Monthly (published early month, we fetch 5th)
- **Size**: ~1.4 GB compressed (~4 GB uncompressed)
- **Note**: Some towns use "Township" suffix (e.g., "Teaneck Township"). Our config includes variant names.

## Census ACS - Demographics

- **URL**: `https://api.census.gov/data/{year}/acs/acs5`
- **Format**: JSON array
- **Query**: `for=county+subdivision:*&in=state:34&in=county:{003|017|013}`
- **Variables**: Population, income, home value, age, ethnicity, commute time
- **Refresh**: Annual (ACS 5-year estimates, published Sept/Oct)
- **Size**: ~50 KB per county (3 API calls total)

## NJ Division of Taxation - Tax Rates

- **URL**: `https://www.nj.gov/treasury/taxation/lpt/taxrate.shtml`
- **Format**: PDF or Excel (varies by year, requires manual extraction)
- **Data**: General tax rate, effective tax rate, equalization ratio
- **Refresh**: Annual (published spring/summer)
- **Note**: Manual process. Extract data into JSON, trigger Lambda with payload.

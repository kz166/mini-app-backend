# Supabase Database Schema

Project: `hxosucwubvtbhatoqsef` (us-east-1)

## Tables

### `towns` (Primary reference table)
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | text | NO | PK, snake_case slug (e.g., `fort_lee`) |
| name_en | text | NO | Official English name |
| name_zh | text | YES | Chinese transliteration |
| county | text | YES | Bergen, Hudson, or Essex |
| state_fips | text | YES | Always '34' (NJ) |
| place_fips | text | YES | 5-digit county subdivision FIPS |
| lat | numeric | YES | Latitude |
| lng | numeric | YES | Longitude |
| description_en | text | YES | English description |
| description_zh | text | YES | Chinese description |
| created_at | timestamptz | YES | Default: now() |
| updated_at | timestamptz | YES | Default: now() |

104 rows (70 Bergen + 12 Hudson + 22 Essex)

### `mortgage_rates` (National, not town-specific)
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | integer | NO | PK, auto-increment |
| date | date | NO | UNIQUE |
| rate_30yr | numeric | YES | 30-year fixed rate (%) |
| rate_15yr | numeric | YES | 15-year fixed rate (%) |
| created_at | timestamptz | YES | |

### `town_demographics`
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | integer | NO | PK, auto-increment |
| town_id | text | YES | FK -> towns.id |
| year | integer | YES | ACS year |
| population | integer | YES | |
| median_income | integer | YES | Household ($) |
| median_home_value | integer | YES | ($) |
| median_age | numeric | YES | |
| ethnic_white_pct | numeric | YES | % |
| ethnic_asian_pct | numeric | YES | % |
| ethnic_hispanic_pct | numeric | YES | % |
| ethnic_black_pct | numeric | YES | % |
| ethnic_other_pct | numeric | YES | % |
| commute_time_avg | numeric | YES | Minutes |
| created_at | timestamptz | YES | |

**Unique**: (town_id, year)

### `tax_rates`
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | integer | NO | PK, auto-increment |
| town_id | text | YES | FK -> towns.id |
| year | integer | YES | |
| general_tax_rate | numeric | YES | Per $100 assessed |
| effective_tax_rate | numeric | YES | Per $100 true value |
| equalization_ratio | numeric | YES | % |
| avg_residential_tax | numeric | YES | ($) |
| created_at | timestamptz | YES | |

**Unique**: (town_id, year)

### `zhvi_values`
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | integer | NO | PK, auto-increment |
| town_id | text | YES | FK -> towns.id |
| date | date | YES | Monthly (YYYY-MM-DD) |
| zhvi_value | numeric | YES | Zillow Home Value Index ($) |
| home_type | text | YES | e.g., 'all_homes' |
| created_at | timestamptz | YES | |

**Unique**: (town_id, date, home_type)

### `market_data`
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | integer | NO | PK, auto-increment |
| town_id | text | YES | FK -> towns.id |
| period_begin | date | YES | |
| period_end | date | YES | |
| property_type | text | YES | e.g., 'All Residential' |
| median_sale_price | numeric | YES | ($) |
| median_list_price | numeric | YES | ($) |
| median_ppsf | numeric | YES | Price per sq ft ($) |
| homes_sold | integer | YES | |
| new_listings | integer | YES | |
| inventory | integer | YES | |
| months_of_supply | numeric | YES | |
| median_dom | integer | YES | Days on market |
| avg_sale_to_list | numeric | YES | Ratio |
| sold_above_list_pct | numeric | YES | % |
| price_drops_pct | numeric | YES | % |
| off_market_in_two_weeks_pct | numeric | YES | % |
| created_at | timestamptz | YES | |

**Unique**: (town_id, period_begin, property_type)

## RLS Policies

All tables have Row Level Security enabled with public read-only access via anon key.
Write operations require the service_role key (used by Lambda ETL).

## Foreign Keys

All child tables reference `towns.id`:
- `town_demographics.town_id` -> `towns.id`
- `tax_rates.town_id` -> `towns.id`
- `zhvi_values.town_id` -> `towns.id`
- `market_data.town_id` -> `towns.id`

`mortgage_rates` has no foreign key (national data).

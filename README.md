# mini-app-backend

Backend services for the Real Estate Mini App.

## Architecture

```
Data Sources (FRED, Zillow, Redfin, Census, NJ Tax)
        | EventBridge schedules
   AWS Lambda (Python ETL)
        | Supabase REST API (service_role key, write)
   Supabase PostgreSQL
        ^ PostgREST (anon key, read-only)
   WeChat Mini App (frontend)

   Survey flow (unchanged):
   WeChat Mini App -> Vercel API -> MongoDB Atlas
```

## Components

### `vercel-api/` - Survey Backend (Vercel)

Serverless API for survey submission and admin dashboard. Deployed on Vercel.

- `POST /api/survey/submit` - Submit survey
- `GET /api/admin/surveys` - List surveys (auth required)
- `GET /api/admin/stats` - Survey statistics (auth required)

### `lambdas/` - ETL Pipeline (AWS Lambda)

Automated data refresh for 104 NJ municipalities (Bergen, Hudson, Essex counties).

| Lambda | Source | Schedule |
|---|---|---|
| `fred_mortgage_rates` | FRED CSV | Weekly (Fri) |
| `zillow_zhvi` | Zillow City CSV | Monthly (18th) |
| `redfin_market` | Redfin TSV.gz | Monthly (5th) |
| `census_demographics` | Census ACS API | Annual (Oct 1) |
| `nj_tax_rates` | Manual JSON | Manual trigger |

## Setup

### Vercel (Survey API)

```bash
cd vercel-api
cp .env.local.example .env.local
# Edit .env.local with your MongoDB URI and admin token
npm install
npm run dev
```

### AWS Lambda (ETL)

```bash
# Prerequisites: AWS SAM CLI, Python 3.12
sam build
sam deploy --guided
```

### Environment Variables

**Vercel** (set in Vercel dashboard):
- `MONGODB_URI` - MongoDB Atlas connection string
- `ADMIN_TOKEN` - Admin authentication token

**AWS Lambda** (set in SSM Parameter Store):
- `/mini-app/supabase-service-key` - Supabase service_role key

**SAM Template Parameters**:
- `SupabaseUrl` - Supabase project URL

## Data Coverage

104 municipalities across 3 NJ counties:
- **Bergen County** (70 towns): Fort Lee, Tenafly, Paramus, Ridgewood, Teaneck, Hackensack, Englewood, ...
- **Hudson County** (12 towns): Hoboken, Jersey City, Bayonne, Union City, North Bergen, ...
- **Essex County** (22 towns): Newark, Montclair, Millburn, Livingston, Maplewood, ...

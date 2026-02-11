.PHONY: build deploy lint lint-py lint-js lint-fix typecheck format \
       invoke-fred invoke-zillow invoke-redfin invoke-census invoke-tax \
       logs-fred logs-zillow logs-redfin logs-census logs-tax

SAM = sam
STACK = mini-app-etl
PY_DIRS = lambdas/
MYPY_TARGETS = lambdas/layer/python/shared/ \
               lambdas/census_demographics/app.py \
               lambdas/fred_mortgage_rates/app.py \
               lambdas/zillow_zhvi/app.py \
               lambdas/redfin_market/app.py \
               lambdas/nj_tax_rates/app.py

# ── Build & Deploy ──────────────────────────────────────────────────

build:
	$(SAM) build

deploy: build
	$(SAM) deploy --no-confirm-changeset

# ── Linting ─────────────────────────────────────────────────────────

# Run all checks (ruff + isort + black + mypy + eslint)
lint: lint-py typecheck lint-js

lint-py:
	python -m ruff check $(PY_DIRS)
	python -m isort --check-only $(PY_DIRS)
	python -m black --check $(PY_DIRS)

lint-js:
	cd vercel-api && npx eslint api/ lib/

typecheck:
	python -m mypy $(MYPY_TARGETS) --explicit-package-bases

# Auto-fix Python lint + formatting
lint-fix:
	python -m ruff check $(PY_DIRS) --fix
	python -m isort $(PY_DIRS)
	python -m black $(PY_DIRS)

format:
	python -m isort $(PY_DIRS)
	python -m black $(PY_DIRS)

# ── Invoke (remote, deployed functions) ─────────────────────────────

invoke-fred:
	aws lambda invoke --function-name mini-app-fred-mortgage-rates --payload '{}' /dev/stdout

invoke-zillow:
	aws lambda invoke --function-name mini-app-zillow-zhvi --payload '{}' --cli-read-timeout 300 /dev/stdout

invoke-redfin:
	aws lambda invoke --function-name mini-app-redfin-market --payload '{}' --cli-read-timeout 900 /dev/stdout

invoke-census:
	aws lambda invoke --function-name mini-app-census-demographics --payload '{}' --cli-read-timeout 300 /dev/stdout

invoke-tax:
	aws lambda invoke --function-name mini-app-nj-tax-rates --payload-file tax_payload.json /dev/stdout

# ── Logs (last 10 min) ─────────────────────────────────────────────

logs-fred:
	aws logs tail /aws/lambda/mini-app-fred-mortgage-rates --since 10m --format short

logs-zillow:
	aws logs tail /aws/lambda/mini-app-zillow-zhvi --since 10m --format short

logs-redfin:
	aws logs tail /aws/lambda/mini-app-redfin-market --since 10m --format short

logs-census:
	aws logs tail /aws/lambda/mini-app-census-demographics --since 10m --format short

logs-tax:
	aws logs tail /aws/lambda/mini-app-nj-tax-rates --since 10m --format short

# ── Local testing (requires Docker) ────────────────────────────────

local-fred:
	$(SAM) local invoke FredMortgageRatesFunction

local-census:
	$(SAM) local invoke CensusDemographicsFunction --event '{"year": 2023}'

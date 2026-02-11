.PHONY: build deploy deploy-quick lint lint-py lint-js lint-fix \
       invoke-fred invoke-zillow invoke-redfin invoke-census invoke-tax \
       logs-fred logs-zillow logs-redfin logs-census logs-tax

SAM = sam
STACK = mini-app-etl

# ── Build & Deploy ──────────────────────────────────────────────────

build:
	$(SAM) build

deploy: build
	$(SAM) deploy --no-confirm-changeset

# Quick deploy: build + deploy without confirmation
deploy-quick: deploy

# Deploy a single function (rebuild all, but only changed functions update)
deploy-fn: build
	$(SAM) deploy --no-confirm-changeset

# ── Linting ─────────────────────────────────────────────────────────

lint: lint-py lint-js

lint-py:
	python -m ruff check lambdas/

lint-js:
	cd vercel-api && npx eslint api/ lib/ --ext .js

lint-fix:
	python -m ruff check lambdas/ --fix
	cd vercel-api && npx eslint api/ lib/ --ext .js --fix

format:
	python -m ruff format lambdas/

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

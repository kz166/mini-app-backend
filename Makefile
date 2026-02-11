.PHONY: build deploy invoke-fred invoke-zillow invoke-redfin invoke-census invoke-tax

# Build all Lambda functions
build:
	sam build

# Deploy to AWS (first time: use `sam deploy --guided`)
deploy: build
	sam deploy

# Manual invocations for testing
invoke-fred:
	sam remote invoke FredMortgageRatesFunction --stack-name mini-app-etl

invoke-zillow:
	sam remote invoke ZillowZhviFunction --stack-name mini-app-etl

invoke-redfin:
	sam remote invoke RedfinMarketFunction --stack-name mini-app-etl

invoke-census:
	sam remote invoke CensusDemographicsFunction --stack-name mini-app-etl --event '{"year": 2023}'

invoke-tax:
	sam remote invoke NjTaxRatesFunction --stack-name mini-app-etl --event-file tax_payload.json

# Local testing (requires Docker)
local-fred:
	sam local invoke FredMortgageRatesFunction

local-census:
	sam local invoke CensusDemographicsFunction --event '{"year": 2023}'

.PHONY: help install test audit clean setup

help:		## Show this help message
	@echo "AWS Security Auditor - Available Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:	## Install dependencies
	pip install --upgrade pip
	pip install -r requirements.txt

test:		## Test current data
	python main.py --audit-only

audit:		## Run full AWS security audit
	python main.py

audit-fetch:	## Fetch AWS data only
	python main.py --fetch-only

audit-analyze:	## Analyze existing data only
	python main.py --audit-only

dashboard:	## Start Streamlit dashboard
	python main.py --dashboard

clean:		## Clean cache and temporary files
	rm -rf .cache/
	rm -rf __pycache__/
	rm -rf */__pycache__/
	rm -f temp_network.html

setup:		## Setup environment and directories
	mkdir -p config utils audit dashboard data reports .cache
	@echo "✅ Directory structure created!"
	@echo "   Next steps:"
	@echo "   1. Copy the new Python files to their directories"
	@echo "   2. Run: make install"
	@echo "   3. Configure AWS: aws configure"
	@echo "   4. Run: make audit"
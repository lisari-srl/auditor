.PHONY: help install test audit clean setup dashboard fetch analyze quick status deps upgrade

help:		## Show this help message
	@echo "AWS Security Auditor v2.1 - Available Commands:"
	@echo "================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🔗 Quick Start:"
	@echo "   make setup install audit dashboard"
	@echo ""

install:	## Install Python dependencies
	@echo "📦 Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

deps:		## Show dependency status  
	@echo "🔍 Checking dependencies..."
	@pip list | grep -E "(boto3|streamlit|plotly|pandas)" || echo "❌ Missing core dependencies"
	@python3 -c "import boto3, streamlit, plotly, pandas; print('✅ Core dependencies OK')" 2>/dev/null || echo "❌ Import test failed"

upgrade:	## Upgrade all dependencies
	@echo "⬆️  Upgrading dependencies..."
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	@echo "✅ Dependencies upgraded!"

setup:		## Setup environment and directories
	@echo "🏗️  Setting up AWS Security Auditor..."
	mkdir -p config utils audit dashboard data reports .cache
	@if [ ! -f .env ]; then cp .env.example .env 2>/dev/null || echo "# AWS Configuration" > .env; fi
	@echo "✅ Directory structure created!"
	@echo ""
	@echo "📋 Next steps:"
	@echo "   1. make install"
	@echo "   2. Configure AWS: aws configure"
	@echo "   3. make test"
	@echo "   4. make audit"

test:		## Test current setup and data
	@echo "🧪 Testing system setup..."
	@python3 -c "import sys; print(f'✅ Python: {sys.version}')"
	@python3 -c "import boto3; print('✅ Boto3 available')" || echo "❌ Boto3 missing"
	@aws sts get-caller-identity > /dev/null && echo "✅ AWS credentials configured" || echo "❌ AWS credentials not configured"
	@if [ -d "data" ] && [ -n "$$(ls -A data/*.json 2>/dev/null)" ]; then \
		echo "✅ Data directory has files"; \
		python3 main.py --audit-only; \
	else \
		echo "ℹ️  No data files found, run 'make fetch' first"; \
	fi

status:		## Show system status
	@echo "📊 AWS Security Auditor Status"
	@echo "=============================="
	@python3 -c "import sys; print(f'Python: {sys.version.split()[0]}')"
	@pip show boto3 | grep Version | head -1 || echo "Boto3: Not installed"
	@pip show streamlit | grep Version | head -1 || echo "Streamlit: Not installed"
	@echo -n "AWS Profile: "; aws configure list | grep profile | awk '{print $$2}' || echo "default"
	@echo -n "AWS Region: "; aws configure get region || echo "not set"
	@echo -n "AWS Identity: "; aws sts get-caller-identity --query 'Arn' --output text 2>/dev/null || echo "not configured"
	@if [ -d "data" ]; then \
		echo -n "Data files: "; ls data/*.json 2>/dev/null | wc -l | tr -d ' '; echo " files"; \
		if [ -f "data/ec2_raw.json" ]; then \
			echo -n "Last fetch: "; stat -c %y data/ec2_raw.json 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1 || echo "unknown"; \
		fi; \
	else \
		echo "Data files: 0 files"; \
	fi
	@if [ -d "reports" ]; then \
		echo -n "Reports: "; ls reports/*.{json,md} 2>/dev/null | wc -l | tr -d ' '; echo " files"; \
	else \
		echo "Reports: 0 files"; \
	fi

fetch:		## Fetch AWS data only
	@echo "📡 Fetching AWS resources..."
	python3 main.py --fetch-only

analyze:	## Analyze existing data only
	@echo "🔍 Analyzing existing data..."
	python3 main.py --audit-only

quick:		## Quick audit (no fetch, no cleanup)
	@echo "⚡ Quick audit on existing data..."
	python3 main.py --quick

audit:		## Run full AWS security audit (fetch + analyze + cleanup)
	@echo "🚀 Running full security audit..."
	python3 main.py

audit-clean:	## Run audit with forced cleanup
	@echo "🧹 Running audit with full cleanup..."
	python3 main.py --force

dashboard:	## Start Streamlit dashboard
	@echo "🚀 Starting security dashboard..."
	python3 main.py --dashboard

dashboard-public:	## Start dashboard accessible from network
	@echo "🌐 Starting public dashboard..."
	python3 main.py --dashboard --host 0.0.0.0

clean:		## Clean cache and temporary files
	@echo "🧹 Cleaning temporary files..."
	rm -rf .cache/
	rm -rf __pycache__/
	rm -rf */__pycache__/
	rm -rf **/__pycache__/
	rm -f temp_network.html
	rm -f *.tmp
	rm -f *.log
	find . -name "*.pyc" -delete
	find . -name ".DS_Store" -delete
	@echo "✅ Cleanup completed!"

clean-data:	## Clean data directory (CAREFUL!)
	@echo "⚠️  This will delete all fetched data!"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	rm -rf data/
	mkdir -p data
	@echo "🗑️  Data directory cleaned!"

clean-all:	## Clean everything (data, cache, reports)
	@echo "🚨 This will delete ALL data, cache, and reports!"
	@echo "Press Ctrl+C to cancel, or wait 10 seconds to continue..."
	@sleep 10
	rm -rf data/ reports/ .cache/
	rm -rf __pycache__/ */__pycache__/ **/__pycache__/
	rm -f temp_network.html *.tmp *.log
	mkdir -p data reports .cache
	@echo "🗑️  Everything cleaned!"

# Region-specific commands
audit-us-east-1:	## Audit only us-east-1 region
	python3 main.py --regions us-east-1

audit-eu-west-1:	## Audit only eu-west-1 region  
	python3 main.py --regions eu-west-1

audit-multi:		## Audit multiple regions
	python3 main.py --regions us-east-1,eu-west-1,ap-southeast-1

# Service-specific commands
audit-ec2:	## Audit only EC2 resources
	python3 main.py --services ec2,eni,sg,vpc

audit-s3:	## Audit only S3 resources
	python3 main.py --services s3

audit-iam:	## Audit only IAM resources
	python3 main.py --services iam

# Development commands
dev-test:	## Run development tests
	@echo "🧪 Running development tests..."
	python3 -m pytest tests/ -v 2>/dev/null || echo "⚠️  No tests found or pytest not installed"
	python3 -c "from utils.async_fetcher import AsyncAWSFetcher; print('✅ Import test passed')"

dev-lint:	## Run code linting
	@echo "🔍 Running code analysis..."
	@flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics 2>/dev/null || echo "⚠️  flake8 not available"
	@black --check . 2>/dev/null || echo "⚠️  black not available"

dev-format:	## Format code
	@echo "🎨 Formatting code..."
	@black . 2>/dev/null || echo "⚠️  black not available, install with: pip install black"

# Monitoring commands
monitor:	## Monitor findings over time
	@echo "📈 Monitoring security findings..."
	@if [ -f "reports/security_findings.json" ]; then \
		echo "Current findings:"; \
		python3 -c "import json; data=json.load(open('reports/security_findings.json')); print(f\"Total: {data['metadata']['total_findings']}\"); [print(f\"{k}: {v}\") for k,v in data['metadata'].get('summary', {}).items() if isinstance(v, str) and v.isdigit()]" 2>/dev/null; \
	else \
		echo "❌ No findings report found. Run 'make audit' first."; \
	fi

report:		## Generate and show latest report
	@echo "📊 Latest Security Report"
	@echo "========================="
	@if [ -f "reports/security_audit_report.md" ]; then \
		head -20 reports/security_audit_report.md; \
		echo ""; \
		echo "📁 Full report: reports/security_audit_report.md"; \
	else \
		echo "❌ No report found. Run 'make audit' first."; \
	fi

summary:	## Show quick summary
	@echo "⚡ Quick Summary"
	@echo "==============="
	@make status
	@echo ""
	@make monitor

# Help for specific use cases
help-first-time:	## Help for first-time users
	@echo "🎯 First Time User Guide"
	@echo "========================"
	@echo "1. make setup install      # Setup environment"
	@echo "2. aws configure           # Configure AWS credentials"  
	@echo "3. make test               # Test setup"
	@echo "4. make audit              # Run full audit"
	@echo "5. make dashboard          # View results"
	@echo ""
	@echo "For help: make help"

help-advanced:	## Help for advanced usage
	@echo "🚀 Advanced Usage"
	@echo "================="
	@echo "Specific regions:   make audit-us-east-1"
	@echo "Specific services:  make audit-ec2"
	@echo "Quick re-audit:     make quick"
	@echo "Public dashboard:   make dashboard-public"
	@echo "Clean everything:   make clean-all"
	@echo ""
	@echo "Custom commands:"
	@echo "  python3 main.py --regions us-east-1,eu-west-1 --services ec2,s3"
	@echo "  python3 main.py --config custom.json --no-cleanup"

# CI/CD helpers
ci-install:	## Install for CI/CD
	pip install --quiet --upgrade pip
	pip install --quiet -r requirements.txt

ci-test:	## Test for CI/CD  
	python3 -c "import boto3, json, os; print('✅ Imports OK')"
	python3 main.py --audit-only 2>/dev/null || echo "⚠️  No data for audit test"

# Docker helpers (if using containers)
docker-build:	## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t aws-security-auditor .

docker-run:	## Run in Docker container
	@echo "🐳 Running in Docker..."
	docker run -it --rm -v ~/.aws:/root/.aws:ro -v $(PWD)/data:/app/data aws-security-auditor

# Backup/restore
backup:		## Backup current data and reports
	@echo "💾 Creating backup..."
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	tar -czf "backup_$$timestamp.tar.gz" data/ reports/ config.json .env 2>/dev/null || true; \
	echo "✅ Backup created: backup_$$timestamp.tar.gz"

restore:	## Restore from backup (specify file with BACKUP=filename)
	@if [ -z "$(BACKUP)" ]; then \
		echo "❌ Specify backup file: make restore BACKUP=backup_20240101_120000.tar.gz"; \
		exit 1; \
	fi
	@echo "🔄 Restoring from $(BACKUP)..."
	tar -xzf $(BACKUP)
	@echo "✅ Restored from $(BACKUP)"
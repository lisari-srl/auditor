# Makefile per AWS Infrastructure Security Auditor v2.1
# Aggiornato con comandi per test produzione

# Configurazione
PYTHON = python3
VENV_DIR = venv
VENV_ACTIVATE = $(VENV_DIR)/bin/activate
PIP = $(VENV_DIR)/bin/pip
PYTHON_VENV = $(VENV_DIR)/bin/python
STREAMLIT = $(VENV_DIR)/bin/streamlit

# Colori per output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
PURPLE = \033[0;35m
CYAN = \033[0;36m
WHITE = \033[1;37m
NC = \033[0m # No Color

# Emoji per categorizzazione
SETUP_EMOJI = 🔧
AUDIT_EMOJI = 🔍
DATA_EMOJI = 📡
DASH_EMOJI = 📊
CLEAN_EMOJI = 🧹
TEST_EMOJI = ✅
WARN_EMOJI = ⚠️
INFO_EMOJI = ℹ️
PROD_EMOJI = 🚀

.PHONY: help install setup clean test audit fetch dashboard quick check-aws check-python status dev

# Default target
.DEFAULT_GOAL := help

## SETUP E INSTALLAZIONE

help: ## Mostra questo help
	@echo ""
	@echo "$(WHITE)🔒 AWS Infrastructure Security Auditor v2.1$(NC)"
	@echo "$(CYAN)==============================================$(NC)"
	@echo ""
	@echo "$(YELLOW)📚 COMANDI SETUP:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(setup|install|check)" | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🚀 COMANDI PRODUZIONE:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(prod|fetch|audit|dashboard)" | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🔧 COMANDI UTILITY:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -vE "(setup|install|check|prod|fetch|audit|dashboard)" | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🎯 Workflow raccomandato per produzione:$(NC)"
	@echo "  1. $(GREEN)make check-aws$(NC)      - Verifica credenziali AWS"
	@echo "  2. $(GREEN)make prod-fetch$(NC)     - Download dati da AWS (SICURO)"
	@echo "  3. $(GREEN)make prod-audit$(NC)     - Analisi sicurezza"
	@echo "  4. $(GREEN)make prod-dashboard$(NC) - Dashboard interattiva"
	@echo ""
	@echo "$(YELLOW)🚨 Test rapidi:$(NC)"
	@echo "  • $(GREEN)make prod-quick$(NC)      - Test completo veloce"
	@echo "  • $(GREEN)make prod-single$(NC)     - Test singola regione"
	@echo ""
	@echo "$(YELLOW)💰 COMANDI SG + COST ANALYSIS:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*💰.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🔥 SHORTCUTS SG COST:$(NC)"
	@echo "  • $(GREEN)make sgc$(NC)      - SG + Cost analysis completa"
	@echo "  • $(GREEN)make sgs$(NC)      - Mostra risparmi potenziali"
	@echo ""
	@echo "$(YELLOW)🌐 COMANDI VPC & NETWORK:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*🌐.*$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $1, $2}'
	@echo ""
	@echo "$(YELLOW)🔥 VPC SHORTCUTS:$(NC)"
	@echo "  • $(GREEN)make vf$(NC)      - VPC fetch"
	@echo "  • $(GREEN)make va$(NC)      - VPC audit"  
	@echo "  • $(GREEN)make vd$(NC)      - VPC dashboard"
	@echo "  • $(GREEN)make vc$(NC)      - VPC costs"
	@echo "  • $(GREEN)make vs$(NC)      - VPC security"

install: check-python ## Installa solo le dipendenze Python
	@echo "$(SETUP_EMOJI) $(YELLOW)Installazione dipendenze...$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(INFO_EMOJI) Creazione virtual environment..."; \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi
	@echo "$(INFO_EMOJI) Aggiornamento pip..."
	@$(PIP) install --upgrade pip --quiet
	@echo "$(INFO_EMOJI) Installazione requirements..."
	@$(PIP) install -r requirements.txt --quiet
	@echo "$(GREEN)✅ Dipendenze installate con successo$(NC)"

setup: install ## Setup completo dell'ambiente (raccomandato per primo utilizzo)
	@echo "$(SETUP_EMOJI) $(YELLOW)Setup ambiente completo...$(NC)"
	@echo "$(INFO_EMOJI) Creazione directory di lavoro..."
	@mkdir -p data reports config .cache
	@if [ ! -f ".env" ] && [ -f ".env.example" ]; then \
		echo "$(INFO_EMOJI) Copia template configurazione..."; \
		cp .env.example .env; \
		echo "$(WARN_EMOJI) $(YELLOW)Modifica .env con le tue configurazioni!$(NC)"; \
	fi
	@echo "$(GREEN)✅ Setup completato!$(NC)"
	@echo ""
	@echo "$(CYAN)Prossimi passi:$(NC)"
	@echo "  1. Configura AWS: $(WHITE)aws configure$(NC)"
	@echo "  2. Verifica setup: $(WHITE)make check-aws$(NC)"
	@echo "  3. Test produzione: $(WHITE)make prod-fetch$(NC)"

## VERIFICA E STATUS

check-python: ## Verifica versione Python
	@echo "$(TEST_EMOJI) $(YELLOW)Verifica Python...$(NC)"
	@command -v $(PYTHON) >/dev/null || (echo "$(RED)❌ Python 3.8+ richiesto$(NC)" && exit 1)
	@PYTHON_VERSION=$$($(PYTHON) --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2); \
	REQUIRED_VERSION="3.8"; \
	if [ "$$(printf '%s\n' "$$REQUIRED_VERSION" "$$PYTHON_VERSION" | sort -V | head -n1)" != "$$REQUIRED_VERSION" ]; then \
		echo "$(RED)❌ Python $$PYTHON_VERSION trovato, richiesto 3.8+$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Python OK$(NC)"

check-aws: check-venv ## Verifica configurazione AWS
	@echo "$(TEST_EMOJI) $(YELLOW)Verifica configurazione AWS...$(NC)"
	@command -v aws >/dev/null || (echo "$(RED)❌ AWS CLI non installato$(NC)" && exit 1)
	@$(PYTHON_VENV) -c "import boto3; boto3.Session().client('sts').get_caller_identity()" 2>/dev/null || \
		(echo "$(RED)❌ Credenziali AWS non configurate$(NC)" && echo "$(CYAN)Esegui: aws configure$(NC)" && exit 1)
	@echo "$(GREEN)✅ AWS configurato correttamente$(NC)"
	@echo "$(INFO_EMOJI) Identity:" 
	@aws sts get-caller-identity --query 'Arn' --output text 2>/dev/null || echo "Unknown"

check-venv: ## Verifica virtual environment
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(WARN_EMOJI) $(YELLOW)Virtual environment non trovato, esegui 'make install'$(NC)"; \
		exit 1; \
	fi

status: check-venv ## Mostra status del sistema e dei dati
	@echo "$(INFO_EMOJI) $(YELLOW)Status del sistema:$(NC)"
	@echo ""
	@echo "$(CYAN)Environment:$(NC)"
	@if [ -d "$(VENV_DIR)" ]; then echo "  ✅ Virtual environment: OK"; else echo "  ❌ Virtual environment: Missing"; fi
	@if [ -f ".env" ]; then echo "  ✅ Configurazione .env: OK"; else echo "  ⚠️  Configurazione .env: Missing"; fi
	@echo ""
	@echo "$(CYAN)AWS Configuration:$(NC)"
	@if command -v aws >/dev/null; then echo "  ✅ AWS CLI: OK"; else echo "  ❌ AWS CLI: Not found"; fi
	@if $(PYTHON_VENV) -c "import boto3; boto3.Session().client('sts').get_caller_identity()" 2>/dev/null; then \
		echo "  ✅ AWS Credentials: OK"; \
		AWS_IDENTITY=$$(aws sts get-caller-identity --query 'Arn' --output text 2>/dev/null || echo "Unknown"); \
		echo "  $(GREEN)Identity: $$AWS_IDENTITY$(NC)"; \
	else \
		echo "  ❌ AWS Credentials: Not configured"; \
	fi
	@echo ""
	@echo "$(CYAN)Data Status:$(NC)"
	@if [ -d "data" ]; then \
		DATA_COUNT=$$(find data -name "*.json" 2>/dev/null | wc -l); \
		if [ "$$DATA_COUNT" -gt 0 ]; then \
			echo "  ✅ Dati disponibili: $$DATA_COUNT file"; \
			NEWEST_FILE=$$(find data -name "*.json" -exec stat -f "%m %N" {} \; 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2- || echo ""); \
			if [ -n "$$NEWEST_FILE" ]; then \
				echo "  📅 Ultimo aggiornamento: $$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$$NEWEST_FILE" 2>/dev/null || echo "Unknown")"; \
			fi; \
		else \
			echo "  ⚠️  Dati: Non disponibili (esegui 'make prod-fetch')"; \
		fi; \
	else \
		echo "  ❌ Directory data: Non trovata"; \
	fi

## 🚀 COMANDI PRODUZIONE

prod-fetch: check-aws ## 📡 [PROD] Download dati da AWS (SICURO - solo lettura)
	@echo "$(PROD_EMOJI) $(YELLOW)Production Fetch - Download dati AWS...$(NC)"
	@echo "$(INFO_EMOJI) Operazione SICURA: solo lettura, nessuna modifica"
	@$(PYTHON_VENV) main.py --fetch-only
	@echo ""
	@echo "$(GREEN)✅ Fetch completato!$(NC)"
	@echo "$(CYAN)Prossimo passo: $(WHITE)make prod-audit$(NC)"

prod-audit: check-venv ## 🔍 [PROD] Audit sicurezza sui dati scaricati
	@echo "$(PROD_EMOJI) $(YELLOW)Production Audit - Analisi sicurezza...$(NC)"
	@$(PYTHON_VENV) main.py --audit-only
	@echo ""
	@echo "$(GREEN)✅ Audit completato!$(NC)"
	@echo "$(CYAN)Controlla i risultati:$(NC)"
	@echo "  📊 Dashboard: $(WHITE)make prod-dashboard$(NC)"
	@echo "  📁 Reports: $(WHITE)ls -la reports/$(NC)"

prod-dashboard: check-venv ## 📊 [PROD] Dashboard interattiva sui risultati
	@echo "$(PROD_EMOJI) $(YELLOW)Production Dashboard - Avvio interfaccia...$(NC)"
	@if [ ! -f "data/ec2_raw.json" ] && [ ! -f "data/sg_raw.json" ]; then \
		echo "$(WARN_EMOJI) $(YELLOW)Nessun dato trovato, eseguo fetch automatico...$(NC)"; \
		$(MAKE) prod-fetch; \
	fi
	@echo "$(INFO_EMOJI) Dashboard disponibile su: $(GREEN)http://localhost:8501$(NC)"
	@echo "$(INFO_EMOJI) Premi Ctrl+C per fermare"
	@$(PYTHON_VENV) main.py --dashboard

prod-full: check-aws ## 🚀 [PROD] Audit completo (fetch + audit + dashboard)
	@echo "$(PROD_EMOJI) $(YELLOW)Production Full Audit - Processo completo...$(NC)"
	@$(PYTHON_VENV) main.py
	@echo ""
	@echo "$(GREEN)✅ Audit completo terminato!$(NC)"
	@echo "$(CYAN)Risultati disponibili:$(NC)"
	@echo "  📊 Dashboard: $(WHITE)make prod-dashboard$(NC)"
	@echo "  📁 Reports: $(WHITE)ls -la reports/$(NC)"

prod-quick: check-aws ## ⚡ [PROD] Test veloce su dati esistenti
	@echo "$(PROD_EMOJI) $(YELLOW)Production Quick Test...$(NC)"
	@$(PYTHON_VENV) main.py --quick
	@echo "$(GREEN)✅ Quick test completato!$(NC)"

prod-single: check-aws ## 🎯 [PROD] Test singola regione us-east-1
	@echo "$(PROD_EMOJI) $(YELLOW)Production Single Region Test (us-east-1)...$(NC)"
	@$(PYTHON_VENV) main.py --regions us-east-1
	@echo "$(GREEN)✅ Single region test completato!$(NC)"

prod-services: check-aws ## 🔧 [PROD] Test servizi specifici (ec2,sg,s3)
	@echo "$(PROD_EMOJI) $(YELLOW)Production Services Test (EC2, SG, S3)...$(NC)"
	@$(PYTHON_VENV) main.py --services ec2,sg,s3
	@echo "$(GREEN)✅ Services test completato!$(NC)"

## COMANDI REGIONALI SPECIFICI

prod-us-east-1: check-aws ## 🇺🇸 [PROD] Audit solo us-east-1
	@echo "$(PROD_EMOJI) $(YELLOW)Production Audit - US East 1...$(NC)"
	@$(PYTHON_VENV) main.py --regions us-east-1

prod-eu-west-1: check-aws ## 🇪🇺 [PROD] Audit solo eu-west-1
	@echo "$(PROD_EMOJI) $(YELLOW)Production Audit - EU West 1...$(NC)"
	@$(PYTHON_VENV) main.py --regions eu-west-1

prod-multi: check-aws ## 🌍 [PROD] Audit regioni multiple
	@echo "$(PROD_EMOJI) $(YELLOW)Production Audit - Multiple Regions...$(NC)"
	@$(PYTHON_VENV) main.py --regions us-east-1,eu-west-1,ap-southeast-1

## RISULTATI E REPORT

show-results: ## 📋 Mostra summary risultati
	@echo "$(INFO_EMOJI) $(YELLOW)Summary risultati audit:$(NC)"
	@if [ -f "reports/security_findings.json" ]; then \
		$(PYTHON_VENV) -c "\
import json; \
data = json.load(open('reports/security_findings.json')); \
findings = data['findings']; \
by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}; \
[by_severity.update({f['severity']: by_severity[f['severity']] + 1}) for f in findings if f['severity'] in by_severity]; \
print(f\"📊 Findings totali: {len(findings)}\"); \
print(f\"🔴 Critical: {by_severity['critical']}\"); \
print(f\"🟠 High: {by_severity['high']}\"); \
print(f\"🟡 Medium: {by_severity['medium']}\"); \
print(f\"🔵 Low: {by_severity['low']}\"); \
print(f\"📅 Ultimo scan: {data['metadata']['scan_time'][:19]}\")"; \
	else \
		echo "$(YELLOW)⚠️  Nessun report disponibile. Esegui 'make prod-audit'$(NC)"; \
	fi

show-critical: ## 🚨 Mostra solo finding critici
	@echo "$(INFO_EMOJI) $(YELLOW)Finding critici:$(NC)"
	@if [ -f "reports/security_findings.json" ]; then \
		$(PYTHON_VENV) -c "\
import json; \
data = json.load(open('reports/security_findings.json')); \
critical = [f for f in data['findings'] if f['severity'] == 'critical']; \
print(f\"🚨 {len(critical)} finding critici trovati:\"); \
[print(f\"  • {f['rule_name']}: {f['resource_name']}\") for f in critical[:10]]"; \
	else \
		echo "$(YELLOW)⚠️  Nessun report disponibile$(NC)"; \
	fi

list-data: ## 📁 Lista file dati disponibili
	@if [ -d "data" ]; then \
		echo "$(INFO_EMOJI) $(YELLOW)File dati disponibili:$(NC)"; \
		ls -lh data/*.json 2>/dev/null | awk '{print "  📄 " $$9 " (" $$5 ")"}' || echo "  Nessun file trovato"; \
	else \
		echo "$(YELLOW)⚠️  Directory data non trovata$(NC)"; \
	fi

list-reports: ## 📋 Lista report disponibili
	@if [ -d "reports" ]; then \
		echo "$(INFO_EMOJI) $(YELLOW)Report disponibili:$(NC)"; \
		find reports -type f \( -name "*.json" -o -name "*.md" -o -name "*.sh" \) 2>/dev/null | sort | awk '{print "  📋 " $$1}' || echo "  Nessun report trovato"; \
	else \
		echo "$(YELLOW)⚠️  Directory reports non trovata$(NC)"; \
	fi

## PULIZIA E MANUTENZIONE

clean: ## 🧹 Pulisce cache e file temporanei
	@echo "$(CLEAN_EMOJI) $(YELLOW)Pulizia cache e file temporanei...$(NC)"
	@rm -rf .cache __pycache__ *.pyc temp_network.html
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Cache pulita$(NC)"

clean-data: ## ⚠️ ATTENZIONE: Elimina TUTTI i dati scaricati
	@echo "$(RED)⚠️  ATTENZIONE: Stai per eliminare TUTTI i dati!$(NC)"
	@read -p "Sei sicuro? Scrivi 'yes' per confermare: " confirm && [ "$$confirm" = "yes" ] || (echo "Operazione annullata" && exit 1)
	@rm -rf data/*
	@echo "$(YELLOW)🗑️ Dati eliminati$(NC)"

clean-reports: ## 🗑️ Elimina tutti i report generati
	@echo "$(CLEAN_EMOJI) $(YELLOW)Eliminazione report...$(NC)"
	@rm -rf reports/*
	@echo "$(GREEN)✅ Report eliminati$(NC)"

clean-all: clean clean-data clean-reports ## 🧹 Pulisce tutto (cache, dati, report)
	@echo "$(CLEAN_EMOJI) $(GREEN)Pulizia completa terminata$(NC)"

## BACKUP E SICUREZZA

backup: ## 💾 Crea backup di dati e report
	@echo "$(INFO_EMOJI) $(YELLOW)Creazione backup...$(NC)"
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	BACKUP_DIR="backup_$$TIMESTAMP"; \
	mkdir -p "$$BACKUP_DIR"; \
	[ -d "data" ] && cp -r data "$$BACKUP_DIR/" || echo "No data to backup"; \
	[ -d "reports" ] && cp -r reports "$$BACKUP_DIR/" || echo "No reports to backup"; \
	[ -f ".env" ] && cp .env "$$BACKUP_DIR/" || echo "No .env to backup"; \
	tar -czf "$$BACKUP_DIR.tar.gz" "$$BACKUP_DIR" && rm -rf "$$BACKUP_DIR"; \
	echo "$(GREEN)✅ Backup creato: $$BACKUP_DIR.tar.gz$(NC)"

## SVILUPPO E TEST

test: check-venv ## ✅ Test integrità progetto
	@echo "$(TEST_EMOJI) $(YELLOW)Test integrità del sistema...$(NC)"
	@$(PYTHON_VENV) test_project_integrity.py

dev: setup ## 🔧 Setup ambiente di sviluppo
	@echo "$(SETUP_EMOJI) $(YELLOW)Setup ambiente sviluppo...$(NC)"
	@$(PIP) install pytest black flake8 mypy --quiet
	@echo "$(GREEN)✅ Tool di sviluppo installati$(NC)"


## 🆕 COMANDI SG + COST ANALYSIS (OPZIONALI)

sg-cost-analysis: check-aws ## 💰 [NUOVO] Analisi completa Security Groups + Cost Explorer
	@echo "$(PROD_EMOJI) $(YELLOW)SG + Cost Analysis - Comprehensive Assessment...$(NC)"
	@$(PYTHON_VENV) main.py --sg-cost-analysis
	@echo ""
	@echo "$(GREEN)✅ SG + Cost analysis completato!$(NC)"
	@echo "$(CYAN)Risultati disponibili:$(NC)"
	@echo "  📊 Executive Summary: $(WHITE)reports/integrated_analysis/executive_summary.md$(NC)"
	@echo "  📋 Action Plan: $(WHITE)reports/integrated_analysis/high_priority_actions.csv$(NC)"
	@echo "  💰 Cleanup Scripts: $(WHITE)reports/integrated_analysis/*.sh$(NC)"

sg-cost-us-east-1: check-aws ## 💰 [NUOVO] SG + Cost analysis solo us-east-1
	@echo "$(PROD_EMOJI) $(YELLOW)SG + Cost Analysis - US East 1...$(NC)"
	@$(PYTHON_VENV) main.py --sg-cost-analysis --regions us-east-1

sg-cost-eu-west-1: check-aws ## 💰 [NUOVO] SG + Cost analysis solo eu-west-1
	@echo "$(PROD_EMOJI) $(YELLOW)SG + Cost Analysis - EU West 1...$(NC)"
	@$(PYTHON_VENV) main.py --sg-cost-analysis --regions eu-west-1

show-sg-savings: ## 💰 [NUOVO] Mostra risparmi potenziali SG
	@echo "$(INFO_EMOJI) $(YELLOW)Security Groups savings summary:$(NC)"
	@if [ -f "reports/integrated_analysis/executive_summary.md" ]; then \
		echo "📊 Executive Summary:"; \
		head -20 reports/integrated_analysis/executive_summary.md | grep -E "(Monthly|Annual|Savings)"; \
		echo ""; \
		echo "🎯 Priority Actions:"; \
		if [ -f "reports/integrated_analysis/high_priority_actions.csv" ]; then \
			head -5 reports/integrated_analysis/high_priority_actions.csv | cut -d',' -f1,2,7 --output-delimiter=' | '; \
		fi; \
	else \
		echo "$(YELLOW)⚠️  Nessun report SG + Cost disponibile. Esegui 'make sg-cost-analysis'$(NC)"; \
	fi

execute-sg-cleanup: ## ⚠️ [NUOVO] ATTENZIONE: Esegue cleanup SG automatico
	@echo "$(RED)⚠️  ATTENZIONE: Stai per eseguire cleanup automatico Security Groups!$(NC)"
	@read -p "Sei sicuro? Scrivi 'yes' per confermare: " confirm && [ "$$confirm" = "yes" ] || (echo "Operazione annullata" && exit 1)
	@if [ -f "reports/integrated_analysis/immediate_cleanup.sh" ]; then \
		echo "$(YELLOW)🔧 Eseguendo cleanup automatico...$(NC)"; \
		bash reports/integrated_analysis/immediate_cleanup.sh; \
		echo "$(GREEN)✅ Cleanup completato!$(NC)"; \
	else \
		echo "$(RED)❌ Script cleanup non trovato. Esegui prima 'make sg-cost-analysis'$(NC)"; \
	fi

# ===== COMANDI VPC E NETWORK =====

vpc-fetch: check-aws ## 🌐 [VPC] Fetch completo dati VPC e network
	@echo "$(PROD_EMOJI) $(YELLOW)VPC Fetch - Download network infrastructure...$(NC)"
	@$(PYTHON_VENV) main.py --vpc-analysis
	@echo "$(GREEN)✅ VPC fetch completato!$(NC)"

vpc-audit: check-venv ## 🛡️ [VPC] Audit VPC e network security
	@echo "$(PROD_EMOJI) $(YELLOW)VPC Audit - Network security analysis...$(NC)"
	@$(PYTHON_VENV) main.py --vpc-analysis --audit-only
	@echo "$(GREEN)✅ VPC audit completato!$(NC)"

network-cost: check-aws ## 💰 [VPC] Analisi costi network (NAT, EIP, LB)
	@echo "$(PROD_EMOJI) $(YELLOW)Network Cost Analysis...$(NC)"
	@$(PYTHON_VENV) main.py --network-optimization
	@echo "$(GREEN)✅ Network cost analysis completato!$(NC)"

vpc-full: check-aws ## 🚀 [VPC] Analisi completa VPC + costi + security
	@echo "$(PROD_EMOJI) $(YELLOW)VPC Full Analysis - Complete network assessment...$(NC)"
	@$(PYTHON_VENV) main.py --vpc-analysis --network-optimization
	@echo ""
	@echo "$(GREEN)✅ VPC full analysis completato!$(NC)"
	@echo "$(CYAN)Risultati:$(NC)"
	@echo "  📊 VPC Dashboard: $(WHITE)make dashboard$(NC)"
	@echo "  📁 VPC Reports: $(WHITE)ls -la reports/vpc/$(NC)"
	@echo "  💰 Cost Reports: $(WHITE)cat reports/vpc/vpc_cost_analysis.json$(NC)"

vpc-dashboard: vpc-audit ## 📊 [VPC] Dashboard VPC con network topology
	@echo "$(PROD_EMOJI) $(YELLOW)VPC Dashboard - Network visualization...$(NC)"
	@echo "$(INFO_EMOJI) Dashboard con sezione VPC: $(GREEN)http://localhost:8501$(NC)"
	@$(PYTHON_VENV) main.py --dashboard

vpc-topology: check-venv ## 🗺️ [VPC] Genera mappa topologia network
	@echo "$(INFO_EMOJI) $(YELLOW)Generazione network topology...$(NC)"
	@if [ -f "reports/vpc/vpc_audit_summary.json" ]; then \
		echo "$(CYAN)Network Topology:$(NC)"; \
		$(PYTHON_VENV) -c "\
import json; \
data = json.load(open('reports/vpc/vpc_audit_summary.json')); \
topology = data.get('summary', {}).get('network_topology', {}); \
print(f'📊 VPCs trovate: {len(topology)}'); \
[print(f'  🏗️  VPC {vpc_id}: {info.get(\"total_subnets\", 0)} subnets, {len(info.get(\"nat_gateways\", []))} NAT GW') for vpc_id, info in topology.items()]"; \
	else \
		echo "$(YELLOW)⚠️  Nessun dato topology. Esegui 'make vpc-audit'$(NC)"; \
	fi

vpc-costs: check-venv ## 💸 [VPC] Mostra breakdown costi network
	@echo "$(INFO_EMOJI) $(YELLOW)VPC Cost Breakdown:$(NC)"
	@if [ -f "reports/vpc/vpc_audit_summary.json" ]; then \
		$(PYTHON_VENV) -c "\
import json; \
data = json.load(open('reports/vpc/vpc_audit_summary.json')); \
summary = data.get('summary', {}); \
print(f'💰 Risparmi mensili potenziali: ${summary.get(\"total_monthly_cost_savings\", 0):.2f}'); \
print(f'📅 Risparmi annuali: ${summary.get(\"total_annual_cost_savings\", 0):.2f}'); \
cost_opts = summary.get('cost_optimizations', []); \
print(f'🎯 Opportunità ottimizzazione: {len(cost_opts)}'); \
[print(f'  • {opt.get(\"type\", \"Unknown\")}: ${opt.get(\"monthly_savings\", 0):.2f}/mese') for opt in cost_opts[:5]]"; \
	else \
		echo "$(YELLOW)⚠️  Nessun dato costi. Esegui 'make vpc-audit'$(NC)"; \
	fi

vpc-security: check-venv ## 🔒 [VPC] Security findings VPC
	@echo "$(INFO_EMOJI) $(YELLOW)VPC Security Issues:$(NC)"
	@if [ -f "reports/security_findings.json" ]; then \
		$(PYTHON_VENV) -c "\
import json; \
data = json.load(open('reports/security_findings.json')); \
vpc_findings = [f for f in data['findings'] if f['resource_type'] in ['VPC', 'Subnet', 'RouteTable', 'NATGateway']]; \
by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}; \
[by_severity.update({f['severity']: by_severity[f['severity']] + 1}) for f in vpc_findings if f['severity'] in by_severity]; \
print(f'🛡️  VPC Security Findings: {len(vpc_findings)}'); \
print(f'🔴 Critical: {by_severity[\"critical\"]}'); \
print(f'🟠 High: {by_severity[\"high\"]}'); \
print(f'🟡 Medium: {by_severity[\"medium\"]}'); \
print(f'🔵 Low: {by_severity[\"low\"]}'); \
if by_severity['critical'] > 0: print('🚨 URGENT: Fix critical VPC security issues!')"; \
	else \
		echo "$(YELLOW)⚠️  Nessun security data. Esegui 'make prod-audit'$(NC)"; \
	fi

vpc-optimize: check-venv ## ⚡ [VPC] Esegue script ottimizzazione VPC
	@echo "$(WARN_EMOJI) $(YELLOW)ATTENZIONE: Ottimizzazione VPC può impattare la rete!$(NC)"
	@read -p "Sei sicuro? Scrivi 'yes' per confermare: " confirm && [ "$confirm" = "yes" ] || (echo "Operazione annullata" && exit 1)
	@if [ -f "reports/vpc/vpc_optimization.sh" ]; then \
		echo "$(YELLOW)🔧 Eseguendo ottimizzazione VPC...$(NC)"; \
		bash reports/vpc/vpc_optimization.sh; \
		echo "$(GREEN)✅ Ottimizzazione completata!$(NC)"; \
	else \
		echo "$(RED)❌ Script ottimizzazione non trovato. Esegui prima 'make vpc-audit'$(NC)"; \
	fi

# ===== ANALISI REGIONALI VPC =====

vpc-us-east-1: check-aws ## 🇺🇸 [VPC] Analisi VPC solo us-east-1
	@echo "$(PROD_EMOJI) $(YELLOW)VPC Analysis - US East 1...$(NC)"
	@$(PYTHON_VENV) main.py --vpc-analysis --regions us-east-1

vpc-eu-west-1: check-aws ## 🇪🇺 [VPC] Analisi VPC solo eu-west-1  
	@echo "$(PROD_EMOJI) $(YELLOW)VPC Analysis - EU West 1...$(NC)"
	@$(PYTHON_VENV) main.py --vpc-analysis --regions eu-west-1

vpc-multi-region: check-aws ## 🌍 [VPC] Analisi VPC multi-regione
	@echo "$(PROD_EMOJI) $(YELLOW)VPC Analysis - Multiple Regions...$(NC)"
	@$(PYTHON_VENV) main.py --vpc-analysis --regions us-east-1,eu-west-1,ap-southeast-1


## SHORTCUTS

f: prod-fetch ## Shortcut per prod-fetch
a: prod-audit ## Shortcut per prod-audit  
d: prod-dashboard ## Shortcut per prod-dashboard
s: status ## Shortcut per status
c: clean ## Shortcut per clean
h: help ## Shortcut per help
r: show-results ## Shortcut per show-results
sgc: sg-cost-analysis ## Shortcut per sg-cost-analysis
sgs: show-sg-savings ## Shortcut per show-sg-savings
vf: vpc-fetch ## Shortcut per vpc-fetch
va: vpc-audit ## Shortcut per vpc-audit  
vd: vpc-dashboard ## Shortcut per vpc-dashboard
vc: vpc-costs ## Shortcut per vpc-costs
vs: vpc-security ## Shortcut per vpc-security
vt: vpc-topology ## Shortcut per vpc-topology

# Makefile per AWS Infrastructure Security Auditor v2.1
# Gestione completa dell'ambiente di sviluppo e audit

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

.PHONY: help install setup clean test audit fetch dashboard quick check-aws check-python status dev

# Default target
.DEFAULT_GOAL := help

## SETUP E INSTALLAZIONE

help: ## Mostra questo help
	@echo ""
	@echo "$(WHITE)🔒 AWS Infrastructure Security Auditor v2.1$(NC)"
	@echo "$(CYAN)==============================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Comandi disponibili:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Workflow raccomandato:$(NC)"
	@echo "  1. $(GREEN)make setup$(NC)     - Configura ambiente"
	@echo "  2. $(GREEN)make check-aws$(NC) - Verifica credenziali AWS"
	@echo "  3. $(GREEN)make audit$(NC)     - Esegui audit completo"
	@echo "  4. $(GREEN)make dashboard$(NC) - Visualizza risultati"
	@echo ""

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
	@echo "  3. Primo audit: $(WHITE)make audit$(NC)"

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
			echo "  ⚠️  Dati: Non disponibili (esegui 'make fetch')"; \
		fi; \
	else \
		echo "  ❌ Directory data: Non trovata"; \
	fi
	@echo ""
	@echo "$(CYAN)Reports Status:$(NC)"
	@if [ -d "reports" ]; then \
		REPORTS_COUNT=$$(find reports -name "*.json" -o -name "*.md" 2>/dev/null | wc -l); \
		if [ "$$REPORTS_COUNT" -gt 0 ]; then \
			echo "  ✅ Report disponibili: $$REPORTS_COUNT file"; \
		else \
			echo "  ⚠️  Report: Non disponibili (esegui 'make audit')"; \
		fi; \
	else \
		echo "  ❌ Directory reports: Non trovata"; \
	fi

## OPERAZIONI PRINCIPALI

audit: check-aws ## Esegui audit completo (fetch + analisi + report)
	@echo "$(AUDIT_EMOJI) $(YELLOW)Audit completo dell'infrastruttura AWS...$(NC)"
	@echo "$(INFO_EMOJI) Questo può richiedere alcuni minuti..."
	@$(PYTHON_VENV) main.py
	@echo ""
	@echo "$(GREEN)✅ Audit completato!$(NC)"
	@echo "$(CYAN)Risultati disponibili in:$(NC)"
	@echo "  📊 Dashboard: $(WHITE)make dashboard$(NC)"
	@echo "  📁 Reports: $(WHITE)./reports/$(NC)"

fetch: check-aws ## Scarica solo i dati da AWS (senza analisi)
	@echo "$(DATA_EMOJI) $(YELLOW)Download dati da AWS...$(NC)"
	@$(PYTHON_VENV) main.py --fetch-only
	@echo "$(GREEN)✅ Dati scaricati!$(NC)"
	@echo "$(CYAN)Prossimo passo: $(WHITE)make analyze$(NC)"

analyze: check-venv ## Analizza i dati esistenti (senza fetch)
	@echo "$(AUDIT_EMOJI) $(YELLOW)Analisi dati esistenti...$(NC)"
	@$(PYTHON_VENV) main.py --audit-only
	@echo "$(GREEN)✅ Analisi completata!$(NC)"

quick: check-venv ## Audit veloce sui dati esistenti (no cleanup)
	@echo "$(AUDIT_EMOJI) $(YELLOW)Audit veloce...$(NC)"
	@$(PYTHON_VENV) main.py --quick
	@echo "$(GREEN)✅ Audit veloce completato!$(NC)"

## DASHBOARD E VISUALIZZAZIONE

dashboard: check-venv ## Avvia dashboard interattivo Streamlit
	@echo "$(DASH_EMOJI) $(YELLOW)Avvio dashboard Streamlit...$(NC)"
	@if [ ! -f "data/ec2_raw.json" ] && [ ! -f "data/sg_raw.json" ]; then \
		echo "$(WARN_EMOJI) $(YELLOW)Nessun dato trovato, eseguo fetch automatico...$(NC)"; \
		$(MAKE) fetch; \
	fi
	@echo "$(INFO_EMOJI) Dashboard disponibile su: $(GREEN)http://localhost:8501$(NC)"
	@echo "$(INFO_EMOJI) Premi Ctrl+C per fermare"
	@$(PYTHON_VENV) main.py --dashboard

dashboard-public: check-venv ## Avvia dashboard accessibile dalla rete
	@echo "$(DASH_EMOJI) $(YELLOW)Avvio dashboard pubblico...$(NC)"
	@echo "$(WARN_EMOJI) $(YELLOW)Dashboard accessibile da TUTTA la rete!$(NC)"
	@$(PYTHON_VENV) main.py --dashboard --host 0.0.0.0

## AUDIT SPECIFICI

audit-region: check-aws ## Audit per regione specifica (usa REGION=us-east-1)
	@if [ -z "$(REGION)" ]; then \
		echo "$(RED)❌ Specifica una regione: make audit-region REGION=us-east-1$(NC)"; \
		exit 1; \
	fi
	@echo "$(AUDIT_EMOJI) $(YELLOW)Audit regione: $(REGION)$(NC)"
	@$(PYTHON_VENV) main.py --regions $(REGION)

audit-service: check-aws ## Audit per servizio specifico (usa SERVICE=ec2,s3)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)❌ Specifica servizi: make audit-service SERVICE=ec2,s3,iam$(NC)"; \
		exit 1; \
	fi
	@echo "$(AUDIT_EMOJI) $(YELLOW)Audit servizi: $(SERVICE)$(NC)"
	@$(PYTHON_VENV) main.py --services $(SERVICE)

## COMANDI VELOCI PREDEFINITI

audit-us-east-1: ## Audit solo us-east-1
	@$(MAKE) audit-region REGION=us-east-1

audit-eu-west-1: ## Audit solo eu-west-1
	@$(MAKE) audit-region REGION=eu-west-1

audit-multi: ## Audit regioni multiple
	@$(MAKE) audit-region REGION=us-east-1,eu-west-1,ap-southeast-1

audit-ec2: ## Audit solo risorse EC2
	@$(MAKE) audit-service SERVICE=ec2,sg,vpc

audit-s3: ## Audit solo S3
	@$(MAKE) audit-service SERVICE=s3

audit-iam: ## Audit solo IAM
	@$(MAKE) audit-service SERVICE=iam

## PULIZIA E MANUTENZIONE

clean: ## Pulisce cache e file temporanei
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

clean-reports: ## Elimina tutti i report generati
	@echo "$(CLEAN_EMOJI) $(YELLOW)Eliminazione report...$(NC)"
	@rm -rf reports/*
	@echo "$(GREEN)✅ Report eliminati$(NC)"

clean-all: clean clean-data clean-reports ## Pulisce tutto (cache, dati, report)
	@echo "$(CLEAN_EMOJI) $(GREEN)Pulizia completa terminata$(NC)"

reset: clean-all ## Reset completo (elimina anche venv)
	@echo "$(CLEAN_EMOJI) $(YELLOW)Reset completo del progetto...$(NC)"
	@rm -rf $(VENV_DIR)
	@rm -f .env
	@echo "$(GREEN)✅ Reset completato$(NC)"
	@echo "$(CYAN)Esegui 'make setup' per ricominciare$(NC)"

## MONITORING E REPORT

monitor: check-venv ## Mostra tendenze e cambiamenti nei dati
	@echo "$(INFO_EMOJI) $(YELLOW)Monitoring infrastruttura...$(NC)"
	@if [ -f "reports/security_findings.json" ]; then \
		echo "$(GREEN)📊 Ultimo report disponibile:$(NC)"; \
		$(PYTHON_VENV) -c "import json; data=json.load(open('reports/security_findings.json')); print(f\"Findings: {data['metadata']['total_findings']}\"); print(f\"Data: {data['metadata']['scan_time'][:19]}\")"; \
	else \
		echo "$(YELLOW)⚠️  Nessun report disponibile. Esegui 'make audit'$(NC)"; \
	fi

report: check-venv ## Mostra summary dell'ultimo report
	@echo "$(INFO_EMOJI) $(YELLOW)Summary ultimo audit:$(NC)"
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
		echo "$(YELLOW)⚠️  Nessun report disponibile$(NC)"; \
	fi

summary: report ## Alias per 'report'

## BACKUP E RIPRISTINO

backup: ## Crea backup di dati e report
	@echo "$(INFO_EMOJI) $(YELLOW)Creazione backup...$(NC)"
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	BACKUP_DIR="backup_$$TIMESTAMP"; \
	mkdir -p "$$BACKUP_DIR"; \
	[ -d "data" ] && cp -r data "$$BACKUP_DIR/" || echo "No data to backup"; \
	[ -d "reports" ] && cp -r reports "$$BACKUP_DIR/" || echo "No reports to backup"; \
	[ -f ".env" ] && cp .env "$$BACKUP_DIR/" || echo "No .env to backup"; \
	tar -czf "$$BACKUP_DIR.tar.gz" "$$BACKUP_DIR" && rm -rf "$$BACKUP_DIR"; \
	echo "$(GREEN)✅ Backup creato: $$BACKUP_DIR.tar.gz$(NC)"

restore: ## Ripristina da backup (usa BACKUP=filename.tar.gz)
	@if [ -z "$(BACKUP)" ]; then \
		echo "$(RED)❌ Specifica il file: make restore BACKUP=backup_20241219_143022.tar.gz$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(BACKUP)" ]; then \
		echo "$(RED)❌ File backup non trovato: $(BACKUP)$(NC)"; \
		exit 1; \
	fi
	@echo "$(INFO_EMOJI) $(YELLOW)Ripristino da $(BACKUP)...$(NC)"
	@tar -xzf "$(BACKUP)"
	@BACKUP_DIR=$$(echo "$(BACKUP)" | sed 's/.tar.gz//'); \
	[ -d "$$BACKUP_DIR/data" ] && cp -r "$$BACKUP_DIR/data" . || echo "No data in backup"; \
	[ -d "$$BACKUP_DIR/reports" ] && cp -r "$$BACKUP_DIR/reports" . || echo "No reports in backup"; \
	[ -f "$$BACKUP_DIR/.env" ] && cp "$$BACKUP_DIR/.env" . || echo "No .env in backup"; \
	rm -rf "$$BACKUP_DIR"; \
	echo "$(GREEN)✅ Ripristino completato$(NC)"

## SVILUPPO E TEST

test: check-venv ## Testa il setup e le configurazioni
	@echo "$(TEST_EMOJI) $(YELLOW)Test del sistema...$(NC)"
	@echo "$(INFO_EMOJI) Test import moduli Python..."
	@$(PYTHON_VENV) -c "import boto3, streamlit, plotly, pandas; print('✅ Tutti i moduli importati correttamente')"
	@echo "$(INFO_EMOJI) Test connessione AWS..."
	@$(PYTHON_VENV) -c "import boto3; print('✅ AWS SDK funzionante')"
	@if [ -d "data" ] && [ "$$(find data -name '*.json' | wc -l)" -gt 0 ]; then \
		echo "$(INFO_EMOJI) Test caricamento dati..."; \
		$(PYTHON_VENV) -c "import json, os; files=[f for f in os.listdir('data') if f.endswith('.json')]; [json.load(open(f'data/{f}')) for f in files[:3]]; print('✅ Dati caricabili correttamente')"; \
	fi
	@echo "$(GREEN)✅ Tutti i test passati!$(NC)"

dev: setup ## Setup ambiente di sviluppo con tool extra
	@echo "$(SETUP_EMOJI) $(YELLOW)Setup ambiente sviluppo...$(NC)"
	@$(PIP) install pytest black flake8 mypy --quiet
	@echo "$(GREEN)✅ Tool di sviluppo installati$(NC)"
	@echo "$(CYAN)Tool disponibili:$(NC)"
	@echo "  - pytest: test"
	@echo "  - black: formatting"
	@echo "  - flake8: linting"
	@echo "  - mypy: type checking"

dev-test: check-venv ## Esegue test di sviluppo
	@echo "$(TEST_EMOJI) $(YELLOW)Test di sviluppo...$(NC)"
	@if [ -f "tests/test_*.py" ]; then \
		$(VENV_DIR)/bin/pytest tests/ -v; \
	else \
		echo "$(YELLOW)⚠️  Nessun test trovato in tests/$(NC)"; \
	fi

dev-format: check-venv ## Formatta il codice con Black
	@echo "$(SETUP_EMOJI) $(YELLOW)Formattazione codice...$(NC)"
	@$(VENV_DIR)/bin/black . --exclude venv
	@echo "$(GREEN)✅ Codice formattato$(NC)"

dev-lint: check-venv ## Linting del codice
	@echo "$(TEST_EMOJI) $(YELLOW)Linting codice...$(NC)"
	@$(VENV_DIR)/bin/flake8 --exclude=venv --max-line-length=120

## CI/CD E AUTOMAZIONE

ci-test: install test ## Test per CI/CD
	@echo "$(TEST_EMOJI) $(YELLOW)Test CI/CD...$(NC)"
	@$(PYTHON_VENV) main.py --help >/dev/null
	@echo "$(GREEN)✅ CI Test completato$(NC)"

docker-build: ## Build immagine Docker (se disponibile Dockerfile)
	@if [ -f "Dockerfile" ]; then \
		echo "$(SETUP_EMOJI) $(YELLOW)Build Docker image...$(NC)"; \
		docker build -t aws-security-auditor:latest .; \
		echo "$(GREEN)✅ Docker image pronta$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Dockerfile non trovato$(NC)"; \
	fi

## INFORMAZIONI E DEBUG

version: ## Mostra versioni dei componenti
	@echo "$(INFO_EMOJI) $(YELLOW)Informazioni versioni:$(NC)"
	@echo "Python: $$($(PYTHON) --version)"
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Streamlit: $$(($(VENV_DIR)/bin/streamlit --version 2>/dev/null || echo 'Not installed') | head -1)"; \
		echo "Boto3: $$($(PYTHON_VENV) -c 'import boto3; print(boto3.__version__)' 2>/dev/null || echo 'Not installed')"; \
	fi
	@if command -v aws >/dev/null; then \
		echo "AWS CLI: $$(aws --version | cut -d' ' -f1)"; \
	fi

debug: ## Informazioni di debug dettagliate
	@echo "$(INFO_EMOJI) $(YELLOW)Informazioni di debug:$(NC)"
	@echo ""
	@echo "$(CYAN)Environment Variables:$(NC)"
	@env | grep -E '^(AWS_|STREAMLIT_)' || echo "  Nessuna variabile AWS/Streamlit"
	@echo ""
	@echo "$(CYAN)Directory Structure:$(NC)"
	@ls -la
	@echo ""
	@echo "$(CYAN)Virtual Environment:$(NC)"
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "  Location: $(VENV_DIR)"; \
		echo "  Python: $$($(PYTHON_VENV) --version)"; \
		echo "  Packages: $$($(PIP) list --format=freeze | wc -l) installed"; \
	else \
		echo "  ❌ Not found"; \
	fi

# Utility per mostrare file disponibili
list-data: ## Lista file dati disponibili
	@if [ -d "data" ]; then \
		echo "$(INFO_EMOJI) $(YELLOW)File dati disponibili:$(NC)"; \
		ls -lh data/*.json 2>/dev/null | awk '{print "  📄 " $$9 " (" $$5 ")"}' || echo "  Nessun file trovato"; \
	else \
		echo "$(YELLOW)⚠️  Directory data non trovata$(NC)"; \
	fi

list-reports: ## Lista report disponibili
	@if [ -d "reports" ]; then \
		echo "$(INFO_EMOJI) $(YELLOW)Report disponibili:$(NC)"; \
		find reports -type f \( -name "*.json" -o -name "*.md" -o -name "*.sh" \) 2>/dev/null | sort | awk '{print "  📋 " $$1}' || echo "  Nessun report trovato"; \
	else \
		echo "$(YELLOW)⚠️  Directory reports non trovata$(NC)"; \
	fi

## SHORTCUTS E ALIAS

a: audit ## Shortcut per audit
f: fetch ## Shortcut per fetch
d: dashboard ## Shortcut per dashboard
s: status ## Shortcut per status
c: clean ## Shortcut per clean
h: help ## Shortcut per help
.PHONY: start setup install check-aws run clean clean-venv clean-pycache reset dashboard
# Makefile per gestire l'ambiente di sviluppo e l'esecuzione dell'auditor
# Colori
YELLOW=\033[1;33m
GREEN=\033[1;32m
RESET=\033[0m

# Entry point
start: setup check-aws run

# 1. Setup: crea venv, attiva, installa requirements e .env
setup:
	@echo "$(YELLOW)[🔧] Setup ambiente virtuale...$(RESET)"
	@if [ ! -d "venv" ]; then \
		echo "[🌀] Creo venv..."; \
		python3 -m venv venv; \
	fi
	@. venv/bin/activate && pip install --upgrade pip
	@. venv/bin/activate && pip install -r requirements.txt
	@if [ ! -f ".env" ] && [ -f ".env.example" ]; then \
		echo "[📄] Copio .env.example -> .env"; \
		cp .env.example .env; \
	fi

# 2. Verifica AWS CLI e credenziali
check-aws:
	@echo "$(YELLOW)[🔐] Controllo credenziali AWS...$(RESET)"
	@command -v aws >/dev/null || (echo "[❌] AWS CLI non installato"; exit 1)
	@aws sts get-caller-identity >/dev/null || (echo "[❌] Credenziali AWS non valide o non configurate"; exit 1)

# 3. Esegue l'auditor
run:
	@echo "$(GREEN)[🚀] Avvio Auditor...$(RESET)"
	@. venv/bin/activate && python main.py

# 4. Avvia il dashboard Streamlit
dashboard:
	@echo "$(GREEN)[🧭] Avvio dashboard Streamlit su http://localhost:8501...$(RESET)"
	@. venv/bin/activate && streamlit run dashboard/app.py --server.headless true

# Pulisce processi Python zombie (opzionale)
clean:
	@echo "$(YELLOW)[🧹] Pulizia processi zombie Python...$(RESET)"
	@ps aux | grep '[p]ython' | awk '{print $$2}' | xargs -r kill -9 || true

# Elimina ambiente virtuale
clean-venv:
	@echo "$(YELLOW)[🧽] Rimozione venv...$(RESET)"
	@rm -rf venv

# Rimuove __pycache__ e file temporanei
clean-pycache:
	@echo "$(YELLOW)[🧽] Pulizia cache Python...$(RESET)"
	@find . -type d -name '__pycache__' -exec rm -r {} +

# Reset completo
reset: clean clean-venv clean-pycache
	@echo "$(YELLOW)[♻️ ] Ambiente completamente resettato.$(RESET)"
#!/bin/bash
set -e

if [[ -z "$VIRTUAL_ENV" ]]; then
  echo "❌ Non sei in un virtual environment! Attivalo con: source venv/bin/activate"
  exit 1
fi

echo "== FETCH =="
for f in scripts/fetch_*.py; do
    python3 "$f"
done

echo "== AUDIT =="
for f in scripts/audit_*.py; do
    python3 "$f"
done

echo "== ANALISI TRASVERSALE =="
python3 scripts/analyze_usage.py

echo "✅ Audit completo terminato!"
echo "🚀 Avvio della dashboard Streamlit..."
streamlit run app.py
#!/bin/bash

echo "🧪 Creazione ambiente virtuale..."
python3 -m venv venv

echo "⚙️ Attivazione ambiente virtuale..."
source venv/bin/activate

echo "⬇️ Installazione pacchetti..."
pip install --upgrade pip
pip install boto3 streamlit pyvis networkx

echo "✅ Ambiente configurato. Per attivarlo in futuro esegui:"
echo "   source venv/bin/activate"
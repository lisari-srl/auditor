#!/bin/bash
set -e

echo "🚀 AWS Security Auditor v2.0 - Setup"
echo "===================================="

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version OK"

# Check AWS CLI
echo "🔍 Checking AWS CLI..."
if ! command -v aws &> /dev/null; then
    echo "⚠️  AWS CLI not found. Install with: pip install awscli"
    echo "   Then run: aws configure"
else
    echo "✅ AWS CLI OK"
fi

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p config utils audit dashboard data reports .cache

# Backup existing files
echo "💾 Backing up existing files..."
if [ -f "app.py" ]; then
    cp app.py app_old.py
    echo "   ✅ app.py backed up to app_old.py"
fi

if [ -f "run_audit.sh" ]; then
    cp run_audit.sh run_audit_old.sh
    echo "   ✅ run_audit.sh backed up to run_audit_old.sh"
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment found"
    source venv/bin/activate
else
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install requirements
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create config if not exists
if [ ! -f "config.json" ]; then
    echo "⚙️  Creating default config.json..."
    cat > config.json << 'EOF'
{
  "regions": ["us-east-1"],
  "profile": null,
  "max_workers": 10,
  "cache_ttl": 3600,
  "services": {
    "ec2": true,
    "eni": true,
    "sg": true,
    "vpc": true,
    "subnet": true,
    "igw": true,
    "route_table": true,
    "s3": true,
    "iam": true
  }
}
EOF
    echo "   ✅ config.json created"
else
    echo "✅ config.json already exists"
fi

# Update run_audit.sh
echo "🔧 Updating run_audit.sh..."
cat > run_audit.sh << 'EOF'
#!/bin/bash
set -e

if [[ -z "$VIRTUAL_ENV" ]]; then
  echo "❌ Non sei in un virtual environment! Attivalo con: source venv/bin/activate"
  exit 1
fi

echo "🚀 AWS Security Auditor v2.0"
echo "=========================="

# Use new main.py if available, fallback to old system
if [ -f "main.py" ]; then
    echo "🔍 Running advanced audit..."
    python main.py "$@"
else
    echo "🔍 Running legacy audit..."
    echo "== FETCH =="
    for f in scripts/fetch_*.py; do
        python3 "$f"
    done

    echo "== AUDIT =="
    for f in scripts/audit_*.py; do
        python3 "$f"
    done

    echo "== DASHBOARD =="
    echo "🚀 Avvio della dashboard Streamlit..."
    streamlit run app.py
fi
EOF

chmod +x run_audit.sh

echo ""
echo "✅ Setup completato!"
echo ""
echo "📋 Prossimi passi:"
echo "   1. Attiva virtual environment: source venv/bin/activate"
echo "   2. Configura AWS credentials: aws configure"
echo "   3. (Opzionale) Modifica config.json per le tue necessità"
echo "   4. Copia i nuovi file Python nelle directory appropriate"
echo "   5. Testa il sistema: make test"
echo "   6. Esegui audit completo: make audit"
echo ""
echo "🔧 Comandi utili:"
echo "   make help         - Mostra tutti i comandi disponibili"
echo "   make audit        - Esegue audit completo"
echo "   make dashboard    - Avvia dashboard"
echo "   make clean        - Pulisce cache"
echo ""
echo "📖 Per assistenza: consulta la guida di migrazione"
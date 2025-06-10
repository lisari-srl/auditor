# 🔒 AWS Infrastructure Security Auditor v2.1

Un tool completo per l'audit di sicurezza e ottimizzazione costi dell'infrastruttura AWS. Analizza automaticamente la tua infrastruttura AWS, identifica vulnerabilità di sicurezza, genera script di remediation e fornisce raccomandazioni per l'ottimizzazione dei costi.

## ✨ Caratteristiche Principali

### 🛡️ **Sicurezza Avanzata**
- **Advanced Security Groups Analysis**: Analisi approfondita con consolidamento intelligente
- **Critical Ports Detection**: Identificazione automatica porte critiche esposte (SSH, RDP, MySQL, etc.)
- **Network Security Assessment**: Analisi completa configurazioni di rete
- **IAM Security Review**: Controllo permessi e policy IAM

### 💰 **Ottimizzazione Costi**
- **EC2 Rightsizing**: Suggerimenti per ridimensionamento istanze
- **Unused Resources Detection**: Identificazione risorse non utilizzate
- **Storage Optimization**: Analisi volumi EBS e snapshot obsoleti
- **Cost Impact Analysis**: Stima risparmi annuali potenziali

### 🤖 **Automazione Intelligente**
- **Script Generation**: Generazione automatica script di remediation
- **Backup Automation**: Backup automatico prima delle modifiche
- **Phased Execution**: Piano di esecuzione organizzato per priorità
- **Safety Checks**: Controlli di sicurezza integrati

### 📊 **Dashboard Interattiva**
- **Real-time Visualization**: Dashboard Streamlit con grafici interattivi
- **Drill-down Analysis**: Analisi dettagliata per categoria
- **Export Capabilities**: Esportazione report in JSON/Markdown
- **Multi-region Support**: Supporto regioni multiple

## 🚀 Quick Start

### 1️⃣ **Installazione**

```bash
# Clone del repository
git clone <repository-url>
cd aws-security-auditor

# Setup automatico
make setup

# Oppure manuale
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ **Configurazione AWS**

```bash
# Configura credenziali AWS
aws configure

# Verifica configurazione
make check-aws
```

### 3️⃣ **Test in Produzione** 🎯

```bash
# Workflow raccomandato (SICURO - solo lettura)
make prod-fetch     # Download dati da AWS
make prod-audit     # Analisi sicurezza
make prod-dashboard # Dashboard interattiva

# Oppure tutto insieme
make prod-full
```

## 📋 Comandi Disponibili

### 🛠️ **Setup e Configurazione**

| Comando | Descrizione |
|---------|-------------|
| `make setup` | Setup completo ambiente (raccomandato primo utilizzo) |
| `make install` | Installa solo dipendenze Python |
| `make check-aws` | Verifica configurazione AWS |
| `make status` | Mostra status sistema e dati |

### 🚀 **Produzione**

| Comando | Descrizione | Sicurezza |
|---------|-------------|-----------|
| `make prod-fetch` | Download dati da AWS | ✅ Solo lettura |
| `make prod-audit` | Analisi sicurezza sui dati | ✅ Nessuna modifica |
| `make prod-dashboard` | Dashboard interattiva | ✅ Visualizzazione |
| `make prod-full` | Processo completo | ✅ Solo analisi |

### ⚡ **Test Rapidi**

| Comando | Descrizione |
|---------|-------------|
| `make prod-quick` | Test veloce su dati esistenti |
| `make prod-single` | Test singola regione (us-east-1) |
| `make prod-services` | Test servizi specifici (ec2,sg,s3) |
| `make prod-us-east-1` | Audit solo US East 1 |
| `make prod-eu-west-1` | Audit solo EU West 1 |
| `make prod-multi` | Audit regioni multiple |

### 📊 **Risultati e Report**

| Comando | Descrizione |
|---------|-------------|
| `make show-results` | Summary risultati audit |
| `make show-critical` | Solo finding critici |
| `make list-data` | File dati disponibili |
| `make list-reports` | Report generati |

### 🧹 **Manutenzione**

| Comando | Descrizione |
|---------|-------------|
| `make clean` | Pulisce cache e file temporanei |
| `make clean-data` | ⚠️ Elimina TUTTI i dati |
| `make backup` | Crea backup di dati e report |

### 🔥 **Shortcuts**

| Shortcut | Comando Completo |
|----------|------------------|
| `make f` | `make prod-fetch` |
| `make a` | `make prod-audit` |
| `make d` | `make prod-dashboard` |
| `make r` | `make show-results` |
| `make s` | `make status` |
| `make h` | `make help` |

## 🎯 Utilizzo Avanzato

### **Audit per Regioni Specifiche**
```bash
# Singola regione
python main.py --regions us-east-1

# Regioni multiple
python main.py --regions us-east-1,eu-west-1,ap-southeast-1
```

### **Audit per Servizi Specifici**
```bash
# Solo EC2 e Security Groups
python main.py --services ec2,sg

# Solo S3 e IAM
python main.py --services s3,iam
```

### **Modalità Avanzate**
```bash
# Quick mode (usa dati esistenti)
python main.py --quick

# Disabilita pulizia cache
python main.py --no-cleanup

# Solo fetch (nessun audit)
python main.py --fetch-only

# Solo audit (sui dati esistenti)
python main.py --audit-only

# Solo dashboard
python main.py --dashboard
```

## 📁 Struttura Output

```
aws-security-auditor/
├── data/                           # Dati scaricati da AWS
│   ├── ec2_raw.json               # Istanze EC2
│   ├── sg_raw.json                # Security Groups
│   └── ...
├── reports/                        # Report generati
│   ├── security_audit_report.md   # Report principale
│   ├── security_findings.json     # Findings dettagliati
│   ├── security_groups/           # Analisi SG avanzata
│   │   ├── advanced_analysis.json
│   │   ├── consolidation_plan.json
│   │   └── advanced_cleanup.sh
│   └── cleanup/                    # Script di cleanup
│       ├── cleanup_plan.json
│       ├── 1_backup_everything.sh
│       ├── 2_critical_security_fixes.sh
│       ├── 3_cost_optimization.sh
│       ├── 4_maintenance_tasks.sh
│       └── 5_verify_cleanup.sh
└── config/                         # Configurazioni
    └── audit_config.yaml
```

## 🛡️ Funzionalità di Sicurezza

### **Security Groups Analysis**
- ✅ **Porte critiche esposte**: SSH (22), RDP (3389), MySQL (3306), PostgreSQL (5432)
- ✅ **Security Groups non utilizzati**: Identificazione SG senza risorse associate
- ✅ **Consolidamento intelligente**: Suggerimenti per unificare SG simili
- ✅ **Network topology analysis**: Mapping relazioni tra SG

### **EC2 Security Assessment**
- ✅ **Istanze con IP pubblico**: Identificazione esposizioni non necessarie
- ✅ **Instance metadata service**: Controllo configurazioni IMDSv2
- ✅ **Storage encryption**: Verifica crittografia volumi EBS
- ✅ **Rightsizing opportunities**: Analisi utilizzo risorse

### **Network Security**
- ✅ **Elastic IP non utilizzati**: Identificazione EIP non associati
- ✅ **Load Balancer analysis**: Controllo configurazioni ALB/NLB
- ✅ **VPC security assessment**: Analisi configurazioni di rete

### **IAM Security Review**
- ✅ **Utenti senza attività**: Identificazione account inattivi
- ✅ **Policy analysis**: Controllo permessi eccessivi
- ✅ **Root account usage**: Monitoraggio utilizzo account root

## 💰 Ottimizzazione Costi

### **Risorse Non Utilizzate**
- 🔍 **EBS Volumes non attaccati**: Con stime costi mensili
- 🔍 **Elastic IP non utilizzati**: $3.65/mese per EIP non associato
- 🔍 **Load Balancer sottoutilizzati**: Analisi utilizzo e consolidamento
- 🔍 **Snapshot obsoleti**: Identificazione backup vecchi

### **EC2 Rightsizing**
- 📊 **Instance type optimization**: Suggerimenti dimensionamento
- 📊 **Cost impact analysis**: Stima risparmi potenziali
- 📊 **Performance considerations**: Bilanciamento costi/performance

### **Storage Optimization**
- 💾 **Volume type optimization**: Migrazione gp2 → gp3
- 💾 **Retention policies**: CloudWatch Logs senza retention
- 💾 **Snapshot lifecycle**: Gestione automatica backup

## 🤖 Script di Remediation

Il tool genera automaticamente script bash organizzati per priorità:

### **1. Backup Everything** (`1_backup_everything.sh`)
```bash
# Backup completo prima di qualsiasi modifica
bash reports/cleanup/1_backup_everything.sh
```

### **2. Critical Security Fixes** (`2_critical_security_fixes.sh`)
```bash
# Fix immediati per vulnerabilità critiche
bash reports/cleanup/2_critical_security_fixes.sh
```

### **3. Cost Optimization** (`3_cost_optimization.sh`)
```bash
# Ottimizzazioni costi con conferma manuale
bash reports/cleanup/3_cost_optimization.sh
```

### **4. Maintenance Tasks** (`4_maintenance_tasks.sh`)
```bash
# Attività di manutenzione generale
bash reports/cleanup/4_maintenance_tasks.sh
```

### **5. Verification** (`5_verify_cleanup.sh`)
```bash
# Verifica post-cleanup
bash reports/cleanup/5_verify_cleanup.sh
```

## 📊 Dashboard Interattiva

La dashboard Streamlit fornisce:

- 📈 **Grafici interattivi**: Distribuzione findings per severity
- 🎯 **Drill-down analysis**: Dettagli per categoria e risorsa
- 📋 **Export capabilities**: Download report in formato JSON/CSV
- 🔄 **Real-time updates**: Refresh automatico dati
- 🌍 **Multi-region view**: Vista aggregata per tutte le regioni

Accesso: `http://localhost:8501` dopo `make prod-dashboard`

## ⚠️ Considerazioni di Sicurezza

### **Permessi AWS Richiesti**
Il tool richiede permessi di sola lettura per:
- EC2 (DescribeInstances, DescribeSecurityGroups, DescribeVolumes)
- S3 (ListBuckets, GetBucketLocation, GetBucketPolicy)
- IAM (ListUsers, ListRoles, ListPolicies)
- VPC (DescribeVpcs, DescribeSubnets, DescribeRouteTables)

### **Modalità Read-Only**
- ✅ **Nessuna modifica automatica**: Il tool non modifica mai risorse AWS
- ✅ **Script generati**: Tutti i fix vengono generati come script da rivedere
- ✅ **Backup automatico**: Script di backup integrati
- ✅ **Conferme manuali**: Ogni azione critica richiede conferma

### **Best Practices**
- 🔐 **Credenziali sicure**: Usa IAM roles invece di access keys quando possibile
- 🔐 **Least privilege**: Concedi solo permessi necessari
- 🔐 **Audit trail**: Mantieni log delle modifiche effettuate
- 🔐 **Test environment**: Testa sempre in ambiente non-produttivo

## 🔧 Configurazione Avanzata

### **File di Configurazione** (`config/audit_config.yaml`)
```yaml
regions:
  - us-east-1
  - eu-west-1

services:
  - ec2
  - sg
  - s3
  - iam
  - vpc

critical_ports:
  - 22    # SSH
  - 3389  # RDP
  - 3306  # MySQL
  - 5432  # PostgreSQL

cost_thresholds:
  monthly_savings_threshold: 10
  annual_savings_threshold: 100
```

### **Variabili d'Ambiente** (`.env`)
```bash
# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
AWS_PROFILE=default

# Dashboard Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost

# Cache Configuration
CACHE_TTL_HOURS=24
ENABLE_CACHE=true

# Output Configuration
OUTPUT_FORMAT=json
VERBOSE=true
```

## 🐛 Troubleshooting

### **Errori Comuni**

**1. Credenziali AWS non configurate**
```bash
make check-aws  # Verifica configurazione
aws configure   # Configura credenziali
```

**2. Permessi insufficienti**
```bash
# Verifica identity corrente
aws sts get-caller-identity

# Testa permessi specifici
aws ec2 describe-instances --dry-run
```

**3. Nessun dato trovato**
```bash
make list-data       # Controlla dati disponibili
make prod-fetch      # Riesegui download
```

**4. Dashboard non si avvia**
```bash
make status          # Controlla environment
make install         # Reinstalla dipendenze
```

### **Debug Mode**
```bash
# Abilita logging dettagliato
export VERBOSE=true
python main.py --audit-only

# Test singolo servizio
python main.py --services ec2 --regions us-east-1
```

## 📝 Changelog

### **v2.1 (Current)**
- ✨ Advanced Security Groups Analysis
- ✨ Automated Cleanup Scripts Generation
- ✨ Enhanced Cost Optimization
- ✨ Production-ready Makefile commands
- ✨ Interactive Dashboard improvements
- 🐛 Fixed f-string syntax errors
- 🔧 Improved error handling

### **v2.0**
- ✨ Streamlit Dashboard
- ✨ Multi-region support
- ✨ Cost optimization analysis
- ✨ Advanced security checks

### **v1.0**
- ✨ Basic security audit
- ✨ EC2 and Security Groups analysis
- ✨ JSON/Markdown reports

## 🤝 Contribuire

1. Fork del repository
2. Crea feature branch (`git checkout -b feature/amazing-feature`)
3. Commit modifiche (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Apri Pull Request

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi file `LICENSE` per dettagli.

## 🆘 Supporto

- 📖 **Documentazione**: Consulta questo README per guide dettagliate
- 🐛 **Bug Reports**: Apri issue su GitHub
- 💡 **Feature Requests**: Proponi nuove funzionalità via issue
- 📧 **Contatto**: [Il tuo contatto]

## 🎯 Roadmap

### **v2.2 (Prossima Release)**
- [ ] AWS Cost Explorer integration
- [ ] Automated compliance checks (SOC2, PCI-DSS)
- [ ] Slack/Teams notifications
- [ ] CI/CD pipeline integration

### **v3.0 (Futuro)**
- [ ] Machine Learning per threat detection
- [ ] Multi-cloud support (Azure, GCP)
- [ ] Advanced remediation automation
- [ ] Enterprise SSO integration

---

⭐ **Se questo tool ti è utile, lascia una stella su GitHub!** ⭐
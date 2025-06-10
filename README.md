# 🔒 AWS Infrastructure Security Auditor v2.1

Un tool completo per l'audit di sicurezza e ottimizzazione costi dell'infrastruttura AWS. Analizza automaticamente la tua infrastruttura AWS, identifica vulnerabilità di sicurezza, genera script di remediation e fornisce raccomandazioni per l'ottimizzazione dei costi.

## ✨ Caratteristiche Principali

### 🛡️ **Sicurezza Avanzata**
- **Advanced Security Groups Analysis**: Analisi approfondita con consolidamento intelligente
- **Critical Ports Detection**: Identificazione automatica porte critiche esposte (SSH, RDP, MySQL, etc.)
- **Network Security Assessment**: Analisi completa configurazioni di rete
- **IAM Security Review**: Controllo permessi e policy IAM

### 💰 **Ottimizzazione Costi Avanzata** 🆕
- **Security Groups + Cost Explorer Integration**: Analisi completa SG con dati costi reali AWS
- **Real-time Cost Analysis**: Utilizzo API Cost Explorer per dati costi attuali
- **Unused Resources Detection**: EIP, volumi EBS, Load Balancer non utilizzati
- **Executive Summary**: Report per management con ROI e timeline implementazione
- **Automated Cleanup Scripts**: Script bash automatici per cleanup sicuro

### 🤖 **Automazione Intelligente**
- **Script Generation**: Generazione automatica script di remediation
- **Backup Automation**: Backup automatico prima delle modifiche
- **Phased Execution**: Piano di esecuzione organizzato per priorità
- **Safety Checks**: Controlli di sicurezza integrati
- **Cost Monitoring Setup**: Configurazione automatica alerting costi

### 📊 **Dashboard Interattiva**
- **Real-time Visualization**: Dashboard Streamlit con grafici interattivi
- **Drill-down Analysis**: Analisi dettagliata per categoria
- **Export Capabilities**: Esportazione report in JSON/Markdown/CSV
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

**⚠️ Permessi Richiesti:**
- **ReadOnlyAccess** (policy AWS gestita) - per audit sicurezza
- **Cost Explorer Read Access** - per analisi costi reali 🆕
- **Billing Read Access** - per dati usage e fatturazione 🆕

### 3️⃣ **Test in Produzione** 🎯

```bash
# Workflow raccomandato (SICURO - solo lettura)
make prod-fetch     # Download dati da AWS
make prod-audit     # Analisi sicurezza
make prod-dashboard # Dashboard interattiva

# 🆕 NUOVO: Analisi completa SG + Costi
python main.py --sg-cost-analysis

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
| `python main.py --sg-cost-analysis` | 🆕 **Analisi SG + Costi completa** | ✅ Solo lettura |

### ⚡ **Test Rapidi**

| Comando | Descrizione |
|---------|-------------|
| `make prod-quick` | Test veloce su dati esistenti |
| `make prod-single` | Test singola regione (us-east-1) |
| `make prod-services` | Test servizi specifici (ec2,sg,s3) |
| `make prod-us-east-1` | Audit solo US East 1 |
| `make prod-eu-west-1` | Audit solo EU West 1 |
| `make prod-multi` | Audit regioni multiple |

### 💰 **Security Groups + Cost Analysis** 🆕

| Comando | Descrizione |
|---------|-------------|
| `python main.py --sg-cost-analysis` | Analisi completa SG + Cost Explorer |
| `python main.py --sg-cost-analysis --regions us-east-1,eu-west-1` | Multi-regione |
| `make sg-cost-analysis` | Shortcut Makefile (opzionale) |
| `make show-sg-savings` | Mostra summary risparmi |

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
| `make sgc` | `python main.py --sg-cost-analysis` 🆕 |
| `make r` | `make show-results` |
| `make s` | `make status` |
| `make h` | `make help` |

## 🎯 Utilizzo Avanzato

### **🆕 Security Groups + Cost Analysis Dettagliata**

```bash
# Analisi completa con Cost Explorer
python main.py --sg-cost-analysis --regions us-east-1

# Output:
# ├── reports/integrated_analysis/
# │   ├── executive_summary.md              # 👔 Per management
# │   ├── complete_sg_cost_report.json      # 📊 Dati completi
# │   ├── detailed_analysis.csv             # 📈 Per Excel
# │   ├── high_priority_actions.csv         # 🎯 Quick wins
# │   ├── immediate_cleanup.sh              # ⚡ Script automatico
# │   ├── setup_monitoring.sh               # 📊 Setup monitoring
# │   ├── validation.sh                     # ✅ Post-cleanup check
# │   └── calculate_savings.sh              # 💰 ROI calculation
```

### **Workflow Completo SG + Cost Optimization**

```bash
# 1. Analisi completa
python main.py --sg-cost-analysis

# 2. Review executive summary
cat reports/integrated_analysis/executive_summary.md

# 3. Priorità azioni
head -10 reports/integrated_analysis/high_priority_actions.csv

# 4. Backup (SEMPRE prima di modifiche!)
aws ec2 describe-security-groups > sg_backup_$(date +%Y%m%d).json

# 5. Cleanup sicuro
bash reports/integrated_analysis/immediate_cleanup.sh

# 6. Setup monitoring futuro
bash reports/integrated_analysis/setup_monitoring.sh

# 7. Validazione post-cleanup
bash reports/integrated_analysis/validation.sh
```

### **Audit per Regioni Specifiche**
```bash
# Singola regione
python main.py --regions us-east-1

# Regioni multiple
python main.py --regions us-east-1,eu-west-1,ap-southeast-1

# SG + Cost per regione specifica
python main.py --sg-cost-analysis --regions eu-west-1
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
├── data/                                  # Dati scaricati da AWS
│   ├── ec2_raw.json                      # Istanze EC2
│   ├── sg_raw.json                       # Security Groups
│   └── ...
├── reports/                               # Report generati
│   ├── security_audit_report.md          # Report principale
│   ├── security_findings.json            # Findings dettagliati
│   ├── integrated_analysis/              # 🆕 SG + Cost Analysis
│   │   ├── executive_summary.md          # 👔 Per management
│   │   ├── complete_sg_cost_report.json  # 📊 Dati completi
│   │   ├── detailed_analysis.csv         # 📈 Analisi dettagliata
│   │   ├── high_priority_actions.csv     # 🎯 Azioni prioritarie
│   │   └── *.sh                          # 🤖 Script automatici
│   ├── security_groups/                  # Analisi SG avanzata
│   │   ├── advanced_analysis.json
│   │   ├── consolidation_plan.json
│   │   └── advanced_cleanup.sh
│   └── cleanup/                           # Script di cleanup
│       ├── cleanup_plan.json
│       ├── 1_backup_everything.sh
│       ├── 2_critical_security_fixes.sh
│       ├── 3_cost_optimization.sh
│       ├── 4_maintenance_tasks.sh
│       └── 5_verify_cleanup.sh
└── config/                                # Configurazioni
    └── audit_config.yaml
```

## 🛡️ Funzionalità di Sicurezza

### **Security Groups Analysis**
- ✅ **Porte critiche esposte**: SSH (22), RDP (3389), MySQL (3306), PostgreSQL (5432)
- ✅ **Security Groups non utilizzati**: Identificazione SG senza risorse associate
- ✅ **Consolidamento intelligente**: Suggerimenti per unificare SG simili
- ✅ **Network topology analysis**: Mapping relazioni tra SG
- ✅ **🆕 Cost impact analysis**: Correlazione SG → Risorse → Costi reali

### **EC2 Security Assessment**
- ✅ **Istanze con IP pubblico**: Identificazione esposizioni non necessarie
- ✅ **Instance metadata service**: Controllo configurazioni IMDSv2
- ✅ **Storage encryption**: Verifica crittografia volumi EBS
- ✅ **🆕 Rightsizing opportunities**: Analisi utilizzo + Cost Explorer

### **Network Security**
- ✅ **Elastic IP non utilizzati**: Identificazione EIP non associati + costi
- ✅ **Load Balancer analysis**: Controllo configurazioni ALB/NLB + costi
- ✅ **VPC security assessment**: Analisi configurazioni di rete
- ✅ **🆕 Data transfer costs**: Analisi costi trasferimento dati

### **IAM Security Review**
- ✅ **Utenti senza attività**: Identificazione account inattivi
- ✅ **Policy analysis**: Controllo permessi eccessivi
- ✅ **Root account usage**: Monitoraggio utilizzo account root

## 💰 Ottimizzazione Costi Avanzata 🆕

### **Analisi Real-time Cost Explorer**
- 🔍 **Dati costi reali AWS**: Utilizzo API Cost Explorer per dati attuali
- 🔍 **Trend analysis**: Analisi variazioni costi mensili
- 🔍 **Anomaly detection**: Identificazione spike costi
- 🔍 **Cross-reference SG → Costs**: Correlazione SG con costi risorse associate

### **Risorse Non Utilizzate con Costi Reali**
- 🔍 **EBS Volumes non attaccati**: Con costi reali e stime risparmio
- 🔍 **Elastic IP non utilizzati**: $3.65/mese per EIP + costi reali
- 🔍 **Load Balancer sottoutilizzati**: $16-25/mese + analisi traffico
- 🔍 **Snapshot obsoleti**: Costi storage + lifecycle recommendations

### **EC2 Cost Optimization**
- 📊 **Instance rightsizing**: Raccomandazioni basate su Cost Explorer + CloudWatch
- 📊 **Reserved Instances opportunities**: Analisi pattern utilizzo
- 📊 **Spot Instances candidates**: Identificazione workload adatti

### **Network Cost Optimization**
- 💾 **Data transfer analysis**: Costi trasferimento inter-AZ/regione
- 💾 **NAT Gateway optimization**: Analisi utilizzo + VPC Endpoints alternatives
- 💾 **CloudFront opportunities**: CDN per ridurre data transfer costs

### **ROI e Business Case**
- 💼 **Executive Summary**: Report per management con ROI calculations
- 💼 **Implementation timeline**: Piano implementazione per fase
- 💼 **Risk assessment**: Analisi rischi per ogni ottimizzazione
- 💼 **Cost tracking**: Setup monitoring per tracking risparmi post-implementazione

## 🤖 Script di Remediation

Il tool genera automaticamente script bash organizzati per priorità:

### **🆕 Integrated Cleanup Scripts**
```bash
# Script integrati SG + Cost optimization
bash reports/integrated_analysis/immediate_cleanup.sh      # Quick wins sicuri
bash reports/integrated_analysis/setup_monitoring.sh       # Setup cost alerting
bash reports/integrated_analysis/validation.sh             # Post-cleanup verification
bash reports/integrated_analysis/calculate_savings.sh      # ROI calculation
```

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
- 💰 **🆕 Cost dashboard**: Integration con Cost Explorer data

Accesso: `http://localhost:8501` dopo `make prod-dashboard`

## ⚠️ Considerazioni di Sicurezza

### **Permessi AWS Richiesti**
Il tool richiede permessi di sola lettura per:
- EC2 (DescribeInstances, DescribeSecurityGroups, DescribeVolumes)
- S3 (ListBuckets, GetBucketLocation, GetBucketPolicy)
- IAM (ListUsers, ListRoles, ListPolicies)
- VPC (DescribeVpcs, DescribeSubnets, DescribeRouteTables)
- **🆕 Cost Explorer (GetCostAndUsage, GetUsageReport)** 
- **🆕 Billing (ViewBilling, ViewUsage)**

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
  
# 🆕 Cost Explorer Configuration
cost_analysis:
  enabled: true
  historical_months: 3
  anomaly_threshold_percent: 20
  currency: USD
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

# 🆕 Cost Analysis Configuration
COST_EXPLORER_ENABLED=true
COST_ANALYSIS_REGIONS=us-east-1,eu-west-1
COST_THRESHOLD_MONTHLY=10
```

## 🐛 Troubleshooting

### **Errori Comuni**

**1. Credenziali AWS non configurate**
```bash
make check-aws  # Verifica configurazione
aws configure   # Configura credenziali
```

**2. 🆕 Permessi Cost Explorer insufficienti**
```bash
# Test permessi Cost Explorer
aws ce get-cost-and-usage --time-period Start=2024-11-01,End=2024-12-01 --granularity MONTHLY --metrics BlendedCost

# Se fallisce, aggiungi policy: 
# - AWSBillingReadOnlyAccess
# - CE:GetCostAndUsage
```

**3. Permessi insufficienti**
```bash
# Verifica identity corrente
aws sts get-caller-identity

# Testa permessi specifici
aws ec2 describe-instances --dry-run
```

**4. Nessun dato trovato**
```bash
make list-data       # Controlla dati disponibili
make prod-fetch      # Riesegui download
```

**5. Dashboard non si avvia**
```bash
make status          # Controlla environment
make install         # Reinstalla dipendenze
```

**6. 🆕 SG + Cost Analysis da $0 savings**
```bash
# Possibili cause:
# - Account AWS nuovo/piccolo (normale)
# - Regione singola analizzata (prova multi-regione)
# - Permessi Cost Explorer limitati
# - Infrastruttura già ottimizzata (ottimo!)

# Test multi-regione
python main.py --sg-cost-analysis --regions us-east-1,eu-west-1,ap-southeast-1

# Verifica risorse manualmente
aws ec2 describe-addresses --query 'Addresses[?!AssociationId]'
aws ec2 describe-volumes --filters "Name=status,Values=available"
```

### **Debug Mode**
```bash
# Abilita logging dettagliato
export VERBOSE=true
python main.py --audit-only

# Test singolo servizio
python main.py --services ec2 --regions us-east-1

# 🆕 Debug SG + Cost Analysis
python main.py --sg-cost-analysis --regions us-east-1 --verbose
```

## 📝 Changelog

### **v2.1 (Current)**
- ✨ **🆕 Security Groups + Cost Explorer Integration**
- ✨ **🆕 Real-time Cost Analysis con API AWS**
- ✨ **🆕 Executive Summary per Management**
- ✨ **🆕 Automated Cleanup Scripts Generation**
- ✨ Advanced Security Groups Analysis
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
- [ ] Multi-account cost analysis
- [ ] Advanced cost anomaly detection with ML
- [ ] Slack/Teams notifications integration
- [ ] CI/CD pipeline cost optimization
- [ ] Reserved Instances optimization recommendations

### **v3.0 (Futuro)**
- [ ] Machine Learning per threat detection
- [ ] Multi-cloud support (Azure, GCP)
- [ ] Advanced remediation automation with approval workflows
- [ ] Enterprise SSO integration
- [ ] Cost allocation and chargeback features

---

⭐ **Se questo tool ti è utile, lascia una stella su GitHub!** ⭐

## 🔍 **Esempi di Output**

### **Security Groups Analysis Standard**
```
📊 22 Security Groups analyzed
🗑️ 8 safe to delete
🚨 2 critical security issues
⚠️ 5 high priority findings
```

### **🆕 SG + Cost Analysis Output**
```
============================================================
📊 SECURITY GROUPS + COST ANALYSIS COMPLETED!
============================================================
💰 Potential Monthly Savings: $127.45
📅 Potential Annual Savings: $1,529.40
🎯 Immediate Actions Available: 12
📋 Medium Term Actions: 8
📁 Detailed Reports: reports/integrated_analysis/

🚀 Next Steps:
1. Review: reports/integrated_analysis/executive_summary.md
2. Prioritize: reports/integrated_analysis/high_priority_actions.csv
3. Execute: reports/integrated_analysis/immediate_cleanup.sh
4. Monitor: reports/integrated_analysis/setup_monitoring.sh

💡 HIGH SAVINGS POTENTIAL: $127.45/month!
```
# 🔒 AWS Infrastructure Security Auditor v2.1

> **Enterprise-grade AWS security auditing tool with interactive dashboard, cost optimization analysis, and comprehensive infrastructure cleanup recommendations**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![AWS](https://img.shields.io/badge/AWS-Compatible-orange.svg)](https://aws.amazon.com/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 Overview

AWS Infrastructure Security Auditor è uno strumento completo per la valutazione della sicurezza e l'ottimizzazione dei costi dell'infrastruttura AWS. Fornisce analisi dettagliate, raccomandazioni actionable e dashboard interattive per mantenere l'infrastruttura AWS sicura, efficiente e conforme agli standard di settore.

### ✨ Funzionalità Chiave

- 🔍 **Audit Multi-Servizio**: EC2, VPC, S3, IAM, Security Groups, RDS, Lambda, e molti altri
- 🌍 **Supporto Multi-Regione**: Audit simultaneo su multiple regioni AWS
- ⚡ **Performance Asincrona**: Fetching parallelo ad alta velocità
- 📊 **Dashboard Interattiva**: Visualizzazione real-time con Streamlit
- 💰 **Analisi Costi Avanzata**: Identificazione potenziali risparmi e ottimizzazioni
- 🛡️ **Analisi Security Groups Avanzata**: Ottimizzazione e cleanup automatico
- 🧹 **Piano Cleanup Infrastruttura**: Script automatici per pulizia risorse
- 📋 **Report Dettagliati**: Formati JSON e Markdown con remediation steps
- 🎯 **Compliance Framework**: Mappatura CIS, SOC2, PCI-DSS, ISO27001
- 🔧 **Regole Estensibili**: Facile aggiunta di regole custom
- 💾 **Smart Caching**: Gestione efficiente dei dati
- 🤖 **Automazione**: Makefile completo per tutte le operazioni

### 🎯 Cosa Viene Auditato

| Servizio | Controlli Principali | Livelli Severity |
|----------|---------------------|------------------|
| **EC2** | IP pubblici, istanze stopped, monitoring, rightsizing | 🔴 🟠 🟡 🔵 |
| **Security Groups** | Porte aperte, gruppi inutilizzati, esposizioni critiche | 🔴 🟠 🟡 🔵 |
| **S3** | Bucket pubblici, encryption, bucket vecchi | 🔴 🟠 🟡
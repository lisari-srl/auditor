# main.py
#!/usr/bin/env python3
"""
AWS Infrastructure Security Auditor - Versione Ottimizzata
"""

import asyncio
import argparse
import sys
import os
import time
from typing import List, Optional
from pathlib import Path

# Aggiungi il path corrente per import
sys.path.append(str(Path(__file__).parent))

from config.settings import AWSConfig
from utils.async_fetcher import AsyncAWSFetcher
from utils.cache_manager import SmartCache
from audit.audit_engine import AuditEngine
from config.audit_rules import Severity

class AWSAuditor:
    """Classe principale per orchestrare l'audit AWS"""
    
    def __init__(self, config_file: Optional[str] = None):
        # Carica configurazione
        self.config = AWSConfig.from_file(config_file) if config_file else AWSConfig()
        
        # Inizializza componenti
        self.fetcher = AsyncAWSFetcher(self.config)
        self.cache = SmartCache(ttl=self.config.cache_ttl)
        self.audit_engines = {}
        
        # Inizializza audit engines per ogni regione
        for region in self.config.regions:
            self.audit_engines[region] = AuditEngine(region)
    
    async def run_full_audit(self, use_cache: bool = True) -> dict:
        """Esegue audit completo: fetch + analyze + report"""
        print("🚀 Avvio AWS Security Audit...")
        start_time = time.time()
        
        try:
            # 1. Fetch dei dati
            if use_cache:
                print("💾 Controllo cache...")
                # TODO: Implementare logica cache più sofisticata
            
            print("📡 Fetching risorse AWS...")
            fetch_start = time.time()
            await self.fetcher.fetch_all_resources()
            fetch_time = time.time() - fetch_start
            print(f"   ✅ Fetch completato in {fetch_time:.2f}s")
            
            # 2. Esegui audit di sicurezza
            print("🔍 Esecuzione audit di sicurezza...")
            audit_start = time.time()
            all_findings = []
            
            for region, engine in self.audit_engines.items():
                print(f"   🌍 Audit regione {region}...")
                findings = engine.run_all_audits()
                all_findings.extend(findings)
            
            audit_time = time.time() - audit_start
            print(f"   ✅ Audit completato in {audit_time:.2f}s")
            
            # 3. Genera summary
            summary = self._generate_global_summary(all_findings)
            total_time = time.time() - start_time
            
            print(f"\n🎯 AUDIT SUMMARY")
            print(f"   Total Time: {total_time:.2f}s")
            print(f"   Total Findings: {len(all_findings)}")
            print(f"   Critical: {summary['critical']} | High: {summary['high']} | Medium: {summary['medium']} | Low: {summary['low']}")
            
            # 4. Avvisi per findings critici
            critical_findings = [f for f in all_findings if f.severity == Severity.CRITICAL]
            if critical_findings:
                print(f"\n🚨 ATTENZIONE: {len(critical_findings)} FINDING CRITICI TROVATI!")
                for finding in critical_findings[:5]:  # Mostra solo i primi 5
                    print(f"   • {finding.resource_name}: {finding.rule_name}")
                if len(critical_findings) > 5:
                    print(f"   • ... e altri {len(critical_findings) - 5} findings critici")
            
            return {
                "success": True,
                "total_findings": len(all_findings),
                "summary": summary,
                "critical_findings": len(critical_findings),
                "execution_time": total_time,
                "regions_audited": list(self.audit_engines.keys())
            }
            
        except Exception as e:
            print(f"❌ Errore durante l'audit: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def _generate_global_summary(self, findings: List) -> dict:
        """Genera summary globale di tutti i findings"""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for finding in findings:
            summary[finding.severity.value] += 1
        
        return summary
    
    async def run_fetch_only(self) -> dict:
        """Esegue solo il fetch dei dati senza audit"""
        print("📡 Fetching dati AWS...")
        start_time = time.time()
        
        try:
            await self.fetcher.fetch_all_resources()
            execution_time = time.time() - start_time
            
            print(f"✅ Fetch completato in {execution_time:.2f}s")
            return {
                "success": True,
                "execution_time": execution_time,
                "regions": self.config.regions
            }
        except Exception as e:
            print(f"❌ Errore durante fetch: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def run_audit_only(self) -> dict:
        """Esegue solo l'audit sui dati esistenti"""
        print("🔍 Esecuzione audit sui dati esistenti...")
        start_time = time.time()
        
        try:
            all_findings = []
            
            for region, engine in self.audit_engines.items():
                findings = engine.run_all_audits()
                all_findings.extend(findings)
            
            summary = self._generate_global_summary(all_findings)
            execution_time = time.time() - start_time
            
            print(f"✅ Audit completato in {execution_time:.2f}s")
            print(f"   Total Findings: {len(all_findings)}")
            
            return {
                "success": True,
                "total_findings": len(all_findings),
                "summary": summary,
                "execution_time": execution_time
            }
        except Exception as e:
            print(f"❌ Errore durante audit: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def start_dashboard(self):
        """Avvia il dashboard Streamlit"""
        print("🚀 Avvio dashboard Streamlit...")
        import subprocess
        
        try:
            subprocess.run(["streamlit", "run", "dashboard/app.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Errore avvio dashboard: {e}")
        except FileNotFoundError:
            print("❌ Streamlit non trovato. Installare con: pip install streamlit")


def main():
    """Funzione principale con CLI"""
    parser = argparse.ArgumentParser(
        description="🔍 AWS Infrastructure Security Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
  python main.py                          # Audit completo
  python main.py --fetch-only             # Solo fetch dati
  python main.py --audit-only             # Solo audit su dati esistenti
  python main.py --dashboard              # Avvia dashboard
  python main.py --config custom.json    # Usa configurazione custom
  python main.py --regions us-east-1,eu-west-1  # Specifica regioni
        """
    )
    
    # Opzioni di esecuzione
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--fetch-only",
        action="store_true",
        help="Esegue solo il fetch dei dati AWS"
    )
    group.add_argument(
        "--audit-only", 
        action="store_true",
        help="Esegue solo l'audit sui dati esistenti"
    )
    group.add_argument(
        "--dashboard",
        action="store_true", 
        help="Avvia il dashboard Streamlit"
    )
    
    # Opzioni di configurazione
    parser.add_argument(
        "--config",
        type=str,
        help="File di configurazione JSON custom"
    )
    parser.add_argument(
        "--regions",
        type=str,
        help="Regioni AWS da auditare (comma-separated)"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disabilita uso della cache"
    )
    parser.add_argument(
        "--services",
        type=str,
        help="Servizi da auditare (comma-separated): ec2,s3,iam,vpc"
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "md", "both"],
        default="both",
        help="Formato output dei report"
    )
    
    args = parser.parse_args()
    
    # Crea auditor con configurazione
    auditor = AWSAuditor(args.config)
    
    # Override configurazione da CLI
    if args.regions:
        auditor.config.regions = args.regions.split(",")
    
    if args.services:
        # Disabilita tutti i servizi e abilita solo quelli specificati
        for service in auditor.config.services:
            auditor.config.services[service] = False
        for service in args.services.split(","):
            if service.strip() in auditor.config.services:
                auditor.config.services[service.strip()] = True
    
    # Esegui operazione richiesta
    if args.dashboard:
        auditor.start_dashboard()
    elif args.fetch_only:
        result = asyncio.run(auditor.run_fetch_only())
        sys.exit(0 if result["success"] else 1)
    elif args.audit_only:
        result = auditor.run_audit_only()
        sys.exit(0 if result["success"] else 1)
    else:
        # Audit completo (default)
        use_cache = not args.no_cache
        result = asyncio.run(auditor.run_full_audit(use_cache))
        
        # Exit code basato sui risultati
        if not result["success"]:
            sys.exit(1)
        elif result.get("critical_findings", 0) > 0:
            print("\n⚠️  Audit completato con finding critici (exit code 2)")
            sys.exit(2)
        else:
            print("\n✅ Audit completato con successo")
            sys.exit(0)


if __name__ == "__main__":
    main()
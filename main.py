# main.py
#!/usr/bin/env python3
"""
AWS Infrastructure Security Auditor - Versione Ottimizzata v2.1
"""

import asyncio
import argparse
import sys
import os
import time
import shutil
from typing import List, Optional
from pathlib import Path

# Aggiungi il path corrente per import
sys.path.append(str(Path(__file__).parent))

from config.settings import AWSConfig
from utils.async_fetcher import AsyncAWSFetcher
from utils.cache_manager import SmartCache
from utils.data_processor import DataProcessor
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
        self.processor = DataProcessor()
        self.audit_engines = {}
        
        # Inizializza audit engines per ogni regione
        for region in self.config.regions:
            self.audit_engines[region] = AuditEngine(region)
    
    def cleanup_old_data(self):
        """Pulisce dati vecchi e cache obsolete"""
        print("🧹 Pulizia dati obsoleti...")
        
        # Pulisci cache
        if hasattr(self.cache, 'clear_cache'):
            self.cache.clear_cache()
            print("   ✅ Cache pulita")
        
        # Pulisci directory temporanee
        temp_dirs = [".cache", "temp", "__pycache__"]
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    if temp_dir == "__pycache__":
                        for root, dirs, files in os.walk("."):
                            for dir_name in dirs:
                                if dir_name == "__pycache__":
                                    full_path = os.path.join(root, dir_name)
                                    shutil.rmtree(full_path, ignore_errors=True)
                    else:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    print(f"   ✅ Directory {temp_dir} pulita")
                except Exception as e:
                    print(f"   ⚠️  Impossibile pulire {temp_dir}: {e}")
        
        # Pulisci file temporanei
        temp_files = ["temp_network.html", "*.tmp", "*.log"]
        for pattern in temp_files:
            if "*" in pattern:
                import glob
                for file_path in glob.glob(pattern):
                    try:
                        os.remove(file_path)
                        print(f"   ✅ File {file_path} rimosso")
                    except Exception:
                        pass
            else:
                if os.path.exists(pattern):
                    try:
                        os.remove(pattern)
                        print(f"   ✅ File {pattern} rimosso")
                    except Exception:
                        pass
    
    def optimize_system(self):
        """Ottimizza il sistema prima dell'audit"""
        print("⚡ Ottimizzazione sistema...")
        
        # Crea directory se non esistono
        directories = ["data", "reports", "config", "utils", "audit", "dashboard", ".cache"]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        # Verifica configurazione AWS
        try:
            import boto3
            session = boto3.Session(profile_name=self.config.profile)
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            print(f"   ✅ AWS Identity: {identity.get('Arn', 'Unknown')}")
        except Exception as e:
            print(f"   ❌ AWS Configuration Error: {e}")
            print("   💡 Suggerimento: eseguire 'aws configure' per configurare le credenziali")
            return False
        
        # Verifica regioni
        if not self.config.regions:
            print("   ❌ Nessuna regione configurata")
            return False
        
        print(f"   ✅ Regioni configurate: {', '.join(self.config.regions)}")
        
        # Verifica servizi abilitati
        active_services = self.config.get_active_services()
        if not active_services:
            print("   ❌ Nessun servizio abilitato")
            return False
        
        print(f"   ✅ Servizi abilitati: {', '.join(active_services)}")
        
        return True
    
    async def run_full_audit(self, use_cache: bool = True, force_cleanup: bool = True) -> dict:
        """Esegue audit completo: cleanup + fetch + analyze + report"""
        print("🚀 Avvio AWS Security Audit Completo...")
        start_time = time.time()
        
        try:
            # 0. Pulizia e ottimizzazione
            if force_cleanup:
                self.cleanup_old_data()
            
            if not self.optimize_system():
                return {
                    "success": False,
                    "error": "System optimization failed",
                    "execution_time": time.time() - start_time
                }
            
            # 1. Fetch dei dati
            print("\n📡 FASE 1: Fetching risorse AWS...")
            fetch_start = time.time()
            await self.fetcher.fetch_all_resources()
            fetch_time = time.time() - fetch_start
            print(f"   ✅ Fetch completato in {fetch_time:.2f}s")
            
            # 2. Process dei dati
            print("\n📊 FASE 2: Processing dati...")
            process_start = time.time()
            if not self.processor.process_all_data():
                print("   ⚠️  Processing completato con errori")
            process_time = time.time() - process_start
            print(f"   ✅ Processing completato in {process_time:.2f}s")
            
            # 3. Esegui audit di sicurezza
            print("\n🔍 FASE 3: Audit di sicurezza...")
            audit_start = time.time()
            all_findings = []
            
            for region, engine in self.audit_engines.items():
                print(f"   🌍 Audit regione {region}...")
                try:
                    findings = engine.run_all_audits()
                    all_findings.extend(findings)
                except Exception as e:
                    print(f"   ❌ Errore audit {region}: {e}")
                    continue
            
            audit_time = time.time() - audit_start
            print(f"   ✅ Audit completato in {audit_time:.2f}s")
            
            # 4. Genera summary
            summary = self._generate_global_summary(all_findings)
            total_time = time.time() - start_time
            
            # 5. Report finale
            print(f"\n🎯 AUDIT SUMMARY")
            print("=" * 50)
            print(f"   ⏱️  Total Time: {total_time:.2f}s")
            print(f"   📊 Total Findings: {len(all_findings)}")
            print(f"   🔴 Critical: {summary['critical']}")
            print(f"   🟠 High: {summary['high']}")
            print(f"   🟡 Medium: {summary['medium']}")
            print(f"   🔵 Low: {summary['low']}")
            print("=" * 50)
            
            # 6. Avvisi per findings critici
            critical_findings = [f for f in all_findings if f.severity == Severity.CRITICAL]
            high_findings = [f for f in all_findings if f.severity == Severity.HIGH]
            
            if critical_findings or high_findings:
                print(f"\n🚨 FINDINGS PRIORITARI:")
                
                if critical_findings:
                    print(f"\n🔴 CRITICAL ({len(critical_findings)}):")
                    for i, finding in enumerate(critical_findings[:3], 1):
                        print(f"   {i}. {finding.resource_name}: {finding.rule_name}")
                    if len(critical_findings) > 3:
                        print(f"   ... e altri {len(critical_findings) - 3} critical findings")
                
                if high_findings:
                    print(f"\n🟠 HIGH ({len(high_findings)}):")
                    for i, finding in enumerate(high_findings[:2], 1):
                        print(f"   {i}. {finding.resource_name}: {finding.rule_name}")
                    if len(high_findings) > 2:
                        print(f"   ... e altri {len(high_findings) - 2} high findings")
                        
                print(f"\n📋 Per dettagli completi: controlla reports/security_audit_report.md")
            else:
                print(f"\n✅ Nessun finding critico o high priority trovato!")
            
            # 7. Suggerimenti prossimi passi
            print(f"\n💡 PROSSIMI PASSI:")
            print(f"   📊 Dashboard: python main.py --dashboard")
            print(f"   🔍 Re-audit: python main.py --audit-only")
            print(f"   📁 Reports: controlla la directory /reports")
            
            return {
                "success": True,
                "total_findings": len(all_findings),
                "summary": summary,
                "critical_findings": len(critical_findings),
                "high_findings": len(high_findings),
                "execution_time": total_time,
                "regions_audited": list(self.audit_engines.keys()),
                "phases": {
                    "fetch_time": fetch_time,
                    "process_time": process_time,
                    "audit_time": audit_time
                }
            }
            
        except KeyboardInterrupt:
            print("\n🛑 Audit interrotto dall'utente")
            return {
                "success": False,
                "error": "User interrupted",
                "execution_time": time.time() - start_time
            }
        except Exception as e:
            print(f"\n❌ Errore durante l'audit: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "traceback": traceback.format_exc()
            }
    
    def _generate_global_summary(self, findings: List) -> dict:
        """Genera summary globale di tutti i findings"""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for finding in findings:
            severity_key = finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity)
            if severity_key in summary:
                summary[severity_key] += 1
        
        return summary
    
    async def run_fetch_only(self, force_cleanup: bool = False) -> dict:
        """Esegue solo il fetch dei dati senza audit"""
        print("📡 Fetching dati AWS...")
        start_time = time.time()
        
        try:
            # Pulizia opzionale
            if force_cleanup:
                self.cleanup_old_data()
            
            # Verifica sistema
            if not self.optimize_system():
                return {
                    "success": False,
                    "error": "System check failed",
                    "execution_time": time.time() - start_time
                }
            
            # Fetch
            await self.fetcher.fetch_all_resources()
            
            # Process dei dati anche nel fetch-only
            print("📊 Processing dati...")
            self.processor.process_all_data()
            
            execution_time = time.time() - start_time
            
            print(f"✅ Fetch e processing completati in {execution_time:.2f}s")
            return {
                "success": True,
                "execution_time": execution_time,
                "regions": self.config.regions
            }
        except Exception as e:
            print(f"❌ Errore durante fetch: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def run_audit_only(self, force_cleanup: bool = False) -> dict:
        """Esegue solo l'audit sui dati esistenti"""
        print("🔍 Esecuzione audit sui dati esistenti...")
        start_time = time.time()
        
        try:
            # Pulizia opzionale
            if force_cleanup:
                self.cleanup_old_data()
            
            # Verifica che esistano dati da auditare
            data_dir = Path("data")
            if not data_dir.exists() or not any(data_dir.glob("*.json")):
                print("❌ Nessun dato trovato in /data. Eseguire prima 'python main.py --fetch-only'")
                return {
                    "success": False,
                    "error": "No data found",
                    "execution_time": time.time() - start_time
                }
            
            # Process dei dati se necessario
            print("📊 Verifica processing dati...")
            self.processor.process_all_data()
            
            all_findings = []
            
            for region, engine in self.audit_engines.items():
                print(f"   🌍 Audit regione {region}...")
                try:
                    findings = engine.run_all_audits()
                    all_findings.extend(findings)
                except Exception as e:
                    print(f"   ❌ Errore audit {region}: {e}")
                    continue
            
            summary = self._generate_global_summary(all_findings)
            execution_time = time.time() - start_time
            
            print(f"✅ Audit completato in {execution_time:.2f}s")
            print(f"   Total Findings: {len(all_findings)}")
            
            # Mostra findings critici
            critical_findings = [f for f in all_findings if f.severity == Severity.CRITICAL]
            if critical_findings:
                print(f"\n🚨 {len(critical_findings)} FINDING CRITICI:")
                for finding in critical_findings[:3]:
                    print(f"   • {finding.resource_name}: {finding.rule_name}")
            
            return {
                "success": True,
                "total_findings": len(all_findings),
                "summary": summary,
                "execution_time": execution_time
            }
        except Exception as e:
            print(f"❌ Errore durante audit: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def start_dashboard(self, host: str = "localhost"):
        """Avvia il dashboard Streamlit"""
        print("🚀 Avvio dashboard Streamlit...")
        
        # Verifica che streamlit sia installato
        try:
            import streamlit
        except ImportError:
            print("❌ Streamlit non trovato. Installare con: pip install streamlit")
            return
        
        # Verifica che esistano dati
        data_dir = Path("data")
        if not data_dir.exists() or not any(data_dir.glob("*.json")):
            print("⚠️  Nessun dato trovato. Il dashboard sarà vuoto.")
            print("   Suggerimento: eseguire prima 'python main.py --fetch-only'")
        
        import subprocess
        import socket
        
        def is_port_available(port, host="localhost"):
            """Verifica se una porta è disponibile"""
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((host, int(port)))
                    return True
                except:
                    return False
        
        # Trova una porta disponibile
        base_port = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
        port = base_port
        
        for i in range(10):  # Prova 10 porte consecutive
            if is_port_available(port, host):
                break
            port += 1
        else:
            print(f"❌ Nessuna porta disponibile da {base_port} a {base_port + 9}")
            return
        
        if port != base_port:
            print(f"⚠️  Porta {base_port} occupata, uso porta {port}")
        
        try:
            # Determina l'indirizzo di binding
            server_address = host if host != "localhost" else "localhost"
            
            print(f"🌐 Dashboard disponibile su: http://localhost:{port}")
            if host != "localhost":
                print(f"🌐 Accessibile anche da: http://{host}:{port}")
            
            # Comando streamlit ottimizzato
            cmd = [
                "streamlit", "run", "dashboard/app.py",
                "--server.port", str(port),
                "--server.address", server_address,
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ]
            
            # Se è localhost, non specificare --server.enableXsrfProtection
            if host == "localhost":
                cmd.extend(["--server.enableXsrfProtection", "false"])
            
            subprocess.run(cmd, check=True)
            
        except subprocess.CalledProcessError as e:
            error_msg = str(e)
            if "Port" in error_msg and "already in use" in error_msg:
                print(f"❌ Porta {port} ancora occupata. Prova manualmente:")
                print(f"   streamlit run dashboard/app.py --server.port {port + 1} --server.address localhost")
            else:
                print(f"❌ Errore avvio dashboard: {e}")
                print("\n🔧 Prova manualmente:")
                print(f"   streamlit run dashboard/app.py --server.port {port} --server.address localhost")
        except FileNotFoundError:
            print("❌ Comando streamlit non trovato nel PATH")
            print("   Installare con: pip install streamlit")
        except KeyboardInterrupt:
            print("\n🛑 Dashboard fermato dall'utente")


def main():
    """Funzione principale con CLI"""
    parser = argparse.ArgumentParser(
        description="🔍 AWS Infrastructure Security Auditor v2.1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
  python main.py                          # Audit completo con pulizia automatica
  python main.py --fetch-only             # Solo fetch dati (con pulizia)
  python main.py --audit-only             # Solo audit su dati esistenti
  python main.py --dashboard              # Avvia dashboard (localhost)
  python main.py --dashboard --host 0.0.0.0  # Dashboard accessibile da rete
  python main.py --config custom.json    # Usa configurazione custom
  python main.py --regions us-east-1,eu-west-1  # Specifica regioni
  python main.py --no-cleanup            # Disabilita pulizia automatica
  python main.py --quick                 # Audit veloce (no fetch, no cleanup)
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
    group.add_argument(
        "--quick",
        action="store_true",
        help="Audit veloce: solo audit sui dati esistenti senza pulizia"
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
        "--no-cleanup",
        action="store_true",
        help="Disabilita pulizia automatica"
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
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Output verboso"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host per il dashboard (default: localhost, usa 0.0.0.0 per accesso rete)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forza l'esecuzione anche in caso di warning"
    )
    
    args = parser.parse_args()
    
    # Setup logging se verbose
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    try:
        # Crea auditor con configurazione
        auditor = AWSAuditor(args.config)
        
        # Override configurazione da CLI
        if args.regions:
            auditor.config.regions = [r.strip() for r in args.regions.split(",")]
            print(f"🌍 Regioni specificate: {auditor.config.regions}")
        
        if args.services:
            # Disabilita tutti i servizi e abilita solo quelli specificati
            for service in auditor.config.services:
                auditor.config.services[service] = False
            for service in args.services.split(","):
                service = service.strip()
                if service in auditor.config.services:
                    auditor.config.services[service] = True
                    print(f"✅ Servizio abilitato: {service}")
                else:
                    print(f"⚠️  Servizio sconosciuto: {service}")
        
        # Determina se fare cleanup
        force_cleanup = not args.no_cleanup
        
        # Esegui operazione richiesta
        if args.dashboard:
            auditor.start_dashboard(host=args.host)
        elif args.fetch_only:
            result = asyncio.run(auditor.run_fetch_only(force_cleanup=force_cleanup))
            sys.exit(0 if result["success"] else 1)
        elif args.audit_only:
            result = auditor.run_audit_only(force_cleanup=force_cleanup)
            sys.exit(0 if result["success"] else 1)
        elif args.quick:
            # Audit veloce: no fetch, no cleanup
            result = auditor.run_audit_only(force_cleanup=False)
            sys.exit(0 if result["success"] else 1)
        else:
            # Audit completo (default)
            use_cache = not args.no_cache
            result = asyncio.run(auditor.run_full_audit(use_cache, force_cleanup))
            
            # Exit code basato sui risultati
            if not result["success"]:
                sys.exit(1)
            elif result.get("critical_findings", 0) > 0:
                print("\n⚠️  Audit completato con finding critici (exit code 2)")
                sys.exit(2)
            else:
                print("\n✅ Audit completato con successo")
                sys.exit(0)
                
    except KeyboardInterrupt:
        print("\n🛑 Operazione interrotta dall'utente")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Errore critico: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
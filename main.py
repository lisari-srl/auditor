#!/usr/bin/env python3
"""
AWS Infrastructure Security Auditor - Complete Version v2.1
Enhanced with cost analysis, security groups optimization, and infrastructure cleanup
"""

import asyncio
import argparse
import sys
import os
import time
import shutil
import json
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

# Add current path for imports
sys.path.append(str(Path(__file__).parent))

from config.settings import AWSConfig
from utils.async_fetcher import AsyncAWSFetcher
from utils.cache_manager import SmartCache
from utils.data_processor import DataProcessor
from audit.audit_engine import AuditEngine
from config.audit_rules import Severity

class AWSAuditor:
    """Classe principale per orchestrare l'audit AWS completo"""
    
    def __init__(self, config_file: Optional[str] = None):
        # Carica configurazione
        self.config = AWSConfig.from_file(config_file) if config_file else AWSConfig()
        
        # Inizializza componenti base
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
        temp_files = ["temp_network.html"]
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"   ✅ File {temp_file} rimosso")
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
    
    def _load_all_processed_data(self) -> dict:
        """Carica tutti i dati processati da tutte le fasi"""
        all_data = {}
        data_dir = Path("data")
        
        if not data_dir.exists():
            return {}
        
        # Carica tutti i file JSON dalla directory data
        for json_file in data_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    all_data[json_file.stem] = json.load(f)
            except Exception as e:
                print(f"   ⚠️  Errore caricamento {json_file.name}: {e}")
        
        return all_data

    def _generate_comprehensive_summary(self, standard_findings, cost_results, 
                                     sg_results, cleanup_results) -> Dict:
        """Genera summary comprensivo di tutti i risultati"""
        standard_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in standard_findings:
            severity = finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity)
            if severity in standard_summary:
                standard_summary[severity] += 1

        total_cost_optimizations = sum(len(r.get("optimizations", [])) for r in cost_results.values())
        total_sg_issues = sum(r.get("total_findings", 0) for r in sg_results.values())
        total_sg_critical = sum(r.get("critical_issues", 0) for r in sg_results.values())
        total_cleanup_items = sum(r.get("total_items", 0) for r in cleanup_results.values())

        return {
            "standard_critical": standard_summary["critical"],
            "standard_high": standard_summary["high"],
            "standard_medium": standard_summary["medium"],
            "standard_low": standard_summary["low"],
            "total_cost_optimizations": total_cost_optimizations,
            "total_sg_issues": total_sg_issues,
            "total_sg_critical": total_sg_critical,
            "total_cleanup_items": total_cleanup_items,
            "analysis_phases": 6,
            "regions_analyzed": len(self.config.regions)
        }

    async def run_full_audit(self, use_cache: bool = True, force_cleanup: bool = True) -> Dict:
        """Esegue audit completo"""
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
            
            # 1. Fetch dei dati (ESTESO)
            print("\n📡 FASE 1: Fetching risorse AWS complete...")
            fetch_start = time.time()
            
            # Usa Extended Fetcher se disponibile
            try:
                from utils.extended_aws_fetcher import ExtendedAWSFetcher
                extended_fetcher = ExtendedAWSFetcher(self.config)
                await extended_fetcher.fetch_all_extended_resources()
                print("   ✅ Extended fetch completato")
            except ImportError:
                print("   ⚠️  Extended fetcher non disponibile, uso fetch standard")
                await self.fetcher.fetch_all_resources()
            except Exception as e:
                print(f"   ⚠️  Errore extended fetch: {e}, uso fetch standard")
                await self.fetcher.fetch_all_resources()
            
            fetch_time = time.time() - fetch_start
            print(f"   ✅ Fetch completo in {fetch_time:.2f}s")
            
            # 2. Process dei dati
            print("\n📊 FASE 2: Processing dati...")
            process_start = time.time()
            if not self.processor.process_all_data():
                print("   ⚠️  Processing completato con errori")
            process_time = time.time() - process_start
            print(f"   ✅ Processing completato in {process_time:.2f}s")
            
            # Carica tutti i dati processati
            all_data = self._load_all_processed_data()
            
            # 3. Esegui audit di sicurezza standard
            print("\n🔍 FASE 3: Audit di sicurezza standard...")
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
            print(f"   ✅ Audit standard completato in {audit_time:.2f}s")
            
            # 4. Analisi costi avanzata (opzionale)
            print("\n💰 FASE 4: Analisi costi e ottimizzazioni...")
            cost_start = time.time()
            
            cost_results = {}
            total_monthly_savings = 0
            
            try:
                from utils.cost_analyzer import AdvancedCostAnalyzer
                
                for region in self.config.regions:
                    print(f"   💰 Analisi costi {region}...")
                    cost_analyzer = AdvancedCostAnalyzer(region)
                    region_cost_analysis = await cost_analyzer.analyze_complete_costs(all_data)
                    cost_results[region] = region_cost_analysis
                    total_monthly_savings += region_cost_analysis.get("potential_monthly_savings", 0)
                
                print(f"   ✅ Analisi costi completata")
                print(f"   💰 Potenziali risparmi: ${total_monthly_savings:.2f}/mese")
                
            except ImportError:
                print("   ⚠️  Cost analyzer non disponibile, skip")
            except Exception as e:
                print(f"   ⚠️  Errore analisi costi: {e}")
                total_monthly_savings = 0
            
            cost_time = time.time() - cost_start
            
            # 5. Ottimizzazione Security Groups (opzionale)
            print("\n🛡️  FASE 5: Ottimizzazione Security Groups...")
            sg_start = time.time()
            
            sg_results = {}
            total_critical_sg_issues = 0
            
            try:
                from utils.simple_sg_optimizer import analyze_security_groups_simple
                
                for region in self.config.regions:
                    print(f"   🛡️  Analisi SG {region}...")
                    region_sg_analysis = analyze_security_groups_simple(all_data, region)
                    sg_results[region] = region_sg_analysis
                    total_critical_sg_issues += region_sg_analysis.get("critical_issues", 0)
                
                print(f"   ✅ Ottimizzazione SG completata")
                
                if total_critical_sg_issues > 0:
                    print(f"   🚨 ATTENZIONE: {total_critical_sg_issues} problemi critici Security Groups!")
                
            except ImportError:
                print("   ⚠️  SG optimizer non disponibile, skip")
            except Exception as e:
                print(f"   ⚠️  Errore ottimizzazione SG: {e}")
                total_critical_sg_issues = 0
            
            sg_time = time.time() - sg_start
            
            # 6. Piano cleanup infrastruttura (opzionale)
            print("\n🧹 FASE 6: Piano cleanup infrastruttura...")
            cleanup_start = time.time()
            
            cleanup_results = {}
            total_annual_savings = 0
            
            try:
                from utils.simple_cleanup_orchestrator import create_infrastructure_cleanup_plan
                
                for region in self.config.regions:
                    print(f"   🧹 Piano cleanup {region}...")
                    region_cleanup = create_infrastructure_cleanup_plan(all_data, region)
                    cleanup_results[region] = region_cleanup
                    total_annual_savings += region_cleanup.get("estimated_annual_savings", 0)
                
                print(f"   ✅ Piano cleanup completato")
                print(f"   💰 Risparmi annuali stimati: ${total_annual_savings:.2f}")
                
            except ImportError:
                print("   ⚠️  Cleanup orchestrator non disponibile, skip")
            except Exception as e:
                print(f"   ⚠️  Errore piano cleanup: {e}")
                total_annual_savings = 0
            
            cleanup_time = time.time() - cleanup_start
            
            # 7. Genera summary globale
            summary = self._generate_comprehensive_summary(
                all_findings, cost_results, sg_results, cleanup_results
            )
            
            total_time = time.time() - start_time
            
            # 8. Report finale completo
            print(f"\n🎯 AUDIT COMPLETO - RISULTATI FINALI")
            print("=" * 60)
            print(f"   ⏱️  Tempo Totale: {total_time:.2f}s")
            print(f"   📊 Audit Standard: {len(all_findings)} findings")
            print(f"   🔴 Critical Standard: {summary['standard_critical']}")
            print(f"   🟠 High Standard: {summary['standard_high']}")
            print("")
            
            if total_monthly_savings > 0:
                print(f"   💰 Analisi Costi:")
                print(f"      - Risparmi mensili: ${total_monthly_savings:.2f}")
                print(f"      - Risparmi annuali: ${total_monthly_savings * 12:.2f}")
                print("")
            
            if total_critical_sg_issues > 0 or len(sg_results) > 0:
                print(f"   🛡️  Security Groups:")
                if total_critical_sg_issues > 0:
                    print(f"      - 🚨 CRITICAL: {total_critical_sg_issues} problemi di sicurezza!")
                else:
                    print(f"      - ✅ Nessun problema critico")
                print("")
            
            if total_annual_savings > 0:
                print(f"   🧹 Cleanup Infrastruttura:")
                print(f"      - Risparmi annuali: ${total_annual_savings:.2f}")
                print(f"      - Items da pulire: {summary.get('total_cleanup_items', 0)}")
                print("")
            
            print("=" * 60)
            
            # 9. Avvisi prioritari
            if total_critical_sg_issues > 0 or summary['standard_critical'] > 0:
                print(f"\n🚨 AZIONI IMMEDIATE RICHIESTE:")
                
                if total_critical_sg_issues > 0:
                    print(f"   🛡️  Security Groups: {total_critical_sg_issues} problemi critici")
                    print(f"      → Esegui: bash reports/security_groups/critical_fixes.sh")
                
                if summary['standard_critical'] > 0:
                    print(f"   🔍 Audit Standard: {summary['standard_critical']} finding critici")
                    print(f"      → Controlla: reports/security_audit_report.md")
                
                print(f"   💾 BACKUP PRIMA: bash reports/cleanup/1_backup_everything.sh")
            
            # 10. Suggerimenti prossimi passi
            print(f"\n💡 PROSSIMI PASSI CONSIGLIATI:")
            print(f"   1. 📊 Dashboard: python main.py --dashboard")
            
            if len(cleanup_results) > 0:
                print(f"   2. 💾 Backup: bash reports/cleanup/1_backup_everything.sh")
            
            if total_critical_sg_issues > 0:
                print(f"   3. 🚨 Fix SG critici: bash reports/security_groups/critical_fixes.sh")
            
            if total_annual_savings > 1000:
                print(f"   4. 💰 Cleanup costi: bash reports/cleanup/3_cost_optimization.sh")
            
            print(f"   5. 🔍 Report completi: directory /reports")
            
            # 11. Salva risultati estesi
            self._save_comprehensive_results({
                "standard_findings": all_findings,
                "cost_analysis": cost_results,
                "security_groups": sg_results,
                "cleanup_plan": cleanup_results,
                "summary": summary
            })
            
            return {
                "success": True,
                "total_findings": len(all_findings),
                "summary": summary,
                "execution_time": time.time() - start_time
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
    
    def _generate_global_summary(self, findings: List) -> dict:
        """Genera summary globale di tutti i findings"""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for finding in findings:
            severity_key = finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity)
            if severity_key in summary:
                summary[severity_key] += 1
        
        return summary


def main():
    """Funzione principale con CLI semplificata"""
    parser = argparse.ArgumentParser(
        description="🔍 AWS Infrastructure Security Auditor v2.1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
  python main.py                          # Audit completo 
  python main.py --fetch-only             # Solo fetch dati
  python main.py --audit-only             # Solo audit su dati esistenti
  python main.py --dashboard              # Avvia dashboard
  python main.py --quick                  # Audit veloce senza fetch
  python main.py --regions us-east-1      # Regione specifica
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
            result = asyncio.run(auditor.run_full_audit(use_cache=True, force_cleanup=force_cleanup))
            
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
        print("\n🛑 Audit interrotto dall'utente")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore durante l'audit: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
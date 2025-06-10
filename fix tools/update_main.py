#!/usr/bin/env python3
"""
Script per aggiornare main.py con la nuova funzionalità SG + Cost Analysis
Esegui: python update_main.py
"""

import os
import shutil
from datetime import datetime

def backup_main():
    """Crea backup del main.py originale"""
    if os.path.exists("main.py"):
        backup_name = f"main_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        shutil.copy2("main.py", backup_name)
        print(f"✅ Backup creato: {backup_name}")
        return backup_name
    else:
        print("❌ main.py non trovato!")
        return None

def read_main_file():
    """Legge il contenuto del main.py"""
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"❌ Errore lettura main.py: {e}")
        return None

def update_help_text(content):
    """Aggiorna il testo di help con il nuovo comando"""
    
    # Trova la sezione epilog
    epilog_start = content.find('epilog="""')
    if epilog_start == -1:
        print("⚠️ Sezione epilog non trovata")
        return content
    
    # Trova la fine dell'epilog
    epilog_end = content.find('"""', epilog_start + 10)
    if epilog_end == -1:
        print("⚠️ Fine epilog non trovata")
        return content
    
    # Estrai l'epilog esistente
    current_epilog = content[epilog_start:epilog_end + 3]
    
    # Nuovo epilog con comando aggiunto
    new_epilog = '''epilog="""
Esempi di utilizzo:
  python main.py                          # Audit completo 
  python main.py --fetch-only             # Solo fetch dati
  python main.py --audit-only             # Solo audit su dati esistenti
  python main.py --dashboard              # Avvia dashboard
  python main.py --quick                  # Audit veloce senza fetch
  python main.py --regions us-east-1      # Regione specifica
  python main.py --sg-cost-analysis       # 🆕 Analisi SG + Costi completa
        """'''
    
    # Sostituisci
    updated_content = content.replace(current_epilog, new_epilog)
    print("✅ Help text aggiornato")
    return updated_content

def add_argument_parser(content):
    """Aggiunge il nuovo argomento --sg-cost-analysis"""
    
    # Cerca il punto dove aggiungere l'argomento (dopo --quick)
    quick_arg_pattern = '''group.add_argument(
        "--quick",
        action="store_true",
        help="Audit veloce: solo audit sui dati esistenti senza pulizia"
    )'''
    
    if quick_arg_pattern not in content:
        print("⚠️ Pattern --quick non trovato, cerco alternativa...")
        # Alternativa: cerca qualsiasi mutually_exclusive_group
        quick_alt_pattern = 'help="Audit veloce: solo audit sui dati esistenti senza pulizia"'
        if quick_alt_pattern in content:
            # Trova la fine di questo blocco
            quick_pos = content.find(quick_alt_pattern)
            next_closing = content.find(')', quick_pos)
            
            if next_closing != -1:
                # Aggiungi dopo la parentesi chiusa
                new_arg = '''
    group.add_argument(
        "--sg-cost-analysis",
        action="store_true",
        help="🆕 Analisi completa Security Groups + Cost Explorer"
    )'''
                
                updated_content = content[:next_closing + 1] + new_arg + content[next_closing + 1:]
                print("✅ Argomento --sg-cost-analysis aggiunto")
                return updated_content
        
        print("❌ Non riesco a trovare dove aggiungere l'argomento")
        return content
    
    # Aggiunge il nuovo argomento dopo --quick
    new_arg = quick_arg_pattern + '''
    group.add_argument(
        "--sg-cost-analysis",
        action="store_true",
        help="🆕 Analisi completa Security Groups + Cost Explorer"
    )'''
    
    updated_content = content.replace(quick_arg_pattern, new_arg)
    print("✅ Argomento --sg-cost-analysis aggiunto")
    return updated_content

def add_sg_cost_logic(content):
    """Aggiunge la logica per gestire --sg-cost-analysis"""
    
    # Cerca il blocco elif args.quick
    quick_logic_pattern = '''elif args.quick:
            # Audit veloce: no fetch, no cleanup
            result = auditor.run_audit_only(force_cleanup=False)
            sys.exit(0 if result["success"] else 1)'''
    
    if quick_logic_pattern not in content:
        print("⚠️ Pattern elif args.quick non trovato, cerco alternativa...")
        # Alternativa più generica
        alt_pattern = 'result = auditor.run_audit_only(force_cleanup=False)'
        if alt_pattern in content:
            # Trova l'inizio del blocco elif args.quick
            quick_pos = content.find(alt_pattern)
            # Trova la fine del blocco (prossima riga che inizia con elif o else)
            lines = content[quick_pos:].split('\n')
            block_end_pos = quick_pos
            for i, line in enumerate(lines):
                if i > 0 and (line.strip().startswith('elif') or line.strip().startswith('else')):
                    block_end_pos = quick_pos + len('\n'.join(lines[:i]))
                    break
            
            # Aggiunge il nuovo blocco
            new_sg_logic = '''
        elif args.sg_cost_analysis:
            print("🚀 Starting comprehensive Security Groups + Cost Analysis...")
            
            # Import del nuovo tool
            try:
                from utils.complete_sg_cost_integration import run_complete_sg_cost_analysis
                
                # Determina regione
                target_region = auditor.config.regions[0] if auditor.config.regions else "us-east-1"
                print(f"🌍 Analyzing region: {target_region}")
                
                # Esegui analisi completa
                result = run_complete_sg_cost_analysis(target_region)
                
                # Output risultati
                print("\\n" + "="*60)
                print("📊 SECURITY GROUPS + COST ANALYSIS COMPLETED!")
                print("="*60)
                
                # Estrai metriche chiave
                recommendations = result.get('recommendations', {})
                monthly_savings = recommendations.get('estimated_total_monthly_savings', 0)
                immediate_actions = len(recommendations.get('immediate_actions', []))
                medium_actions = len(recommendations.get('medium_term_actions', []))
                
                # Summary results
                print(f"💰 Potential Monthly Savings: ${monthly_savings:.2f}")
                print(f"📅 Potential Annual Savings: ${monthly_savings * 12:.2f}")
                print(f"🎯 Immediate Actions Available: {immediate_actions}")
                print(f"📋 Medium Term Actions: {medium_actions}")
                print(f"📁 Detailed Reports: reports/integrated_analysis/")
                
                # Quick wins summary
                if immediate_actions > 0:
                    print(f"\\n🚀 Next Steps:")
                    print(f"1. Review: reports/integrated_analysis/executive_summary.md")
                    print(f"2. Prioritize: reports/integrated_analysis/high_priority_actions.csv")
                    print(f"3. Execute: reports/integrated_analysis/immediate_cleanup.sh")
                    print(f"4. Monitor: reports/integrated_analysis/setup_monitoring.sh")
                
                # Exit code based on findings
                if monthly_savings > 50:
                    print(f"\\n💡 HIGH SAVINGS POTENTIAL: ${monthly_savings:.2f}/month!")
                    sys.exit(0)
                elif monthly_savings > 10:
                    print(f"\\n✅ MODERATE SAVINGS FOUND: ${monthly_savings:.2f}/month")
                    sys.exit(0)
                else:
                    print(f"\\n✅ ANALYSIS COMPLETED: Limited savings opportunities")
                    sys.exit(0)
                    
            except ImportError as e:
                print(f"❌ SG Cost Analysis tool not available: {e}")
                print("💡 Make sure utils/complete_sg_cost_integration.py exists")
                sys.exit(1)
            except Exception as e:
                print(f"❌ Error during SG Cost Analysis: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)'''
            
            updated_content = content[:block_end_pos] + new_sg_logic + content[block_end_pos:]
            print("✅ Logica --sg-cost-analysis aggiunta")
            return updated_content
        
        print("❌ Non riesco a trovare dove aggiungere la logica")
        return content
    
    # Aggiunge dopo il blocco quick
    new_sg_logic = quick_logic_pattern + '''
        elif args.sg_cost_analysis:
            print("🚀 Starting comprehensive Security Groups + Cost Analysis...")
            
            # Import del nuovo tool
            try:
                from utils.complete_sg_cost_integration import run_complete_sg_cost_analysis
                
                # Determina regione
                target_region = auditor.config.regions[0] if auditor.config.regions else "us-east-1"
                print(f"🌍 Analyzing region: {target_region}")
                
                # Esegui analisi completa
                result = run_complete_sg_cost_analysis(target_region)
                
                # Output risultati
                print("\\n" + "="*60)
                print("📊 SECURITY GROUPS + COST ANALYSIS COMPLETED!")
                print("="*60)
                
                # Estrai metriche chiave
                recommendations = result.get('recommendations', {})
                monthly_savings = recommendations.get('estimated_total_monthly_savings', 0)
                immediate_actions = len(recommendations.get('immediate_actions', []))
                medium_actions = len(recommendations.get('medium_term_actions', []))
                
                # Summary results
                print(f"💰 Potential Monthly Savings: ${monthly_savings:.2f}")
                print(f"📅 Potential Annual Savings: ${monthly_savings * 12:.2f}")
                print(f"🎯 Immediate Actions Available: {immediate_actions}")
                print(f"📋 Medium Term Actions: {medium_actions}")
                print(f"📁 Detailed Reports: reports/integrated_analysis/")
                
                # Quick wins summary
                if immediate_actions > 0:
                    print(f"\\n🚀 Next Steps:")
                    print(f"1. Review: reports/integrated_analysis/executive_summary.md")
                    print(f"2. Prioritize: reports/integrated_analysis/high_priority_actions.csv")
                    print(f"3. Execute: reports/integrated_analysis/immediate_cleanup.sh")
                    print(f"4. Monitor: reports/integrated_analysis/setup_monitoring.sh")
                
                # Exit code based on findings
                if monthly_savings > 50:
                    print(f"\\n💡 HIGH SAVINGS POTENTIAL: ${monthly_savings:.2f}/month!")
                    sys.exit(0)
                elif monthly_savings > 10:
                    print(f"\\n✅ MODERATE SAVINGS FOUND: ${monthly_savings:.2f}/month")
                    sys.exit(0)
                else:
                    print(f"\\n✅ ANALYSIS COMPLETED: Limited savings opportunities")
                    sys.exit(0)
                    
            except ImportError as e:
                print(f"❌ SG Cost Analysis tool not available: {e}")
                print("💡 Make sure utils/complete_sg_cost_integration.py exists")
                sys.exit(1)
            except Exception as e:
                print(f"❌ Error during SG Cost Analysis: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)'''
    
    updated_content = content.replace(quick_logic_pattern, new_sg_logic)
    print("✅ Logica --sg-cost-analysis aggiunta")
    return updated_content

def write_updated_main(content):
    """Scrive il main.py aggiornato"""
    try:
        with open("main.py", "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ main.py aggiornato con successo")
        return True
    except Exception as e:
        print(f"❌ Errore scrittura main.py: {e}")
        return False

def verify_update():
    """Verifica che l'aggiornamento sia stato applicato correttamente"""
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        checks = [
            ("--sg-cost-analysis in help", "--sg-cost-analysis" in content),
            ("sg-cost-analysis argument", '"--sg-cost-analysis"' in content),
            ("elif args.sg_cost_analysis", "elif args.sg_cost_analysis:" in content),
            ("run_complete_sg_cost_analysis import", "run_complete_sg_cost_analysis" in content)
        ]
        
        print("\n🔍 Verifica aggiornamento:")
        all_good = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")
            if not check_result:
                all_good = False
        
        return all_good
    except Exception as e:
        print(f"❌ Errore verifica: {e}")
        return False

def main():
    """Funzione principale dello script di aggiornamento"""
    print("🚀 AWS Security Auditor - Script di Aggiornamento main.py")
    print("=" * 60)
    
    # 1. Backup
    backup_file = backup_main()
    if not backup_file:
        return
    
    # 2. Leggi contenuto
    content = read_main_file()
    if not content:
        return
    
    # 3. Controlla se già aggiornato
    if "--sg-cost-analysis" in content:
        print("⚠️ main.py sembra già aggiornato (contiene --sg-cost-analysis)")
        response = input("Vuoi procedere comunque? (y/N): ")
        if response.lower() != 'y':
            print("❌ Aggiornamento annullato")
            return
    
    # 4. Applica modifiche
    print("\n🔧 Applicazione modifiche...")
    
    # Aggiorna help text
    content = update_help_text(content)
    
    # Aggiunge argomento
    content = add_argument_parser(content)
    
    # Aggiunge logica
    content = add_sg_cost_logic(content)
    
    # 5. Scrivi file aggiornato
    if write_updated_main(content):
        # 6. Verifica
        if verify_update():
            print("\n✅ AGGIORNAMENTO COMPLETATO CON SUCCESSO!")
            print(f"📁 Backup salvato come: {backup_file}")
            print("\n🎯 Nuovo comando disponibile:")
            print("   python main.py --sg-cost-analysis")
            print("\n📋 Test suggerito:")
            print("   python main.py --help  # Verifica che il nuovo comando appaia")
        else:
            print("\n❌ Aggiornamento applicato ma verifica fallita")
            print("💡 Controlla manualmente il file main.py")
    else:
        print("\n❌ ERRORE durante l'aggiornamento")
        print(f"💡 Puoi ripristinare il backup: cp {backup_file} main.py")

if __name__ == "__main__":
    main()
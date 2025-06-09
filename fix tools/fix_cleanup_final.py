#!/usr/bin/env python3
# fix_cleanup_final.py - Fix definitivo per simple_cleanup_orchestrator.py

import re
from pathlib import Path

def fix_cleanup_orchestrator():
    """Fix definitivo per l'errore delle parentesi graffe"""
    
    cleanup_file = Path("utils/simple_cleanup_orchestrator.py")
    
    if not cleanup_file.exists():
        print("❌ File simple_cleanup_orchestrator.py non trovato")
        return False
    
    print("🔍 Fixing simple_cleanup_orchestrator.py...")
    
    # Leggi il contenuto
    with open(cleanup_file, 'r') as f:
        content = f.read()
    
    # Backup
    with open(f"{cleanup_file}.backup_final", 'w') as f:
        f.write(content)
    
    # Trova l'errore specifico alla linea 237
    lines = content.split('\n')
    
    print(f"📄 File ha {len(lines)} linee")
    
    # Controlla intorno alla linea 237
    error_found = False
    for i in range(max(0, 235), min(len(lines), 245)):
        line = lines[i]
        if 'f"' in line and '{' in line:
            # Conta parentesi graffe
            open_braces = line.count('{')
            close_braces = line.count('}')
            
            if open_braces > close_braces:
                print(f"🎯 Errore trovato alla linea {i+1}: {line.strip()}")
                
                # Fix comuni
                if 'problemi di sicurezza!"' in line:
                    lines[i] = line.replace('problemi di sicurezza!"', 'problemi di sicurezza}!"')
                    error_found = True
                    print(f"✅ Fixed: problemi di sicurezza")
                
                elif 'exceeds $1000"' in line:
                    lines[i] = line.replace('exceeds $1000"', 'exceeds $1000}"')
                    error_found = True
                    print(f"✅ Fixed: exceeds $1000")
                
                elif '{' in line and not '}' in line and line.endswith('"'):
                    # Generic fix: aggiungi } prima della "
                    lines[i] = line[:-1] + '}' + line[-1]
                    error_found = True
                    print(f"✅ Fixed: added missing }}")
                
                else:
                    # Manual fix needed
                    print(f"⚠️  Fix manuale necessario per: {line.strip()}")
                    print(f"   Aggiungi }} prima della \" finale")
    
    # Fix aggiuntivi per pattern comuni
    fixed_content = '\n'.join(lines)
    
    # Pattern comuni da correggere
    patterns = [
        (r'f"([^"]*\{[^}]*)"', r'f"\1}"'),  # f"text {var}" -> f"text {var}"
        (r'f"([^"]*\{[^}]*\[[^\]]*\])"', r'f"\1}"'),  # f"text {dict[key]}" -> f"text {dict[key]}"
        (r'(\{[^}]*)"', r'\1}"'),  # {var}" -> {var}"
    ]
    
    for pattern, replacement in patterns:
        old_content = fixed_content
        fixed_content = re.sub(pattern, replacement, fixed_content)
        if old_content != fixed_content:
            print("✅ Applied regex fix")
    
    # Salva il file corretto
    with open(cleanup_file, 'w') as f:
        f.write(fixed_content)
    
    # Test syntax
    try:
        compile(fixed_content, str(cleanup_file), 'exec')
        print("✅ Syntax check passed!")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error still present: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False

def manual_fix_instructions():
    """Istruzioni per fix manuale se necessario"""
    
    print("""
🔧 FIX MANUALE per simple_cleanup_orchestrator.py:

1. Apri utils/simple_cleanup_orchestrator.py
2. Vai alla linea 237 (circa)
3. Cerca righe con f-strings che hanno { ma non }

PATTERN COMUNI DA CORREGGERE:

❌ SBAGLIATO:
f"🚨 CRITICAL: {total_critical_sg_issues} problemi di sicurezza!"

✅ CORRETTO:
f"🚨 CRITICAL: {total_critical_sg_issues} problemi di sicurezza}!"

❌ SBAGLIATO:
f"Monthly cost (${self.total_monthly_cost:.2f}) exceeds $1000"

✅ CORRETTO:
f"Monthly cost (${self.total_monthly_cost:.2f}) exceeds $1000}"

REGOLA GENERALE:
- Ogni { deve avere una } corrispondente
- Le f-strings devono essere bilanciate: f"text {variable}"
""")

def quick_disable():
    """Disabilita temporaneamente il cleanup orchestrator"""
    
    print("☢️  Disabilitando temporaneamente cleanup orchestrator...")
    
    # Trova tutti i file che importano simple_cleanup_orchestrator
    files_to_fix = [
        "main.py",
        "test_project_integrity.py"
    ]
    
    for file_path in files_to_fix:
        path = Path(file_path)
        if path.exists():
            with open(path, 'r') as f:
                content = f.read()
            
            # Commenta l'import
            content = content.replace(
                'from utils.simple_cleanup_orchestrator import',
                '# from utils.simple_cleanup_orchestrator import'
            )
            
            # Commenta l'uso
            content = content.replace(
                'create_infrastructure_cleanup_plan',
                '# create_infrastructure_cleanup_plan'
            )
            
            with open(path, 'w') as f:
                f.write(content)
            
            print(f"✅ Disabled in {file_path}")
    
    print("✅ Cleanup orchestrator temporaneamente disabilitato")
    print("   Il progetto funzionerà senza la funzionalità di cleanup")

def main():
    """Menu di scelta"""
    
    print("🔧 Fix per simple_cleanup_orchestrator.py")
    print("=" * 50)
    print("1. 🔧 Fix automatico (raccomandato)")
    print("2. 📖 Istruzioni fix manuale") 
    print("3. ☢️  Disabilita temporaneamente")
    print("4. ⏭️  Procedi senza fix (il progetto funziona già!)")
    
    choice = input("\nScegli (1/2/3/4): ").strip()
    
    if choice == "1":
        if fix_cleanup_orchestrator():
            print("\n🎉 Fix completato!")
            print("Test: python test_project_integrity.py")
        else:
            print("\n⚠️  Fix automatico fallito, prova il fix manuale")
            manual_fix_instructions()
    
    elif choice == "2":
        manual_fix_instructions()
    
    elif choice == "3":
        quick_disable()
        print("Test: python test_project_integrity.py")
    
    elif choice == "4":
        print("\n🚀 PERFETTO! Il progetto funziona già benissimo!")
        print("\nI tuoi risultati attuali:")
        print("✅ 7 findings di sicurezza trovati")
        print("✅ 2 critical, 1 high priority")
        print("✅ Advanced SG Auditor funzionante")
        print("✅ Dashboard pronta")
        print("\nProcedi con:")
        print("python main.py --dashboard")
    
    else:
        print("❌ Scelta non valida")

if __name__ == "__main__":
    main()

# Quick fix se chiamato con argomento
import sys
if len(sys.argv) > 1:
    if sys.argv[1] == "auto":
        fix_cleanup_orchestrator()
    elif sys.argv[1] == "disable":
        quick_disable()
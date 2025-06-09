#!/usr/bin/env python3
# manual_protocol_fix.py - Fix manuale preciso

"""
Il problema è che l'errore 'protocol' persiste. 
Facciamo una diagnosi precisa e fix mirato.
"""

from pathlib import Path
import traceback

def diagnose_protocol_error():
    """Diagnosi precisa dell'errore protocol"""
    
    print("🔍 Diagnosi precisa dell'errore 'protocol'...")
    
    # Test import specifico
    try:
        from audit.advanced_sg_auditor import AdvancedSecurityGroupAuditor
        print("✅ Import successful")
        
        # Test inizializzazione
        auditor = AdvancedSecurityGroupAuditor("us-east-1")
        print("✅ Initialization successful")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("📍 Traceback completo:")
        traceback.print_exc()
        
        # Trova la linea specifica con l'errore
        tb = traceback.format_exc()
        lines = tb.split('\n')
        for i, line in enumerate(lines):
            if 'protocol' in line and 'not defined' in line:
                print(f"🎯 Errore trovato alla linea: {line}")
                if i > 0:
                    print(f"📄 Contesto: {lines[i-1]}")

def find_protocol_usage():
    """Trova tutti gli usi di 'protocol' nel file"""
    
    sg_file = Path("audit/advanced_sg_auditor.py")
    
    if not sg_file.exists():
        print("❌ File non trovato")
        return
    
    with open(sg_file, 'r') as f:
        lines = f.readlines()
    
    print("🔍 Tutte le occorrenze di 'protocol':")
    
    for i, line in enumerate(lines, 1):
        if 'protocol' in line.lower():
            print(f"Linea {i}: {line.strip()}")

def targeted_fix():
    """Fix mirato basato sull'errore specifico"""
    
    sg_file = Path("audit/advanced_sg_auditor.py")
    
    if not sg_file.exists():
        print("❌ File non trovato")
        return False
    
    with open(sg_file, 'r') as f:
        content = f.read()
    
    # Backup
    with open(f"{sg_file}.backup2", 'w') as f:
        f.write(content)
    
    print("🔧 Applicando fix mirati...")
    
    # Fix specifici basati sui pattern comuni
    fixes = [
        # Fix 1: protocol in remediation commands
        ('f"aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol {protocol}"',
         'f"aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol {rule.get(\'IpProtocol\', \'tcp\')}"'),
        
        # Fix 2: protocol in f-strings generici
        ('--protocol {protocol}',
         '--protocol {rule.get(\'IpProtocol\', \'tcp\')}'),
        
        # Fix 3: protocol standalone
        ('{protocol}',
         '{rule.get("IpProtocol", "tcp")}'),
        
        # Fix 4: remediation_cmd con protocol
        ('remediation_cmd += f" --protocol {protocol}"',
         'remediation_cmd += f" --protocol {rule.get(\'IpProtocol\', \'tcp\')}"'),
    ]
    
    for old, new in fixes:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ Fixed: {old[:50]}...")
    
    # Salva
    with open(sg_file, 'w') as f:
        f.write(content)
    
    return True

def nuclear_option():
    """Opzione nucleare: disabilita temporaneamente advanced auditor"""
    
    print("☢️  OPZIONE NUCLEARE: Disabilito temporaneamente advanced auditor")
    
    # Modifica audit_engine.py per disabilitare advanced auditor
    engine_file = Path("audit/audit_engine.py")
    
    if engine_file.exists():
        with open(engine_file, 'r') as f:
            content = f.read()
        
        # Backup
        with open(f"{engine_file}.backup", 'w') as f:
            f.write(content)
        
        # Commenta l'import dell'advanced auditor
        content = content.replace(
            'from audit.advanced_sg_auditor import AdvancedSecurityGroupAuditor',
            '# from audit.advanced_sg_auditor import AdvancedSecurityGroupAuditor  # DISABLED'
        )
        
        # Commenta l'inizializzazione
        content = content.replace(
            'self.auditors["advanced_security_groups"] = AdvancedSecurityGroupAuditor(self.region)',
            '# self.auditors["advanced_security_groups"] = AdvancedSecurityGroupAuditor(self.region)  # DISABLED'
        )
        
        with open(engine_file, 'w') as f:
            f.write(content)
        
        print("✅ Advanced auditor temporaneamente disabilitato")
        print("   Il progetto funzionerà solo con core auditors")
        return True
    
    return False

def main():
    """Menu di fix"""
    
    print("🔧 Fix per errore 'protocol' not defined")
    print("=" * 50)
    
    # Step 1: Diagnosi
    print("\n1️⃣ DIAGNOSI:")
    diagnose_protocol_error()
    
    print("\n" + "=" * 50)
    
    # Step 2: Trova tutti gli usi di protocol
    print("\n2️⃣ ANALISI:")
    find_protocol_usage()
    
    print("\n" + "=" * 50)
    
    # Step 3: Chiedi cosa fare
    print("\n3️⃣ SOLUZIONI DISPONIBILI:")
    print("1. Fix mirato (raccomandato)")
    print("2. Opzione nucleare (disabilita advanced auditor)")
    print("3. Continua senza fix (usa solo core auditors)")
    
    choice = input("\nScegli (1/2/3): ").strip()
    
    if choice == "1":
        print("\n🔧 Applicando fix mirato...")
        if targeted_fix():
            print("✅ Fix applicato!")
            print("Test: python test_project_integrity.py")
        else:
            print("❌ Fix fallito")
    
    elif choice == "2":
        print("\n☢️  Applicando opzione nucleare...")
        if nuclear_option():
            print("✅ Advanced auditor disabilitato!")
            print("Il progetto funzionerà con solo core auditors")
            print("Test: python test_project_integrity.py")
    
    elif choice == "3":
        print("\n✅ Il progetto funziona già con i core auditors!")
        print("Puoi procedere con:")
        print("python main.py --audit-only")
        print("python main.py --dashboard")
    
    else:
        print("❌ Scelta non valida")

if __name__ == "__main__":
    main()

# Quick fix diretto se chiamato con argomento
import sys
if len(sys.argv) > 1:
    if sys.argv[1] == "fix":
        targeted_fix()
        print("Test: python test_project_integrity.py")
    elif sys.argv[1] == "disable":
        nuclear_option() 
        print("Test: python test_project_integrity.py")
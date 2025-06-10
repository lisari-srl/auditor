#!/usr/bin/env python3
"""
Fix definitivo per il problema import os in sg_cost_analyzer.py
"""

def quick_fix():
    """Fix veloce e definitivo"""
    
    filename = "utils/sg_cost_analyzer.py"
    
    print(f"🔧 Fixing {filename}...")
    
    # Leggi il contenuto
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Errore lettura: {e}")
        return False
    
    # Verifica se import os è presente
    if "import os" in content:
        print("ℹ️ Import 'os' già presente nel file")
        # Ma potrebbe essere nel posto sbagliato, forziamo la correzione
    
    # Forza l'aggiunta all'inizio se non c'è
    lines = content.split('\n')
    
    # Trova la prima riga non vuota e non commento
    insert_position = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            insert_position = i
            break
    
    # Controlla se nelle prime 10 righe c'è già import os
    first_lines = '\n'.join(lines[:10])
    if "import os" not in first_lines:
        # Aggiungi import os all'inizio degli import
        lines.insert(insert_position, "import os")
        print("✅ Import 'os' aggiunto")
    else:
        print("✅ Import 'os' già presente nelle prime righe")
    
    # Assicurati che ci sia import os nelle prime righe comunque
    content_fixed = '\n'.join(lines)
    
    # Double check: se os.chmod è usato ma import os non è presente, forza l'aggiunta
    if "os.chmod" in content_fixed and "import os" not in content_fixed[:200]:
        content_fixed = "import os\n" + content_fixed
        print("✅ Forzato import 'os' all'inizio")
    
    # Scrivi il file
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content_fixed)
        print(f"✅ {filename} aggiornato")
        return True
    except Exception as e:
        print(f"❌ Errore scrittura: {e}")
        return False

def verify_fix():
    """Verifica che il fix sia applicato"""
    filename = "utils/sg_cost_analyzer.py"
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Controlla che import os sia presente
        if "import os" in content:
            print("✅ Import 'os' presente nel file")
            
            # Controlla che sia nelle prime righe
            first_lines = '\n'.join(content.split('\n')[:10])
            if "import os" in first_lines:
                print("✅ Import 'os' nelle prime righe")
                return True
            else:
                print("⚠️ Import 'os' presente ma non nelle prime righe")
                return False
        else:
            print("❌ Import 'os' NON presente")
            return False
            
    except Exception as e:
        print(f"❌ Errore verifica: {e}")
        return False

def main():
    """Fix principale"""
    print("🚀 Quick Fix - Import OS Definitivo")
    print("=" * 40)
    
    if quick_fix():
        if verify_fix():
            print("\n✅ FIX COMPLETATO CON SUCCESSO!")
            print("\n🧪 Riprova ora:")
            print("   python main.py --sg-cost-analysis")
        else:
            print("\n⚠️ Fix applicato ma verifica fallita")
            print("💡 Controlla manualmente utils/sg_cost_analyzer.py")
    else:
        print("\n❌ Fix fallito")

if __name__ == "__main__":
    main()
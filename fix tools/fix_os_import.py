#!/usr/bin/env python3
"""
Script per fixare il missing import 'os' nel sg_cost_analyzer.py
Esegui: python fix_os_import.py
"""

import os
import shutil
from datetime import datetime

def fix_os_import():
    """Fix del missing import os nel sg_cost_analyzer.py"""
    
    filename = "utils/sg_cost_analyzer.py"
    
    # Backup veloce
    backup_name = f"{filename}_backup_os_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if os.path.exists(filename):
        shutil.copy2(filename, backup_name)
        print(f"✅ Backup creato: {backup_name}")
    
    # Leggi il file
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Errore lettura {filename}: {e}")
        return False
    
    # Controlla se import os è già presente
    if "import os" in content:
        print("✅ Import 'os' già presente")
        return True
    
    # Trova la sezione import e aggiungi 'import os'
    lines = content.split('\n')
    import_section_end = 0
    
    # Trova l'ultima riga di import
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            import_section_end = i
    
    # Inserisci 'import os' dopo l'ultima import
    if import_section_end > 0:
        lines.insert(import_section_end + 1, 'import os')
        print("✅ Import 'os' aggiunto dopo gli altri import")
    else:
        # Se non trova import, aggiunge all'inizio
        lines.insert(0, 'import os')
        print("✅ Import 'os' aggiunto all'inizio del file")
    
    # Ricostruisci il contenuto
    updated_content = '\n'.join(lines)
    
    # Scrivi il file
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"✅ {filename} aggiornato con successo")
        return True
    except Exception as e:
        print(f"❌ Errore scrittura {filename}: {e}")
        return False

def main():
    """Funzione principale del fix"""
    print("🔧 Fix Missing OS Import - sg_cost_analyzer.py")
    print("=" * 50)
    
    if fix_os_import():
        print("\n✅ FIX APPLICATO CON SUCCESSO!")
        print("\n🧪 Test suggerito:")
        print("   python main.py --sg-cost-analysis")
        print("\n💡 Dovrebbe ora completare l'analisi senza errori!")
    else:
        print("\n❌ FIX FALLITO")
        print("💡 Puoi ripristinare il backup se necessario")

if __name__ == "__main__":
    main()
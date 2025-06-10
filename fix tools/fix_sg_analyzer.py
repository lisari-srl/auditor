#!/usr/bin/env python3
"""
Script per fixare il problema datetime nel sg_cost_analyzer.py
Esegui: python fix_sg_analyzer.py
"""

import os
import shutil
from datetime import datetime

def backup_file(filename):
    """Crea backup del file"""
    if os.path.exists(filename):
        backup_name = f"{filename}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filename, backup_name)
        print(f"✅ Backup creato: {backup_name}")
        return backup_name
    else:
        print(f"❌ {filename} non trovato!")
        return None

def fix_datetime_issue():
    """Fix del problema datetime nel sg_cost_analyzer.py"""
    
    filename = "utils/sg_cost_analyzer.py"
    
    # Backup
    backup_file(filename)
    
    # Leggi il file
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Errore lettura {filename}: {e}")
        return False
    
    # Fix 1: Aggiungere import timezone se non presente
    if "from datetime import datetime, timezone" not in content:
        if "from datetime import datetime" in content:
            content = content.replace(
                "from datetime import datetime", 
                "from datetime import datetime, timezone"
            )
            print("✅ Import timezone aggiunto")
    
    # Fix 2: Sostituire la funzione problematica _calculate_usage_score
    old_function = '''def _calculate_usage_score(self, sg: Dict, usage: Dict) -> float:
        """Calcola score di utilizzo (0-100)"""
        score = 0
        
        # Attachment attuali (40 punti max)
        total_attachments = usage.get('total_attachments', 0)
        if total_attachments > 0:
            score += min(40, total_attachments * 10)
        
        # Diversità di risorse (30 punti max)
        resource_types = len(usage.get('resource_types', []))
        score += min(30, resource_types * 10)
        
        # Attività recente (20 punti max)
        creation_dates = usage.get('creation_dates', [])
        if creation_dates:
            # Se ha risorse create negli ultimi 30 giorni
            recent_cutoff = datetime.now() - timedelta(days=30)
            recent_resources = sum(1 for date in creation_dates 
                                 if isinstance(date, datetime) and date > recent_cutoff)
            if recent_resources > 0:
                score += 20
        
        # Complessità regole (10 punti max)
        rules_count = len(sg.get('IpPermissions', [])) + len(sg.get('IpPermissionsEgress', []))
        if rules_count > 2:  # Più del default
            score += min(10, rules_count * 2)
        
        return min(100, score)'''

    new_function = '''def _calculate_usage_score(self, sg: Dict, usage: Dict) -> float:
        """Calcola score di utilizzo (0-100)"""
        score = 0
        
        # Attachment attuali (40 punti max)
        total_attachments = usage.get('total_attachments', 0)
        if total_attachments > 0:
            score += min(40, total_attachments * 10)
        
        # Diversità di risorse (30 punti max)
        resource_types = len(usage.get('resource_types', []))
        score += min(30, resource_types * 10)
        
        # Attività recente (20 punti max)
        creation_dates = usage.get('creation_dates', [])
        if creation_dates:
            # Se ha risorse create negli ultimi 30 giorni
            recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            recent_resources = 0
            
            for date in creation_dates:
                if isinstance(date, datetime):
                    try:
                        # Normalizza la data per il confronto
                        if date.tzinfo is None:
                            # Se la data non ha timezone, assume UTC
                            date_aware = date.replace(tzinfo=timezone.utc)
                        else:
                            # Se ha timezone, usala così com'è
                            date_aware = date
                        
                        if date_aware > recent_cutoff:
                            recent_resources += 1
                    except Exception:
                        # Se c'è qualche problema con la data, ignora
                        continue
            
            if recent_resources > 0:
                score += 20
        
        # Complessità regole (10 punti max)
        rules_count = len(sg.get('IpPermissions', [])) + len(sg.get('IpPermissionsEgress', []))
        if rules_count > 2:  # Più del default
            score += min(10, rules_count * 2)
        
        return min(100, score)'''

    # Sostituisci la funzione
    if old_function in content:
        content = content.replace(old_function, new_function)
        print("✅ Funzione _calculate_usage_score aggiornata")
    else:
        print("⚠️ Funzione _calculate_usage_score non trovata nella forma attesa")
        # Prova una sostituzione più specifica del pezzo problematico
        old_snippet = '''recent_cutoff = datetime.now() - timedelta(days=30)
            recent_resources = sum(1 for date in creation_dates 
                                 if isinstance(date, datetime) and date > recent_cutoff)'''
        
        new_snippet = '''recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            recent_resources = 0
            
            for date in creation_dates:
                if isinstance(date, datetime):
                    try:
                        # Normalizza la data per il confronto
                        if date.tzinfo is None:
                            # Se la data non ha timezone, assume UTC
                            date_aware = date.replace(tzinfo=timezone.utc)
                        else:
                            # Se ha timezone, usala così com'è
                            date_aware = date
                        
                        if date_aware > recent_cutoff:
                            recent_resources += 1
                    except Exception:
                        # Se c'è qualche problema con la data, ignora
                        continue'''
        
        if old_snippet in content:
            content = content.replace(old_snippet, new_snippet)
            print("✅ Snippet datetime problematico corretto")
        else:
            print("❌ Snippet problematico non trovato")
            return False
    
    # Aggiungi import timedelta se non presente
    if "from datetime import datetime, timezone" in content and "timedelta" not in content.split("from datetime import")[1].split("\n")[0]:
        content = content.replace(
            "from datetime import datetime, timezone",
            "from datetime import datetime, timezone, timedelta"
        )
        print("✅ Import timedelta aggiunto")
    
    # Scrivi il file corretto
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ {filename} aggiornato con successo")
        return True
    except Exception as e:
        print(f"❌ Errore scrittura {filename}: {e}")
        return False

def main():
    """Funzione principale del fix"""
    print("🔧 Fix DateTime Issue - sg_cost_analyzer.py")
    print("=" * 50)
    
    if fix_datetime_issue():
        print("\n✅ FIX APPLICATO CON SUCCESSO!")
        print("\n🧪 Test suggerito:")
        print("   python main.py --sg-cost-analysis")
    else:
        print("\n❌ FIX FALLITO")
        print("💡 Puoi ripristinare il backup se necessario")

if __name__ == "__main__":
    main()
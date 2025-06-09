#!/usr/bin/env python3
from pathlib import Path
import re

sg_file = Path("audit/advanced_sg_auditor.py")

if sg_file.exists():
    with open(sg_file, 'r') as f:
        content = f.read()
    
    # Backup
    with open(f"{sg_file}.backup", 'w') as f:
        f.write(content)
    
    # Fix: aggiungi protocol definition nelle funzioni che ne hanno bisogno
    functions_to_fix = [
        '_handle_open_ingress',
        '_handle_broad_cidr',
        '_analyze_egress_rule'
    ]
    
    for func_name in functions_to_fix:
        # Cerca pattern: def function(...): """docstring"""
        pattern = f'(def {func_name}\\([^)]+\\):\\s*"""[^"]*""")'
        
        def replacement(match):
            return match.group(1) + '\n        protocol = rule.get("IpProtocol", "tcp")'
        
        content = re.sub(pattern, replacement, content)
    
    # Salva il fix
    with open(sg_file, 'w') as f:
        f.write(content)
    
    print("✅ Fixed protocol error!")

print("Run: python test_project_integrity.py")
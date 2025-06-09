#!/usr/bin/env python3
from pathlib import Path

# Fix 1: Cleanup Orchestrator f-string issue
cleanup_file = Path("utils/simple_cleanup_orchestrator.py")
if cleanup_file.exists():
    with open(cleanup_file, 'r') as f:
        content = f.read()
    
    # Find and fix unclosed braces in f-strings
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'f"' in line and '{' in line and line.count('{') > line.count('}'):
            print(f"Line {i}: {line.strip()}")
    
    # Common fix: add missing } before closing quote
    content = content.replace('problemi di sicurezza!"', 'problemi di sicurezza}!"')
    content = content.replace('exceeds $1000"', 'exceeds $1000}"')
    
    with open(cleanup_file, 'w') as f:
        f.write(content)
    print("✅ Fixed cleanup orchestrator")

# Fix 2: Advanced SG Auditor severity comparison  
sg_file = Path("audit/advanced_sg_auditor.py")
if sg_file.exists():
    with open(sg_file, 'r') as f:
        content = f.read()
    
    # Replace max() comparison with index-based comparison
    old = "severity = max(severity, port_info[\"severity\"])"
    new = """# Fixed severity comparison
                severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
                try:
                    if severity_order.index(port_info["severity"]) > severity_order.index(severity):
                        severity = port_info["severity"]
                except ValueError:
                    severity = port_info["severity"]"""
    
    content = content.replace(old, new)
    
    with open(sg_file, 'w') as f:
        f.write(content)
    print("✅ Fixed advanced SG auditor")

print("🎉 Quick fixes applied! Run: python test_project_integrity.py")
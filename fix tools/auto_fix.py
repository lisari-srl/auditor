#!/usr/bin/env python3
# auto_fix.py - Script di riparazione automatica

import os
import shutil
import stat
from pathlib import Path

def fix_directory_structure():
    """Crea le directory mancanti"""
    print("🔧 Fixing directory structure...")
    
    required_dirs = [
        "config", "audit", "utils", "dashboard", 
        "data", "reports", "reports/security_groups",
        "reports/cleanup", ".cache"
    ]
    
    for directory in required_dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created/verified: {directory}")

def fix_permissions():
    """Corregge i permessi dei file"""
    print("🔧 Fixing file permissions...")
    
    executable_files = [
        "setup.sh", "main.py"
    ]
    
    for file_path in executable_files:
        if Path(file_path).exists():
            # Make file executable
            current_stat = os.stat(file_path)
            os.chmod(file_path, current_stat.st_mode | stat.S_IEXEC)
            print(f"   ✅ Made executable: {file_path}")

def create_missing_init_files():
    """Crea file __init__.py mancanti"""
    print("🔧 Creating __init__.py files...")
    
    packages = ["config", "audit", "utils", "dashboard"]
    
    for package in packages:
        init_file = Path(package) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"   ✅ Created: {init_file}")

def fix_import_paths():
    """Corregge eventuali problemi di import path"""
    print("🔧 Fixing import paths...")
    
    # Aggiungi il progetto al PYTHONPATH se necessario
    current_dir = Path.cwd()
    
    # Crea un file .pth per il progetto se non esiste
    try:
        import site
        site_packages = site.getusersitepackages()
        if site_packages:
            Path(site_packages).mkdir(parents=True, exist_ok=True)
            pth_file = Path(site_packages) / "aws_auditor.pth"
            if not pth_file.exists():
                with open(pth_file, 'w') as f:
                    f.write(str(current_dir))
                print(f"   ✅ Created path file: {pth_file}")
            else:
                print(f"   ℹ️  Path file already exists: {pth_file}")
        else:
            print("   ⚠️  Could not determine user site-packages")
    except Exception as e:
        print(f"   ⚠️  Could not create .pth file: {e}")

def fix_makefile_permissions():
    """Corregge permessi degli script nel Makefile"""
    print("🔧 Fixing Makefile script permissions...")
    
    # Scripts che potrebbero essere generati dal sistema
    script_patterns = [
        "reports/cleanup/*.sh",
        "reports/security_groups/*.sh"
    ]
    
    for pattern in script_patterns:
        for script_file in Path().glob(pattern):
            if script_file.exists():
                current_stat = os.stat(script_file)
                os.chmod(script_file, current_stat.st_mode | stat.S_IEXEC)
                print(f"   ✅ Made executable: {script_file}")

def verify_python_environment():
    """Verifica ambiente Python"""
    print("🔧 Verifying Python environment...")
    
    import sys
    python_version = sys.version_info
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"   ❌ Python {python_version.major}.{python_version.minor} detected. Python 3.8+ required.")
        return False
    else:
        print(f"   ✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} OK")
    
    # Check required packages
    required_packages = [
        "boto3", "aioboto3", "streamlit", "plotly", "pandas"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package} available")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package} missing")
    
    if missing_packages:
        print(f"   💡 Install missing packages: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def fix_aws_config_template():
    """Crea template configurazione AWS se non esiste"""
    print("🔧 Creating AWS config template...")
    
    config_file = Path("config.json")
    env_file = Path(".env")
    
    if not config_file.exists():
        config_template = {
            "regions": ["us-east-1"],
            "profile": None,
            "max_workers": 10,
            "cache_ttl": 3600,
            "services": {
                "ec2": True,
                "eni": True,
                "sg": True,
                "vpc": True,
                "subnet": True,
                "igw": True,
                "route_table": True,
                "s3": True,
                "iam": True
            }
        }
        
        import json
        with open(config_file, 'w') as f:
            json.dump(config_template, f, indent=2)
        print(f"   ✅ Created: {config_file}")
    
    if not env_file.exists():
        env_template = """# AWS Configuration
# AWS_PROFILE=default
# AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key

# Audit Configuration
# AWS_AUDIT_REGIONS=us-east-1,eu-west-1
# AWS_AUDIT_MAX_WORKERS=10
"""
        with open(env_file, 'w') as f:
            f.write(env_template)
        print(f"   ✅ Created: {env_file}")

def clean_python_cache():
    """Pulisce cache Python"""
    print("🔧 Cleaning Python cache...")
    
    cache_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo"
    ]
    
    cleaned = 0
    for pattern in cache_patterns:
        for cache_file in Path().glob(pattern):
            try:
                if cache_file.is_dir():
                    shutil.rmtree(cache_file)
                else:
                    cache_file.unlink()
                cleaned += 1
            except Exception as e:
                print(f"   ⚠️  Could not remove {cache_file}: {e}")
    
    if cleaned > 0:
        print(f"   ✅ Cleaned {cleaned} cache files/directories")
    else:
        print("   ℹ️  No cache files to clean")

def fix_dashboard_imports():
    """Fix imports nella dashboard"""
    print("🔧 Fixing dashboard imports...")
    
    dashboard_file = Path("dashboard/app.py")
    if dashboard_file.exists():
        # Read the file
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        # Check for potential import issues
        fixes_needed = []
        
        # Check if streamlit import is at the top
        if "import streamlit as st" not in content[:200]:
            fixes_needed.append("streamlit import not at top")
        
        # Check for sys.path.append
        if "sys.path.append" not in content and "from config" in content:
            fixes_needed.append("missing sys.path.append")
        
        if fixes_needed:
            print(f"   ⚠️  Dashboard may need manual fixes: {fixes_needed}")
            print("   💡 Consider updating dashboard/app.py imports")
        else:
            print("   ✅ Dashboard imports look OK")

def create_test_files():
    """Crea file di test se mancanti"""
    print("🔧 Creating test files...")
    
    # Create simple test data if data directory is empty
    data_dir = Path("data")
    if data_dir.exists() and not any(data_dir.glob("*.json")):
        print("   ℹ️  Data directory empty - will be populated by test script")
    
    # Create empty reports directory structure
    reports_dirs = ["reports", "reports/security_groups", "reports/cleanup"]
    for dir_path in reports_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("   ✅ Test file structure ready")

def main():
    """Esegue tutte le riparazioni"""
    print("🔧 AWS Security Auditor - Auto Fix Tool\n")
    
    fixes = [
        ("Directory Structure", fix_directory_structure),
        ("File Permissions", fix_permissions),
        ("Python Packages", create_missing_init_files),
        ("Import Paths", fix_import_paths),
        ("Script Permissions", fix_makefile_permissions),
        ("Python Environment", verify_python_environment),
        ("AWS Config Template", fix_aws_config_template),
        ("Python Cache", clean_python_cache),
        ("Dashboard Imports", fix_dashboard_imports),
        ("Test Files", create_test_files)
    ]
    
    passed = 0
    total = len(fixes)
    
    for fix_name, fix_func in fixes:
        print(f"\n{'='*40}")
        print(f"Fix: {fix_name}")
        print(f"{'='*40}")
        
        try:
            result = fix_func()
            if result is False:
                print(f"⚠️  {fix_name}: NEEDS ATTENTION")
            else:
                print(f"✅ {fix_name}: COMPLETED")
                passed += 1
        except Exception as e:
            print(f"❌ {fix_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*40}")
    print(f"RESULTS: {passed}/{total} fixes completed successfully")
    print(f"{'='*40}")
    
    if passed >= total - 1:
        print("🎉 Auto-fix completed successfully!")
        print("\nNext steps:")
        print("1. Run: python test_project_integrity.py")
        print("2. If tests pass: python main.py --help")
        print("3. Configure AWS: aws configure")
    else:
        print("⚠️  Some fixes failed or need attention.")
        print("\nManual steps needed:")
        print("1. Check Python version (3.8+ required)")
        print("2. Install requirements: pip install -r requirements.txt")
        print("3. Configure AWS credentials")
    
    return 0 if passed >= total - 1 else 1

if __name__ == "__main__":
    exit(main())
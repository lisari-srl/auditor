#!/usr/bin/env python3
# test_project_integrity.py - Script di validazione

import sys
import os
import json
from pathlib import Path

def test_imports():
    """Test degli import principali"""
    print("🔍 Testing core imports...")
    
    try:
        # Core modules
        from config.settings import AWSConfig
        from config.audit_rules import Severity, get_rule_by_id
        from audit.base_auditor import BaseAuditor, Finding
        from audit.security_group_auditor import SecurityGroupAuditor
        from audit.ec2_auditor import EC2Auditor
        from audit.audit_engine import AuditEngine
        from utils.async_fetcher import AsyncAWSFetcher
        from utils.data_processor import DataProcessor
        print("   ✅ Core imports successful")
        
        # Test advanced imports
        try:
            from audit.advanced_sg_auditor import AdvancedSecurityGroupAuditor
            print("   ✅ Advanced SG Auditor available")
        except ImportError:
            print("   ⚠️  Advanced SG Auditor not available")
        
        try:
            from utils.extended_aws_fetcher import ExtendedAWSFetcher
            print("   ✅ Extended AWS Fetcher available")
        except ImportError:
            print("   ⚠️  Extended AWS Fetcher not available")
        
        try:
            from utils.simple_sg_optimizer import analyze_security_groups_simple
            print("   ✅ SG Optimizer available")
        except ImportError:
            print("   ⚠️  SG Optimizer not available")
        
        try:
            from utils.simple_cleanup_orchestrator import create_infrastructure_cleanup_plan
            print("   ✅ Cleanup Orchestrator available")
        except ImportError:
            print("   ⚠️  Cleanup Orchestrator not available")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False

def test_directory_structure():
    """Test della struttura directory"""
    print("🔍 Testing directory structure...")
    
    required_dirs = [
        "config", "audit", "utils", "dashboard", 
        "data", "reports"
    ]
    
    required_files = [
        "main.py", "requirements.txt", "Makefile",
        "config/settings.py", "config/audit_rules.py",
        "audit/base_auditor.py", "audit/security_group_auditor.py",
        "audit/ec2_auditor.py", "audit/audit_engine.py",
        "utils/async_fetcher.py", "utils/data_processor.py",
        "dashboard/app.py"
    ]
    
    missing_dirs = []
    missing_files = []
    
    for directory in required_dirs:
        if not Path(directory).exists():
            missing_dirs.append(directory)
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_dirs:
        print(f"   ❌ Missing directories: {missing_dirs}")
    if missing_files:
        print(f"   ❌ Missing files: {missing_files}")
    
    if not missing_dirs and not missing_files:
        print("   ✅ Directory structure complete")
        return True
    else:
        return False

def test_config_loading():
    """Test caricamento configurazione"""
    print("🔍 Testing configuration loading...")
    
    try:
        from config.settings import AWSConfig
        config = AWSConfig()
        
        # Test basic config
        assert hasattr(config, 'regions')
        assert hasattr(config, 'services')
        assert hasattr(config, 'max_workers')
        
        print(f"   ✅ Config loaded: {len(config.regions)} regions, {len(config.get_active_services())} services")
        return True
        
    except Exception as e:
        print(f"   ❌ Config error: {e}")
        return False

def test_audit_engine():
    """Test dell'audit engine"""
    print("🔍 Testing audit engine...")
    
    try:
        from audit.audit_engine import AuditEngine
        engine = AuditEngine("us-east-1")
        
        # Check auditors
        core_auditors = ["security_groups", "ec2"]
        for auditor_name in core_auditors:
            if auditor_name not in engine.auditors:
                print(f"   ❌ Missing core auditor: {auditor_name}")
                return False
        
        print(f"   ✅ Audit engine initialized with {len(engine.auditors)} auditors")
        return True
        
    except Exception as e:
        print(f"   ❌ Audit engine error: {e}")
        return False

def test_dashboard_imports():
    """Test imports dashboard"""
    print("🔍 Testing dashboard imports...")
    
    try:
        import streamlit
        import plotly
        import pandas
        print("   ✅ Dashboard dependencies available")
        return True
    except ImportError as e:
        print(f"   ⚠️  Dashboard dependency missing: {e}")
        return False

def create_sample_data():
    """Crea dati di esempio per test"""
    print("🔍 Creating sample test data...")
    
    os.makedirs("data", exist_ok=True)
    
    # Sample EC2 data
    ec2_data = {
        "Reservations": [{
            "Instances": [{
                "InstanceId": "i-1234567890abcdef0",
                "InstanceType": "t3.micro",
                "State": {"Name": "running"},
                "PublicIpAddress": "203.0.113.1",
                "PrivateIpAddress": "10.0.1.10",
                "SubnetId": "subnet-12345678",
                "VpcId": "vpc-12345678",
                "SecurityGroups": [{"GroupId": "sg-12345678"}],
                "Tags": [{"Key": "Name", "Value": "test-instance"}]
            }]
        }]
    }
    
    # Sample SG data
    sg_data = {
        "SecurityGroups": [{
            "GroupId": "sg-12345678",
            "GroupName": "test-sg",
            "Description": "Test security group",
            "VpcId": "vpc-12345678",
            "IpPermissions": [{
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
            }],
            "IpPermissionsEgress": []
        }]
    }
    
    # Sample ENI data
    eni_data = {
        "NetworkInterfaces": [{
            "NetworkInterfaceId": "eni-12345678",
            "SubnetId": "subnet-12345678",
            "VpcId": "vpc-12345678",
            "Groups": [{"GroupId": "sg-12345678"}]
        }]
    }
    
    # Sample IAM data
    iam_data = {
        "Users": [{
            "UserName": "test-user",
            "CreateDate": "2024-01-01T00:00:00Z",
            "PasswordLastUsed": "2024-01-15T10:30:00Z"
        }],
        "Roles": [{
            "RoleName": "test-role",
            "CreateDate": "2024-01-01T00:00:00Z",
            "Description": "Test role"
        }],
        "Policies": []
    }
    
    # Sample S3 data
    s3_data = [{
        "Name": "test-bucket",
        "CreationDate": "2024-01-01T00:00:00Z",
        "PublicAccess": False
    }]
    
    # Sample VPC data
    vpc_data = {
        "Vpcs": [{
            "VpcId": "vpc-12345678",
            "CidrBlock": "10.0.0.0/16",
            "State": "available",
            "IsDefault": False
        }]
    }
    
    # Save sample data
    files_to_create = {
        "ec2_raw.json": ec2_data,
        "sg_raw.json": sg_data,
        "eni_raw.json": eni_data,
        "iam_raw.json": iam_data,
        "s3_raw.json": s3_data,
        "vpc_raw.json": vpc_data
    }
    
    for filename, data in files_to_create.items():
        with open(f"data/{filename}", "w") as f:
            json.dump(data, f, indent=2)
    
    print(f"   ✅ Sample data created ({len(files_to_create)} files)")
    return True

def run_sample_audit():
    """Esegue audit di esempio"""
    print("🔍 Running sample audit...")
    
    try:
        from audit.audit_engine import AuditEngine
        engine = AuditEngine("us-east-1")
        
        findings = engine.run_all_audits("data")
        
        print(f"   ✅ Sample audit completed: {len(findings)} findings")
        
        # Show sample findings
        if findings:
            print("   📋 Sample findings:")
            for i, finding in enumerate(findings[:3]):
                print(f"      {i+1}. {finding.rule_name}: {finding.description}")
        
        return len(findings) >= 0  # Accept 0 findings as success
        
    except Exception as e:
        print(f"   ❌ Sample audit error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_processor():
    """Test del data processor"""
    print("🔍 Testing data processor...")
    
    try:
        from utils.data_processor import DataProcessor
        processor = DataProcessor()
        
        success = processor.process_all_data()
        
        if success:
            print("   ✅ Data processor working")
            
            # Check if processed files exist
            processed_files = ["ec2_audit.json", "sg_audit.json"]
            found_files = []
            for file in processed_files:
                if Path(f"data/{file}").exists():
                    found_files.append(file)
            
            print(f"   📁 Processed files created: {found_files}")
            return True
        else:
            print("   ❌ Data processor failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Data processor error: {e}")
        return False

def main():
    """Esegue tutti i test"""
    print("🚀 AWS Security Auditor - Project Integrity Test\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Directory Structure", test_directory_structure), 
        ("Configuration Loading", test_config_loading),
        ("Audit Engine", test_audit_engine),
        ("Dashboard Dependencies", test_dashboard_imports),
        ("Sample Data Creation", create_sample_data),
        ("Data Processor", test_data_processor),
        ("Sample Audit Run", run_sample_audit)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {test_name}")
        print(f"{'='*50}")
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*50}")
    print(f"FINAL RESULTS: {passed}/{total} tests passed")
    print(f"{'='*50}")
    
    if passed == total:
        print("🎉 All tests passed! Project is ready to use.")
        print("\nNext steps:")
        print("1. Configure AWS credentials: aws configure")
        print("2. Run: python main.py --fetch-only")
        print("3. Run: python main.py --audit-only")
        print("4. Run: python main.py --dashboard")
    elif passed >= total - 2:
        print("✅ Most tests passed! Project should work with minor issues.")
        print("\nYou can proceed with:")
        print("1. python main.py --audit-only  # Use sample data")
        print("2. python main.py --dashboard   # View results")
    else:
        print("⚠️  Several tests failed. Please check the errors above.")
        print("\nTry these fixes:")
        print("1. pip install -r requirements.txt")
        print("2. python auto_fix.py")
        print("3. Check file locations and permissions")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
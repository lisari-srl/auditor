# audit/audit_engine.py - VERSIONE CORRETTA
import sys
import importlib
from typing import Dict, List, Any, Type, Optional
from audit.base_auditor import BaseAuditor, Finding
from audit.security_group_auditor import SecurityGroupAuditor
from audit.ec2_auditor import EC2Auditor
from config.audit_rules import Severity
import json
import os
from datetime import datetime
from pathlib import Path

class AuditEngine:
    """Engine principale per eseguire tutti gli audit con import dinamici"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.auditors: Dict[str, BaseAuditor] = {}
        self.all_findings: List[Finding] = []
        
        # Inizializza auditor base sempre disponibili
        self._init_core_auditors()
        
        # Tenta di inizializzare auditor avanzati
        self._init_advanced_auditors()
    
    def _init_core_auditors(self):
        """Inizializza auditor sempre disponibili"""
        try:
            self.auditors["security_groups"] = SecurityGroupAuditor(self.region)
            self.auditors["ec2"] = EC2Auditor(self.region)
            print(f"   ✅ Core auditors initialized for {self.region}")
        except Exception as e:
            print(f"   ❌ Error initializing core auditors: {e}")
    
    def _init_advanced_auditors(self):
        """Inizializza auditor avanzati con gestione errori"""
        
        # Advanced Security Group Auditor
        try:
            from audit.advanced_sg_auditor import AdvancedSecurityGroupAuditor
            self.auditors["advanced_security_groups"] = AdvancedSecurityGroupAuditor(self.region)
            print(f"   ✅ Advanced Security Group Auditor enabled for {self.region}")
        except ImportError as e:
            print(f"   ⚠️  Advanced Security Group Auditor not available: {e}")
        except Exception as e:
            print(f"   ❌ Error loading Advanced Security Group Auditor: {e}")
        
        # Potrebbero essere aggiunti altri auditor avanzati qui
        # Es: RDS Advanced Auditor, S3 Advanced Auditor, etc.
    
    def run_all_audits(self, data_dir: str = "data") -> List[Finding]:
        """Esegue tutti gli audit disponibili sui dati"""
        print(f"🔍 Starting comprehensive audit for region {self.region}...")
        
        self.all_findings = []
        audit_results = {}
        
        # Carica dati una volta per tutti gli auditor
        audit_data = self._load_audit_data(data_dir)
        
        if not audit_data:
            print(f"   ⚠️  No audit data found in {data_dir}")
            return self.all_findings
        
        # Esegui audit standard
        for auditor_name, auditor in self.auditors.items():
            if auditor_name in ["security_groups", "ec2"]:  # Core auditors
                try:
                    print(f"   🔍 Running {auditor_name} audit...")
                    findings = auditor.audit(audit_data)
                    self.all_findings.extend(findings)
                    audit_results[auditor_name] = len(findings)
                    print(f"      └─ {len(findings)} findings")
                except Exception as e:
                    print(f"      ❌ Error in {auditor_name} audit: {e}")
                    audit_results[auditor_name] = 0
        
        # Esegui audit avanzati
        if "advanced_security_groups" in self.auditors:
            try:
                print(f"   🛡️  Running advanced Security Groups audit...")
                advanced_auditor = self.auditors["advanced_security_groups"]
                advanced_findings = advanced_auditor.audit(audit_data)
                self.all_findings.extend(advanced_findings)
                audit_results["advanced_security_groups"] = len(advanced_findings)
                print(f"      └─ {len(advanced_findings)} advanced findings")
                
                # Salva ottimizzazioni se disponibili
                if hasattr(advanced_auditor, 'get_optimization_summary'):
                    try:
                        optimization_summary = advanced_auditor.get_optimization_summary()
                        self._save_advanced_sg_results(optimization_summary, advanced_auditor)
                        print(f"      └─ {optimization_summary.get('total_recommendations', 0)} optimization recommendations")
                    except Exception as e:
                        print(f"      ⚠️  Error saving advanced SG results: {e}")
                        
            except Exception as e:
                print(f"      ❌ Error in advanced SG audit: {e}")
                audit_results["advanced_security_groups"] = 0
        
        # Genera summary finale
        summary = self._generate_audit_summary(audit_results)
        print(f"✅ Audit completed: {summary}")
        
        # Salva tutti i findings
        self._save_all_findings()
        
        return self.all_findings
    
    def _load_audit_data(self, data_dir: str) -> Dict[str, Any]:
        """Carica tutti i dati necessari per l'audit"""
        data_path = Path(data_dir)
        combined_data = {}
        
        if not data_path.exists():
            print(f"   ❌ Data directory {data_dir} not found")
            return {}
        
        # File di dati richiesti
        required_files = [
            "ec2_raw.json", "sg_raw.json", "eni_raw.json", 
            "iam_raw.json", "s3_raw.json", "vpc_raw.json"
        ]
        
        files_loaded = 0
        for filename in required_files:
            filepath = data_path / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    # Merge dei dati con chiave appropriata
                    if isinstance(data, dict):
                        combined_data.update(data)
                    else:
                        # Se è lista, usa nome file come chiave
                        key = filename.replace("_raw.json", "").replace(".json", "")
                        combined_data[key] = data
                    
                    files_loaded += 1
                    
                except Exception as e:
                    print(f"   ⚠️  Error loading {filename}: {e}")
            else:
                print(f"   ⚠️  File {filename} not found")
        
        print(f"   📁 Loaded {files_loaded}/{len(required_files)} data files")
        return combined_data
    
    def _save_advanced_sg_results(self, optimization_summary: Dict[str, Any], advanced_auditor):
        """Salva risultati avanzati Security Groups"""
        try:
            reports_dir = Path("reports/security_groups")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Salva summary ottimizzazioni
            summary_file = reports_dir / "advanced_optimization_summary.json"
            with open(summary_file, "w") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "region": self.region,
                    "optimization_summary": optimization_summary
                }, f, indent=2)
            
            # Genera script di cleanup se disponibile
            if hasattr(advanced_auditor, 'generate_cleanup_script'):
                try:
                    cleanup_script = advanced_auditor.generate_cleanup_script({})
                    script_file = reports_dir / "advanced_cleanup.sh"
                    with open(script_file, "w") as f:
                        f.write(cleanup_script)
                    script_file.chmod(0o755)
                    print(f"      └─ Cleanup script saved: {script_file}")
                except Exception as e:
                    print(f"      ⚠️  Error generating cleanup script: {e}")
                    
        except Exception as e:
            print(f"   ⚠️  Error saving advanced SG results: {e}")
    
    def _generate_audit_summary(self, audit_results: Dict[str, int]) -> str:
        """Genera summary dei risultati audit"""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for finding in self.all_findings:
            severity = finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity)
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        total = len(self.all_findings)
        auditor_summary = ", ".join([f"{name}: {count}" for name, count in audit_results.items()])
        
        return f"{total} total findings ({severity_counts['critical']} critical, {severity_counts['high']} high) | {auditor_summary}"
    
    def _save_all_findings(self):
        """Salva tutti i findings in formato standardizzato"""
        try:
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            # Prepare findings data
            findings_data = {
                "metadata": {
                    "scan_time": datetime.now().isoformat(),
                    "region": self.region,
                    "total_findings": len(self.all_findings),
                    "auditors_used": list(self.auditors.keys()),
                    "advanced_sg_audit": "advanced_security_groups" in self.auditors
                },
                "findings": [f.to_dict() for f in self.all_findings]
            }
            
            # Save JSON
            findings_file = reports_dir / "security_findings.json"
            with open(findings_file, "w") as f:
                json.dump(findings_data, f, indent=2)
            
            # Generate markdown report
            self._generate_markdown_report(findings_data)
            
            print(f"   💾 Findings saved to {findings_file}")
            
        except Exception as e:
            print(f"   ❌ Error saving findings: {e}")
    
    def _generate_markdown_report(self, findings_data: Dict[str, Any]):
        """Genera report markdown"""
        try:
            report_file = Path("reports/security_audit_report.md")
            
            with open(report_file, "w") as f:
                f.write("# 🔒 AWS Security Audit Report\n\n")
                
                metadata = findings_data["metadata"]
                f.write(f"**Scan Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Region**: {metadata['region']}\n")
                f.write(f"**Total Findings**: {metadata['total_findings']}\n")
                f.write(f"**Auditors Used**: {', '.join(metadata['auditors_used'])}\n")
                
                if metadata.get("advanced_sg_audit"):
                    f.write("**Advanced Security Groups Analysis**: ✅ Enabled\n")
                
                f.write("\n## 📊 Summary by Severity\n\n")
                
                # Count by severity
                findings = findings_data["findings"]
                severity_counts = {}
                for finding in findings:
                    sev = finding.get("severity", "low")
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1
                
                # Severity table
                f.write("| Severity | Count |\n")
                f.write("|----------|-------|\n")
                for sev in ["critical", "high", "medium", "low"]:
                    count = severity_counts.get(sev, 0)
                    emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}[sev]
                    f.write(f"| {emoji} {sev.title()} | {count} |\n")
                
                # Critical findings section
                critical_findings = [f for f in findings if f.get("severity") == "critical"]
                if critical_findings:
                    f.write("\n## 🚨 Critical Findings\n\n")
                    for finding in critical_findings[:10]:  # Top 10
                        f.write(f"### {finding.get('rule_name', 'Unknown')}\n")
                        f.write(f"**Resource**: {finding.get('resource_name')} (`{finding.get('resource_id')}`)\n")
                        f.write(f"**Description**: {finding.get('description')}\n")
                        f.write(f"**Recommendation**: {finding.get('recommendation')}\n")
                        if finding.get('remediation'):
                            f.write(f"**Remediation**: `{finding['remediation']}`\n")
                        f.write("\n")
                
                # Advanced analysis note
                if metadata.get("advanced_sg_audit"):
                    f.write("\n## 🛡️ Advanced Security Groups Analysis\n\n")
                    f.write("Advanced Security Groups analysis has been performed.\n")
                    f.write("Check `reports/security_groups/` for detailed optimization recommendations.\n\n")
            
            print(f"   📋 Markdown report saved to {report_file}")
            
        except Exception as e:
            print(f"   ⚠️  Error generating markdown report: {e}")
    
    # Utility methods
    def get_findings_by_severity(self, severity: Severity) -> List[Finding]:
        """Ritorna findings per severity specifica"""
        return [f for f in self.all_findings if f.severity == severity]
    
    def get_critical_findings(self) -> List[Finding]:
        """Ritorna solo findings critici"""
        return self.get_findings_by_severity(Severity.CRITICAL)
    
    def get_findings_by_service(self, service: str) -> List[Finding]:
        """Ritorna findings per servizio specifico"""
        service_map = {
            "ec2": ["EC2Instance", "SecurityGroup"],
            "s3": ["S3Bucket"],
            "iam": ["IAMUser", "IAMRole", "IAMPolicy"],
            "vpc": ["VPC", "Subnet", "SecurityGroup"]
        }
        
        resource_types = service_map.get(service, [service])
        return [f for f in self.all_findings if f.resource_type in resource_types]
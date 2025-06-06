# audit/audit_engine.py
from typing import Dict, List, Any, Type
from audit.base_auditor import BaseAuditor, Finding
from audit.security_group_auditor import SecurityGroupAuditor
from audit.ec2_auditor import EC2Auditor
from config.audit_rules import Severity
import json
import os
from datetime import datetime

class AuditEngine:
    """Engine principale per eseguire tutti gli audit"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.auditors: Dict[str, BaseAuditor] = {
            "security_groups": SecurityGroupAuditor(region),
            "ec2": EC2Auditor(region),
        }
        self.all_findings: List[Finding] = []
    
    def run_all_audits(self, data_dir: str = "data") -> List[Finding]:
        """Esegue tutti gli audit sui dati nella directory specificata"""
        print(f"🔍 Avvio audit completo per regione {self.region}...")
        
        self.all_findings = []
        
        # Security Groups Audit
        if "security_groups" in self.auditors:
            sg_data = self._load_audit_data(data_dir, ["sg_raw.json", "eni_raw.json"])
            if sg_data:
                print("   🛡️  Audit Security Groups...")
                findings = self.auditors["security_groups"].audit(sg_data)
                self.all_findings.extend(findings)
                print(f"      └─ {len(findings)} findings trovati")
        
        # EC2 Audit
        if "ec2" in self.auditors:
            ec2_data = self._load_audit_data(data_dir, ["ec2_raw.json"])
            if ec2_data:
                print("   🖥️  Audit EC2 Instances...")
                findings = self.auditors["ec2"].audit(ec2_data)
                self.all_findings.extend(findings)
                print(f"      └─ {len(findings)} findings trovati")
        
        # Genera summary
        summary = self._generate_summary()
        print(f"✅ Audit completato: {summary}")
        
        # Salva risultati
        self._save_findings(data_dir)
        
        return self.all_findings
    
    def _load_audit_data(self, data_dir: str, required_files: List[str]) -> Dict[str, Any]:
        """Carica dati necessari per l'audit"""
        combined_data = {}
        
        for filename in required_files:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath) as f:
                        data = json.load(f)
                    
                    # Merge dei dati
                    if isinstance(data, dict):
                        combined_data.update(data)
                    else:
                        # Se è una lista, usa il nome del file come chiave
                        key = filename.replace("_raw.json", "").replace(".json", "")
                        combined_data[key] = data
                        
                except Exception as e:
                    print(f"   ❌ Errore caricamento {filename}: {e}")
        
        return combined_data
    
    def _generate_summary(self) -> str:
        """Genera summary dei findings"""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for finding in self.all_findings:
            summary[finding.severity.value] += 1
        
        total = len(self.all_findings)
        return f"{total} total ({summary['critical']} critical, {summary['high']} high, {summary['medium']} medium, {summary['low']} low)"
    
    def _save_findings(self, data_dir: str):
        """Salva findings in formato JSON e report markdown"""
        os.makedirs("reports", exist_ok=True)
        
        # Salva JSON completo
        findings_data = {
            "metadata": {
                "scan_time": datetime.now().isoformat(),
                "region": self.region,
                "total_findings": len(self.all_findings),
                "summary": self._generate_summary()
            },
            "findings": [f.to_dict() for f in self.all_findings]
        }
        
        with open("reports/security_findings.json", "w") as f:
            json.dump(findings_data, f, indent=2)
        
        # Genera report markdown
        self._generate_markdown_report()
    
    def _generate_markdown_report(self):
        """Genera report markdown strutturato"""
        with open("reports/security_audit_report.md", "w") as f:
            f.write("# 🔒 AWS Security Audit Report\n\n")
            f.write(f"**Scan Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Region**: {self.region}\n")
            f.write(f"**Total Findings**: {len(self.all_findings)}\n\n")
            
            # Summary per severity
            severity_counts = {}
            for finding in self.all_findings:
                sev = finding.severity.value
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            f.write("## 📊 Summary\n\n")
            f.write("| Severity | Count |\n")
            f.write("|----------|-------|\n")
            for sev in ["critical", "high", "medium", "low"]:
                count = severity_counts.get(sev, 0)
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}[sev]
                f.write(f"| {emoji} {sev.title()} | {count} |\n")
            
            # Findings per severity
            for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
                severity_findings = [f for f in self.all_findings if f.severity == severity]
                if not severity_findings:
                    continue
                
                f.write(f"\n## {severity.value.upper()} Findings\n\n")
                
                for finding in severity_findings:
                    f.write(f"### {finding.rule_name}\n")
                    f.write(f"**Resource**: {finding.resource_name} (`{finding.resource_id}`)\n")
                    f.write(f"**Description**: {finding.description}\n")
                    f.write(f"**Recommendation**: {finding.recommendation}\n")
                    if finding.remediation:
                        f.write(f"**Remediation**: `{finding.remediation}`\n")
                    f.write(f"**Compliance**: {', '.join(finding.compliance_frameworks)}\n\n")
    
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
            "iam": ["IAMUser", "IAMRole", "IAMPolicy"]
        }
        
        resource_types = service_map.get(service, [service])
        return [f for f in self.all_findings if f.resource_type in resource_types]
    
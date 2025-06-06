# audit/base_auditor.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from config.audit_rules import AuditRule, Severity

@dataclass
class Finding:
    """Risultato di una regola di audit"""
    resource_id: str
    resource_type: str
    resource_name: str
    rule_id: str
    rule_name: str
    description: str
    severity: Severity
    region: str
    recommendation: str
    remediation: str
    compliance_frameworks: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il finding in dizionario"""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "description": self.description,
            "severity": self.severity.value,
            "region": self.region,
            "recommendation": self.recommendation,
            "remediation": self.remediation,
            "compliance_frameworks": self.compliance_frameworks,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }

class BaseAuditor(ABC):
    """Classe base per tutti gli auditor"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.findings: List[Finding] = []
    
    @abstractmethod
    def audit(self, data: Dict[str, Any]) -> List[Finding]:
        """Implementa la logica di audit specifica"""
        pass
    
    def add_finding(self, finding: Finding):
        """Aggiunge un finding alla lista"""
        self.findings.append(finding)
    
    def get_findings_by_severity(self, severity: Severity) -> List[Finding]:
        """Ritorna findings per severity specifica"""
        return [f for f in self.findings if f.severity == severity]
    
    def get_critical_findings(self) -> List[Finding]:
        """Ritorna solo finding critici"""
        return self.get_findings_by_severity(Severity.CRITICAL)
    
    def get_findings_summary(self) -> Dict[str, int]:
        """Ritorna sommario dei findings per severity"""
        summary = {s.value: 0 for s in Severity}
        for finding in self.findings:
            summary[finding.severity.value] += 1
        return summary
    
    def clear_findings(self):
        """Pulisce i findings"""
        self.findings = []

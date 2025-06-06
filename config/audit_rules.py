# config/audit_rules.py
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditRule:
    """Definizione di una regola di audit"""
    rule_id: str
    name: str
    description: str
    severity: Severity
    service: str
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

# Regole predefinite
PREDEFINED_RULES = {
    # Security Group Rules
    "SG001": AuditRule(
        rule_id="SG001",
        name="Security Group aperto a Internet",
        description="Security Group permette traffico da 0.0.0.0/0",
        severity=Severity.HIGH,
        service="ec2",
        metadata={"ports": [22, 3389, 3306, 5432]}
    ),
    "SG002": AuditRule(
        rule_id="SG002", 
        name="Security Group non utilizzato",
        description="Security Group non associato a risorse",
        severity=Severity.LOW,
        service="ec2"
    ),
    "SG003": AuditRule(
        rule_id="SG003",
        name="Porte sensibili esposte",
        description="Porte critiche (SSH, RDP, DB) esposte pubblicamente",
        severity=Severity.CRITICAL,
        service="ec2",
        metadata={"critical_ports": [22, 3389, 1433, 3306, 5432]}
    ),
    
    # EC2 Rules  
    "EC2001": AuditRule(
        rule_id="EC2001",
        name="Istanza EC2 con IP pubblico",
        description="Istanza EC2 con indirizzo IP pubblico assegnato", 
        severity=Severity.MEDIUM,
        service="ec2"
    ),
    "EC2002": AuditRule(
        rule_id="EC2002",
        name="Istanza EC2 stopped da molto tempo",
        description="Istanza EC2 ferma da più di 30 giorni",
        severity=Severity.LOW,
        service="ec2",
        metadata={"max_stopped_days": 30}
    ),
    
    # S3 Rules
    "S3001": AuditRule(
        rule_id="S3001",
        name="Bucket S3 pubblicamente accessibile",
        description="Bucket S3 con accesso pubblico in lettura/scrittura",
        severity=Severity.CRITICAL,
        service="s3"
    ),
    "S3002": AuditRule(
        rule_id="S3002",
        name="Bucket S3 senza encryption",
        description="Bucket S3 senza encryption at rest configurata",
        severity=Severity.HIGH,
        service="s3"
    ),
    
    # IAM Rules
    "IAM001": AuditRule(
        rule_id="IAM001",
        name="Utente IAM senza attività recente", 
        description="Utente IAM non utilizzato negli ultimi 90 giorni",
        severity=Severity.MEDIUM,
        service="iam",
        metadata={"max_inactive_days": 90}
    ),
    "IAM002": AuditRule(
        rule_id="IAM002",
        name="Ruolo IAM con permessi amministratore",
        description="Ruolo IAM con policy AdministratorAccess",
        severity=Severity.HIGH, 
        service="iam"
    ),
    
    # VPC Rules
    "VPC001": AuditRule(
        rule_id="VPC001",
        name="Utilizzo VPC default",
        description="Risorse deployate nella VPC default",
        severity=Severity.MEDIUM,
        service="vpc"
    ),
    "VPC002": AuditRule(
        rule_id="VPC002",
        name="Subnet pubblica senza protezioni",
        description="Subnet pubblica senza controlli di accesso aggiuntivi",
        severity=Severity.MEDIUM,
        service="vpc"
    ),
}

def get_rules_for_service(service: str) -> List[AuditRule]:
    """Ritorna tutte le regole per un servizio specifico"""
    return [rule for rule in PREDEFINED_RULES.values() if rule.service == service]

def get_enabled_rules() -> List[AuditRule]:
    """Ritorna tutte le regole abilitate"""
    return [rule for rule in PREDEFINED_RULES.values() if rule.enabled]

def get_rule_by_id(rule_id: str) -> Optional[AuditRule]:
    """Ritorna una regola specifica per ID"""
    return PREDEFINED_RULES.get(rule_id)

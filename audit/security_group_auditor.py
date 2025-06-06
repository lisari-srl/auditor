# audit/security_group_auditor.py
from audit.base_auditor import BaseAuditor, Finding
from config.audit_rules import Severity, get_rule_by_id
from datetime import datetime, timezone
from typing import Dict, List, Any

class SecurityGroupAuditor(BaseAuditor):
    """Auditor specializzato per Security Groups"""
    
    def audit(self, data: Dict[str, Any]) -> List[Finding]:
        """Analizza Security Groups per problemi di sicurezza"""
        self.clear_findings()
        
        security_groups = data.get("SecurityGroups", [])
        network_interfaces = data.get("NetworkInterfaces", [])
        
        # Mappa SG utilizzati
        used_sg_ids = set()
        for eni in network_interfaces:
            for group in eni.get("Groups", []):
                used_sg_ids.add(group.get("GroupId"))
        
        for sg in security_groups:
            # Check SG aperti a Internet
            self._check_open_security_groups(sg)
            
            # Check SG non utilizzati
            self._check_unused_security_groups(sg, used_sg_ids)
            
            # Check porte sensibili
            self._check_sensitive_ports(sg)
            
            # Check regole duplicate
            self._check_duplicate_rules(sg)
        
        return self.findings
    
    def _check_open_security_groups(self, sg: Dict[str, Any]):
        """Verifica SG aperti a 0.0.0.0/0"""
        rule = get_rule_by_id("SG001")
        if not rule or not rule.enabled:
            return
        
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        
        # Check ingress rules
        for perm in sg.get("IpPermissions", []):
            for ip_range in perm.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0":
                    port_info = f"{perm.get('FromPort', 'All')}"
                    if perm.get("FromPort") != perm.get("ToPort"):
                        port_info += f"-{perm.get('ToPort', 'All')}"
                    
                    self.add_finding(Finding(
                        resource_id=sg_id,
                        resource_type="SecurityGroup",
                        resource_name=sg_name,
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        description=f"Security Group '{sg_name}' permette traffico ingress da 0.0.0.0/0 su porta {port_info}",
                        severity=rule.severity,
                        region=self.region,
                        recommendation="Restringere l'accesso a IP specifici o range più piccoli",
                        remediation=f"aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol {perm.get('IpProtocol')} --port {perm.get('FromPort')} --cidr 0.0.0.0/0",
                        compliance_frameworks=["CIS", "SOC2", "PCI-DSS"],
                        metadata={
                            "port": perm.get("FromPort"),
                            "protocol": perm.get("IpProtocol"),
                            "direction": "ingress",
                            "vpc_id": sg.get("VpcId")
                        },
                        timestamp=datetime.now(timezone.utc)
                    ))
    
    def _check_unused_security_groups(self, sg: Dict[str, Any], used_sg_ids: set):
        """Verifica SG non utilizzati"""
        rule = get_rule_by_id("SG002")
        if not rule or not rule.enabled:
            return
        
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        
        # Skip default security group
        if sg_name == "default":
            return
        
        if sg_id not in used_sg_ids:
            self.add_finding(Finding(
                resource_id=sg_id,
                resource_type="SecurityGroup", 
                resource_name=sg_name,
                rule_id=rule.rule_id,
                rule_name=rule.name,
                description=f"Security Group '{sg_name}' non è associato a nessuna risorsa",
                severity=rule.severity,
                region=self.region,
                recommendation="Rimuovere Security Group non utilizzati per ridurre la superficie di attacco",
                remediation=f"aws ec2 delete-security-group --group-id {sg_id}",
                compliance_frameworks=["CIS"],
                metadata={
                    "vpc_id": sg.get("VpcId"),
                    "description": sg.get("Description")
                },
                timestamp=datetime.now(timezone.utc)
            ))
    
    def _check_sensitive_ports(self, sg: Dict[str, Any]):
        """Verifica porte sensibili esposte pubblicamente"""
        rule = get_rule_by_id("SG003")
        if not rule or not rule.enabled:
            return
        
        critical_ports = rule.metadata.get("critical_ports", [22, 3389, 1433, 3306, 5432])
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        
        for perm in sg.get("IpPermissions", []):
            from_port = perm.get("FromPort")
            to_port = perm.get("ToPort")
            
            # Check se range include porte critiche
            for critical_port in critical_ports:
                port_exposed = False
                if from_port is None and to_port is None:
                    # All ports (-1 protocol)
                    port_exposed = True
                elif from_port <= critical_port <= to_port:
                    port_exposed = True
                
                if port_exposed:
                    for ip_range in perm.get("IpRanges", []):
                        if ip_range.get("CidrIp") == "0.0.0.0/0":
                            port_name = self._get_port_name(critical_port)
                            
                            self.add_finding(Finding(
                                resource_id=sg_id,
                                resource_type="SecurityGroup",
                                resource_name=sg_name,
                                rule_id=rule.rule_id,
                                rule_name=rule.name,
                                description=f"Porta critica {critical_port} ({port_name}) esposta pubblicamente su Security Group '{sg_name}'",
                                severity=rule.severity,
                                region=self.region,
                                recommendation=f"Bloccare accesso pubblico alla porta {critical_port} o utilizzare un bastion host",
                                remediation=f"aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol {perm.get('IpProtocol')} --port {critical_port} --cidr 0.0.0.0/0",
                                compliance_frameworks=["CIS", "SOC2", "PCI-DSS", "ISO27001"],
                                metadata={
                                    "critical_port": critical_port,
                                    "port_name": port_name,
                                    "protocol": perm.get("IpProtocol"),
                                    "vpc_id": sg.get("VpcId")
                                },
                                timestamp=datetime.now(timezone.utc)
                            ))
    
    def _check_duplicate_rules(self, sg: Dict[str, Any]):
        """Verifica regole duplicate"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        
        seen_rules = set()
        for direction in ["IpPermissions", "IpPermissionsEgress"]:
            for perm in sg.get(direction, []):
                rule_key = (
                    perm.get("IpProtocol"),
                    perm.get("FromPort"),
                    perm.get("ToPort"),
                    tuple(sorted([ip.get("CidrIp") for ip in perm.get("IpRanges", [])]))
                )
                
                if rule_key in seen_rules:
                    self.add_finding(Finding(
                        resource_id=sg_id,
                        resource_type="SecurityGroup",
                        resource_name=sg_name,
                        rule_id="SG004",
                        rule_name="Regole duplicate",
                        description=f"Security Group '{sg_name}' contiene regole duplicate",
                        severity=Severity.LOW,
                        region=self.region,
                        recommendation="Rimuovere regole duplicate per semplificare la gestione",
                        remediation="Rivedere manualmente le regole del Security Group",
                        compliance_frameworks=["Best Practices"],
                        metadata={
                            "duplicate_rule": rule_key,
                            "vpc_id": sg.get("VpcId")
                        },
                        timestamp=datetime.now(timezone.utc)
                    ))
                
                seen_rules.add(rule_key)
    
    def _get_port_name(self, port: int) -> str:
        """Ritorna nome servizio per porta"""
        port_names = {
            22: "SSH",
            80: "HTTP", 
            443: "HTTPS",
            3389: "RDP",
            3306: "MySQL",
            5432: "PostgreSQL",
            1433: "MSSQL",
            25: "SMTP",
            53: "DNS",
            21: "FTP"
        }
        return port_names.get(port, f"Port {port}")

# audit/ec2_auditor.py
from audit.base_auditor import BaseAuditor, Finding
from config.audit_rules import Severity, get_rule_by_id
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

class EC2Auditor(BaseAuditor):
    """Auditor specializzato per istanze EC2"""
    
    def audit(self, data: Dict[str, Any]) -> List[Finding]:
        """Analizza istanze EC2 per problemi di sicurezza e conformità"""
        self.clear_findings()
        
        reservations = data.get("Reservations", [])
        
        for reservation in reservations:
            for instance in reservation.get("Instances", []):
                # Check istanze con IP pubblico
                self._check_public_ip_instances(instance)
                
                # Check istanze stopped da molto tempo
                self._check_long_stopped_instances(instance)
                
                # Check istanze senza monitoring
                self._check_monitoring_disabled(instance)
                
                # Check istanze in subnet pubbliche
                self._check_instances_in_public_subnets(instance)
        
        return self.findings
    
    def _check_public_ip_instances(self, instance: Dict[str, Any]):
        """Verifica istanze con IP pubblico"""
        rule = get_rule_by_id("EC2001")
        if not rule or not rule.enabled:
            return
        
        instance_id = instance.get("InstanceId")
        instance_name = self._get_instance_name(instance)
        public_ip = instance.get("PublicIpAddress")
        
        if public_ip:
            self.add_finding(Finding(
                resource_id=instance_id,
                resource_type="EC2Instance",
                resource_name=instance_name,
                rule_id=rule.rule_id,
                rule_name=rule.name,
                description=f"Istanza EC2 '{instance_name}' ha un indirizzo IP pubblico ({public_ip})",
                severity=rule.severity,
                region=self.region,
                recommendation="Utilizzare un Load Balancer o NAT Gateway invece di IP pubblici diretti",
                remediation="Spostare l'istanza in subnet privata e configurare accesso tramite Load Balancer",
                compliance_frameworks=["CIS", "Well-Architected"],
                metadata={
                    "public_ip": public_ip,
                    "instance_type": instance.get("InstanceType"),
                    "subnet_id": instance.get("SubnetId"),
                    "vpc_id": instance.get("VpcId"),
                    "state": instance.get("State", {}).get("Name")
                },
                timestamp=datetime.now(timezone.utc)
            ))
    
    def _check_long_stopped_instances(self, instance: Dict[str, Any]):
        """Verifica istanze stopped da molto tempo"""
        rule = get_rule_by_id("EC2002")
        if not rule or not rule.enabled:
            return
        
        state = instance.get("State", {}).get("Name")
        if state != "stopped":
            return
        
        instance_id = instance.get("InstanceId")
        instance_name = self._get_instance_name(instance)
        
        # Parsing StateTransitionReason per ottenere data
        state_reason = instance.get("StateTransitionReason", "")
        try:
            # Formato: "User initiated (2024-10-07 17:58:28 GMT)"
            if "(" in state_reason and "GMT)" in state_reason:
                date_str = state_reason.split("(")[1].split(" GMT)")[0]
                stop_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                stop_date = stop_date.replace(tzinfo=timezone.utc)
                
                days_stopped = (datetime.now(timezone.utc) - stop_date).days
                max_days = rule.metadata.get("max_stopped_days", 30)
                
                if days_stopped > max_days:
                    self.add_finding(Finding(
                        resource_id=instance_id,
                        resource_type="EC2Instance",
                        resource_name=instance_name,
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        description=f"Istanza EC2 '{instance_name}' è ferma da {days_stopped} giorni",
                        severity=rule.severity,
                        region=self.region,
                        recommendation=f"Valutare se terminare l'istanza se non più necessaria per ridurre costi",
                        remediation=f"aws ec2 terminate-instances --instance-ids {instance_id}",
                        compliance_frameworks=["Cost Optimization"],
                        metadata={
                            "days_stopped": days_stopped,
                            "stop_date": stop_date.isoformat(),
                            "instance_type": instance.get("InstanceType"),
                            "max_allowed_days": max_days
                        },
                        timestamp=datetime.now(timezone.utc)
                    ))
        except Exception:
            # Non riesco a parsare la data, skip
            pass
    
    def _check_monitoring_disabled(self, instance: Dict[str, Any]):
        """Verifica istanze senza monitoring CloudWatch dettagliato"""
        monitoring = instance.get("Monitoring", {})
        if monitoring.get("State") != "enabled":
            instance_id = instance.get("InstanceId")
            instance_name = self._get_instance_name(instance)
            
            self.add_finding(Finding(
                resource_id=instance_id,
                resource_type="EC2Instance",
                resource_name=instance_name,
                rule_id="EC2003",
                rule_name="Monitoring CloudWatch disabilitato",
                description=f"Istanza EC2 '{instance_name}' non ha il monitoring CloudWatch dettagliato abilitato",
                severity=Severity.LOW,
                region=self.region,
                recommendation="Abilitare CloudWatch detailed monitoring per migliore visibilità",
                remediation=f"aws ec2 monitor-instances --instance-ids {instance_id}",
                compliance_frameworks=["Well-Architected"],
                metadata={
                    "monitoring_state": monitoring.get("State", "disabled"),
                    "instance_type": instance.get("InstanceType")
                },
                timestamp=datetime.now(timezone.utc)
            ))
    
    def _check_instances_in_public_subnets(self, instance: Dict[str, Any]):
        """Verifica istanze in subnet pubbliche (logica semplificata)"""
        # Questo check richiederebbe dati delle subnet per determinare se sono pubbliche
        # Per ora facciamo un check basico basato sulla presenza di IP pubblico
        public_ip = instance.get("PublicIpAddress")
        if public_ip:
            instance_id = instance.get("InstanceId")
            instance_name = self._get_instance_name(instance)
            
            self.add_finding(Finding(
                resource_id=instance_id,
                resource_type="EC2Instance",
                resource_name=instance_name,
                rule_id="EC2004",
                rule_name="Istanza in subnet pubblica",
                description=f"Istanza EC2 '{instance_name}' sembra essere in una subnet pubblica",
                severity=Severity.MEDIUM,
                region=self.region,
                recommendation="Spostare istanze non-web in subnet private per maggiore sicurezza",
                remediation="Configurare subnet private e NAT Gateway per accesso Internet",
                compliance_frameworks=["CIS", "Well-Architected"],
                metadata={
                    "subnet_id": instance.get("SubnetId"),
                    "public_ip": public_ip,
                    "instance_type": instance.get("InstanceType")
                },
                timestamp=datetime.now(timezone.utc)
            ))
    
    def _get_instance_name(self, instance: Dict[str, Any]) -> str:
        """Estrae il nome dell'istanza dai tag"""
        for tag in instance.get("Tags", []):
            if tag.get("Key") == "Name":
                return tag.get("Value", instance.get("InstanceId"))
        return instance.get("InstanceId", "Unknown")

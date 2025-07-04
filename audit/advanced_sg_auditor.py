# audit/advanced_sg_auditor.py - VERSIONE CORRETTA
from audit.base_auditor import BaseAuditor, Finding
from config.audit_rules import Severity
from datetime import datetime, timezone
from typing import Dict, List, Any, Set, Tuple
import json

class AdvancedSecurityGroupAuditor(BaseAuditor):
    """Auditor avanzato per Security Groups con analisi dettagliata e ottimizzazione"""
    
    def __init__(self, region: str = "us-east-1"):
        super().__init__(region)
        self.optimization_recommendations = []
        self.security_violations = []
        self.cost_savings_opportunities = []
    
    def audit(self, data: Dict[str, Any]) -> List[Finding]:
        """Analisi completa Security Groups con ottimizzazioni"""
        self.clear_findings()
        self.optimization_recommendations = []
        self.security_violations = []
        self.cost_savings_opportunities = []
        
        security_groups = data.get("SecurityGroups", [])
        network_interfaces = data.get("NetworkInterfaces", [])
        ec2_instances = self._extract_ec2_instances(data.get("ec2_raw", {}))
        
        # Mappa utilizzo SG
        sg_usage_map = self._build_sg_usage_map(network_interfaces, ec2_instances)
        
        print(f"   🔍 Analyzing {len(security_groups)} Security Groups...")
        
        for sg in security_groups:
            # Analisi di sicurezza
            self._analyze_security_violations(sg, sg_usage_map)
            
            # Analisi di ottimizzazione
            self._analyze_optimization_opportunities(sg, sg_usage_map)
            
            # Analisi costi
            self._analyze_cost_optimization(sg, sg_usage_map)
            
            # Analisi conformità
            self._analyze_compliance_issues(sg)
        
        # Genera raccomandazioni consolidate
        self._generate_consolidation_recommendations(security_groups, sg_usage_map)
        
        return self.findings
    
    def _extract_ec2_instances(self, ec2_data: Dict) -> List[Dict]:
        """Estrae istanze EC2 dai dati raw"""
        instances = []
        for reservation in ec2_data.get("Reservations", []):
            instances.extend(reservation.get("Instances", []))
        return instances
    
    def _build_sg_usage_map(self, network_interfaces: List[Dict], ec2_instances: List[Dict]) -> Dict[str, Dict]:
        """Costruisce mappa dettagliata utilizzo Security Groups"""
        usage_map = {}
        
        # Mappa SG da ENI
        for eni in network_interfaces:
            for group in eni.get("Groups", []):
                sg_id = group.get("GroupId")
                if sg_id:
                    if sg_id not in usage_map:
                        usage_map[sg_id] = {
                            "attached_enis": [],
                            "attached_instances": [],
                            "instance_types": set(),
                            "subnets": set(),
                            "vpcs": set(),
                            "total_attachments": 0
                        }
                    
                    usage_map[sg_id]["attached_enis"].append({
                        "eni_id": eni.get("NetworkInterfaceId"),
                        "subnet_id": eni.get("SubnetId"),
                        "vpc_id": eni.get("VpcId"),
                        "status": eni.get("Status"),
                        "instance_id": eni.get("Attachment", {}).get("InstanceId"),
                        "device_index": eni.get("Attachment", {}).get("DeviceIndex")
                    })
                    
                    if eni.get("SubnetId"):
                        usage_map[sg_id]["subnets"].add(eni.get("SubnetId"))
                    if eni.get("VpcId"):
                        usage_map[sg_id]["vpcs"].add(eni.get("VpcId"))
        
        # Arricchisci con dati istanze
        for instance in ec2_instances:
            instance_id = instance.get("InstanceId")
            instance_type = instance.get("InstanceType")
            
            for sg in instance.get("SecurityGroups", []):
                sg_id = sg.get("GroupId")
                if sg_id in usage_map:
                    usage_map[sg_id]["attached_instances"].append({
                        "instance_id": instance_id,
                        "instance_type": instance_type,
                        "state": instance.get("State", {}).get("Name"),
                        "launch_time": instance.get("LaunchTime"),
                        "public_ip": instance.get("PublicIpAddress"),
                        "private_ip": instance.get("PrivateIpAddress")
                    })
                    
                    if instance_type:
                        usage_map[sg_id]["instance_types"].add(instance_type)
                    
                    usage_map[sg_id]["total_attachments"] += 1
        
        return usage_map
    
    def _analyze_security_violations(self, sg: Dict[str, Any], usage_map: Dict):
        """Analizza violazioni di sicurezza specifiche"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        
        # Check porte critiche con analisi avanzata
        critical_ports = {
            22: {"name": "SSH", "severity": Severity.CRITICAL, "alternatives": ["AWS Systems Manager Session Manager"]},
            3389: {"name": "RDP", "severity": Severity.CRITICAL, "alternatives": ["AWS Systems Manager Session Manager"]},
            21: {"name": "FTP", "severity": Severity.HIGH, "alternatives": ["SFTP", "AWS Transfer Family"]},
            23: {"name": "Telnet", "severity": Severity.CRITICAL, "alternatives": ["SSH"]},
            135: {"name": "RPC", "severity": Severity.HIGH, "alternatives": ["Disable or restrict"]},
            139: {"name": "NetBIOS", "severity": Severity.HIGH, "alternatives": ["Disable or restrict"]},
            445: {"name": "SMB", "severity": Severity.HIGH, "alternatives": ["VPN access only"]},
            1433: {"name": "MSSQL", "severity": Severity.HIGH, "alternatives": ["VPC peering", "Private subnets"]},
            3306: {"name": "MySQL", "severity": Severity.HIGH, "alternatives": ["VPC peering", "Private subnets"]},
            5432: {"name": "PostgreSQL", "severity": Severity.HIGH, "alternatives": ["VPC peering", "Private subnets"]},
            1521: {"name": "Oracle", "severity": Severity.HIGH, "alternatives": ["VPC peering", "Private subnets"]},
            27017: {"name": "MongoDB", "severity": Severity.HIGH, "alternatives": ["VPC peering", "Private subnets"]},
            6379: {"name": "Redis", "severity": Severity.HIGH, "alternatives": ["VPC peering", "Private subnets"]},
            11211: {"name": "Memcached", "severity": Severity.HIGH, "alternatives": ["VPC peering", "Private subnets"]},
            9200: {"name": "Elasticsearch", "severity": Severity.MEDIUM, "alternatives": ["VPC peering", "Private subnets"]},
            5984: {"name": "CouchDB", "severity": Severity.MEDIUM, "alternatives": ["VPC peering", "Private subnets"]}
        }
        
        for rule in sg.get("IpPermissions", []):
            self._analyze_ingress_rule(sg, rule, critical_ports, usage_map)
        
        for rule in sg.get("IpPermissionsEgress", []):
            self._analyze_egress_rule(sg, rule, usage_map)
        
        # Analisi regole ridondanti
        self._check_redundant_rules(sg)
        
        # Analisi overlapping rules
        self._check_overlapping_rules(sg)
        
        # Check default deny policy
        self._check_default_deny_policy(sg)
    
    def _analyze_ingress_rule(self, sg: Dict, rule: Dict, critical_ports: Dict, usage_map: Dict):
        """Analizza singola regola ingress"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        protocol = rule.get("IpProtocol", "")
        from_port = rule.get("FromPort")
        to_port = rule.get("ToPort")
        
        # Analizza ogni range IP
        for ip_range in rule.get("IpRanges", []):
            cidr = ip_range.get("CidrIp")
            description = ip_range.get("Description", "")
            
            if cidr == "0.0.0.0/0":
                self._handle_open_ingress(sg, rule, ip_range, critical_ports, usage_map)
            elif self._is_broad_cidr(cidr):
                self._handle_broad_cidr(sg, rule, ip_range, usage_map)
        
        # Analizza Security Group references
        for sg_ref in rule.get("UserIdGroupPairs", []):
            self._analyze_sg_reference(sg, rule, sg_ref, usage_map)
    
    def _handle_open_ingress(self, sg: Dict, rule: Dict, ip_range: Dict, critical_ports: Dict, usage_map: Dict):
        """Gestisce regole ingress aperte a 0.0.0.0/0"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        from_port = rule.get("FromPort")
        to_port = rule.get("ToPort")
        protocol = rule.get("IpProtocol")
        description = ip_range.get("Description", "")
        
        # Determina criticità basata su porta e contesto
        severity = Severity.MEDIUM
        recommendations = []
        alternatives = []
        
        if protocol == "-1":  # All traffic
            severity = Severity.CRITICAL
            recommendations.append("Remove all-traffic access from 0.0.0.0/0")
            alternatives.extend(["Use specific ports", "Implement WAF", "Use VPC peering"])
        elif from_port is not None and to_port is not None:
            # Fixed severity comparison
            severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
            current_severity_index = severity_order.index(severity)
            
            for port in range(from_port, to_port + 1):
                if port in critical_ports:
                    port_info = critical_ports[port]
                    port_severity_index = severity_order.index(port_info["severity"])
                    
                    # Fix: Confronto corretto delle severity
                    if port_severity_index > current_severity_index:
                        severity = port_info["severity"]
                        current_severity_index = port_severity_index
                    
                    alternatives.extend(port_info["alternatives"])
        
        # Controlla se è veramente necessario
        usage = usage_map.get(sg_id, {})
        attached_instances = usage.get("attached_instances", [])
        
        # Se è attaccato a istanze in subnet private, è meno critico
        is_internal_use = all(
            not inst.get("public_ip") 
            for inst in attached_instances
        )
        
        if is_internal_use and severity == Severity.HIGH:
            severity = Severity.MEDIUM
            recommendations.append("Consider moving to private subnet access only")
        
        # Genera finding
        port_desc = f"{from_port}" if from_port == to_port else f"{from_port}-{to_port}"
        if protocol == "-1":
            port_desc = "All ports"
        
        finding_desc = f"Security Group '{sg_name}' allows {protocol} traffic on {port_desc} from 0.0.0.0/0"
        if description:
            finding_desc += f" ({description})"
        
        recommendation = "Restrict access to specific IP ranges or use AWS services like CloudFront, WAF, or Load Balancers"
        if alternatives:
            recommendation += f". Alternatives: {', '.join(set(alternatives))}"
        
        remediation_cmd = f"aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol {protocol}"
        if from_port is not None:
            remediation_cmd += f" --port {from_port}"
        remediation_cmd += " --cidr 0.0.0.0/0"
        
        self.add_finding(Finding(
            resource_id=sg_id,
            resource_type="SecurityGroup",
            resource_name=sg_name,
            rule_id="SG_ADV_001",
            rule_name="Ingress aperto da Internet",
            description=finding_desc,
            severity=severity,
            region=self.region,
            recommendation=recommendation,
            remediation=remediation_cmd,
            compliance_frameworks=["CIS", "SOC2", "PCI-DSS", "ISO27001"],
            metadata={
                "port_range": f"{from_port}-{to_port}",
                "protocol": protocol,
                "cidr": "0.0.0.0/0",
                "attached_instances": len(attached_instances),
                "has_public_instances": not is_internal_use,
                "description": description,
                "alternatives": list(set(alternatives))
            },
            timestamp=datetime.now(timezone.utc)
        ))
    
    def _is_broad_cidr(self, cidr: str) -> bool:
        """Verifica se CIDR è troppo ampio"""
        if not cidr or "/" not in cidr:
            return False
        
        try:
            prefix_length = int(cidr.split("/")[1])
            return prefix_length < 16  # /15 o meno è considerato ampio
        except:
            return False
    
    def _handle_broad_cidr(self, sg: Dict, rule: Dict, ip_range: Dict, usage_map: Dict):
        """Gestisce CIDR troppo ampi"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        cidr = ip_range.get("CidrIp")
        from_port = rule.get("FromPort")
        to_port = rule.get("ToPort")
        protocol = rule.get("IpProtocol")
        
        try:
            prefix_length = int(cidr.split("/")[1])
            ip_count = 2 ** (32 - prefix_length)
            
            if ip_count > 65536:  # Più di 65k IPs
                self.add_finding(Finding(
                    resource_id=sg_id,
                    resource_type="SecurityGroup",
                    resource_name=sg_name,
                    rule_id="SG_ADV_002",
                    rule_name="CIDR range troppo ampio",
                    description=f"Security Group '{sg_name}' permette accesso da CIDR ampio {cidr} ({ip_count:,} IPs)",
                    severity=Severity.MEDIUM,
                    region=self.region,
                    recommendation="Restringere il CIDR range ai soli IP necessari",
                    remediation=f"aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol {protocol} --port {from_port} --cidr {cidr}",
                    compliance_frameworks=["CIS", "Best Practices"],
                    metadata={
                        "cidr": cidr,
                        "ip_count": ip_count,
                        "prefix_length": prefix_length,
                        "port_range": f"{from_port}-{to_port}"
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
        except:
            pass
    
    def _analyze_egress_rule(self, sg: Dict, rule: Dict, usage_map: Dict):
        """Analizza regole egress"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        protocol = rule.get("IpProtocol")
        from_port = rule.get("FromPort")
        to_port = rule.get("ToPort")
        
        # Check egress troppo permissivo
        for ip_range in rule.get("IpRanges", []):
            cidr = ip_range.get("CidrIp")
            
            if cidr == "0.0.0.0/0" and protocol == "-1":
                # Egress tutto aperto - comune ma non best practice
                usage = usage_map.get(sg_id, {})
                if usage.get("total_attachments", 0) > 0:
                    self.add_finding(Finding(
                        resource_id=sg_id,
                        resource_type="SecurityGroup",
                        resource_name=sg_name,
                        rule_id="SG_ADV_003",
                        rule_name="Egress completamente aperto",
                        description=f"Security Group '{sg_name}' permette tutto il traffico egress (0.0.0.0/0)",
                        severity=Severity.LOW,
                        region=self.region,
                        recommendation="Implementare regole egress specifiche per migliorare security posture",
                        remediation="Definire regole egress specifiche per i servizi necessari",
                        compliance_frameworks=["Defense in Depth"],
                        metadata={
                            "attached_resources": usage.get("total_attachments", 0),
                            "egress_type": "all_traffic"
                        },
                        timestamp=datetime.now(timezone.utc)
                    ))
    
    def _analyze_sg_reference(self, sg: Dict, rule: Dict, sg_ref: Dict, usage_map: Dict):
        """Analizza riferimenti ad altri Security Groups"""
        # Placeholder per analisi avanzata di SG references
        pass
    
    def _check_redundant_rules(self, sg: Dict):
        """Verifica regole ridondanti"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        
        seen_rules = set()
        duplicates = []
        
        # Check ingress rules
        for rule in sg.get("IpPermissions", []):
            rule_signature = self._create_rule_signature(rule)
            if rule_signature in seen_rules:
                duplicates.append(("ingress", rule))
            seen_rules.add(rule_signature)
        
        # Check egress rules
        seen_rules.clear()
        for rule in sg.get("IpPermissionsEgress", []):
            rule_signature = self._create_rule_signature(rule)
            if rule_signature in seen_rules:
                duplicates.append(("egress", rule))
            seen_rules.add(rule_signature)
        
        if duplicates:
            self.add_finding(Finding(
                resource_id=sg_id,
                resource_type="SecurityGroup",
                resource_name=sg_name,
                rule_id="SG_ADV_004",
                rule_name="Regole duplicate",
                description=f"Security Group '{sg_name}' contiene {len(duplicates)} regole duplicate",
                severity=Severity.LOW,
                region=self.region,
                recommendation="Rimuovere regole duplicate per semplificare gestione",
                remediation="Rivedere e consolidare regole duplicate",
                compliance_frameworks=["Best Practices"],
                metadata={
                    "duplicate_count": len(duplicates),
                    "duplicate_rules": [f"{d[0]}: {self._rule_to_string(d[1])}" for d in duplicates]
                },
                timestamp=datetime.now(timezone.utc)
            ))
    
    def _check_overlapping_rules(self, sg: Dict):
        """Verifica regole overlapping"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        
        ingress_rules = sg.get("IpPermissions", [])
        overlaps = []
        
        for i, rule1 in enumerate(ingress_rules):
            for j, rule2 in enumerate(ingress_rules[i+1:], i+1):
                if self._rules_overlap(rule1, rule2):
                    overlaps.append((rule1, rule2))
        
        if overlaps:
            self.add_finding(Finding(
                resource_id=sg_id,
                resource_type="SecurityGroup",
                resource_name=sg_name,
                rule_id="SG_ADV_005",
                rule_name="Regole overlapping",
                description=f"Security Group '{sg_name}' ha {len(overlaps)} coppie di regole overlapping",
                severity=Severity.LOW,
                region=self.region,
                recommendation="Consolidare regole overlapping per ottimizzare performance",
                remediation="Analizzare e consolidare regole con range sovrapposti",
                compliance_frameworks=["Best Practices"],
                metadata={
                    "overlap_count": len(overlaps),
                    "overlapping_pairs": len(overlaps)
                },
                timestamp=datetime.now(timezone.utc)
            ))
    
    def _check_default_deny_policy(self, sg: Dict):
        """Verifica policy default deny"""
        # Placeholder per check di default deny policy
        pass
    
    def _analyze_optimization_opportunities(self, sg: Dict, usage_map: Dict):
        """Analizza opportunità di ottimizzazione"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        usage = usage_map.get(sg_id, {})
        
        # Check SG non utilizzati
        if usage.get("total_attachments", 0) == 0 and sg_name != "default":
            self.add_finding(Finding(
                resource_id=sg_id,
                resource_type="SecurityGroup",
                resource_name=sg_name,
                rule_id="SG_OPT_001",
                rule_name="Security Group non utilizzato",
                description=f"Security Group '{sg_name}' non è associato a nessuna risorsa",
                severity=Severity.LOW,
                region=self.region,
                recommendation="Rimuovere Security Group non utilizzati per ridurre complessità e costi",
                remediation=f"aws ec2 delete-security-group --group-id {sg_id}",
                compliance_frameworks=["Cost Optimization"],
                metadata={
                    "vpc_id": sg.get("VpcId"),
                    "rule_count": len(sg.get("IpPermissions", [])) + len(sg.get("IpPermissionsEgress", [])),
                    "cost_savings": "Minimal but improves management"
                },
                timestamp=datetime.now(timezone.utc)
            ))
            
            self.cost_savings_opportunities.append({
                "type": "unused_sg",
                "resource_id": sg_id,
                "estimated_monthly_savings": 0,  # Minimal direct cost savings
                "management_benefit": "High"
            })
        
        # Check SG con troppi attachment (può indicare design non ottimale)
        if usage.get("total_attachments", 0) > 20:
            self.optimization_recommendations.append({
                "type": "over_used_sg",
                "resource_id": sg_id,
                "resource_name": sg_name,
                "current_attachments": usage.get("total_attachments"),
                "recommendation": "Consider splitting into multiple purpose-specific Security Groups",
                "benefit": "Improved security granularity and easier management"
            })
    
    def _analyze_cost_optimization(self, sg: Dict, usage_map: Dict):
        """Analizza opportunità di ottimizzazione costi"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        usage = usage_map.get(sg_id, {})
        
        # Analizza regole che potrebbero generare costi nascosti
        ingress_rules = sg.get("IpPermissions", [])
        egress_rules = sg.get("IpPermissionsEgress", [])
        
        # Regole con range IP molto ampi potrebbero causare overhead di rete
        for rule in ingress_rules:
            for ip_range in rule.get("IpRanges", []):
                cidr = ip_range.get("CidrIp", "")
                if self._is_broad_cidr(cidr):
                    prefix_length = int(cidr.split("/")[1]) if "/" in cidr else 32
                    if prefix_length < 8:  # Estremamente ampio
                        self.cost_savings_opportunities.append({
                            "type": "network_overhead",
                            "resource_id": sg_id,
                            "issue": f"Very broad CIDR {cidr} may cause network processing overhead",
                            "estimated_monthly_impact": "Low",
                            "recommendation": "Narrow down CIDR ranges to reduce network processing"
                        })
    
    def _analyze_compliance_issues(self, sg: Dict):
        """Analizza problemi di compliance"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        
        # Check per default security group usage
        if sg_name == "default":
            ingress_rules = sg.get("IpPermissions", [])
            egress_rules = sg.get("IpPermissionsEgress", [])
            
            # Default SG non dovrebbe avere regole custom per CIS compliance
            custom_ingress = [r for r in ingress_rules if not self._is_default_rule(r)]
            
            if custom_ingress:
                self.add_finding(Finding(
                    resource_id=sg_id,
                    resource_type="SecurityGroup",
                    resource_name=sg_name,
                    rule_id="SG_COMP_001",
                    rule_name="Default Security Group modificato",
                    description=f"Default Security Group ha {len(custom_ingress)} regole ingress custom",
                    severity=Severity.MEDIUM,
                    region=self.region,
                    recommendation="Non utilizzare default Security Group per risorse. Creare SG dedicati",
                    remediation="Creare Security Groups specifici e rimuovere regole custom dal default",
                    compliance_frameworks=["CIS", "AWS Well-Architected"],
                    metadata={
                        "custom_ingress_rules": len(custom_ingress),
                        "vpc_id": sg.get("VpcId")
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
    
    def _generate_consolidation_recommendations(self, security_groups: List[Dict], usage_map: Dict):
        """Genera raccomandazioni per consolidamento SG"""
        print("   📋 Generating consolidation recommendations...")
        
        # Raggruppa SG simili
        similar_groups = self._find_similar_sg_groups(security_groups)
        
        for group in similar_groups:
            if len(group) > 1:
                primary_sg = group[0]
                similar_sgs = group[1:]
                
                total_attachments = sum(
                    usage_map.get(sg["GroupId"], {}).get("total_attachments", 0) 
                    for sg in group
                )
                
                if total_attachments < 50:  # Safe to consolidate
                    self.optimization_recommendations.append({
                        "type": "consolidation_opportunity",
                        "primary_sg": {
                            "id": primary_sg["GroupId"],
                            "name": primary_sg["GroupName"]
                        },
                        "consolidation_candidates": [
                            {"id": sg["GroupId"], "name": sg["GroupName"]} 
                            for sg in similar_sgs
                        ],
                        "total_attachments": total_attachments,
                        "estimated_management_improvement": "High",
                        "recommendation": f"Consider consolidating {len(similar_sgs)} similar Security Groups"
                    })
    
    def _find_similar_sg_groups(self, security_groups: List[Dict]) -> List[List[Dict]]:
        """Trova gruppi di Security Groups simili"""
        groups = []
        processed = set()
        
        for sg1 in security_groups:
            if sg1["GroupId"] in processed:
                continue
                
            similar_group = [sg1]
            processed.add(sg1["GroupId"])
            
            for sg2 in security_groups:
                if sg2["GroupId"] in processed:
                    continue
                    
                if self._are_sgs_similar(sg1, sg2):
                    similar_group.append(sg2)
                    processed.add(sg2["GroupId"])
            
            if len(similar_group) > 1:
                groups.append(similar_group)
        
        return groups
    
    def _are_sgs_similar(self, sg1: Dict, sg2: Dict) -> bool:
        """Verifica se due Security Groups sono simili"""
        # Stesso VPC
        if sg1.get("VpcId") != sg2.get("VpcId"):
            return False
        
        # Regole simili (80% overlap)
        rules1 = self._get_all_rule_signatures(sg1)
        rules2 = self._get_all_rule_signatures(sg2)
        
        if not rules1 or not rules2:
            return False
        
        overlap = len(rules1.intersection(rules2))
        min_rules = min(len(rules1), len(rules2))
        
        return (overlap / min_rules) >= 0.8
    
    def _get_all_rule_signatures(self, sg: Dict) -> Set[str]:
        """Ottieni signature di tutte le regole di un SG"""
        signatures = set()
        
        for rule in sg.get("IpPermissions", []):
            signatures.add(self._create_rule_signature(rule))
        
        for rule in sg.get("IpPermissionsEgress", []):
            signatures.add(self._create_rule_signature(rule))
        
        return signatures
    
    def _create_rule_signature(self, rule: Dict) -> str:
        """Crea signature univoca per una regola"""
        protocol = rule.get("IpProtocol", "")
        from_port = rule.get("FromPort", "")
        to_port = rule.get("ToPort", "")
        
        ip_ranges = sorted([ip.get("CidrIp", "") for ip in rule.get("IpRanges", [])])
        sg_refs = sorted([sg.get("GroupId", "") for sg in rule.get("UserIdGroupPairs", [])])
        
        return f"{protocol}:{from_port}:{to_port}:{','.join(ip_ranges)}:{','.join(sg_refs)}"
    
    def _rules_overlap(self, rule1: Dict, rule2: Dict) -> bool:
        """Verifica se due regole si sovrappongono"""
        # Protocollo diverso = no overlap
        if rule1.get("IpProtocol") != rule2.get("IpProtocol"):
            return False
        
        # Port ranges overlap?
        range1 = (rule1.get("FromPort", 0), rule1.get("ToPort", 65535))
        range2 = (rule2.get("FromPort", 0), rule2.get("ToPort", 65535))
        
        if not (range1[0] <= range2[1] and range2[0] <= range1[1]):
            return False
        
        # IP ranges overlap?
        ips1 = set(ip.get("CidrIp", "") for ip in rule1.get("IpRanges", []))
        ips2 = set(ip.get("CidrIp", "") for ip in rule2.get("IpRanges", []))
        
        return bool(ips1.intersection(ips2))
    
    def _rule_to_string(self, rule: Dict) -> str:
        """Converte regola in stringa leggibile"""
        protocol = rule.get("IpProtocol", "")
        from_port = rule.get("FromPort", "")
        to_port = rule.get("ToPort", "")
        
        port_str = f"{from_port}" if from_port == to_port else f"{from_port}-{to_port}"
        
        sources = []
        for ip in rule.get("IpRanges", []):
            sources.append(ip.get("CidrIp", ""))
        for sg in rule.get("UserIdGroupPairs", []):
            sources.append(sg.get("GroupId", ""))
        
        return f"{protocol}:{port_str} from {','.join(sources)}"
    
    def _is_default_rule(self, rule: Dict) -> bool:
        """Verifica se è una regola default del Security Group"""
        # Default rules tipicamente permettono tutto il traffico da se stesso
        sg_refs = rule.get("UserIdGroupPairs", [])
        return len(sg_refs) == 1 and not rule.get("IpRanges", [])
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Ritorna summary delle ottimizzazioni raccomandate"""
        return {
            "total_recommendations": len(self.optimization_recommendations),
            "cost_savings_opportunities": len(self.cost_savings_opportunities),
            "security_violations": len(self.security_violations),
            "recommendations": self.optimization_recommendations,
            "cost_savings": self.cost_savings_opportunities,
            "violations": self.security_violations
        }
    
    def generate_cleanup_script(self, sg_usage_map: Dict) -> str:
        """Genera script per cleanup automatico"""
        script_lines = [
            "#!/bin/bash",
            "# AWS Security Groups Cleanup Script",
            "# Generated by AWS Security Auditor",
            "",
            "set -e",
            "echo 'Starting Security Groups cleanup...'",
            ""
        ]
        
        # Unused Security Groups
        for recommendation in self.optimization_recommendations:
            if recommendation.get("type") == "unused_sg":
                sg_id = recommendation["resource_id"]
                script_lines.extend([
                    f"# Remove unused Security Group {sg_id}",
                    f"echo 'Removing unused SG {sg_id}...'",
                    f"aws ec2 delete-security-group --group-id {sg_id}",
                    ""
                ])
        
        # Consolidation opportunities
        for recommendation in self.optimization_recommendations:
            if recommendation.get("type") == "consolidation_opportunity":
                script_lines.extend([
                    "# Consolidation opportunity found",
                    f"# Primary SG: {recommendation['primary_sg']['id']}",
                    f"# Consider consolidating: {[sg['id'] for sg in recommendation['consolidation_candidates']]}",
                    "# Manual review required for consolidation",
                    ""
                ])
        
        script_lines.append("echo 'Cleanup completed!'")
        
        return "\n".join(script_lines)
# audit/vpc_auditor.py
"""
VPC Auditor integrato nel sistema AWS Auditor esistente
Analizza VPC, subnet, routing, NAT Gateway e ottimizzazioni di rete
"""

from audit.base_auditor import BaseAuditor, Finding
from config.audit_rules import Severity
from datetime import datetime, timezone
from typing import Dict, List, Any, Set, Tuple
import json

class VPCAuditor(BaseAuditor):
    """Auditor specializzato per VPC e infrastruttura di rete"""
    
    def __init__(self, region: str = "us-east-1"):
        super().__init__(region)
        self.network_topology = {}
        self.cost_optimizations = []
        
    def audit(self, data: Dict[str, Any]) -> List[Finding]:
        """Analizza infrastruttura VPC completa"""
        self.clear_findings()
        self.network_topology = {}
        self.cost_optimizations = []
        
        # Estrai dati VPC
        vpcs = data.get("vpc_raw", {}).get("Vpcs", [])
        subnets = data.get("subnet_raw", {}).get("Subnets", [])
        route_tables = data.get("route_table_raw", {}).get("RouteTables", [])
        internet_gateways = data.get("igw_raw", {}).get("InternetGateways", [])
        nat_gateways = data.get("nat_gateways_raw", {}).get("NatGateways", [])
        vpc_endpoints = data.get("vpc_endpoints_raw", {}).get("VpcEndpoints", [])
        security_groups = data.get("sg_raw", {}).get("SecurityGroups", [])
        
        print(f"   🌐 Analyzing {len(vpcs)} VPCs in {self.region}...")
        
        # Costruisci topologia di rete
        self._build_network_topology(vpcs, subnets, route_tables, internet_gateways, nat_gateways)
        
        # Analisi VPC
        for vpc in vpcs:
            self._audit_vpc_configuration(vpc, subnets, security_groups)
            self._audit_vpc_security(vpc, subnets, route_tables)
            self._audit_vpc_cost_optimization(vpc, nat_gateways, vpc_endpoints)
        
        # Analisi subnet
        self._audit_subnet_utilization(subnets, data)
        self._audit_subnet_security(subnets, route_tables, internet_gateways)
        
        # Analisi routing
        self._audit_routing_configuration(route_tables, vpcs)
        
        # Analisi NAT Gateway
        self._audit_nat_gateway_optimization(nat_gateways, vpc_endpoints)
        
        # Analisi VPC Endpoints
        self._audit_vpc_endpoints_opportunities(vpc_endpoints, nat_gateways, data)
        
        return self.findings
    
    def _build_network_topology(self, vpcs, subnets, route_tables, igws, nat_gws):
        """Costruisce mappa della topologia di rete"""
        for vpc in vpcs:
            vpc_id = vpc["VpcId"]
            self.network_topology[vpc_id] = {
                "vpc": vpc,
                "subnets": [s for s in subnets if s.get("VpcId") == vpc_id],
                "route_tables": [rt for rt in route_tables if rt.get("VpcId") == vpc_id],
                "internet_gateways": [],
                "nat_gateways": [ng for ng in nat_gws if ng.get("VpcId") == vpc_id],
                "public_subnets": [],
                "private_subnets": [],
                "isolated_subnets": []
            }
            
            # Associa Internet Gateway
            for igw in igws:
                for attachment in igw.get("Attachments", []):
                    if attachment.get("VpcId") == vpc_id:
                        self.network_topology[vpc_id]["internet_gateways"].append(igw)
            
            # Classifica subnet per tipo
            self._classify_subnets(vpc_id)
    
    def _classify_subnets(self, vpc_id: str):
        """Classifica subnet come pubbliche, private o isolate"""
        vpc_topo = self.network_topology[vpc_id]
        
        for subnet in vpc_topo["subnets"]:
            subnet_id = subnet["SubnetId"]
            subnet_type = self._determine_subnet_type(subnet_id, vpc_topo["route_tables"])
            
            if subnet_type == "public":
                vpc_topo["public_subnets"].append(subnet)
            elif subnet_type == "private":
                vpc_topo["private_subnets"].append(subnet)
            else:
                vpc_topo["isolated_subnets"].append(subnet)
    
    def _determine_subnet_type(self, subnet_id: str, route_tables: List[Dict]) -> str:
        """Determina il tipo di subnet basandosi sulle route table"""
        # Trova route table associata alla subnet
        associated_rt = None
        
        for rt in route_tables:
            for assoc in rt.get("Associations", []):
                if assoc.get("SubnetId") == subnet_id:
                    associated_rt = rt
                    break
            if associated_rt:
                break
        
        # Se non trovata associazione specifica, usa main route table
        if not associated_rt:
            for rt in route_tables:
                for assoc in rt.get("Associations", []):
                    if assoc.get("Main"):
                        associated_rt = rt
                        break
        
        if not associated_rt:
            return "isolated"
        
        # Analizza routes per determinare tipo
        has_igw_route = False
        has_nat_route = False
        
        for route in associated_rt.get("Routes", []):
            gateway_id = route.get("GatewayId", "")
            
            if gateway_id.startswith("igw-"):
                has_igw_route = True
            elif gateway_id.startswith("nat-"):
                has_nat_route = True
        
        if has_igw_route:
            return "public"
        elif has_nat_route:
            return "private"
        else:
            return "isolated"
    
    def _audit_vpc_configuration(self, vpc: Dict, subnets: List[Dict], security_groups: List[Dict]):
        """Audita configurazione base VPC"""
        vpc_id = vpc["VpcId"]
        is_default = vpc.get("IsDefault", False)
        
        # Check utilizzo VPC default
        if is_default:
            vpc_subnets = [s for s in subnets if s.get("VpcId") == vpc_id]
            vpc_sgs = [sg for sg in security_groups if sg.get("VpcId") == vpc_id]
            
            # Se VPC default ha risorse, è un problema
            if len(vpc_subnets) > 0 or len(vpc_sgs) > 1:  # >1 perché c'è sempre default SG
                self.add_finding(Finding(
                    resource_id=vpc_id,
                    resource_type="VPC",
                    resource_name="Default VPC",
                    rule_id="VPC001",
                    rule_name="Utilizzo VPC Default",
                    description=f"VPC default contiene {len(vpc_subnets)} subnet e {len(vpc_sgs)} security groups",
                    severity=Severity.MEDIUM,
                    region=self.region,
                    recommendation="Migrare risorse da VPC default a VPC dedicata per migliore sicurezza",
                    remediation="Creare VPC dedicata e migrare risorse",
                    compliance_frameworks=["CIS", "Well-Architected"],
                    metadata={
                        "is_default": True,
                        "subnet_count": len(vpc_subnets),
                        "sg_count": len(vpc_sgs),
                        "cidr_block": vpc.get("CidrBlock")
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
        
        # Check CIDR block size appropriato
        cidr_block = vpc.get("CidrBlock", "")
        if "/" in cidr_block:
            prefix_length = int(cidr_block.split("/")[1])
            max_ips = 2 ** (32 - prefix_length)
            
            vpc_subnets = [s for s in subnets if s.get("VpcId") == vpc_id]
            
            # VPC troppo grande per poche subnet
            if max_ips > 65536 and len(vpc_subnets) < 5:
                self.add_finding(Finding(
                    resource_id=vpc_id,
                    resource_type="VPC",
                    resource_name=f"VPC {vpc_id}",
                    rule_id="VPC002",
                    rule_name="CIDR Block Sovradimensionato",
                    description=f"VPC con CIDR /{prefix_length} ({max_ips:,} IPs) ha solo {len(vpc_subnets)} subnet",
                    severity=Severity.LOW,
                    region=self.region,
                    recommendation="Considerare CIDR più piccolo per ottimizzare utilizzo IP",
                    remediation="Pianificare migrazione a VPC con CIDR appropriato",
                    compliance_frameworks=["Well-Architected"],
                    metadata={
                        "cidr_block": cidr_block,
                        "max_ips": max_ips,
                        "subnet_count": len(vpc_subnets),
                        "utilization_ratio": len(vpc_subnets) / (max_ips / 1000)
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
    
    def _audit_vpc_security(self, vpc: Dict, subnets: List[Dict], route_tables: List[Dict]):
        """Audita aspetti di sicurezza VPC"""
        vpc_id = vpc["VpcId"]
        vpc_topo = self.network_topology[vpc_id]
        
        # Check flow logs abilitati
        # Nota: richiederebbe chiamata describe-flow-logs per verifica completa
        # Per ora assumiamo non ci siano flow logs se non presenti nei dati
        
        # Check distribuzione Multi-AZ
        if len(vpc_topo["subnets"]) > 0:
            availability_zones = set(s.get("AvailabilityZone") for s in vpc_topo["subnets"])
            
            if len(availability_zones) == 1:
                self.add_finding(Finding(
                    resource_id=vpc_id,
                    resource_type="VPC",
                    resource_name=f"VPC {vpc_id}",
                    rule_id="VPC003",
                    rule_name="Single AZ Deployment",
                    description=f"VPC ha subnet solo in {list(availability_zones)[0]}",
                    severity=Severity.HIGH,
                    region=self.region,
                    recommendation="Distribuire subnet su multiple AZ per alta disponibilità",
                    remediation="Creare subnet in almeno 2 AZ diverse",
                    compliance_frameworks=["Well-Architected", "Reliability"],
                    metadata={
                        "availability_zones": list(availability_zones),
                        "subnet_count": len(vpc_topo["subnets"])
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
        
        # Check isolamento rete appropriato
        public_subnets = len(vpc_topo["public_subnets"])
        private_subnets = len(vpc_topo["private_subnets"])
        
        if public_subnets > 0 and private_subnets == 0:
            self.add_finding(Finding(
                resource_id=vpc_id,
                resource_type="VPC",
                resource_name=f"VPC {vpc_id}",
                rule_id="VPC004",
                rule_name="Mancanza Subnet Private",
                description=f"VPC ha {public_subnets} subnet pubbliche ma 0 private",
                severity=Severity.MEDIUM,
                region=self.region,
                recommendation="Implementare subnet private per backend services",
                remediation="Creare subnet private con NAT Gateway per accesso Internet",
                compliance_frameworks=["CIS", "Security"],
                metadata={
                    "public_subnets": public_subnets,
                    "private_subnets": private_subnets
                },
                timestamp=datetime.now(timezone.utc)
            ))
    
    def _audit_vpc_cost_optimization(self, vpc: Dict, nat_gateways: List[Dict], vpc_endpoints: List[Dict]):
        """Audita opportunità di ottimizzazione costi VPC"""
        vpc_id = vpc["VpcId"]
        
        # NAT Gateway nella stessa AZ (ridondanza costosa)
        vpc_nat_gws = [ng for ng in nat_gateways if ng.get("VpcId") == vpc_id and ng.get("State") == "available"]
        
        if len(vpc_nat_gws) > 1:
            # Raggruppa per AZ
            nat_by_az = {}
            for ng in vpc_nat_gws:
                az = ng.get("SubnetId", "")  # Subnet implica AZ
                if az not in nat_by_az:
                    nat_by_az[az] = []
                nat_by_az[az].append(ng)
            
            # Costo mensile stimato per NAT Gateway aggiuntivi
            extra_nat_cost = (len(vpc_nat_gws) - 1) * 45.36  # $45.36/mese per NAT GW
            
            if len(vpc_nat_gws) > 2:  # Più di 2 è spesso eccessivo
                self.add_finding(Finding(
                    resource_id=vpc_id,
                    resource_type="VPC",
                    resource_name=f"VPC {vpc_id}",
                    rule_id="VPC005",
                    rule_name="NAT Gateway Ridondanti",
                    description=f"VPC ha {len(vpc_nat_gws)} NAT Gateway (costo extra: ${extra_nat_cost:.2f}/mese)",
                    severity=Severity.MEDIUM,
                    region=self.region,
                    recommendation="Valutare se tutti i NAT Gateway sono necessari",
                    remediation="Considerare consolidamento NAT Gateway o NAT Instance per dev/test",
                    compliance_frameworks=["Cost Optimization"],
                    metadata={
                        "nat_gateway_count": len(vpc_nat_gws),
                        "estimated_monthly_cost": len(vpc_nat_gws) * 45.36,
                        "potential_monthly_savings": extra_nat_cost,
                        "nat_gateway_ids": [ng.get("NatGatewayId") for ng in vpc_nat_gws]
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
                
                # Aggiungi a ottimizzazioni costi
                self.cost_optimizations.append({
                    "type": "nat_gateway_consolidation",
                    "vpc_id": vpc_id,
                    "current_cost": len(vpc_nat_gws) * 45.36,
                    "optimized_cost": 45.36,  # Almeno uno necessario
                    "monthly_savings": extra_nat_cost,
                    "annual_savings": extra_nat_cost * 12
                })
    
    def _audit_subnet_utilization(self, subnets: List[Dict], data: Dict[str, Any]):
        """Audita utilizzo delle subnet"""
        # Conta istanze per subnet
        instances_by_subnet = {}
        ec2_data = data.get("ec2_raw", {})
        
        for reservation in ec2_data.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                subnet_id = instance.get("SubnetId")
                if subnet_id:
                    if subnet_id not in instances_by_subnet:
                        instances_by_subnet[subnet_id] = []
                    instances_by_subnet[subnet_id].append(instance)
        
        for subnet in subnets:
            subnet_id = subnet["SubnetId"]
            available_ips = subnet.get("AvailableIpAddressCount", 0)
            total_ips = self._calculate_subnet_total_ips(subnet.get("CidrBlock", ""))
            utilization = (total_ips - available_ips) / total_ips if total_ips > 0 else 0
            
            instances_count = len(instances_by_subnet.get(subnet_id, []))
            
            # Subnet sottoutilizzate (molti IP, poche risorse)
            if total_ips > 1000 and instances_count < 5 and utilization < 0.1:
                self.add_finding(Finding(
                    resource_id=subnet_id,
                    resource_type="Subnet",
                    resource_name=f"Subnet {subnet_id}",
                    rule_id="SUBNET001",
                    rule_name="Subnet Sottoutilizzata",
                    description=f"Subnet con {total_ips} IP ha solo {instances_count} istanze (utilizzo: {utilization:.1%})",
                    severity=Severity.LOW,
                    region=self.region,
                    recommendation="Considerare subnet più piccola o consolidamento",
                    remediation="Pianificare migrazione a subnet con CIDR appropriato",
                    compliance_frameworks=["Cost Optimization"],
                    metadata={
                        "total_ips": total_ips,
                        "available_ips": available_ips,
                        "utilization_percent": utilization * 100,
                        "instances_count": instances_count,
                        "cidr_block": subnet.get("CidrBlock"),
                        "availability_zone": subnet.get("AvailabilityZone")
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
            
            # Subnet quasi piene (>90% utilizzo)
            elif utilization > 0.9:
                self.add_finding(Finding(
                    resource_id=subnet_id,
                    resource_type="Subnet",
                    resource_name=f"Subnet {subnet_id}",
                    rule_id="SUBNET002",
                    rule_name="Subnet Quasi Piena",
                    description=f"Subnet ha utilizzo {utilization:.1%} ({available_ips} IP disponibili)",
                    severity=Severity.MEDIUM,
                    region=self.region,
                    recommendation="Pianificare espansione subnet o migrazione",
                    remediation="Creare subnet aggiuntiva o espandere CIDR se possibile",
                    compliance_frameworks=["Operational Excellence"],
                    metadata={
                        "total_ips": total_ips,
                        "available_ips": available_ips,
                        "utilization_percent": utilization * 100,
                        "instances_count": instances_count
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
    
    def _audit_subnet_security(self, subnets: List[Dict], route_tables: List[Dict], igws: List[Dict]):
        """Audita sicurezza delle subnet"""
        for subnet in subnets:
            subnet_id = subnet["SubnetId"]
            subnet_type = self._determine_subnet_type(subnet_id, route_tables)
            
            # Check subnet pubbliche con auto-assign IP pubblico
            if subnet_type == "public" and subnet.get("MapPublicIpOnLaunch", False):
                self.add_finding(Finding(
                    resource_id=subnet_id,
                    resource_type="Subnet",
                    resource_name=f"Subnet {subnet_id}",
                    rule_id="SUBNET003",
                    rule_name="Auto-assign IP Pubblico Abilitato",
                    description="Subnet pubblica assegna automaticamente IP pubblici",
                    severity=Severity.MEDIUM,
                    region=self.region,
                    recommendation="Disabilitare auto-assign e usare Elastic IP quando necessario",
                    remediation=f"aws ec2 modify-subnet-attribute --subnet-id {subnet_id} --no-map-public-ip-on-launch",
                    compliance_frameworks=["CIS", "Security"],
                    metadata={
                        "subnet_type": subnet_type,
                        "availability_zone": subnet.get("AvailabilityZone"),
                        "cidr_block": subnet.get("CidrBlock")
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
    
    def _audit_routing_configuration(self, route_tables: List[Dict], vpcs: List[Dict]):
        """Audita configurazione routing"""
        for rt in route_tables:
            rt_id = rt["RouteTableId"]
            
            # Check route table con molte route (complessità)
            routes = rt.get("Routes", [])
            if len(routes) > 20:
                self.add_finding(Finding(
                    resource_id=rt_id,
                    resource_type="RouteTable",
                    resource_name=f"Route Table {rt_id}",
                    rule_id="ROUTE001",
                    rule_name="Route Table Complessa",
                    description=f"Route table ha {len(routes)} route (>20)",
                    severity=Severity.LOW,
                    region=self.region,
                    recommendation="Semplificare routing o dividere in multiple route table",
                    remediation="Rivedere necessità di tutte le route",
                    compliance_frameworks=["Operational Excellence"],
                    metadata={
                        "routes_count": len(routes),
                        "vpc_id": rt.get("VpcId"),
                        "associations_count": len(rt.get("Associations", []))
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
            
            # Check route 0.0.0.0/0 multiple (potenziale problema)
            default_routes = [r for r in routes if r.get("DestinationCidrBlock") == "0.0.0.0/0"]
            if len(default_routes) > 1:
                self.add_finding(Finding(
                    resource_id=rt_id,
                    resource_type="RouteTable",
                    resource_name=f"Route Table {rt_id}",
                    rule_id="ROUTE002",
                    rule_name="Route Default Multiple",
                    description=f"Route table ha {len(default_routes)} route default",
                    severity=Severity.MEDIUM,
                    region=self.region,
                    recommendation="Verificare configurazione routing default",
                    remediation="Controllare conflitti nelle route 0.0.0.0/0",
                    compliance_frameworks=["Reliability"],
                    metadata={
                        "default_routes_count": len(default_routes),
                        "default_routes": [r.get("GatewayId") for r in default_routes]
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
    
    def _audit_nat_gateway_optimization(self, nat_gateways: List[Dict], vpc_endpoints: List[Dict]):
        """Audita ottimizzazione NAT Gateway"""
        for nat_gw in nat_gateways:
            if nat_gw.get("State") != "available":
                continue
            
            nat_gw_id = nat_gw["NatGatewayId"]
            vpc_id = nat_gw.get("VpcId")
            
            # Check se VPC Endpoint S3 potrebbe ridurre traffico NAT
            s3_endpoints = [ep for ep in vpc_endpoints 
                           if ep.get("VpcId") == vpc_id and "s3" in ep.get("ServiceName", "")]
            
            if len(s3_endpoints) == 0:
                # Nessun S3 VPC Endpoint - potenziale risparmio
                estimated_savings = 10  # Stima $10/mese in data transfer
                
                self.add_finding(Finding(
                    resource_id=nat_gw_id,
                    resource_type="NATGateway",
                    resource_name=f"NAT Gateway {nat_gw_id}",
                    rule_id="NAT001",
                    rule_name="Mancanza S3 VPC Endpoint",
                    description="NAT Gateway potrebbe essere alleggerito con S3 VPC Endpoint",
                    severity=Severity.LOW,
                    region=self.region,
                    recommendation="Creare S3 VPC Endpoint per ridurre traffico NAT Gateway",
                    remediation=f"aws ec2 create-vpc-endpoint --vpc-id {vpc_id} --service-name com.amazonaws.{self.region}.s3",
                    compliance_frameworks=["Cost Optimization"],
                    metadata={
                        "vpc_id": vpc_id,
                        "estimated_monthly_savings": estimated_savings,
                        "subnet_id": nat_gw.get("SubnetId")
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
    
    def _audit_vpc_endpoints_opportunities(self, vpc_endpoints: List[Dict], nat_gateways: List[Dict], data: Dict[str, Any]):
        """Audita opportunità VPC Endpoints"""
        # Raggruppa per VPC
        endpoints_by_vpc = {}
        for ep in vpc_endpoints:
            vpc_id = ep.get("VpcId")
            if vpc_id not in endpoints_by_vpc:
                endpoints_by_vpc[vpc_id] = []
            endpoints_by_vpc[vpc_id].append(ep)
        
        # Per ogni VPC con NAT Gateway, verifica endpoints mancanti
        for nat_gw in nat_gateways:
            if nat_gw.get("State") != "available":
                continue
                
            vpc_id = nat_gw.get("VpcId")
            existing_endpoints = endpoints_by_vpc.get(vpc_id, [])
            
            # Servizi comuni che beneficiano di VPC Endpoints
            recommended_services = {
                "s3": f"com.amazonaws.{self.region}.s3",
                "dynamodb": f"com.amazonaws.{self.region}.dynamodb",
                "ec2": f"com.amazonaws.{self.region}.ec2",
                "ssm": f"com.amazonaws.{self.region}.ssm"
            }
            
            missing_services = []
            for service_name, service_endpoint in recommended_services.items():
                has_endpoint = any(service_endpoint in ep.get("ServiceName", "") 
                                 for ep in existing_endpoints)
                if not has_endpoint:
                    missing_services.append(service_name)
            
            if missing_services:
                estimated_savings = len(missing_services) * 5  # $5/mese per servizio
                
                self.add_finding(Finding(
                    resource_id=vpc_id,
                    resource_type="VPC",
                    resource_name=f"VPC {vpc_id}",
                    rule_id="ENDPOINT001",
                    rule_name="VPC Endpoints Mancanti",
                    description=f"VPC potrebbe beneficiare di {len(missing_services)} VPC Endpoints",
                    severity=Severity.LOW,
                    region=self.region,
                    recommendation=f"Creare VPC Endpoints per: {', '.join(missing_services)}",
                    remediation="Implementare VPC Endpoints per ridurre costi data transfer",
                    compliance_frameworks=["Cost Optimization"],
                    metadata={
                        "missing_services": missing_services,
                        "existing_endpoints": len(existing_endpoints),
                        "estimated_monthly_savings": estimated_savings,
                        "nat_gateway_id": nat_gw["NatGatewayId"]
                    },
                    timestamp=datetime.now(timezone.utc)
                ))
    
    def _calculate_subnet_total_ips(self, cidr_block: str) -> int:
        """Calcola numero totale IP in subnet"""
        if not cidr_block or "/" not in cidr_block:
            return 0
        
        try:
            prefix_length = int(cidr_block.split("/")[1])
            return 2 ** (32 - prefix_length) - 5  # AWS riserva 5 IP per subnet
        except:
            return 0
    
    def get_network_topology(self) -> Dict[str, Any]:
        """Ritorna topologia di rete costruita"""
        return self.network_topology
    
    def get_cost_optimizations(self) -> List[Dict[str, Any]]:
        """Ritorna ottimizzazioni di costo identificate"""
        return self.cost_optimizations
    
    def generate_vpc_summary_report(self) -> Dict[str, Any]:
        """Genera report di summary VPC"""
        total_vpcs = len(self.network_topology)
        total_findings = len(self.findings)
        
        findings_by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in self.findings:
            severity = finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity)
            findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1
        
        total_cost_savings = sum(opt.get("monthly_savings", 0) for opt in self.cost_optimizations)
        
        return {
            "total_vpcs_analyzed": total_vpcs,
            "total_findings": total_findings,
            "findings_by_severity": findings_by_severity,
            "total_monthly_cost_savings": total_cost_savings,
            "total_annual_cost_savings": total_cost_savings * 12,
            "network_topology": self.network_topology,
            "cost_optimizations": self.cost_optimizations,
                            "top_recommendations": [
                f.rule_name for f in sorted(self.findings, 
                key=lambda x: ["critical", "high", "medium", "low"].index(x.severity.value 
                if hasattr(x.severity, 'value') else str(x.severity)))[:5]
            ]
        }
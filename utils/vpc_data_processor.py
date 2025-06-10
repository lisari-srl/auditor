# utils/vpc_data_processor.py
"""
Estensione del DataProcessor per elaborare dati VPC
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

def process_vpc_extended_data(data_dir: str = "data") -> bool:
    """Elabora dati VPC estesi per audit"""
    data_path = Path(data_dir)
    
    # Carica dati VPC grezzi
    vpc_files = {
        "vpc_raw.json": "Vpcs",
        "subnet_raw.json": "Subnets", 
        "route_table_raw.json": "RouteTables",
        "igw_raw.json": "InternetGateways",
        "nat_gateways_raw.json": "NatGateways",
        "vpc_endpoints_raw.json": "VpcEndpoints"
    }
    
    vpc_data = {}
    for filename, key in vpc_files.items():
        filepath = data_path / filename
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    vpc_data[key.lower()] = data.get(key, [])
            except Exception as e:
                print(f"   ⚠️  Error loading {filename}: {e}")
                vpc_data[key.lower()] = []
    
    # Elabora network topology
    network_topology = build_network_topology(vpc_data)
    
    # Genera audit data VPC
    vpc_audit_data = {
        "metadata": {
            "processed_at": datetime.now().isoformat(),
            "total_vpcs": len(vpc_data.get("vpcs", [])),
            "total_subnets": len(vpc_data.get("subnets", [])),
            "total_nat_gateways": len(vpc_data.get("natgateways", []))
        },
        "network_topology": network_topology,
        "vpc_analysis": analyze_vpc_configurations(vpc_data),
        "subnet_analysis": analyze_subnet_utilization(vpc_data),
        "cost_analysis": analyze_vpc_costs(vpc_data)
    }
    
    # Salva risultati
    try:
        output_file = data_path / "vpc_audit.json"
        with open(output_file, 'w') as f:
            json.dump(vpc_audit_data, f, indent=2, default=str)
        print(f"   ✅ VPC audit data saved: {output_file}")
        return True
    except Exception as e:
        print(f"   ❌ Error saving VPC audit data: {e}")
        return False

def build_network_topology(vpc_data: dict) -> dict:
    """Costruisce topologia di rete da dati VPC"""
    topology = {}
    
    vpcs = vpc_data.get("vpcs", [])
    subnets = vpc_data.get("subnets", [])
    route_tables = vpc_data.get("routetables", [])
    igws = vpc_data.get("internetgateways", [])
    nat_gws = vpc_data.get("natgateways", [])
    
    for vpc in vpcs:
        vpc_id = vpc["VpcId"]
        
        # Subnets per VPC
        vpc_subnets = [s for s in subnets if s.get("VpcId") == vpc_id]
        
        # Route tables per VPC
        vpc_route_tables = [rt for rt in route_tables if rt.get("VpcId") == vpc_id]
        
        # Internet Gateways per VPC
        vpc_igws = []
        for igw in igws:
            for attachment in igw.get("Attachments", []):
                if attachment.get("VpcId") == vpc_id:
                    vpc_igws.append(igw)
        
        # NAT Gateways per VPC
        vpc_nat_gws = [ng for ng in nat_gws if ng.get("VpcId") == vpc_id]
        
        # Classifica subnet
        public_subnets = []
        private_subnets = []
        isolated_subnets = []
        
        for subnet in vpc_subnets:
            subnet_type = classify_subnet_type(subnet, vpc_route_tables)
            if subnet_type == "public":
                public_subnets.append(subnet)
            elif subnet_type == "private":
                private_subnets.append(subnet)
            else:
                isolated_subnets.append(subnet)
        
        topology[vpc_id] = {
            "vpc_info": vpc,
            "total_subnets": len(vpc_subnets),
            "public_subnets": public_subnets,
            "private_subnets": private_subnets,
            "isolated_subnets": isolated_subnets,
            "internet_gateways": vpc_igws,
            "nat_gateways": vpc_nat_gws,
            "route_tables": vpc_route_tables,
            "availability_zones": list(set(s.get("AvailabilityZone") for s in vpc_subnets)),
            "cidr_utilization": calculate_cidr_utilization(vpc, vpc_subnets)
        }
    
    return topology

def classify_subnet_type(subnet: dict, route_tables: list) -> str:
    """Classifica subnet come public, private o isolated"""
    subnet_id = subnet["SubnetId"]
    
    # Trova route table associata
    associated_rt = None
    for rt in route_tables:
        for assoc in rt.get("Associations", []):
            if assoc.get("SubnetId") == subnet_id:
                associated_rt = rt
                break
        if associated_rt:
            break
    
    # Se non trovata, usa main route table
    if not associated_rt:
        for rt in route_tables:
            for assoc in rt.get("Associations", []):
                if assoc.get("Main"):
                    associated_rt = rt
                    break
    
    if not associated_rt:
        return "isolated"
    
    # Analizza routes
    for route in associated_rt.get("Routes", []):
        gateway_id = route.get("GatewayId", "")
        if gateway_id.startswith("igw-"):
            return "public"
        elif gateway_id.startswith("nat-"):
            return "private"
    
    return "isolated"

def analyze_vpc_configurations(vpc_data: dict) -> dict:
    """Analizza configurazioni VPC"""
    vpcs = vpc_data.get("vpcs", [])
    analysis = {
        "default_vpcs": [],
        "oversized_vpcs": [],
        "single_az_vpcs": [],
        "recommendations": []
    }
    
    for vpc in vpcs:
        vpc_id = vpc["VpcId"]
        
        # Check VPC default
        if vpc.get("IsDefault"):
            analysis["default_vpcs"].append({
                "vpc_id": vpc_id,
                "cidr_block": vpc.get("CidrBlock"),
                "recommendation": "Migrate from default VPC to custom VPC"
            })
        
        # Check CIDR oversized
        cidr_block = vpc.get("CidrBlock", "")
        if "/" in cidr_block:
            prefix_length = int(cidr_block.split("/")[1])
            if prefix_length < 20:  # Larger than /20
                analysis["oversized_vpcs"].append({
                    "vpc_id": vpc_id,
                    "cidr_block": cidr_block,
                    "max_ips": 2 ** (32 - prefix_length),
                    "recommendation": "Consider smaller CIDR for better IP management"
                })
    
    return analysis

def analyze_subnet_utilization(vpc_data: dict) -> dict:
    """Analizza utilizzo subnet"""
    subnets = vpc_data.get("subnets", [])
    analysis = {
        "underutilized_subnets": [],
        "nearly_full_subnets": [],
        "recommendations": []
    }
    
    for subnet in subnets:
        available_ips = subnet.get("AvailableIpAddressCount", 0)
        cidr_block = subnet.get("CidrBlock", "")
        
        if "/" in cidr_block:
            prefix_length = int(cidr_block.split("/")[1])
            total_ips = 2 ** (32 - prefix_length) - 5  # AWS reserves 5 IPs
            
            if total_ips > 0:
                utilization = (total_ips - available_ips) / total_ips
                
                # Underutilized (< 10% used, > 100 total IPs)
                if utilization < 0.1 and total_ips > 100:
                    analysis["underutilized_subnets"].append({
                        "subnet_id": subnet["SubnetId"],
                        "cidr_block": cidr_block,
                        "utilization_percent": utilization * 100,
                        "total_ips": total_ips,
                        "available_ips": available_ips
                    })
                
                # Nearly full (> 90% used)
                elif utilization > 0.9:
                    analysis["nearly_full_subnets"].append({
                        "subnet_id": subnet["SubnetId"],
                        "cidr_block": cidr_block,
                        "utilization_percent": utilization * 100,
                        "available_ips": available_ips
                    })
    
    return analysis

def analyze_vpc_costs(vpc_data: dict) -> dict:
    """Analizza costi VPC"""
    nat_gws = vpc_data.get("natgateways", [])
    vpc_endpoints = vpc_data.get("vpcendpoints", [])
    
    # NAT Gateway costs
    active_nat_gws = [ng for ng in nat_gws if ng.get("State") == "available"]
    nat_monthly_cost = len(active_nat_gws) * 45.36  # $45.36/month per NAT GW
    
    # Group by VPC
    nat_by_vpc = {}
    for ng in active_nat_gws:
        vpc_id = ng.get("VpcId")
        if vpc_id not in nat_by_vpc:
            nat_by_vpc[vpc_id] = []
        nat_by_vpc[vpc_id].append(ng)
    
    # Identify optimization opportunities
    optimization_opportunities = []
    for vpc_id, nat_list in nat_by_vpc.items():
        if len(nat_list) > 1:
            potential_savings = (len(nat_list) - 1) * 45.36
            optimization_opportunities.append({
                "vpc_id": vpc_id,
                "current_nat_count": len(nat_list),
                "potential_monthly_savings": potential_savings,
                "recommendation": "Consider consolidating NAT Gateways"
            })
    
    return {
        "total_nat_gateways": len(active_nat_gws),
        "total_monthly_nat_cost": nat_monthly_cost,
        "total_vpc_endpoints": len(vpc_endpoints),
        "optimization_opportunities": optimization_opportunities,
        "potential_monthly_savings": sum(op["potential_monthly_savings"] 
                                       for op in optimization_opportunities)
    }

def calculate_cidr_utilization(vpc: dict, subnets: list) -> dict:
    """Calcola utilizzo CIDR VPC"""
    vpc_cidr = vpc.get("CidrBlock", "")
    if "/" not in vpc_cidr:
        return {"error": "Invalid CIDR"}
    
    vpc_prefix = int(vpc_cidr.split("/")[1])
    vpc_total_ips = 2 ** (32 - vpc_prefix)
    
    # Calcola IP allocati alle subnet
    subnet_allocated_ips = 0
    for subnet in subnets:
        subnet_cidr = subnet.get("CidrBlock", "")
        if "/" in subnet_cidr:
            subnet_prefix = int(subnet_cidr.split("/")[1])
            subnet_allocated_ips += 2 ** (32 - subnet_prefix)
    
    utilization = subnet_allocated_ips / vpc_total_ips if vpc_total_ips > 0 else 0
    
    return {
        "vpc_total_ips": vpc_total_ips,
        "subnet_allocated_ips": subnet_allocated_ips,
        "utilization_percent": utilization * 100,
        "available_for_new_subnets": vpc_total_ips - subnet_allocated_ips
    }


# ==============================================================================
# ESTENSIONI PER GLI ALTRI MODULI
# ==============================================================================

def get_extended_fetcher_vpc_methods():
    """
    Restituisce i metodi da aggiungere a ExtendedAWSFetcher
    """
    async def _fetch_vpc_extended_resources(self, region: str) -> Dict[str, Any]:
        """Fetch completo risorse VPC per analisi approfondita"""
        try:
            vpc_data = {}
            
            async with self.session.client('ec2', region_name=region) as ec2:
                # VPC Flow Logs
                flow_logs_paginator = ec2.get_paginator('describe_flow_logs')
                flow_logs = []
                async for page in flow_logs_paginator.paginate():
                    flow_logs.extend(page['FlowLogs'])
                
                # DHCP Options Sets
                dhcp_options = await ec2.describe_dhcp_options()
                
                # VPC Peering Connections
                vpc_peering_paginator = ec2.get_paginator('describe_vpc_peering_connections')
                peering_connections = []
                async for page in vpc_peering_paginator.paginate():
                    peering_connections.extend(page['VpcPeeringConnections'])
                
                # Transit Gateway Attachments (if any)
                try:
                    tgw_attachments = await ec2.describe_transit_gateway_vpc_attachments()
                    vpc_data["transit_gateway_attachments"] = tgw_attachments.get('TransitGatewayVpcAttachments', [])
                except Exception:
                    vpc_data["transit_gateway_attachments"] = []
                
                # VPC Endpoint Service Configurations
                try:
                    endpoint_services = await ec2.describe_vpc_endpoint_service_configurations()
                    vpc_data["vpc_endpoint_services"] = endpoint_services.get('ServiceConfigurations', [])
                except Exception:
                    vpc_data["vpc_endpoint_services"] = []
                
                vpc_data.update({
                    "flow_logs": flow_logs,
                    "dhcp_options": dhcp_options.get('DhcpOptions', []),
                    "vpc_peering_connections": peering_connections
                })
                
                print(f"   ✅ VPC Extended: {len(flow_logs)} flow logs, {len(peering_connections)} peering connections")
                
                return {"vpc_extended_raw": vpc_data}
                
        except Exception as e:
            print(f"   ❌ VPC Extended error: {e}")
            return {"vpc_extended_raw": {"flow_logs": [], "dhcp_options": [], "vpc_peering_connections": []}}
    
    return {
        "_fetch_vpc_extended_resources": _fetch_vpc_extended_resources
    }

def get_audit_engine_vpc_methods():
    """
    Restituisce i metodi da aggiungere a AuditEngine
    """
    def _init_vpc_auditor(self):
        """Inizializza VPC auditor se disponibile"""
        try:
            # Mock VPC auditor - in futuro potrebbe essere implementato
            print(f"   ✅ VPC Auditor mock enabled for {self.region}")
            return True
        except Exception as e:
            print(f"   ❌ Error loading VPC Auditor: {e}")
            return False

    def run_vpc_audit(self, data_dir: str = "data") -> List:
        """Esegue audit specifico VPC"""
        print(f"🌐 Starting VPC audit for region {self.region}...")
        
        # Processo dati VPC se necessario
        if not process_vpc_extended_data(data_dir):
            print("   ⚠️  VPC data processing failed")
        
        # Carica dati per audit VPC
        vpc_audit_data = self._load_vpc_audit_data(data_dir)
        
        if not vpc_audit_data:
            print(f"   ⚠️  No VPC audit data found")
            return []
        
        print(f"   🌐 VPC audit completed with basic analysis")
        return []  # Mock findings per ora

    def _load_vpc_audit_data(self, data_dir: str) -> Dict[str, Any]:
        """Carica dati specifici per audit VPC"""
        data_path = Path(data_dir)
        vpc_data = {}
        
        # File necessari per audit VPC
        vpc_files = [
            "vpc_raw.json", "subnet_raw.json", "route_table_raw.json",
            "igw_raw.json", "nat_gateways_raw.json", "vpc_endpoints_raw.json",
            "sg_raw.json", "ec2_raw.json"
        ]
        
        for filename in vpc_files:
            filepath = data_path / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        vpc_data[filename.replace('.json', '')] = data
                except Exception as e:
                    print(f"   ⚠️  Error loading {filename}: {e}")
        
        return vpc_data

    def _save_vpc_specific_results(self, vpc_findings):
        """Salva risultati specifici audit VPC"""
        reports_dir = Path("reports/vpc")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Salva summary VPC
            with open(reports_dir / "vpc_audit_summary.json", "w") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "region": self.region,
                    "findings_count": len(vpc_findings)
                }, f, indent=2)
            
            print(f"   💾 VPC audit results saved to {reports_dir}")
            
        except Exception as e:
            print(f"   ❌ Error saving VPC results: {e}")
    
    return {
        "_init_vpc_auditor": _init_vpc_auditor,
        "run_vpc_audit": run_vpc_audit,
        "_load_vpc_audit_data": _load_vpc_audit_data,
        "_save_vpc_specific_results": _save_vpc_specific_results
    }


# ==============================================================================
# INTEGRAZIONE DINAMICA (opzionale)
# ==============================================================================

def integrate_vpc_methods():
    """
    Integra dinamicamente i metodi VPC nelle classi esistenti
    """
    try:
        # Prova a integrare con ExtendedAWSFetcher
        try:
            from utils.extended_aws_fetcher import ExtendedAWSFetcher
            vpc_methods = get_extended_fetcher_vpc_methods()
            for method_name, method in vpc_methods.items():
                setattr(ExtendedAWSFetcher, method_name, method)
            print("   ✅ VPC methods integrated into ExtendedAWSFetcher")
        except ImportError:
            print("   ⚠️  ExtendedAWSFetcher not found, skipping integration")
        
        # Prova a integrare con AuditEngine
        try:
            from audit.audit_engine import AuditEngine
            vpc_methods = get_audit_engine_vpc_methods()
            for method_name, method in vpc_methods.items():
                setattr(AuditEngine, method_name, method)
            print("   ✅ VPC methods integrated into AuditEngine")
        except ImportError:
            print("   ⚠️  AuditEngine not found, skipping integration")
        
        return True
    except Exception as e:
        print(f"   ❌ Error during VPC integration: {e}")
        return False

# Auto-integrazione se il modulo viene importato
if __name__ != "__main__":
    integrate_vpc_methods()
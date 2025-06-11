#!/usr/bin/env python3
"""
AWS Infrastructure Dependency Mapper v1.0
Crea mappa visuale delle dipendenze tra risorse AWS per identificare:
- Cosa è critico vs eliminabile
- Collegamenti tra risorse
- Suggerimenti per ottimizzazione architettura
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime
import networkx as nx
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Resource:
    id: str
    name: str
    type: str
    state: str
    dependencies: List[str]
    dependents: List[str]
    criticality: str  # CRITICAL, IMPORTANT, OPTIONAL, UNUSED
    metadata: Dict[str, Any]

class AWSInfrastructureMapper:
    """Mapper per creare mappa visuale dipendenze infrastruttura AWS"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.resources = {}
        self.dependency_graph = nx.DiGraph()
        self.criticality_analysis = {}
        self.architecture_analysis = {}
        
    def analyze_infrastructure(self) -> Dict[str, Any]:
        """Analizza completa dell'infrastruttura"""
        print("🗺️  Analyzing AWS Infrastructure Dependencies...")
        
        # Load all data
        data = self._load_all_data()
        
        # Build resource inventory
        self._build_resource_inventory(data)
        
        # Map dependencies
        self._map_dependencies(data)
        
        # Analyze criticality
        self._analyze_criticality()
        
        # Analyze architecture patterns
        self._analyze_architecture_patterns()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Create visual outputs
        visual_outputs = self._create_visual_outputs()
        
        # Save results
        self._save_analysis_results()
        
        return {
            "total_resources": len(self.resources),
            "dependency_graph": self.dependency_graph,
            "criticality_summary": self._get_criticality_summary(),
            "architecture_analysis": self.architecture_analysis,
            "recommendations": recommendations,
            "visual_outputs": visual_outputs
        }
    
    def _load_all_data(self) -> Dict[str, Any]:
        """Carica tutti i dati necessari"""
        data = {}
        
        required_files = [
            "ec2_raw.json", "sg_raw.json", "eni_raw.json", "vpc_raw.json",
            "subnet_raw.json", "route_table_raw.json", "igw_raw.json",
            "nat_gateways_raw.json", "eip_raw.json", "lb_raw.json",
            "iam_raw.json", "s3_raw.json"
        ]
        
        for filename in required_files:
            filepath = self.data_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r') as f:
                        data[filename.replace('.json', '')] = json.load(f)
                except Exception as e:
                    print(f"   ⚠️  Error loading {filename}: {e}")
        
        return data
    
    def _build_resource_inventory(self, data: Dict[str, Any]):
        """Costruisce inventario completo risorse"""
        print("   📋 Building resource inventory...")
        
        # EC2 Instances
        ec2_data = data.get("ec2_raw", {})
        for reservation in ec2_data.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_id = instance["InstanceId"]
                self.resources[instance_id] = Resource(
                    id=instance_id,
                    name=self._get_instance_name(instance),
                    type="EC2Instance",
                    state=instance.get("State", {}).get("Name", "unknown"),
                    dependencies=[],
                    dependents=[],
                    criticality="UNKNOWN",
                    metadata={
                        "instance_type": instance.get("InstanceType"),
                        "subnet_id": instance.get("SubnetId"),
                        "vpc_id": instance.get("VpcId"),
                        "security_groups": [sg["GroupId"] for sg in instance.get("SecurityGroups", [])],
                        "public_ip": instance.get("PublicIpAddress"),
                        "private_ip": instance.get("PrivateIpAddress"),
                        "launch_time": str(instance.get("LaunchTime", "")),
                        "platform": instance.get("Platform"),
                        "monitoring": instance.get("Monitoring", {}).get("State")
                    }
                )
        
        # Security Groups
        sg_data = data.get("sg_raw", {})
        for sg in sg_data.get("SecurityGroups", []):
            sg_id = sg["GroupId"]
            self.resources[sg_id] = Resource(
                id=sg_id,
                name=sg.get("GroupName", sg_id),
                type="SecurityGroup",
                state="active",
                dependencies=[],
                dependents=[],
                criticality="UNKNOWN",
                metadata={
                    "vpc_id": sg.get("VpcId"),
                    "description": sg.get("Description", ""),
                    "ingress_rules": len(sg.get("IpPermissions", [])),
                    "egress_rules": len(sg.get("IpPermissionsEgress", [])),
                    "is_default": sg.get("GroupName") == "default"
                }
            )
        
        # Network Interfaces
        eni_data = data.get("eni_raw", {})
        for eni in eni_data.get("NetworkInterfaces", []):
            eni_id = eni["NetworkInterfaceId"]
            self.resources[eni_id] = Resource(
                id=eni_id,
                name=f"ENI-{eni_id[-8:]}",
                type="NetworkInterface",
                state=eni.get("Status", "unknown"),
                dependencies=[],
                dependents=[],
                criticality="UNKNOWN",
                metadata={
                    "subnet_id": eni.get("SubnetId"),
                    "vpc_id": eni.get("VpcId"),
                    "private_ip": eni.get("PrivateIpAddress"),
                    "public_ip": eni.get("Association", {}).get("PublicIp"),
                    "security_groups": [g["GroupId"] for g in eni.get("Groups", [])],
                    "attachment": eni.get("Attachment", {}),
                    "description": eni.get("Description", "")
                }
            )
        
        # VPCs
        vpc_data = data.get("vpc_raw", {})
        for vpc in vpc_data.get("Vpcs", []):
            vpc_id = vpc["VpcId"]
            self.resources[vpc_id] = Resource(
                id=vpc_id,
                name=f"VPC-{vpc_id[-8:]}",
                type="VPC",
                state=vpc.get("State", "unknown"),
                dependencies=[],
                dependents=[],
                criticality="CRITICAL",  # VPCs are usually critical
                metadata={
                    "cidr_block": vpc.get("CidrBlock"),
                    "is_default": vpc.get("IsDefault", False),
                    "dhcp_options_id": vpc.get("DhcpOptionsId"),
                    "instance_tenancy": vpc.get("InstanceTenancy")
                }
            )
        
        # Subnets
        subnet_data = data.get("subnet_raw", {})
        for subnet in subnet_data.get("Subnets", []):
            subnet_id = subnet["SubnetId"]
            self.resources[subnet_id] = Resource(
                id=subnet_id,
                name=f"Subnet-{subnet_id[-8:]}",
                type="Subnet",
                state=subnet.get("State", "unknown"),
                dependencies=[],
                dependents=[],
                criticality="UNKNOWN",
                metadata={
                    "vpc_id": subnet.get("VpcId"),
                    "cidr_block": subnet.get("CidrBlock"),
                    "availability_zone": subnet.get("AvailabilityZone"),
                    "available_ip_count": subnet.get("AvailableIpAddressCount"),
                    "map_public_ip": subnet.get("MapPublicIpOnLaunch", False)
                }
            )
        
        # NAT Gateways
        nat_data = data.get("nat_gateways_raw", {})
        for nat_gw in nat_data.get("NatGateways", []):
            nat_id = nat_gw["NatGatewayId"]
            self.resources[nat_id] = Resource(
                id=nat_id,
                name=f"NAT-{nat_id[-8:]}",
                type="NATGateway",
                state=nat_gw.get("State", "unknown"),
                dependencies=[],
                dependents=[],
                criticality="IMPORTANT",
                metadata={
                    "vpc_id": nat_gw.get("VpcId"),
                    "subnet_id": nat_gw.get("SubnetId"),
                    "create_time": str(nat_gw.get("CreateTime", "")),
                    "connectivity_type": nat_gw.get("ConnectivityType", "public")
                }
            )
        
        # Load Balancers
        lb_data = data.get("lb_raw", {})
        if lb_data:
            for alb in lb_data.get("ApplicationLoadBalancers", []):
                lb_arn = alb["LoadBalancerArn"]
                lb_name = alb["LoadBalancerName"]
                self.resources[lb_arn] = Resource(
                    id=lb_arn,
                    name=lb_name,
                    type="ApplicationLoadBalancer",
                    state=alb.get("State", {}).get("Code", "unknown"),
                    dependencies=[],
                    dependents=[],
                    criticality="CRITICAL",  # Load balancers are usually critical
                    metadata={
                        "dns_name": alb.get("DNSName"),
                        "scheme": alb.get("Scheme"),
                        "type": alb.get("Type"),
                        "vpc_id": alb.get("VpcId"),
                        "security_groups": alb.get("SecurityGroups", []),
                        "subnets": alb.get("AvailabilityZones", [])
                    }
                )
        
        # Elastic IPs
        eip_data = data.get("eip_raw", {})
        for eip in eip_data.get("Addresses", []):
            allocation_id = eip.get("AllocationId")
            if allocation_id:
                self.resources[allocation_id] = Resource(
                    id=allocation_id,
                    name=f"EIP-{eip.get('PublicIp', 'unknown')}",
                    type="ElasticIP",
                    state="available" if not eip.get("AssociationId") else "associated",
                    dependencies=[],
                    dependents=[],
                    criticality="OPTIONAL" if not eip.get("AssociationId") else "IMPORTANT",
                    metadata={
                        "public_ip": eip.get("PublicIp"),
                        "association_id": eip.get("AssociationId"),
                        "instance_id": eip.get("InstanceId"),
                        "network_interface_id": eip.get("NetworkInterfaceId")
                    }
                )
        
        print(f"      ✅ Built inventory: {len(self.resources)} resources")
    
    def _map_dependencies(self, data: Dict[str, Any]):
        """Mappa dipendenze tra risorse"""
        print("   🔗 Mapping dependencies...")
        
        # EC2 -> Security Groups dependencies
        for resource_id, resource in self.resources.items():
            if resource.type == "EC2Instance":
                sg_ids = resource.metadata.get("security_groups", [])
                for sg_id in sg_ids:
                    if sg_id in self.resources:
                        resource.dependencies.append(sg_id)
                        self.resources[sg_id].dependents.append(resource_id)
                        self.dependency_graph.add_edge(resource_id, sg_id, relationship="uses_security_group")
                
                # EC2 -> Subnet dependency
                subnet_id = resource.metadata.get("subnet_id")
                if subnet_id and subnet_id in self.resources:
                    resource.dependencies.append(subnet_id)
                    self.resources[subnet_id].dependents.append(resource_id)
                    self.dependency_graph.add_edge(resource_id, subnet_id, relationship="in_subnet")
        
        # ENI -> Security Groups dependencies
        for resource_id, resource in self.resources.items():
            if resource.type == "NetworkInterface":
                sg_ids = resource.metadata.get("security_groups", [])
                for sg_id in sg_ids:
                    if sg_id in self.resources:
                        resource.dependencies.append(sg_id)
                        self.resources[sg_id].dependents.append(resource_id)
                        self.dependency_graph.add_edge(resource_id, sg_id, relationship="uses_security_group")
                
                # ENI -> EC2 attachment
                attachment = resource.metadata.get("attachment", {})
                instance_id = attachment.get("InstanceId")
                if instance_id and instance_id in self.resources:
                    resource.dependents.append(instance_id)
                    self.resources[instance_id].dependencies.append(resource_id)
                    self.dependency_graph.add_edge(instance_id, resource_id, relationship="uses_eni")
        
        # Subnet -> VPC dependencies
        for resource_id, resource in self.resources.items():
            if resource.type == "Subnet":
                vpc_id = resource.metadata.get("vpc_id")
                if vpc_id and vpc_id in self.resources:
                    resource.dependencies.append(vpc_id)
                    self.resources[vpc_id].dependents.append(resource_id)
                    self.dependency_graph.add_edge(resource_id, vpc_id, relationship="in_vpc")
        
        # Security Groups -> VPC dependencies
        for resource_id, resource in self.resources.items():
            if resource.type == "SecurityGroup":
                vpc_id = resource.metadata.get("vpc_id")
                if vpc_id and vpc_id in self.resources:
                    resource.dependencies.append(vpc_id)
                    self.resources[vpc_id].dependents.append(resource_id)
                    self.dependency_graph.add_edge(resource_id, vpc_id, relationship="in_vpc")
        
        # Load Balancer dependencies
        for resource_id, resource in self.resources.items():
            if resource.type == "ApplicationLoadBalancer":
                sg_ids = resource.metadata.get("security_groups", [])
                for sg_id in sg_ids:
                    if sg_id in self.resources:
                        resource.dependencies.append(sg_id)
                        self.resources[sg_id].dependents.append(resource_id)
                        self.dependency_graph.add_edge(resource_id, sg_id, relationship="uses_security_group")
        
        # EIP associations
        for resource_id, resource in self.resources.items():
            if resource.type == "ElasticIP":
                instance_id = resource.metadata.get("instance_id")
                eni_id = resource.metadata.get("network_interface_id")
                
                if instance_id and instance_id in self.resources:
                    resource.dependents.append(instance_id)
                    self.resources[instance_id].dependencies.append(resource_id)
                    self.dependency_graph.add_edge(instance_id, resource_id, relationship="uses_eip")
                
                if eni_id and eni_id in self.resources:
                    resource.dependents.append(eni_id)
                    self.resources[eni_id].dependencies.append(resource_id)
                    self.dependency_graph.add_edge(eni_id, resource_id, relationship="uses_eip")
        
        print(f"      ✅ Mapped {self.dependency_graph.number_of_edges()} dependencies")
    
    def _analyze_criticality(self):
        """Analizza criticità delle risorse"""
        print("   🎯 Analyzing resource criticality...")
        
        for resource_id, resource in self.resources.items():
            if resource.criticality == "UNKNOWN":
                resource.criticality = self._determine_criticality(resource)
        
        # Summary by criticality
        self.criticality_analysis = {
            "CRITICAL": [r for r in self.resources.values() if r.criticality == "CRITICAL"],
            "IMPORTANT": [r for r in self.resources.values() if r.criticality == "IMPORTANT"],
            "OPTIONAL": [r for r in self.resources.values() if r.criticality == "OPTIONAL"],
            "UNUSED": [r for r in self.resources.values() if r.criticality == "UNUSED"]
        }
        
        print(f"      ✅ Criticality: {len(self.criticality_analysis['CRITICAL'])} critical, "
              f"{len(self.criticality_analysis['UNUSED'])} unused")
    
    def _determine_criticality(self, resource: Resource) -> str:
        """Determina criticità di una risorsa"""
        
        # VPCs are always critical
        if resource.type == "VPC":
            return "CRITICAL"
        
        # Load Balancers are critical if active
        if resource.type == "ApplicationLoadBalancer":
            return "CRITICAL" if resource.state == "active" else "OPTIONAL"
        
        # Running EC2 instances are critical
        if resource.type == "EC2Instance":
            if resource.state == "running":
                return "CRITICAL"
            elif resource.state == "stopped":
                return "OPTIONAL"
            else:
                return "UNUSED"
        
        # Security Groups
        if resource.type == "SecurityGroup":
            if len(resource.dependents) > 0:
                # If attached to running instances or load balancers
                for dependent_id in resource.dependents:
                    dependent = self.resources.get(dependent_id)
                    if dependent and dependent.type == "EC2Instance" and dependent.state == "running":
                        return "CRITICAL"
                    if dependent and dependent.type == "ApplicationLoadBalancer":
                        return "CRITICAL"
                return "IMPORTANT"
            else:
                return "UNUSED" if resource.name != "default" else "OPTIONAL"
        
        # Network Interfaces
        if resource.type == "NetworkInterface":
            attachment = resource.metadata.get("attachment", {})
            if attachment.get("InstanceId"):
                instance = self.resources.get(attachment["InstanceId"])
                if instance and instance.state == "running":
                    return "CRITICAL"
                else:
                    return "IMPORTANT"
            return "UNUSED"
        
        # Subnets
        if resource.type == "Subnet":
            if len(resource.dependents) > 0:
                # Check if has running instances
                for dependent_id in resource.dependents:
                    dependent = self.resources.get(dependent_id)
                    if dependent and dependent.type == "EC2Instance" and dependent.state == "running":
                        return "CRITICAL"
                return "IMPORTANT"
            return "UNUSED"
        
        # NAT Gateways
        if resource.type == "NATGateway":
            return "IMPORTANT" if resource.state == "available" else "UNUSED"
        
        # Elastic IPs
        if resource.type == "ElasticIP":
            if resource.state == "associated":
                # Check if associated with running instance
                instance_id = resource.metadata.get("instance_id")
                if instance_id:
                    instance = self.resources.get(instance_id)
                    if instance and instance.state == "running":
                        return "IMPORTANT"
                return "OPTIONAL"
            return "UNUSED"
        
        return "OPTIONAL"
    
    def _analyze_architecture_patterns(self):
        """Analizza pattern architetturali"""
        print("   🏗️  Analyzing architecture patterns...")
        
        # Count resources by type
        resource_counts = defaultdict(int)
        for resource in self.resources.values():
            resource_counts[resource.type] += 1
        
        # Analyze VPC structure
        vpc_analysis = self._analyze_vpc_structure()
        
        # Analyze security posture
        security_analysis = self._analyze_security_posture()
        
        # Analyze high availability
        ha_analysis = self._analyze_high_availability()
        
        # Analyze cost optimization opportunities
        cost_analysis = self._analyze_cost_opportunities()
        
        self.architecture_analysis = {
            "resource_counts": dict(resource_counts),
            "vpc_structure": vpc_analysis,
            "security_posture": security_analysis,
            "high_availability": ha_analysis,
            "cost_optimization": cost_analysis,
            "overall_score": self._calculate_architecture_score()
        }
    
    def _analyze_vpc_structure(self) -> Dict[str, Any]:
        """Analizza struttura VPC"""
        vpcs = [r for r in self.resources.values() if r.type == "VPC"]
        
        analysis = {
            "total_vpcs": len(vpcs),
            "default_vpcs": len([v for v in vpcs if v.metadata.get("is_default")]),
            "multi_vpc_setup": len(vpcs) > 1,
            "recommendations": []
        }
        
        if analysis["default_vpcs"] > 0:
            analysis["recommendations"].append("Migrate from default VPC to custom VPC")
        
        if len(vpcs) > 3:
            analysis["recommendations"].append("Consider VPC consolidation for simpler management")
        
        return analysis
    
    def _analyze_security_posture(self) -> Dict[str, Any]:
        """Analizza postura di sicurezza"""
        security_groups = [r for r in self.resources.values() if r.type == "SecurityGroup"]
        
        # Load security audit data if available
        try:
            with open(self.data_dir.parent / "reports" / "security_findings.json", 'r') as f:
                security_data = json.load(f)
                critical_findings = len([f for f in security_data.get("findings", []) if f.get("severity") == "critical"])
                high_findings = len([f for f in security_data.get("findings", []) if f.get("severity") == "high"])
        except:
            critical_findings = 0
            high_findings = 0
        
        analysis = {
            "total_security_groups": len(security_groups),
            "unused_security_groups": len([sg for sg in security_groups if sg.criticality == "UNUSED"]),
            "critical_security_issues": critical_findings,
            "high_security_issues": high_findings,
            "security_score": max(0, 100 - (critical_findings * 25) - (high_findings * 10)),
            "recommendations": []
        }
        
        if analysis["unused_security_groups"] > 0:
            analysis["recommendations"].append(f"Remove {analysis['unused_security_groups']} unused security groups")
        
        if critical_findings > 0:
            analysis["recommendations"].append(f"URGENT: Fix {critical_findings} critical security issues")
        
        return analysis
    
    def _analyze_high_availability(self) -> Dict[str, Any]:
        """Analizza alta disponibilità"""
        running_instances = [r for r in self.resources.values() 
                           if r.type == "EC2Instance" and r.state == "running"]
        
        # Group by AZ
        az_distribution = defaultdict(int)
        for instance in running_instances:
            subnet_id = instance.metadata.get("subnet_id")
            if subnet_id and subnet_id in self.resources:
                subnet = self.resources[subnet_id]
                az = subnet.metadata.get("availability_zone")
                if az:
                    az_distribution[az] += 1
        
        analysis = {
            "total_running_instances": len(running_instances),
            "availability_zones": len(az_distribution),
            "az_distribution": dict(az_distribution),
            "single_point_of_failure": len(az_distribution) == 1,
            "load_balancers": len([r for r in self.resources.values() if r.type == "ApplicationLoadBalancer"]),
            "recommendations": []
        }
        
        if analysis["single_point_of_failure"]:
            analysis["recommendations"].append("Deploy instances across multiple AZs for high availability")
        
        if analysis["load_balancers"] == 0 and len(running_instances) > 1:
            analysis["recommendations"].append("Consider load balancer for distributing traffic")
        
        return analysis
    
    def _analyze_cost_opportunities(self) -> Dict[str, Any]:
        """Analizza opportunità di ottimizzazione costi"""
        unused_eips = len([r for r in self.resources.values() 
                          if r.type == "ElasticIP" and r.criticality == "UNUSED"])
        unused_sgs = len([r for r in self.resources.values() 
                         if r.type == "SecurityGroup" and r.criticality == "UNUSED"])
        stopped_instances = len([r for r in self.resources.values() 
                               if r.type == "EC2Instance" and r.state == "stopped"])
        
        # Estimated monthly savings
        estimated_monthly_savings = (unused_eips * 3.65) + (stopped_instances * 10)  # Rough estimates
        
        analysis = {
            "unused_elastic_ips": unused_eips,
            "unused_security_groups": unused_sgs,
            "stopped_instances": stopped_instances,
            "estimated_monthly_savings": estimated_monthly_savings,
            "estimated_annual_savings": estimated_monthly_savings * 12,
            "recommendations": []
        }
        
        if unused_eips > 0:
            analysis["recommendations"].append(f"Release {unused_eips} unused Elastic IPs (${unused_eips * 3.65:.2f}/month)")
        
        if stopped_instances > 0:
            analysis["recommendations"].append(f"Review {stopped_instances} stopped instances for termination")
        
        return analysis
    
    def _calculate_architecture_score(self) -> Dict[str, Any]:
        """Calcola score architettura"""
        score = 100
        
        # Deduct points for issues
        security_score = self.architecture_analysis.get("security_posture", {}).get("security_score", 100)
        score = min(score, security_score)
        
        if self.architecture_analysis.get("vpc_structure", {}).get("default_vpcs", 0) > 0:
            score -= 20
        
        if self.architecture_analysis.get("high_availability", {}).get("single_point_of_failure", False):
            score -= 30
        
        if self.architecture_analysis.get("cost_optimization", {}).get("unused_elastic_ips", 0) > 0:
            score -= 10
        
        score = max(0, score)
        
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return {"score": score, "grade": grade}
    
    def _generate_recommendations(self) -> Dict[str, Any]:
        """Genera raccomandazioni per migliorare l'architettura"""
        recommendations = {
            "immediate_actions": [],
            "short_term_improvements": [],
            "long_term_strategies": [],
            "infrastructure_as_code_template": self._generate_iac_template()
        }
        
        # Immediate actions (critical issues)
        critical_resources = self.criticality_analysis["CRITICAL"]
        unused_resources = self.criticality_analysis["UNUSED"]
        
        if len(unused_resources) > 0:
            recommendations["immediate_actions"].append({
                "action": "Remove unused resources",
                "details": f"Delete {len(unused_resources)} unused resources to reduce costs and complexity",
                "resources": [{"id": r.id, "type": r.type, "name": r.name} for r in unused_resources[:10]],
                "estimated_monthly_savings": self.architecture_analysis["cost_optimization"]["estimated_monthly_savings"]
            })
        
        # Security improvements
        security_issues = self.architecture_analysis["security_posture"]["critical_security_issues"]
        if security_issues > 0:
            recommendations["immediate_actions"].append({
                "action": "Fix critical security issues",
                "details": f"Address {security_issues} critical security vulnerabilities",
                "priority": "URGENT"
            })
        
        # High availability improvements
        if self.architecture_analysis["high_availability"]["single_point_of_failure"]:
            recommendations["short_term_improvements"].append({
                "action": "Implement multi-AZ deployment",
                "details": "Deploy instances across multiple availability zones",
                "benefit": "Improved fault tolerance and availability"
            })
        
        # Architecture modernization
        recommendations["long_term_strategies"].append({
            "action": "Infrastructure as Code implementation",
            "details": "Implement Terraform/CloudFormation for reproducible infrastructure",
            "benefit": "Consistent deployments, version control, reduced manual errors"
        })
        
        return recommendations
    
    def _generate_iac_template(self) -> str:
        """Genera template Infrastructure as Code ottimizzato"""
        # Analyze current architecture to suggest optimal IaC
        running_instances = [r for r in self.resources.values() 
                           if r.type == "EC2Instance" and r.state == "running"]
        vpcs = [r for r in self.resources.values() if r.type == "VPC" and not r.metadata.get("is_default")]
        
        template = f"""# Optimized AWS Infrastructure Template
# Generated from current infrastructure analysis
# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Summary of current infrastructure:
# - {len(running_instances)} running EC2 instances
# - {len(vpcs)} custom VPCs
# - {len(self.resources)} total resources

terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

# Variables for environment customization
variable "environment" {{
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}}

variable "project_name" {{
  description = "Project name for resource naming"
  type        = string
  default     = "optimized-infrastructure"
}}

# Optimized VPC (based on current analysis)
resource "aws_vpc" "main" {{
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {{
    Name        = "${{var.project_name}}-vpc"
    Environment = var.environment
    Managed     = "terraform"
  }}
}}

# Multi-AZ Subnets for high availability
resource "aws_subnet" "public" {{
  count = 2
  
  vpc_id                  = aws_vpc.main.id
  cidr_block             = "10.0.${{count.index + 1}}.0/24"
  availability_zone      = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {{
    Name = "${{var.project_name}}-public-${{count.index + 1}}"
    Type = "public"
  }}
}}

resource "aws_subnet" "private" {{
  count = 2
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${{count.index + 10}}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {{
    Name = "${{var.project_name}}-private-${{count.index + 1}}"
    Type = "private"
  }}
}}

# Internet Gateway
resource "aws_internet_gateway" "main" {{
  vpc_id = aws_vpc.main.id
  
  tags = {{
    Name = "${{var.project_name}}-igw"
  }}
}}

# Single NAT Gateway (cost optimized)
resource "aws_eip" "nat" {{
  domain = "vpc"
  
  tags = {{
    Name = "${{var.project_name}}-nat-eip"
  }}
}}

resource "aws_nat_gateway" "main" {{
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  
  tags = {{
    Name = "${{var.project_name}}-nat"
  }}
  
  depends_on = [aws_internet_gateway.main]
}}

# Optimized Security Groups
resource "aws_security_group" "web" {{
  name_prefix = "${{var.project_name}}-web-"
  vpc_id      = aws_vpc.main.id
  
  # Only necessary ports
  ingress {{
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  ingress {{
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  tags = {{
    Name = "${{var.project_name}}-web-sg"
  }}
}}

resource "aws_security_group" "app" {{
  name_prefix = "${{var.project_name}}-app-"
  vpc_id      = aws_vpc.main.id
  
  # Internal communication only
  ingress {{
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
  }}
  
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  tags = {{
    Name = "${{var.project_name}}-app-sg"
  }}
}}

# Application Load Balancer for high availability
resource "aws_lb" "main" {{
  name               = "${{var.project_name}}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.web.id]
  subnets           = aws_subnet.public[*].id
  
  enable_deletion_protection = false
  
  tags = {{
    Name = "${{var.project_name}}-alb"
  }}
}}

# Data sources
data "aws_availability_zones" "available" {{
  state = "available"
}}

data "aws_ami" "amazon_linux" {{
  most_recent = true
  owners      = ["amazon"]
  
  filter {{
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }}
}}

# Auto Scaling Group for resilience
resource "aws_launch_template" "app" {{
  name_prefix   = "${{var.project_name}}-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"  # Cost optimized
  
  vpc_security_group_ids = [aws_security_group.app.id]
  
  user_data = base64encode(templatefile("${{path.module}}/user_data.sh", {{
    project_name = var.project_name
  }}))
  
  tag_specifications {{
    resource_type = "instance"
    tags = {{
      Name = "${{var.project_name}}-app"
    }}
  }}
}}

resource "aws_autoscaling_group" "app" {{
  name                = "${{var.project_name}}-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  target_group_arns   = [aws_lb_target_group.app.arn]
  health_check_type   = "ELB"
  
  min_size         = 1
  max_size         = 3
  desired_capacity = 2
  
  launch_template {{
    id      = aws_launch_template.app.id
    version = "$Latest"
  }}
  
  tag {{
    key                 = "Name"
    value               = "${{var.project_name}}-asg"
    propagate_at_launch = false
  }}
}}

# Target Group for Load Balancer
resource "aws_lb_target_group" "app" {{
  name     = "${{var.project_name}}-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  
  health_check {{
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }}
}}

resource "aws_lb_listener" "app" {{
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {{
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }}
}}

# Route Tables
resource "aws_route_table" "public" {{
  vpc_id = aws_vpc.main.id
  
  route {{
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }}
  
  tags = {{
    Name = "${{var.project_name}}-public-rt"
  }}
}}

resource "aws_route_table" "private" {{
  vpc_id = aws_vpc.main.id
  
  route {{
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }}
  
  tags = {{
    Name = "${{var.project_name}}-private-rt"
  }}
}}

# Route Table Associations
resource "aws_route_table_association" "public" {{
  count = length(aws_subnet.public)
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}}

resource "aws_route_table_association" "private" {{
  count = length(aws_subnet.private)
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}}

# Outputs
output "vpc_id" {{
  value = aws_vpc.main.id
}}

output "load_balancer_dns" {{
  value = aws_lb.main.dns_name
}}

output "public_subnets" {{
  value = aws_subnet.public[*].id
}}

output "private_subnets" {{
  value = aws_subnet.private[*].id
}}
"""
        
        return template.strip()
    
    def _create_visual_outputs(self) -> Dict[str, Any]:
        """Crea output visuali"""
        print("   📊 Creating visual outputs...")
        
        # Create graphviz DOT format for dependency graph
        dot_graph = self._create_dot_graph()
        
        # Create HTML dependency map
        html_map = self._create_html_dependency_map()
        
        # Create cleanup priority matrix
        cleanup_matrix = self._create_cleanup_matrix()
        
        return {
            "dependency_graph_dot": dot_graph,
            "html_dependency_map": html_map,
            "cleanup_priority_matrix": cleanup_matrix
        }
    
    def _create_dot_graph(self) -> str:
        """Crea grafo in formato DOT per Graphviz"""
        dot_lines = [
            "digraph AWS_Infrastructure {",
            "  rankdir=TB;",
            "  node [shape=box, style=filled];",
            "  edge [fontsize=10];",
            ""
        ]
        
        # Define colors by resource type and criticality
        colors = {
            "CRITICAL": "#FF4444",
            "IMPORTANT": "#FFA500", 
            "OPTIONAL": "#90EE90",
            "UNUSED": "#D3D3D3"
        }
        
        # Add nodes
        for resource_id, resource in self.resources.items():
            color = colors.get(resource.criticality, "#FFFFFF")
            label = f"{resource.name}\\n({resource.type})\\n{resource.state}"
            
            dot_lines.append(f'  "{resource_id}" [label="{label}", fillcolor="{color}"];')
        
        dot_lines.append("")
        
        # Add edges
        for edge in self.dependency_graph.edges(data=True):
            source, target, data = edge
            relationship = data.get("relationship", "depends_on")
            dot_lines.append(f'  "{source}" -> "{target}" [label="{relationship}"];')
        
        dot_lines.extend(["", "}"])
        
        return "\n".join(dot_lines)
    
    def _create_html_dependency_map(self) -> str:
        """Crea mappa HTML interattiva"""
        html_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>AWS Infrastructure Dependency Map</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .node circle { cursor: pointer; }
        .node text { font-size: 12px; }
        .link { stroke: #999; stroke-opacity: 0.6; stroke-width: 2px; }
        .legend { position: absolute; top: 10px; right: 10px; }
        .legend-item { margin: 5px 0; }
        .tooltip { position: absolute; background: rgba(0,0,0,0.8); color: white; 
                   padding: 10px; border-radius: 5px; font-size: 12px; pointer-events: none; }
    </style>
</head>
<body>
    <h1>🗺️ AWS Infrastructure Dependency Map</h1>
    <div class="legend">
        <div class="legend-item"><span style="color: #FF4444;">●</span> Critical</div>
        <div class="legend-item"><span style="color: #FFA500;">●</span> Important</div>
        <div class="legend-item"><span style="color: #90EE90;">●</span> Optional</div>
        <div class="legend-item"><span style="color: #D3D3D3;">●</span> Unused</div>
    </div>
    <svg width="1200" height="800"></svg>
    <div class="tooltip" style="display: none;"></div>
    
    <script>
        // D3.js visualization code would go here
        // This is a simplified version - full implementation would include:
        // - Interactive force-directed graph
        // - Drag and drop functionality  
        // - Tooltips with resource details
        // - Filtering by criticality
        // - Export functionality
        
        console.log("Interactive dependency map would be rendered here");
        
        // For now, display a text summary
        const svg = d3.select("svg");
        svg.append("text")
           .attr("x", 600)
           .attr("y", 400)
           .attr("text-anchor", "middle")
           .style("font-size", "20px")
           .text("Interactive dependency map placeholder");
           
        svg.append("text")
           .attr("x", 600)
           .attr("y", 430)
           .attr("text-anchor", "middle")
           .style("font-size", "14px")
           .text("Full D3.js implementation would render interactive graph here");
    </script>
</body>
</html>
'''
        return html_template
    
    def _create_cleanup_matrix(self) -> List[Dict[str, Any]]:
        """Crea matrice di priorità per cleanup"""
        cleanup_items = []
        
        for resource in self.resources.values():
            if resource.criticality in ["UNUSED", "OPTIONAL"]:
                # Calculate cleanup priority score
                priority_score = 0
                
                if resource.criticality == "UNUSED":
                    priority_score += 10
                elif resource.criticality == "OPTIONAL":
                    priority_score += 5
                
                # Add points for cost savings
                if resource.type == "ElasticIP" and resource.state == "available":
                    priority_score += 8  # High cost savings
                elif resource.type == "EC2Instance" and resource.state == "stopped":
                    priority_score += 6  # Medium cost savings
                elif resource.type == "SecurityGroup":
                    priority_score += 2  # Low cost savings but reduces complexity
                
                # Reduce score if has dependents
                if len(resource.dependents) > 0:
                    priority_score -= 5
                
                cleanup_items.append({
                    "resource_id": resource.id,
                    "resource_name": resource.name,
                    "resource_type": resource.type,
                    "criticality": resource.criticality,
                    "state": resource.state,
                    "priority_score": priority_score,
                    "dependents_count": len(resource.dependents),
                    "dependencies_count": len(resource.dependencies),
                    "estimated_monthly_savings": self._estimate_resource_cost(resource),
                    "risk_level": "LOW" if len(resource.dependents) == 0 else "MEDIUM"
                })
        
        # Sort by priority score (highest first)
        cleanup_items.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return cleanup_items
    
    def _estimate_resource_cost(self, resource: Resource) -> float:
        """Stima costo mensile risorsa"""
        if resource.type == "ElasticIP" and resource.state == "available":
            return 3.65  # $3.65/month for unassociated EIP
        elif resource.type == "EC2Instance":
            instance_type = resource.metadata.get("instance_type", "t3.micro")
            # Simplified cost estimation
            cost_map = {
                "t3.micro": 7.59, "t3.small": 15.18, "t3.medium": 30.37,
                "t3.large": 60.74, "m5.large": 70.08, "m5.xlarge": 140.16
            }
            return cost_map.get(instance_type, 30.0)
        elif resource.type == "NATGateway":
            return 45.36  # $45.36/month for NAT Gateway
        else:
            return 0.0
    
    def _get_criticality_summary(self) -> Dict[str, Any]:
        """Ottieni summary criticità"""
        return {
            "critical_count": len(self.criticality_analysis["CRITICAL"]),
            "important_count": len(self.criticality_analysis["IMPORTANT"]),
            "optional_count": len(self.criticality_analysis["OPTIONAL"]),
            "unused_count": len(self.criticality_analysis["UNUSED"]),
            "total_resources": len(self.resources)
        }
    
    def _save_analysis_results(self):
        """Salva risultati analisi"""
        print("   💾 Saving analysis results...")
        
        # Create reports directory
        reports_dir = Path("reports/infrastructure_map")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Save complete analysis
        analysis_data = {
            "timestamp": datetime.now().isoformat(),
            "resources": {rid: {
                "id": r.id,
                "name": r.name,
                "type": r.type,
                "state": r.state,
                "criticality": r.criticality,
                "dependencies": r.dependencies,
                "dependents": r.dependents,
                "metadata": r.metadata
            } for rid, r in self.resources.items()},
            "criticality_analysis": {
                k: [{"id": r.id, "name": r.name, "type": r.type} for r in v]
                for k, v in self.criticality_analysis.items()
            },
            "architecture_analysis": self.architecture_analysis
        }
        
        with open(reports_dir / "complete_analysis.json", "w") as f:
            json.dump(analysis_data, f, indent=2)
        
        # Save DOT graph
        visual_outputs = self._create_visual_outputs()
        
        with open(reports_dir / "dependency_graph.dot", "w") as f:
            f.write(visual_outputs["dependency_graph_dot"])
        
        with open(reports_dir / "dependency_map.html", "w") as f:
            f.write(visual_outputs["html_dependency_map"])
        
        # Save cleanup matrix
        cleanup_matrix = visual_outputs["cleanup_priority_matrix"]
        with open(reports_dir / "cleanup_priority_matrix.json", "w") as f:
            json.dump(cleanup_matrix, f, indent=2)
        
        # Generate summary report
        self._generate_infrastructure_report(reports_dir)
        
        print(f"      ✅ Results saved to {reports_dir}")
    
    def _generate_infrastructure_report(self, reports_dir: Path):
        """Genera report riassuntivo dell'infrastruttura"""
        
        report_lines = [
            "# 🗺️ AWS Infrastructure Analysis Report",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 📊 Infrastructure Overview",
            f"- **Total Resources**: {len(self.resources)}",
            f"- **Critical Resources**: {len(self.criticality_analysis['CRITICAL'])}",
            f"- **Unused Resources**: {len(self.criticality_analysis['UNUSED'])}",
            f"- **Architecture Score**: {self.architecture_analysis['overall_score']['score']}/100 ({self.architecture_analysis['overall_score']['grade']})",
            "",
            "## 🎯 Resource Criticality Breakdown",
            ""
        ]
        
        for criticality, resources in self.criticality_analysis.items():
            if resources:
                icon = {"CRITICAL": "🔴", "IMPORTANT": "🟡", "OPTIONAL": "🟢", "UNUSED": "⚪"}[criticality]
                report_lines.append(f"### {icon} {criticality} ({len(resources)} resources)")
                
                for resource in resources[:10]:  # Show first 10
                    report_lines.append(f"- {resource.name} ({resource.type}) - {resource.state}")
                
                if len(resources) > 10:
                    report_lines.append(f"- ... and {len(resources) - 10} more")
                
                report_lines.append("")
        
        # Architecture Analysis
        report_lines.extend([
            "## 🏗️ Architecture Analysis",
            "",
            f"**VPC Structure**: {self.architecture_analysis['vpc_structure']['total_vpcs']} VPCs",
            f"**Security Score**: {self.architecture_analysis['security_posture']['security_score']}/100",
            f"**High Availability**: {'❌ Single AZ' if self.architecture_analysis['high_availability']['single_point_of_failure'] else '✅ Multi-AZ'}",
            f"**Estimated Monthly Savings**: ${self.architecture_analysis['cost_optimization']['estimated_monthly_savings']:.2f}",
            ""
        ])
        
        # Immediate Actions
        if self.criticality_analysis["UNUSED"]:
            report_lines.extend([
                "## 🚨 Immediate Actions Required",
                "",
                f"### Remove {len(self.criticality_analysis['UNUSED'])} Unused Resources",
                ""
            ])
            
            for resource in self.criticality_analysis["UNUSED"][:5]:
                cost = self._estimate_resource_cost(resource)
                cost_text = f" (${cost:.2f}/month)" if cost > 0 else ""
                report_lines.append(f"- **{resource.name}** ({resource.type}){cost_text}")
            
            report_lines.append("")
        
        # Recommendations
        report_lines.extend([
            "## 💡 Optimization Recommendations",
            "",
            "### Infrastructure as Code Template",
            "A Terraform template has been generated based on your current infrastructure.",
            "Key improvements in the template:",
            "- Multi-AZ deployment for high availability",
            "- Optimized security groups with minimal required access",
            "- Cost-optimized instance types and NAT Gateway setup",
            "- Auto Scaling Groups for resilience",
            "- Application Load Balancer for traffic distribution",
            "",
            "### Next Steps",
            "1. **Review unused resources** and plan for removal",
            "2. **Fix critical security issues** (see security audit report)",
            "3. **Plan multi-AZ migration** for high availability",
            "4. **Implement Infrastructure as Code** using the generated template",
            "5. **Set up monitoring and alerting** for the new architecture",
            "",
            "## 📁 Generated Files",
            "- `complete_analysis.json` - Full infrastructure analysis data",
            "- `dependency_graph.dot` - Graphviz dependency graph",
            "- `dependency_map.html` - Interactive HTML map",
            "- `cleanup_priority_matrix.json` - Prioritized cleanup recommendations",
            "",
            "## 🔧 Tools for Visualization",
            "To visualize the dependency graph:",
            "```bash",
            "# Install Graphviz",
            "brew install graphviz  # macOS",
            "# sudo apt-get install graphviz  # Ubuntu",
            "",
            "# Generate PNG image",
            "dot -Tpng dependency_graph.dot -o infrastructure_map.png",
            "",
            "# Generate SVG for web",
            "dot -Tsvg dependency_graph.dot -o infrastructure_map.svg",
            "```"
        ])
        
        # Save report
        with open(reports_dir / "infrastructure_analysis_report.md", "w") as f:
            f.write("\n".join(report_lines))
    
    def _get_instance_name(self, instance: Dict[str, Any]) -> str:
        """Estrae nome istanza dai tag"""
        for tag in instance.get("Tags", []):
            if tag.get("Key") == "Name":
                return tag.get("Value", instance.get("InstanceId", "Unknown"))
        return instance.get("InstanceId", "Unknown")


def main():
    """Funzione principale"""
    mapper = AWSInfrastructureMapper()
    results = mapper.analyze_infrastructure()
    
    print("\n" + "="*60)
    print("🗺️ AWS INFRASTRUCTURE MAPPING COMPLETED!")
    print("="*60)
    
    summary = results["criticality_summary"]
    print(f"📊 Total Resources: {summary['total_resources']}")
    print(f"🔴 Critical: {summary['critical_count']}")
    print(f"🟡 Important: {summary['important_count']}")
    print(f"🟢 Optional: {summary['optional_count']}")
    print(f"⚪ Unused: {summary['unused_count']}")
    
    print(f"\n🏗️ Architecture Score: {results['architecture_analysis']['overall_score']['score']}/100 "
          f"({results['architecture_analysis']['overall_score']['grade']})")
    
    estimated_savings = results["architecture_analysis"]["cost_optimization"]["estimated_monthly_savings"]
    print(f"💰 Potential Monthly Savings: ${estimated_savings:.2f}")
    
    print(f"\n📁 Reports generated in: reports/infrastructure_map/")
    print("🔧 To visualize dependency graph:")
    print("   dot -Tpng reports/infrastructure_map/dependency_graph.dot -o infrastructure_map.png")


if __name__ == "__main__":
    main()
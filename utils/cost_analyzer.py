# utils/cost_analyzer.py
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio

@dataclass
class CostBreakdown:
    service: str
    monthly_cost: float
    annual_cost: float
    resources: List[Dict]
    optimization_potential: float
    criticality: str  # "essential", "important", "optional"

@dataclass
class CostOptimization:
    resource_id: str
    resource_type: str
    current_monthly_cost: float
    optimized_monthly_cost: float
    savings_monthly: float
    optimization_type: str
    effort_level: str  # "low", "medium", "high"
    risk_level: str   # "low", "medium", "high"
    implementation_steps: List[str]

class AdvancedCostAnalyzer:
    """Analizzatore avanzato dei costi AWS con ottimizzazioni specifiche"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.session = boto3.Session()
        self.ce_client = self.session.client('ce', region_name='us-east-1')  # Cost Explorer è solo us-east-1
        self.pricing_client = self.session.client('pricing', region_name='us-east-1')  # Pricing API
        
        # Mappatura prezzi base (USD/ora) - aggiornare periodicamente
        self.pricing_map = {
            'ec2': {
                't2.micro': 0.0116, 't2.small': 0.0232, 't2.medium': 0.0464, 't2.large': 0.0928,
                't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416, 't3.large': 0.0832,
                't3.xlarge': 0.1664, 't3.2xlarge': 0.3328,
                'm5.large': 0.096, 'm5.xlarge': 0.192, 'm5.2xlarge': 0.384, 'm5.4xlarge': 0.768,
                'c5.large': 0.085, 'c5.xlarge': 0.17, 'c5.2xlarge': 0.34,
                'r5.large': 0.126, 'r5.xlarge': 0.252, 'r5.2xlarge': 0.504,
                'i3.large': 0.156, 'i3.xlarge': 0.312
            },
            'rds': {
                'db.t3.micro': 0.017, 'db.t3.small': 0.034, 'db.t3.medium': 0.068,
                'db.t3.large': 0.136, 'db.t3.xlarge': 0.272,
                'db.m5.large': 0.192, 'db.m5.xlarge': 0.384, 'db.m5.2xlarge': 0.768,
                'db.r5.large': 0.24, 'db.r5.xlarge': 0.48
            },
            'storage': {
                'gp2': 0.10, 'gp3': 0.08, 'io1': 0.125, 'io2': 0.125,
                'st1': 0.045, 'sc1': 0.025
            },
            'nat_gateway': 0.045,  # per ora
            'load_balancer': {'alb': 0.0225, 'nlb': 0.0225, 'clb': 0.025},
            'cloudwatch': {'custom_metrics': 0.30, 'alarms': 0.10, 'dashboards': 3.00}
        }
        
        self.cost_breakdown = []
        self.optimizations = []
        self.total_monthly_cost = 0
        self.total_potential_savings = 0
    
    async def analyze_complete_costs(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisi completa dei costi con raccomandazioni"""
        print("💰 Analyzing complete AWS costs...")
        
        # Reset
        self.cost_breakdown = []
        self.optimizations = []
        self.total_monthly_cost = 0
        self.total_potential_savings = 0
        
        # Analizza ogni categoria di risorsa
        await self._analyze_ec2_costs(audit_data)
        await self._analyze_rds_costs(audit_data)
        await self._analyze_storage_costs(audit_data)
        await self._analyze_network_costs(audit_data)
        await self._analyze_lambda_costs(audit_data)
        await self._analyze_container_costs(audit_data)
        await self._analyze_data_transfer_costs(audit_data)
        await self._analyze_monitoring_costs(audit_data)
        
        # Fetch dati storici da Cost Explorer
        historical_costs = await self._fetch_historical_costs()
        
        # Genera raccomandazioni di ottimizzazione
        self._generate_optimization_recommendations()
        
        # Calcola ROI delle ottimizzazioni
        roi_analysis = self._calculate_optimization_roi()
        
        return {
            "current_monthly_cost": self.total_monthly_cost,
            "annual_cost": self.total_monthly_cost * 12,
            "potential_monthly_savings": self.total_potential_savings,
            "potential_annual_savings": self.total_potential_savings * 12,
            "savings_percentage": (self.total_potential_savings / max(self.total_monthly_cost, 1)) * 100,
            "cost_breakdown": [self._breakdown_to_dict(cb) for cb in self.cost_breakdown],
            "optimizations": [self._optimization_to_dict(opt) for opt in self.optimizations],
            "historical_data": historical_costs,
            "roi_analysis": roi_analysis,
            "quick_wins": self._identify_quick_wins(),
            "cost_alerts": self._generate_cost_alerts(),
            "recommendations_summary": self._generate_recommendations_summary()
        }
    
    async def _analyze_ec2_costs(self, audit_data: Dict[str, Any]):
        """Analizza costi EC2 dettagliati"""
        ec2_data = audit_data.get("ec2_audit", {})
        active_instances = ec2_data.get("active", [])
        stopped_instances = ec2_data.get("stopped", [])
        
        total_ec2_cost = 0
        optimization_potential = 0
        ec2_resources = []
        
        # Istanze attive
        for instance in active_instances:
            instance_type = instance.get("Type", "t3.micro")
            hourly_cost = self.pricing_map['ec2'].get(instance_type, 0.05)
            monthly_cost = hourly_cost * 24 * 30.44  # Media giorni al mese
            
            total_ec2_cost += monthly_cost
            
            ec2_resources.append({
                "id": instance.get("InstanceId"),
                "name": instance.get("Name"),
                "type": instance_type,
                "state": "running",
                "monthly_cost": monthly_cost,
                "public_ip": instance.get("PublicIp"),
                "optimization_candidate": self._is_rightsizing_candidate(instance)
            })
            
            # Calcola potential savings per rightsizing
            if self._is_rightsizing_candidate(instance):
                recommended_type = self._get_recommended_instance_type(instance_type)
                if recommended_type != instance_type:
                    recommended_cost = self.pricing_map['ec2'].get(recommended_type, hourly_cost) * 24 * 30.44
                    savings = monthly_cost - recommended_cost
                    if savings > 0:
                        optimization_potential += savings
                        
                        self.optimizations.append(CostOptimization(
                            resource_id=instance.get("InstanceId"),
                            resource_type="EC2",
                            current_monthly_cost=monthly_cost,
                            optimized_monthly_cost=recommended_cost,
                            savings_monthly=savings,
                            optimization_type="rightsizing",
                            effort_level="medium",
                            risk_level="low",
                            implementation_steps=[
                                "1. Creare AMI backup dell'istanza",
                                f"2. Fermare istanza {instance.get('InstanceId')}",
                                f"3. Modificare tipo da {instance_type} a {recommended_type}",
                                "4. Riavviare e monitorare performance"
                            ]
                        ))
        
        # Istanze stopped (spreco completo)
        for instance in stopped_instances:
            instance_type = instance.get("Type", "t3.micro")
            hourly_cost = self.pricing_map['ec2'].get(instance_type, 0.05)
            monthly_cost = hourly_cost * 24 * 30.44
            
            # Le istanze stopped non costano per compute, ma potrebbero avere EBS associati
            # Per ora consideriamo solo il potenziale se fossero accese
            ec2_resources.append({
                "id": instance.get("InstanceId"),
                "name": instance.get("Name"),
                "type": instance_type,
                "state": "stopped",
                "monthly_cost": 0,  # Compute cost
                "potential_cost_if_running": monthly_cost,
                "recommendation": "terminate_if_unused"
            })
            
            # Optimization: terminate se stopped da molto tempo
            if self._is_long_stopped(instance):
                optimization_potential += monthly_cost * 0.1  # Stima risparmio EBS
                
                self.optimizations.append(CostOptimization(
                    resource_id=instance.get("InstanceId"),
                    resource_type="EC2",
                    current_monthly_cost=monthly_cost * 0.1,  # Solo EBS
                    optimized_monthly_cost=0,
                    savings_monthly=monthly_cost * 0.1,
                    optimization_type="termination",
                    effort_level="low",
                    risk_level="medium",
                    implementation_steps=[
                        "1. Verificare che l'istanza non sia più necessaria",
                        "2. Fare backup di dati importanti sui volumi EBS",
                        f"3. Terminare istanza {instance.get('InstanceId')}",
                        "4. Eliminare volumi EBS non più necessari"
                    ]
                ))
        
        self.cost_breakdown.append(CostBreakdown(
            service="EC2",
            monthly_cost=total_ec2_cost,
            annual_cost=total_ec2_cost * 12,
            resources=ec2_resources,
            optimization_potential=optimization_potential,
            criticality="essential"
        ))
        
        self.total_monthly_cost += total_ec2_cost
        self.total_potential_savings += optimization_potential
        
        print(f"   💰 EC2: ${total_ec2_cost:.2f}/month, ${optimization_potential:.2f} potential savings")
    
    async def _analyze_rds_costs(self, audit_data: Dict[str, Any]):
        """Analizza costi RDS"""
        rds_data = audit_data.get("rds_raw", {})
        db_instances = rds_data.get("DBInstances", [])
        db_clusters = rds_data.get("DBClusters", [])
        
        total_rds_cost = 0
        optimization_potential = 0
        rds_resources = []
        
        # DB Instances
        for db in db_instances:
            db_class = db.get("DBInstanceClass", "db.t3.micro")
            engine = db.get("Engine", "mysql")
            multi_az = db.get("MultiAZ", False)
            
            hourly_cost = self.pricing_map['rds'].get(db_class, 0.05)
            if multi_az:
                hourly_cost *= 2  # Multi-AZ doubles cost
            
            monthly_cost = hourly_cost * 24 * 30.44
            total_rds_cost += monthly_cost
            
            # Storage cost
            allocated_storage = db.get("AllocatedStorage", 20)
            storage_type = db.get("StorageType", "gp2")
            storage_cost = allocated_storage * self.pricing_map['storage'].get(storage_type, 0.10)
            monthly_cost += storage_cost
            
            rds_resources.append({
                "id": db.get("DBInstanceIdentifier"),
                "class": db_class,
                "engine": engine,
                "storage_gb": allocated_storage,
                "multi_az": multi_az,
                "monthly_cost": monthly_cost,
                "status": db.get("DBInstanceStatus")
            })
            
            # Optimization: controllare utilizzo
            if self._is_rds_oversized(db):
                smaller_class = self._get_smaller_rds_class(db_class)
                if smaller_class:
                    smaller_cost = self.pricing_map['rds'].get(smaller_class, hourly_cost) * 24 * 30.44
                    if multi_az:
                        smaller_cost *= 2
                    smaller_cost += storage_cost
                    
                    savings = monthly_cost - smaller_cost
                    if savings > 0:
                        optimization_potential += savings
                        
                        self.optimizations.append(CostOptimization(
                            resource_id=db.get("DBInstanceIdentifier"),
                            resource_type="RDS",
                            current_monthly_cost=monthly_cost,
                            optimized_monthly_cost=smaller_cost,
                            savings_monthly=savings,
                            optimization_type="rightsizing",
                            effort_level="medium",
                            risk_level="medium",
                            implementation_steps=[
                                f"1. Monitorare utilizzo CPU/memoria di {db.get('DBInstanceIdentifier')}",
                                "2. Creare snapshot di backup",
                                f"3. Modificare classe da {db_class} a {smaller_class}",
                                "4. Monitorare performance post-modifica"
                            ]
                        ))
        
        # DB Clusters (Aurora)
        for cluster in db_clusters:
            engine = cluster.get("Engine", "aurora")
            cluster_members = cluster.get("DBClusterMembers", [])
            
            cluster_cost = 0
            for member in cluster_members:
                # Aurora pricing is different - estimate based on instances
                cluster_cost += 0.10 * 24 * 30.44  # Base Aurora cost per instance
            
            total_rds_cost += cluster_cost
            
            rds_resources.append({
                "id": cluster.get("DBClusterIdentifier"),
                "type": "aurora_cluster",
                "engine": engine,
                "members": len(cluster_members),
                "monthly_cost": cluster_cost,
                "status": cluster.get("Status")
            })
        
        self.cost_breakdown.append(CostBreakdown(
            service="RDS",
            monthly_cost=total_rds_cost,
            annual_cost=total_rds_cost * 12,
            resources=rds_resources,
            optimization_potential=optimization_potential,
            criticality="important"
        ))
        
        self.total_monthly_cost += total_rds_cost
        self.total_potential_savings += optimization_potential
        
        print(f"   💰 RDS: ${total_rds_cost:.2f}/month, ${optimization_potential:.2f} potential savings")
    
    async def _analyze_storage_costs(self, audit_data: Dict[str, Any]):
        """Analizza costi storage (EBS, S3, etc.)"""
        total_storage_cost = 0
        optimization_potential = 0
        storage_resources = []
        
        # EBS Volumes
        ebs_data = audit_data.get("ebs_raw", {})
        volumes = ebs_data.get("volumes", [])
        
        for volume in volumes:
            size_gb = volume.get("Size", 0)
            volume_type = volume.get("VolumeType", "gp2")
            state = volume.get("State", "available")
            
            monthly_cost = size_gb * self.pricing_map['storage'].get(volume_type, 0.10)
            total_storage_cost += monthly_cost
            
            storage_resources.append({
                "id": volume.get("VolumeId"),
                "type": "ebs",
                "size_gb": size_gb,
                "volume_type": volume_type,
                "state": state,
                "monthly_cost": monthly_cost,
                "attached": state == "in-use"
            })
            
            # Optimization: volumi non attaccati
            if state == "available":
                optimization_potential += monthly_cost
                
                self.optimizations.append(CostOptimization(
                    resource_id=volume.get("VolumeId"),
                    resource_type="EBS",
                    current_monthly_cost=monthly_cost,
                    optimized_monthly_cost=0,
                    savings_monthly=monthly_cost,
                    optimization_type="deletion",
                    effort_level="low",
                    risk_level="medium",
                    implementation_steps=[
                        f"1. Verificare che volume {volume.get('VolumeId')} non contenga dati importanti",
                        "2. Creare snapshot se necessario per backup",
                        "3. Eliminare volume non utilizzato"
                    ]
                ))
            
            # Optimization: upgrade gp2 -> gp3
            elif volume_type == "gp2" and size_gb > 100:
                gp3_cost = size_gb * self.pricing_map['storage']['gp3']
                savings = monthly_cost - gp3_cost
                if savings > 0:
                    optimization_potential += savings
                    
                    self.optimizations.append(CostOptimization(
                        resource_id=volume.get("VolumeId"),
                        resource_type="EBS",
                        current_monthly_cost=monthly_cost,
                        optimized_monthly_cost=gp3_cost,
                        savings_monthly=savings,
                        optimization_type="upgrade",
                        effort_level="low",
                        risk_level="low",
                        implementation_steps=[
                            f"1. Modificare tipo volume {volume.get('VolumeId')} da gp2 a gp3",
                            "2. Monitorare performance (gp3 ha prestazioni migliori)"
                        ]
                    ))
        
        # EBS Snapshots
        snapshots_data = audit_data.get("ebs_snapshots_raw", {})
        snapshots = snapshots_data.get("Snapshots", [])
        
        snapshot_storage_gb = 0
        old_snapshots = 0
        
        for snapshot in snapshots:
            # Stima dimensione (non sempre disponibile)
            volume_size = snapshot.get("VolumeSize", 0)
            snapshot_storage_gb += volume_size * 0.5  # Stima: snapshot = 50% del volume
            
            # Check per snapshot vecchi
            start_time = snapshot.get("StartTime")
            if start_time:
                try:
                    if isinstance(start_time, str):
                        start_date = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    else:
                        start_date = start_time
                    
                    days_old = (datetime.now(start_date.tzinfo) - start_date).days
                    if days_old > 90:  # Snapshot più vecchi di 3 mesi
                        old_snapshots += 1
                except:
                    pass
        
        snapshot_cost = snapshot_storage_gb * 0.05  # $0.05/GB/month per snapshot
        total_storage_cost += snapshot_cost
        
        if old_snapshots > 0:
            old_snapshot_cost = old_snapshots * 10  # Stima $10/snapshot vecchio
            optimization_potential += old_snapshot_cost
            
            self.optimizations.append(CostOptimization(
                resource_id="multiple_snapshots",
                resource_type="EBS_Snapshots",
                current_monthly_cost=old_snapshot_cost,
                optimized_monthly_cost=0,
                savings_monthly=old_snapshot_cost,
                optimization_type="cleanup",
                effort_level="low",
                risk_level="low",
                implementation_steps=[
                    f"1. Identificare {old_snapshots} snapshot più vecchi di 90 giorni",
                    "2. Verificare che non siano necessari per compliance",
                    "3. Eliminare snapshot obsoleti",
                    "4. Implementare lifecycle policy automatica"
                ]
            ))
        
        storage_resources.append({
            "type": "ebs_snapshots",
            "total_snapshots": len(snapshots),
            "estimated_gb": snapshot_storage_gb,
            "monthly_cost": snapshot_cost,
            "old_snapshots": old_snapshots
        })
        
        # S3 Storage (stima base)
        s3_data = audit_data.get("s3_audit", {})
        total_buckets = s3_data.get("metadata", {}).get("total_buckets", 0)
        s3_cost = total_buckets * 5  # Stima $5/bucket/month
        total_storage_cost += s3_cost
        
        storage_resources.append({
            "type": "s3",
            "bucket_count": total_buckets,
            "monthly_cost": s3_cost
        })
        
        self.cost_breakdown.append(CostBreakdown(
            service="Storage",
            monthly_cost=total_storage_cost,
            annual_cost=total_storage_cost * 12,
            resources=storage_resources,
            optimization_potential=optimization_potential,
            criticality="essential"
        ))
        
        self.total_monthly_cost += total_storage_cost
        self.total_potential_savings += optimization_potential
        
        print(f"   💰 Storage: ${total_storage_cost:.2f}/month, ${optimization_potential:.2f} potential savings")
    
    async def _analyze_network_costs(self, audit_data: Dict[str, Any]):
        """Analizza costi di rete"""
        total_network_cost = 0
        optimization_potential = 0
        network_resources = []
        
        # NAT Gateways
        nat_gw_data = audit_data.get("nat_gateways_raw", {})
        nat_gateways = nat_gw_data.get("NatGateways", [])
        
        for nat_gw in nat_gateways:
            if nat_gw.get("State") == "available":
                monthly_cost = self.pricing_map['nat_gateway'] * 24 * 30.44
                total_network_cost += monthly_cost
                
                network_resources.append({
                    "id": nat_gw.get("NatGatewayId"),
                    "type": "nat_gateway",
                    "subnet": nat_gw.get("SubnetId"),
                    "monthly_cost": monthly_cost,
                    "state": nat_gw.get("State")
                })
        
        # Load Balancers
        lb_data = audit_data.get("lb_raw", {})
        albs = lb_data.get("ApplicationLoadBalancers", [])
        nlbs = lb_data.get("NetworkLoadBalancers", [])
        clbs = lb_data.get("ClassicLoadBalancers", [])
        
        for alb in albs:
            monthly_cost = self.pricing_map['load_balancer']['alb'] * 24 * 30.44
            total_network_cost += monthly_cost
            
            network_resources.append({
                "id": alb.get("LoadBalancerArn"),
                "type": "application_lb",
                "name": alb.get("LoadBalancerName"),
                "monthly_cost": monthly_cost,
                "scheme": alb.get("Scheme")
            })
            
            # Optimization: verificare utilizzo
            if self._is_lb_underutilized(alb):
                optimization_potential += monthly_cost * 0.5  # Stima risparmio
        
        for nlb in nlbs:
            monthly_cost = self.pricing_map['load_balancer']['nlb'] * 24 * 30.44
            total_network_cost += monthly_cost
            
            network_resources.append({
                "id": nlb.get("LoadBalancerArn"),
                "type": "network_lb",
                "name": nlb.get("LoadBalancerName"),
                "monthly_cost": monthly_cost,
                "scheme": nlb.get("Scheme")
            })
        
        for clb in clbs:
            monthly_cost = self.pricing_map['load_balancer']['clb'] * 24 * 30.44
            total_network_cost += monthly_cost
            
            network_resources.append({
                "id": clb.get("LoadBalancerName"),
                "type": "classic_lb",
                "name": clb.get("LoadBalancerName"),
                "monthly_cost": monthly_cost
            })
            
            # Optimization: migrare CLB a ALB/NLB
            alb_cost = self.pricing_map['load_balancer']['alb'] * 24 * 30.44
            if alb_cost < monthly_cost:
                savings = monthly_cost - alb_cost
                optimization_potential += savings
                
                self.optimizations.append(CostOptimization(
                    resource_id=clb.get("LoadBalancerName"),
                    resource_type="Classic_LB",
                    current_monthly_cost=monthly_cost,
                    optimized_monthly_cost=alb_cost,
                    savings_monthly=savings,
                    optimization_type="migration",
                    effort_level="medium",
                    risk_level="medium",
                    implementation_steps=[
                        f"1. Creare nuovo ALB per sostituire CLB {clb.get('LoadBalancerName')}",
                        "2. Configurare target groups e health checks",
                        "3. Testare nuovo ALB",
                        "4. Aggiornare DNS records",
                        "5. Eliminare CLB"
                    ]
                ))
        
        # Elastic IPs
        eip_data = audit_data.get("eip_raw", {})
        elastic_ips = eip_data.get("Addresses", [])
        
        unassociated_eips = 0
        for eip in elastic_ips:
            if not eip.get("AssociationId"):  # Non associato
                unassociated_eips += 1
        
        if unassociated_eips > 0:
            eip_waste_cost = unassociated_eips * 3.65  # $0.005/ora = ~$3.65/mese per EIP non utilizzato
            total_network_cost += eip_waste_cost
            optimization_potential += eip_waste_cost
            
            network_resources.append({
                "type": "elastic_ips",
                "total_count": len(elastic_ips),
                "unassociated": unassociated_eips,
                "waste_cost": eip_waste_cost
            })
            
            self.optimizations.append(CostOptimization(
                resource_id="unassociated_eips",
                resource_type="Elastic_IP",
                current_monthly_cost=eip_waste_cost,
                optimized_monthly_cost=0,
                savings_monthly=eip_waste_cost,
                optimization_type="cleanup",
                effort_level="low",
                risk_level="low",
                implementation_steps=[
                    f"1. Identificare {unassociated_eips} Elastic IP non associati",
                    "2. Verificare se sono necessari",
                    "3. Rilasciare Elastic IP non utilizzati"
                ]
            ))
        
        self.cost_breakdown.append(CostBreakdown(
            service="Network",
            monthly_cost=total_network_cost,
            annual_cost=total_network_cost * 12,
            resources=network_resources,
            optimization_potential=optimization_potential,
            criticality="important"
        ))
        
        self.total_monthly_cost += total_network_cost
        self.total_potential_savings += optimization_potential
        
        print(f"   💰 Network: ${total_network_cost:.2f}/month, ${optimization_potential:.2f} potential savings")
    
    async def _analyze_lambda_costs(self, audit_data: Dict[str, Any]):
        """Analizza costi Lambda"""
        lambda_data = audit_data.get("lambda_raw", {})
        functions = lambda_data.get("Functions", [])
        
        total_lambda_cost = 0
        optimization_potential = 0
        lambda_resources = []
        
        for func in functions:
            # Stima costi Lambda (difficile senza metriche di invocazione)
            memory_mb = func.get("MemorySize", 128)
            timeout = func.get("Timeout", 3)
            
            # Stima base: 1000 invocazioni al mese
            estimated_invocations = 1000
            estimated_duration_ms = timeout * 1000 * 0.5  # Assume 50% del timeout
            
            # Pricing Lambda: $0.0000166667 per GB-secondo
            gb_seconds = (memory_mb / 1024) * (estimated_duration_ms / 1000) * estimated_invocations
            compute_cost = gb_seconds * 0.0000166667
            
            # Request cost: $0.0000002 per request
            request_cost = estimated_invocations * 0.0000002
            
            monthly_cost = compute_cost + request_cost
            total_lambda_cost += monthly_cost
            
            lambda_resources.append({
                "name": func.get("FunctionName"),
                "runtime": func.get("Runtime"),
                "memory_mb": memory_mb,
                "timeout": timeout,
                "estimated_monthly_cost": monthly_cost,
                "last_modified": func.get("LastModified")
            })
            
            # Optimization: funzioni over-provisioned
            if memory_mb > 512:  # Funzioni con molta memoria potrebbero essere ottimizzabili
                optimized_memory = max(128, memory_mb // 2)
                optimized_cost = monthly_cost * (optimized_memory / memory_mb)
                savings = monthly_cost - optimized_cost
                
                if savings > 1:  # Solo se risparmio > $1/mese
                    optimization_potential += savings
                    
                    self.optimizations.append(CostOptimization(
                        resource_id=func.get("FunctionName"),
                        resource_type="Lambda",
                        current_monthly_cost=monthly_cost,
                        optimized_monthly_cost=optimized_cost,
                        savings_monthly=savings,
                        optimization_type="rightsizing",
                        effort_level="low",
                        risk_level="low",
                        implementation_steps=[
                            f"1. Monitorare utilizzo memoria di {func.get('FunctionName')}",
                            f"2. Test con memoria ridotta ({optimized_memory}MB)",
                            "3. Aggiornare configurazione se performance OK"
                        ]
                    ))
        
        self.cost_breakdown.append(CostBreakdown(
            service="Lambda",
            monthly_cost=total_lambda_cost,
            annual_cost=total_lambda_cost * 12,
            resources=lambda_resources,
            optimization_potential=optimization_potential,
            criticality="optional"
        ))
        
        self.total_monthly_cost += total_lambda_cost
        self.total_potential_savings += optimization_potential
        
        print(f"   💰 Lambda: ${total_lambda_cost:.2f}/month, ${optimization_potential:.2f} potential savings")
    
    async def _analyze_container_costs(self, audit_data: Dict[str, Any]):
        """Analizza costi ECS/EKS"""
        containers_data = audit_data.get("containers_raw", {})
        ecs_data = containers_data.get("ECS", {})
        eks_data = containers_data.get("EKS", {})
        
        total_container_cost = 0
        optimization_potential = 0
        container_resources = []
        
        # ECS Clusters
        ecs_clusters = ecs_data.get("Clusters", [])
        for cluster in ecs_clusters:
            # ECS costi sono principalmente dalle istanze EC2 sottostanti
            # Stima base per cluster attivo
            monthly_cost = 50  # Stima per overhead ECS
            total_container_cost += monthly_cost
            
            container_resources.append({
                "name": cluster.get("clusterName"),
                "type": "ecs_cluster",
                "status": cluster.get("status"),
                "active_services": cluster.get("activeServicesCount", 0),
                "running_tasks": cluster.get("runningTasksCount", 0),
                "estimated_monthly_cost": monthly_cost
            })
        
        # EKS Clusters
        eks_clusters = eks_data.get("Clusters", [])
        for cluster in eks_clusters:
            # EKS ha costo fisso per control plane
            control_plane_cost = 73  # $0.10/ora = ~$73/mese per control plane
            
            # Stima costi node groups (se disponibili)
            node_groups = eks_data.get("NodeGroups", [])
            node_group_cost = 0
            
            cluster_name = cluster.get("name")
            cluster_node_groups = [ng for ng in node_groups if ng.get("clusterName") == cluster_name]
            
            for ng in cluster_node_groups:
                # Stima basata su tipo istanza del node group
                instance_types = ng.get("instanceTypes", ["t3.medium"])
                desired_size = ng.get("scalingConfig", {}).get("desiredSize", 1)
                
                for instance_type in instance_types:
                    instance_cost = self.pricing_map['ec2'].get(instance_type, 0.05) * 24 * 30.44
                    node_group_cost += instance_cost * desired_size
            
            total_cluster_cost = control_plane_cost + node_group_cost
            total_container_cost += total_cluster_cost
            
            container_resources.append({
                "name": cluster_name,
                "type": "eks_cluster",
                "status": cluster.get("status"),
                "version": cluster.get("version"),
                "node_groups": len(cluster_node_groups),
                "control_plane_cost": control_plane_cost,
                "node_groups_cost": node_group_cost,
                "total_monthly_cost": total_cluster_cost
            })
            
            # Optimization: cluster sottoutilizzati
            if node_group_cost > 500 and len(cluster_node_groups) > 2:
                # Cluster costoso con molti node groups - possibile ottimizzazione
                potential_savings = node_group_cost * 0.3  # Stima 30% risparmio
                optimization_potential += potential_savings
                
                self.optimizations.append(CostOptimization(
                    resource_id=cluster_name,
                    resource_type="EKS",
                    current_monthly_cost=total_cluster_cost,
                    optimized_monthly_cost=total_cluster_cost - potential_savings,
                    savings_monthly=potential_savings,
                    optimization_type="consolidation",
                    effort_level="high",
                    risk_level="medium",
                    implementation_steps=[
                        f"1. Analizzare utilizzo cluster EKS {cluster_name}",
                        "2. Considerare consolidamento node groups",
                        "3. Implementare Cluster Autoscaler",
                        "4. Valutare Spot Instances per workload non critici"
                    ]
                ))
        
        self.cost_breakdown.append(CostBreakdown(
            service="Containers",
            monthly_cost=total_container_cost,
            annual_cost=total_container_cost * 12,
            resources=container_resources,
            optimization_potential=optimization_potential,
            criticality="important"
        ))
        
        self.total_monthly_cost += total_container_cost
        self.total_potential_savings += optimization_potential
        
        print(f"   💰 Containers: ${total_container_cost:.2f}/month, ${optimization_potential:.2f} potential savings")
    
    async def _analyze_data_transfer_costs(self, audit_data: Dict[str, Any]):
        """Analizza costi di data transfer"""
        # Data transfer è difficile da stimare senza CloudWatch metrics
        # Facciamo una stima basata sulla configurazione
        
        total_transfer_cost = 0
        optimization_potential = 0
        transfer_resources = []
        
        # Stima basata su NAT Gateways (indicatore di traffico)
        nat_gw_data = audit_data.get("nat_gateways_raw", {})
        nat_gateways = nat_gw_data.get("NatGateways", [])
        
        active_nat_gws = len([ng for ng in nat_gateways if ng.get("State") == "available"])
        
        if active_nat_gws > 0:
            # Stima: $0.045/GB processato + $0.09/GB out to internet
            estimated_gb_per_month = active_nat_gws * 100  # 100GB per NAT GW
            processing_cost = estimated_gb_per_month * 0.045
            transfer_cost = estimated_gb_per_month * 0.09
            
            total_transfer_cost = processing_cost + transfer_cost
            
            transfer_resources.append({
                "type": "nat_gateway_data_processing",
                "nat_gateways": active_nat_gws,
                "estimated_gb": estimated_gb_per_month,
                "monthly_cost": total_transfer_cost
            })
            
            # Optimization: VPC Endpoints possono ridurre data transfer
            vpc_endpoints_data = audit_data.get("vpc_endpoints_raw", {})
            endpoints = vpc_endpoints_data.get("VpcEndpoints", [])
            
            s3_endpoints = len([ep for ep in endpoints if "s3" in ep.get("ServiceName", "")])
            
            if s3_endpoints == 0 and active_nat_gws > 0:
                # Nessun S3 VPC endpoint ma NAT Gateway presente
                potential_savings = total_transfer_cost * 0.2  # Stima 20% risparmio
                optimization_potential += potential_savings
                
                self.optimizations.append(CostOptimization(
                    resource_id="vpc_endpoints_s3",
                    resource_type="Data_Transfer",
                    current_monthly_cost=total_transfer_cost,
                    optimized_monthly_cost=total_transfer_cost - potential_savings,
                    savings_monthly=potential_savings,
                    optimization_type="vpc_endpoint",
                    effort_level="low",
                    risk_level="low",
                    implementation_steps=[
                        "1. Creare VPC Endpoint per S3",
                        "2. Aggiornare route tables per usare VPC endpoint",
                        "3. Monitorare riduzione traffico NAT Gateway"
                    ]
                ))
        
        # CloudFront usage (riduce data transfer costs)
        cloudfront_data = audit_data.get("cloudfront_raw", {})
        distributions = cloudfront_data.get("Distributions", [])
        
        if len(distributions) == 0:
            # Nessuna CloudFront ma possibili benefici
            s3_data = audit_data.get("s3_audit", {})
            public_buckets = s3_data.get("public_buckets", [])
            
            if len(public_buckets) > 0:
                estimated_savings = 20  # $20/mese stima per CDN
                optimization_potential += estimated_savings
                
                self.optimizations.append(CostOptimization(
                    resource_id="cloudfront_cdn",
                    resource_type="Data_Transfer",
                    current_monthly_cost=0,
                    optimized_monthly_cost=-estimated_savings,
                    savings_monthly=estimated_savings,
                    optimization_type="cdn_implementation",
                    effort_level="medium",
                    risk_level="low",
                    implementation_steps=[
                        "1. Configurare CloudFront distribution",
                        "2. Puntare a bucket S3 pubblici",
                        "3. Aggiornare DNS per usare CloudFront",
                        "4. Monitorare riduzione costi data transfer"
                    ]
                ))
        
        self.cost_breakdown.append(CostBreakdown(
            service="Data_Transfer",
            monthly_cost=total_transfer_cost,
            annual_cost=total_transfer_cost * 12,
            resources=transfer_resources,
            optimization_potential=optimization_potential,
            criticality="optional"
        ))
        
        self.total_monthly_cost += total_transfer_cost
        self.total_potential_savings += optimization_potential
        
        print(f"   💰 Data Transfer: ${total_transfer_cost:.2f}/month, ${optimization_potential:.2f} potential savings")
    
    async def _analyze_monitoring_costs(self, audit_data: Dict[str, Any]):
        """Analizza costi CloudWatch e monitoring"""
        cloudwatch_data = audit_data.get("cloudwatch_raw", {})
        alarms = cloudwatch_data.get("Alarms", [])
        dashboards = cloudwatch_data.get("Dashboards", [])
        custom_metrics = cloudwatch_data.get("CustomMetrics", [])
        log_groups = cloudwatch_data.get("LogGroups", [])
        
        total_monitoring_cost = 0
        optimization_potential = 0
        monitoring_resources = []
        
        # CloudWatch Alarms
        alarm_count = len(alarms)
        free_alarms = 10
        paid_alarms = max(0, alarm_count - free_alarms)
        alarm_cost = paid_alarms * self.pricing_map['cloudwatch']['alarms']
        
        # CloudWatch Dashboards
        dashboard_count = len(dashboards)
        free_dashboards = 3
        paid_dashboards = max(0, dashboard_count - free_dashboards)
        dashboard_cost = paid_dashboards * self.pricing_map['cloudwatch']['dashboards']
        
        # Custom Metrics
        custom_metric_count = len(custom_metrics)
        free_metrics = 10000
        paid_metrics = max(0, custom_metric_count - free_metrics)
        metrics_cost = paid_metrics * self.pricing_map['cloudwatch']['custom_metrics']
        
        # Log Groups (stima storage)
        total_log_storage_gb = 0
        old_log_groups = 0
        
        for log_group in log_groups:
            stored_bytes = log_group.get("storedBytes", 0)
            storage_gb = stored_bytes / (1024**3)
            total_log_storage_gb += storage_gb
            
            # Check retention policy
            retention_days = log_group.get("retentionInDays")
            if not retention_days:  # Retention infinita
                old_log_groups += 1
        
        log_storage_cost = total_log_storage_gb * 0.50  # $0.50/GB/month
        
        total_monitoring_cost = alarm_cost + dashboard_cost + metrics_cost + log_storage_cost
        
        monitoring_resources.extend([
            {
                "type": "cloudwatch_alarms",
                "total_count": alarm_count,
                "free_tier": free_alarms,
                "paid_count": paid_alarms,
                "monthly_cost": alarm_cost
            },
            {
                "type": "cloudwatch_dashboards",
                "total_count": dashboard_count,
                "free_tier": free_dashboards,
                "paid_count": paid_dashboards,
                "monthly_cost": dashboard_cost
            },
            {
                "type": "custom_metrics",
                "total_count": custom_metric_count,
                "free_tier": free_metrics,
                "paid_count": paid_metrics,
                "monthly_cost": metrics_cost
            },
            {
                "type": "log_storage",
                "total_gb": total_log_storage_gb,
                "log_groups": len(log_groups),
                "groups_without_retention": old_log_groups,
                "monthly_cost": log_storage_cost
            }
        ])
        
        # Optimization: Log Groups senza retention
        if old_log_groups > 0:
            estimated_savings = old_log_groups * 5  # $5/log group senza retention
            optimization_potential += estimated_savings
            
            self.optimizations.append(CostOptimization(
                resource_id="log_retention_policy",
                resource_type="CloudWatch_Logs",
                current_monthly_cost=estimated_savings,
                optimized_monthly_cost=0,
                savings_monthly=estimated_savings,
                optimization_type="retention_policy",
                effort_level="low",
                risk_level="low",
                implementation_steps=[
                    f"1. Identificare {old_log_groups} log groups senza retention policy",
                    "2. Impostare retention appropriata (es. 30-90 giorni)",
                    "3. Considerare export a S3 per long-term storage"
                ]
            ))
        
        # Optimization: Alarms inutili
        if alarm_count > 20:
            # Molti alarms potrebbero indicare configurazione non ottimale
            estimated_cleanup = alarm_count * 0.2  # 20% degli alarms potrebbe essere ridondante
            alarm_savings = estimated_cleanup * self.pricing_map['cloudwatch']['alarms']
            
            if alarm_savings > 5:  # Solo se risparmio significativo
                optimization_potential += alarm_savings
                
                self.optimizations.append(CostOptimization(
                    resource_id="cloudwatch_alarms_cleanup",
                    resource_type="CloudWatch_Alarms",
                    current_monthly_cost=alarm_cost,
                    optimized_monthly_cost=alarm_cost - alarm_savings,
                    savings_monthly=alarm_savings,
                    optimization_type="cleanup",
                    effort_level="medium",
                    risk_level="low",
                    implementation_steps=[
                        f"1. Analizzare {alarm_count} CloudWatch alarms",
                        "2. Identificare alarms duplicati o non necessari",
                        "3. Consolidare alarms simili",
                        "4. Eliminare alarms per risorse terminate"
                    ]
                ))
        
        self.cost_breakdown.append(CostBreakdown(
            service="Monitoring",
            monthly_cost=total_monitoring_cost,
            annual_cost=total_monitoring_cost * 12,
            resources=monitoring_resources,
            optimization_potential=optimization_potential,
            criticality="important"
        ))
        
        self.total_monthly_cost += total_monitoring_cost
        self.total_potential_savings += optimization_potential
        
        print(f"   💰 Monitoring: ${total_monitoring_cost:.2f}/month, ${optimization_potential:.2f} potential savings")
    
    async def _fetch_historical_costs(self) -> Dict[str, Any]:
        """Fetch dati storici da Cost Explorer"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # Ultimi 3 mesi
            
            # Get monthly costs
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            monthly_data = []
            for result in response['ResultsByTime']:
                month_data = {
                    'month': result['TimePeriod']['Start'],
                    'total_cost': float(result['Total']['BlendedCost']['Amount']),
                    'services': {}
                }
                
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    month_data['services'][service] = cost
                
                monthly_data.append(month_data)
            
            # Calculate trends
            if len(monthly_data) >= 2:
                latest_month = monthly_data[-1]['total_cost']
                previous_month = monthly_data[-2]['total_cost']
                month_over_month = ((latest_month - previous_month) / previous_month) * 100 if previous_month > 0 else 0
            else:
                month_over_month = 0
            
            return {
                'monthly_data': monthly_data,
                'trend_analysis': {
                    'month_over_month_change': month_over_month,
                    'average_monthly_cost': sum(m['total_cost'] for m in monthly_data) / len(monthly_data) if monthly_data else 0
                }
            }
            
        except Exception as e:
            print(f"   ⚠️  Could not fetch historical data: {e}")
            return {'monthly_data': [], 'trend_analysis': {}}
    
    def _generate_optimization_recommendations(self):
        """Genera raccomandazioni di ottimizzazione aggiuntive"""
        # Raggruppa ottimizzazioni per tipo
        optimization_types = {}
        for opt in self.optimizations:
            opt_type = opt.optimization_type
            if opt_type not in optimization_types:
                optimization_types[opt_type] = []
            optimization_types[opt_type].append(opt)
        
        # Genera raccomandazioni di alto livello
        if 'rightsizing' in optimization_types and len(optimization_types['rightsizing']) > 3:
            # Molte opportunità di rightsizing - raccomandazione strategica
            total_rightsizing_savings = sum(opt.savings_monthly for opt in optimization_types['rightsizing'])
            
            self.optimizations.append(CostOptimization(
                resource_id="strategic_rightsizing",
                resource_type="Strategy",
                current_monthly_cost=0,
                optimized_monthly_cost=0,
                savings_monthly=total_rightsizing_savings,
                optimization_type="strategic",
                effort_level="high",
                risk_level="low",
                implementation_steps=[
                    "1. Implementare monitoring automatico delle risorse",
                    "2. Configurare CloudWatch per tracking utilizzo",
                    "3. Implementare policy di rightsizing automatico",
                    "4. Schedulare review mensili delle risorse"
                ]
            ))
    
    def _calculate_optimization_roi(self) -> Dict[str, Any]:
        """Calcola ROI delle ottimizzazioni"""
        total_annual_savings = self.total_potential_savings * 12
        
        # Stima effort costs (tempo ingegnere)
        effort_costs = {
            'low': 2,      # 2 ore
            'medium': 8,   # 1 giorno
            'high': 40     # 1 settimana
        }
        
        hourly_rate = 100  # $100/ora per ingegnere
        
        total_implementation_cost = 0
        roi_by_optimization = []
        
        for opt in self.optimizations:
            effort_hours = effort_costs.get(opt.effort_level, 8)
            implementation_cost = effort_hours * hourly_rate
            annual_savings = opt.savings_monthly * 12
            
            roi = ((annual_savings - implementation_cost) / implementation_cost * 100) if implementation_cost > 0 else float('inf')
            payback_months = implementation_cost / opt.savings_monthly if opt.savings_monthly > 0 else float('inf')
            
            roi_by_optimization.append({
                'resource_id': opt.resource_id,
                'annual_savings': annual_savings,
                'implementation_cost': implementation_cost,
                'roi_percentage': roi,
                'payback_months': payback_months,
                'effort_level': opt.effort_level
            })
            
            total_implementation_cost += implementation_cost
        
        overall_roi = ((total_annual_savings - total_implementation_cost) / total_implementation_cost * 100) if total_implementation_cost > 0 else float('inf')
        
        return {
            'total_annual_savings': total_annual_savings,
            'total_implementation_cost': total_implementation_cost,
            'overall_roi_percentage': overall_roi,
            'optimizations_roi': sorted(roi_by_optimization, key=lambda x: x['roi_percentage'], reverse=True)
        }
    
    def _identify_quick_wins(self) -> List[Dict]:
        """Identifica quick wins (basso effort, alto impatto)"""
        quick_wins = []
        
        for opt in self.optimizations:
            if opt.effort_level == 'low' and opt.savings_monthly > 10:
                quick_wins.append({
                    'resource_id': opt.resource_id,
                    'resource_type': opt.resource_type,
                    'monthly_savings': opt.savings_monthly,
                    'annual_savings': opt.savings_monthly * 12,
                    'optimization_type': opt.optimization_type,
                    'implementation_steps': opt.implementation_steps
                })
        
        return sorted(quick_wins, key=lambda x: x['monthly_savings'], reverse=True)[:10]
    
    def _generate_cost_alerts(self) -> List[Dict]:
        """Genera alert sui costi"""
        alerts = []
        
        # Alert se costo mensile > $1000
        if self.total_monthly_cost > 1000:
            alerts.append({
                'level': 'warning',
                'message': f'Monthly cost (${self.total_monthly_cost:.2f}) exceeds $1000',
                'recommendation': 'Review high-cost resources and implement optimizations'
            })
        
        # Alert se potential savings > 20%
        savings_percentage = (self.total_potential_savings / max(self.total_monthly_cost, 1)) * 100
        if savings_percentage > 20:
            alerts.append({
                'level': 'info',
                'message': f'High optimization potential: {savings_percentage:.1f}% savings available',
                'recommendation': 'Prioritize quick wins and low-risk optimizations'
            })
        
        # Alert per specific waste patterns
        for breakdown in self.cost_breakdown:
            if breakdown.service == "Storage" and breakdown.optimization_potential > breakdown.monthly_cost * 0.3:
                alerts.append({
                    'level': 'warning',
                    'message': 'Significant storage waste detected',
                    'recommendation': 'Review unattached volumes and old snapshots'
                })
        
        return alerts
    
    def _generate_recommendations_summary(self) -> Dict[str, Any]:
        """Genera summary delle raccomandazioni"""
        optimization_count_by_type = {}
        savings_by_type = {}
        
        for opt in self.optimizations:
            opt_type = opt.optimization_type
            optimization_count_by_type[opt_type] = optimization_count_by_type.get(opt_type, 0) + 1
            savings_by_type[opt_type] = savings_by_type.get(opt_type, 0) + opt.savings_monthly
        
        return {
            'total_optimizations': len(self.optimizations),
            'optimization_types': optimization_count_by_type,
            'savings_by_type': savings_by_type,
            'top_optimization_type': max(savings_by_type.items(), key=lambda x: x[1])[0] if savings_by_type else None,
            'implementation_priority': self._calculate_implementation_priority()
        }
    
    def _calculate_implementation_priority(self) -> List[str]:
        """Calcola ordine di priorità implementazione"""
        # Ordina per ROI e facilità di implementazione
        priority_score = []
        
        for opt in self.optimizations:
            effort_score = {'low': 3, 'medium': 2, 'high': 1}[opt.effort_level]
            savings_score = min(opt.savings_monthly / 10, 10)  # Normalizza savings
            risk_score = {'low': 3, 'medium': 2, 'high': 1}[opt.risk_level]
            
            total_score = effort_score + savings_score + risk_score
            priority_score.append((opt.resource_id, total_score))
        
        # Ordina per score decrescente
        priority_score.sort(key=lambda x: x[1], reverse=True)
        
        return [item[0] for item in priority_score[:20]]  # Top 20
    
    # Helper methods
    def _breakdown_to_dict(self, breakdown: CostBreakdown) -> Dict:
        return {
            'service': breakdown.service,
            'monthly_cost': breakdown.monthly_cost,
            'annual_cost': breakdown.annual_cost,
            'resources': breakdown.resources,
            'optimization_potential': breakdown.optimization_potential,
            'criticality': breakdown.criticality
        }
    
    def _optimization_to_dict(self, opt: CostOptimization) -> Dict:
        return {
            'resource_id': opt.resource_id,
            'resource_type': opt.resource_type,
            'current_monthly_cost': opt.current_monthly_cost,
            'optimized_monthly_cost': opt.optimized_monthly_cost,
            'savings_monthly': opt.savings_monthly,
            'savings_annual': opt.savings_monthly * 12,
            'optimization_type': opt.optimization_type,
            'effort_level': opt.effort_level,
            'risk_level': opt.risk_level,
            'implementation_steps': opt.implementation_steps
        }
    
    def _is_rightsizing_candidate(self, instance: Dict) -> bool:
        """Determina se istanza è candidata per rightsizing"""
        instance_type = instance.get("Type", "")
        
        # Istanze grandi senza monitoring dettagliato sono candidate
        large_families = ["m5.large", "m5.xlarge", "c5.large", "c5.xlarge", "r5.large", "r5.xlarge"]
        return instance_type in large_families
    
    def _get_recommended_instance_type(self, current_type: str) -> str:
        """Ottieni tipo istanza raccomandato"""
        rightsizing_map = {
            "m5.xlarge": "m5.large",
            "m5.large": "t3.large",
            "c5.xlarge": "c5.large", 
            "c5.large": "t3.large",
            "r5.xlarge": "r5.large",
            "r5.large": "m5.large",
            "t3.large": "t3.medium",
            "t3.medium": "t3.small"
        }
        return rightsizing_map.get(current_type, current_type)
    
    def _is_long_stopped(self, instance: Dict) -> bool:
        """Verifica se istanza è stopped da molto tempo"""
        # Implementare parsing StateTransitionReason
        return True  # Placeholder
    
    def _is_rds_oversized(self, db: Dict) -> bool:
        """Verifica se database RDS è oversized"""
        db_class = db.get("DBInstanceClass", "")
        # DB grandi sono candidati per rightsizing
        return any(size in db_class for size in ["large", "xlarge", "2xlarge"])
    
    def _get_smaller_rds_class(self, current_class: str) -> Optional[str]:
        """Ottieni classe RDS più piccola"""
        downsize_map = {
            "db.m5.xlarge": "db.m5.large",
            "db.m5.large": "db.t3.large",
            "db.t3.large": "db.t3.medium",
            "db.t3.medium": "db.t3.small",
            "db.r5.xlarge": "db.r5.large",
            "db.r5.large": "db.m5.large"
        }
        return downsize_map.get(current_class)
    
    def _is_lb_underutilized(self, lb: Dict) -> bool:
        """Verifica se Load Balancer è sottoutilizzato"""
        # Placeholder - richiederebbe metriche CloudWatch
        return False
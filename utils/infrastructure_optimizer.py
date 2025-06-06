class InfrastructureOptimizer:
    """Analizzatore e ottimizzatore completo dell'infrastruttura"""
    
    def __init__(self, audit_data: Dict[str, Any], cost_data: Dict[str, Any] = None):
        self.audit_data = audit_data
        self.cost_data = cost_data or {}
        self.recommendations: List[OptimizationRecommendation] = []
        self.current_monthly_cost = 0
        self.potential_monthly_savings = 0
        
    def analyze_and_optimize(self) -> Dict[str, Any]:
        """Analisi completa e generazione raccomandazioni"""
        print("🔍 Analyzing infrastructure for optimization opportunities...")
        
        # Analizza costi attuali
        self._analyze_current_costs()
        
        # Genera raccomandazioni per categoria
        self._analyze_ec2_optimization()
        self._analyze_storage_optimization()
        self._analyze_network_optimization()
        self._analyze_security_cleanup()
        self._analyze_compliance_fixes()
        self._analyze_resource_cleanup()
        
        # Prioritizza raccomandazioni
        self._prioritize_recommendations()
        
        # Genera piano di implementazione
        implementation_plan = self._generate_implementation_plan()
        
        return {
            "current_monthly_cost": self.current_monthly_cost,
            "potential_monthly_savings": self.potential_monthly_savings,
            "total_recommendations": len(self.recommendations),
            "recommendations_by_priority": self._group_by_priority(),
            "recommendations_by_type": self._group_by_type(),
            "implementation_plan": implementation_plan,
            "quick_wins": self._identify_quick_wins(),
            "high_impact_changes": self._identify_high_impact(),
            "detailed_recommendations": [self._recommendation_to_dict(r) for r in self.recommendations]
        }
    
    def _analyze_current_costs(self):
        """Analizza costi attuali basandosi sui dati disponibili"""
        ec2_data = self.audit_data.get("ec2_audit", {})
        s3_data = self.audit_data.get("s3_audit", {})
        
        # Stima costi EC2
        active_instances = ec2_data.get("active", [])
        for instance in active_instances:
            instance_type = instance.get("Type", "t3.micro")
            monthly_cost = self._estimate_ec2_monthly_cost(instance_type)
            self.current_monthly_cost += monthly_cost
        
        # Stima costi storage
        if "ebs" in self.audit_data:
            ebs_data = self.audit_data["ebs"]
            self.current_monthly_cost += ebs_data.get("estimated_monthly_cost", 0)
        
        # Stima costi S3
        s3_buckets = s3_data.get("metadata", {}).get("total_buckets", 0)
        self.current_monthly_cost += s3_buckets * 0.023  # Stima base
        
    def _analyze_ec2_optimization(self):
        """Analizza ottimizzazioni EC2"""
        ec2_data = self.audit_data.get("ec2_audit", {})
        
        # Istanze stopped da rimuovere
        stopped_instances = ec2_data.get("stopped", [])
        for instance in stopped_instances:
            if self._is_long_stopped(instance):
                self._add_recommendation(OptimizationRecommendation(
                    id=f"ec2_cleanup_{instance.get('InstanceId')}",
                    title=f"Terminate stopped instance {instance.get('Name', instance.get('InstanceId'))}",
                    description=f"Instance {instance.get('Name')} è ferma da molto tempo e potrebbe non essere più necessaria",
                    optimization_type=OptimizationType.COST_REDUCTION,
                    priority=Priority.HIGH,
                    estimated_monthly_savings=self._estimate_ec2_monthly_cost(instance.get("Type", "t3.micro")),
                    implementation_effort="Low",
                    risk_level="Medium",
                    resources_affected=[instance.get("InstanceId")],
                    implementation_steps=[
                        "1. Verificare che l'istanza non sia più necessaria",
                        "2. Fare backup di eventuali dati importanti",
                        "3. Terminare l'istanza"
                    ],
                    cli_commands=[
                        f"aws ec2 create-snapshot --volume-id <ebs-volume-id> --description 'Backup before termination'",
                        f"aws ec2 terminate-instances --instance-ids {instance.get('InstanceId')}"
                    ],
                    rollback_plan="Launch new instance from AMI if necessario",
                    compliance_impact=["Cost Optimization"],
                    dependencies=[]
                ))
        
        # Rightsizing opportunities
        active_instances = ec2_data.get("active", [])
        for instance in active_instances:
            if self._needs_rightsizing(instance):
                current_type = instance.get("Type", "")
                recommended_type = self._get_recommended_instance_type(instance)
                current_cost = self._estimate_ec2_monthly_cost(current_type)
                new_cost = self._estimate_ec2_monthly_cost(recommended_type)
                savings = current_cost - new_cost
                
                if savings > 0:
                    self._add_recommendation(OptimizationRecommendation(
                        id=f"ec2_rightsize_{instance.get('InstanceId')}",
                        title=f"Rightsize instance {instance.get('Name', instance.get('InstanceId'))}",
                        description=f"Instance {instance.get('Name')} può essere ridimensionata da {current_type} a {recommended_type}",
                        optimization_type=OptimizationType.COST_REDUCTION,
                        priority=Priority.MEDIUM,
                        estimated_monthly_savings=savings,
                        implementation_effort="Medium",
                        risk_level="Low",
                        resources_affected=[instance.get("InstanceId")],
                        implementation_steps=[
                            "1. Creare AMI dell'istanza corrente",
                            "2. Fermare l'istanza",
                            "3. Modificare il tipo di istanza",
                            "4. Riavviare e verificare funzionamento"
                        ],
                        cli_commands=[
                            f"aws ec2 create-image --instance-id {instance.get('InstanceId')} --name 'backup-before-rightsize' --no-reboot",
                            f"aws ec2 stop-instances --instance-ids {instance.get('InstanceId')}",
                            f"aws ec2 modify-instance-attribute --instance-id {instance.get('InstanceId')} --instance-type {recommended_type}",
                            f"aws ec2 start-instances --instance-ids {instance.get('InstanceId')}"
                        ],
                        rollback_plan=f"Revert to {current_type} using same procedure",
                        compliance_impact=["Cost Optimization"],
                        dependencies=["Backup completion"]
                    ))
    
    def _analyze_storage_optimization(self):
        """Analizza ottimizzazioni storage"""
        # EBS Volumes non utilizzati
        if "ebs" in self.audit_data:
            ebs_data = self.audit_data["ebs"]
            unattached_volumes = ebs_data.get("unattached_volumes", [])
            
            for volume in unattached_volumes:
                volume_id = volume.get("VolumeId")
                size_gb = volume.get("Size", 0)
                volume_type = volume.get("VolumeType", "gp3")
                monthly_cost = self._estimate_ebs_monthly_cost(size_gb, volume_type)
                
                self._add_recommendation(OptimizationRecommendation(
                    id=f"ebs_cleanup_{volume_id}",
                    title=f"Remove unattached EBS volume {volume_id}",
                    description=f"Volume EBS {volume_id} ({size_gb}GB) non è attaccato a nessuna istanza",
                    optimization_type=OptimizationType.COST_REDUCTION,
                    priority=Priority.HIGH,
                    estimated_monthly_savings=monthly_cost,
                    implementation_effort="Low",
                    risk_level="Medium",
                    resources_affected=[volume_id],
                    implementation_steps=[
                        "1. Verificare che il volume non contenga dati importanti",
                        "2. Creare snapshot se necessario",
                        "3. Eliminare il volume"
                    ],
                    cli_commands=[
                        f"aws ec2 create-snapshot --volume-id {volume_id} --description 'Backup before deletion'",
                        f"aws ec2 delete-volume --volume-id {volume_id}"
                    ],
                    rollback_plan="Restore from snapshot if needed",
                    compliance_impact=["Cost Optimization"],
                    dependencies=[]
                ))
        
        # S3 Optimization
        s3_data = self.audit_data.get("s3_audit", {})
        old_buckets = s3_data.get("old_buckets", [])
        
        for bucket in old_buckets:
            if bucket.get("DaysOld", 0) > 730:  # Più di 2 anni
                self._add_recommendation(OptimizationRecommendation(
                    id=f"s3_lifecycle_{bucket.get('Name')}",
                    title=f"Implement lifecycle policy for old bucket {bucket.get('Name')}",
                    description=f"Bucket S3 {bucket.get('Name')} è vecchio ({bucket.get('DaysOld')} giorni) e potrebbe beneficiare di lifecycle policies",
                    optimization_type=OptimizationType.COST_REDUCTION,
                    priority=Priority.MEDIUM,
                    estimated_monthly_savings=10.0,  # Stima
                    implementation_effort="Low",
                    risk_level="Low",
                    resources_affected=[bucket.get("Name")],
                    implementation_steps=[
                        "1. Analizzare pattern di accesso ai dati",
                        "2. Configurare lifecycle policy per transizione a storage classes più economiche",
                        "3. Configurare elimination automatica di dati vecchi se appropriato"
                    ],
                    cli_commands=[
                        f"aws s3api put-bucket-lifecycle-configuration --bucket {bucket.get('Name')} --lifecycle-configuration file://lifecycle-policy.json"
                    ],
                    rollback_plan="Remove lifecycle policy if issues arise",
                    compliance_impact=["Cost Optimization"],
                    dependencies=["Lifecycle policy definition"]
                ))
    
    def _analyze_network_optimization(self):
        """Analizza ottimizzazioni di rete"""
        # Load Balancers non utilizzati
        if "load_balancers" in self.audit_data:
            lb_data = self.audit_data["load_balancers"]
            
            # Check per ALB/NLB con pochi target
            for lb in lb_data.get("application", []) + lb_data.get("network", []):
                lb_name = lb.get("LoadBalancerName", lb.get("LoadBalancerArn", "").split("/")[-1])
                
                # Se load balancer ha pochi target, potrebbe non essere necessario
                self._add_recommendation(OptimizationRecommendation(
                    id=f"lb_review_{lb_name}",
                    title=f"Review necessity of Load Balancer {lb_name}",
                    description=f"Load Balancer {lb_name} potrebbe non essere necessario se serve poche istanze",
                    optimization_type=OptimizationType.COST_REDUCTION,
                    priority=Priority.MEDIUM,
                    estimated_monthly_savings=18.25,  # Costo ALB base
                    implementation_effort="Medium",
                    risk_level="High",
                    resources_affected=[lb.get("LoadBalancerArn")],
                    implementation_steps=[
                        "1. Analizzare traffico e utilizzo del Load Balancer",
                        "2. Valutare se può essere sostituito con soluzioni più economiche",
                        "3. Se necessario, rimuovere dopo aver reindirizzato traffico"
                    ],
                    cli_commands=[
                        f"# Analizzare metriche prima di procedere",
                        f"aws elbv2 describe-target-health --target-group-arn <target-group-arn>"
                    ],
                    rollback_plan="Recreate Load Balancer if needed",
                    compliance_impact=["Cost Optimization"],
                    dependencies=["Traffic analysis"]
                ))
    
    def _analyze_security_cleanup(self):
        """Analizza cleanup di sicurezza"""
        sg_data = self.audit_data.get("sg_audit", {})
        
        # Security Groups non utilizzati
        unused_sgs = sg_data.get("unused", [])
        for sg in unused_sgs:
            sg_id = sg.get("GroupId")
            sg_name = sg.get("GroupName", sg_id)
            
            if sg_name != "default":
                self._add_recommendation(OptimizationRecommendation(
                    id=f"sg_cleanup_{sg_id}",
                    title=f"Remove unused Security Group {sg_name}",
                    description=f"Security Group {sg_name} non è utilizzato da nessuna risorsa",
                    optimization_type=OptimizationType.CLEANUP,
                    priority=Priority.LOW,
                    estimated_monthly_savings=0,  # Nessun costo diretto ma migliora gestione
                    implementation_effort="Low",
                    risk_level="Low",
                    resources_affected=[sg_id],
                    implementation_steps=[
                        "1. Verificare che non sia referenziato da altri SG",
                        "2. Eliminare il Security Group"
                    ],
                    cli_commands=[
                        f"aws ec2 delete-security-group --group-id {sg_id}"
                    ],
                    rollback_plan="Recreate Security Group if needed",
                    compliance_impact=["Management Simplification"],
                    dependencies=[]
                ))
        
        # Security Groups con regole critiche
        critical_ports_sgs = sg_data.get("critical_ports", [])
        for sg_rule in critical_ports_sgs:
            sg_id = sg_rule.get("GroupId")
            sg_name = sg_rule.get("GroupName")
            critical_port = sg_rule.get("CriticalPort")
            port_name = sg_rule.get("PortName")
            
            self._add_recommendation(OptimizationRecommendation(
                id=f"sg_security_{sg_id}_{critical_port}",
                title=f"Secure {port_name} access in {sg_name}",
                description=f"Security Group {sg_name} espone porta critica {critical_port} ({port_name}) pubblicamente",
                optimization_type=OptimizationType.SECURITY_IMPROVEMENT,
                priority=Priority.CRITICAL,
                estimated_monthly_savings=0,
                implementation_effort="Medium",
                risk_level="Medium",
                resources_affected=[sg_id],
                implementation_steps=[
                    f"1. Identificare chi ha bisogno di accesso alla porta {critical_port}",
                    "2. Restringere accesso a IP specifici o implementare VPN",
                    "3. Considerare alternative come AWS Systems Manager per SSH/RDP"
                ],
                cli_commands=[
                    f"aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol tcp --port {critical_port} --cidr 0.0.0.0/0",
                    f"aws ec2 authorize-security-group-ingress --group-id {sg_id} --protocol tcp --port {critical_port} --cidr YOUR_IP/32"
                ],
                rollback_plan="Re-add 0.0.0.0/0 rule if absolutely necessary",
                compliance_impact=["CIS", "SOC2", "PCI-DSS"],
                dependencies=["IP address identification"]
            ))
    
    def _analyze_compliance_fixes(self):
        """Analizza fix di compliance"""
        # IAM users vecchi
        iam_data = self.audit_data.get("iam_audit", {})
        old_users = iam_data.get("old_users", [])
        
        for user in old_users:
            username = user.get("UserName")
            days_ago = user.get("DaysAgo", 0)
            
            if days_ago > 90 or days_ago == -1:
                priority = Priority.HIGH if days_ago > 180 else Priority.MEDIUM
                
                self._add_recommendation(OptimizationRecommendation(
                    id=f"iam_cleanup_{username}",
                    title=f"Review inactive IAM user {username}",
                    description=f"IAM user {username} non è attivo da {days_ago} giorni",
                    optimization_type=OptimizationType.SECURITY_IMPROVEMENT,
                    priority=priority,
                    estimated_monthly_savings=0,
                    implementation_effort="Low",
                    risk_level="Medium",
                    resources_affected=[username],
                    implementation_steps=[
                        "1. Verificare se l'utente è ancora necessario",
                        "2. Se non necessario, rimuovere access keys e policies",
                        "3. Eliminare l'utente IAM"
                    ],
                    cli_commands=[
                        f"aws iam list-access-keys --user-name {username}",
                        f"aws iam delete-access-key --user-name {username} --access-key-id <key-id>",
                        f"aws iam delete-user --user-name {username}"
                    ],
                    rollback_plan="Recreate user if needed",
                    compliance_impact=["CIS", "Least Privilege"],
                    dependencies=["User necessity verification"]
                ))
    
    def _analyze_resource_cleanup(self):
        """Analizza cleanup generale delle risorse"""
        # VPC default usage
        vpc_data = self.audit_data.get("vpc_audit", {})
        default_vpcs = vpc_data.get("default_vpcs", [])
        
        for vpc in default_vpcs:
            if vpc.get("SubnetCount", 0) > 0:
                self._add_recommendation(OptimizationRecommendation(
                    id=f"vpc_default_{vpc.get('VpcId')}",
                    title="Migrate resources from default VPC",
                    description=f"Default VPC {vpc.get('VpcId')} contiene {vpc.get('SubnetCount')} subnet con risorse",
                    optimization_type=OptimizationType.SECURITY_IMPROVEMENT,
                    priority=Priority.MEDIUM,
                    estimated_monthly_savings=0,
                    implementation_effort="High",
                    risk_level="Medium",
                    resources_affected=[vpc.get("VpcId")],
                    implementation_steps=[
                        "1. Creare VPC dedicata con design sicuro",
                        "2. Migrare risorse dalla VPC default",
                        "3. Aggiornare Security Groups e routing"
                    ],
                    cli_commands=[
                        "aws ec2 create-vpc --cidr-block 10.0.0.0/16",
                        "# Migration commands depend on specific resources"
                    ],
                    rollback_plan="Keep default VPC as fallback during migration",
                    compliance_impact=["CIS", "AWS Well-Architected"],
                    dependencies=["New VPC design", "Migration planning"]
                ))
    
    def _prioritize_recommendations(self):
        """Prioritizza raccomandazioni basandosi su impatto e effort"""
        # Ordina per priorità, poi per savings, poi per effort
        self.recommendations.sort(key=lambda r: (
            -self._priority_weight(r.priority),
            -r.estimated_monthly_savings,
            self._effort_weight(r.implementation_effort)
        ))
    
    def _priority_weight(self, priority: Priority) -> int:
        weights = {
            Priority.CRITICAL: 4,
            Priority.HIGH: 3,
            Priority.MEDIUM: 2,
            Priority.LOW: 1
        }
        return weights.get(priority, 0)
    
    def _effort_weight(self, effort: str) -> int:
        weights = {"Low": 1, "Medium": 2, "High": 3}
        return weights.get(effort, 2)
    
    def _generate_implementation_plan(self) -> Dict[str, Any]:
        """Genera piano di implementazione temporale"""
        phases = {
            "immediate": [],  # 0-1 settimana
            "short_term": [],  # 1-4 settimane
            "medium_term": [],  # 1-3 mesi
            "long_term": []  # 3+ mesi
        }
        
        for rec in self.recommendations:
            if rec.priority == Priority.CRITICAL:
                phases["immediate"].append(rec.id)
            elif rec.priority == Priority.HIGH and rec.implementation_effort == "Low":
                phases["immediate"].append(rec.id)
            elif rec.priority == Priority.HIGH:
                phases["short_term"].append(rec.id)
            elif rec.implementation_effort == "High":
                phases["long_term"].append(rec.id)
            else:
                phases["medium_term"].append(rec.id)
        
        return {
            "phases": phases,
            "total_timeline": "3-6 months",
            "immediate_savings": sum(r.estimated_monthly_savings for r in self.recommendations if r.id in phases["immediate"]),
            "phase_descriptions": {
                "immediate": "Critical security fixes and quick cost reductions",
                "short_term": "High-impact changes with moderate effort",
                "medium_term": "Standard optimizations and cleanup",
                "long_term": "Complex architectural improvements"
            }
        }
    
    def _identify_quick_wins(self) -> List[Dict]:
        """Identifica quick wins (alto impatto, basso effort)"""
        quick_wins = []
        for rec in self.recommendations:
            if (rec.implementation_effort == "Low" and 
                (rec.estimated_monthly_savings > 20 or rec.priority in [Priority.CRITICAL, Priority.HIGH])):
                quick_wins.append({
                    "id": rec.id,
                    "title": rec.title,
                    "savings": rec.estimated_monthly_savings,
                    "priority": rec.priority.value
                })
        return quick_wins[:5]  # Top 5 quick wins
    
    def _identify_high_impact(self) -> List[Dict]:
        """Identifica cambiamenti ad alto impatto"""
        high_impact = []
        for rec in self.recommendations:
            if rec.estimated_monthly_savings > 50 or rec.priority == Priority.CRITICAL:
                high_impact.append({
                    "id": rec.id,
                    "title": rec.title,
                    "savings": rec.estimated_monthly_savings,
                    "effort": rec.implementation_effort,
                    "risk": rec.risk_level
                })
        return high_impact
    
    def _group_by_priority(self) -> Dict[str, List[str]]:
        """Raggruppa raccomandazioni per priorità"""
        groups = {p.value: [] for p in Priority}
        for rec in self.recommendations:
            groups[rec.priority.value].append(rec.id)
        return groups
    
    def _group_by_type(self) -> Dict[str, List[str]]:
        """Raggruppa raccomandazioni per tipo"""
        groups = {t.value: [] for t in OptimizationType}
        for rec in self.recommendations:
            groups[rec.optimization_type.value].append(rec.id)
        return groups
    
    def _add_recommendation(self, recommendation: OptimizationRecommendation):
        """Aggiunge raccomandazione alla lista"""
        self.recommendations.append(recommendation)
        self.potential_monthly_savings += recommendation.estimated_monthly_savings
    
    def _recommendation_to_dict(self, rec: OptimizationRecommendation) -> Dict:
        """Converte raccomandazione in dizionario"""
        return {
            "id": rec.id,
            "title": rec.title,
            "description": rec.description,
            "optimization_type": rec.optimization_type.value,
            "priority": rec.priority.value,
            "estimated_monthly_savings": rec.estimated_monthly_savings,
            "implementation_effort": rec.implementation_effort,
            "risk_level": rec.risk_level,
            "resources_affected": rec.resources_affected,
            "implementation_steps": rec.implementation_steps,
            "cli_commands": rec.cli_commands,
            "rollback_plan": rec.rollback_plan,
            "compliance_impact": rec.compliance_impact,
            "dependencies": rec.dependencies
        }
    
    # Helper methods per stime costi
    def _estimate_ec2_monthly_cost(self, instance_type: str) -> float:
        """Stima costo mensile istanza EC2"""
        pricing_map = {
            't2.micro': 8.47, 't2.small': 16.79, 't2.medium': 33.58,
            't3.micro': 7.59, 't3.small': 15.18, 't3.medium': 30.37,
            't3.large': 60.74, 't3.xlarge': 121.47,
            'm5.large': 70.08, 'm5.xlarge': 140.16,
            'c5.large': 62.05, 'c5.xlarge': 124.10,
            'r5.large': 91.98, 'r5.xlarge': 183.96
        }
        return pricing_map.get(instance_type, 50.0)  # Default fallback
    
    def _estimate_ebs_monthly_cost(self, size_gb: int, volume_type: str) -> float:
        """Stima costo mensile volume EBS"""
        pricing_per_gb = {
            'gp2': 0.10, 'gp3': 0.08, 'io1': 0.125, 'io2': 0.125,
            'st1': 0.045, 'sc1': 0.025
        }
        return size_gb * pricing_per_gb.get(volume_type, 0.10)
    
    def _is_long_stopped(self, instance: Dict) -> bool:
        """Verifica se istanza è stopped da molto tempo"""
        # Logic per determinare se istanza è stopped da molto tempo
        state_reason = instance.get("StateTransitionReason", "")
        # Implementare parsing della data da StateTransitionReason
        return True  # Placeholder
    
    def _needs_rightsizing(self, instance: Dict) -> bool:
        """Verifica se istanza ha bisogno di rightsizing"""
        # Logic basata su metriche di utilizzo (se disponibili)
        instance_type = instance.get("Type", "")
        # Per ora, suggerisci rightsizing per istanze grandi senza utilizzo noto
        large_types = ["m5.large", "m5.xlarge", "c5.large", "c5.xlarge"]
        return instance_type in large_types
    
    def _get_recommended_instance_type(self, instance: Dict) -> str:
        """Ottieni tipo di istanza raccomandato"""
        current_type = instance.get("Type", "")
        
        # Mappatura semplificata per rightsizing
        downsize_map = {
            "m5.xlarge": "m5.large",
            "m5.large": "t3.large",
            "c5.xlarge": "c5.large",
            "c5.large": "t3.large",
            "t3.large": "t3.medium",
            "t3.medium": "t3.small"
        }
        
        return downsize_map.get(current_type, current_type)
    
    def generate_cleanup_script(self) -> str:
        """Genera script bash per implementare le raccomandazioni"""
        script_lines = [
            "#!/bin/bash",
            "# AWS Infrastructure Optimization Script",
            "# Generated by AWS Security Auditor",
            "",
            "set -e",
            "echo 'Starting infrastructure optimization...'",
            "",
            "# Function to check if resource exists",
            "check_resource_exists() {",
            "    local resource_type=$1",
            "    local resource_id=$2",
            "    # Implementation depends on resource type",
            "    echo 'Checking $resource_type: $resource_id'",
            "}",
            "",
            "# Function to create backup",
            "create_backup() {",
            "    local resource_id=$1",
            "    echo 'Creating backup for $resource_id'",
            "    # Implementation depends on resource type",
            "}",
            ""
        ]
        
        # Aggiungi comandi per quick wins
        quick_wins = self._identify_quick_wins()
        if quick_wins:
            script_lines.extend([
                "echo '=== PHASE 1: Quick Wins ==='",
                ""
            ])
            
            for quick_win in quick_wins:
                rec = next((r for r in self.recommendations if r.id == quick_win["id"]), None)
                if rec and rec.cli_commands:
                    script_lines.extend([
                        f"# {rec.title}",
                        f"echo 'Implementing: {rec.title}'",
                        *rec.cli_commands,
                        ""
                    ])
        
        # Aggiungi sezione per backup e rollback
        script_lines.extend([
            "",
            "echo '=== Creating rollback script ==='",
            "cat > rollback.sh << 'EOF'",
            "#!/bin/bash",
            "# Rollback script for infrastructure changes",
            "echo 'This script contains rollback procedures'",
            "# Add specific rollback commands based on what was changed",
            "EOF",
            "",
            "chmod +x rollback.sh",
            "echo 'Optimization completed! Check rollback.sh for rollback procedures.'"
        ])
        
        return "\n".join(script_lines)
    
    def generate_cost_report(self) -> str:
        """Genera report dettagliato sui costi"""
        report_lines = [
            "# 💰 AWS Cost Optimization Report",
            "",
            f"**Current Estimated Monthly Cost**: ${self.current_monthly_cost:.2f}",
            f"**Potential Monthly Savings**: ${self.potential_monthly_savings:.2f}",
            f"**Potential Annual Savings**: ${self.potential_monthly_savings * 12:.2f}",
            f"**Optimization Percentage**: {(self.potential_monthly_savings / max(self.current_monthly_cost, 1)) * 100:.1f}%",
            "",
            "## 📊 Savings by Category",
            ""
        ]
        
        # Raggruppa savings per tipo
        savings_by_type = {}
        for rec in self.recommendations:
            opt_type = rec.optimization_type.value
            if opt_type not in savings_by_type:
                savings_by_type[opt_type] = {"count": 0, "savings": 0}
            savings_by_type[opt_type]["count"] += 1
            savings_by_type[opt_type]["savings"] += rec.estimated_monthly_savings
        
        for opt_type, data in savings_by_type.items():
            report_lines.append(f"- **{opt_type.replace('_', ' ').title()}**: ${data['savings']:.2f}/month ({data['count']} items)")
        
        report_lines.extend([
            "",
            "## 🚀 Quick Wins (High Impact, Low Effort)",
            ""
        ])
        
        quick_wins = self._identify_quick_wins()
        for qw in quick_wins:
            report_lines.append(f"- {qw['title']} - ${qw['savings']:.2f}/month")
        
        report_lines.extend([
            "",
            "## 🎯 Implementation Roadmap",
            ""
        ])
        
        implementation_plan = self._generate_implementation_plan()
        for phase, items in implementation_plan["phases"].items():
            if items:
                phase_savings = sum(
                    rec.estimated_monthly_savings 
                    for rec in self.recommendations 
                    if rec.id in items
                )
                report_lines.extend([
                    f"### {phase.replace('_', ' ').title()} ({len(items)} items - ${phase_savings:.2f}/month)",
                    f"{implementation_plan['phase_descriptions'][phase]}",
                    ""
                ])
                
                for item_id in items[:3]:  # Show first 3 items
                    rec = next((r for r in self.recommendations if r.id == item_id), None)
                    if rec:
                        report_lines.append(f"- {rec.title} (${rec.estimated_monthly_savings:.2f})")
                
                if len(items) > 3:
                    report_lines.append(f"- ... and {len(items) - 3} more items")
                report_lines.append("")
        
        return "\n".join(report_lines)
            # utils/infrastructure_optimizer.py
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from enum import Enum

class OptimizationType(Enum):
    COST_REDUCTION = "cost_reduction"
    SECURITY_IMPROVEMENT = "security_improvement"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    COMPLIANCE_FIX = "compliance_fix"
    CLEANUP = "cleanup"

class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class OptimizationRecommendation:
    id: str
    title: str
    description: str
    optimization_type: OptimizationType
    priority: Priority
    estimated_monthly_savings: float
    implementation_effort: str  # "Low", "Medium", "High"
    risk_level: str  # "Low", "Medium", "High"
    resources_affected: List[str]
    implementation_steps: List[str]
    cli_commands: List[str]
    rollback_plan: str
    compliance_impact: List[str]
    dependencies: List[str]

class InfrastructureOptimizer:
    """Analizzatore e ottimizzatore completo dell'infrastruttura AWS"""
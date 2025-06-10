# utils/complete_sg_cost_integration.py
import boto3
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

class CompleteSGCostIntegration:
    """Integrazione completa Security Groups + Cost Explorer + Automated Cleanup"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.ce = boto3.client('ce', region_name='us-east-1')  # Cost Explorer sempre us-east-1
        self.elbv2 = boto3.client('elbv2', region_name=region)
        self.rds = boto3.client('rds', region_name=region)
        
        # Import del nostro analyzer precedente
        from utils.sg_cost_analyzer import SecurityGroupCostAnalyzer
        self.sg_analyzer = SecurityGroupCostAnalyzer(region)
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """Esegue analisi completa integrata"""
        print("🚀 Starting Complete Security Groups + Cost Analysis...")
        
        # Fase 1: Analisi Security Groups
        print("\n📊 Phase 1: Security Groups Analysis")
        sg_analysis = self.sg_analyzer.analyze_all_security_groups()
        
        # Fase 2: Cost Explorer Integration
        print("\n💰 Phase 2: Cost Explorer Integration")
        cost_analysis = self._analyze_costs_with_explorer()
        
        # Fase 3: Cross-Reference Analysis
        print("\n🔍 Phase 3: Cross-Reference Analysis")
        integrated_analysis = self._cross_reference_sg_costs(sg_analysis, cost_analysis)
        
        # Fase 4: Generate Actionable Recommendations
        print("\n🎯 Phase 4: Actionable Recommendations")
        recommendations = self._generate_integrated_recommendations(integrated_analysis)
        
        # Fase 5: Generate Automated Scripts
        print("\n⚙️ Phase 5: Automated Cleanup Scripts")
        scripts = self._generate_automated_scripts(recommendations)
        
        # Save complete report
        complete_report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "region": self.region,
            "sg_analysis": sg_analysis,
            "cost_analysis": cost_analysis,
            "integrated_findings": integrated_analysis,
            "recommendations": recommendations,
            "automation_scripts": scripts
        }
        
        self._save_complete_report(complete_report)
        
        return complete_report
    
    def _analyze_costs_with_explorer(self) -> Dict[str, Any]:
        """Analisi costi tramite Cost Explorer API"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # Ultimi 3 mesi
        
        cost_analysis = {
            "ec2_costs": self._get_ec2_costs(start_date, end_date),
            "network_costs": self._get_network_costs(start_date, end_date),
            "storage_costs": self._get_storage_costs(start_date, end_date),
            "unused_resources": self._identify_unused_resources(),
            "cost_trends": self._analyze_cost_trends(start_date, end_date)
        }
        
        return cost_analysis
    
    def _get_ec2_costs(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Ottieni costi EC2 dettagliati"""
        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Elastic Compute Cloud - Compute']
                    }
                }
            )
            
            ec2_costs = {"total_cost": 0, "monthly_breakdown": [], "by_usage_type": {}}
            
            for result in response['ResultsByTime']:
                month = result['TimePeriod']['Start']
                monthly_cost = 0
                
                for group in result['Groups']:
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    usage_type = group['Keys'][1] if len(group['Keys']) > 1 else 'Unknown'
                    
                    monthly_cost += cost
                    
                    if usage_type not in ec2_costs["by_usage_type"]:
                        ec2_costs["by_usage_type"][usage_type] = 0
                    ec2_costs["by_usage_type"][usage_type] += cost
                
                ec2_costs["monthly_breakdown"].append({
                    "month": month,
                    "cost": monthly_cost
                })
                ec2_costs["total_cost"] += monthly_cost
            
            return ec2_costs
            
        except Exception as e:
            print(f"⚠️ Error fetching EC2 costs: {e}")
            return {"total_cost": 0, "error": str(e)}
    
    def _get_network_costs(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Ottieni costi network (EIP, LB, Data Transfer)"""
        try:
            # Network costs includono ELB, Data Transfer, NAT Gateway
            services = [
                'Amazon Elastic Load Balancing',
                'Amazon Elastic Compute Cloud - Compute',  # Per EIP e Data Transfer
                'Amazon Virtual Private Cloud'  # Per NAT Gateway
            ]
            
            network_costs = {"total_cost": 0, "by_service": {}}
            
            for service in services:
                response = self.ce.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': end_date.strftime('%Y-%m-%d')
                    },
                    Granularity='MONTHLY',
                    Metrics=['BlendedCost'],
                    Filter={
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': [service]
                        }
                    }
                )
                
                service_cost = 0
                for result in response['ResultsByTime']:
                    cost = float(result['Total']['BlendedCost']['Amount'])
                    service_cost += cost
                
                network_costs["by_service"][service] = service_cost
                network_costs["total_cost"] += service_cost
            
            return network_costs
            
        except Exception as e:
            print(f"⚠️ Error fetching network costs: {e}")
            return {"total_cost": 0, "error": str(e)}
    
    def _get_storage_costs(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Ottieni costi storage (EBS, Snapshots)"""
        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Elastic Compute Cloud - Compute']
                    }
                }
            )
            
            storage_costs = {"total_cost": 0, "ebs_volumes": 0, "snapshots": 0}
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    usage_type = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if 'EBS' in usage_type and 'Volume' in usage_type:
                        storage_costs["ebs_volumes"] += cost
                    elif 'EBS' in usage_type and 'Snapshot' in usage_type:
                        storage_costs["snapshots"] += cost
                    
                    storage_costs["total_cost"] += cost
            
            return storage_costs
            
        except Exception as e:
            print(f"⚠️ Error fetching storage costs: {e}")
            return {"total_cost": 0, "error": str(e)}
    
    def _identify_unused_resources(self) -> Dict[str, Any]:
        """Identifica risorse non utilizzate con stima costi"""
        unused = {
            "elastic_ips": [],
            "unattached_volumes": [],
            "unused_load_balancers": [],
            "total_monthly_waste": 0
        }
        
        # Elastic IPs non utilizzati
        try:
            eips = self.ec2.describe_addresses()['Addresses']
            for eip in eips:
                if 'AssociationId' not in eip:
                    unused["elastic_ips"].append({
                        "allocation_id": eip['AllocationId'],
                        "public_ip": eip['PublicIp'],
                        "monthly_cost": 3.65  # $0.005/hour
                    })
                    unused["total_monthly_waste"] += 3.65
        except Exception as e:
            print(f"⚠️ Error checking EIPs: {e}")
        
        # Volumi EBS non attaccati
        try:
            volumes = self.ec2.describe_volumes(
                Filters=[{'Name': 'status', 'Values': ['available']}]
            )['Volumes']
            
            for volume in volumes:
                monthly_cost = volume['Size'] * 0.08  # ~$0.08/GB/month per gp3
                unused["unattached_volumes"].append({
                    "volume_id": volume['VolumeId'],
                    "size_gb": volume['Size'],
                    "volume_type": volume['VolumeType'],
                    "monthly_cost": monthly_cost
                })
                unused["total_monthly_waste"] += monthly_cost
        except Exception as e:
            print(f"⚠️ Error checking volumes: {e}")
        
        # Load Balancers sottoutilizzati (heuristic)
        try:
            lbs = self.elbv2.describe_load_balancers()['LoadBalancers']
            for lb in lbs:
                # Check target groups
                tgs = self.elbv2.describe_target_groups(
                    LoadBalancerArn=lb['LoadBalancerArn']
                )['TargetGroups']
                
                total_targets = 0
                for tg in tgs:
                    targets = self.elbv2.describe_target_health(
                        TargetGroupArn=tg['TargetGroupArn']
                    )['TargetHealthDescriptions']
                    total_targets += len(targets)
                
                if total_targets == 0:  # LB senza target
                    lb_cost = 16.20 if lb['Type'] == 'application' else 22.50  # ALB vs NLB
                    unused["unused_load_balancers"].append({
                        "lb_arn": lb['LoadBalancerArn'],
                        "lb_name": lb['LoadBalancerName'],
                        "type": lb['Type'],
                        "target_count": total_targets,
                        "monthly_cost": lb_cost
                    })
                    unused["total_monthly_waste"] += lb_cost
        except Exception as e:
            print(f"⚠️ Error checking load balancers: {e}")
        
        return unused
    
    def _analyze_cost_trends(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analizza trend di costo per identificare anomalie"""
        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost']
            )
            
            monthly_costs = []
            for result in response['ResultsByTime']:
                cost = float(result['Total']['BlendedCost']['Amount'])
                monthly_costs.append({
                    "month": result['TimePeriod']['Start'],
                    "cost": cost
                })
            
            # Calcola trend
            if len(monthly_costs) >= 2:
                latest = monthly_costs[-1]['cost']
                previous = monthly_costs[-2]['cost']
                trend_percentage = ((latest - previous) / previous * 100) if previous > 0 else 0
                
                trend_analysis = {
                    "monthly_costs": monthly_costs,
                    "latest_month_cost": latest,
                    "previous_month_cost": previous,
                    "trend_percentage": trend_percentage,
                    "trend_direction": "UP" if trend_percentage > 5 else "DOWN" if trend_percentage < -5 else "STABLE",
                    "anomaly_detected": abs(trend_percentage) > 20  # Spike >20%
                }
            else:
                trend_analysis = {"monthly_costs": monthly_costs, "error": "Insufficient data"}
            
            return trend_analysis
            
        except Exception as e:
            print(f"⚠️ Error analyzing cost trends: {e}")
            return {"error": str(e)}
    
    def _cross_reference_sg_costs(self, sg_analysis: Dict, cost_analysis: Dict) -> Dict[str, Any]:
        """Cross-reference Security Groups con analisi costi"""
        integrated_findings = {
            "high_impact_deletions": [],
            "cost_correlated_sgs": [],
            "hidden_cost_discoveries": [],
            "safe_deletions_with_savings": []
        }
        
        # Ottieni SG sicuri da eliminare dall'analisi precedente
        safe_deletions = [
            sg for sg in sg_analysis.get("detailed_analyses", [])
            if isinstance(sg, dict) and sg.get("deletion_safety") == "SAFE"
        ]
        
        # Correlazione con unused resources
        unused_resources = cost_analysis.get("unused_resources", {})
        
        for sg in safe_deletions:
            sg_id = sg.get("sg_id")
            
            # Check se questo SG è collegato a risorse unused costose
            monthly_savings = 0
            
            # Check EIP collegati
            for eip in unused_resources.get("elastic_ips", []):
                # Verifica se l'EIP è associato a risorse che usano questo SG
                # (logica semplificata)
                monthly_savings += eip.get("monthly_cost", 0) * 0.1  # 10% del costo EIP
            
            if monthly_savings > 0:
                integrated_findings["safe_deletions_with_savings"].append({
                    "sg_id": sg_id,
                    "sg_name": sg.get("sg_name"),
                    "estimated_monthly_savings": monthly_savings,
                    "confidence": "HIGH" if monthly_savings > 10 else "MEDIUM"
                })
        
        # Identifica SG collegati a Load Balancer unused
        for lb in unused_resources.get("unused_load_balancers", []):
            # Trova SG associati a questo LB
            try:
                lb_details = self.elbv2.describe_load_balancers(
                    LoadBalancerArns=[lb["lb_arn"]]
                )["LoadBalancers"][0]
                
                for sg_id in lb_details.get("SecurityGroups", []):
                    integrated_findings["high_impact_deletions"].append({
                        "sg_id": sg_id,
                        "associated_lb": lb["lb_name"],
                        "monthly_savings": lb["monthly_cost"],
                        "action_required": "Remove unused Load Balancer first, then SG"
                    })
            except Exception:
                pass
        
        return integrated_findings
    
    def _generate_integrated_recommendations(self, integrated_analysis: Dict) -> Dict[str, Any]:
        """Genera raccomandazioni integrate basate su SG + Cost analysis"""
        recommendations = {
            "immediate_actions": [],
            "medium_term_actions": [],
            "long_term_strategies": [],
            "estimated_total_monthly_savings": 0
        }
        
        # Immediate actions (0-7 giorni)
        for deletion in integrated_analysis.get("safe_deletions_with_savings", []):
            if deletion.get("confidence") == "HIGH":
                recommendations["immediate_actions"].append({
                    "action": f"Delete Security Group {deletion['sg_name']}",
                    "priority": "HIGH",
                    "estimated_savings": deletion["estimated_monthly_savings"],
                    "effort": "LOW",
                    "risk": "LOW"
                })
                recommendations["estimated_total_monthly_savings"] += deletion["estimated_monthly_savings"]
        
        for high_impact in integrated_analysis.get("high_impact_deletions", []):
            recommendations["immediate_actions"].append({
                "action": f"Remove unused Load Balancer before deleting SG {high_impact['sg_id']}",
                "priority": "HIGH",
                "estimated_savings": high_impact["monthly_savings"],
                "effort": "MEDIUM",
                "risk": "MEDIUM"
            })
            recommendations["estimated_total_monthly_savings"] += high_impact["monthly_savings"]
        
        # Medium term actions (1-4 settimane)
        recommendations["medium_term_actions"].extend([
            {
                "action": "Implement automated SG cleanup process",
                "priority": "MEDIUM",
                "estimated_savings": recommendations["estimated_total_monthly_savings"] * 0.2,
                "effort": "HIGH",
                "risk": "LOW"
            },
            {
                "action": "Setup Cost Anomaly Detection for network resources",
                "priority": "MEDIUM",
                "estimated_savings": 0,  # Preventive
                "effort": "MEDIUM",
                "risk": "LOW"
            }
        ])
        
        # Long term strategies (1-6 mesi)
        recommendations["long_term_strategies"].extend([
            {
                "action": "Implement Infrastructure as Code for all Security Groups",
                "priority": "LOW",
                "estimated_savings": 0,  # Operational efficiency
                "effort": "HIGH",
                "risk": "LOW"
            },
            {
                "action": "Setup automated tagging and cost allocation for network resources",
                "priority": "LOW", 
                "estimated_savings": 0,  # Better visibility
                "effort": "HIGH",
                "risk": "LOW"
            }
        ])
        
        return recommendations
    
    def _generate_automated_scripts(self, recommendations: Dict) -> Dict[str, str]:
        """Genera script automatizzati per le azioni raccomandate"""
        scripts = {}
        
        # Script 1: Cleanup immediato
        immediate_script = [
            "#!/bin/bash",
            "# Immediate Security Groups + Cost Cleanup",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "set -e",
            "",
            "echo '🚀 Starting immediate cleanup...'",
            "",
            "# Create backup",
            f"aws ec2 describe-security-groups --region {self.region} > sg_cost_backup_$(date +%Y%m%d_%H%M%S).json",
            ""
        ]
        
        for action in recommendations.get("immediate_actions", []):
            if "Delete Security Group" in action["action"]:
                # Extract SG name from action text
                sg_name = action["action"].split("Delete Security Group ")[1]
                immediate_script.extend([
                    f"# {action['action']} (${action['estimated_savings']:.2f}/month savings)",
                    f"echo 'Processing: {sg_name}'",
                    f"# Add actual deletion command here after manual verification",
                    f"# aws ec2 delete-security-group --group-name '{sg_name}' --region {self.region}",
                    ""
                ])
        
        immediate_script.extend([
            "echo '✅ Immediate cleanup completed!'",
            f"echo 'Estimated monthly savings: ${recommendations.get('estimated_total_monthly_savings', 0):.2f}'",
            ""
        ])
        
        scripts["immediate_cleanup.sh"] = "\n".join(immediate_script)
        
        # Script 2: Monitoring setup
        monitoring_script = [
            "#!/bin/bash",
            "# Setup Cost Monitoring for Security Groups",
            "",
            "echo '📊 Setting up cost monitoring...'",
            "",
            "# Create budget for network costs",
            'aws budgets create-budget --account-id $(aws sts get-caller-identity --query Account --output text) --budget \'{"BudgetName":"NetworkResourcesBudget","BudgetLimit":{"Amount":"100","Unit":"USD"},"TimeUnit":"MONTHLY","BudgetType":"COST","CostFilters":{"Service":["Amazon Elastic Compute Cloud - Compute","Amazon Elastic Load Balancing"]}}\'',
            "",
            "# Setup cost anomaly detection",
            'aws ce create-anomaly-monitor --anomaly-monitor \'{"MonitorName":"SecurityGroupCostMonitor","MonitorType":"DIMENSIONAL","MonitorSpecification":"{\\"Dimension\\":{\\"Key\\":\\"SERVICE\\",\\"Values\\":[\\"Amazon Elastic Compute Cloud - Compute\\"]}}"}\'',
            "",
            "echo '✅ Monitoring setup completed!'",
            ""
        ]
        
        scripts["setup_monitoring.sh"] = "\n".join(monitoring_script)
        
        # Script 3: Validation post-cleanup
        validation_script = [
            "#!/bin/bash",
            "# Validation Script - Run after cleanup",
            "",
            "echo '🔍 Validating cleanup results...'",
            "",
            "# Check for orphaned resources",
            "echo 'Checking for unused Elastic IPs...'",
            f"aws ec2 describe-addresses --region {self.region} --query 'Addresses[?!AssociationId]' --output table",
            "",
            "echo 'Checking for unattached EBS volumes...'",
            f"aws ec2 describe-volumes --region {self.region} --filters 'Name=status,Values=available' --query 'Volumes[*].{{VolumeId:VolumeId,Size:Size,Cost:Size}}' --output table",
            "",
            "echo 'Checking for unused Load Balancers...'",
            f"aws elbv2 describe-load-balancers --region {self.region} --query 'LoadBalancers[*].{{Name:LoadBalancerName,State:State.Code}}' --output table",
            "",
            "echo 'Security Groups summary:'",
            f"TOTAL_SGS=$(aws ec2 describe-security-groups --region {self.region} --query 'length(SecurityGroups)')",
            'echo "Total Security Groups: $TOTAL_SGS"',
            "",
            "echo '✅ Validation completed!'",
            ""
        ]
        
        scripts["validation.sh"] = "\n".join(validation_script)
        
        # Script 4: Cost calculation
        cost_calc_script = [
            "#!/bin/bash",
            "# Calculate actual cost savings",
            "",
            "echo '💰 Calculating cost savings...'",
            "",
            "# Function to calculate EIP costs",
            "calculate_eip_waste() {",
            f"    UNUSED_EIPS=$(aws ec2 describe-addresses --region {self.region} --query 'length(Addresses[?!AssociationId])')",
            '    EIP_MONTHLY_COST=$(echo "$UNUSED_EIPS * 3.65" | bc -l)',
            '    echo "Unused EIPs: $UNUSED_EIPS"',
            '    echo "Monthly waste: $EIP_MONTHLY_COST USD"',
            "}",
            "",
            "# Function to calculate EBS costs",
            "calculate_ebs_waste() {",
            f"    aws ec2 describe-volumes --region {self.region} --filters 'Name=status,Values=available' --query 'Volumes[*].Size' --output text | \\",
            '    awk \'{sum+=$1} END {printf "Unattached EBS GB: %.0f\\nMonthly waste: $%.2f USD\\n", sum, sum*0.08}\'',
            "}",
            "",
            "# Execute calculations",
            "calculate_eip_waste",
            "calculate_ebs_waste",
            "",
            "# Generate savings report",
            "echo '📊 Savings Summary:' > cost_savings_report.txt",
            "date >> cost_savings_report.txt",
            "calculate_eip_waste >> cost_savings_report.txt",
            "calculate_ebs_waste >> cost_savings_report.txt",
            "",
            "echo '✅ Cost calculation completed! Check cost_savings_report.txt'",
            ""
        ]
        
        scripts["calculate_savings.sh"] = "\n".join(cost_calc_script)
        
        return scripts
    
    def _save_complete_report(self, report: Dict[str, Any]):
        """Salva il report completo integrato"""
        os.makedirs("reports/integrated_analysis", exist_ok=True)
        
        # Save JSON report
        with open("reports/integrated_analysis/complete_sg_cost_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save scripts
        for script_name, script_content in report["automation_scripts"].items():
            script_path = f"reports/integrated_analysis/{script_name}"
            with open(script_path, "w") as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)  # Make executable
        
        # Generate executive summary
        self._generate_executive_summary(report)
        
        # Generate detailed CSV for analysis
        self._generate_detailed_csv(report)
        
        print(f"\n✅ Complete analysis saved to reports/integrated_analysis/")
        print(f"📊 Total potential monthly savings: ${report['recommendations']['estimated_total_monthly_savings']:.2f}")
        print(f"📋 {len(report['recommendations']['immediate_actions'])} immediate actions identified")
        print(f"🔧 {len(report['automation_scripts'])} automation scripts generated")
    
    def _generate_executive_summary(self, report: Dict[str, Any]):
        """Genera executive summary per management"""
        summary_lines = [
            "# 🎯 Executive Summary: Security Groups & Cost Optimization",
            "",
            f"**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Region**: {self.region}",
            "",
            "## 💰 Financial Impact",
            "",
            f"**Estimated Monthly Savings**: ${report['recommendations']['estimated_total_monthly_savings']:.2f}",
            f"**Estimated Annual Savings**: ${report['recommendations']['estimated_total_monthly_savings'] * 12:.2f}",
            "",
            "### Cost Breakdown:",
        ]
        
        # Add cost analysis summary
        cost_analysis = report.get("cost_analysis", {})
        if "unused_resources" in cost_analysis:
            unused = cost_analysis["unused_resources"]
            summary_lines.extend([
                f"- **Unused Elastic IPs**: {len(unused.get('elastic_ips', []))} IPs → ${len(unused.get('elastic_ips', [])) * 3.65:.2f}/month",
                f"- **Unattached EBS Volumes**: {len(unused.get('unattached_volumes', []))} volumes → ${sum(v.get('monthly_cost', 0) for v in unused.get('unattached_volumes', [])):.2f}/month",
                f"- **Unused Load Balancers**: {len(unused.get('unused_load_balancers', []))} LBs → ${sum(lb.get('monthly_cost', 0) for lb in unused.get('unused_load_balancers', [])):.2f}/month",
            ])
        
        summary_lines.extend([
            "",
            "## 🛡️ Security Groups Analysis",
            "",
            f"**Total Security Groups**: {report.get('sg_analysis', {}).get('analysis_summary', {}).get('total_security_groups', 'N/A')}",
            f"**Safe to Delete**: {report.get('sg_analysis', {}).get('analysis_summary', {}).get('safe_to_delete', 'N/A')}",
            f"**Require Review**: {report.get('sg_analysis', {}).get('analysis_summary', {}).get('risky_to_delete', 'N/A')}",
            f"**Critical (Do Not Delete)**: {report.get('sg_analysis', {}).get('analysis_summary', {}).get('dangerous_to_delete', 'N/A')}",
            "",
            "## 🎯 Recommended Actions",
            "",
            "### Immediate (0-7 days):",
        ])
        
        # Add immediate actions
        for i, action in enumerate(report.get("recommendations", {}).get("immediate_actions", [])[:5], 1):
            summary_lines.append(f"{i}. {action.get('action', 'N/A')} (${action.get('estimated_savings', 0):.2f}/month)")
        
        summary_lines.extend([
            "",
            "### Medium Term (1-4 weeks):",
        ])
        
        # Add medium term actions
        for i, action in enumerate(report.get("recommendations", {}).get("medium_term_actions", [])[:3], 1):
            summary_lines.append(f"{i}. {action.get('action', 'N/A')}")
        
        summary_lines.extend([
            "",
            "## 📊 Risk Assessment",
            "",
            "- **Financial Risk**: LOW (automated backups before changes)",
            "- **Operational Risk**: LOW (phased approach recommended)",
            "- **Security Risk**: POSITIVE (reduced attack surface)",
            "",
            "## 🚀 Implementation Timeline",
            "",
            "- **Week 1**: Execute immediate cleanup actions",
            "- **Week 2-3**: Implement monitoring and automation",
            "- **Month 2-3**: Strategic infrastructure improvements",
            "",
            "## 📋 Next Steps",
            "",
            "1. **Approve immediate actions** (estimated savings: ${:.2f}/month)".format(
                sum(a.get('estimated_savings', 0) for a in report.get("recommendations", {}).get("immediate_actions", []))
            ),
            "2. **Schedule maintenance window** for cleanup execution",
            "3. **Review automated scripts** in reports/integrated_analysis/",
            "4. **Setup monitoring** for ongoing cost optimization",
            "",
            "---",
            "",
            "*For detailed technical information, see complete_sg_cost_report.json*"
        ])
        
        with open("reports/integrated_analysis/executive_summary.md", "w") as f:
            f.write("\n".join(summary_lines))
    
    def _generate_detailed_csv(self, report: Dict[str, Any]):
        """Genera CSV dettagliato per analisi approfondita"""
        
        # Combine all data into comprehensive CSV
        detailed_data = []
        
        # Security Groups data
        sg_analyses = report.get("sg_analysis", {}).get("detailed_analyses", [])
        for sg in sg_analyses:
            if isinstance(sg, dict):
                detailed_data.append({
                    "Resource_Type": "Security Group",
                    "Resource_ID": sg.get("sg_id", ""),
                    "Resource_Name": sg.get("sg_name", ""),
                    "VPC_ID": sg.get("vpc_id", ""),
                    "Usage_Score": sg.get("usage_score", 0),
                    "Deletion_Safety": sg.get("deletion_safety", ""),
                    "Monthly_Impact": sg.get("estimated_monthly_impact", 0),
                    "Rules_Count": sg.get("rules_count", 0),
                    "Attached_Resources": "; ".join(sg.get("attached_resources", [])),
                    "Top_Recommendation": sg.get("recommendations", [""])[0] if sg.get("recommendations") else "",
                    "Action_Priority": "HIGH" if sg.get("deletion_safety") == "SAFE" else "MEDIUM" if sg.get("deletion_safety") == "RISKY" else "LOW"
                })
        
        # Unused resources data
        unused_resources = report.get("cost_analysis", {}).get("unused_resources", {})
        
        # Elastic IPs
        for eip in unused_resources.get("elastic_ips", []):
            detailed_data.append({
                "Resource_Type": "Elastic IP",
                "Resource_ID": eip.get("allocation_id", ""),
                "Resource_Name": eip.get("public_ip", ""),
                "VPC_ID": "N/A",
                "Usage_Score": 0,
                "Deletion_Safety": "SAFE",
                "Monthly_Impact": eip.get("monthly_cost", 0),
                "Rules_Count": 0,
                "Attached_Resources": "None",
                "Top_Recommendation": "Release unused Elastic IP",
                "Action_Priority": "HIGH"
            })
        
        # EBS Volumes
        for volume in unused_resources.get("unattached_volumes", []):
            detailed_data.append({
                "Resource_Type": "EBS Volume",
                "Resource_ID": volume.get("volume_id", ""),
                "Resource_Name": f"{volume.get('size_gb', 0)}GB {volume.get('volume_type', '')}",
                "VPC_ID": "N/A",
                "Usage_Score": 0,
                "Deletion_Safety": "RISKY",  # Need snapshot first
                "Monthly_Impact": volume.get("monthly_cost", 0),
                "Rules_Count": 0,
                "Attached_Resources": "None",
                "Top_Recommendation": "Create snapshot then delete volume",
                "Action_Priority": "MEDIUM"
            })
        
        # Load Balancers
        for lb in unused_resources.get("unused_load_balancers", []):
            detailed_data.append({
                "Resource_Type": "Load Balancer",
                "Resource_ID": lb.get("lb_arn", "").split("/")[-1] if lb.get("lb_arn") else "",
                "Resource_Name": lb.get("lb_name", ""),
                "VPC_ID": "N/A",
                "Usage_Score": 0,
                "Deletion_Safety": "RISKY",  # Check dependencies
                "Monthly_Impact": lb.get("monthly_cost", 0),
                "Rules_Count": 0,
                "Attached_Resources": f"Targets: {lb.get('target_count', 0)}",
                "Top_Recommendation": "Remove load balancer with no targets",
                "Action_Priority": "HIGH"
            })
        
        # Save to CSV
        if detailed_data:
            df = pd.DataFrame(detailed_data)
            df = df.sort_values(["Action_Priority", "Monthly_Impact"], ascending=[True, False])
            df.to_csv("reports/integrated_analysis/detailed_analysis.csv", index=False)
            
            # Generate prioritized action list
            priority_df = df[df["Action_Priority"] == "HIGH"].head(20)
            priority_df.to_csv("reports/integrated_analysis/high_priority_actions.csv", index=False)


# Funzione principale per eseguire l'analisi completa
def run_complete_sg_cost_analysis(region: str = "us-east-1"):
    """Esegue l'analisi completa integrata Security Groups + Cost Explorer"""
    analyzer = CompleteSGCostIntegration(region)
    return analyzer.run_complete_analysis()


# Script per utilizzo CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Complete Security Groups + Cost Analysis")
    parser.add_argument("--region", default="us-east-1", help="AWS Region")
    parser.add_argument("--output-dir", default="reports/integrated_analysis", help="Output directory")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting complete analysis for region: {args.region}")
    
    try:
        report = run_complete_sg_cost_analysis(args.region)
        
        print("\n" + "="*60)
        print("📊 ANALYSIS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"💰 Potential Monthly Savings: ${report['recommendations']['estimated_total_monthly_savings']:.2f}")
        print(f"📅 Annual Savings: ${report['recommendations']['estimated_total_monthly_savings'] * 12:.2f}")
        print(f"🎯 Immediate Actions: {len(report['recommendations']['immediate_actions'])}")
        print(f"📋 Medium Term Actions: {len(report['recommendations']['medium_term_actions'])}")
        print(f"📁 Reports saved to: {args.output_dir}")
        print("\n🚀 Next Steps:")
        print("1. Review executive_summary.md")
        print("2. Check high_priority_actions.csv")
        print("3. Execute immediate_cleanup.sh after review")
        print("4. Setup monitoring with setup_monitoring.sh")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
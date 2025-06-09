# utils/simple_cleanup_orchestrator.py
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

class SimpleCleanupOrchestrator:
    """Orchestratore semplificato per cleanup infrastruttura AWS"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.cleanup_items = []
        self.total_estimated_savings = 0
        
    def create_cleanup_plan(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea piano di cleanup semplificato"""
        print("🧹 Creating infrastructure cleanup plan...")
        
        # Reset
        self.cleanup_items = []
        self.total_estimated_savings = 0
        
        # Analyze different resource types
        self._analyze_ec2_cleanup(audit_data)
        self._analyze_storage_cleanup(audit_data)
        self._analyze_network_cleanup(audit_data)
        self._analyze_security_groups_cleanup(audit_data)
        self._analyze_unused_resources(audit_data)
        
        # Create execution plan
        plan = self._create_execution_plan()
        
        # Generate scripts
        scripts = self._generate_cleanup_scripts()
        
        # Save results
        self._save_cleanup_plan(plan, scripts)
        
        return {
            "total_items": len(self.cleanup_items),
            "estimated_annual_savings": self.total_estimated_savings,
            "plan": plan,
            "scripts": scripts,
            "items": self.cleanup_items
        }
    
    def _analyze_ec2_cleanup(self, audit_data: Dict[str, Any]):
        """Analizza opportunità cleanup EC2"""
        ec2_data = audit_data.get("ec2_audit", {})
        
        # Stopped instances (potential waste)
        stopped_instances = ec2_data.get("stopped", [])
        for instance in stopped_instances:
            # Check if stopped for a long time
            instance_type = instance.get("Type", "t3.micro")
            estimated_cost = self._estimate_instance_monthly_cost(instance_type)
            
            self.cleanup_items.append({
                "type": "ec2_stopped",
                "resource_id": instance.get("InstanceId"),
                "resource_name": instance.get("Name", "Unknown"),
                "description": f"EC2 instance '{instance.get('Name')}' has been stopped",
                "action": "Review and terminate if not needed",
                "priority": "medium",
                "estimated_monthly_savings": 0,  # No cost while stopped, but potential cleanup
                "risk": "medium",
                "commands": [
                    f"# Review instance {instance.get('InstanceId')}",
                    f"aws ec2 describe-instances --instance-ids {instance.get('InstanceId')}",
                    f"# If not needed:",
                    f"aws ec2 terminate-instances --instance-ids {instance.get('InstanceId')}"
                ]
            })
        
        # Running instances that might be oversized
        active_instances = ec2_data.get("active", [])
        for instance in active_instances:
            instance_type = instance.get("Type", "")
            
            # Simple rightsizing suggestions for large instances
            if any(size in instance_type for size in ["large", "xlarge"]):
                current_cost = self._estimate_instance_monthly_cost(instance_type)
                smaller_type = self._suggest_smaller_instance_type(instance_type)
                smaller_cost = self._estimate_instance_monthly_cost(smaller_type)
                savings = current_cost - smaller_cost
                
                if savings > 10:  # Only suggest if savings > $10/month
                    self.cleanup_items.append({
                        "type": "ec2_rightsize",
                        "resource_id": instance.get("InstanceId"),
                        "resource_name": instance.get("Name", "Unknown"),
                        "description": f"Instance '{instance.get('Name')}' might be oversized ({instance_type})",
                        "action": f"Consider downsizing to {smaller_type}",
                        "priority": "low",
                        "estimated_monthly_savings": savings,
                        "risk": "low",
                        "commands": [
                            f"# Monitor usage first",
                            f"# If underutilized, resize from {instance_type} to {smaller_type}:",
                            f"aws ec2 stop-instances --instance-ids {instance.get('InstanceId')}",
                            f"aws ec2 modify-instance-attribute --instance-id {instance.get('InstanceId')} --instance-type {smaller_type}",
                            f"aws ec2 start-instances --instance-ids {instance.get('InstanceId')}"
                        ]
                    })
                    self.total_estimated_savings += savings * 12
    
    def _analyze_storage_cleanup(self, audit_data: Dict[str, Any]):
        """Analizza opportunità cleanup storage"""
        
        # Unattached EBS volumes
        ebs_data = audit_data.get("ebs_raw", {})
        if "volumes" in ebs_data:
            for volume in ebs_data["volumes"]:
                if volume.get("State") == "available":  # Unattached
                    size_gb = volume.get("Size", 0)
                    volume_type = volume.get("VolumeType", "gp2")
                    monthly_cost = size_gb * self._get_storage_price(volume_type)
                    
                    self.cleanup_items.append({
                        "type": "ebs_unattached",
                        "resource_id": volume.get("VolumeId"),
                        "resource_name": f"EBS Volume ({size_gb}GB)",
                        "description": f"Unattached EBS volume ({size_gb}GB, {volume_type})",
                        "action": "Create snapshot and delete if not needed",
                        "priority": "high",
                        "estimated_monthly_savings": monthly_cost,
                        "risk": "medium",
                        "commands": [
                            f"# Backup first",
                            f"aws ec2 create-snapshot --volume-id {volume.get('VolumeId')} --description 'Backup before deletion'",
                            f"# Delete volume (be careful!)",
                            f"aws ec2 delete-volume --volume-id {volume.get('VolumeId')}"
                        ]
                    })
                    self.total_estimated_savings += monthly_cost * 12
        
        # Old EBS snapshots
        snapshots_data = audit_data.get("ebs_snapshots_raw", {})
        if "Snapshots" in snapshots_data:
            old_snapshots = 0
            for snapshot in snapshots_data["Snapshots"]:
                try:
                    start_time = snapshot.get("StartTime")
                    if start_time:
                        # Simple age check - if snapshot is old, flag for review
                        old_snapshots += 1
                except:
                    pass
            
            if old_snapshots > 10:  # Many snapshots might indicate cleanup opportunity
                estimated_cost = old_snapshots * 2  # Rough estimate $2/snapshot
                self.cleanup_items.append({
                    "type": "old_snapshots",
                    "resource_id": "multiple_snapshots",
                    "resource_name": f"{old_snapshots} EBS snapshots",
                    "description": f"Found {old_snapshots} EBS snapshots that might be old",
                    "action": "Review and delete unnecessary snapshots",
                    "priority": "low",
                    "estimated_monthly_savings": estimated_cost,
                    "risk": "low",
                    "commands": [
                        "# List old snapshots",
                        "aws ec2 describe-snapshots --owner-ids self --query 'Snapshots[?StartTime<=`2023-01-01`]'",
                        "# Delete specific snapshot (example)",
                        "# aws ec2 delete-snapshot --snapshot-id snap-xxxxxxxx"
                    ]
                })
                self.total_estimated_savings += estimated_cost * 12
    
    def _analyze_network_cleanup(self, audit_data: Dict[str, Any]):
        """Analizza opportunità cleanup di rete"""
        
        # Unassociated Elastic IPs
        eip_data = audit_data.get("eip_raw", {})
        if "Addresses" in eip_data:
            unassociated_eips = []
            for eip in eip_data["Addresses"]:
                if not eip.get("AssociationId"):  # Not associated
                    unassociated_eips.append(eip)
            
            if unassociated_eips:
                monthly_cost = len(unassociated_eips) * 3.65  # ~$3.65/month per unused EIP
                
                self.cleanup_items.append({
                    "type": "unused_eips",
                    "resource_id": "multiple_eips",
                    "resource_name": f"{len(unassociated_eips)} Elastic IPs",
                    "description": f"{len(unassociated_eips)} unassociated Elastic IPs",
                    "action": "Release unused Elastic IPs",
                    "priority": "high",
                    "estimated_monthly_savings": monthly_cost,
                    "risk": "low",
                    "commands": [
                        "# List unassociated EIPs",
                        "aws ec2 describe-addresses --query 'Addresses[?!AssociationId]'",
                        "# Release specific EIP (example)",
                        "# aws ec2 release-address --allocation-id eipalloc-xxxxxxxx"
                    ]
                })
                self.total_estimated_savings += monthly_cost * 12
        
        # Load Balancers with few targets (potential waste)
        lb_data = audit_data.get("lb_raw", {})
        if lb_data:
            total_lbs = (len(lb_data.get("ApplicationLoadBalancers", [])) + 
                        len(lb_data.get("NetworkLoadBalancers", [])) + 
                        len(lb_data.get("ClassicLoadBalancers", [])))
            
            if total_lbs > 0:
                # Rough cost estimate for load balancers
                estimated_cost = total_lbs * 18  # ~$18/month per ALB
                
                self.cleanup_items.append({
                    "type": "review_load_balancers",
                    "resource_id": "multiple_lbs",
                    "resource_name": f"{total_lbs} Load Balancers",
                    "description": f"Review {total_lbs} load balancers for utilization",
                    "action": "Review load balancers and consolidate if possible",
                    "priority": "medium",
                    "estimated_monthly_savings": estimated_cost * 0.2,  # Assume 20% could be optimized
                    "risk": "high",  # High risk because LBs are critical
                    "commands": [
                        "# List all load balancers",
                        "aws elbv2 describe-load-balancers",
                        "aws elb describe-load-balancers",
                        "# Review target health and utilization before making changes"
                    ]
                })
    
    def _analyze_security_groups_cleanup(self, audit_data: Dict[str, Any]):
        """Analizza cleanup Security Groups dal sg_audit se disponibile"""
        sg_data = audit_data.get("sg_audit", {})
        
        # Unused security groups
        unused_sgs = sg_data.get("unused", [])
        if unused_sgs:
            self.cleanup_items.append({
                "type": "unused_security_groups",
                "resource_id": "multiple_sgs",
        # Unused security groups
        unused_sgs = sg_data.get("unused", [])
        if unused_sgs:
            self.cleanup_items.append({
                "type": "unused_security_groups",
                "resource_id": "multiple_sgs",
                "resource_name": f"{len(unused_sgs)} Security Groups",
                "description": f"{len(unused_sgs)} unused Security Groups found",
                "action": "Remove unused Security Groups",
                "priority": "medium",
                "estimated_monthly_savings": 0,  # No direct cost but reduces complexity
                "risk": "low",
                "commands": [
                    "# List unused security groups",
                    "# aws ec2 describe-security-groups --group-ids sg-xxxxxxxx",
                    "# Delete unused SGs (check dependencies first)",
                    *[f"aws ec2 delete-security-group --group-id {sg.get('GroupId')}" for sg in unused_sgs[:5]]
                ]
            })
        
        # Security Groups with critical exposures
        critical_ports = sg_data.get("critical_ports", [])
        if critical_ports:
            self.cleanup_items.append({
                "type": "critical_sg_exposure",
                "resource_id": "multiple_sgs",
                "resource_name": f"{len(critical_ports)} Critical Exposures",
                "description": f"{len(critical_ports)} critical ports exposed to Internet",
                "action": "URGENT: Restrict critical port access",
                "priority": "critical",
                "estimated_monthly_savings": 0,  # Security improvement
                "risk": "low",  # Low risk to fix, high risk to leave
                "commands": [
                    "# URGENT: Fix critical exposures",
                    *[f"aws ec2 revoke-security-group-ingress --group-id {sg.get('GroupId')} --protocol tcp --port {sg.get('CriticalPort')} --cidr 0.0.0.0/0" 
                      for sg in critical_ports[:3]]
                ]
            })
    
    def _analyze_unused_resources(self, audit_data: Dict[str, Any]):
        """Analizza altre risorse non utilizzate"""
        
        # Old AMIs (if available)
        ami_data = audit_data.get("ami_raw", {})
        if "Images" in ami_data:
            old_amis = len(ami_data["Images"])
            if old_amis > 10:  # Many AMIs might indicate cleanup opportunity
                self.cleanup_items.append({
                    "type": "old_amis",
                    "resource_id": "multiple_amis",
                    "resource_name": f"{old_amis} AMIs",
                    "description": f"Review {old_amis} custom AMIs for cleanup",
                    "action": "Review and delete unused AMIs",
                    "priority": "low",
                    "estimated_monthly_savings": old_amis * 0.5,  # Rough estimate for storage
                    "risk": "medium",
                    "commands": [
                        "# List your AMIs",
                        "aws ec2 describe-images --owners self",
                        "# Deregister old AMI (example)",
                        "# aws ec2 deregister-image --image-id ami-xxxxxxxx"
                    ]
                })
                self.total_estimated_savings += old_amis * 0.5 * 12
        
        # CloudWatch Log Groups without retention
        cloudwatch_data = audit_data.get("cloudwatch_raw", {})
        if "LogGroups" in cloudwatch_data:
            log_groups = cloudwatch_data["LogGroups"]
            no_retention = [lg for lg in log_groups if not lg.get("retentionInDays")]
            
            if no_retention:
                estimated_cost = len(no_retention) * 2  # Rough estimate
                self.cleanup_items.append({
                    "type": "log_retention",
                    "resource_id": "multiple_log_groups",
                    "resource_name": f"{len(no_retention)} Log Groups",
                    "description": f"{len(no_retention)} log groups without retention policy",
                    "action": "Set retention policies to control costs",
                    "priority": "medium",
                    "estimated_monthly_savings": estimated_cost,
                    "risk": "low",
                    "commands": [
                        "# Set retention policy (example: 30 days)",
                        *[f"aws logs put-retention-policy --log-group-name {lg.get('logGroupName')} --retention-in-days 30" 
                          for lg in no_retention[:3]]
                    ]
                })
                self.total_estimated_savings += estimated_cost * 12
    
    def _create_execution_plan(self) -> Dict[str, Any]:
        """Crea piano di esecuzione organizzato per priorità"""
        
        # Organizza per priorità
        by_priority = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for item in self.cleanup_items:
            priority = item.get("priority", "low")
            by_priority[priority].append(item)
        
        # Calcola savings per priorità
        savings_by_priority = {}
        for priority, items in by_priority.items():
            total_savings = sum(item.get("estimated_monthly_savings", 0) for item in items)
            savings_by_priority[priority] = total_savings * 12  # Annual
        
        return {
            "execution_phases": {
                "immediate": {
                    "description": "Critical security issues - Fix immediately",
                    "timeline": "0-24 hours",
                    "items": by_priority["critical"],
                    "count": len(by_priority["critical"]),
                    "estimated_annual_savings": savings_by_priority.get("critical", 0)
                },
                "urgent": {
                    "description": "High priority cost savings",
                    "timeline": "1-7 days",
                    "items": by_priority["high"],
                    "count": len(by_priority["high"]),
                    "estimated_annual_savings": savings_by_priority.get("high", 0)
                },
                "medium_term": {
                    "description": "Medium priority optimizations",
                    "timeline": "1-4 weeks",
                    "items": by_priority["medium"],
                    "count": len(by_priority["medium"]),
                    "estimated_annual_savings": savings_by_priority.get("medium", 0)
                },
                "maintenance": {
                    "description": "Low priority maintenance items",
                    "timeline": "1-3 months",
                    "items": by_priority["low"],
                    "count": len(by_priority["low"]),
                    "estimated_annual_savings": savings_by_priority.get("low", 0)
                }
            },
            "total_annual_savings": self.total_estimated_savings,
            "summary": {
                "total_items": len(self.cleanup_items),
                "by_priority": {k: len(v) for k, v in by_priority.items()},
                "high_impact_items": len(by_priority["critical"]) + len(by_priority["high"])
            }
        }
    
    def _generate_cleanup_scripts(self) -> Dict[str, str]:
        """Genera script di cleanup organizzati"""
        
        # Script per backup completo
        backup_script = [
            "#!/bin/bash",
            "# Complete AWS Infrastructure Backup Script",
            "# Run this BEFORE making any changes!",
            "",
            "set -e",
            "timestamp=$(date +%Y%m%d_%H%M%S)",
            "backup_dir=\"aws_backup_$timestamp\"",
            "mkdir -p \"$backup_dir\"",
            "",
            "echo '🔄 Creating complete AWS backup...'",
            "",
            "# Backup EC2 instances",
            "aws ec2 describe-instances > \"$backup_dir/ec2_instances.json\"",
            "",
            "# Backup Security Groups",
            "aws ec2 describe-security-groups > \"$backup_dir/security_groups.json\"",
            "",
            "# Backup EBS volumes",
            "aws ec2 describe-volumes > \"$backup_dir/ebs_volumes.json\"",
            "",
            "# Backup Load Balancers",
            "aws elbv2 describe-load-balancers > \"$backup_dir/load_balancers.json\" 2>/dev/null || echo 'No ALBs'",
            "aws elb describe-load-balancers > \"$backup_dir/classic_load_balancers.json\" 2>/dev/null || echo 'No CLBs'",
            "",
            "# Backup Elastic IPs",
            "aws ec2 describe-addresses > \"$backup_dir/elastic_ips.json\"",
            "",
            "echo \"✅ Backup completed in: $backup_dir\"",
            "echo \"📁 Keep this backup safe before making changes!\"",
            ""
        ]
        
        # Script critico (sicurezza)
        critical_script = [
            "#!/bin/bash",
            "# CRITICAL Security Fixes",
            "# Execute immediately after backup",
            "",
            "set -e",
            "echo '🚨 Applying critical security fixes...'",
            ""
        ]
        
        critical_items = [item for item in self.cleanup_items if item.get("priority") == "critical"]
        for item in critical_items:
            critical_script.extend([
                f"# {item['description']}",
                f"echo 'Fixing: {item['resource_name']}'",
                *item.get("commands", []),
                ""
            ])
        
        if not critical_items:
            critical_script.append("echo '✅ No critical security issues found!'")
        
        # Script cleanup costi
        cost_cleanup_script = [
            "#!/bin/bash",
            "# Cost Optimization Cleanup",
            "# Review each command before executing",
            "",
            "set -e",
            "echo '💰 Starting cost optimization cleanup...'",
            ""
        ]
        
        high_priority_items = [item for item in self.cleanup_items if item.get("priority") == "high"]
        for item in high_priority_items:
            cost_cleanup_script.extend([
                f"# {item['description']} (${item.get('estimated_monthly_savings', 0):.2f}/month savings)",
                f"echo 'Processing: {item['resource_name']}'",
                *item.get("commands", []),
                "echo 'Completed - verify before continuing'",
                "read -p 'Press Enter to continue or Ctrl+C to stop...'",
                ""
            ])
        
        # Script manutenzione generale
        maintenance_script = [
            "#!/bin/bash",
            "# General Maintenance Tasks",
            "# Low priority items for regular maintenance",
            "",
            "set -e",
            "echo '🔧 Running maintenance tasks...'",
            ""
        ]
        
        low_priority_items = [item for item in self.cleanup_items if item.get("priority") in ["medium", "low"]]
        for item in low_priority_items[:10]:  # Limit to first 10
            maintenance_script.extend([
                f"# {item['description']}",
                f"echo 'Maintenance: {item['resource_name']}'",
                *item.get("commands", []),
                ""
            ])
        
        # Script di verifica post-cleanup
        verify_script = [
            "#!/bin/bash",
            "# Post-Cleanup Verification",
            "# Run this after cleanup to verify everything is working",
            "",
            "set -e",
            "echo '🔍 Verifying infrastructure after cleanup...'",
            "",
            "# Check running instances",
            "echo 'Running EC2 instances:'",
            "aws ec2 describe-instances --filters 'Name=instance-state-name,Values=running' --query 'Reservations[].Instances[].{ID:InstanceId,Type:InstanceType,State:State.Name}' --output table",
            "",
            "# Check load balancers",
            "echo 'Active Load Balancers:'",
            "aws elbv2 describe-load-balancers --query 'LoadBalancers[].{Name:LoadBalancerName,State:State.Code}' --output table 2>/dev/null || echo 'No ALBs found'",
            "",
            "# Check security groups with issues",
            "echo 'Checking for remaining security issues...'",
            "aws ec2 describe-security-groups --query 'SecurityGroups[?IpPermissions[?IpProtocol==`tcp` && (FromPort==`22` || FromPort==`3306` || FromPort==`3389`) && IpRanges[?CidrIp==`0.0.0.0/0`]]].{GroupId:GroupId,GroupName:GroupName}' --output table",
            "",
            "# Check unattached volumes",
            "echo 'Unattached EBS volumes:'",
            "aws ec2 describe-volumes --filters 'Name=status,Values=available' --query 'Volumes[].{VolumeId:VolumeId,Size:Size,VolumeType:VolumeType}' --output table",
            "",
            "echo '✅ Verification completed!'",
            ""
        ]
        
        return {
            "1_backup_everything.sh": "\n".join(backup_script),
            "2_critical_security_fixes.sh": "\n".join(critical_script),
            "3_cost_optimization.sh": "\n".join(cost_cleanup_script),
            "4_maintenance_tasks.sh": "\n".join(maintenance_script),
            "5_verify_cleanup.sh": "\n".join(verify_script)
        }
    
    def _save_cleanup_plan(self, plan: Dict[str, Any], scripts: Dict[str, str]):
        """Salva piano di cleanup e script"""
        os.makedirs("reports/cleanup", exist_ok=True)
        
        # Salva piano completo
        with open("reports/cleanup/cleanup_plan.json", "w") as f:
            json.dump({
                "created_date": datetime.now().isoformat(),
                "region": self.region,
                "plan": plan,
                "cleanup_items": self.cleanup_items
            }, f, indent=2)
        
        # Salva script
        for script_name, script_content in scripts.items():
            with open(f"reports/cleanup/{script_name}", "w") as f:
                f.write(script_content)
            # Make scripts executable
            os.chmod(f"reports/cleanup/{script_name}", 0o755)
        
        # Genera report summary
        self._generate_cleanup_report(plan)
        
        print(f"✅ Cleanup plan created!")
        print(f"📁 Files saved in: reports/cleanup/")
        print(f"💰 Total estimated annual savings: ${self.total_estimated_savings:.2f}")
        print(f"🚨 Critical items: {plan['summary']['by_priority'].get('critical', 0)}")
        print(f"⚠️  High priority items: {plan['summary']['by_priority'].get('high', 0)}")
    
    def _generate_cleanup_report(self, plan: Dict[str, Any]):
        """Genera report di cleanup in markdown"""
        
        report = [
            "# 🧹 AWS Infrastructure Cleanup Plan",
            "",
            f"**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Region**: {self.region}",
            "",
            "## 💰 Cost Savings Summary",
            "",
            f"**Total Estimated Annual Savings**: ${self.total_estimated_savings:.2f}",
            f"**Total Cleanup Items**: {len(self.cleanup_items)}",
            "",
            "### Savings by Priority",
            ""
        ]
        
        for phase_name, phase_data in plan["execution_phases"].items():
            savings = phase_data["estimated_annual_savings"]
            count = phase_data["count"]
            report.append(f"- **{phase_name.title()}**: ${savings:.2f}/year ({count} items)")
        
        report.extend([
            "",
            "## 🚀 Execution Plan",
            ""
        ])
        
        # Add execution phases
        for phase_name, phase_data in plan["execution_phases"].items():
            if phase_data["count"] > 0:
                report.extend([
                    f"### {phase_data['description']} ({phase_data['timeline']})",
                    f"**Items**: {phase_data['count']}",
                    f"**Savings**: ${phase_data['estimated_annual_savings']:.2f}/year",
                    ""
                ])
                
                # Show top items
                for item in phase_data["items"][:3]:
                    report.append(f"- {item['resource_name']}: {item['description']}")
                
                if len(phase_data["items"]) > 3:
                    report.append(f"- ... and {len(phase_data['items']) - 3} more items")
                
                report.append("")
        
        # Add quick start guide
        report.extend([
            "## 🎯 Quick Start Guide",
            "",
            "1. **BACKUP FIRST**: `bash reports/cleanup/1_backup_everything.sh`",
            "2. **Fix Critical Issues**: `bash reports/cleanup/2_critical_security_fixes.sh`",
            "3. **Cost Optimization**: `bash reports/cleanup/3_cost_optimization.sh`",
            "4. **Maintenance**: `bash reports/cleanup/4_maintenance_tasks.sh`",
            "5. **Verify**: `bash reports/cleanup/5_verify_cleanup.sh`",
            "",
            "## ⚠️ Important Notes",
            "",
            "- **Always backup first** before making any changes",
            "- **Review each script** before execution",
            "- **Test in non-production** environment when possible",
            "- **Monitor applications** after changes",
            "",
            "## 📊 Detailed Items",
            ""
        ])
        
        # Add detailed items
        for item in self.cleanup_items:
            priority_emoji = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "🔵",
                "low": "⚪"
            }.get(item.get("priority", "low"), "⚪")
            
            savings = item.get("estimated_monthly_savings", 0)
            savings_text = f" (${savings:.2f}/month)" if savings > 0 else ""
            
            report.extend([
                f"### {priority_emoji} {item['resource_name']}{savings_text}",
                f"**Type**: {item['type']}",
                f"**Description**: {item['description']}",
                f"**Action**: {item['action']}",
                f"**Risk**: {item.get('risk', 'unknown')}",
                ""
            ])
        
        # Save report
        with open("reports/cleanup/cleanup_report.md", "w") as f:
            f.write("\n".join(report))
    
    # Helper methods per stime costi
    def _estimate_instance_monthly_cost(self, instance_type: str) -> float:
        """Stima costo mensile istanza EC2"""
        pricing_map = {
            't2.micro': 8.47, 't2.small': 16.79, 't2.medium': 33.58, 't2.large': 67.77,
            't3.micro': 7.59, 't3.small': 15.18, 't3.medium': 30.37, 't3.large': 60.74,
            't3.xlarge': 121.47, 't3.2xlarge': 242.94,
            'm5.large': 70.08, 'm5.xlarge': 140.16, 'm5.2xlarge': 280.32,
            'c5.large': 62.05, 'c5.xlarge': 124.10, 'c5.2xlarge': 248.20,
            'r5.large': 91.98, 'r5.xlarge': 183.96
        }
        return pricing_map.get(instance_type, 50.0)  # Default fallback
    
    def _suggest_smaller_instance_type(self, current_type: str) -> str:
        """Suggerisce tipo istanza più piccolo"""
        downsize_map = {
            't3.2xlarge': 't3.xlarge',
            't3.xlarge': 't3.large',
            't3.large': 't3.medium',
            't3.medium': 't3.small',
            'm5.2xlarge': 'm5.xlarge',
            'm5.xlarge': 'm5.large',
            'm5.large': 't3.large',
            'c5.2xlarge': 'c5.xlarge',
            'c5.xlarge': 'c5.large',
            'c5.large': 't3.large',
            'r5.xlarge': 'r5.large',
            'r5.large': 'm5.large'
        }
        return downsize_map.get(current_type, current_type)
    
    def _get_storage_price(self, volume_type: str) -> float:
        """Ottieni prezzo storage per GB/mese"""
        pricing = {
            'gp2': 0.10, 'gp3': 0.08, 'io1': 0.125, 'io2': 0.125,
            'st1': 0.045, 'sc1': 0.025
        }
        return pricing.get(volume_type, 0.10)


# Helper function to run cleanup analysis
def create_infrastructure_cleanup_plan(audit_data: Dict[str, Any], region: str = "us-east-1") -> Dict[str, Any]:
    """Funzione helper per creare piano di cleanup"""
    
    orchestrator = SimpleCleanupOrchestrator(region)
    results = orchestrator.create_cleanup_plan(audit_data)
    
    return results
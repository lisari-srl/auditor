# utils/sg_cost_analyzer.py
import os
import boto3
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class SGAnalysis:
    sg_id: str
    sg_name: str
    vpc_id: str
    creation_date: str
    rules_count: int
    attached_resources: List[str]
    resource_types: List[str]
    usage_score: float
    deletion_safety: str  # "SAFE", "RISKY", "DANGEROUS"
    estimated_monthly_impact: float
    recommendations: List[str]
    dependencies: List[str]

class SecurityGroupCostAnalyzer:
    """Analizzatore completo per Security Groups con analisi costi e dipendenze"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.ce = boto3.client('ce', region_name='us-east-1')  # Cost Explorer è solo us-east-1
        
    def analyze_all_security_groups(self) -> Dict[str, Any]:
        """Analisi completa di tutti i Security Groups"""
        print("🔍 Starting comprehensive Security Groups analysis...")
        
        # Fetch tutti i dati necessari
        security_groups = self._fetch_security_groups()
        network_interfaces = self._fetch_network_interfaces()
        instances = self._fetch_instances()
        load_balancers = self._fetch_load_balancers()
        rds_instances = self._fetch_rds_instances()
        
        # Costruisci mappa utilizzo completa
        usage_map = self._build_comprehensive_usage_map(
            security_groups, network_interfaces, instances, load_balancers, rds_instances
        )
        
        # Analizza ogni Security Group
        analyses = []
        for sg in security_groups:
            analysis = self._analyze_single_sg(sg, usage_map)
            analyses.append(analysis)
        
        # Genera report e raccomandazioni
        report = self._generate_comprehensive_report(analyses)
        
        # Salva risultati
        self._save_analysis_results(report, analyses)
        
        return report
    
    def _fetch_security_groups(self) -> List[Dict]:
        """Fetch di tutti i Security Groups"""
        paginator = self.ec2.get_paginator('describe_security_groups')
        sgs = []
        for page in paginator.paginate():
            sgs.extend(page['SecurityGroups'])
        return sgs
    
    def _fetch_network_interfaces(self) -> List[Dict]:
        """Fetch di tutte le Network Interfaces"""
        paginator = self.ec2.get_paginator('describe_network_interfaces')
        enis = []
        for page in paginator.paginate():
            enis.extend(page['NetworkInterfaces'])
        return enis
    
    def _fetch_instances(self) -> List[Dict]:
        """Fetch di tutte le istanze EC2"""
        paginator = self.ec2.get_paginator('describe_instances')
        instances = []
        for page in paginator.paginate():
            for reservation in page['Reservations']:
                instances.extend(reservation['Instances'])
        return instances
    
    def _fetch_load_balancers(self) -> List[Dict]:
        """Fetch dei Load Balancers (ALB/NLB)"""
        try:
            elbv2 = boto3.client('elbv2', region_name=self.region)
            paginator = elbv2.get_paginator('describe_load_balancers')
            lbs = []
            for page in paginator.paginate():
                lbs.extend(page['LoadBalancers'])
            return lbs
        except Exception as e:
            print(f"⚠️ Could not fetch load balancers: {e}")
            return []
    
    def _fetch_rds_instances(self) -> List[Dict]:
        """Fetch delle istanze RDS"""
        try:
            rds = boto3.client('rds', region_name=self.region)
            paginator = rds.get_paginator('describe_db_instances')
            db_instances = []
            for page in paginator.paginate():
                db_instances.extend(page['DBInstances'])
            return db_instances
        except Exception as e:
            print(f"⚠️ Could not fetch RDS instances: {e}")
            return []
    
    def _build_comprehensive_usage_map(self, security_groups, network_interfaces, 
                                     instances, load_balancers, rds_instances) -> Dict[str, Dict]:
        """Costruisce mappa completa dell'utilizzo dei Security Groups"""
        usage_map = defaultdict(lambda: {
            'enis': [],
            'instances': [],
            'load_balancers': [],
            'rds_instances': [],
            'lambda_functions': [],
            'other_resources': [],
            'total_attachments': 0,
            'resource_types': set(),
            'creation_dates': [],
            'last_activity': None
        })
        
        # Mappa da Network Interfaces
        for eni in network_interfaces:
            for group in eni.get('Groups', []):
                sg_id = group['GroupId']
                usage_map[sg_id]['enis'].append({
                    'eni_id': eni['NetworkInterfaceId'],
                    'status': eni['Status'],
                    'subnet_id': eni.get('SubnetId'),
                    'vpc_id': eni.get('VpcId'),
                    'description': eni.get('Description', ''),
                    'attachment': eni.get('Attachment', {})
                })
                usage_map[sg_id]['total_attachments'] += 1
        
        # Mappa da istanze EC2
        for instance in instances:
            for sg in instance.get('SecurityGroups', []):
                sg_id = sg['GroupId']
                usage_map[sg_id]['instances'].append({
                    'instance_id': instance['InstanceId'],
                    'instance_type': instance.get('InstanceType'),
                    'state': instance['State']['Name'],
                    'launch_time': instance.get('LaunchTime'),
                    'public_ip': instance.get('PublicIpAddress'),
                    'private_ip': instance.get('PrivateIpAddress'),
                    'tags': instance.get('Tags', [])
                })
                usage_map[sg_id]['resource_types'].add('EC2')
                if instance.get('LaunchTime'):
                    usage_map[sg_id]['creation_dates'].append(instance['LaunchTime'])
        
        # Mappa da Load Balancers
        for lb in load_balancers:
            for sg_id in lb.get('SecurityGroups', []):
                usage_map[sg_id]['load_balancers'].append({
                    'lb_arn': lb['LoadBalancerArn'],
                    'lb_name': lb['LoadBalancerName'],
                    'type': lb['Type'],
                    'state': lb['State']['Code'],
                    'created_time': lb.get('CreatedTime')
                })
                usage_map[sg_id]['resource_types'].add('LoadBalancer')
                if lb.get('CreatedTime'):
                    usage_map[sg_id]['creation_dates'].append(lb['CreatedTime'])
        
        # Mappa da RDS
        for rds in rds_instances:
            for sg in rds.get('VpcSecurityGroups', []):
                sg_id = sg['VpcSecurityGroupId']
                usage_map[sg_id]['rds_instances'].append({
                    'db_instance_id': rds['DBInstanceIdentifier'],
                    'db_instance_class': rds.get('DBInstanceClass'),
                    'engine': rds.get('Engine'),
                    'status': rds.get('DBInstanceStatus'),
                    'created_time': rds.get('InstanceCreateTime')
                })
                usage_map[sg_id]['resource_types'].add('RDS')
                if rds.get('InstanceCreateTime'):
                    usage_map[sg_id]['creation_dates'].append(rds['InstanceCreateTime'])
        
        return dict(usage_map)
    
    def _analyze_single_sg(self, sg: Dict, usage_map: Dict) -> SGAnalysis:
        """Analizza un singolo Security Group"""
        sg_id = sg['GroupId']
        sg_name = sg.get('GroupName', sg_id)
        usage = usage_map.get(sg_id, {})
        
        # Calcola usage score
        usage_score = self._calculate_usage_score(sg, usage)
        
        # Determina safety di eliminazione
        deletion_safety = self._assess_deletion_safety(sg, usage)
        
        # Stima impatto economico
        monthly_impact = self._estimate_monthly_impact(sg, usage)
        
        # Genera raccomandazioni
        recommendations = self._generate_recommendations(sg, usage, usage_score, deletion_safety)
        
        # Trova dipendenze
        dependencies = self._find_dependencies(sg, usage_map)
        
        return SGAnalysis(
            sg_id=sg_id,
            sg_name=sg_name,
            vpc_id=sg.get('VpcId', 'unknown'),
            creation_date=sg.get('CreationDate', '').split('T')[0] if sg.get('CreationDate') else 'unknown',
            rules_count=len(sg.get('IpPermissions', [])) + len(sg.get('IpPermissionsEgress', [])),
            attached_resources=[
                f"EC2: {len(usage.get('instances', []))}",
                f"ENI: {len(usage.get('enis', []))}",
                f"LB: {len(usage.get('load_balancers', []))}",
                f"RDS: {len(usage.get('rds_instances', []))}"
            ],
            resource_types=list(usage.get('resource_types', [])),
            usage_score=usage_score,
            deletion_safety=deletion_safety,
            estimated_monthly_impact=monthly_impact,
            recommendations=recommendations,
            dependencies=dependencies
        )
    
    def _calculate_usage_score(self, sg: Dict, usage: Dict) -> float:
        """Calcola score di utilizzo (0-100)"""
        score = 0
        
        # Attachment attuali (40 punti max)
        total_attachments = usage.get('total_attachments', 0)
        if total_attachments > 0:
            score += min(40, total_attachments * 10)
        
        # Diversità di risorse (30 punti max)
        resource_types = len(usage.get('resource_types', []))
        score += min(30, resource_types * 10)
        
        # Attività recente (20 punti max)
        creation_dates = usage.get('creation_dates', [])
        if creation_dates:
            # Se ha risorse create negli ultimi 30 giorni
            recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            recent_resources = 0
            
            for date in creation_dates:
                if isinstance(date, datetime):
                    try:
                        # Normalizza la data per il confronto
                        if date.tzinfo is None:
                            # Se la data non ha timezone, assume UTC
                            date_aware = date.replace(tzinfo=timezone.utc)
                        else:
                            # Se ha timezone, usala così com'è
                            date_aware = date
                        
                        if date_aware > recent_cutoff:
                            recent_resources += 1
                    except Exception:
                        # Se c'è qualche problema con la data, ignora
                        continue
            
            if recent_resources > 0:
                score += 20
        
        # Complessità regole (10 punti max)
        rules_count = len(sg.get('IpPermissions', [])) + len(sg.get('IpPermissionsEgress', []))
        if rules_count > 2:  # Più del default
            score += min(10, rules_count * 2)
        
        return min(100, score)
    
    def _assess_deletion_safety(self, sg: Dict, usage: Dict) -> str:
        """Valuta la sicurezza dell'eliminazione"""
        sg_name = sg.get('GroupName', '')
        total_attachments = usage.get('total_attachments', 0)
        resource_types = usage.get('resource_types', set())
        
        # DANGEROUS: Non eliminare mai
        if sg_name == 'default':
            return "DANGEROUS"
        
        if 'LoadBalancer' in resource_types:
            return "DANGEROUS"
        
        if 'RDS' in resource_types:
            return "DANGEROUS"
        
        running_instances = sum(1 for inst in usage.get('instances', []) 
                              if inst.get('state') == 'running')
        if running_instances > 0:
            return "DANGEROUS"
        
        # RISKY: Eliminazione possibile ma con attenzione
        if total_attachments > 0:
            return "RISKY"
        
        if any(keyword in sg_name.lower() for keyword in ['prod', 'production', 'critical']):
            return "RISKY"
        
        # SAFE: Sicuro da eliminare
        return "SAFE"
    
    def _estimate_monthly_impact(self, sg: Dict, usage: Dict) -> float:
        """Stima l'impatto economico mensile dell'eliminazione"""
        # I Security Groups in sé non hanno costi diretti,
        # ma stimiamo l'impatto sulla gestione delle risorse
        
        total_attachments = usage.get('total_attachments', 0)
        resource_types = len(usage.get('resource_types', []))
        
        # Stima costo di gestione/complessità
        management_cost = total_attachments * 0.1  # $0.10 per attachment
        complexity_cost = resource_types * 0.5     # $0.50 per tipo di risorsa
        
        return management_cost + complexity_cost
    
    def _generate_recommendations(self, sg: Dict, usage: Dict, usage_score: float, 
                                deletion_safety: str) -> List[str]:
        """Genera raccomandazioni specifiche"""
        recommendations = []
        sg_name = sg.get('GroupName', sg['GroupId'])
        
        if deletion_safety == "SAFE" and usage_score < 10:
            recommendations.append(f"✅ SAFE TO DELETE: {sg_name} is unused and safe to remove")
            recommendations.append("💡 Run backup script before deletion")
        
        elif deletion_safety == "RISKY" and usage_score < 30:
            recommendations.append(f"⚠️ REVIEW FOR DELETION: {sg_name} has low usage")
            recommendations.append("🔍 Check if attached resources are still needed")
        
        elif deletion_safety == "DANGEROUS":
            recommendations.append(f"❌ DO NOT DELETE: {sg_name} is attached to critical resources")
        
        # Raccomandazioni per ottimizzazione
        rules_count = len(sg.get('IpPermissions', [])) + len(sg.get('IpPermissionsEgress', []))
        if rules_count > 10:
            recommendations.append("🔧 Consider splitting complex rules into multiple SGs")
        
        if usage_score > 80:
            recommendations.append("✨ Well-utilized Security Group - keep as is")
        
        return recommendations
    
    def _find_dependencies(self, sg: Dict, usage_map: Dict) -> List[str]:
        """Trova dipendenze del Security Group"""
        dependencies = []
        sg_id = sg['GroupId']
        
        # Check se altri SG referenziano questo
        for other_sg_id, other_usage in usage_map.items():
            if other_sg_id == sg_id:
                continue
            
            # TODO: Implementare check dei riferimenti tra SG
            # Richiederebbe analisi delle regole che referenziano sg_id
        
        return dependencies
    
    def _generate_comprehensive_report(self, analyses: List[SGAnalysis]) -> Dict[str, Any]:
        """Genera report comprensivo"""
        total_sgs = len(analyses)
        safe_to_delete = [a for a in analyses if a.deletion_safety == "SAFE"]
        risky_to_delete = [a for a in analyses if a.deletion_safety == "RISKY"]
        dangerous_to_delete = [a for a in analyses if a.deletion_safety == "DANGEROUS"]
        
        # Calcola risparmi potenziali
        total_monthly_savings = sum(a.estimated_monthly_impact for a in safe_to_delete)
        
        # Trova top candidates per eliminazione
        deletion_candidates = sorted(
            [a for a in analyses if a.deletion_safety in ["SAFE", "RISKY"] and a.usage_score < 30],
            key=lambda x: (x.deletion_safety == "SAFE", -x.usage_score)
        )
        
        return {
            "analysis_summary": {
                "total_security_groups": total_sgs,
                "safe_to_delete": len(safe_to_delete),
                "risky_to_delete": len(risky_to_delete), 
                "dangerous_to_delete": len(dangerous_to_delete),
                "deletion_candidates": len(deletion_candidates),
                "potential_monthly_savings": total_monthly_savings,
                "potential_annual_savings": total_monthly_savings * 12
            },
            "immediate_actions": {
                "safe_deletions": safe_to_delete[:10],  # Top 10
                "review_for_deletion": risky_to_delete[:5],  # Top 5
                "consolidation_opportunities": self._find_consolidation_opportunities(analyses)
            },
            "cost_impact": {
                "management_complexity_reduction": len(safe_to_delete) * 2,  # hours/month
                "security_posture_improvement": len(deletion_candidates),
                "maintenance_cost_reduction": total_monthly_savings
            },
            "detailed_analyses": analyses
        }
    
    def _find_consolidation_opportunities(self, analyses: List[SGAnalysis]) -> List[Dict]:
        """Trova opportunità di consolidamento"""
        # Placeholder per logica di consolidamento
        consolidation_opportunities = []
        
        # Raggruppa SG simili per VPC
        vpc_groups = defaultdict(list)
        for analysis in analyses:
            if analysis.usage_score > 20:  # Solo SG utilizzati
                vpc_groups[analysis.vpc_id].append(analysis)
        
        # Identifica possibili consolidamenti
        for vpc_id, sg_list in vpc_groups.items():
            if len(sg_list) > 5:  # VPC con molti SG
                consolidation_opportunities.append({
                    "vpc_id": vpc_id,
                    "security_groups_count": len(sg_list),
                    "consolidation_potential": "HIGH" if len(sg_list) > 10 else "MEDIUM",
                    "estimated_reduction": len(sg_list) // 3,  # Stima 30% riduzione
                    "recommendation": f"Review {len(sg_list)} SGs in VPC {vpc_id} for consolidation"
                })
        
        return consolidation_opportunities
    
    def _save_analysis_results(self, report: Dict, analyses: List[SGAnalysis]):
        """Salva risultati dell'analisi"""
        import os
        os.makedirs("reports/security_groups", exist_ok=True)
        
        # Salva report JSON
        with open("reports/security_groups/sg_cost_analysis.json", "w") as f:
            # Convert SGAnalysis objects to dict for JSON serialization
            analyses_dict = [
                {
                    'sg_id': a.sg_id,
                    'sg_name': a.sg_name,
                    'vpc_id': a.vpc_id,
                    'creation_date': a.creation_date,
                    'rules_count': a.rules_count,
                    'attached_resources': a.attached_resources,
                    'resource_types': a.resource_types,
                    'usage_score': a.usage_score,
                    'deletion_safety': a.deletion_safety,
                    'estimated_monthly_impact': a.estimated_monthly_impact,
                    'recommendations': a.recommendations,
                    'dependencies': a.dependencies
                } for a in analyses
            ]
            
            report_copy = report.copy()
            report_copy['detailed_analyses'] = analyses_dict
            
            json.dump(report_copy, f, indent=2, default=str)
        
        # Genera CSV per analisi
        self._generate_csv_report(analyses)
        
        # Genera script di eliminazione
        self._generate_deletion_script(analyses)
        
        print(f"✅ Analysis saved to reports/security_groups/")
        print(f"📊 {len(analyses)} Security Groups analyzed")
        print(f"🗑️ {report['analysis_summary']['safe_to_delete']} safe to delete")
        print(f"💰 ${report['analysis_summary']['potential_monthly_savings']:.2f}/month potential savings")
    
    def _generate_csv_report(self, analyses: List[SGAnalysis]):
        """Genera report CSV per analisi in Excel"""
        data = []
        for a in analyses:
            data.append({
                'Security Group ID': a.sg_id,
                'Security Group Name': a.sg_name,
                'VPC ID': a.vpc_id,
                'Creation Date': a.creation_date,
                'Rules Count': a.rules_count,
                'Attached Resources': '; '.join(a.attached_resources),
                'Resource Types': '; '.join(a.resource_types),
                'Usage Score': a.usage_score,
                'Deletion Safety': a.deletion_safety,
                'Monthly Impact ($)': a.estimated_monthly_impact,
                'Top Recommendation': a.recommendations[0] if a.recommendations else 'No recommendations'
            })
        
        df = pd.DataFrame(data)
        df.to_csv("reports/security_groups/sg_analysis.csv", index=False)
        print("📄 CSV report saved: reports/security_groups/sg_analysis.csv")
    
    def _generate_deletion_script(self, analyses: List[SGAnalysis]):
        """Genera script per eliminazione sicura"""
        safe_to_delete = [a for a in analyses if a.deletion_safety == "SAFE"]
        
        script_lines = [
            "#!/bin/bash",
            "# Security Groups Safe Deletion Script",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Found {len(safe_to_delete)} Security Groups safe to delete",
            "",
            "set -e",
            "",
            "echo '🔒 Starting Security Groups cleanup...'",
            "echo 'Creating backup first...'",
            "",
            "# Backup all Security Groups",
            f"aws ec2 describe-security-groups --region {self.region} > sg_backup_$(date +%Y%m%d_%H%M%S).json",
            "",
            "echo 'Backup completed. Starting deletions...'",
            ""
        ]
        
        for analysis in safe_to_delete:
            script_lines.extend([
                f"# Delete {analysis.sg_name} (Usage Score: {analysis.usage_score})",
                f"echo 'Deleting {analysis.sg_id}...'",
                f"aws ec2 delete-security-group --group-id {analysis.sg_id} --region {self.region}",
                f"echo 'Deleted {analysis.sg_name}'",
                ""
            ])
        
        script_lines.extend([
            "echo '✅ Security Groups cleanup completed!'",
            f"echo 'Deleted {len(safe_to_delete)} unused Security Groups'",
            ""
        ])
        
        with open("reports/security_groups/safe_deletion.sh", "w") as f:
            f.write("\n".join(script_lines))
        
        # Make executable
        os.chmod("reports/security_groups/safe_deletion.sh", 0o755)
        print("🗑️ Deletion script saved: reports/security_groups/safe_deletion.sh")

# Funzione di utilizzo
def analyze_sg_costs_and_usage(region: str = "us-east-1"):
    """Analizza costi e utilizzo dei Security Groups"""
    analyzer = SecurityGroupCostAnalyzer(region)
    return analyzer.analyze_all_security_groups()

if __name__ == "__main__":
    # Test
    report = analyze_sg_costs_and_usage()
    print(json.dumps(report["analysis_summary"], indent=2))
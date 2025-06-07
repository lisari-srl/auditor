# utils/simple_sg_optimizer.py
import json
import os
from typing import Dict, List, Any
from datetime import datetime

class SimpleSecurityGroupOptimizer:
    """Ottimizzatore semplificato per Security Groups"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.findings = []
        
        # Porte critiche che non dovrebbero mai essere aperte a 0.0.0.0/0
        self.critical_ports = {
            22: "SSH", 3389: "RDP", 3306: "MySQL", 5432: "PostgreSQL",
            1433: "MSSQL", 6379: "Redis", 27017: "MongoDB", 11211: "Memcached"
        }
    
    def analyze_security_groups(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analizza Security Groups e trova problemi principali"""
        print("🛡️  Analyzing Security Groups for optimization...")
        
        sg_data = audit_data.get("sg_raw", {})
        security_groups = sg_data.get("SecurityGroups", [])
        
        # Build usage map
        usage_map = self._build_usage_map(audit_data)
        
        # Clear previous findings
        self.findings = []
        
        # Analyze each security group
        for sg in security_groups:
            self._check_critical_exposures(sg)
            self._check_unused_sg(sg, usage_map)
            self._check_duplicate_rules(sg)
            self._check_overly_broad_rules(sg)
        
        # Generate summary
        summary = self._generate_summary()
        
        # Create cleanup scripts
        cleanup_scripts = self._create_cleanup_scripts()
        
        # Save results
        self._save_results(summary, cleanup_scripts)
        
        return {
            "total_security_groups": len(security_groups),
            "total_findings": len(self.findings),
            "critical_issues": len([f for f in self.findings if f["severity"] == "critical"]),
            "high_issues": len([f for f in self.findings if f["severity"] == "high"]),
            "findings": self.findings,
            "summary": summary,
            "cleanup_scripts": cleanup_scripts
        }
    
    def _build_usage_map(self, audit_data: Dict[str, Any]) -> Dict[str, int]:
        """Costruisce mappa utilizzo Security Groups"""
        usage_map = {}
        
        # Check ENI usage
        eni_data = audit_data.get("eni_raw", {})
        for eni in eni_data.get("NetworkInterfaces", []):
            for group in eni.get("Groups", []):
                sg_id = group.get("GroupId")
                if sg_id:
                    usage_map[sg_id] = usage_map.get(sg_id, 0) + 1
        
        return usage_map
    
    def _check_critical_exposures(self, sg: Dict[str, Any]):
        """Verifica esposizioni critiche (database/admin ports aperti)"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        
        for rule in sg.get("IpPermissions", []):
            from_port = rule.get("FromPort")
            to_port = rule.get("ToPort")
            
            # Check each IP range
            for ip_range in rule.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0":
                    # Check if critical ports are exposed
                    if from_port in self.critical_ports:
                        self.findings.append({
                            "type": "critical_exposure",
                            "security_group_id": sg_id,
                            "security_group_name": sg_name,
                            "severity": "critical",
                            "port": from_port,
                            "service": self.critical_ports[from_port],
                            "description": f"CRITICAL: {self.critical_ports[from_port]} (port {from_port}) is open to the Internet",
                            "recommendation": f"Immediately restrict {self.critical_ports[from_port]} access to specific IP ranges",
                            "fix_command": f"aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol tcp --port {from_port} --cidr 0.0.0.0/0"
                        })
                    
                    # Check for other concerning open ports
                    elif from_port in [80, 443]:
                        # HTTP/HTTPS are sometimes intentionally open, but flag for review
                        self.findings.append({
                            "type": "web_exposure",
                            "security_group_id": sg_id,
                            "security_group_name": sg_name,
                            "severity": "medium",
                            "port": from_port,
                            "service": "HTTP" if from_port == 80 else "HTTPS",
                            "description": f"Web service on port {from_port} is open to Internet",
                            "recommendation": "Verify this is intentional and consider using CloudFront/ALB",
                            "fix_command": f"# Review if port {from_port} needs to be public"
                        })
                    
                    # Check for wide port ranges
                    elif from_port and to_port and (to_port - from_port) > 10:
                        self.findings.append({
                            "type": "wide_port_range",
                            "security_group_id": sg_id,
                            "security_group_name": sg_name,
                            "severity": "high",
                            "port_range": f"{from_port}-{to_port}",
                            "description": f"Wide port range {from_port}-{to_port} open to Internet",
                            "recommendation": "Narrow down to specific ports needed",
                            "fix_command": f"aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol tcp --port {from_port}-{to_port} --cidr 0.0.0.0/0"
                        })
    
    def _check_unused_sg(self, sg: Dict[str, Any], usage_map: Dict[str, int]):
        """Verifica Security Groups non utilizzati"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        
        # Skip default security group
        if sg_name == "default":
            return
        
        # Check if unused
        if usage_map.get(sg_id, 0) == 0:
            self.findings.append({
                "type": "unused_sg",
                "security_group_id": sg_id,
                "security_group_name": sg_name,
                "severity": "low",
                "description": f"Security Group '{sg_name}' is not attached to any resources",
                "recommendation": "Remove unused Security Group to reduce complexity",
                "fix_command": f"aws ec2 delete-security-group --group-id {sg_id}",
                "rules_count": len(sg.get("IpPermissions", [])) + len(sg.get("IpPermissionsEgress", []))
            })
    
    def _check_duplicate_rules(self, sg: Dict[str, Any]):
        """Verifica regole duplicate"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        
        seen_rules = set()
        duplicates = 0
        
        # Check ingress rules
        for rule in sg.get("IpPermissions", []):
            rule_signature = self._create_rule_signature(rule)
            if rule_signature in seen_rules:
                duplicates += 1
            seen_rules.add(rule_signature)
        
        if duplicates > 0:
            self.findings.append({
                "type": "duplicate_rules",
                "security_group_id": sg_id,
                "security_group_name": sg_name,
                "severity": "low",
                "duplicates_count": duplicates,
                "description": f"Security Group '{sg_name}' has {duplicates} duplicate rules",
                "recommendation": "Remove duplicate rules to simplify management",
                "fix_command": f"# Review and remove duplicate rules in {sg_id}"
            })
    
    def _check_overly_broad_rules(self, sg: Dict[str, Any]):
        """Verifica regole troppo ampie"""
        sg_id = sg.get("GroupId")
        sg_name = sg.get("GroupName", sg_id)
        
        for rule in sg.get("IpPermissions", []):
            # Check for very broad CIDR blocks
            for ip_range in rule.get("IpRanges", []):
                cidr = ip_range.get("CidrIp", "")
                if "/" in cidr:
                    try:
                        prefix_length = int(cidr.split("/")[1])
                        if prefix_length < 16:  # Very broad (more than 65k IPs)
                            self.findings.append({
                                "type": "broad_cidr",
                                "security_group_id": sg_id,
                                "security_group_name": sg_name,
                                "severity": "medium",
                                "cidr": cidr,
                                "ip_count": 2 ** (32 - prefix_length),
                                "description": f"Very broad CIDR {cidr} allows access from {2**(32-prefix_length):,} IP addresses",
                                "recommendation": "Narrow down to specific IP ranges actually needed",
                                "fix_command": f"# Replace {cidr} with more specific CIDR blocks"
                            })
                    except:
                        pass
    
    def _create_rule_signature(self, rule: Dict[str, Any]) -> str:
        """Crea signature univoca per una regola"""
        protocol = rule.get("IpProtocol", "")
        from_port = rule.get("FromPort", "")
        to_port = rule.get("ToPort", "")
        
        ip_ranges = sorted([ip.get("CidrIp", "") for ip in rule.get("IpRanges", [])])
        
        return f"{protocol}:{from_port}:{to_port}:{','.join(ip_ranges)}"
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Genera summary dei findings"""
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_type = {}
        
        for finding in self.findings:
            severity = finding.get("severity", "low")
            finding_type = finding.get("type", "unknown")
            
            by_severity[severity] += 1
            by_type[finding_type] = by_type.get(finding_type, 0) + 1
        
        return {
            "by_severity": by_severity,
            "by_type": by_type,
            "total_findings": len(self.findings),
            "security_score": self._calculate_security_score(by_severity)
        }
    
    def _calculate_security_score(self, by_severity: Dict[str, int]) -> Dict[str, Any]:
        """Calcola score di sicurezza"""
        # Start with 100, subtract penalties
        score = 100
        score -= by_severity["critical"] * 25  # -25 per critical
        score -= by_severity["high"] * 10      # -10 per high
        score -= by_severity["medium"] * 5     # -5 per medium
        score -= by_severity["low"] * 1        # -1 per low
        
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
        
        return {
            "score": score,
            "grade": grade,
            "status": "CRITICAL" if by_severity["critical"] > 0 else "GOOD" if score >= 80 else "NEEDS_IMPROVEMENT"
        }
    
    def _create_cleanup_scripts(self) -> Dict[str, str]:
        """Crea script di cleanup"""
        
        # Critical fixes script
        critical_script = ["#!/bin/bash", "# CRITICAL Security Fixes - Execute Immediately", "", "set -e", ""]
        
        critical_findings = [f for f in self.findings if f["severity"] == "critical"]
        for finding in critical_findings:
            critical_script.extend([
                f"# {finding['description']}",
                f"echo 'Fixing: {finding['security_group_name']}'",
                finding["fix_command"],
                ""
            ])
        
        # Cleanup unused SGs script
        cleanup_script = ["#!/bin/bash", "# Remove Unused Security Groups", "", "set -e", ""]
        
        unused_findings = [f for f in self.findings if f["type"] == "unused_sg"]
        for finding in unused_findings:
            cleanup_script.extend([
                f"# Remove unused SG: {finding['security_group_name']}",
                f"echo 'Removing {finding['security_group_id']}'",
                finding["fix_command"],
                ""
            ])
        
        # Backup script
        backup_script = [
            "#!/bin/bash",
            "# Backup Security Groups before making changes",
            "",
            "timestamp=$(date +%Y%m%d_%H%M%S)",
            "mkdir -p sg_backup_$timestamp",
            "",
            "echo 'Backing up all Security Groups...'",
            "aws ec2 describe-security-groups > sg_backup_$timestamp/all_security_groups.json",
            "",
            "echo 'Backup completed in sg_backup_$timestamp/'",
            "echo 'IMPORTANT: Keep this backup before making any changes!'"
        ]
        
        return {
            "critical_fixes.sh": "\n".join(critical_script),
            "cleanup_unused.sh": "\n".join(cleanup_script),
            "backup_security_groups.sh": "\n".join(backup_script)
        }
    
    def _save_results(self, summary: Dict[str, Any], cleanup_scripts: Dict[str, str]):
        """Salva risultati su file"""
        os.makedirs("reports/security_groups", exist_ok=True)
        
        # Save detailed findings
        with open("reports/security_groups/sg_analysis.json", "w") as f:
            json.dump({
                "analysis_date": datetime.now().isoformat(),
                "region": self.region,
                "summary": summary,
                "findings": self.findings
            }, f, indent=2)
        
        # Save cleanup scripts
        for script_name, script_content in cleanup_scripts.items():
            with open(f"reports/security_groups/{script_name}", "w") as f:
                f.write(script_content)
        
        # Generate simple report
        self._generate_simple_report(summary)
        
        print(f"✅ Security Groups analysis completed!")
        print(f"📁 Results saved in: reports/security_groups/")
        print(f"🎯 Security Score: {summary['security_score']['score']}/100 ({summary['security_score']['grade']})")
        if summary["by_severity"]["critical"] > 0:
            print(f"🚨 URGENT: {summary['by_severity']['critical']} critical security issues found!")
    
    def _generate_simple_report(self, summary: Dict[str, Any]):
        """Genera report semplice in markdown"""
        
        report = [
            "# 🛡️ Security Groups Analysis Report",
            "",
            f"**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Region**: {self.region}",
            "",
            "## 🎯 Security Score",
            "",
            f"**Score**: {summary['security_score']['score']}/100 (Grade: {summary['security_score']['grade']})",
            f"**Status**: {summary['security_score']['status']}",
            "",
            "## 📊 Issues Summary",
            "",
            f"- 🔴 **Critical**: {summary['by_severity']['critical']} (immediate action required)",
            f"- 🟠 **High**: {summary['by_severity']['high']} (fix within 24-48h)",
            f"- 🟡 **Medium**: {summary['by_severity']['medium']} (fix within 1 week)",
            f"- 🔵 **Low**: {summary['by_severity']['low']} (maintenance items)",
            "",
            f"**Total Issues**: {summary['total_findings']}",
            ""
        ]
        
        # Critical issues section
        critical_findings = [f for f in self.findings if f["severity"] == "critical"]
        if critical_findings:
            report.extend([
                "## 🚨 CRITICAL ISSUES - IMMEDIATE ACTION REQUIRED",
                ""
            ])
            
            for finding in critical_findings:
                report.extend([
                    f"### {finding['security_group_name']} - {finding.get('service', 'Security Issue')}",
                    f"**Issue**: {finding['description']}",
                    f"**Fix**: {finding['recommendation']}",
                    f"**Command**: `{finding['fix_command']}`",
                    ""
                ])
        
        # Quick recommendations
        report.extend([
            "## 💡 Quick Actions",
            "",
            "1. **Run critical fixes**: `bash reports/security_groups/critical_fixes.sh`",
            "2. **Backup first**: `bash reports/security_groups/backup_security_groups.sh`",
            "3. **Clean unused SGs**: `bash reports/security_groups/cleanup_unused.sh`",
            "",
            "## 📋 Next Steps",
            "",
            "- Review all critical issues immediately",
            "- Implement principle of least privilege",
            "- Regular security group audits",
            "- Use Infrastructure as Code for security groups",
            ""
        ])
        
        # Save report
        with open("reports/security_groups/sg_report.md", "w") as f:
            f.write("\n".join(report))


# Helper function to run analysis
def analyze_security_groups_simple(audit_data: Dict[str, Any], region: str = "us-east-1") -> Dict[str, Any]:
    """Funzione helper per analisi semplificata Security Groups"""
    
    optimizer = SimpleSecurityGroupOptimizer(region)
    results = optimizer.analyze_security_groups(audit_data)
    
    return results
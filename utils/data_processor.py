# utils/data_processor.py
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class DataProcessor:
    """Elabora i dati raw in formato adatto per l'audit"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
    
    def process_all_data(self) -> bool:
        """Elabora tutti i dati raw disponibili"""
        print("📊 Processing dati per audit...")
        
        try:
            # Process EC2 data
            if self._file_exists("ec2_raw.json"):
                self._process_ec2_data()
            
            # Process Security Groups
            if self._file_exists("sg_raw.json"):
                self._process_sg_data()
            
            # Process S3 data  
            if self._file_exists("s3_raw.json"):
                self._process_s3_data()
                
            # Process IAM data
            if self._file_exists("iam_raw.json"):
                self._process_iam_data()
            
            print("✅ Processing completato!")
            return True
            
        except Exception as e:
            print(f"❌ Errore durante processing: {e}")
            return False
    
    def _file_exists(self, filename: str) -> bool:
        """Verifica se file esiste"""
        return (self.data_dir / filename).exists()
    
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Carica file JSON"""
        try:
            with open(self.data_dir / filename) as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Errore caricamento {filename}: {e}")
            return {}
    
    def _save_json(self, filename: str, data: Any):
        """Salva file JSON"""
        with open(self.data_dir / filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _process_ec2_data(self):
        """Elabora dati EC2 per audit"""
        print("   🖥️  Processing EC2 instances...")
        
        raw_data = self._load_json("ec2_raw.json")
        
        active_instances = []
        stopped_instances = []
        
        for reservation in raw_data.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_data = {
                    "InstanceId": instance.get("InstanceId"),
                    "Name": self._get_instance_name(instance),
                    "Type": instance.get("InstanceType"),
                    "State": instance.get("State", {}).get("Name"),
                    "LaunchTime": instance.get("LaunchTime"),
                    "PublicIp": instance.get("PublicIpAddress"),
                    "PrivateIp": instance.get("PrivateIpAddress"),
                    "SubnetId": instance.get("SubnetId"),
                    "VpcId": instance.get("VpcId"),
                    "SecurityGroups": [sg.get("GroupId") for sg in instance.get("SecurityGroups", [])],
                    "Monitoring": instance.get("Monitoring", {}).get("State"),
                    "Platform": instance.get("Platform"),
                    "Architecture": instance.get("Architecture"),
                    "StateTransitionReason": instance.get("StateTransitionReason"),
                    "Tags": instance.get("Tags", [])
                }
                
                if instance_data["State"] == "running":
                    active_instances.append(instance_data)
                elif instance_data["State"] == "stopped":
                    stopped_instances.append(instance_data)
        
        audit_data = {
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "total_instances": len(active_instances) + len(stopped_instances)
            },
            "active": active_instances,
            "stopped": stopped_instances
        }
        
        self._save_json("ec2_audit.json", audit_data)
        print(f"      ✅ {len(active_instances)} running, {len(stopped_instances)} stopped")
    
    def _process_sg_data(self):
        """Elabora dati Security Groups per audit"""
        print("   🛡️  Processing Security Groups...")
        
        sg_data = self._load_json("sg_raw.json")
        eni_data = self._load_json("eni_raw.json")
        
        # Analizza SG aperti
        open_ingress = []
        open_egress = []
        unused_sgs = []
        
        # Mappa ENI per trovare SG utilizzati
        used_sg_ids = set()
        for eni in eni_data.get("NetworkInterfaces", []):
            for group in eni.get("Groups", []):
                used_sg_ids.add(group.get("GroupId"))
        
        for sg in sg_data.get("SecurityGroups", []):
            sg_id = sg.get("GroupId")
            sg_name = sg.get("GroupName", sg_id)
            
            # Check ingress rules aperti
            for rule in sg.get("IpPermissions", []):
                for ip_range in rule.get("IpRanges", []):
                    if ip_range.get("CidrIp") == "0.0.0.0/0":
                        open_ingress.append({
                            "GroupId": sg_id,
                            "GroupName": sg_name,
                            "Protocol": rule.get("IpProtocol"),
                            "FromPort": rule.get("FromPort"),
                            "ToPort": rule.get("ToPort"),
                            "CidrIp": ip_range.get("CidrIp")
                        })
            
            # Check egress rules aperti
            for rule in sg.get("IpPermissionsEgress", []):
                for ip_range in rule.get("IpRanges", []):
                    if ip_range.get("CidrIp") == "0.0.0.0/0":
                        open_egress.append({
                            "GroupId": sg_id,
                            "GroupName": sg_name,
                            "Protocol": rule.get("IpProtocol"),
                            "FromPort": rule.get("FromPort"),
                            "ToPort": rule.get("ToPort"),
                            "CidrIp": ip_range.get("CidrIp")
                        })
            
            # Check SG non utilizzati (skip default)
            if sg_name != "default" and sg_id not in used_sg_ids:
                unused_sgs.append({
                    "GroupId": sg_id,
                    "GroupName": sg_name,
                    "VpcId": sg.get("VpcId"),
                    "Description": sg.get("Description")
                })
        
        audit_data = {
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "total_security_groups": len(sg_data.get("SecurityGroups", [])),
                "used_security_groups": len(used_sg_ids)
            },
            "open_ingress": open_ingress,
            "open_egress": open_egress,
            "unused": unused_sgs
        }
        
        self._save_json("sg_audit.json", audit_data)
        print(f"      ✅ {len(open_ingress)} open ingress, {len(unused_sgs)} unused")
    
    def _process_s3_data(self):
        """Elabora dati S3 per audit"""
        print("   🗂️  Processing S3 buckets...")
        
        s3_data = self._load_json("s3_raw.json")
        
        if not isinstance(s3_data, list):
            print("      ⚠️  S3 data format unexpected")
            return
        
        public_buckets = []
        unencrypted_buckets = []
        
        for bucket in s3_data:
            bucket_name = bucket.get("Name")
            
            # Check public access
            if bucket.get("PublicAccess", False):
                public_buckets.append({
                    "Name": bucket_name,
                    "CreationDate": bucket.get("CreationDate"),
                    "Reason": "Public ACL or Policy"
                })
            
            # Per encryption, dovremmo fare chiamate aggiuntive
            # Per ora marchiamo come "unknown"
            if not bucket.get("Encryption"):  # Campo non presente nel fetch
                unencrypted_buckets.append({
                    "Name": bucket_name,
                    "CreationDate": bucket.get("CreationDate"),
                    "Reason": "Encryption status unknown"
                })
        
        audit_data = {
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "total_buckets": len(s3_data)
            },
            "public_buckets": public_buckets,
            "unencrypted_buckets": unencrypted_buckets
        }
        
        self._save_json("s3_audit.json", audit_data)
        print(f"      ✅ {len(public_buckets)} public, {len(unencrypted_buckets)} encryption unknown")
    
    def _process_iam_data(self):
        """Elabora dati IAM per audit"""
        print("   👤 Processing IAM resources...")
        
        iam_data = self._load_json("iam_raw.json")
        
        users = iam_data.get("Users", [])
        roles = iam_data.get("Roles", [])
        policies = iam_data.get("Policies", [])
        
        # Analisi base (per audit più dettagliato servirebbero più API calls)
        old_users = []
        admin_roles = []
        
        for user in users:
            # Check per utenti senza attività recente
            last_used = user.get("PasswordLastUsed")
            if last_used:
                try:
                    last_used_date = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
                    days_ago = (datetime.now() - last_used_date.replace(tzinfo=None)).days
                    if days_ago > 90:
                        old_users.append({
                            "UserName": user.get("UserName"),
                            "LastUsed": last_used,
                            "DaysAgo": days_ago
                        })
                except:
                    pass
        
        # Check per ruoli con nomi sospetti (admin)
        for role in roles:
            role_name = role.get("RoleName", "").lower()
            if any(term in role_name for term in ["admin", "root", "super"]):
                admin_roles.append({
                    "RoleName": role.get("RoleName"),
                    "CreationDate": role.get("CreateDate"),
                    "Description": role.get("Description", "")
                })
        
        audit_data = {
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "total_users": len(users),
                "total_roles": len(roles),
                "total_policies": len(policies)
            },
            "old_users": old_users,
            "admin_roles": admin_roles
        }
        
        self._save_json("iam_audit.json", audit_data)
        print(f"      ✅ {len(old_users)} old users, {len(admin_roles)} admin roles")
    
    def _get_instance_name(self, instance: Dict[str, Any]) -> str:
        """Estrae il nome dell'istanza dai tag"""
        for tag in instance.get("Tags", []):
            if tag.get("Key") == "Name":
                return tag.get("Value", instance.get("InstanceId"))
        return instance.get("InstanceId", "Unknown")
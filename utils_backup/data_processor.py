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
        self.processed_files = []
        self.errors = []
    
    def process_all_data(self) -> bool:
        """Elabora tutti i dati raw disponibili"""
        print("📊 Processing dati per audit...")
        
        self.processed_files = []
        self.errors = []
        
        try:
            # Verifica che la directory data esista
            if not self.data_dir.exists():
                print("❌ Directory /data non trovata")
                return False
            
            # Lista file disponibili
            available_files = list(self.data_dir.glob("*_raw.json"))
            if not available_files:
                print("⚠️  Nessun file *_raw.json trovato in /data")
                return False
            
            print(f"   📁 Trovati {len(available_files)} file da processare")
            
            # Process EC2 data
            if self._file_exists("ec2_raw.json"):
                if self._process_ec2_data():
                    self.processed_files.append("ec2_audit.json")
            
            # Process Security Groups
            if self._file_exists("sg_raw.json"):
                if self._process_sg_data():
                    self.processed_files.append("sg_audit.json")
            
            # Process S3 data  
            if self._file_exists("s3_raw.json"):
                if self._process_s3_data():
                    self.processed_files.append("s3_audit.json")
                    
            # Process IAM data
            if self._file_exists("iam_raw.json"):
                if self._process_iam_data():
                    self.processed_files.append("iam_audit.json")
            
            # Process VPC data
            if self._file_exists("vpc_raw.json"):
                if self._process_vpc_data():
                    self.processed_files.append("vpc_audit.json")
            
            print(f"✅ Processing completato! {len(self.processed_files)} file processati")
            
            if self.errors:
                print(f"⚠️  {len(self.errors)} errori durante processing:")
                for error in self.errors[:3]:  # Mostra solo i primi 3
                    print(f"   • {error}")
                if len(self.errors) > 3:
                    print(f"   • ... e altri {len(self.errors) - 3} errori")
            
            return len(self.processed_files) > 0
            
        except Exception as e:
            print(f"❌ Errore critico durante processing: {e}")
            self.errors.append(f"Critical error: {e}")
            return False
    
    def _file_exists(self, filename: str) -> bool:
        """Verifica se file esiste"""
        return (self.data_dir / filename).exists()
    
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Carica file JSON con gestione errori"""
        try:
            file_path = self.data_dir / filename
            
            # Verifica dimensione file
            file_size = file_path.stat().st_size
            if file_size == 0:
                print(f"   ⚠️  File {filename} è vuoto")
                return {}
            
            if file_size > 50 * 1024 * 1024:  # > 50MB
                print(f"   ⚠️  File {filename} molto grande ({file_size // (1024*1024)}MB), processing potrebbe essere lento")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"   ✅ Caricato {filename} ({file_size // 1024}KB)")
                return data
        except json.JSONDecodeError as e:
            error_msg = f"JSON error in {filename}: {e}"
            print(f"   ❌ {error_msg}")
            self.errors.append(error_msg)
            return {}
        except Exception as e:
            error_msg = f"Load error {filename}: {e}"
            print(f"   ❌ {error_msg}")
            self.errors.append(error_msg)
            return {}
    
    def _save_json(self, filename: str, data: Any) -> bool:
        """Salva file JSON con gestione errori"""
        try:
            file_path = self.data_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
            
            # Log dimensione file salvato
            file_size = file_path.stat().st_size
            print(f"   💾 Salvato {filename} ({file_size // 1024}KB)")
            return True
        except Exception as e:
            error_msg = f"Save error {filename}: {e}"
            print(f"   ❌ {error_msg}")
            self.errors.append(error_msg)
            return False
    
    def _process_ec2_data(self) -> bool:
        """Elabora dati EC2 per audit"""
        print("   🖥️  Processing EC2 instances...")
        
        try:
            raw_data = self._load_json("ec2_raw.json")
            if not raw_data:
                return False
            
            active_instances = []
            stopped_instances = []
            terminated_instances = []
            
            total_processed = 0
            
            for reservation in raw_data.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    try:
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
                            "SecurityGroups": [sg.get("GroupId") for sg in instance.get("SecurityGroups", []) if sg.get("GroupId")],
                            "Monitoring": instance.get("Monitoring", {}).get("State"),
                            "Platform": instance.get("Platform"),
                            "Architecture": instance.get("Architecture"),
                            "StateTransitionReason": instance.get("StateTransitionReason"),
                            "Tags": instance.get("Tags", []),
                            "EbsOptimized": instance.get("EbsOptimized", False),
                            "InstanceProfile": instance.get("IamInstanceProfile", {}).get("Arn") if instance.get("IamInstanceProfile") else None
                        }
                        
                        state = instance_data["State"]
                        if state == "running":
                            active_instances.append(instance_data)
                        elif state == "stopped":
                            stopped_instances.append(instance_data)
                        elif state in ["terminated", "terminating"]:
                            terminated_instances.append(instance_data)
                        
                        total_processed += 1
                        
                    except Exception as e:
                        self.errors.append(f"EC2 instance processing error: {e}")
                        continue
            
            audit_data = {
                "metadata": {
                    "processed_at": datetime.now().isoformat(),
                    "total_instances": total_processed,
                    "total_reservations": len(raw_data.get("Reservations", []))
                },
                "active": active_instances,
                "stopped": stopped_instances,
                "terminated": terminated_instances,
                "summary": {
                    "running": len(active_instances),
                    "stopped": len(stopped_instances),
                    "terminated": len(terminated_instances)
                }
            }
            
            if self._save_json("ec2_audit.json", audit_data):
                print(f"      ✅ {len(active_instances)} running, {len(stopped_instances)} stopped, {len(terminated_instances)} terminated")
                return True
            return False
            
        except Exception as e:
            error_msg = f"EC2 processing failed: {e}"
            print(f"   ❌ {error_msg}")
            self.errors.append(error_msg)
            return False
    
    def _process_sg_data(self) -> bool:
        """Elabora dati Security Groups per audit"""
        print("   🛡️  Processing Security Groups...")
        
        try:
            sg_data = self._load_json("sg_raw.json")
            eni_data = self._load_json("eni_raw.json")
            
            if not sg_data:
                return False
            
            # Analizza SG aperti e usage
            open_ingress = []
            open_egress = []
            unused_sgs = []
            critical_ports = []
            
            # Mappa ENI per trovare SG utilizzati
            used_sg_ids = set()
            if eni_data:
                for eni in eni_data.get("NetworkInterfaces", []):
                    for group in eni.get("Groups", []):
                        sg_id = group.get("GroupId")
                        if sg_id:
                            used_sg_ids.add(sg_id)
            
            total_sgs = 0
            for sg in sg_data.get("SecurityGroups", []):
                try:
                    sg_id = sg.get("GroupId")
                    sg_name = sg.get("GroupName", sg_id)
                    
                    if not sg_id:
                        continue
                    
                    total_sgs += 1
                    
                    # Check ingress rules aperti
                    for rule in sg.get("IpPermissions", []):
                        for ip_range in rule.get("IpRanges", []):
                            if ip_range.get("CidrIp") == "0.0.0.0/0":
                                rule_data = {
                                    "GroupId": sg_id,
                                    "GroupName": sg_name,
                                    "Protocol": rule.get("IpProtocol"),
                                    "FromPort": rule.get("FromPort"),
                                    "ToPort": rule.get("ToPort"),
                                    "CidrIp": ip_range.get("CidrIp"),
                                    "Description": ip_range.get("Description", "")
                                }
                                open_ingress.append(rule_data)
                                
                                # Check porte critiche
                                from_port = rule.get("FromPort", -1)
                                to_port = rule.get("ToPort", -1)
                                critical_port_list = [22, 3389, 1433, 3306, 5432, 21, 23, 143, 993, 995]
                                
                                for crit_port in critical_port_list:
                                    if (from_port == -1 or from_port <= crit_port <= to_port or from_port == crit_port):
                                        critical_ports.append({
                                            **rule_data,
                                            "CriticalPort": crit_port,
                                            "PortName": self._get_port_name(crit_port)
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
                                    "CidrIp": ip_range.get("CidrIp"),
                                    "Description": ip_range.get("Description", "")
                                })
                    
                    # Check SG non utilizzati (skip default)
                    if sg_name != "default" and sg_id not in used_sg_ids:
                        unused_sgs.append({
                            "GroupId": sg_id,
                            "GroupName": sg_name,
                            "VpcId": sg.get("VpcId"),
                            "Description": sg.get("Description", ""),
                            "IngressRules": len(sg.get("IpPermissions", [])),
                            "EgressRules": len(sg.get("IpPermissionsEgress", []))
                        })
                        
                except Exception as e:
                    self.errors.append(f"SG processing error for {sg.get('GroupId', 'unknown')}: {e}")
                    continue
            
            audit_data = {
                "metadata": {
                    "processed_at": datetime.now().isoformat(),
                    "total_security_groups": total_sgs,
                    "used_security_groups": len(used_sg_ids)
                },
                "open_ingress": open_ingress,
                "open_egress": open_egress,
                "unused": unused_sgs,
                "critical_ports": critical_ports,
                "summary": {
                    "total_open_ingress": len(open_ingress),
                    "total_open_egress": len(open_egress),
                    "total_unused": len(unused_sgs),
                    "total_critical_ports": len(critical_ports)
                }
            }
            
            if self._save_json("sg_audit.json", audit_data):
                print(f"      ✅ {len(open_ingress)} open ingress, {len(unused_sgs)} unused, {len(critical_ports)} critical ports")
                return True
            return False
            
        except Exception as e:
            error_msg = f"SG processing failed: {e}"
            print(f"   ❌ {error_msg}")
            self.errors.append(error_msg)
            return False
    
    def _process_s3_data(self) -> bool:
        """Elabora dati S3 per audit"""
        print("   🗂️  Processing S3 buckets...")
        
        try:
            s3_data = self._load_json("s3_raw.json")
            
            if not s3_data:
                return False
            
            if not isinstance(s3_data, list):
                print("      ⚠️  S3 data format unexpected, skipping")
                return False
            
            public_buckets = []
            unencrypted_buckets = []
            old_buckets = []
            
            current_date = datetime.now()
            
            for bucket in s3_data:
                try:
                    bucket_name = bucket.get("Name")
                    if not bucket_name:
                        continue
                    
                    # Check public access
                    if bucket.get("PublicAccess", False):
                        public_buckets.append({
                            "Name": bucket_name,
                            "CreationDate": bucket.get("CreationDate"),
                            "Region": bucket.get("ActualRegion", "unknown"),
                            "Reason": "Public ACL or Policy"
                        })
                    
                    # Check creation date per bucket vecchi
                    creation_date_str = bucket.get("CreationDate")
                    if creation_date_str:
                        try:
                            if "T" in creation_date_str:
                                creation_date = datetime.fromisoformat(creation_date_str.replace('Z', '+00:00'))
                            else:
                                creation_date = datetime.strptime(creation_date_str[:10], "%Y-%m-%d")
                            
                            days_old = (current_date - creation_date.replace(tzinfo=None)).days
                            if days_old > 365:  # Più di un anno
                                old_buckets.append({
                                    "Name": bucket_name,
                                    "CreationDate": creation_date_str,
                                    "DaysOld": days_old,
                                    "Region": bucket.get("ActualRegion", "unknown")
                                })
                        except Exception:
                            pass
                    
                    # Per encryption, dovremmo fare chiamate aggiuntive
                    # Per ora marchiamo come "unknown" se non abbiamo info
                    if not bucket.get("Encryption"):
                        unencrypted_buckets.append({
                            "Name": bucket_name,
                            "CreationDate": creation_date_str,
                            "Region": bucket.get("ActualRegion", "unknown"),
                            "Reason": "Encryption status unknown"
                        })
                        
                except Exception as e:
                    self.errors.append(f"S3 bucket processing error for {bucket.get('Name', 'unknown')}: {e}")
                    continue
            
            audit_data = {
                "metadata": {
                    "processed_at": datetime.now().isoformat(),
                    "total_buckets": len(s3_data)
                },
                "public_buckets": public_buckets,
                "unencrypted_buckets": unencrypted_buckets,
                "old_buckets": old_buckets,
                "summary": {
                    "total_public": len(public_buckets),
                    "total_unencrypted": len(unencrypted_buckets),
                    "total_old": len(old_buckets)
                }
            }
            
            if self._save_json("s3_audit.json", audit_data):
                print(f"      ✅ {len(public_buckets)} public, {len(unencrypted_buckets)} encryption unknown, {len(old_buckets)} old")
                return True
            return False
            
        except Exception as e:
            error_msg = f"S3 processing failed: {e}"
            print(f"   ❌ {error_msg}")
            self.errors.append(error_msg)
            return False
    
    def _process_iam_data(self) -> bool:
        """Elabora dati IAM per audit"""
        print("   👤 Processing IAM resources...")
        
        try:
            iam_data = self._load_json("iam_raw.json")
            
            if not iam_data:
                return False
            
            users = iam_data.get("Users", [])
            roles = iam_data.get("Roles", [])
            policies = iam_data.get("Policies", [])
            
            # Analisi avanzata
            old_users = []
            admin_roles = []
            service_roles = []
            unused_policies = []
            
            current_date = datetime.now()
            
            # Analizza users
            for user in users:
                try:
                    user_name = user.get("UserName")
                    if not user_name:
                        continue
                    
                    # Check per utenti senza attività recente
                    last_used = user.get("PasswordLastUsed")
                    if last_used:
                        try:
                            last_used_date = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
                            days_ago = (current_date - last_used_date.replace(tzinfo=None)).days
                            if days_ago > 90:
                                old_users.append({
                                    "UserName": user_name,
                                    "LastUsed": last_used,
                                    "DaysAgo": days_ago,
                                    "CreationDate": user.get("CreateDate"),
                                    "Path": user.get("Path", "/")
                                })
                        except Exception:
                            # Se non riesco a parsare la data, considero come potenzialmente vecchio
                            old_users.append({
                                "UserName": user_name,
                                "LastUsed": "Never or unparseable",
                                "DaysAgo": -1,
                                "CreationDate": user.get("CreateDate"),
                                "Path": user.get("Path", "/")
                            })
                    else:
                        # Nessun ultimo utilizzo = potenzialmente vecchio
                        creation_date = user.get("CreateDate")
                        if creation_date:
                            try:
                                created = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
                                days_since_creation = (current_date - created.replace(tzinfo=None)).days
                                if days_since_creation > 30:  # Creato più di 30 giorni fa e mai usato
                                    old_users.append({
                                        "UserName": user_name,
                                        "LastUsed": "Never",
                                        "DaysAgo": -1,
                                        "CreationDate": creation_date,
                                        "Path": user.get("Path", "/"),
                                        "DaysSinceCreation": days_since_creation
                                    })
                            except Exception:
                                pass
                except Exception as e:
                    self.errors.append(f"IAM user processing error for {user.get('UserName', 'unknown')}: {e}")
                    continue
            
            # Analizza roles
            for role in roles:
                try:
                    role_name = role.get("RoleName", "")
                    if not role_name:
                        continue
                    
                    role_name_lower = role_name.lower()
                    
                    # Check per ruoli admin
                    if any(term in role_name_lower for term in ["admin", "root", "super", "full", "power"]):
                        admin_roles.append({
                            "RoleName": role_name,
                            "CreationDate": role.get("CreateDate"),
                            "Description": role.get("Description", ""),
                            "Path": role.get("Path", "/"),
                            "MaxSessionDuration": role.get("MaxSessionDuration", 3600)
                        })
                    
                    # Check per service roles
                    if any(term in role_name_lower for term in ["service", "lambda", "ec2", "s3", "rds"]):
                        service_roles.append({
                            "RoleName": role_name,
                            "CreationDate": role.get("CreateDate"),
                            "Description": role.get("Description", ""),
                            "ServiceType": self._guess_service_type(role_name_lower)
                        })
                        
                except Exception as e:
                    self.errors.append(f"IAM role processing error for {role.get('RoleName', 'unknown')}: {e}")
                    continue
            
            # Analizza policies (basic analysis)
            for policy in policies:
                try:
                    policy_name = policy.get("PolicyName")
                    if not policy_name:
                        continue
                    
                    # Per ora, segniamo policy custom create da molto tempo come potenzialmente inutilizzate
                    # (avremmo bisogno di API aggiuntive per un'analisi completa)
                    creation_date = policy.get("CreateDate")
                    if creation_date:
                        try:
                            created = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
                            days_old = (current_date - created.replace(tzinfo=None)).days
                            if days_old > 180:  # Policy vecchie di 6+ mesi
                                unused_policies.append({
                                    "PolicyName": policy_name,
                                    "CreationDate": creation_date,
                                    "DaysOld": days_old,
                                    "Arn": policy.get("Arn", ""),
                                    "Description": policy.get("Description", "")
                                })
                        except Exception:
                            pass
                            
                except Exception as e:
                    self.errors.append(f"IAM policy processing error for {policy.get('PolicyName', 'unknown')}: {e}")
                    continue
            
            audit_data = {
                "metadata": {
                    "processed_at": current_date.isoformat(),
                    "total_users": len(users),
                    "total_roles": len(roles),
                    "total_policies": len(policies)
                },
                "old_users": old_users,
                "admin_roles": admin_roles,
                "service_roles": service_roles,
                "unused_policies": unused_policies,
                "summary": {
                    "total_old_users": len(old_users),
                    "total_admin_roles": len(admin_roles),
                    "total_service_roles": len(service_roles),
                    "total_unused_policies": len(unused_policies)
                }
            }
            
            if self._save_json("iam_audit.json", audit_data):
                print(f"      ✅ {len(old_users)} old users, {len(admin_roles)} admin roles, {len(unused_policies)} old policies")
                return True
            return False
            
        except Exception as e:
            error_msg = f"IAM processing failed: {e}"
            print(f"   ❌ {error_msg}")
            self.errors.append(error_msg)
            return False
    
    def _process_vpc_data(self) -> bool:
        """Elabora dati VPC per audit"""
        print("   🌐 Processing VPC resources...")
        
        try:
            vpc_data = self._load_json("vpc_raw.json")
            subnet_data = self._load_json("subnet_raw.json")
            igw_data = self._load_json("igw_raw.json")
            route_table_data = self._load_json("route_table_raw.json")
            
            if not vpc_data:
                return False
            
            default_vpcs = []
            unused_vpcs = []
            public_subnets = []
            private_subnets = []
            
            vpcs = vpc_data.get("Vpcs", [])
            subnets = subnet_data.get("Subnets", []) if subnet_data else []
            igws = igw_data.get("InternetGateways", []) if igw_data else []
            route_tables = route_table_data.get("RouteTables", []) if route_table_data else []
            
            # Mappa IGW per VPC
            vpc_igw_map = {}
            for igw in igws:
                for attachment in igw.get("Attachments", []):
                    vpc_id = attachment.get("VpcId")
                    if vpc_id:
                        vpc_igw_map[vpc_id] = igw.get("InternetGatewayId")
            
            # Mappa subnet usage
            subnet_usage = {}
            for subnet in subnets:
                subnet_id = subnet.get("SubnetId")
                vpc_id = subnet.get("VpcId")
                if subnet_id and vpc_id:
                    if vpc_id not in subnet_usage:
                        subnet_usage[vpc_id] = []
                    subnet_usage[vpc_id].append(subnet)
            
            # Analizza VPCs
            for vpc in vpcs:
                try:
                    vpc_id = vpc.get("VpcId")
                    if not vpc_id:
                        continue
                    
                    # Check default VPC
                    if vpc.get("IsDefault", False):
                        default_vpcs.append({
                            "VpcId": vpc_id,
                            "CidrBlock": vpc.get("CidrBlock"),
                            "State": vpc.get("State"),
                            "HasInternetGateway": vpc_id in vpc_igw_map,
                            "SubnetCount": len(subnet_usage.get(vpc_id, []))
                        })
                    
                    # Check unused VPCs (no subnets)
                    if not subnet_usage.get(vpc_id):
                        unused_vpcs.append({
                            "VpcId": vpc_id,
                            "CidrBlock": vpc.get("CidrBlock"),
                            "State": vpc.get("State"),
                            "IsDefault": vpc.get("IsDefault", False)
                        })
                        
                except Exception as e:
                    self.errors.append(f"VPC processing error for {vpc.get('VpcId', 'unknown')}: {e}")
                    continue
            
            # Analizza Subnets per determinare pubbliche/private
            for subnet in subnets:
                try:
                    subnet_id = subnet.get("SubnetId")
                    vpc_id = subnet.get("VpcId")
                    
                    if not subnet_id or not vpc_id:
                        continue
                    
                    # Determina se subnet è pubblica controllando route tables
                    is_public = False
                    for rt in route_tables:
                        # Check se questa subnet è associata a questa route table
                        for assoc in rt.get("Associations", []):
                            if assoc.get("SubnetId") == subnet_id:
                                # Check se route table ha route verso IGW
                                for route in rt.get("Routes", []):
                                    if route.get("GatewayId", "").startswith("igw-"):
                                        is_public = True
                                        break
                                break
                        if is_public:
                            break
                    
                    subnet_info = {
                        "SubnetId": subnet_id,
                        "VpcId": vpc_id,
                        "CidrBlock": subnet.get("CidrBlock"),
                        "AvailabilityZone": subnet.get("AvailabilityZone"),
                        "State": subnet.get("State"),
                        "MapPublicIpOnLaunch": subnet.get("MapPublicIpOnLaunch", False)
                    }
                    
                    if is_public:
                        public_subnets.append(subnet_info)
                    else:
                        private_subnets.append(subnet_info)
                        
                except Exception as e:
                    self.errors.append(f"Subnet processing error for {subnet.get('SubnetId', 'unknown')}: {e}")
                    continue
            
            audit_data = {
                "metadata": {
                    "processed_at": datetime.now().isoformat(),
                    "total_vpcs": len(vpcs),
                    "total_subnets": len(subnets),
                    "total_igws": len(igws),
                    "total_route_tables": len(route_tables)
                },
                "default_vpcs": default_vpcs,
                "unused_vpcs": unused_vpcs,
                "public_subnets": public_subnets,
                "private_subnets": private_subnets,
                "summary": {
                    "total_default_vpcs": len(default_vpcs),
                    "total_unused_vpcs": len(unused_vpcs),
                    "total_public_subnets": len(public_subnets),
                    "total_private_subnets": len(private_subnets)
                }
            }
            
            if self._save_json("vpc_audit.json", audit_data):
                print(f"      ✅ {len(default_vpcs)} default VPCs, {len(public_subnets)} public subnets, {len(unused_vpcs)} unused VPCs")
                return True
            return False
            
        except Exception as e:
            error_msg = f"VPC processing failed: {e}"
            print(f"   ❌ {error_msg}")
            self.errors.append(error_msg)
            return False
    
    def _get_instance_name(self, instance: Dict[str, Any]) -> str:
        """Estrae il nome dell'istanza dai tag"""
        try:
            for tag in instance.get("Tags", []):
                if tag.get("Key") == "Name":
                    return tag.get("Value", instance.get("InstanceId", "Unknown"))
            return instance.get("InstanceId", "Unknown")
        except Exception:
            return "Unknown"
    
    def _get_port_name(self, port: int) -> str:
        """Ritorna nome servizio per porta"""
        port_names = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP", 
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            993: "IMAPS",
            995: "POP3S",
            1433: "MSSQL",
            3306: "MySQL",
            3389: "RDP",
            5432: "PostgreSQL",
            5984: "CouchDB",
            6379: "Redis",
            27017: "MongoDB"
        }
        return port_names.get(port, f"Port {port}")
    
    def _guess_service_type(self, role_name_lower: str) -> str:
        """Indovina il tipo di servizio dal nome del ruolo"""
        if "lambda" in role_name_lower:
            return "Lambda"
        elif "ec2" in role_name_lower:
            return "EC2"
        elif "s3" in role_name_lower:
            return "S3"
        elif "rds" in role_name_lower:
            return "RDS"
        elif "ecs" in role_name_lower:
            return "ECS"
        elif "eks" in role_name_lower:
            return "EKS"
        elif "api" in role_name_lower or "gateway" in role_name_lower:
            return "API Gateway"
        elif "cloudformation" in role_name_lower:
            return "CloudFormation"
        else:
            return "Generic Service"
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Ritorna summary del processing"""
        return {
            "processed_files": self.processed_files,
            "errors": self.errors,
            "success": len(self.processed_files) > 0,
            "error_count": len(self.errors)
        }
# utils/async_fetcher.py
import asyncio
import aioboto3
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from config.settings import AWSConfig

class AsyncAWSFetcher:
    """Fetcher asincrono multi-region per risorse AWS"""
    
    def __init__(self, config: AWSConfig):
        self.config = config
        self.session = aioboto3.Session()
        # Fallback a boto3 sincrono per IAM (globale)
        self.sync_session = boto3.Session(profile_name=config.profile)
        
    async def fetch_all_resources(self) -> Dict[str, Any]:
        """Fetch tutte le risorse abilitate in tutte le regioni"""
        print(f"🌍 Fetching risorse da {len(self.config.regions)} regioni...")
        print(f"📋 Servizi abilitati: {', '.join(self.config.get_active_services())}")
        
        # Pulisci directory data prima del fetch
        self._cleanup_data_directory()
        
        all_results = {}
        
        # Fetch servizi regionali in parallelo
        regional_tasks = []
        for region in self.config.regions:
            regional_tasks.append(self._fetch_region_resources(region))
        
        # Esegui fetch regionali in parallelo
        if regional_tasks:
            regional_results = await asyncio.gather(*regional_tasks, return_exceptions=True)
            
            # Combina risultati regionali - FIX: gestione corretta
            for result in regional_results:
                if isinstance(result, Exception):
                    print(f"❌ Errore durante fetch: {result}")
                    continue
                
                # Merge dei risultati
                if isinstance(result, dict):
                    all_results.update(result)
        
        # Fetch servizi globali (IAM) in modo sincrono
        if self.config.is_service_enabled("iam"):
            print("🔐 Fetching IAM resources (global)...")
            iam_results = self._fetch_iam_resources_sync()
            all_results.update(iam_results)
        
        # Salva risultati
        await self._save_results(all_results)
        
        print(f"✅ Fetch completato! Risorse salvate in /data")
        return all_results
    
    def _cleanup_data_directory(self):
        """Pulisce la directory data da file vecchi"""
        data_dir = "data"
        if os.path.exists(data_dir):
            print("🧹 Pulizia directory data...")
            for file in os.listdir(data_dir):
                if file.endswith(('.json', '.tmp', '.bak')):
                    file_path = os.path.join(data_dir, file)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"⚠️  Impossibile rimuovere {file}: {e}")
        else:
            os.makedirs(data_dir, exist_ok=True)
    
    async def _fetch_region_resources(self, region: str) -> Dict[str, Any]:
        """Fetch tutte le risorse per una singola regione"""
        print(f"🌍 Fetching resources from {region}...")
        
        results = {}
        
        try:
            # Fetch EC2/VPC resources
            if any(self.config.is_service_enabled(svc) for svc in 
                   ["ec2", "eni", "sg", "vpc", "subnet", "igw", "route_table"]):
                ec2_results = await self._fetch_ec2_resources(region)
                results.update(ec2_results)
            
            # Fetch S3 resources (solo per la prima regione)
            if self.config.is_service_enabled("s3") and region == self.config.regions[0]:
                s3_results = await self._fetch_s3_resources(region)
                results.update(s3_results)
                
        except Exception as e:
            print(f"❌ Errore connessione {region}: {e}")
            
        return results
    
    async def _fetch_ec2_resources(self, region: str) -> Dict[str, Any]:
        """Fetch tutte le risorse EC2 per una regione"""
        print(f"🖥️  Fetching EC2 resources from {region}...")
        
        results = {}
        
        try:
            async with self.session.client('ec2', region_name=region) as ec2:
                # Fetch in parallelo tutte le risorse EC2
                tasks = []
                
                if self.config.is_service_enabled("ec2"):
                    tasks.append(self._fetch_ec2_instances(ec2, region))
                if self.config.is_service_enabled("eni"):
                    tasks.append(self._fetch_enis(ec2, region))
                if self.config.is_service_enabled("sg"):
                    tasks.append(self._fetch_security_groups(ec2, region))
                if self.config.is_service_enabled("vpc"):
                    tasks.append(self._fetch_vpcs(ec2, region))
                if self.config.is_service_enabled("subnet"):
                    tasks.append(self._fetch_subnets(ec2, region))
                if self.config.is_service_enabled("igw"):
                    tasks.append(self._fetch_internet_gateways(ec2, region))
                if self.config.is_service_enabled("route_table"):
                    tasks.append(self._fetch_route_tables(ec2, region))
                
                # Esegui tutte le chiamate in parallelo
                if tasks:
                    task_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Combina risultati
                    for task_result in task_results:
                        if isinstance(task_result, Exception):
                            print(f"❌ Errore fetch {region}: {task_result}")
                            continue
                        if isinstance(task_result, dict):
                            results.update(task_result)
                        
        except Exception as e:
            print(f"❌ Errore connessione EC2 {region}: {e}")
            
        return results
    
    async def _fetch_ec2_instances(self, ec2_client, region: str) -> Dict[str, Any]:
        """Fetch istanze EC2"""
        try:
            paginator = ec2_client.get_paginator('describe_instances')
            instances = {"Reservations": []}
            
            async for page in paginator.paginate():
                instances["Reservations"].extend(page["Reservations"])
            
            instance_count = sum(len(r['Instances']) for r in instances['Reservations'])
            print(f"   ✅ EC2 instances: {instance_count}")
            return {"ec2_raw": instances}
        except Exception as e:
            print(f"   ❌ EC2 instances error: {e}")
            return {"ec2_raw": {"Reservations": []}}
    
    async def _fetch_enis(self, ec2_client, region: str) -> Dict[str, Any]:
        """Fetch Elastic Network Interfaces"""
        try:
            paginator = ec2_client.get_paginator('describe_network_interfaces')
            enis = {"NetworkInterfaces": []}
            
            async for page in paginator.paginate():
                enis["NetworkInterfaces"].extend(page["NetworkInterfaces"])
            
            print(f"   ✅ ENIs: {len(enis['NetworkInterfaces'])}")
            return {"eni_raw": enis}
        except Exception as e:
            print(f"   ❌ ENI error: {e}")
            return {"eni_raw": {"NetworkInterfaces": []}}
    
    async def _fetch_security_groups(self, ec2_client, region: str) -> Dict[str, Any]:
        """Fetch Security Groups"""
        try:
            paginator = ec2_client.get_paginator('describe_security_groups')
            sgs = {"SecurityGroups": []}
            
            async for page in paginator.paginate():
                sgs["SecurityGroups"].extend(page["SecurityGroups"])
            
            print(f"   ✅ Security Groups: {len(sgs['SecurityGroups'])}")
            return {"sg_raw": sgs}
        except Exception as e:
            print(f"   ❌ Security Groups error: {e}")
            return {"sg_raw": {"SecurityGroups": []}}
    
    async def _fetch_vpcs(self, ec2_client, region: str) -> Dict[str, Any]:
        """Fetch VPCs"""
        try:
            response = await ec2_client.describe_vpcs()
            print(f"   ✅ VPCs: {len(response['Vpcs'])}")
            return {"vpc_raw": response}
        except Exception as e:
            print(f"   ❌ VPC error: {e}")
            return {"vpc_raw": {"Vpcs": []}}
    
    async def _fetch_subnets(self, ec2_client, region: str) -> Dict[str, Any]:
        """Fetch Subnets"""
        try:
            paginator = ec2_client.get_paginator('describe_subnets')
            subnets = {"Subnets": []}
            
            async for page in paginator.paginate():
                subnets["Subnets"].extend(page["Subnets"])
            
            print(f"   ✅ Subnets: {len(subnets['Subnets'])}")
            return {"subnet_raw": subnets}
        except Exception as e:
            print(f"   ❌ Subnets error: {e}")
            return {"subnet_raw": {"Subnets": []}}
    
    async def _fetch_internet_gateways(self, ec2_client, region: str) -> Dict[str, Any]:
        """Fetch Internet Gateways"""
        try:
            response = await ec2_client.describe_internet_gateways()
            print(f"   ✅ Internet Gateways: {len(response['InternetGateways'])}")
            return {"igw_raw": response}
        except Exception as e:
            print(f"   ❌ IGW error: {e}")
            return {"igw_raw": {"InternetGateways": []}}
    
    async def _fetch_route_tables(self, ec2_client, region: str) -> Dict[str, Any]:
        """Fetch Route Tables"""
        try:
            paginator = ec2_client.get_paginator('describe_route_tables')
            route_tables = {"RouteTables": []}
            
            async for page in paginator.paginate():
                route_tables["RouteTables"].extend(page["RouteTables"])
            
            print(f"   ✅ Route Tables: {len(route_tables['RouteTables'])}")
            return {"route_table_raw": route_tables}
        except Exception as e:
            print(f"   ❌ Route Tables error: {e}")
            return {"route_table_raw": {"RouteTables": []}}
    
    async def _fetch_s3_resources(self, region: str) -> Dict[str, Any]:
        """Fetch risorse S3 (globali ma con region context)"""
        print(f"🗂️  Fetching S3 resources...")
        
        try:
            async with self.session.client('s3', region_name=region) as s3:
                # Lista bucket
                buckets_response = await s3.list_buckets()
                buckets = buckets_response.get("Buckets", [])
                
                s3_data = []
                
                # Process bucket limitato per evitare timeout
                for i, bucket in enumerate(buckets[:50]):  # Limita a 50 bucket per performance
                    bucket_name = bucket["Name"]
                    bucket_info = {
                        "Name": bucket_name,
                        "CreationDate": str(bucket.get("CreationDate", "")),
                        "Region": region,
                        "Policy": None,
                        "ACL": None, 
                        "PublicAccess": False
                    }
                    
                    try:
                        # Timeout rapido per evitare blocchi
                        bucket_location = await asyncio.wait_for(
                            s3.get_bucket_location(Bucket=bucket_name),
                            timeout=5.0
                        )
                        bucket_info["ActualRegion"] = bucket_location.get('LocationConstraint', 'us-east-1')
                    except asyncio.TimeoutError:
                        bucket_info["ActualRegion"] = "unknown"
                    except Exception:
                        bucket_info["ActualRegion"] = "error"
                    
                    # Check ACL veloce
                    try:
                        acl = await asyncio.wait_for(
                            s3.get_bucket_acl(Bucket=bucket_name),
                            timeout=3.0
                        )
                        bucket_info["ACL"] = "present"
                        for grant in acl.get("Grants", []):
                            grantee = grant.get("Grantee", {})
                            if grantee.get("URI", "").endswith("AllUsers"):
                                bucket_info["PublicAccess"] = True
                    except asyncio.TimeoutError:
                        bucket_info["ACL"] = "timeout"
                    except Exception:
                        bucket_info["ACL"] = "private"
                    
                    s3_data.append(bucket_info)
                
                print(f"   ✅ S3 Buckets: {len(s3_data)} (max 50)")
                return {"s3_raw": s3_data}
                
        except Exception as e:
            print(f"   ❌ S3 error: {e}")
            return {"s3_raw": []}
    
    def _fetch_iam_resources_sync(self) -> Dict[str, Any]:
        """Fetch risorse IAM (sincrono perché sono globali)"""
        try:
            iam = self.sync_session.client('iam')
            
            result = {"Users": [], "Roles": [], "Policies": []}
            
            # Users con limite
            try:
                paginator = iam.get_paginator('list_users')
                user_count = 0
                for page in paginator.paginate():
                    page_users = page["Users"]
                    result["Users"].extend(page_users)
                    user_count += len(page_users)
                    if user_count >= 100:  # Limite per performance
                        break
            except Exception as e:
                print(f"   ⚠️  IAM Users error: {e}")
            
            # Roles con limite
            try:
                paginator = iam.get_paginator('list_roles')
                role_count = 0
                for page in paginator.paginate():
                    page_roles = page["Roles"]
                    result["Roles"].extend(page_roles)
                    role_count += len(page_roles)
                    if role_count >= 100:  # Limite per performance
                        break
            except Exception as e:
                print(f"   ⚠️  IAM Roles error: {e}")
            
            # Policies (solo custom) con limite
            try:
                paginator = iam.get_paginator('list_policies')
                policy_count = 0
                for page in paginator.paginate(Scope='Local'):
                    page_policies = page["Policies"]
                    result["Policies"].extend(page_policies)
                    policy_count += len(page_policies)
                    if policy_count >= 50:  # Limite per performance
                        break
            except Exception as e:
                print(f"   ⚠️  IAM Policies error: {e}")
            
            print(f"   ✅ IAM: {len(result['Users'])} users, {len(result['Roles'])} roles, {len(result['Policies'])} policies")
            return {"iam_raw": result}
            
        except Exception as e:
            print(f"   ❌ IAM error: {e}")
            return {"iam_raw": {"Users": [], "Roles": [], "Policies": []}}
    
    async def _save_results(self, results: Dict[str, Any]):
        """Salva risultati su file con timestamp"""
        os.makedirs("data", exist_ok=True)
        
        def default_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        
        # Salva ogni tipo di dato
        saved_files = 0
        for data_type, data in results.items():
            if not data:  # Skip empty data
                continue
                
            filename = f"data/{data_type}.json"
            
            try:
                with open(filename, "w") as f:
                    json.dump(data, f, indent=2, default=default_serializer)
                saved_files += 1
                
                # Log dimensione file
                file_size = os.path.getsize(filename)
                if file_size > 1024 * 1024:  # > 1MB
                    print(f"   📁 {data_type}.json: {file_size // (1024*1024)}MB")
                else:
                    print(f"   📁 {data_type}.json: {file_size // 1024}KB")
                    
            except Exception as e:
                print(f"   ❌ Errore salvataggio {data_type}.json: {e}")
                
        print(f"💾 Salvati {saved_files}/{len(results)} file di dati in /data")
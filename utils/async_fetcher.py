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
        
        all_results = {}
        
        # Fetch servizi regionali in parallelo
        regional_tasks = []
        for region in self.config.regions:
            if self.config.is_service_enabled("ec2"):
                regional_tasks.append(self._fetch_ec2_resources(region))
            if self.config.is_service_enabled("s3"):
                regional_tasks.append(self._fetch_s3_resources(region))
        
        # Esegui fetch regionali in parallelo
        if regional_tasks:
            regional_results = await asyncio.gather(*regional_tasks, return_exceptions=True)
            
            # Combina risultati regionali - FIX: gestione corretta della struttura dati
            for result in regional_results:
                if isinstance(result, Exception):
                    print(f"❌ Errore durante fetch: {result}")
                    continue
                
                # Ora result è una dict con chiavi region
                for region_key, region_data in result.items():
                    if isinstance(region_data, dict):
                        # Merge dei dati per tipo
                        for data_type, data_content in region_data.items():
                            all_results[data_type] = data_content
                    else:
                        # Se non è un dict, trattalo come data type diretto
                        all_results[region_key] = region_data
        
        # Fetch servizi globali (IAM) in modo sincrono
        if self.config.is_service_enabled("iam"):
            print("🔐 Fetching IAM resources (global)...")
            iam_results = self._fetch_iam_resources_sync()
            all_results.update(iam_results)
        
        # Salva risultati
        await self._save_results(all_results)
        
        print(f"✅ Fetch completato! Risorse salvate in /data")
        return all_results
    
    async def _fetch_ec2_resources(self, region: str) -> Dict[str, Any]:
        """Fetch tutte le risorse EC2 per una regione"""
        print(f"🖥️  Fetching EC2 resources from {region}...")
        
        # FIX: struttura dati semplificata
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
                task_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Combina risultati
                for task_result in task_results:
                    if isinstance(task_result, Exception):
                        print(f"❌ Errore fetch {region}: {task_result}")
                        continue
                    if isinstance(task_result, dict):
                        results.update(task_result)
                        
        except Exception as e:
            print(f"❌ Errore connessione {region}: {e}")
            
        return {region: results}
    
    async def _fetch_ec2_instances(self, ec2_client, region: str) -> Dict[str, Any]:
        """Fetch istanze EC2"""
        try:
            paginator = ec2_client.get_paginator('describe_instances')
            instances = {"Reservations": []}
            
            async for page in paginator.paginate():
                instances["Reservations"].extend(page["Reservations"])
            
            print(f"   ✅ EC2 instances: {sum(len(r['Instances']) for r in instances['Reservations'])}")
            return {"ec2_raw": instances}
        except Exception as e:
            print(f"   ❌ EC2 instances error: {e}")
            return {"ec2_raw": {"Reservations": []}}
    
    async def _fetch_enis(self, ec2_client, region: str) -> Dict[str, Any]:
        """Fetch Elastic Network Interfaces"""
        try:
            response = await ec2_client.describe_network_interfaces()
            print(f"   ✅ ENIs: {len(response['NetworkInterfaces'])}")
            return {"eni_raw": response}
        except Exception as e:
            print(f"   ❌ ENI error: {e}")
            return {"eni_raw": {"NetworkInterfaces": []}}
    
    async def _fetch_security_groups(self, ec2_client, region: str) -> Dict[str, Any]:
        """Fetch Security Groups"""
        try:
            response = await ec2_client.describe_security_groups()
            print(f"   ✅ Security Groups: {len(response['SecurityGroups'])}")
            return {"sg_raw": response}
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
            response = await ec2_client.describe_subnets()
            print(f"   ✅ Subnets: {len(response['Subnets'])}")
            return {"subnet_raw": response}
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
            response = await ec2_client.describe_route_tables()
            print(f"   ✅ Route Tables: {len(response['RouteTables'])}")
            return {"route_table_raw": response}
        except Exception as e:
            print(f"   ❌ Route Tables error: {e}")
            return {"route_table_raw": {"RouteTables": []}}
    
    async def _fetch_s3_resources(self, region: str) -> Dict[str, Any]:
        """Fetch risorse S3 (globali ma con region context)"""
        if region != self.config.regions[0]:  # Fetch S3 solo per la prima regione
            return {}
            
        print(f"🗂️  Fetching S3 resources...")
        
        try:
            async with self.session.client('s3', region_name=region) as s3:
                # Lista bucket
                buckets_response = await s3.list_buckets()
                buckets = buckets_response.get("Buckets", [])
                
                s3_data = []
                for bucket in buckets:
                    bucket_name = bucket["Name"]
                    bucket_info = {
                        "Name": bucket_name,
                        "CreationDate": str(bucket.get("CreationDate", "")),
                        "Region": region,
                        "Policy": None,
                        "ACL": None, 
                        "PublicAccess": False
                    }
                    
                    # Check bucket policy (può fallire)
                    try:
                        policy = await s3.get_bucket_policy(Bucket=bucket_name)
                        bucket_info["Policy"] = policy.get("Policy", "")
                    except:
                        bucket_info["Policy"] = None
                    
                    # Check ACL (può fallire)
                    try:
                        acl = await s3.get_bucket_acl(Bucket=bucket_name)
                        bucket_info["ACL"] = acl
                        for grant in acl.get("Grants", []):
                            grantee = grant.get("Grantee", {})
                            if grantee.get("URI", "").endswith("AllUsers"):
                                bucket_info["PublicAccess"] = True
                    except:
                        bucket_info["ACL"] = None
                    
                    s3_data.append(bucket_info)
                
                print(f"   ✅ S3 Buckets: {len(s3_data)}")
                return {"s3_raw": s3_data}
                
        except Exception as e:
            print(f"   ❌ S3 error: {e}")
            return {"s3_raw": []}
    
    def _fetch_iam_resources_sync(self) -> Dict[str, Any]:
        """Fetch risorse IAM (sincrono perché sono globali)"""
        try:
            iam = self.sync_session.client('iam')
            
            result = {"Users": [], "Roles": [], "Policies": []}
            
            # Users
            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                result["Users"].extend(page["Users"])
            
            # Roles
            paginator = iam.get_paginator('list_roles')
            for page in paginator.paginate():
                result["Roles"].extend(page["Roles"])
            
            # Policies (solo custom)
            paginator = iam.get_paginator('list_policies')
            for page in paginator.paginate(Scope='Local'):
                result["Policies"].extend(page["Policies"])
            
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
        
        # Salva ogni tipo di dato in un file separato
        for data_type, data in results.items():
            filename = f"data/{data_type}.json"
            
            # Se il file esiste già, decide se mergiare o sovrascrivere
            existing_data = {}
            if os.path.exists(filename):
                try:
                    with open(filename) as f:
                        existing_data = json.load(f)
                except:
                    existing_data = {}
            
            # Merge logic per diversi tipi di dati
            if data_type.endswith("_raw"):
                # Per dati raw, sovrascriviamo sempre (sono più recenti)
                final_data = data
                
                # Eccetto per multi-region dove vogliamo appendere
                if isinstance(data, dict) and isinstance(existing_data, dict):
                    # Se entrambi hanno struttura simile, mergia
                    for key, value in data.items():
                        if key in existing_data and isinstance(value, list) and isinstance(existing_data[key], list):
                            # Merge liste (per multi-region)
                            final_data[key] = existing_data[key] + value
                        else:
                            final_data[key] = value
                else:
                    final_data = data
            else:
                final_data = data
            
            # Salva i dati
            with open(filename, "w") as f:
                json.dump(final_data, f, indent=2, default=default_serializer)
                
        print(f"💾 Salvati {len(results)} file di dati in /data")
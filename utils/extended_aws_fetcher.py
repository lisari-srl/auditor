# utils/extended_aws_fetcher.py
import asyncio
import aioboto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from utils.async_fetcher import AsyncAWSFetcher

class ExtendedAWSFetcher(AsyncAWSFetcher):
    """Fetcher esteso per mappatura completa dell'infrastruttura AWS"""
    
    async def fetch_all_extended_resources(self) -> Dict[str, Any]:
        """Fetch completo di tutte le risorse AWS per analisi costi e ottimizzazione"""
        print("🌐 Fetching COMPLETE AWS infrastructure...")
        
        # Cleanup e fetch base
        await super().fetch_all_resources()
        
        # Fetch risorse aggiuntive
        extended_results = {}
        
        # Parallelize fetching across regions
        regional_tasks = []
        for region in self.config.regions:
            regional_tasks.append(self._fetch_extended_region_resources(region))
        
        if regional_tasks:
            results = await asyncio.gather(*regional_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict):
                    extended_results.update(result)
        
        # Fetch global services
        global_results = await self._fetch_global_services()
        extended_results.update(global_results)
        
        # Save extended results
        await self._save_extended_results(extended_results)
        
        print(f"✅ Extended fetch completed! {len(extended_results)} service types collected")
        return extended_results
    
    async def _fetch_extended_region_resources(self, region: str) -> Dict[str, Any]:
        """Fetch risorse estese per regione"""
        print(f"🔍 Extended fetching from {region}...")
        
        results = {}
        
        try:
            # RDS Resources
            results.update(await self._fetch_rds_resources(region))
            
            # Lambda Functions
            results.update(await self._fetch_lambda_resources(region))
            
            # ELB/ALB/NLB
            results.update(await self._fetch_load_balancer_resources(region))
            
            # CloudWatch Resources
            results.update(await self._fetch_cloudwatch_resources(region))
            
            # Auto Scaling Groups
            results.update(await self._fetch_autoscaling_resources(region))
            
            # ECS/EKS Resources
            results.update(await self._fetch_container_resources(region))
            
            # ElastiCache
            results.update(await self._fetch_elasticache_resources(region))
            
            # Redshift
            results.update(await self._fetch_redshift_resources(region))
            
            # EFS/FSx
            results.update(await self._fetch_filesystem_resources(region))
            
            # NAT Gateways
            results.update(await self._fetch_nat_gateways(region))
            
            # VPC Endpoints
            results.update(await self._fetch_vpc_endpoints(region))
            
            # Elastic IPs
            results.update(await self._fetch_elastic_ips(region))
            
            # EBS Snapshots
            results.update(await self._fetch_ebs_snapshots(region))
            
            # AMIs
            results.update(await self._fetch_amis(region))
            
        except Exception as e:
            print(f"❌ Error in extended fetching {region}: {e}")
        
        return results
    
    async def _fetch_rds_resources(self, region: str) -> Dict[str, Any]:
        """Fetch RDS instances, clusters, snapshots"""
        try:
            async with self.session.client('rds', region_name=region) as rds:
                # DB Instances
                instances_paginator = rds.get_paginator('describe_db_instances')
                instances = []
                async for page in instances_paginator.paginate():
                    instances.extend(page['DBInstances'])
                
                # DB Clusters (Aurora)
                clusters_paginator = rds.get_paginator('describe_db_clusters')
                clusters = []
                async for page in clusters_paginator.paginate():
                    clusters.extend(page['DBClusters'])
                
                # Snapshots
                snapshots_paginator = rds.get_paginator('describe_db_snapshots')
                snapshots = []
                async for page in snapshots_paginator.paginate(OwnerFilter='self'):
                    snapshots.extend(page['DBSnapshots'])
                
                # Parameter Groups
                param_groups = await rds.describe_db_parameter_groups()
                
                # Subnet Groups
                subnet_groups = await rds.describe_db_subnet_groups()
                
                print(f"   ✅ RDS: {len(instances)} instances, {len(clusters)} clusters, {len(snapshots)} snapshots")
                
                return {
                    "rds_raw": {
                        "DBInstances": instances,
                        "DBClusters": clusters,
                        "DBSnapshots": snapshots,
                        "DBParameterGroups": param_groups['DBParameterGroups'],
                        "DBSubnetGroups": subnet_groups['DBSubnetGroups']
                    }
                }
        except Exception as e:
            print(f"   ❌ RDS error: {e}")
            return {"rds_raw": {"DBInstances": [], "DBClusters": [], "DBSnapshots": []}}
    
    async def _fetch_lambda_resources(self, region: str) -> Dict[str, Any]:
        """Fetch Lambda functions e configurazioni"""
        try:
            async with self.session.client('lambda', region_name=region) as lambda_client:
                # Functions
                functions_paginator = lambda_client.get_paginator('list_functions')
                functions = []
                async for page in functions_paginator.paginate():
                    functions.extend(page['Functions'])
                
                # Event Source Mappings
                esm_paginator = lambda_client.get_paginator('list_event_source_mappings')
                event_mappings = []
                async for page in esm_paginator.paginate():
                    event_mappings.extend(page['EventSourceMappings'])
                
                # Layers
                layers_paginator = lambda_client.get_paginator('list_layers')
                layers = []
                async for page in layers_paginator.paginate():
                    layers.extend(page['Layers'])
                
                print(f"   ✅ Lambda: {len(functions)} functions, {len(layers)} layers")
                
                return {
                    "lambda_raw": {
                        "Functions": functions,
                        "EventSourceMappings": event_mappings,
                        "Layers": layers
                    }
                }
        except Exception as e:
            print(f"   ❌ Lambda error: {e}")
            return {"lambda_raw": {"Functions": [], "EventSourceMappings": [], "Layers": []}}
    
    async def _fetch_load_balancer_resources(self, region: str) -> Dict[str, Any]:
        """Fetch tutti i tipi di Load Balancer"""
        try:
            lb_data = {"ApplicationLoadBalancers": [], "NetworkLoadBalancers": [], "ClassicLoadBalancers": []}
            
            # ALB/NLB
            async with self.session.client('elbv2', region_name=region) as elbv2:
                lbs_paginator = elbv2.get_paginator('describe_load_balancers')
                async for page in lbs_paginator.paginate():
                    for lb in page['LoadBalancers']:
                        if lb['Type'] == 'application':
                            lb_data["ApplicationLoadBalancers"].append(lb)
                        elif lb['Type'] == 'network':
                            lb_data["NetworkLoadBalancers"].append(lb)
                
                # Target Groups
                tgs_paginator = elbv2.get_paginator('describe_target_groups')
                target_groups = []
                async for page in tgs_paginator.paginate():
                    target_groups.extend(page['TargetGroups'])
                
                lb_data["TargetGroups"] = target_groups
            
            # Classic Load Balancers
            async with self.session.client('elb', region_name=region) as elb:
                clbs_paginator = elb.get_paginator('describe_load_balancers')
                async for page in clbs_paginator.paginate():
                    lb_data["ClassicLoadBalancers"].extend(page['LoadBalancerDescriptions'])
            
            total_lbs = len(lb_data["ApplicationLoadBalancers"]) + len(lb_data["NetworkLoadBalancers"]) + len(lb_data["ClassicLoadBalancers"])
            print(f"   ✅ Load Balancers: {total_lbs} total")
            
            return {"lb_raw": lb_data}
            
        except Exception as e:
            print(f"   ❌ Load Balancer error: {e}")
            return {"lb_raw": {"ApplicationLoadBalancers": [], "NetworkLoadBalancers": [], "ClassicLoadBalancers": []}}
    
    async def _fetch_cloudwatch_resources(self, region: str) -> Dict[str, Any]:
        """Fetch CloudWatch alarms, dashboards, log groups"""
        try:
            async with self.session.client('cloudwatch', region_name=region) as cw:
                # Alarms
                alarms_paginator = cw.get_paginator('describe_alarms')
                alarms = []
                async for page in alarms_paginator.paginate():
                    alarms.extend(page['MetricAlarms'])
                
                # Dashboards
                dashboards_response = await cw.list_dashboards()
                dashboards = dashboards_response['DashboardEntries']
                
                # Custom Metrics (sample)
                metrics_paginator = cw.get_paginator('list_metrics')
                custom_metrics = []
                async for page in metrics_paginator.paginate():
                    for metric in page['Metrics']:
                        if not metric['Namespace'].startswith('AWS/'):
                            custom_metrics.append(metric)
                    if len(custom_metrics) > 100:  # Limit for performance
                        break
            
            # CloudWatch Logs
            async with self.session.client('logs', region_name=region) as logs:
                log_groups_paginator = logs.get_paginator('describe_log_groups')
                log_groups = []
                async for page in log_groups_paginator.paginate():
                    log_groups.extend(page['logGroups'])
            
            print(f"   ✅ CloudWatch: {len(alarms)} alarms, {len(dashboards)} dashboards, {len(log_groups)} log groups")
            
            return {
                "cloudwatch_raw": {
                    "Alarms": alarms,
                    "Dashboards": dashboards,
                    "CustomMetrics": custom_metrics,
                    "LogGroups": log_groups
                }
            }
            
        except Exception as e:
            print(f"   ❌ CloudWatch error: {e}")
            return {"cloudwatch_raw": {"Alarms": [], "Dashboards": [], "LogGroups": []}}
    
    async def _fetch_autoscaling_resources(self, region: str) -> Dict[str, Any]:
        """Fetch Auto Scaling Groups e Launch Configurations"""
        try:
            async with self.session.client('autoscaling', region_name=region) as asg:
                # Auto Scaling Groups
                asgs_paginator = asg.get_paginator('describe_auto_scaling_groups')
                asgs = []
                async for page in asgs_paginator.paginate():
                    asgs.extend(page['AutoScalingGroups'])
                
                # Launch Configurations
                lcs_paginator = asg.get_paginator('describe_launch_configurations')
                launch_configs = []
                async for page in lcs_paginator.paginate():
                    launch_configs.extend(page['LaunchConfigurations'])
                
                # Launch Templates
                async with self.session.client('ec2', region_name=region) as ec2:
                    lts_paginator = ec2.get_paginator('describe_launch_templates')
                    launch_templates = []
                    async for page in lts_paginator.paginate():
                        launch_templates.extend(page['LaunchTemplates'])
                
                print(f"   ✅ Auto Scaling: {len(asgs)} groups, {len(launch_configs)} configs, {len(launch_templates)} templates")
                
                return {
                    "autoscaling_raw": {
                        "AutoScalingGroups": asgs,
                        "LaunchConfigurations": launch_configs,
                        "LaunchTemplates": launch_templates
                    }
                }
        except Exception as e:
            print(f"   ❌ Auto Scaling error: {e}")
            return {"autoscaling_raw": {"AutoScalingGroups": [], "LaunchConfigurations": [], "LaunchTemplates": []}}
    
    async def _fetch_container_resources(self, region: str) -> Dict[str, Any]:
        """Fetch ECS e EKS resources"""
        try:
            container_data = {}
            
            # ECS
            async with self.session.client('ecs', region_name=region) as ecs:
                # Clusters
                clusters_response = await ecs.list_clusters()
                clusters = []
                if clusters_response['clusterArns']:
                    clusters_detail = await ecs.describe_clusters(clusters=clusters_response['clusterArns'])
                    clusters = clusters_detail['clusters']
                
                # Services
                services = []
                for cluster_arn in clusters_response['clusterArns']:
                    services_response = await ecs.list_services(cluster=cluster_arn)
                    if services_response['serviceArns']:
                        services_detail = await ecs.describe_services(
                            cluster=cluster_arn,
                            services=services_response['serviceArns']
                        )
                        services.extend(services_detail['services'])
                
                # Task Definitions
                task_defs_paginator = ecs.get_paginator('list_task_definitions')
                task_definitions = []
                async for page in task_defs_paginator.paginate():
                    task_definitions.extend(page['taskDefinitionArns'])
                
                container_data["ECS"] = {
                    "Clusters": clusters,
                    "Services": services,
                    "TaskDefinitions": task_definitions[:50]  # Limit for performance
                }
            
            # EKS
            async with self.session.client('eks', region_name=region) as eks:
                # Clusters
                eks_clusters_response = await eks.list_clusters()
                eks_clusters = []
                for cluster_name in eks_clusters_response['clusters']:
                    cluster_detail = await eks.describe_cluster(name=cluster_name)
                    eks_clusters.append(cluster_detail['cluster'])
                
                # Node Groups
                nodegroups = []
                for cluster_name in eks_clusters_response['clusters']:
                    ng_response = await eks.list_nodegroups(clusterName=cluster_name)
                    for ng_name in ng_response['nodegroups']:
                        ng_detail = await eks.describe_nodegroup(clusterName=cluster_name, nodegroupName=ng_name)
                        nodegroups.append(ng_detail['nodegroup'])
                
                container_data["EKS"] = {
                    "Clusters": eks_clusters,
                    "NodeGroups": nodegroups
                }
            
            total_resources = len(container_data.get("ECS", {}).get("Clusters", [])) + len(container_data.get("EKS", {}).get("Clusters", []))
            print(f"   ✅ Containers: {total_resources} clusters")
            
            return {"containers_raw": container_data}
            
        except Exception as e:
            print(f"   ❌ Container resources error: {e}")
            return {"containers_raw": {"ECS": {"Clusters": []}, "EKS": {"Clusters": []}}}
    
    async def _fetch_elasticache_resources(self, region: str) -> Dict[str, Any]:
        """Fetch ElastiCache clusters"""
        try:
            async with self.session.client('elasticache', region_name=region) as elasticache:
                # Redis clusters
                redis_clusters_paginator = elasticache.get_paginator('describe_replication_groups')
                redis_clusters = []
                async for page in redis_clusters_paginator.paginate():
                    redis_clusters.extend(page['ReplicationGroups'])
                
                # Memcached clusters
                memcached_clusters_paginator = elasticache.get_paginator('describe_cache_clusters')
                memcached_clusters = []
                async for page in memcached_clusters_paginator.paginate():
                    memcached_clusters.extend(page['CacheClusters'])
                
                # Subnet Groups
                subnet_groups_paginator = elasticache.get_paginator('describe_cache_subnet_groups')
                subnet_groups = []
                async for page in subnet_groups_paginator.paginate():
                    subnet_groups.extend(page['CacheSubnetGroups'])
                
                print(f"   ✅ ElastiCache: {len(redis_clusters)} Redis, {len(memcached_clusters)} Memcached")
                
                return {
                    "elasticache_raw": {
                        "RedisReplicationGroups": redis_clusters,
                        "MemcachedClusters": memcached_clusters,
                        "SubnetGroups": subnet_groups
                    }
                }
        except Exception as e:
            print(f"   ❌ ElastiCache error: {e}")
            return {"elasticache_raw": {"RedisReplicationGroups": [], "MemcachedClusters": []}}
    
    async def _fetch_redshift_resources(self, region: str) -> Dict[str, Any]:
        """Fetch Redshift clusters"""
        try:
            async with self.session.client('redshift', region_name=region) as redshift:
                clusters_paginator = redshift.get_paginator('describe_clusters')
                clusters = []
                async for page in clusters_paginator.paginate():
                    clusters.extend(page['Clusters'])
                
                # Snapshots
                snapshots_paginator = redshift.get_paginator('describe_cluster_snapshots')
                snapshots = []
                async for page in snapshots_paginator.paginate(OwnerFilter='self'):
                    snapshots.extend(page['Snapshots'])
                
                print(f"   ✅ Redshift: {len(clusters)} clusters, {len(snapshots)} snapshots")
                
                return {
                    "redshift_raw": {
                        "Clusters": clusters,
                        "Snapshots": snapshots
                    }
                }
        except Exception as e:
            print(f"   ❌ Redshift error: {e}")
            return {"redshift_raw": {"Clusters": [], "Snapshots": []}}
    
    async def _fetch_filesystem_resources(self, region: str) -> Dict[str, Any]:
        """Fetch EFS e FSx filesystems"""
        try:
            fs_data = {}
            
            # EFS
            async with self.session.client('efs', region_name=region) as efs:
                efs_paginator = efs.get_paginator('describe_file_systems')
                efs_filesystems = []
                async for page in efs_paginator.paginate():
                    efs_filesystems.extend(page['FileSystems'])
                
                fs_data["EFS"] = efs_filesystems
            
            # FSx
            async with self.session.client('fsx', region_name=region) as fsx:
                fsx_paginator = fsx.get_paginator('describe_file_systems')
                fsx_filesystems = []
                async for page in fsx_paginator.paginate():
                    fsx_filesystems.extend(page['FileSystems'])
                
                fs_data["FSx"] = fsx_filesystems
            
            total_fs = len(fs_data.get("EFS", [])) + len(fs_data.get("FSx", []))
            print(f"   ✅ Filesystems: {total_fs} total")
            
            return {"filesystem_raw": fs_data}
            
        except Exception as e:
            print(f"   ❌ Filesystem error: {e}")
            return {"filesystem_raw": {"EFS": [], "FSx": []}}
    
    async def _fetch_nat_gateways(self, region: str) -> Dict[str, Any]:
        """Fetch NAT Gateways"""
        try:
            async with self.session.client('ec2', region_name=region) as ec2:
                nat_gws_paginator = ec2.get_paginator('describe_nat_gateways')
                nat_gateways = []
                async for page in nat_gws_paginator.paginate():
                    nat_gateways.extend(page['NatGateways'])
                
                print(f"   ✅ NAT Gateways: {len(nat_gateways)}")
                
                return {"nat_gateways_raw": {"NatGateways": nat_gateways}}
        except Exception as e:
            print(f"   ❌ NAT Gateway error: {e}")
            return {"nat_gateways_raw": {"NatGateways": []}}
    
    async def _fetch_vpc_endpoints(self, region: str) -> Dict[str, Any]:
        """Fetch VPC Endpoints"""
        try:
            async with self.session.client('ec2', region_name=region) as ec2:
                endpoints_paginator = ec2.get_paginator('describe_vpc_endpoints')
                endpoints = []
                async for page in endpoints_paginator.paginate():
                    endpoints.extend(page['VpcEndpoints'])
                
                print(f"   ✅ VPC Endpoints: {len(endpoints)}")
                
                return {"vpc_endpoints_raw": {"VpcEndpoints": endpoints}}
        except Exception as e:
            print(f"   ❌ VPC Endpoints error: {e}")
            return {"vpc_endpoints_raw": {"VpcEndpoints": []}}
    
    async def _fetch_elastic_ips(self, region: str) -> Dict[str, Any]:
        """Fetch Elastic IPs"""
        try:
            async with self.session.client('ec2', region_name=region) as ec2:
                eips_response = await ec2.describe_addresses()
                eips = eips_response['Addresses']
                
                print(f"   ✅ Elastic IPs: {len(eips)}")
                
                return {"eip_raw": {"Addresses": eips}}
        except Exception as e:
            print(f"   ❌ Elastic IP error: {e}")
            return {"eip_raw": {"Addresses": []}}
    
    async def _fetch_ebs_snapshots(self, region: str) -> Dict[str, Any]:
        """Fetch EBS Snapshots (owned by account)"""
        try:
            async with self.session.client('ec2', region_name=region) as ec2:
                snapshots_paginator = ec2.get_paginator('describe_snapshots')
                snapshots = []
                
                # Only fetch owned snapshots to avoid huge lists
                async for page in snapshots_paginator.paginate(OwnerIds=['self']):
                    snapshots.extend(page['Snapshots'])
                    if len(snapshots) > 500:  # Limit for performance
                        break
                
                print(f"   ✅ EBS Snapshots: {len(snapshots)} (owned)")
                
                return {"ebs_snapshots_raw": {"Snapshots": snapshots}}
        except Exception as e:
            print(f"   ❌ EBS Snapshots error: {e}")
            return {"ebs_snapshots_raw": {"Snapshots": []}}
    
    async def _fetch_amis(self, region: str) -> Dict[str, Any]:
        """Fetch AMIs owned by account"""
        try:
            async with self.session.client('ec2', region_name=region) as ec2:
                amis_paginator = ec2.get_paginator('describe_images')
                amis = []
                
                # Only fetch owned AMIs
                async for page in amis_paginator.paginate(Owners=['self']):
                    amis.extend(page['Images'])
                    if len(amis) > 200:  # Limit for performance
                        break
                
                print(f"   ✅ AMIs: {len(amis)} (owned)")
                
                return {"ami_raw": {"Images": amis}}
        except Exception as e:
            print(f"   ❌ AMI error: {e}")
            return {"ami_raw": {"Images": []}}
    
    async def _fetch_global_services(self) -> Dict[str, Any]:
        """Fetch servizi globali (non regionali)"""
        print("🌍 Fetching global services...")
        
        global_data = {}
        
        try:
            # CloudFront
            async with self.session.client('cloudfront', region_name='us-east-1') as cf:
                distributions_paginator = cf.get_paginator('list_distributions')
                distributions = []
                async for page in distributions_paginator.paginate():
                    if 'Items' in page.get('DistributionList', {}):
                        distributions.extend(page['DistributionList']['Items'])
                
                global_data["cloudfront_raw"] = {"Distributions": distributions}
                print(f"   ✅ CloudFront: {len(distributions)} distributions")
            
            # Route53
            async with self.session.client('route53', region_name='us-east-1') as route53:
                zones_paginator = route53.get_paginator('list_hosted_zones')
                zones = []
                async for page in zones_paginator.paginate():
                    zones.extend(page['HostedZones'])
                
                global_data["route53_raw"] = {"HostedZones": zones}
                print(f"   ✅ Route53: {len(zones)} hosted zones")
            
            # WAF (v2)
            async with self.session.client('wafv2', region_name='us-east-1') as wafv2:
                # Global WebACLs (CloudFront)
                global_webacls = await wafv2.list_web_acls(Scope='CLOUDFRONT')
                
                # Regional WebACLs for first region
                regional_webacls = await wafv2.list_web_acls(Scope='REGIONAL')
                
                global_data["waf_raw"] = {
                    "GlobalWebACLs": global_webacls.get('WebACLs', []),
                    "RegionalWebACLs": regional_webacls.get('WebACLs', [])
                }
                print(f"   ✅ WAF: {len(global_webacls.get('WebACLs', []))} global, {len(regional_webacls.get('WebACLs', []))} regional")
            
            # Certificate Manager
            async with self.session.client('acm', region_name='us-east-1') as acm:
                certs_paginator = acm.get_paginator('list_certificates')
                certificates = []
                async for page in certs_paginator.paginate():
                    certificates.extend(page['CertificateSummaryList'])
                
                global_data["acm_raw"] = {"Certificates": certificates}
                print(f"   ✅ ACM: {len(certificates)} certificates")
            
        except Exception as e:
            print(f"❌ Global services error: {e}")
        
        return global_data
    
    async def _save_extended_results(self, results: Dict[str, Any]):
        """Salva risultati estesi"""
        import os
        os.makedirs("data", exist_ok=True)
        
        def default_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        
        for data_type, data in results.items():
            if not data:
                continue
            
            filename = f"data/{data_type}.json"
            try:
                with open(filename, "w") as f:
                    json.dump(data, f, indent=2, default=default_serializer)
                
                file_size = os.path.getsize(filename)
                size_str = f"{file_size // (1024*1024)}MB" if file_size > 1024*1024 else f"{file_size // 1024}KB"
                print(f"   💾 {data_type}.json: {size_str}")
                
            except Exception as e:
                print(f"   ❌ Save error {data_type}: {e}")
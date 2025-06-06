# utils/cost_analysis_fetcher.py
import asyncio
import aioboto3
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from decimal import Decimal

class CostAnalysisFetcher:
    """Fetcher specializzato per analisi dei costi e risorse aggiuntive"""
    
    def __init__(self, config):
        self.config = config
        self.session = aioboto3.Session()
        self.sync_session = boto3.Session(profile_name=config.profile)
        
    async def fetch_cost_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch completi dati di costo da Cost Explorer"""
        print("💰 Fetching cost analysis data...")
        
        try:
            # Cost Explorer è solo sincrono
            ce_client = self.sync_session.client('ce', region_name='us-east-1')
            
            cost_data = {
                "daily_costs": await self._get_daily_costs(ce_client, start_date, end_date),
                "service_costs": await self._get_costs_by_service(ce_client, start_date, end_date),
                "instance_costs": await self._get_costs_by_instance(ce_client, start_date, end_date),
                "recommendations": await self._get_cost_recommendations(ce_client),
                "rightsizing": await self._get_rightsizing_recommendations(ce_client),
                "savings_plans": await self._get_savings_plans_recommendations(ce_client),
                "reserved_instances": await self._get_ri_recommendations(ce_client),
                "anomalies": await self._get_cost_anomalies(ce_client, start_date, end_date)
            }
            
            return cost_data
            
        except Exception as e:
            print(f"❌ Error fetching cost data: {e}")
            return {}
    
    async def _get_daily_costs(self, ce_client, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Ottieni costi giornalieri"""
        try:
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            daily_costs = []
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                total_cost = float(result['Total']['BlendedCost']['Amount'])
                
                services = []
                for group in result['Groups']:
                    service_name = group['Keys'][0]
                    service_cost = float(group['Metrics']['BlendedCost']['Amount'])
                    if service_cost > 0:
                        services.append({
                            'service': service_name,
                            'cost': service_cost
                        })
                
                daily_costs.append({
                    'date': date,
                    'total_cost': total_cost,
                    'services': sorted(services, key=lambda x: x['cost'], reverse=True)
                })
            
            return daily_costs
            
        except Exception as e:
            print(f"❌ Error getting daily costs: {e}")
            return []
    
    async def _get_costs_by_service(self, ce_client, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Ottieni costi per servizio"""
        try:
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            services = []
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service_name = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    usage = float(group['Metrics']['UsageQuantity']['Amount'])
                    
                    if cost > 0:
                        services.append({
                            'service': service_name,
                            'cost': cost,
                            'usage_quantity': usage,
                            'period': result['TimePeriod']
                        })
            
            # Sort by cost descending
            return sorted(services, key=lambda x: x['cost'], reverse=True)
            
        except Exception as e:
            print(f"❌ Error getting service costs: {e}")
            return []
    
    async def _get_costs_by_instance(self, ce_client, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Ottieni costi per istanza EC2"""
        try:
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'RESOURCE_ID'}
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Elastic Compute Cloud - Compute']
                    }
                }
            )
            
            instances = []
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    resource_id = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if cost > 0 and resource_id != 'NoResourceId':
                        instances.append({
                            'resource_id': resource_id,
                            'cost': cost,
                            'period': result['TimePeriod']
                        })
            
            return sorted(instances, key=lambda x: x['cost'], reverse=True)
            
        except Exception as e:
            print(f"❌ Error getting instance costs: {e}")
            return []
    
    async def _get_cost_recommendations(self, ce_client) -> Dict[str, Any]:
        """Ottieni raccomandazioni di ottimizzazione costi"""
        try:
            recommendations = {}
            
            # Rightsizing recommendations
            try:
                response = ce_client.get_rightsizing_recommendation(
                    Service='AmazonEC2',
                    Configuration={
                        'BenefitsConsidered': True,
                        'RecommendationTarget': 'SAME_INSTANCE_FAMILY'
                    }
                )
                recommendations['rightsizing'] = response
            except Exception as e:
                recommendations['rightsizing'] = {'error': str(e)}
            
            # Usage-based recommendations
            try:
                response = ce_client.get_usage_forecast(
                    TimePeriod={
                        'Start': datetime.now().strftime('%Y-%m-%d'),
                        'End': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                    },
                    Metric='BLENDED_COST',
                    Granularity='MONTHLY'
                )
                recommendations['forecast'] = response
            except Exception as e:
                recommendations['forecast'] = {'error': str(e)}
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Error getting cost recommendations: {e}")
            return {}
    
    async def _get_rightsizing_recommendations(self, ce_client) -> List[Dict]:
        """Ottieni raccomandazioni rightsizing dettagliate"""
        try:
            # Compute Optimizer per rightsizing recommendations
            co_client = self.sync_session.client('compute-optimizer', region_name='us-east-1')
            
            recommendations = []
            
            # EC2 Recommendations
            try:
                response = co_client.get_ec2_instance_recommendations()
                for rec in response.get('instanceRecommendations', []):
                    current_instance = rec.get('currentInstance', {})
                    recommendations.append({
                        'type': 'EC2_RIGHTSIZING',
                        'current_instance_arn': current_instance.get('instanceArn'),
                        'current_instance_type': current_instance.get('instanceType'),
                        'current_monthly_cost': self._calculate_monthly_cost(current_instance),
                        'recommendation_options': rec.get('recommendationOptions', []),
                        'finding': rec.get('finding'),
                        'utilization_metrics': rec.get('utilizationMetrics', {}),
                        'last_refresh_timestamp': rec.get('lastRefreshTimestamp')
                    })
            except Exception as e:
                print(f"⚠️ EC2 recommendations error: {e}")
            
            # EBS Volume Recommendations  
            try:
                response = co_client.get_ebs_volume_recommendations()
                for rec in response.get('volumeRecommendations', []):
                    current_config = rec.get('currentConfiguration', {})
                    recommendations.append({
                        'type': 'EBS_RIGHTSIZING',
                        'volume_arn': rec.get('volumeArn'),
                        'current_configuration': current_config,
                        'recommendation_options': rec.get('recommendationOptions', []),
                        'finding': rec.get('finding'),
                        'utilization_metrics': rec.get('utilizationMetrics', {}),
                        'last_refresh_timestamp': rec.get('lastRefreshTimestamp')
                    })
            except Exception as e:
                print(f"⚠️ EBS recommendations error: {e}")
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Error getting rightsizing recommendations: {e}")
            return []
    
    async def _get_savings_plans_recommendations(self, ce_client) -> Dict[str, Any]:
        """Ottieni raccomandazioni Savings Plans"""
        try:
            response = ce_client.get_savings_plans_purchase_recommendation(
                SavingsPlansType='COMPUTE_SP',
                TermInYears='ONE_YEAR',
                PaymentOption='NO_UPFRONT',
                LookbackPeriodInDays='SEVEN_DAYS'
            )
            
            return {
                'metadata': response.get('Metadata', {}),
                'recommendations': response.get('SavingsPlansRecommendations', []),
                'next_page_token': response.get('NextPageToken')
            }
            
        except Exception as e:
            print(f"❌ Error getting Savings Plans recommendations: {e}")
            return {}
    
    async def _get_ri_recommendations(self, ce_client) -> Dict[str, Any]:
        """Ottieni raccomandazioni Reserved Instances"""
        try:
            response = ce_client.get_reservation_purchase_recommendation(
                Service='Amazon Elastic Compute Cloud - Compute',
                TermInYears='ONE_YEAR',
                PaymentOption='NO_UPFRONT'
            )
            
            return {
                'metadata': response.get('Metadata', {}),
                'recommendations': response.get('Recommendations', []),
                'next_page_token': response.get('NextPageToken')
            }
            
        except Exception as e:
            print(f"❌ Error getting RI recommendations: {e}")
            return {}
    
    async def _get_cost_anomalies(self, ce_client, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Ottieni anomalie nei costi"""
        try:
            response = ce_client.get_anomalies(
                DateInterval={
                    'StartDate': start_date.strftime('%Y-%m-%d'),
                    'EndDate': end_date.strftime('%Y-%m-%d')
                },
                MaxResults=100
            )
            
            anomalies = []
            for anomaly in response.get('Anomalies', []):
                anomalies.append({
                    'anomaly_id': anomaly.get('AnomalyId'),
                    'anomaly_start_date': anomaly.get('AnomalyStartDate'),
                    'anomaly_end_date': anomaly.get('AnomalyEndDate'),
                    'dimension_key': anomaly.get('DimensionKey'),
                    'impact': anomaly.get('Impact', {}),
                    'monitor_arn': anomaly.get('MonitorArn'),
                    'feedback': anomaly.get('Feedback'),
                    'root_causes': anomaly.get('RootCauses', [])
                })
            
            return anomalies
            
        except Exception as e:
            print(f"❌ Error getting cost anomalies: {e}")
            return []
    
    def _calculate_monthly_cost(self, instance_config: Dict) -> float:
        """Calcola costo mensile approssimativo per istanza"""
        # Mappatura prezzi approssimativi per ora (us-east-1)
        pricing_map = {
            't2.micro': 0.0116,
            't2.small': 0.023,
            't2.medium': 0.046,
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
            'c5.large': 0.085,
            'c5.xlarge': 0.17
        }
        
        instance_type = instance_config.get('instanceType', '')
        hourly_rate = pricing_map.get(instance_type, 0.05)  # Default fallback
        
        # 730 ore al mese (24 * 30.4)
        return hourly_rate * 730
    
    async def fetch_additional_resources(self) -> Dict[str, Any]:
        """Fetch risorse aggiuntive per analisi completa"""
        print("🔍 Fetching additional AWS resources...")
        
        additional_resources = {}
        
        # CloudWatch costs and usage
        additional_resources['cloudwatch'] = await self._fetch_cloudwatch_resources()
        
        # EBS volumes detailed
        additional_resources['ebs'] = await self._fetch_ebs_resources()
        
        # Load Balancers
        additional_resources['load_balancers'] = await self._fetch_load_balancers()
        
        # RDS instances
        additional_resources['rds'] = await self._fetch_rds_resources()
        
        # Lambda functions
        additional_resources['lambda'] = await self._fetch_lambda_resources()
        
        # CloudFormation stacks
        additional_resources['cloudformation'] = await self._fetch_cloudformation_resources()
        
        # Route53 resources
        additional_resources['route53'] = await self._fetch_route53_resources()
        
        # CloudFront distributions
        additional_resources['cloudfront'] = await self._fetch_cloudfront_resources()
        
        return additional_resources
    
    async def _fetch_cloudwatch_resources(self) -> Dict[str, Any]:
        """Fetch risorse CloudWatch per analisi costi"""
        try:
            async with self.session.client('cloudwatch', region_name='us-east-1') as cw:
                # List metrics
                paginator = cw.get_paginator('list_metrics')
                metrics = []
                
                async for page in paginator.paginate():
                    metrics.extend(page['Metrics'])
                
                # List alarms
                alarms_response = await cw.describe_alarms()
                alarms = alarms_response['MetricAlarms']
                
                # List dashboards
                dashboards_response = await cw.list_dashboards()
                dashboards = dashboards_response['DashboardEntries']
                
                return {
                    'metrics_count': len(metrics),
                    'custom_metrics': [m for m in metrics if not m['Namespace'].startswith('AWS/')],
                    'alarms': alarms,
                    'dashboards': dashboards,
                    'estimated_monthly_cost': self._estimate_cloudwatch_cost(metrics, alarms, dashboards)
                }
        except Exception as e:
            print(f"❌ Error fetching CloudWatch resources: {e}")
            return {}
    
    async def _fetch_ebs_resources(self) -> Dict[str, Any]:
        """Fetch dettagli volumi EBS"""
        try:
            async with self.session.client('ec2', region_name='us-east-1') as ec2:
                paginator = ec2.get_paginator('describe_volumes')
                volumes = []
                
                async for page in paginator.paginate():
                    volumes.extend(page['Volumes'])
                
                # Calcola costi stimati
                total_gb = sum(vol['Size'] for vol in volumes)
                estimated_monthly_cost = total_gb * 0.10  # ~$0.10/GB/month for gp3
                
                return {
                    'volumes': volumes,
                    'total_volumes': len(volumes),
                    'total_size_gb': total_gb,
                    'estimated_monthly_cost': estimated_monthly_cost,
                    'unattached_volumes': [v for v in volumes if v['State'] == 'available']
                }
        except Exception as e:
            print(f"❌ Error fetching EBS resources: {e}")
            return {}
    
    async def _fetch_load_balancers(self) -> Dict[str, Any]:
        """Fetch Load Balancers (ALB, NLB, CLB)"""
        try:
            lb_data = {'application': [], 'network': [], 'classic': []}
            
            # Application and Network Load Balancers
            async with self.session.client('elbv2', region_name='us-east-1') as elbv2:
                response = await elbv2.describe_load_balancers()
                for lb in response['LoadBalancers']:
                    if lb['Type'] == 'application':
                        lb_data['application'].append(lb)
                    elif lb['Type'] == 'network':
                        lb_data['network'].append(lb)
            
            # Classic Load Balancers
            async with self.session.client('elb', region_name='us-east-1') as elb:
                response = await elb.describe_load_balancers()
                lb_data['classic'] = response['LoadBalancerDescriptions']
            
            # Calcola costi stimati
            total_lbs = len(lb_data['application']) + len(lb_data['network']) + len(lb_data['classic'])
            estimated_monthly_cost = total_lbs * 18.25  # ~$18.25/month per ALB
            
            return {
                **lb_data,
                'total_load_balancers': total_lbs,
                'estimated_monthly_cost': estimated_monthly_cost
            }
        except Exception as e:
            print(f"❌ Error fetching Load Balancers: {e}")
            return {}
    
    async def _fetch_rds_resources(self) -> Dict[str, Any]:
        """Fetch istanze RDS"""
        try:
            async with self.session.client('rds', region_name='us-east-1') as rds:
                # DB Instances
                instances_response = await rds.describe_db_instances()
                instances = instances_response['DBInstances']
                
                # DB Clusters (Aurora)
                clusters_response = await rds.describe_db_clusters()
                clusters = clusters_response['DBClusters']
                
                return {
                    'db_instances': instances,
                    'db_clusters': clusters,
                    'total_instances': len(instances),
                    'total_clusters': len(clusters)
                }
        except Exception as e:
            print(f"❌ Error fetching RDS resources: {e}")
            return {}
    
    async def _fetch_lambda_resources(self) -> Dict[str, Any]:
        """Fetch funzioni Lambda"""
        try:
            async with self.session.client('lambda', region_name='us-east-1') as lambda_client:
                paginator = lambda_client.get_paginator('list_functions')
                functions = []
                
                async for page in paginator.paginate():
                    functions.extend(page['Functions'])
                
                return {
                    'functions': functions,
                    'total_functions': len(functions)
                }
        except Exception as e:
            print(f"❌ Error fetching Lambda resources: {e}")
            return {}
    
    async def _fetch_cloudformation_resources(self) -> Dict[str, Any]:
        """Fetch CloudFormation stacks"""
        try:
            async with self.session.client('cloudformation', region_name='us-east-1') as cf:
                paginator = cf.get_paginator('describe_stacks')
                stacks = []
                
                async for page in paginator.paginate():
                    stacks.extend(page['Stacks'])
                
                return {
                    'stacks': stacks,
                    'total_stacks': len(stacks),
                    'active_stacks': [s for s in stacks if s['StackStatus'] in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']]
                }
        except Exception as e:
            print(f"❌ Error fetching CloudFormation resources: {e}")
            return {}
    
    async def _fetch_route53_resources(self) -> Dict[str, Any]:
        """Fetch Route53 hosted zones"""
        try:
            async with self.session.client('route53', region_name='us-east-1') as route53:
                zones_response = await route53.list_hosted_zones()
                zones = zones_response['HostedZones']
                
                return {
                    'hosted_zones': zones,
                    'total_zones': len(zones),
                    'estimated_monthly_cost': len(zones) * 0.50  # $0.50 per hosted zone
                }
        except Exception as e:
            print(f"❌ Error fetching Route53 resources: {e}")
            return {}
    
    async def _fetch_cloudfront_resources(self) -> Dict[str, Any]:
        """Fetch CloudFront distributions"""
        try:
            async with self.session.client('cloudfront', region_name='us-east-1') as cf:
                response = await cf.list_distributions()
                distributions = response.get('DistributionList', {}).get('Items', [])
                
                return {
                    'distributions': distributions,
                    'total_distributions': len(distributions)
                }
        except Exception as e:
            print(f"❌ Error fetching CloudFront resources: {e}")
            return {}
    
    def _estimate_cloudwatch_cost(self, metrics: List, alarms: List, dashboards: List) -> float:
        """Stima costi CloudWatch mensili"""
        custom_metrics = len([m for m in metrics if not m['Namespace'].startswith('AWS/')])
        
        # Pricing approssimativo
        metrics_cost = max(0, custom_metrics - 10000) * 0.30  # First 10k free
        alarms_cost = max(0, len(alarms) - 10) * 0.10  # First 10 free
        dashboards_cost = max(0, len(dashboards) - 3) * 3.00  # First 3 free
        
        return metrics_cost + alarms_cost + dashboards_cost
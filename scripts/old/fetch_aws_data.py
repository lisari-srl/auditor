import boto3
import json
import os
from datetime import datetime

REGION = "us-east-1"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def save_to_file(name, data):
    path = os.path.join(OUTPUT_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=default_serializer)
    print(f"✅ Salvato {name}.json")

def fetch_ec2_data():
    ec2 = boto3.client("ec2", region_name=REGION)
    # EC2 Instances (con tutti i dettagli)
    paginator = ec2.get_paginator('describe_instances')
    instances = {"Reservations": []}
    for page in paginator.paginate():
        instances["Reservations"].extend(page["Reservations"])
    save_to_file("ec2_audit", instances)
    # ENI
    enis = ec2.describe_network_interfaces()
    save_to_file("network_interfaces", enis)
    # Security Groups
    sgs = ec2.describe_security_groups()
    save_to_file("security_groups", sgs)
    # VPC
    vpcs = ec2.describe_vpcs()
    save_to_file("vpcs", vpcs)
    # Subnets
    subnets = ec2.describe_subnets()
    save_to_file("subnets", subnets)
    # Route Tables
    route_tables = ec2.describe_route_tables()
    save_to_file("route_tables", route_tables)
    # Internet Gateways
    igws = ec2.describe_internet_gateways()
    save_to_file("internet_gateways", igws)

def fetch_s3_data():
    s3 = boto3.client("s3", region_name=REGION)
    buckets = s3.list_buckets().get("Buckets", [])
    s3_data = []
    for b in buckets:
        bucket_name = b["Name"]
        bucket_info = {"Name": bucket_name, "CreationDate": b.get("CreationDate", ""), "Policy": None, "ACL": None, "PublicAccess": False}
        try:
            policy = s3.get_bucket_policy(Bucket=bucket_name)
            bucket_info["Policy"] = policy.get("Policy", "")
        except Exception:
            bucket_info["Policy"] = None
        try:
            acl = s3.get_bucket_acl(Bucket=bucket_name)
            bucket_info["ACL"] = acl
            for grant in acl.get("Grants", []):
                grantee = grant.get("Grantee", {})
                if grantee.get("URI", "").endswith("AllUsers"):
                    bucket_info["PublicAccess"] = True
        except Exception:
            bucket_info["ACL"] = None
        s3_data.append(bucket_info)
    save_to_file("s3_buckets", s3_data)

def fetch_iam_data():
    iam = boto3.client("iam", region_name=REGION)
    result = {"Users": [], "Roles": [], "Policies": []}
    paginator = iam.get_paginator('list_users')
    for page in paginator.paginate():
        for user in page["Users"]:
            # Last used info
            try:
                last_used = iam.get_user(UserName=user["UserName"]).get("User", {}).get("PasswordLastUsed")
                user["PasswordLastUsed"] = last_used
            except Exception:
                user["PasswordLastUsed"] = None
            result["Users"].append(user)
    paginator = iam.get_paginator('list_roles')
    for page in paginator.paginate():
        result["Roles"].extend(page["Roles"])
    paginator = iam.get_paginator('list_policies')
    for page in paginator.paginate(Scope='Local'):
        result["Policies"].extend(page["Policies"])
    save_to_file("iam_audit", result)

def fetch_all():
    print("🔍 Fetching EC2-related data...")
    fetch_ec2_data()
    print("🔍 Fetching S3-related data...")
    fetch_s3_data()
    print("🔍 Fetching IAM-related data...")
    fetch_iam_data()
    print("✅ Audit AWS completato.")

if __name__ == "__main__":
    fetch_all()
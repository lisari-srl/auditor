import boto3
import json
import os
from datetime import datetime

def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def fetch_ec2():
    ec2 = boto3.client('ec2', region_name='us-east-1')  # Forza la regione N. Virginia
    paginator = ec2.get_paginator('describe_instances')
    results = {"Reservations": []}
    for page in paginator.paginate():
        results["Reservations"].extend(page["Reservations"])
    os.makedirs("data", exist_ok=True)
    with open("data/ec2_raw.json", "w") as f:
        json.dump(results, f, indent=2, default=default_serializer)
    print("✅ Salvato data/ec2_raw.json")

if __name__ == "__main__":
    fetch_ec2()
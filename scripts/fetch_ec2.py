import boto3
import json
import os

def fetch_ec2():
    ec2 = boto3.client('ec2')
    paginator = ec2.get_paginator('describe_instances')
    results = {"Reservations": []}
    for page in paginator.paginate():
        results["Reservations"].extend(page["Reservations"])
    os.makedirs("data", exist_ok=True)
    with open("data/ec2_raw.json", "w") as f:
        json.dump(results, f, indent=2)
    print("✅ Salvato data/ec2_raw.json")

if __name__ == "__main__":
    fetch_ec2()
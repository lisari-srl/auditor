import boto3
import json
import os

def fetch_subnet():
    ec2 = boto3.client('ec2')
    subnets = ec2.describe_subnets()
    os.makedirs("data", exist_ok=True)
    with open("data/subnet_raw.json", "w") as f:
        json.dump(subnets, f, indent=2)
    print("✅ Salvato data/subnet_raw.json")

if __name__ == "__main__":
    fetch_subnet()
import boto3
import json
import os

def fetch_vpc():
    ec2 = boto3.client('ec2')
    vpcs = ec2.describe_vpcs()
    os.makedirs("data", exist_ok=True)
    with open("data/vpc_raw.json", "w") as f:
        json.dump(vpcs, f, indent=2)
    print("✅ Salvato data/vpc_raw.json")

if __name__ == "__main__":
    fetch_vpc()
import boto3
import json
import os

def fetch_sg():
    ec2 = boto3.client('ec2')
    sgs = ec2.describe_security_groups()
    os.makedirs("data", exist_ok=True)
    with open("data/sg_raw.json", "w") as f:
        json.dump(sgs, f, indent=2)
    print("✅ Salvato data/sg_raw.json")

if __name__ == "__main__":
    fetch_sg()
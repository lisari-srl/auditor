import boto3
import json
import os

def fetch_igw():
    ec2 = boto3.client('ec2')
    igws = ec2.describe_internet_gateways()
    os.makedirs("data", exist_ok=True)
    with open("data/igw_raw.json", "w") as f:
        json.dump(igws, f, indent=2)
    print("✅ Salvato data/igw_raw.json")

if __name__ == "__main__":
    fetch_igw()
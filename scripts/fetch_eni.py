import boto3
import json
import os

def fetch_eni():
    ec2 = boto3.client('ec2')
    enis = ec2.describe_network_interfaces()
    os.makedirs("data", exist_ok=True)
    with open("data/eni_raw.json", "w") as f:
        json.dump(enis, f, indent=2)
    print("✅ Salvato data/eni_raw.json")

if __name__ == "__main__":
    fetch_eni()
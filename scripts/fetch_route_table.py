import boto3
import json
import os

def fetch_route_table():
    ec2 = boto3.client('ec2')
    route_tables = ec2.describe_route_tables()
    os.makedirs("data", exist_ok=True)
    with open("data/route_table_raw.json", "w") as f:
        json.dump(route_tables, f, indent=2)
    print("✅ Salvato data/route_table_raw.json")

if __name__ == "__main__":
    fetch_route_table()
# audit/ec2_audit.py

import boto3
import json
import os

def run_ec2_audit():
    ec2 = boto3.client('ec2')
    results = {
        "Reservations": []
    }

    paginator = ec2.get_paginator('describe_instances')
    for page in paginator.paginate():
        results["Reservations"].extend(page["Reservations"])

    sg_map = ec2.describe_security_groups()
    eni_map = ec2.describe_network_interfaces()

    os.makedirs("data", exist_ok=True)
    with open("data/ec2_audit.json", "w") as f:
        json.dump(results, f, indent=2)

    with open("data/security_groups.json", "w") as f:
        json.dump(sg_map, f, indent=2)

    with open("data/network_interfaces.json", "w") as f:
        json.dump(eni_map, f, indent=2)

    with open('reports/ec2_audit_report.md', 'w') as report:
        report.write("✅ EC2 + SG + ENI audit completato e salvato in /data\n")
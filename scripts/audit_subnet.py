import json
import os

def audit_subnet():
    with open("data/subnet_raw.json") as f:
        subnet_data = json.load(f)

    subnets = subnet_data["Subnets"]
    public_subnets = [s for s in subnets if s.get("MapPublicIpOnLaunch")]
    no_ip_subnets = [s for s in subnets if s.get("AvailableIpAddressCount", 1) == 0]

    os.makedirs("data", exist_ok=True)
    with open("data/subnet_audit.json", "w") as f:
        json.dump({"public_subnets": public_subnets, "no_ip_subnets": no_ip_subnets}, f, indent=2)

    os.makedirs("reports", exist_ok=True)
    with open("reports/audit_subnet_report.md", "w") as report:
        report.write("# Subnet Audit Report\n\n")
        report.write("## Public Subnets\n")
        for s in public_subnets:
            report.write(f"- {s['SubnetId']} | VPC: {s['VpcId']} | CIDR: {s['CidrBlock']} | AZ: {s['AvailabilityZone']}\n")
        report.write("\n## Subnets with 0 available IPs\n")
        for s in no_ip_subnets:
            report.write(f"- {s['SubnetId']} | VPC: {s['VpcId']} | CIDR: {s['CidrBlock']} | AZ: {s['AvailabilityZone']}\n")
    print("✅ Subnet audit completato e salvato in /data e /reports")

if __name__ == "__main__":
    audit_subnet()
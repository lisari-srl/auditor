import json
import os

def audit_vpc():
    with open("data/vpc_raw.json") as f:
        vpc_data = json.load(f)

    vpcs = vpc_data["Vpcs"]
    default_vpcs = [v for v in vpcs if v.get("IsDefault")]
    not_available_vpcs = [v for v in vpcs if v.get("State") != "available"]
    public_access_vpcs = [
        v for v in vpcs
        if v.get("BlockPublicAccessStates", {}).get("InternetGatewayBlockMode") == "off"
    ]

    os.makedirs("data", exist_ok=True)
    with open("data/vpc_audit.json", "w") as f:
        json.dump({
            "default_vpcs": default_vpcs,
            "not_available_vpcs": not_available_vpcs,
            "public_access_vpcs": public_access_vpcs
        }, f, indent=2)

    os.makedirs("reports", exist_ok=True)
    with open("reports/audit_vpc_report.md", "w") as report:
        report.write("# VPC Audit Report\n\n")
        report.write("## Default VPCs\n")
        for v in default_vpcs:
            report.write(f"- {v['VpcId']} | CIDR: {v['CidrBlock']} | State: {v['State']}\n")
        report.write("\n## VPCs not available\n")
        for v in not_available_vpcs:
            report.write(f"- {v['VpcId']} | CIDR: {v['CidrBlock']} | State: {v['State']}\n")
        report.write("\n## VPCs with public access enabled (InternetGatewayBlockMode: off)\n")
        for v in public_access_vpcs:
            report.write(f"- {v['VpcId']} | CIDR: {v['CidrBlock']} | State: {v['State']}\n")
    print("✅ VPC audit completato e salvato in /data e /reports")

if __name__ == "__main__":
    audit_vpc()
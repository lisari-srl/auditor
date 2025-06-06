import json
import os

def audit_igw():
    with open("data/igw_raw.json") as f:
        igw_data = json.load(f)

    igws = igw_data.get("InternetGateways", [])
    os.makedirs("data", exist_ok=True)
    with open("data/igw_audit.json", "w") as f:
        json.dump({"internet_gateways": igws}, f, indent=2)

    os.makedirs("reports", exist_ok=True)
    with open("reports/audit_igw_report.md", "w") as report:
        report.write("# Internet Gateway Audit Report\n\n")
        for igw in igw_data["InternetGateways"]:
            for attachment in igw.get("Attachments", []):
                vpc_id = attachment.get("VpcId")
                state = attachment.get("State")
                report.write(f"- {igw.get('InternetGatewayId')} | VPC: {vpc_id} | State: {state}\n")
    print("✅ IGW audit completato e salvato in /data e /reports")

if __name__ == "__main__":
    audit_igw()
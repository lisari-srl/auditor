import json
import os

def audit_eni():
    with open("data/eni_raw.json") as f:
        eni_data = json.load(f)

    attached = []
    orphans = []
    for eni in eni_data["NetworkInterfaces"]:
        attachment = eni.get("Attachment")
        info = {
            "NetworkInterfaceId": eni.get("NetworkInterfaceId"),
            "Description": eni.get("Description"),
            "SubnetId": eni.get("SubnetId"),
            "VpcId": eni.get("VpcId"),
            "PrivateIp": eni.get("PrivateIpAddress"),
            "Status": eni.get("Status"),
        }
        if attachment and attachment.get("InstanceId"):
            info["InstanceId"] = attachment.get("InstanceId")
            attached.append(info)
        else:
            orphans.append(info)

    os.makedirs("data", exist_ok=True)
    with open("data/eni_audit.json", "w") as f:
        json.dump({"attached": attached, "orphans": orphans}, f, indent=2)

    os.makedirs("reports", exist_ok=True)
    with open("reports/audit_eni_report.md", "w") as report:
        report.write("# ENI Audit Report\n\n")
        report.write("## Attached ENIs\n")
        for eni in attached:
            report.write(f"- {eni['NetworkInterfaceId']} (Instance: {eni.get('InstanceId','-')}), Subnet: {eni['SubnetId']}, VPC: {eni['VpcId']}, Private IP: {eni['PrivateIp']}\n")
        report.write("\n## Orphan ENIs\n")
        for eni in orphans:
            report.write(f"- {eni['NetworkInterfaceId']}, Subnet: {eni['SubnetId']}, VPC: {eni['VpcId']}, Private IP: {eni['PrivateIp']}\n")
    print("✅ ENI audit completato e salvato in /data e /reports")

if __name__ == "__main__":
    audit_eni()
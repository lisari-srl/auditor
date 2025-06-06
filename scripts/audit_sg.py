import json
import os

def audit_sg():
    with open("data/sg_raw.json") as f:
        sg_data = json.load(f)

    open_ingress = []
    open_egress = []

    for sg in sg_data["SecurityGroups"]:
        # Analisi regole INGRESS
        for rule in sg.get("IpPermissions", []):
            for ip_range in rule.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0":
                    open_ingress.append({
                        "GroupId": sg.get("GroupId"),
                        "GroupName": sg.get("GroupName"),
                        "Port": rule.get("FromPort"),
                        "Protocol": rule.get("IpProtocol"),
                        "Description": sg.get("Description"),
                        "Direction": "ingress"
                    })
        # Analisi regole EGRESS
        for rule in sg.get("IpPermissionsEgress", []):
            for ip_range in rule.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0":
                    open_egress.append({
                        "GroupId": sg.get("GroupId"),
                        "GroupName": sg.get("GroupName"),
                        "Port": rule.get("FromPort"),
                        "Protocol": rule.get("IpProtocol"),
                        "Description": sg.get("Description"),
                        "Direction": "egress"
                    })

    os.makedirs("data", exist_ok=True)
    with open("data/sg_audit.json", "w") as f:
        json.dump({"open_ingress": open_ingress, "open_egress": open_egress}, f, indent=2)

    os.makedirs("reports", exist_ok=True)
    with open("reports/audit_sg_report.md", "w") as report:
        report.write("# Security Group Audit Report\n\n")
        report.write("## Security Groups with open INGRESS rules (0.0.0.0/0)\n")
        for sg in open_ingress:
            report.write(f"- {sg['GroupName']} ({sg['GroupId']}), Port: {sg['Port']}, Protocol: {sg['Protocol']}, Desc: {sg['Description']}\n")
        report.write("\n## Security Groups with open EGRESS rules (0.0.0.0/0)\n")
        for sg in open_egress:
            report.write(f"- {sg['GroupName']} ({sg['GroupId']}), Port: {sg['Port']}, Protocol: {sg['Protocol']}, Desc: {sg['Description']}\n")
    print("✅ SG audit completato e salvato in /data e /reports")

if __name__ == "__main__":
    audit_sg()
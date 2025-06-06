import json
import os

def audit_iam():
    with open("data/iam_raw.json") as f:
        iam_data = json.load(f)

    users = iam_data.get("Users", [])
    os.makedirs("data", exist_ok=True)
    with open("data/iam_audit.json", "w") as f:
        json.dump({"users": users}, f, indent=2)

    os.makedirs("reports", exist_ok=True)
    with open("reports/audit_iam_report.md", "w") as report:
        report.write("# IAM Audit Report\n\n")
        report.write("## Users\n")
        for user in users:
            report.write(f"- {user['UserName']} (Created: {user['CreateDate']})\n")
        
        report.write("\n## Roles\n")
        for role in iam_data.get("Roles", []):
            report.write(f"- {role['RoleName']} (Created: {role['CreateDate']})\n")
        
        report.write("\n## Policies\n")
        for policy in iam_data.get("Policies", []):
            report.write(f"- {policy['PolicyName']} (Attached: {policy['AttachmentCount']} entities)\n")
    
    print("✅ IAM audit completato e salvato in /data e /reports")

if __name__ == "__main__":
    audit_iam()
# audit/iam_audit.py

import boto3
import json
import os

def run_iam_audit():
    iam = boto3.client('iam')
    result = {"Users": [], "Roles": [], "Policies": []}

    paginator = iam.get_paginator('list_users')
    for page in paginator.paginate():
        for user in page["Users"]:
            try:
                last_used = iam.get_user(UserName=user["UserName"]).get("User", {}).get("PasswordLastUsed")
                user["PasswordLastUsed"] = last_used
            except Exception:
                user["PasswordLastUsed"] = None
            result["Users"].append(user)

    paginator = iam.get_paginator('list_roles')
    for page in paginator.paginate():
        result["Roles"].extend(page["Roles"])

    paginator = iam.get_paginator('list_policies')
    for page in paginator.paginate(Scope='Local'):
        result["Policies"].extend(page["Policies"])

    os.makedirs("data", exist_ok=True)
    with open("data/iam_audit.json", "w") as f:
        json.dump(result, f, indent=2)

    with open('reports/iam_audit_report.md', 'w') as report:
        report.write("✅ IAM audit completato e salvato in /data\n")
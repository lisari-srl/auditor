# audit/s3_audit.py

import boto3
import json
import os

def run_s3_audit():
    s3 = boto3.client('s3')
    buckets = s3.list_buckets()["Buckets"]
    results = []

    for bucket in buckets:
        name = bucket["Name"]
        creation = bucket.get("CreationDate", "")
        bucket_info = {"Name": name, "CreationDate": str(creation), "PublicAccess": False, "PolicyStatus": {}, "ACL": {}}

        try:
            policy = s3.get_bucket_policy_status(Bucket=name)
            bucket_info["PolicyStatus"] = policy.get("PolicyStatus", {})
        except Exception:
            pass

        try:
            acl = s3.get_bucket_acl(Bucket=name)
            bucket_info["ACL"] = acl
            for grant in acl.get("Grants", []):
                grantee = grant.get("Grantee", {})
                if grantee.get("URI", "").endswith("AllUsers"):
                    bucket_info["PublicAccess"] = True
        except Exception:
            pass

        results.append(bucket_info)

    os.makedirs("data", exist_ok=True)
    with open("data/s3_audit.json", "w") as f:
        json.dump(results, f, indent=2)

    with open('reports/s3_audit_report.md', 'w') as report:
        report.write("✅ S3 audit completato e salvato in /data\n")
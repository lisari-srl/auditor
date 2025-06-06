import boto3
import json
import os

def fetch_s3():
    s3 = boto3.client('s3')
    buckets = s3.list_buckets().get("Buckets", [])
    s3_data = []
    for b in buckets:
        bucket_name = b["Name"]
        bucket_info = {"Name": bucket_name, "CreationDate": str(b.get("CreationDate", "")), "Policy": None, "ACL": None, "PublicAccess": False}
        try:
            policy = s3.get_bucket_policy(Bucket=bucket_name)
            bucket_info["Policy"] = policy.get("Policy", "")
        except Exception:
            bucket_info["Policy"] = None
        try:
            acl = s3.get_bucket_acl(Bucket=bucket_name)
            bucket_info["ACL"] = acl
            for grant in acl.get("Grants", []):
                grantee = grant.get("Grantee", {})
                if grantee.get("URI", "").endswith("AllUsers"):
                    bucket_info["PublicAccess"] = True
        except Exception:
            bucket_info["ACL"] = None
        s3_data.append(bucket_info)
    os.makedirs("data", exist_ok=True)
    with open("data/s3_raw.json", "w") as f:
        json.dump(s3_data, f, indent=2)
    print("✅ Salvato data/s3_raw.json")

if __name__ == "__main__":
    fetch_s3()
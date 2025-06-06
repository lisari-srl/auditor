import json
import os

def audit_s3():
    with open("data/s3_raw.json") as f:
        s3_data = json.load(f)

    for bucket in s3_data:
        # logica di audit
        public_buckets = [b for b in s3_data if b.get("PublicAccessBlock")]
        os.makedirs("data", exist_ok=True)
        with open("data/s3_audit.json", "w") as f:
            json.dump({"public_buckets": public_buckets}, f, indent=2)

        os.makedirs("reports", exist_ok=True)
        with open("reports/audit_s3_report.md", "w") as report:
            report.write("# S3 Audit Report\n\n")
            report.write("## Public Buckets\n")
            for b in public_buckets:
                report.write(f"- {b['Name']} (Created: {b['CreationDate']})\n")
    print("✅ S3 audit completato e salvato in /data e /reports")

if __name__ == "__main__":
    audit_s3()
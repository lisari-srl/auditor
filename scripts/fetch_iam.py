import boto3
import json
import os
from datetime import datetime

def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def fetch_iam():
    iam = boto3.client('iam')
    result = {"Users": [], "Roles": [], "Policies": []}
    paginator = iam.get_paginator('list_users')
    for page in paginator.paginate():
        result["Users"].extend(page["Users"])
    paginator = iam.get_paginator('list_roles')
    for page in paginator.paginate():
        result["Roles"].extend(page["Roles"])
    paginator = iam.get_paginator('list_policies')
    for page in paginator.paginate(Scope='Local'):
        result["Policies"].extend(page["Policies"])
    os.makedirs("data", exist_ok=True)
    with open("data/iam_raw.json", "w") as f:
        json.dump(result, f, indent=2, default=default_serializer)
    print("✅ Salvato data/iam_raw.json")

if __name__ == "__main__":
    fetch_iam()
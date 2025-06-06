import json
import os

def run_ec2_audit():
    with open("data/ec2_raw.json") as f:
        ec2_data = json.load(f)

    active = []
    stopped = []
    for reservation in ec2_data["Reservations"]:
        for instance in reservation["Instances"]:
            state = instance.get("State", {}).get("Name", "")
            name = next((t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"), instance.get("InstanceId"))
            info = {
                "InstanceId": instance.get("InstanceId"),
                "Name": name,
                "Type": instance.get("InstanceType"),
                "State": state,
                "SubnetId": instance.get("SubnetId"),
                "VpcId": instance.get("VpcId"),
                "SecurityGroups": [sg["GroupId"] for sg in instance.get("SecurityGroups", [])],
                "LaunchTime": instance.get("LaunchTime"),
                "PublicIp": instance.get("PublicIpAddress"),
                "PrivateIp": instance.get("PrivateIpAddress"),
            }
            if state == "running":
                active.append(info)
            else:
                stopped.append(info)

    os.makedirs("data", exist_ok=True)
    with open("data/ec2_audit.json", "w") as f:
        json.dump({"active": active, "stopped": stopped}, f, indent=2)

    os.makedirs("reports", exist_ok=True)
    with open("reports/ec2_audit_report.md", "w") as report:
        report.write("# EC2 Audit Report\n\n")
        report.write("## Running Instances\n")
        for inst in active:
            report.write(f"- {inst['Name']} ({inst['InstanceId']}), Type: {inst['Type']}, Subnet: {inst['SubnetId']}, VPC: {inst['VpcId']}, Public IP: {inst['PublicIp']}, Private IP: {inst['PrivateIp']}\n")
        report.write("\n## Stopped Instances\n")
        for inst in stopped:
            report.write(f"- {inst['Name']} ({inst['InstanceId']}), Type: {inst['Type']}, Subnet: {inst['SubnetId']}, VPC: {inst['VpcId']}\n")
    print("✅ EC2 audit completato e salvato in /data e /reports")

if __name__ == "__main__":
    run_ec2_audit()
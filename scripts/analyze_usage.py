import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORT_FILE = os.path.join(BASE_DIR, "reports", "resource_usage_report.md")

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

# Caricamento dati
ec2_data = load_json("ec2_audit.json")
eni_data = load_json("network_interfaces.json")
sg_data = load_json("security_groups.json")

# Analisi EC2
active_ec2 = []
stopped_ec2 = []
for reservation in ec2_data.get("Reservations", []):
    for instance in reservation.get("Instances", []):
        state = instance.get("State", {}).get("Name", "")
        name = next((t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"), instance.get("InstanceId"))
        instance_info = {
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
            active_ec2.append(instance_info)
        else:
            stopped_ec2.append(instance_info)

# Analisi ENI orfane (non collegate a EC2)
eni_orphans = []
for eni in eni_data.get("NetworkInterfaces", []):
    attachment = eni.get("Attachment")
    if not attachment or not attachment.get("InstanceId"):
        eni_orphans.append({
            "NetworkInterfaceId": eni.get("NetworkInterfaceId"),
            "Description": eni.get("Description"),
            "SubnetId": eni.get("SubnetId"),
            "VpcId": eni.get("VpcId"),
            "PrivateIp": eni.get("PrivateIpAddress"),
        })

# Analisi Security Group non associati
sg_ids_in_use = set()
for eni in eni_data.get("NetworkInterfaces", []):
    for sg in eni.get("Groups", []):
        sg_ids_in_use.add(sg.get("GroupId"))

sg_not_used = []
for sg in sg_data.get("SecurityGroups", []):
    if sg.get("GroupId") not in sg_ids_in_use:
        sg_not_used.append({
            "GroupId": sg.get("GroupId"),
            "GroupName": sg.get("GroupName"),
            "Description": sg.get("Description"),
            "VpcId": sg.get("VpcId"),
        })

# Analisi Security Group troppo aperti
sg_too_open = []
for sg in sg_data.get("SecurityGroups", []):
    for rule in sg.get("IpPermissions", []):
        for ip_range in rule.get("IpRanges", []):
            if ip_range.get("CidrIp") == "0.0.0.0/0":
                sg_too_open.append({
                    "GroupId": sg.get("GroupId"),
                    "GroupName": sg.get("GroupName"),
                    "Port": rule.get("FromPort"),
                    "Protocol": rule.get("IpProtocol"),
                    "Description": sg.get("Description"),
                })

# Scrittura report
with open(REPORT_FILE, "w") as f:
    f.write("# AWS Resource Usage Report\n\n")
    f.write("## EC2 Instances (Running)\n")
    for inst in active_ec2:
        f.write(f"- **{inst['Name']}** ({inst['InstanceId']}), Type: {inst['Type']}, Subnet: {inst['SubnetId']}, VPC: {inst['VpcId']}, Public IP: {inst['PublicIp']}, Private IP: {inst['PrivateIp']}\n")
    f.write("\n## EC2 Instances (Stopped)\n")
    for inst in stopped_ec2:
        f.write(f"- **{inst['Name']}** ({inst['InstanceId']}), Type: {inst['Type']}, Subnet: {inst['SubnetId']}, VPC: {inst['VpcId']}\n")
    f.write("\n## Orphan ENIs (not attached to EC2)\n")
    for eni in eni_orphans:
        f.write(f"- {eni['NetworkInterfaceId']}, Subnet: {eni['SubnetId']}, VPC: {eni['VpcId']}, Private IP: {eni['PrivateIp']}\n")
    f.write("\n## Security Groups NOT in use\n")
    for sg in sg_not_used:
        f.write(f"- {sg['GroupName']} ({sg['GroupId']}), VPC: {sg['VpcId']}, Desc: {sg['Description']}\n")
    f.write("\n## Security Groups with open rules (0.0.0.0/0)\n")
    for sg in sg_too_open:
        f.write(f"- {sg['GroupName']} ({sg['GroupId']}), Port: {sg['Port']}, Protocol: {sg['Protocol']}, Desc: {sg['Description']}\n")

print(f"✅ Report scritto in {REPORT_FILE}")
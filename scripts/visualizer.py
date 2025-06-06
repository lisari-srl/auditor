import json
from pathlib import Path
from pyvis.network import Network
import shutil
import webbrowser

# Setup directories
base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "data"
reports_dir = base_dir / "reports"

# Ensure directories exist
reports_dir.mkdir(parents=True, exist_ok=True)

def load_json(path):
    if not path.exists():
        print(f"❌ File mancante: {path}")
        exit(1)
    with open(path) as f:
        return json.load(f)

# Caricamento dati
ec2_data = load_json(data_dir / "ec2_audit.json")
eni_data = load_json(data_dir / "eni_raw.json")
sg_data = load_json(data_dir / "sg_raw.json")

net = Network(height="800px", width="100%", bgcolor="#111", font_color="white")

colors = {
    "EC2": "#1f78b4",
    "ENI": "#33a02c",
    "SG": "#ff7f00"
}

# Aggiungi Security Groups con regole dettagliate
for sg in sg_data.get("SecurityGroups", []):
    sg_id = sg.get("GroupId")
    name = sg.get("GroupName", "")
    desc = sg.get("Description", "")
    vpc = sg.get("VpcId", "")
    ingress = sg.get("IpPermissions", [])
    egress = sg.get("IpPermissionsEgress", [])
    ingress_rules = "<br>".join([
        f"{r.get('IpProtocol')} {r.get('FromPort','')}-{r.get('ToPort','')} {','.join([ip.get('CidrIp','') for ip in r.get('IpRanges',[])])}"
        for r in ingress
    ]) or "Nessuna"
    egress_rules = "<br>".join([
        f"{r.get('IpProtocol')} {r.get('FromPort','')}-{r.get('ToPort','')} {','.join([ip.get('CidrIp','') for ip in r.get('IpRanges',[])])}"
        for r in egress
    ]) or "Nessuna"
    label = f"{name}\n{sg_id}"
    title = f"Desc: {desc}<br>VPC: {vpc}<br><b>Ingress:</b><br>{ingress_rules}<br><b>Egress:</b><br>{egress_rules}"
    net.add_node(sg_id, label=label, title=title, color=colors["SG"])

# Aggiungi EC2 con nome, tipo, stato, subnet, VPC
for reservation in ec2_data.get("Reservations", []):
    for instance in reservation.get("Instances", []):
        instance_id = instance.get("InstanceId")
        name = next((t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"), instance_id)
        state = instance.get("State", {}).get("Name", "")
        itype = instance.get("InstanceType", "")
        subnet = instance.get("SubnetId", "")
        vpc = instance.get("VpcId", "")
        label = f"{name}\n{instance_id}"
        title = f"Type: {itype}<br>State: {state}<br>Subnet: {subnet}<br>VPC: {vpc}"
        net.add_node(instance_id, label=label, title=title, color=colors["EC2"])

# Aggiungi ENI con dettagli e collegamenti
for eni in eni_data.get("NetworkInterfaces", []):
    eni_id = eni.get("NetworkInterfaceId")
    desc = eni.get("Description", "")
    subnet = eni.get("SubnetId", "")
    vpc = eni.get("VpcId", "")
    private_ip = eni.get("PrivateIpAddress", "")
    public_ip = eni.get("Association", {}).get("PublicIp", "")
    label = f"{eni_id}"
    title = f"Desc: {desc}<br>Subnet: {subnet}<br>VPC: {vpc}<br>Private IP: {private_ip}<br>Public IP: {public_ip}"
    net.add_node(eni_id, label=label, title=title, color=colors["ENI"])
    # Collegamento EC2 ⇄ ENI
    attachment = eni.get("Attachment")
    if attachment:
        instance_id = attachment.get("InstanceId")
        if instance_id:
            net.add_edge(instance_id, eni_id)
    # Collegamento ENI ⇄ SG
    for sg in eni.get("Groups", []):
        group_id = sg.get("GroupId")
        if group_id:
            net.add_edge(eni_id, group_id)

# Salva il grafo nella directory corrente
temp_html = "aws_network_graph.html"
net.write_html(temp_html)

# Sposta il file nella cartella reports
final_html = reports_dir / temp_html
shutil.move(temp_html, final_html)

print(f"✅ Grafico salvato in: {final_html}")

# Apri il file HTML salvato nel browser predefinito
webbrowser.open(final_html.as_uri())
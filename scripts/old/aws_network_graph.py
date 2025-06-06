import json
from pyvis.network import Network
import os

# Percorso assoluto delle cartelle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(BASE_DIR, "audit", "aws_network_graph.html")

# Caricamento dati
def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), "r") as f:
        return json.load(f)

# Carica i dati JSON salvati
ec2_instances = load_json("ec2_instances.json")
security_groups = load_json("security_groups.json")
network_interfaces = load_json("network_interfaces.json")
vpcs = load_json("vpcs.json")
subnets = load_json("subnets.json")
route_tables = load_json("route_tables.json")
internet_gateways = load_json("internet_gateways.json")
rds_instances = load_json("rds_instances.json") if os.path.exists(os.path.join(DATA_DIR, "rds_instances.json")) else {"DBInstances": []}
lambda_functions = load_json("lambda_functions.json") if os.path.exists(os.path.join(DATA_DIR, "lambda_functions.json")) else {"Functions": []}

# Crea la rete PyVis
net = Network(height="850px", width="100%", bgcolor="#1e1e1e", font_color="white")

net.set_options(json.dumps({
    "layout": {
        "hierarchical": {
            "enabled": False
        }
    },
    "physics": {
        "enabled": True,
        "stabilization": {
            "enabled": True,
            "iterations": 250,
            "updateInterval": 25,
            "fit": True
        },
        "barnesHut": {
            "gravitationalConstant": -8000,
            "springLength": 250,
            "springConstant": 0.04,
            "centralGravity": 0.3,
            "damping": 0.09
        }
    },
    "interaction": {
        "dragNodes": True,
        "dragView": True,
        "zoomView": True,
        "multiselect": True,
        "navigationButtons": True,
        "keyboard": {
            "enabled": True,
            "bindToWindow": True
        }
    },
    "manipulation": {
        "enabled": False
    },
    "groups": {
        "EC2": { "color": { "background": "#1E90FF" }, "shape": "box" },
        "ENI": { "color": { "background": "#32CD32" }, "shape": "ellipse" },
        "SG": { "color": { "background": "#FFD700" }, "shape": "hexagon" },
        "Subnet": { "color": { "background": "#FF8C00" }, "shape": "diamond" },
        "VPC": { "color": { "background": "#FF1493" }, "shape": "triangle" },
        "IGW": { "color": { "background": "#DC143C" }, "shape": "star" },
        "RT": { "color": { "background": "#4682B4" }, "shape": "triangleDown" },
        "RDS": { "color": { "background": "#20B2AA" }, "shape": "database" },
        "Lambda": { "color": { "background": "#DA70D6" }, "shape": "dot" }
    },
    "configure": {
        "enabled": True,
        "filter": ["physics"],
        "showButton": True
    }
}))

# Legenda fissa
legend = {
    "EC2": {"shape": "box", "color": "#1E90FF"},      # DodgerBlue
    "ENI": {"shape": "ellipse", "color": "#32CD32"},  # LimeGreen
    "SG": {"shape": "hexagon", "color": "#FFD700"},   # Gold
    "Subnet": {"shape": "diamond", "color": "#FF8C00"}, # DarkOrange
    "VPC": {"shape": "triangle", "color": "#FF1493"}, # DeepPink
    "IGW": {"shape": "star", "color": "#DC143C"},     # Crimson
    "RT": {"shape": "triangleDown", "color": "#4682B4"}, # SteelBlue
    "RDS": {"shape": "database", "color": "#20B2AA"}, # LightSeaGreen
    "Lambda": {"shape": "dot", "color": "#DA70D6"}    # Orchid
}

for label, style in legend.items():
    net.add_node(f"legend_{label}", label=label, **style, physics=False, fixed=True)

# Aggiunge i Security Groups
for sg in security_groups.get("SecurityGroups", []):
    net.add_node(
        sg["GroupId"],
        label=f"SG: {sg.get('GroupName', sg['GroupId'])}",
        title=f"Ingress: {len(sg.get('IpPermissions', []))} | Egress: {len(sg.get('IpPermissionsEgress', []))}",
        **legend["SG"]
    )

# Aggiunge gli EC2
for reservation in ec2_instances.get("Reservations", []):
    for instance in reservation.get("Instances", []):
        instance_id = instance["InstanceId"]
        name_tag = next((t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"), instance_id)
        net.add_node(
            instance_id,
            label=f"EC2: {name_tag}",
            title=f"Type: {instance.get('InstanceType')}",
            **legend["EC2"]
        )
        for sg in instance.get("SecurityGroups", []):
            net.add_edge(instance_id, sg["GroupId"], label="attached")

# Aggiunge le ENI
for eni in network_interfaces.get("NetworkInterfaces", []):
    eni_id = eni["NetworkInterfaceId"]
    net.add_node(
        eni_id,
        label=f"ENI: {eni_id}",
        **legend["ENI"]
    )
    for sg in eni.get("Groups", []):
        net.add_edge(eni_id, sg["GroupId"], label="SG")
    if "Attachment" in eni and "InstanceId" in eni["Attachment"]:
        net.add_edge(eni["Attachment"]["InstanceId"], eni_id, label="attached")

# Aggiunge VPC/Subnet/IGW/RT
for vpc in vpcs.get("Vpcs", []):
    vpc_id = vpc["VpcId"]
    net.add_node(vpc_id, label=f"VPC: {vpc_id}", **legend["VPC"])

for subnet in subnets.get("Subnets", []):
    subnet_id = subnet["SubnetId"]
    vpc_id = subnet["VpcId"]
    net.add_node(subnet_id, label=f"Subnet: {subnet_id}", **legend["Subnet"])
    net.add_edge(subnet_id, vpc_id, label="belongs to")
    for eni in network_interfaces.get("NetworkInterfaces", []):
        if eni.get("SubnetId") == subnet_id:
            net.add_edge(eni["NetworkInterfaceId"], subnet_id, label="in subnet")

for igw in internet_gateways.get("InternetGateways", []):
    igw_id = igw["InternetGatewayId"]
    net.add_node(igw_id, label=f"IGW: {igw_id}", **legend["IGW"])
    for attachment in igw.get("Attachments", []):
        net.add_edge(igw_id, attachment["VpcId"], label="attached")

for rt in route_tables.get("RouteTables", []):
    rt_id = rt["RouteTableId"]
    net.add_node(rt_id, label=f"RT: {rt_id}", **legend["RT"])
    for assoc in rt.get("Associations", []):
        if assoc.get("SubnetId"):
            net.add_edge(rt_id, assoc["SubnetId"], label="routed")

# Aggiunge RDS
for rds in rds_instances.get("DBInstances", []):
    rds_id = rds["DBInstanceIdentifier"]
    net.add_node(rds_id, label=f"RDS: {rds_id}", **legend["RDS"])
    for sg in rds.get("VpcSecurityGroups", []):
        net.add_edge(rds_id, sg["VpcSecurityGroupId"], label="SG")

# Aggiunge Lambda
for lmb in lambda_functions.get("Functions", []):
    name = lmb["FunctionName"]
    net.add_node(name, label=f"Lambda: {name}", **legend["Lambda"])
    if "VpcConfig" in lmb:
        for sg in lmb["VpcConfig"].get("SecurityGroupIds", []):
            net.add_edge(name, sg, label="SG")
        for subnet in lmb["VpcConfig"].get("SubnetIds", []):
            net.add_edge(name, subnet, label="in subnet")

#
# Posizionamento fisso della legenda
legend_positions = {
    "legend_EC2": (-800, -400),
    "legend_ENI": (-800, -350),
    "legend_SG": (-800, -300),
    "legend_Subnet": (-800, -250),
    "legend_VPC": (-800, -200),
    "legend_IGW": (-800, -150),
    "legend_RT": (-800, -100),
    "legend_RDS": (-800, -50),
    "legend_Lambda": (-800, 0)
}

for node_id, (x, y) in legend_positions.items():
    net.nodes = [
        {**n, "x": x, "y": y, "fixed": {"x": True, "y": True}} if n["id"] == node_id else n
        for n in net.nodes
    ]

# Esporta mappa
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
html = net.generate_html()
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Mappa generata: {OUTPUT_FILE}")
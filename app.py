import streamlit as st
import json
import os

DATA_DIR = "data"
REPORTS_DIR = "reports"

st.set_page_config(layout="wide")
st.title("🔍 AWS Infrastructure Audit - Dashboard")

# Funzione di utilità
def load_json(filename):
    try:
        with open(os.path.join(DATA_DIR, filename)) as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning(f"⚠️ File non trovato: {filename}")
        return []

# Funzione per visualizzare la mappa interattiva con PyVis
def show_network_map():
    from pyvis.network import Network
    import networkx as nx
    import streamlit.components.v1 as components

    # Esempio: crea un grafo semplice tra EC2, ENI e SG
    ec2_data = load_json("ec2_audit.json")
    eni_data = load_json("eni_raw.json")
    sg_data = load_json("sg_raw.json")

    G = nx.Graph()

    # Aggiungi EC2
    for group in ec2_data.get("active", []) + ec2_data.get("stopped", []):
        G.add_node(group["InstanceId"], label=group["Name"], group="EC2")
        # Collega EC2 a ENI
        if group.get("NetworkInterfaces"):
            for eni in group["NetworkInterfaces"]:
                G.add_edge(group["InstanceId"], eni, label="ENI")
        # Collega EC2 a SG
        for sg in group.get("SecurityGroups", []):
            G.add_edge(group["InstanceId"], sg, label="SG")

    # Aggiungi ENI
    for eni in eni_data.get("NetworkInterfaces", []):
        G.add_node(eni["NetworkInterfaceId"], label=eni["NetworkInterfaceId"], group="ENI")
        # Collega ENI a SG
        for sg in eni.get("Groups", []):
            G.add_edge(eni["NetworkInterfaceId"], sg["GroupId"], label="SG")

    # Aggiungi SG
    for sg in sg_data.get("SecurityGroups", []):
        G.add_node(sg["GroupId"], label=sg["GroupName"], group="SG")

    net = Network(height="600px", width="100%", notebook=False, directed=False)
    net.from_nx(G)
    net.repulsion(node_distance=200, central_gravity=0.3, spring_length=200, spring_strength=0.05, damping=0.95)
    net.toggle_physics(True)
    net.show_buttons(filter_=['physics'])

    net.save_graph("temp_network.html")
    with open("temp_network.html", "r", encoding="utf-8") as f:
        html = f.read()
    components.html(html, height=650, scrolling=True)

# Sidebar
st.sidebar.header("🔧 Seleziona Risorsa")
resource = st.sidebar.selectbox(
    "Tipo",
    [
        "EC2",
        "ENI",
        "Security Groups",
        "S3 Buckets",
        "IAM",
        "VPC",
        "Subnet",
        "Route Table",
        "Internet Gateway",
        "Mappa Risorse"
    ]
)

# Main display
if resource == "EC2":
    ec2_data = load_json("ec2_audit.json")
    st.subheader("🖥️ EC2 Instances")
    st.json(ec2_data)

elif resource == "ENI":
    eni_data = load_json("eni_raw.json")
    st.subheader("🔗 Elastic Network Interfaces (ENI)")
    st.json(eni_data)

elif resource == "Security Groups":
    sg_data = load_json("sg_raw.json")
    st.subheader("🛡️ Security Groups")
    st.json(sg_data)

elif resource == "S3 Buckets":
    s3_data = load_json("s3_raw.json")
    st.subheader("🗂️ S3 Buckets")
    st.json(s3_data)

elif resource == "IAM":
    iam_data = load_json("iam_audit.json")
    st.subheader("👤 IAM (Users, Roles, Policies)")
    st.json(iam_data)

elif resource == "VPC":
    vpc_data = load_json("vpc_raw.json")
    st.subheader("🌐 VPC")
    st.json(vpc_data)

elif resource == "Subnet":
    subnet_data = load_json("subnet_raw.json")
    st.subheader("🔸 Subnets")
    st.json(subnet_data)

elif resource == "Route Table":
    rt_data = load_json("route_table_raw.json")
    st.subheader("🛣️ Route Tables")
    st.json(rt_data)

elif resource == "Internet Gateway":
    igw_data = load_json("igw_raw.json")
    st.subheader("🌉 Internet Gateways")
    st.json(igw_data)

elif resource == "Mappa Risorse":
    st.subheader("🌐 Mappa Interattiva delle Risorse AWS")
    show_network_map()

# Opzionale: link alla mappa HTML
st.markdown("---")
network_map_path = os.path.join(REPORTS_DIR, "aws_network_graph.html")
if os.path.exists(network_map_path):
    st.markdown(f"🌐 [Apri la mappa visiva della rete]({network_map_path})")
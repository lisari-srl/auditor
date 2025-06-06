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
        "Internet Gateway"
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

# Opzionale: link alla mappa HTML
st.markdown("---")
network_map_path = os.path.join(REPORTS_DIR, "aws_network_graph.html")
if os.path.exists(network_map_path):
    st.markdown(f"🌐 [Apri la mappa visiva della rete]({network_map_path})")
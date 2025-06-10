# dashboard/app.py
import streamlit as st
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import sys
import subprocess

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Safe imports with fallbacks
try:
    from config.audit_rules import Severity
except ImportError:
    # Fallback se non riesce a importare
    class Severity:
        CRITICAL = "critical"
        HIGH = "high" 
        MEDIUM = "medium"
        LOW = "low"

# Page config
st.set_page_config(
    page_title="AWS Security Audit Dashboard",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .critical-finding {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
        margin: 0.5rem 0;
    }
    .high-finding {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff9800;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

class SecurityDashboard:
    def __init__(self):
        self.data_dir = Path("data")
        self.reports_dir = Path("reports")
        
    def load_json(self, filename: str):
        """Carica file JSON con gestione errori"""
        try:
            file_path = self.data_dir / filename
            if file_path.exists():
                with open(file_path) as f:
                    return json.load(f)
            else:
                st.warning(f"⚠️ File non trovato: {filename}")
                return {}
        except Exception as e:
            st.error(f"❌ Errore caricamento {filename}: {e}")
            return {}
    
    def load_security_findings(self):
        """Carica findings di sicurezza"""
        findings_file = self.reports_dir / "security_findings.json"
        if findings_file.exists():
            try:
                with open(findings_file) as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"❌ Errore caricamento security findings: {e}")
        return None
    
    def render_header(self):
        """Render header del dashboard"""
        st.title("🔒 AWS Infrastructure Security Dashboard")
        
        # Load last scan info
        findings_data = self.load_security_findings()
        if findings_data and "metadata" in findings_data:
            metadata = findings_data["metadata"]
            scan_time = metadata.get("scan_time", "Unknown")
            try:
                scan_date = datetime.fromisoformat(scan_time.replace('Z', '+00:00'))
                time_ago = datetime.now() - scan_date.replace(tzinfo=None)
                
                if time_ago.days > 0:
                    time_str = f"{time_ago.days} giorni fa"
                elif time_ago.seconds > 3600:
                    time_str = f"{time_ago.seconds // 3600} ore fa" 
                else:
                    time_str = f"{time_ago.seconds // 60} minuti fa"
                    
                st.info(f"📅 Ultimo scan: {scan_date.strftime('%Y-%m-%d %H:%M')} ({time_str})")
            except:
                st.info(f"📅 Ultimo scan: {scan_time}")
    
    def render_metrics_overview(self):
        """Render overview con metriche principali"""
        st.subheader("📊 Security Overview")
        
        findings_data = self.load_security_findings()
        if not findings_data:
            st.warning("⚠️ Nessun dato di security audit disponibile. Eseguire prima `python main.py`")
            return
        
        # Extract metrics
        findings = findings_data.get("findings", [])
        metadata = findings_data.get("metadata", {})
        
        # Count by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in findings:
            severity = finding.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Metrics columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🔴 Critical Findings",
                value=severity_counts["critical"],
                delta=f"{metadata.get('total_findings', 0)} total"
            )
        
        with col2:
            st.metric(
                label="🟠 High Findings", 
                value=severity_counts["high"],
                delta="Security issues"
            )
        
        with col3:
            st.metric(
                label="🟡 Medium Findings",
                value=severity_counts["medium"],
                delta="Configuration issues"
            )
        
        with col4:
            st.metric(
                label="🔵 Low Findings",
                value=severity_counts["low"],
                delta="Best practices"
            )
    
    def render_findings_charts(self):
        """Render grafici dei findings"""
        findings_data = self.load_security_findings()
        if not findings_data:
            return
        
        findings = findings_data.get("findings", [])
        if not findings:
            st.info("ℹ️ Nessun finding di sicurezza trovato")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Findings per Severity")
            
            # Count by severity
            severity_counts = {}
            for finding in findings:
                severity = finding.get("severity", "low")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Create pie chart
            if severity_counts:
                colors = {
                    "critical": "#d32f2f",
                    "high": "#f57c00", 
                    "medium": "#fbc02d",
                    "low": "#1976d2"
                }
                
                fig = go.Figure(data=[go.Pie(
                    labels=list(severity_counts.keys()),
                    values=list(severity_counts.values()),
                    marker_colors=[colors.get(k, "#gray") for k in severity_counts.keys()],
                    hole=0.4
                )])
                
                fig.update_layout(
                    title="Distribuzione per Severity",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Findings per Risorsa")
            
            # Count by resource type
            resource_counts = {}
            for finding in findings:
                resource_type = finding.get("resource_type", "Unknown")
                resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
            
            if resource_counts:
                # Create bar chart
                fig = px.bar(
                    x=list(resource_counts.values()),
                    y=list(resource_counts.keys()),
                    orientation='h',
                    title="Findings per Tipo Risorsa",
                    color=list(resource_counts.values()),
                    color_continuous_scale="Reds"
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    def render_critical_findings(self):
        """Render sezione findings critici"""
        findings_data = self.load_security_findings()
        if not findings_data:
            return
        
        findings = findings_data.get("findings", [])
        critical_findings = [f for f in findings if f.get("severity") == "critical"]
        high_findings = [f for f in findings if f.get("severity") == "high"]
        
        if critical_findings or high_findings:
            st.subheader("🚨 Priority Findings")
            
            # Critical findings
            if critical_findings:
                st.markdown("#### 🔴 Critical Issues")
                for finding in critical_findings[:5]:  # Show max 5
                    with st.expander(f"🔴 {finding.get('rule_name', 'Unknown')} - {finding.get('resource_name', 'Unknown')}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Descrizione**: {finding.get('description', 'N/A')}")
                            st.write(f"**Raccomandazione**: {finding.get('recommendation', 'N/A')}")
                            if finding.get('remediation'):
                                st.code(finding['remediation'], language='bash')
                        
                        with col2:
                            st.write(f"**Risorsa**: {finding.get('resource_id', 'N/A')}")
                            st.write(f"**Regione**: {finding.get('region', 'N/A')}")
                            st.write(f"**Compliance**: {', '.join(finding.get('compliance_frameworks', []))}")
            
            # High findings
            if high_findings:
                st.markdown("#### 🟠 High Priority Issues")
                for finding in high_findings[:3]:  # Show max 3
                    with st.expander(f"🟠 {finding.get('rule_name', 'Unknown')} - {finding.get('resource_name', 'Unknown')}"):
                        st.write(f"**Descrizione**: {finding.get('description', 'N/A')}")
                        st.write(f"**Raccomandazione**: {finding.get('recommendation', 'N/A')}")
    
    def render_resource_inventory(self):
        """Render inventario risorse"""
        st.subheader("📦 Resource Inventory")
        
        # Tabs per diversi tipi di risorse
        tab1, tab2, tab3, tab4 = st.tabs(["🖥️ EC2", "🛡️ Security Groups", "🗂️ S3", "👤 IAM"])
        
        with tab1:
            self.render_ec2_inventory()
        
        with tab2:
            self.render_sg_inventory()
        
        with tab3:
            self.render_s3_inventory()
            
        with tab4:
            self.render_iam_inventory()
    
    def render_ec2_inventory(self):
        """Render inventario EC2"""
        try:
            ec2_data = self.load_json("ec2_audit.json")
            
            if not ec2_data:
                st.info("ℹ️ Nessun dato EC2 disponibile")
                return
            
            active_instances = ec2_data.get("active", [])
            stopped_instances = ec2_data.get("stopped", [])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("🟢 Running Instances", len(active_instances))
                
                if active_instances:
                    df = pd.DataFrame(active_instances)
                    display_cols = ["Name", "Type", "PublicIp", "PrivateIp"]
                    available_cols = [col for col in display_cols if col in df.columns]
                    if available_cols:
                        st.dataframe(
                            df[available_cols].fillna("N/A"),
                            use_container_width=True
                        )
            
            with col2:
                st.metric("🔴 Stopped Instances", len(stopped_instances))
                
                if stopped_instances:
                    df = pd.DataFrame(stopped_instances)
                    display_cols = ["Name", "Type", "SubnetId"]
                    available_cols = [col for col in display_cols if col in df.columns]
                    if available_cols:
                        st.dataframe(
                            df[available_cols].fillna("N/A"),
                            use_container_width=True
                        )
        except Exception as e:
            st.error(f"Errore caricamento dati EC2: {e}")
    
    def render_sg_inventory(self):
        """Render inventario Security Groups"""
        try:
            sg_data = self.load_json("sg_raw.json")
            sg_audit = self.load_json("sg_audit.json")
            
            if not sg_data:
                st.info("ℹ️ Nessun dato Security Groups disponibile")
                return
            
            security_groups = sg_data.get("SecurityGroups", [])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("🛡️ Total Security Groups", len(security_groups))
                
                # Show SG with issues
                if sg_audit:
                    open_ingress = len(sg_audit.get("open_ingress", []))
                    unused = len(sg_audit.get("unused", []))
                    
                    if open_ingress > 0:
                        st.warning(f"⚠️ {open_ingress} SG con regole ingress aperte")
                    if unused > 0:
                        st.info(f"ℹ️ {unused} SG non utilizzati")
            
            with col2:
                if security_groups:
                    # Create DataFrame for display
                    sg_summary = []
                    for sg in security_groups[:10]:  # Show first 10
                        sg_summary.append({
                            "Name": sg.get("GroupName", "N/A"),
                            "ID": sg.get("GroupId", "N/A"),
                            "Ingress Rules": len(sg.get("IpPermissions", [])),
                            "Egress Rules": len(sg.get("IpPermissionsEgress", []))
                        })
                    
                    if sg_summary:
                        df = pd.DataFrame(sg_summary)
                        st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Errore caricamento dati SG: {e}")
    
    def render_s3_inventory(self):
        """Render inventario S3"""
        try:
            s3_data = self.load_json("s3_raw.json")
            
            if not s3_data or not isinstance(s3_data, list):
                st.info("ℹ️ Nessun dato S3 disponibile")
                return
            
            st.metric("🗂️ Total S3 Buckets", len(s3_data))
            
            # Check for public buckets
            public_buckets = [b for b in s3_data if b.get("PublicAccess", False)]
            if public_buckets:
                st.error(f"🚨 {len(public_buckets)} bucket pubblicamente accessibili!")
            
            # Create DataFrame
            bucket_summary = []
            for bucket in s3_data:
                bucket_summary.append({
                    "Name": bucket.get("Name", "N/A"),
                    "Creation Date": bucket.get("CreationDate", "N/A"),
                    "Public Access": "🔴 Yes" if bucket.get("PublicAccess", False) else "🟢 No",
                    "Has Policy": "Yes" if bucket.get("Policy") else "No"
                })
            
            if bucket_summary:
                df = pd.DataFrame(bucket_summary)
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Errore caricamento dati S3: {e}")
    
    def render_iam_inventory(self):
        """Render inventario IAM"""
        try:
            iam_data = self.load_json("iam_raw.json")
            
            if not iam_data:
                st.info("ℹ️ Nessun dato IAM disponibile")
                return
            
            users = iam_data.get("Users", [])
            roles = iam_data.get("Roles", [])
            policies = iam_data.get("Policies", [])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("👤 IAM Users", len(users))
            with col2:
                st.metric("🎭 IAM Roles", len(roles))
            with col3:
                st.metric("📋 IAM Policies", len(policies))
            
            # Show recent users
            if users:
                st.subheader("Recent IAM Users")
                user_summary = []
                for user in users[:10]:
                    last_used = user.get("PasswordLastUsed", "Never")
                    if last_used and last_used != "Never":
                        try:
                            last_used_date = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
                            days_ago = (datetime.now() - last_used_date.replace(tzinfo=None)).days
                            last_used = f"{days_ago} giorni fa"
                        except:
                            pass
                    
                    user_summary.append({
                        "Username": user.get("UserName", "N/A"),
                        "Created": user.get("CreateDate", "N/A")[:10] if user.get("CreateDate") else "N/A",
                        "Last Password Use": last_used
                    })
                
                if user_summary:
                    df = pd.DataFrame(user_summary)
                    st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Errore caricamento dati IAM: {e}")
    
    def render_network_map(self):
        """Render mappa di rete con fallback sicuro"""
        st.subheader("🌐 Network Topology")
        
        # Check if pyvis is available
        try:
            from pyvis.network import Network
            import networkx as nx
            import streamlit.components.v1 as components
            pyvis_available = True
        except ImportError:
            pyvis_available = False
        
        if not pyvis_available:
            st.warning("⚠️ PyVis non disponibile. Installare con: `pip install pyvis networkx`")
            self.render_network_table()
            return
        
        try:
            # Load data for network map
            ec2_data = self.load_json("ec2_audit.json")
            sg_data = self.load_json("sg_raw.json")
            
            if not ec2_data or not sg_data:
                st.info("ℹ️ Dati insufficienti per generare mappa di rete")
                self.render_network_table()
                return
            
            # Create network graph
            G = nx.Graph()
            
            # Add EC2 instances
            all_instances = ec2_data.get("active", []) + ec2_data.get("stopped", [])
            for instance in all_instances:
                instance_id = instance.get("InstanceId", "unknown")
                instance_name = instance.get("Name", instance_id)
                state = instance.get("State", "unknown")
                
                # Color based on state
                color = "#4CAF50" if state == "running" else "#f44336"
                
                G.add_node(
                    instance_id,
                    label=instance_name,
                    group="EC2",
                    color=color,
                    title=f"Type: {instance.get('Type', 'unknown')}<br>State: {state}"
                )
                
                # Connect to security groups
                for sg_id in instance.get("SecurityGroups", []):
                    if sg_id:  # Only add if sg_id is not None
                        G.add_edge(instance_id, sg_id, label="uses")
            
            # Add Security Groups
            for sg in sg_data.get("SecurityGroups", []):
                sg_id = sg.get("GroupId", "unknown")
                sg_name = sg.get("GroupName", sg_id)
                
                # Check if SG has open rules
                has_open_rules = False
                for rule in sg.get("IpPermissions", []) + sg.get("IpPermissionsEgress", []):
                    for ip_range in rule.get("IpRanges", []):
                        if ip_range.get("CidrIp") == "0.0.0.0/0":
                            has_open_rules = True
                            break
                
                color = "#FF9800" if has_open_rules else "#2196F3"
                
                G.add_node(
                    sg_id,
                    label=sg_name,
                    group="SG", 
                    color=color,
                    title=f"Security Group<br>Ingress: {len(sg.get('IpPermissions', []))}<br>Egress: {len(sg.get('IpPermissionsEgress', []))}"
                )
            
            # Only create network if we have nodes
            if len(G.nodes()) > 0:
                # Create PyVis network
                net = Network(height="600px", width="100%", bgcolor="#f8f9fa")
                net.from_nx(G)
                net.repulsion(node_distance=200, central_gravity=0.3, spring_length=200)
                net.set_options("""
                var options = {
                  "physics": {
                    "enabled": true,
                    "stabilization": {"iterations": 100}
                  }
                }
                """)
                
                # Generate and display
                temp_file = "temp_network.html"
                net.save_graph(temp_file)
                
                with open(temp_file, "r", encoding="utf-8") as f:
                    html = f.read()
                components.html(html, height=650)
                
                # Cleanup
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            else:
                st.info("ℹ️ Nessun nodo da visualizzare nella mappa di rete")
                self.render_network_table()
            
        except Exception as e:
            st.error(f"❌ Errore generazione mappa: {e}")
            self.render_network_table()
    
    def render_network_table(self):
        """Fallback: render tabella connections invece di mappa"""
        st.subheader("📋 Network Connections (Table View)")
        
        try:
            ec2_data = self.load_json("ec2_audit.json")
            sg_data = self.load_json("sg_raw.json")
            
            if not ec2_data or not sg_data:
                st.info("ℹ️ Dati insufficienti")
                return
            
            # Create connections table
            connections = []
            all_instances = ec2_data.get("active", []) + ec2_data.get("stopped", [])
            
            for instance in all_instances:
                instance_name = instance.get("Name", instance.get("InstanceId", "Unknown"))
                state = instance.get("State", "unknown")
                
                for sg_id in instance.get("SecurityGroups", []):
                    if sg_id:  # Only process if sg_id is not None
                        # Find SG name
                        sg_name = sg_id
                        for sg in sg_data.get("SecurityGroups", []):
                            if sg.get("GroupId") == sg_id:
                                sg_name = sg.get("GroupName", sg_id)
                                break
                        
                        connections.append({
                            "Instance": instance_name,
                            "State": state,
                            "Security Group": sg_name,
                            "SG ID": sg_id
                        })
            
            if connections:
                df = pd.DataFrame(connections)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Nessuna connessione trovata")
                
        except Exception as e:
            st.error(f"Errore generazione tabella: {e}")

    # ========== NUOVI METODI VPC ==========
    
    def render_vpc_overview(self):
        """Render overview VPC e networking"""
        st.subheader("🌐 VPC & Network Infrastructure")
        
        # Carica dati VPC
        vpc_audit_data = self.load_json("vpc_audit.json")
        vpc_findings = self.load_security_findings()
        
        if not vpc_audit_data:
            st.warning("⚠️ Nessun dato VPC disponibile. Eseguire prima `python main.py --vpc-analysis`")
            return
        
        # Extract data
        metadata = vpc_audit_data.get("metadata", {})
        network_topology = vpc_audit_data.get("network_topology", {})
        cost_analysis = vpc_audit_data.get("cost_analysis", {})
        
        # VPC Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🏗️ Total VPCs",
                value=metadata.get("total_vpcs", 0),
                delta="Network isolation"
            )
        
        with col2:
            st.metric(
                label="🔗 Total Subnets",
                value=metadata.get("total_subnets", 0),
                delta="Network segments"
            )
        
        with col3:
            st.metric(
                label="🌐 NAT Gateways",
                value=metadata.get("total_nat_gateways", 0),
                delta=f"${cost_analysis.get('total_monthly_nat_cost', 0):.0f}/month"
            )
        
        with col4:
            potential_savings = cost_analysis.get("potential_monthly_savings", 0)
            st.metric(
                label="💰 Potential Savings",
                value=f"${potential_savings:.2f}/month",
                delta=f"${potential_savings * 12:.2f}/year"
            )

    def render_network_topology_advanced(self):
        """Render topologia di rete avanzata"""
        st.subheader("🏗️ Network Topology Analysis")
        
        vpc_audit_data = self.load_json("vpc_audit.json")
        if not vpc_audit_data:
            st.info("No VPC topology data available")
            return
        
        network_topology = vpc_audit_data.get("network_topology", {})
        
        if not network_topology:
            st.info("No network topology found")
            return
        
        # VPC selector
        vpc_ids = list(network_topology.keys())
        if not vpc_ids:
            st.info("No VPCs found in topology")
            return
        
        selected_vpc = st.selectbox("Select VPC to analyze:", vpc_ids)
        
        if selected_vpc:
            vpc_data = network_topology[selected_vpc]
            
            # VPC Info
            st.markdown(f"### VPC {selected_vpc}")
            vpc_info = vpc_data.get("vpc_info", {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**CIDR Block**: {vpc_info.get('CidrBlock', 'N/A')}")
                st.write(f"**State**: {vpc_info.get('State', 'N/A')}")
                st.write(f"**Is Default**: {vpc_info.get('IsDefault', False)}")
            
            with col2:
                st.write(f"**Total Subnets**: {vpc_data.get('total_subnets', 0)}")
                st.write(f"**Availability Zones**: {len(vpc_data.get('availability_zones', []))}")
                st.write(f"**NAT Gateways**: {len(vpc_data.get('nat_gateways', []))}")
            
            # Subnet Distribution
            st.markdown("#### Subnet Distribution")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                public_subnets = vpc_data.get("public_subnets", [])
                st.metric("🌍 Public Subnets", len(public_subnets))
                
                if public_subnets:
                    with st.expander("View Public Subnets"):
                        for subnet in public_subnets:
                            st.write(f"- {subnet.get('SubnetId')} ({subnet.get('CidrBlock')}) - {subnet.get('AvailabilityZone')}")
            
            with col2:
                private_subnets = vpc_data.get("private_subnets", [])
                st.metric("🔒 Private Subnets", len(private_subnets))
                
                if private_subnets:
                    with st.expander("View Private Subnets"):
                        for subnet in private_subnets:
                            st.write(f"- {subnet.get('SubnetId')} ({subnet.get('CidrBlock')}) - {subnet.get('AvailabilityZone')}")
            
            with col3:
                isolated_subnets = vpc_data.get("isolated_subnets", [])
                st.metric("🏝️ Isolated Subnets", len(isolated_subnets))
                
                if isolated_subnets:
                    with st.expander("View Isolated Subnets"):
                        for subnet in isolated_subnets:
                            st.write(f"- {subnet.get('SubnetId')} ({subnet.get('CidrBlock')}) - {subnet.get('AvailabilityZone')}")
            
            # CIDR Utilization
            cidr_util = vpc_data.get("cidr_utilization", {})
            if cidr_util and not cidr_util.get("error"):
                st.markdown("#### CIDR Utilization")
                
                total_ips = cidr_util.get("vpc_total_ips", 0)
                allocated_ips = cidr_util.get("subnet_allocated_ips", 0)
                utilization = cidr_util.get("utilization_percent", 0)
                
                # Progress bar for utilization
                st.progress(utilization / 100)
                st.write(f"**Utilization**: {utilization:.1f}% ({allocated_ips:,} of {total_ips:,} IPs allocated)")
                
                if utilization < 20:
                    st.info("💡 Low CIDR utilization - consider smaller VPC for future deployments")
                elif utilization > 80:
                    st.warning("⚠️ High CIDR utilization - consider planning for expansion")
            
            # Network Gateways
            st.markdown("#### Network Gateways")
            
            igws = vpc_data.get("internet_gateways", [])
            nat_gws = vpc_data.get("nat_gateways", [])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Internet Gateways**: {len(igws)}")
                if igws:
                    for igw in igws:
                        st.write(f"- {igw.get('InternetGatewayId')} ({igw.get('State', 'unknown')})")
            
            with col2:
                st.write(f"**NAT Gateways**: {len(nat_gws)}")
                if nat_gws:
                    for nat_gw in nat_gws:
                        state = nat_gw.get("State", "unknown")
                        cost_per_month = 45.36 if state == "available" else 0
                        st.write(f"- {nat_gw.get('NatGatewayId')} ({state}) - ${cost_per_month:.2f}/month")

    def render_vpc_cost_analysis(self):
        """Render analisi costi VPC"""
        st.subheader("💰 VPC Cost Analysis")
        
        vpc_audit_data = self.load_json("vpc_audit.json")
        if not vpc_audit_data:
            st.info("No VPC cost data available")
            return
        
        cost_analysis = vpc_audit_data.get("cost_analysis", {})
        
        # Cost Overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            monthly_nat_cost = cost_analysis.get("total_monthly_nat_cost", 0)
            st.metric(
                label="💸 NAT Gateway Costs",
                value=f"${monthly_nat_cost:.2f}/month",
                delta=f"${monthly_nat_cost * 12:.2f}/year"
            )
        
        with col2:
            potential_savings = cost_analysis.get("potential_monthly_savings", 0)
            st.metric(
                label="💰 Potential Savings",
                value=f"${potential_savings:.2f}/month",
                delta=f"{(potential_savings/monthly_nat_cost*100) if monthly_nat_cost > 0 else 0:.1f}% reduction"
            )
        
        with col3:
            vpc_endpoints = cost_analysis.get("total_vpc_endpoints", 0)
            st.metric(
                label="🔗 VPC Endpoints",
                value=vpc_endpoints,
                delta="Data transfer savings"
            )
        
        # Optimization Opportunities
        optimizations = cost_analysis.get("optimization_opportunities", [])
        
        if optimizations:
            st.markdown("#### 🎯 Cost Optimization Opportunities")
            
            for opt in optimizations:
                with st.expander(f"💰 {opt.get('recommendation', 'Optimization')} - ${opt.get('potential_monthly_savings', 0):.2f}/month"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**VPC**: {opt.get('vpc_id', 'N/A')}")
                        st.write(f"**Current NAT Count**: {opt.get('current_nat_count', 0)}")
                        st.write(f"**Monthly Savings**: ${opt.get('potential_monthly_savings', 0):.2f}")
                    
                    with col2:
                        st.write(f"**Annual Savings**: ${opt.get('potential_monthly_savings', 0) * 12:.2f}")
                        st.write(f"**Recommendation**: {opt.get('recommendation', 'N/A')}")
                        
                        if st.button(f"Generate Optimization Script", key=f"opt_{opt.get('vpc_id')}"):
                            script = self.generate_nat_optimization_script(opt)
                            st.code(script, language='bash')
        else:
            st.success("✅ No cost optimization opportunities found - your VPC setup is already optimized!")

    def render_vpc_security_analysis(self):
        """Render analisi sicurezza VPC"""
        st.subheader("🛡️ VPC Security Analysis")
        
        # Carica VPC findings
        findings_data = self.load_security_findings()
        if not findings_data:
            st.info("No security findings available")
            return
        
        findings = findings_data.get("findings", [])
        
        # Filter VPC-related findings
        vpc_findings = [f for f in findings if f.get("resource_type") in ["VPC", "Subnet", "RouteTable", "NATGateway"]]
        
        if not vpc_findings:
            st.success("✅ No VPC security issues found!")
            return
        
        # Security metrics
        security_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in vpc_findings:
            severity = finding.get("severity", "low")
            security_severity[severity] += 1
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔴 Critical", security_severity["critical"])
        with col2:
            st.metric("🟠 High", security_severity["high"])
        with col3:
            st.metric("🟡 Medium", security_severity["medium"])
        with col4:
            st.metric("🔵 Low", security_severity["low"])
        
        # VPC Security Issues
        if security_severity["critical"] > 0 or security_severity["high"] > 0:
            st.markdown("#### 🚨 Priority Security Issues")
            
            priority_findings = [f for f in vpc_findings if f.get("severity") in ["critical", "high"]]
            
            for finding in priority_findings[:5]:  # Show top 5
                severity = finding.get("severity", "low")
                severity_color = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}[severity]
                
                with st.expander(f"{severity_color} {finding.get('rule_name', 'Security Issue')} - {finding.get('resource_name', 'Unknown')}"):
                    st.write(f"**Resource Type**: {finding.get('resource_type', 'N/A')}")
                    st.write(f"**Description**: {finding.get('description', 'N/A')}")
                    st.write(f"**Recommendation**: {finding.get('recommendation', 'N/A')}")
                    
                    if finding.get('remediation'):
                        st.code(finding['remediation'], language='bash')
        
        # VPC Configuration Issues
        vpc_config_findings = [f for f in vpc_findings if "VPC" in f.get("resource_type", "")]
        
        if vpc_config_findings:
            st.markdown("#### 🏗️ VPC Configuration Issues")
            
            for finding in vpc_config_findings:
                severity = finding.get("severity", "low")
                if severity in ["medium", "low"]:  # Show non-critical issues
                    st.info(f"**{finding.get('rule_name')}**: {finding.get('description')}")

    def render_network_recommendations(self):
        """Render raccomandazioni di rete"""
        st.subheader("💡 Network Optimization Recommendations")
        
        vpc_audit_data = self.load_json("vpc_audit.json")
        if not vpc_audit_data:
            st.info("No VPC data for recommendations")
            return
        
        # Analisi dati per raccomandazioni
        network_topology = vpc_audit_data.get("network_topology", {})
        cost_analysis = vpc_audit_data.get("cost_analysis", {})
        
        recommendations = []
        
        # Generate recommendations based on analysis
        for vpc_id, vpc_data in network_topology.items():
            vpc_recommendations = self.generate_vpc_recommendations(vpc_id, vpc_data, cost_analysis)
            recommendations.extend(vpc_recommendations)
        
        if not recommendations:
            st.success("✅ Your VPC configuration is well-optimized! No recommendations at this time.")
            return
        
        # Group recommendations by priority
        priority_groups = {"High Priority": [], "Medium Priority": [], "Low Priority": []}
        
        for rec in recommendations:
            priority = rec.get("priority", "Low Priority")
            if priority in priority_groups:
                priority_groups[priority].append(rec)
        
        # Display recommendations by priority
        for priority, recs in priority_groups.items():
            if recs:
                st.markdown(f"#### {priority}")
                
                for rec in recs:
                    icon = {"High Priority": "🚨", "Medium Priority": "⚠️", "Low Priority": "💡"}[priority]
                    
                    with st.expander(f"{icon} {rec['title']}"):
                        st.write(f"**VPC**: {rec.get('vpc_id', 'N/A')}")
                        st.write(f"**Issue**: {rec.get('description', 'N/A')}")
                        st.write(f"**Recommendation**: {rec.get('recommendation', 'N/A')}")
                        
                        if rec.get('estimated_savings'):
                            st.write(f"**Potential Savings**: ${rec['estimated_savings']:.2f}/month")
                        
                        if rec.get('implementation_steps'):
                            st.markdown("**Implementation Steps:**")
                            for step in rec['implementation_steps']:
                                st.write(f"- {step}")

    def generate_vpc_recommendations(self, vpc_id, vpc_data, cost_analysis):
        """Genera raccomandazioni specifiche per VPC"""
        recommendations = []
        
        # Check for default VPC usage
        vpc_info = vpc_data.get("vpc_info", {})
        if vpc_info.get("IsDefault"):
            recommendations.append({
                "title": "Migrate from Default VPC",
                "vpc_id": vpc_id,
                "priority": "High Priority",
                "description": "Using default VPC is not recommended for production workloads",
                "recommendation": "Create dedicated VPC with proper network segmentation",
                "implementation_steps": [
                    "Design new VPC with appropriate CIDR blocks",
                    "Create public and private subnets across multiple AZs", 
                    "Set up NAT Gateway for private subnet internet access",
                    "Migrate resources with proper testing"
                ]
            })
        
        # Check for single AZ deployment
        availability_zones = vpc_data.get("availability_zones", [])
        if len(availability_zones) == 1:
            recommendations.append({
                "title": "Implement Multi-AZ Deployment",
                "vpc_id": vpc_id,
                "priority": "High Priority",
                "description": f"VPC is deployed in single AZ: {availability_zones[0]}",
                "recommendation": "Distribute resources across multiple AZs for high availability",
                "implementation_steps": [
                    "Create subnets in at least 2 additional AZs",
                    "Deploy applications across multiple AZs",
                    "Configure load balancers for AZ distribution",
                    "Test failover scenarios"
                ]
            })
        
        # Check for too many NAT Gateways
        nat_gateways = vpc_data.get("nat_gateways", [])
        active_nat_gws = [ng for ng in nat_gateways if ng.get("State") == "available"]
        
        if len(active_nat_gws) > 2:
            potential_savings = (len(active_nat_gws) - 1) * 45.36
            recommendations.append({
                "title": "Optimize NAT Gateway Usage",
                "vpc_id": vpc_id,
                "priority": "Medium Priority",
                "description": f"VPC has {len(active_nat_gws)} NAT Gateways",
                "recommendation": "Consider consolidating NAT Gateways to reduce costs",
                "estimated_savings": potential_savings,
                "implementation_steps": [
                    "Analyze traffic patterns for each NAT Gateway",
                    "Identify NAT Gateways with low utilization",
                    "Plan route table updates for consolidation",
                    "Implement changes during maintenance window"
                ]
            })
        
        # Check for missing private subnets
        public_subnets = len(vpc_data.get("public_subnets", []))
        private_subnets = len(vpc_data.get("private_subnets", []))
        
        if public_subnets > 0 and private_subnets == 0:
            recommendations.append({
                "title": "Implement Network Segmentation",
                "vpc_id": vpc_id,
                "priority": "High Priority",
                "description": "VPC only has public subnets - missing private network tier",
                "recommendation": "Create private subnets for backend services",
                "implementation_steps": [
                    "Design private subnet CIDR blocks",
                    "Create private subnets in each AZ",
                    "Set up NAT Gateway for internet access",
                    "Move non-public services to private subnets"
                ]
            })
        
        # Check CIDR utilization
        cidr_util = vpc_data.get("cidr_utilization", {})
        if cidr_util and not cidr_util.get("error"):
            utilization = cidr_util.get("utilization_percent", 0)
            
            if utilization < 10:
                recommendations.append({
                    "title": "Optimize CIDR Block Size",
                    "vpc_id": vpc_id,
                    "priority": "Low Priority",
                    "description": f"Very low CIDR utilization: {utilization:.1f}%",
                    "recommendation": "Consider smaller CIDR blocks for future VPCs",
                    "implementation_steps": [
                        "Document current IP requirements",
                        "Plan for future growth",
                        "Use smaller CIDR blocks for new VPCs",
                        "Implement IP Address Management (IPAM)"
                    ]
                })
        
        return recommendations

    def generate_nat_optimization_script(self, optimization):
        """Genera script di ottimizzazione NAT Gateway"""
        vpc_id = optimization.get("vpc_id", "")
        savings = optimization.get("potential_monthly_savings", 0)
        
        script = f"""#!/bin/bash
# NAT Gateway Optimization Script for VPC {vpc_id}
# Potential monthly savings: ${savings:.2f}

set -e

echo "🔍 Analyzing NAT Gateways in VPC {vpc_id}..."

# List current NAT Gateways
echo "Current NAT Gateways:"
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values={vpc_id}" \\
    --query 'NatGateways[?State==`available`].[NatGatewayId,SubnetId,State]' \\
    --output table

# Check route tables using NAT Gateways
echo "Checking route table dependencies..."
aws ec2 describe-route-tables --filters "Name=vpc-id,Values={vpc_id}" \\
    --query 'RouteTables[?Routes[?starts_with(GatewayId, `nat-`)]].[RouteTableId,Routes[?starts_with(GatewayId, `nat-`)].GatewayId]' \\
    --output table

echo "⚠️  WARNING: Manual verification required!"
echo "1. Ensure no critical traffic depends on redundant NAT Gateways"
echo "2. Update route tables to point to consolidated NAT Gateway"
echo "3. Test connectivity after changes"
echo ""
echo "Example commands (REVIEW BEFORE RUNNING):"
echo "# aws ec2 delete-nat-gateway --nat-gateway-id nat-xxxxxxxxx"
echo "# aws ec2 replace-route --route-table-id rtb-xxxxxxxxx --destination-cidr-block 0.0.0.0/0 --nat-gateway-id nat-yyyyyyyyy"
"""
        
        return script
    
    def render_sidebar(self):
        """Render sidebar con controlli"""
        st.sidebar.title("🔧 Controls")
        
        # Refresh button
        if st.sidebar.button("🔄 Refresh Data", type="primary"):
            st.rerun()
        
        # Quick actions
        st.sidebar.subheader("⚡ Quick Actions")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("📡 Fetch", help="Fetch AWS data"):
                with st.spinner("Fetching..."):
                    try:
                        # Ottieni path assoluto allo script main.py
                        main_path = str(Path(__file__).parent.parent / "main.py")
                        
                        # Esegui il comando nella directory corretta
                        result = subprocess.run(
                            ["python", main_path, "--fetch-only"],
                            capture_output=True, text=True,
                            cwd=str(Path(__file__).parent.parent)
                        )
                        
                        if result.returncode == 0:
                            st.success("✅ Fetch completed")
                            st.rerun()
                        else:
                            st.error(f"❌ Fetch failed: {result.stderr}")
                            st.code(result.stderr)
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        with col2:
            if st.button("🔍 Audit", help="Run security audit"):
                with st.spinner("Auditing..."):
                    try:
                        # Ottieni path assoluto allo script main.py
                        main_path = str(Path(__file__).parent.parent / "main.py")
                        
                        # Esegui il comando nella directory corretta
                        result = subprocess.run(
                            ["python", main_path, "--audit-only"],
                            capture_output=True, text=True,
                            cwd=str(Path(__file__).parent.parent)
                        )
                        
                        if result.returncode == 0:
                            st.success("✅ Audit completed")
                            st.rerun()
                        else:
                            st.error(f"❌ Audit failed: {result.stderr}")
                            st.code(result.stderr)
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        # VPC Actions
        self.render_vpc_sidebar_actions()
        
        # Data freshness
        data_files = ["ec2_raw.json", "sg_raw.json", "iam_raw.json"]
        oldest_file = None
        for filename in data_files:
            filepath = self.data_dir / filename
            if filepath.exists():
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if oldest_file is None or mtime < oldest_file:
                    oldest_file = mtime
        
        if oldest_file:
            age = datetime.now() - oldest_file
            if age.days > 0:
                st.sidebar.warning(f"⏰ Data age: {age.days} days old")
            elif age.seconds > 3600:
                st.sidebar.info(f"⏰ Data age: {age.seconds // 3600} hours old")
            else:
                st.sidebar.success(f"⏰ Data age: {age.seconds // 60} minutes old")

    def render_vpc_sidebar_actions(self):
        """Render azioni rapide VPC nella sidebar"""
        st.sidebar.subheader("🌐 VPC Actions")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("📡 VPC Fetch", help="Fetch VPC data"):
                with st.spinner("Fetching VPC data..."):
                    try:
                        main_path = str(Path(__file__).parent.parent / "main.py")
                        result = subprocess.run(
                            ["python", main_path, "--vpc-analysis"],
                            capture_output=True, text=True,
                            cwd=str(Path(__file__).parent.parent)
                        )
                        
                        if result.returncode == 0:
                            st.success("✅ VPC analysis completed")
                            st.rerun()
                        else:
                            st.error(f"❌ VPC analysis failed: {result.stderr}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        with col2:
            if st.button("💰 Cost Opt", help="VPC cost optimization"):
                with st.spinner("Analyzing costs..."):
                    try:
                        main_path = str(Path(__file__).parent.parent / "main.py")
                        result = subprocess.run(
                            ["python", main_path, "--network-optimization"],
                            capture_output=True, text=True,
                            cwd=str(Path(__file__).parent.parent)
                        )
                        
                        if result.returncode == 0:
                            st.success("✅ Cost analysis completed")
                            st.rerun()
                        else:
                            st.error(f"❌ Cost analysis failed: {result.stderr}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    def run(self):
        """Esegue il dashboard"""
        try:
            # Render sidebar
            self.render_sidebar()
            
            # Main content
            self.render_header()
            
            # Navigation tabs - AGGIORNATO con VPC
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🏠 Overview", 
                "🚨 Security", 
                "📦 Resources", 
                "🌐 Network & VPC",  # NUOVO TAB
                "💰 Cost Analysis"   # NUOVO TAB
            ])
            
            with tab1:
                self.render_metrics_overview()
                st.markdown("---")
                self.render_findings_charts()
            
            with tab2:
                self.render_critical_findings()
                st.markdown("---")
                self.render_vpc_security_analysis()  # Aggiunto
            
            with tab3:
                self.render_resource_inventory()
            
            with tab4:  # NUOVO TAB VPC
                self.render_vpc_overview()
                st.markdown("---")
                self.render_network_topology_advanced()
                st.markdown("---")
                self.render_network_recommendations()
            
            with tab5:  # NUOVO TAB COST
                self.render_vpc_cost_analysis()
                
        except Exception as e:
            st.error(f"❌ Errore dashboard: {e}")
            st.exception(e)


# Main execution
if __name__ == "__main__":
    dashboard = SecurityDashboard()
    dashboard.run()
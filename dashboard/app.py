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
    
    def run(self):
        """Esegue il dashboard"""
        try:
            # Render sidebar
            self.render_sidebar()
            
            # Main content
            self.render_header()
            
            # Navigation tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "🏠 Overview", 
                "🚨 Security", 
                "📦 Resources", 
                "🌐 Network"
            ])
            
            with tab1:
                self.render_metrics_overview()
                st.markdown("---")
                self.render_findings_charts()
            
            with tab2:
                self.render_critical_findings()
            
            with tab3:
                self.render_resource_inventory()
            
            with tab4:
                self.render_network_map()
                
        except Exception as e:
            st.error(f"❌ Errore dashboard: {e}")
            st.exception(e)


# Main execution
if __name__ == "__main__":
    dashboard = SecurityDashboard()
    dashboard.run()
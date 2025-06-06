# 🔒 AWS Infrastructure Security Auditor v2.1

> **Professional-grade AWS security auditing tool with interactive dashboard and comprehensive reporting**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![AWS](https://img.shields.io/badge/AWS-Compatible-orange.svg)](https://aws.amazon.com/)

## 🚀 Overview

AWS Infrastructure Security Auditor is a comprehensive security assessment tool that analyzes your AWS infrastructure for security vulnerabilities, misconfigurations, and compliance issues. It provides an interactive dashboard for visualization and generates detailed reports with actionable remediation steps.

### ✨ Key Features

- 🔍 **Multi-Service Security Audit**: EC2, VPC, S3, IAM, Security Groups
- 🌍 **Multi-Region Support**: Audit across multiple AWS regions simultaneously
- ⚡ **Async Performance**: High-speed parallel data fetching
- 📊 **Interactive Dashboard**: Real-time visualization with Streamlit
- 📋 **Detailed Reports**: JSON and Markdown formats with remediation steps
- 🎯 **Compliance Frameworks**: CIS, SOC2, PCI-DSS, ISO27001 mapping
- 🔧 **Extensible Rules**: Easy to add custom audit rules
- 💾 **Smart Caching**: Efficient data management and processing

### 🎯 What Gets Audited

| Service | Checks | Severity Levels |
|---------|--------|----------------|
| **EC2** | Public IPs, stopped instances, monitoring | 🔴 🟠 🟡 🔵 |
| **Security Groups** | Open ports, unused groups, critical exposures | 🔴 🟠 🟡 🔵 |
| **S3** | Public buckets, encryption, old buckets | 🔴 🟠 🟡 🔵 |
| **IAM** | Inactive users, admin roles, unused policies | 🔴 🟠 🟡 🔵 |
| **VPC** | Default VPCs, public subnets, unused resources | 🔴 🟠 🟡 🔵 |

## 🏗️ Quick Start

### Prerequisites

- **Python 3.8+**
- **AWS CLI configured** (`aws configure`)
- **Valid AWS credentials** with read permissions

### 1. Clone & Setup

```bash
git clone <repository-url>
cd aws-security-auditor
./setup.sh  # Automated setup script
```

Or manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup directories
make setup
```

### 2. Configure AWS

```bash
# Configure AWS credentials
aws configure

# Verify access
aws sts get-caller-identity
```

### 3. Run Your First Audit

```bash
# Full audit (recommended)
make audit

# Or step by step
make fetch    # Fetch AWS data
make analyze  # Run security analysis  
make dashboard # View results
```

## 📖 Usage Guide

### Command Line Interface

```bash
# Full audit with cleanup
python main.py

# Fetch data only
python main.py --fetch-only

# Audit existing data
python main.py --audit-only

# Quick audit (no fetch, no cleanup)
python main.py --quick

# Interactive dashboard
python main.py --dashboard

# Public dashboard (network accessible)
python main.py --dashboard --host 0.0.0.0
```

### Advanced Options

```bash
# Specific regions
python main.py --regions us-east-1,eu-west-1

# Specific services
python main.py --services ec2,s3,iam

# Custom configuration
python main.py --config custom-config.json

# Verbose output
python main.py --verbose

# Force execution despite warnings
python main.py --force
```

### Makefile Commands

```bash
make help           # Show all available commands
make install        # Install dependencies
make setup          # Setup environment and directories
make test           # Test current setup
make status         # Show system status

# Audit commands
make audit          # Full security audit
make fetch          # Fetch AWS data only
make analyze        # Analyze existing data
make quick          # Quick audit on existing data

# Dashboard
make dashboard      # Start dashboard (localhost)
make dashboard-public # Start public dashboard

# Region-specific audits
make audit-us-east-1     # Audit only us-east-1
make audit-eu-west-1     # Audit only eu-west-1
make audit-multi         # Audit multiple regions

# Service-specific audits
make audit-ec2      # Audit only EC2 resources
make audit-s3       # Audit only S3 resources
make audit-iam      # Audit only IAM resources

# Maintenance
make clean          # Clean cache and temporary files
make clean-data     # Clean data directory (CAREFUL!)
make clean-all      # Clean everything

# Monitoring
make monitor        # Monitor findings over time
make report         # Generate and show latest report
make summary        # Show quick summary

# Backup/restore
make backup         # Backup current data and reports
make restore BACKUP=filename # Restore from backup
```

## 📊 Dashboard Features

The interactive Streamlit dashboard provides:

### 🏠 Overview Tab
- 📈 **Metrics Overview**: Critical, High, Medium, Low findings
- 📊 **Charts**: Distribution by severity and resource type
- ⏰ **Scan Information**: Last scan time and freshness indicators

### 🚨 Security Tab
- 🔴 **Critical Findings**: Immediate action required
- 🟠 **High Priority**: Important security issues
- 📋 **Detailed Findings**: Expandable cards with remediation steps
- 💡 **Actionable Recommendations**: Copy-paste AWS CLI commands

### 📦 Resources Tab
- 🖥️ **EC2 Inventory**: Running/stopped instances with details
- 🛡️ **Security Groups**: Rules analysis and usage tracking
- 🗂️ **S3 Buckets**: Public access and encryption status
- 👤 **IAM Resources**: Users, roles, and policies analysis

### 🌐 Network Tab
- 🗺️ **Interactive Network Map**: Visual topology (requires pyvis)
- 📋 **Connection Table**: Fallback tabular view
- 🔗 **Resource Relationships**: Instance-to-SG mappings

### ⚡ Quick Actions
- 🔄 **Refresh Data**: Re-run analysis
- 📡 **Fetch New Data**: Update from AWS
- 🔍 **Re-audit**: Analyze current data

## 📁 Project Structure

```
aws-security-auditor/
├── 📄 main.py                 # Main application entry point
├── 📁 config/                 # Configuration and audit rules
│   ├── settings.py            # Global configuration management
│   └── audit_rules.py         # Security audit rule definitions
├── 📁 utils/                  # Utility modules
│   ├── async_fetcher.py       # Async AWS data fetching
│   ├── cache_manager.py       # Smart caching system
│   └── data_processor.py      # Raw data processing
├── 📁 audit/                  # Audit engine and auditors
│   ├── audit_engine.py        # Main audit orchestration
│   ├── base_auditor.py        # Base auditor class
│   ├── ec2_auditor.py         # EC2-specific security checks
│   └── security_group_auditor.py # Security Group analysis
├── 📁 dashboard/              # Interactive dashboard
│   └── app.py                 # Streamlit dashboard application
├── 📁 data/                   # Raw and processed data (auto-created)
├── 📁 reports/                # Generated audit reports (auto-created)
├── 📁 .cache/                 # Performance cache (auto-created)
├── 📄 requirements.txt        # Python dependencies
├── 📄 Makefile               # Automation commands
├── 📄 setup.sh               # Setup script
├── 📄 .env.example           # Environment configuration template
└── 📄 .gitignore             # Git ignore rules
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# AWS Configuration
AWS_AUDIT_REGIONS=us-east-1,eu-west-1
AWS_PROFILE=default
AWS_AUDIT_MAX_WORKERS=10
AWS_AUDIT_CACHE_TTL=3600

# Notification Settings (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Dashboard Settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Configuration File

Create `config.json` for advanced configuration:

```json
{
  "regions": ["us-east-1", "eu-west-1"],
  "profile": "audit-profile",
  "max_workers": 15,
  "cache_ttl": 7200,
  "services": {
    "ec2": true,
    "eni": true,
    "sg": true,
    "vpc": true,
    "subnet": true,
    "igw": true,
    "route_table": true,
    "s3": true,
    "iam": true,
    "rds": false,
    "lambda": false
  },
  "audit_rules": {
    "sg_open_ports": [22, 3389, 3306, 5432],
    "sg_allow_all_cidr": true,
    "s3_public_access": true,
    "iam_unused_roles": true,
    "iam_old_access_keys": 90,
    "ec2_public_ips": true,
    "vpc_default_usage": true
  },
  "notifications": {
    "enabled": false,
    "slack_webhook": null,
    "critical_only": true
  }
}
```

## 🔍 Understanding Audit Results

### Severity Levels

| Level | Icon | Description | Action Required |
|-------|------|-------------|-----------------|
| **Critical** | 🔴 | Immediate security risk | **Fix immediately** |
| **High** | 🟠 | Significant security concern | **Fix within 24h** |
| **Medium** | 🟡 | Security improvement needed | **Fix within 1 week** |
| **Low** | 🔵 | Best practice recommendation | **Consider fixing** |

### Common Findings

#### 🔴 Critical Issues
- **Open SSH/RDP to Internet** (0.0.0.0/0)
- **Database ports exposed publicly**
- **S3 buckets with public write access**
- **Root access keys in use**

#### 🟠 High Priority Issues
- **Security Groups with broad access**
- **Unencrypted S3 buckets**
- **IAM users without MFA**
- **Default VPC usage**

#### 🟡 Medium Issues
- **EC2 instances with public IPs**
- **Overprivileged IAM roles**
- **Unused security groups**
- **Old CloudTrail logs**

#### 🔵 Low Priority Issues
- **Stopped instances (cost optimization)**
- **Monitoring not enabled**
- **Inactive IAM users**
- **Old S3 buckets**

### Report Formats

#### JSON Report (`reports/security_findings.json`)
```json
{
  "metadata": {
    "scan_time": "2024-12-19T10:30:00",
    "region": "us-east-1",
    "total_findings": 35
  },
  "findings": [
    {
      "resource_id": "sg-12345678",
      "resource_type": "SecurityGroup",
      "rule_name": "Porte sensibili esposte",
      "severity": "critical",
      "description": "Security Group permette SSH da 0.0.0.0/0",
      "recommendation": "Limitare accesso SSH a IP specifici",
      "remediation": "aws ec2 revoke-security-group-ingress...",
      "compliance_frameworks": ["CIS", "SOC2"]
    }
  ]
}
```

#### Markdown Report (`reports/security_audit_report.md`)
- Executive summary with counts
- Findings organized by severity
- Detailed remediation steps
- Compliance framework mapping

## 🛠️ Extending the Auditor

### Adding Custom Audit Rules

1. **Define the rule** in `config/audit_rules.py`:

```python
"CUSTOM001": AuditRule(
    rule_id="CUSTOM001",
    name="Custom Security Check",
    description="Checks for custom security requirement",
    severity=Severity.HIGH,
    service="ec2",
    metadata={"custom_param": "value"}
)
```

2. **Implement the check** in appropriate auditor:

```python
def _check_custom_requirement(self, resource):
    rule = get_rule_by_id("CUSTOM001")
    if not rule or not rule.enabled:
        return
    
    # Your custom logic here
    if custom_condition_met:
        self.add_finding(Finding(
            resource_id=resource["Id"],
            resource_type="EC2Instance",
            rule_id=rule.rule_id,
            rule_name=rule.name,
            # ... other fields
        ))
```

### Creating New Auditors

1. **Inherit from BaseAuditor**:

```python
from audit.base_auditor import BaseAuditor, Finding

class CustomAuditor(BaseAuditor):
    def audit(self, data: Dict[str, Any]) -> List[Finding]:
        self.clear_findings()
        # Implement your audit logic
        return self.findings
```

2. **Register in AuditEngine**:

```python
# In audit_engine.py
self.auditors["custom"] = CustomAuditor(region)
```

## 🚨 Troubleshooting

### Common Issues

#### AWS Credentials Not Found
```bash
# Solution
aws configure
# or
export AWS_PROFILE=your-profile
```

#### Permission Denied Errors
```bash
# Check current identity
aws sts get-caller-identity

# Required permissions: 
# - ec2:Describe*
# - s3:ListAllMyBuckets, s3:GetBucketLocation, s3:GetBucketAcl
# - iam:List*, iam:Get*
```

#### Large Data Sets Timeout
```bash
# Reduce scope
python main.py --regions us-east-1 --services ec2,sg

# Or increase timeout in config
AWS_AUDIT_CACHE_TTL=7200
```

#### Dashboard Won't Start
```bash
# Check if port is available
lsof -i :8501

# Try different port
python main.py --dashboard --port 8502

# Install missing dependencies
pip install streamlit plotly pyvis
```

### Debug Mode

```bash
# Verbose output
python main.py --verbose

# Check system status
make status

# Test individual components
make test
```

### Performance Optimization

```bash
# Use fewer workers for slower connections
AWS_AUDIT_MAX_WORKERS=5

# Enable smart caching
AWS_AUDIT_CACHE_TTL=3600

# Limit scope for large accounts
python main.py --regions us-east-1 --services ec2,sg,s3
```

## 📈 Monitoring & Automation

### Continuous Monitoring

```bash
# Daily audit via cron
0 6 * * * cd /path/to/auditor && source venv/bin/activate && make audit

# Weekly deep audit
0 2 * * 0 cd /path/to/auditor && source venv/bin/activate && python main.py --force

# Monitoring script
make monitor  # Shows trend analysis
```

### CI/CD Integration

```yaml
# GitHub Actions example
name: AWS Security Audit
on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Configure AWS
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          make ci-test
      - name: Run Audit
        run: |
          python main.py --audit-only
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: audit-results
          path: reports/
```

### Notifications

Configure Slack notifications in `.env`:

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

The auditor will send alerts for critical findings.

## 🤝 Contributing

We welcome contributions! Please:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/aws-security-auditor.git
cd aws-security-auditor

# Setup development environment
make setup
pip install -r requirements.txt

# Install development tools
pip install pytest black flake8 mypy

# Run tests
make dev-test

# Code formatting
make dev-format

# Linting
make dev-lint
```

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **Documentation**: Include docstrings for all functions
- **Testing**: Add tests for new audit rules
- **Commits**: Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: [Wiki](https://github.com/your-org/aws-security-auditor/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/aws-security-auditor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/aws-security-auditor/discussions)
- **Releases**: [GitHub Releases](https://github.com/your-org/aws-security-auditor/releases)

## 🙏 Acknowledgments

- **AWS SDK**: Built with boto3 and aioboto3
- **Dashboard**: Powered by Streamlit and Plotly
- **Security Rules**: Based on CIS AWS Benchmarks
- **Community**: Thanks to all contributors and users

---

## 🆘 Support

- 📖 **Documentation**: Check the wiki for detailed guides
- 🐛 **Bug Reports**: Open an issue with reproduction steps
- 💡 **Feature Requests**: Discuss in GitHub Discussions
- 📧 **Contact**: [your-email@example.com](mailto:your-email@example.com)

---

**⭐ If this tool helps secure your AWS infrastructure, please star the repository!**
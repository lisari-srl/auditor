# EC2 Audit Report

## Running Instances
- Database (MySQL) - Mr Burns (i-09e13d3e46fa2bad0), Type: m5.large, Subnet: subnet-abdd89e2, VPC: vpc-acd677ca, Public IP: None, Private IP: 172.31.3.24
- Broker (Redis) - Kent Brockman (i-0e53cd2fa2c03b01c), Type: r5.large, Subnet: subnet-abdd89e2, VPC: vpc-acd677ca, Public IP: None, Private IP: 172.31.1.82
- Engine (NodeJS) - Maggie (i-0db4f7e43b3237e34), Type: m5.large, Subnet: subnet-abdd89e2, VPC: vpc-acd677ca, Public IP: None, Private IP: 172.31.2.249
- API Gateway (Swift) - Winchester (i-0a743f992f55b449b), Type: r7g.medium, Subnet: subnet-abdd89e2, VPC: vpc-acd677ca, Public IP: None, Private IP: 172.31.15.30
- Game Backend (Swift) - Bart (i-0d3719ffa7eb6a38e), Type: c7g.xlarge, Subnet: subnet-5c8eb515, VPC: vpc-acd677ca, Public IP: 13.220.55.29, Private IP: 172.31.81.63

## Stopped Instances
- Bastion (Windows) - Skinner (i-0b0edbabd4b9ca128), Type: t2.nano, Subnet: subnet-5c8eb515, VPC: vpc-acd677ca
- Management (Windows) - Marge (i-0a0d3bf9ab4745e77), Type: t3.medium, Subnet: subnet-5c8eb515, VPC: vpc-acd677ca

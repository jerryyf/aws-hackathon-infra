# Data Model: AWS Infrastructure Entities

## VPC (Virtual Private Cloud)
- **CIDR**: 10.0.0.0/16
- **Region**: us-east-1
- **Attributes**: Name, CIDR, DNS settings, tenancy
- **Relationships**: Contains subnets, internet gateway, NAT gateways, VPC endpoints
- **Validation**: CIDR valid, no overlap with existing VPCs

## Public Subnets
- **CIDR**: 10.0.1.0/24 (AZ-1), 10.0.2.0/24 (AZ-2)
- **Type**: Public
- **Attributes**: AZ, CIDR, route table
- **Relationships**: Belongs to VPC, has NAT gateway, internet gateway access
- **Validation**: Correct AZ, public routing

## Private Application Subnets
- **CIDR**: 10.0.11.0/24 (AZ-1), 10.0.12.0/24 (AZ-2)
- **Type**: Private
- **Attributes**: AZ, CIDR, route table
- **Relationships**: Belongs to VPC, routes through NAT gateway
- **Validation**: No direct internet access, NAT routing

## Private AgentCore Subnets
- **CIDR**: 10.0.21.0/24 (AZ-1), 10.0.22.0/24 (AZ-2)
- **Type**: Private
- **Attributes**: AZ, CIDR, route table
- **Relationships**: Belongs to VPC, routes through NAT gateway
- **Validation**: Isolated for agent runtime, VPC endpoint access

## Private Data Subnets
- **CIDR**: 10.0.31.0/24 (AZ-1), 10.0.32.0/24 (AZ-2)
- **Type**: Private
- **Attributes**: AZ, CIDR, route table
- **Relationships**: Belongs to VPC, routes through NAT gateway
- **Validation**: Database and search service isolation

## Application Load Balancer
- **Type**: Public ALB
- **Attributes**: DNS name, security groups, target groups, listeners
- **Relationships**: Spans public subnets, routes to backend services
- **Validation**: HTTPS enabled, WAF attached, health checks configured

## RDS PostgreSQL Cluster
- **Engine**: PostgreSQL
- **Attributes**: Instance class, storage, multi-AZ, backup settings
- **Relationships**: Uses data subnets, accessed via RDS proxy
- **Validation**: Multi-AZ enabled, encryption at rest

## OpenSearch Cluster
- **Type**: Managed OpenSearch
- **Attributes**: Instance type, node count, storage, encryption
- **Relationships**: Uses data subnets
- **Validation**: Multi-AZ, encryption enabled

## S3 Buckets
- **Types**: Knowledge Base, Logs, BDA
- **Attributes**: Name, region, versioning, encryption, lifecycle
- **Relationships**: VPC endpoint access
- **Validation**: Encryption enabled, versioning on

## ECR Repositories
- **Attributes**: Name, image scanning, tag immutability
- **Relationships**: VPC endpoint access
- **Validation**: Scanning enabled, immutable tags

## Security Groups
- **Types**: ALB, Backend, Database, AgentCore
- **Attributes**: Name, VPC, ingress/egress rules
- **Relationships**: Applied to resources
- **Validation**: Least privilege rules

## VPC Endpoints
- **Types**: Gateway (S3), Interface (Bedrock, Secrets, SSM, ECR, CloudWatch)
- **Attributes**: Service name, VPC, subnets, security groups
- **Relationships**: Enables private AWS service access
- **Validation**: Correct service, private DNS enabled

## CloudWatch Resources
- **Types**: Log groups, alarms, dashboards
- **Attributes**: Names, metrics, thresholds
- **Relationships**: Monitor infrastructure resources
- **Validation**: Appropriate thresholds set

## Route 53 Resources
- **Types**: Hosted zone, records
- **Attributes**: Domain name, record types, targets
- **Relationships**: Points to ALB
- **Validation**: Valid DNS configuration
# Network Stack Sanity Checks

Timestamp: 2025-10-09 00:30:00 UTC
Stack: NetworkStack

Checklist
---------
- CloudFormation status: NetworkStack = CREATE_COMPLETE
- VPC: correct CIDR 10.0.0.0/16, two AZs
- Subnets: Public/PrivateApp/PrivateAgent/PrivateData per AZ
- NAT Gateways: present in public subnets
- ALB: DNS name present, HTTPS listener, SG rules allow 443
- Internal ALB: internal scheme, SG restricts to VPC CIDR
- WAF: WebACL associated to public ALB
- Route53/ACM: if domain was provided, check hosted zone and ACM validation CNAME
- VPCEndpoints: Bedrock status = Available, other interface endpoints = Available

Commands
--------
- Show VPC ID:
  ```bash
  aws cloudformation describe-stacks --stack-name NetworkStack --query "Stacks[0].Outputs[?OutputKey=='VpcId'].OutputValue" --output text
  ```

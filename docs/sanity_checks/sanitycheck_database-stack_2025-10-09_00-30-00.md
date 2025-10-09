# Database Stack Sanity Checks

Timestamp: 2025-10-09 00:30:00 UTC
Stack: DatabaseStack

Checklist
---------
- CloudFormation: DatabaseStack = CREATE_COMPLETE
- RDS cluster: status = available
- RDS Proxy: status = available; endpoint present
- Secrets Manager: secret `hackathon/rds/credentials` exists
- OpenSearch: domain status = Active; data node count = 2
- VPC/Subnets: DB sits in `PrivateData` subnets

Commands
--------
- Get RDS Proxy endpoint from stack outputs:
  ```bash
  aws cloudformation describe-stacks --stack-name DatabaseStack --query "Stacks[0].Outputs[?OutputKey=='RdsEndpoint'].OutputValue" --output text
  ```

# Security Stack Sanity Checks

Timestamp: 2025-10-09 00:30:00 UTC
Stack: SecurityStack

Checklist
---------
- CloudFormation: SecurityStack = CREATE_COMPLETE
- SSM Parameters: `/hackathon/app/config`, `/hackathon/endpoints` exist
- Cognito: user pool `hackathon-users` exists and sign-in aliases are configured

Commands
--------
- Get SSM parameter values:
  ```bash
  aws ssm get-parameter --name /hackathon/app/config --query Parameter.Value --output text
  ```

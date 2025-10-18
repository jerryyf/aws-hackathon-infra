# Security Stack Sanity Checks

Timestamp: 2025-10-09 00:30:00 UTC
Stack: SecurityStack

Checklist
---------
- CloudFormation: SecurityStack = CREATE_COMPLETE
- SSM Parameters: `/bidopsai/app/config`, `/bidopsai/endpoints` exist
- Cognito: user pool `bidopsai-users` exists and sign-in aliases are configured

Commands
--------
- Get SSM parameter values:
  ```bash
  aws ssm get-parameter --name /bidopsai/app/config --query Parameter.Value --output text
  ```

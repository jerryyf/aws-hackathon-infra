# Database Stack Deployment Report

Timestamp: 2025-10-09 00:30:00 UTC
Stack: DatabaseStack

Key resources
-------------
- RDS: Aurora PostgreSQL (serverless v2)
  - Writer and reader serverless instances
  - Default DB: hackathon
- RDS Proxy (DatabaseProxy)
- SecretsManager secret for DB credentials: `hackathon/rds/credentials`
- OpenSearch domain (2 data nodes for 2-AZ deployment)

Important file/artifact
-----------------------
- Synth template: `cdk/cdk.out/DatabaseStack.template.json`

Notes & troubleshooting history
-------------------------------
- DatabaseStack initially failed due to missing PrivateData subnet export; fixed by referencing NetworkStack VPC private subnets directly.
- OpenSearch failed validation because it used 3 data nodes for a 2-AZ deployment; corrected to 2 data nodes.
- RDS Proxy failed due to missing RDS service-linked role. The CDK now conditionally creates a `AWS::IAM::ServiceLinkedRole` resource when needed and uses a deterministic custom suffix to avoid name collisions in accounts where the default service-linked role name is taken.

Sanity checks (Console)
-----------------------
- CloudFormation: `DatabaseStack` status = `CREATE_COMPLETE` / `UPDATE_COMPLETE`.
- RDS console: cluster status = `available`, instances healthy.
- RDS Proxy console: proxy status = `available`, endpoint present.
- Secrets Manager: secret `hackathon/rds/credentials` exists and is accessible.
- OpenSearch console: domain status = `Active`, data node count = 2, zone awareness works across two AZs.

CLI quick checks
----------------
- Check RDS proxy endpoint exported by stack outputs.

Next steps
----------
- Verify database connectivity from compute resources within the VPC.
- Confirm backups and snapshots (7-day retention configured).
- If RDS Proxy role creation fails due to IAM permission, ask the admin to create the service-linked role or grant iam:CreateServiceLinkedRole to the deploy principal.

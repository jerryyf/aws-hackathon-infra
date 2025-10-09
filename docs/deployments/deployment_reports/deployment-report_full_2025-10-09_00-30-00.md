# Full Deployment Report — Hackathon Infra

Timestamp: 2025-10-09 00:30:00 UTC
Repository: aws-hackathon-infra (branch: 002-create-python-application)
Target: Full CDK app (Network, Database, Compute, Storage, Security, Monitoring)

Overview
--------
This document summarizes the deployment and validation status for the full CDK application.

Artifacts
---------
- CDK synth output directory: `cdk/cdk.out`
- Network stack template: `cdk/cdk.out/NetworkStack.template.json`
- Database stack template: `cdk/cdk.out/DatabaseStack.template.json`
- Other stacks templates are available in `cdk/cdk.out`.
- Per-stack reports live under `docs/` with timestamps.

High-level status
-----------------
- NetworkStack: synthesized and deployed (VPC, subnets, ALBs, VPC endpoints, ACM handling).
- DatabaseStack: synthesized and deployed (RDS Aurora PostgreSQL serverless v2, RDS Proxy, OpenSearch domain). Resolved issues: OpenSearch node count adjusted to 2 for 2-AZ deployment; RDS service-linked role handling added with collision-safe creation.
- ComputeStack: ECS cluster and Fargate task definition created.
- StorageStack: S3 buckets and ECR repository created.
- SecurityStack: SSM params and Cognito user pool created.
- MonitoringStack: CloudWatch log groups, alarms, and CloudTrail created.

Key changes made during troubleshooting
-------------------------------------
- HostedZone/ACM guarding: CDK code now only performs hosted zone lookups and DNS-validated ACM certificate creation when a public domain is provided and the CDK environment (account/region) is configured.
- Bedrock VPCEndpoint service name: resolved to a concrete region-specific string at deploy time to avoid invalid service-name errors.
- DatabaseStack: now references NetworkStack VPC subnets directly to avoid CFN Export timing races; falls back to import_value when necessary.
- OpenSearch: data node count set to an even number (2) for a 2-AZ deployment to avoid service validation errors.
- RDS service-linked role: CDK now attempts to detect existing roles and creates a service-linked role with a deterministic suffix if there is a name collision.

Where to find logs and templates
--------------------------------
- Synthesized templates: `cdk/cdk.out/`
- CloudFormation events: AWS Console > CloudFormation > [StackName] > Events
- Service logs: CloudWatch Log Groups (names: `/hackathon/app`, `/hackathon/alb`)

Recommendations & next steps
---------------------------
- Verify in AWS Console the following per-stack items (use the per-stack sanity-check docs in `docs/`): Network, Database, Compute, Storage, Security, Monitoring.
- Confirm ACM certificate status (ISSUED) if using a public domain.
- Confirm RDS Proxy and OpenSearch domain are healthy and available.

Appendix
--------
Per-stack reports and sanity checks are provided alongside this document in `docs/`.

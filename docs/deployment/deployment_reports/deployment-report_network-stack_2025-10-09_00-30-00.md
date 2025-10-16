# Network Stack Deployment Report

Timestamp: 2025-10-09 00:30:00 UTC

Repository: aws-hackathon-infra (branch: 002-create-python-application)
Target stack: NetworkStack

Summary
-------
This report documents the NetworkStack synthesis and deployment investigation performed on 2025-10-09 UTC. It captures what was synthesized, key resources, notable fixes applied to the CDK codebase, and recommended next steps for live validation.

Artifacts
---------
- CDK synth output (template): `cdk/cdk.out/NetworkStack.template.json`
- Relevant module files examined/edited:
  - `cdk/stacks/network_stack.py`
  - `cdk/app.py`
  - `docs/sanitycheck_network_cdk.md`

Synthesis result
----------------
`cdk synth` completed successfully. A CloudFormation template was generated at:

`cdk/cdk.out/NetworkStack.template.json`

Key template resources (high level)
----------------------------------
- VPC: `Vpc8378EB38` (10.0.0.0/16)
- Subnets:
  - Public: `VpcPublicSubnet1Subnet5C2D37C4`, `VpcPublicSubnet2Subnet691E08A3` (10.0.0.0/24, 10.0.1.0/24)
  - PrivateApp: `VpcPrivateAppSubnet1SubnetDB32FF69`, `VpcPrivateAppSubnet2Subnet2B6BEA34`
  - PrivateAgent: `VpcPrivateAgentSubnet1SubnetA030A312`, `VpcPrivateAgentSubnet2Subnet335A65CF`
  - PrivateData: `VpcPrivateDataSubnet1Subnet588C411B`, `VpcPrivateDataSubnet2SubnetE20E2EF3`
- NAT Gateways: created in each public subnet
- VPC Endpoints:
  - S3 (Gateway): `VpcS3Endpoint4A3DE4B5`
  - Bedrock (Interface): `VpcBedrockEndpoint67430A7D` (ServiceName in template: `com.amazonaws.us-east-1.bedrock-runtime`)
  - SecretsManager, SSM, ECR (api/dkr), CloudWatch Logs (Interface endpoints)
- Load Balancers:
  - Public ALB: logical id `Alb` (internet-facing)
  - Internal ALB: logical id `InternalAlb` (internal)
- WAFv2 WebACL: `WafAcl` associated with the public ALB
- ACM Certificate in template: `Certificate4E7ABB08` (Domain: `bidopsai.com`) — created because a hosted zone was discovered in the environment used for synth

Notable fixes applied
---------------------
- Avoid creating public ACM certs for non-public domains (e.g., `.local`): CDK code was changed to accept an optional `domain_name` and only perform `HostedZone.from_lookup` + DNS-validated `acm.Certificate` when a public domain is provided and CDK env/account/region are available.
- Bedrock VPCEndpoint `ServiceName` resolved to a concrete region-specific value (`com.amazonaws.<region>.bedrock-runtime`) at deploy-time instead of a literal substitution that caused CloudFormation validation errors.
- CDK context lookups (Route53) were gated by checking for presence of `CDK_DEFAULT_ACCOUNT` to avoid test/synth failures where env is not set.
- Small test/synth fixes: absolute imports for `cdk.stacks.*`, deterministic availability zones, and security group listener adjustments (public ALB accepts HTTPS only as expected by tests).

Template fragments (where to look)
----------------------------------
- Bedrock endpoint service name in the synthesized template: `Resources -> VpcBedrockEndpoint67430A7D -> Properties -> ServiceName` shows `com.amazonaws.us-east-1.bedrock-runtime`.
- ACM certificate resource: `Resources -> Certificate4E7ABB08` and `Outputs -> CertificateArn` (value references the created certificate resource).

Current issues and notes
------------------------
- If your original deployment used a `.local` domain (e.g., `hackathon.local`), public ACM cannot issue certificates for non-public TLDs and DNS validation will fail. Use a public domain or skip creating public ACM cert for local development (the code now skips it).
- Hosted zone discovery via AWS occurs only when `CDK_DEFAULT_ACCOUNT` and region are present; otherwise you must pass `--context domain_name=<yourdomain>` when running CDK synth/deploy if you want a certificate to be created.
- Live validation (ACM certificate issuance, VPCEndpoint availability) requires `cdk deploy` in an AWS account with Route53 hosted zone control and appropriate permissions.

How to validate in console (short)
----------------------------------
- ACM console: Check Certificate ARN (`Certificate4E7ABB08`) status (ISSUED / PENDING_VALIDATION / FAILED). If PENDING_VALIDATION, check Route53 DNS CNAME records for domain validation.
- Route 53: Confirm hosted zone ID `Z042050615UULZLF8XUAT` (if this is your zone) and that the validation CNAME exists.
- VPC console: Validate subnets, route tables, NAT Gateways, and VPC endpoints; check Bedrock endpoint status is `Available` and service name is `com.amazonaws.<region>.bedrock-runtime`.
- ELB console: Confirm ALB DNS name and listeners (HTTPS) and that the WAF is associated.

Next steps / Recommendations
----------------------------
1. If you want an ACM cert for production, ensure you own the public domain and pass it via CDK context:

   cdk deploy --context domain_name=example.com

   or set env variable DOMAIN_NAME=example.com before running the app.

2. Run `cdk deploy` with AWS credentials and verify the ACM record(s) in Route53 are created.
3. If you want me to run exact template fragment extraction and paste the resource blocks into this report, tell me which ones (Certificate, Bedrock endpoint, ALB), and I will add them.

Appendix: commands used
-----------------------
- Synthesize: `PYTHONPATH=. cdk synth` (from `cdk/` dir)
- Tests run (targeted): `PYTHONPATH=. pytest tests/unit/test_cdk_synth.py -q`

Report authoring notes
----------------------
- Generated by the local development workflow on 2025-10-09 00:30:00 UTC.
- File saved as `docs/deployment-report_network-stack_2025-10-09_00-30-00.md`.

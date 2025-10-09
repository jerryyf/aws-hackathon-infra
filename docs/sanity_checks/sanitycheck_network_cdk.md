# Network Stack Sanity Check (CDK)

Use this checklist after deploying the `NetworkStack` to verify the core networking resources are created and healthy.

1) CloudFormation

- Go to CloudFormation → Stacks → select `NetworkStack`.
- Confirm Stack Status = CREATE_COMPLETE (or UPDATE_COMPLETE).
- Open the Resources and Outputs tabs and note values: `VpcId`, `PublicSubnetIds`, `PrivateAppSubnetIds`, `PrivateAgentSubnetIds`, `PrivateDataSubnetIds`, `AlbDnsName`, `InternalAlbDnsName`, `HostedZoneId`, `CertificateArn`.

2) VPC & Subnets

- Console: VPC → Your VPCs → find the VPC by `VpcId`.
- Check CIDR is `10.0.0.0/16` and subnets exist in the configured AZs.
- Console: VPC → Subnets — verify Public and Private subnet tiers and that subnets are placed across at least 2 AZs.

3) Route tables & VPC Endpoints

- Console: VPC → Route Tables — public subnets should route 0.0.0.0/0 to an Internet Gateway.
- Console: VPC → Endpoints — verify there is a Gateway endpoint for S3 and Interface endpoints for Bedrock, Secrets Manager, SSM, ECR (api + docker), CloudWatch Logs.
- For each interface endpoint, check `PrivateDnsEnabled = True` and correct `SubnetIds` and `SecurityGroupIds`.

4) Security Groups

- Console: EC2 → Security Groups — find the ALB SG (description should be "Security group for ALB").
	- Ingress: 443 from 0.0.0.0/0
	- Egress: 0.0.0.0/0
- Internal ALB SG should allow traffic from the VPC CIDR.
- VPC endpoint SGs should allow traffic from the VPC CIDR on the expected ports.

5) Application Load Balancers

- Console: EC2 → Load Balancers — verify the public ALB:
	- Scheme = internet-facing
	- Type = application
	- Security group is the ALB SG
	- HTTPS listener exists and (if using ACM) uses the CertificateArn from outputs
- Internal ALB should be `internet-facing = No` and attached to private subnets.

6) WAF Association

- Console: WAF & Shield → Web ACLs — check the WebACL exists and is associated with the ALB.

7) Route53 & ACM

- Console: Route 53 → Hosted zones — verify the hosted zone (if created or looked-up) matches your domain.
- Console: Route 53 → Record sets — confirm any ACM DNS validation CNAMEs are present when using DNS validation.
- Console: Certificate Manager → Certificates — find the `CertificateArn` output:
	- Status = ISSUED means cert is valid.
	- PENDING_VALIDATION: check the CNAME validation record.
	- FAILED: inspect the status reason (often mismatch between certificate domain and hosted zone).

8) Bedrock VPC Endpoint

- Console: VPC → Endpoints — find the Bedrock endpoint and confirm:
	- `ServiceName` is concrete for the region (e.g. `com.amazonaws.us-east-1.bedrock-runtime`).
	- `PrivateDnsEnabled` = True
	- Subnets are private subnets and SecurityGroup(s) are attached.

9) Tags and security controls

- Spot check resource tags (Project/Environment/Owner/CostCenter) are present.
- Verify encryption settings for data services (S3, RDS) per your security requirements.

10) Observability

- Console: CloudWatch → Metrics/Logs — confirm ALB metrics and any log groups (if configured) exist.

Quick CLI commands (optional)

```
aws cloudformation describe-stacks --stack-name NetworkStack --query "Stacks[0].Outputs" --output table
aws acm describe-certificate --certificate-arn <CERT_ARN> --region us-east-1
aws route53 list-resource-record-sets --hosted-zone-id <HOSTED_ZONE_ID>
aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<VpcId>
```

Troubleshooting tips

- Certificate not Issued: ensure the hosted zone matches the certificate domain and the DNS validation record is present.
- Bedrock endpoint errors: ensure the endpoint `ServiceName` is the region-specific service and redeploy after setting CDK env/account if needed.
- ALB health check / targets: ensure the compute stack is deployed and target instances/containers are healthy and registered.

If you'd like, I can also print the `NetworkStack` template fragment (Bedrock endpoint, ALB, Certificate) from the synth output so you can inspect exact values.


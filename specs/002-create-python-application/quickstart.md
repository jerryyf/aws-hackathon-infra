# Quickstart: AWS CDK Infrastructure Deployment

## Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.11+
- Node.js 18+ (for CDK CLI)
- Git
- pytest (for contract tests)

## Installation
```bash
# Clone repository
git clone <repo-url>
cd aws-hackathon-infra

# Install Python dependencies
cd cdk
pip install -r requirements.txt

# Install CDK CLI globally
npm install -g aws-cdk

# Bootstrap CDK (first time only, per region/account)
cdk bootstrap aws://ACCOUNT-ID/us-east-1
```

## Deployment Scenarios

### Scenario 1: Full Development Environment
```bash
cd cdk

# Synthesize all stacks
cdk synth

# Deploy in dependency order
cdk deploy NetworkStack --require-approval never
cdk deploy SecurityStack --require-approval never
cdk deploy DatabaseStack --require-approval never
cdk deploy StorageStack --require-approval never
cdk deploy ComputeStack --require-approval never
cdk deploy MonitoringStack --require-approval never

# Run contract tests
cd ../tests/contract
pytest -v
```

### Scenario 2: Production Deployment
```bash
cd cdk

# Set production context
export CDK_ENVIRONMENT=production

# Deploy with approval for production changes
cdk deploy --all --context environment=production

# Verify stack outputs
aws cloudformation describe-stacks --stack-name NetworkStack --query 'Stacks[0].Outputs'
aws cloudformation describe-stacks --stack-name DatabaseStack --query 'Stacks[0].Outputs'
```

### Scenario 3: Contract Test Validation Only
```bash
# Run contract tests against deployed stacks
cd tests/contract

# Test network stack outputs
pytest test_vpc_contract.py -v

# Test security stack outputs
pytest test_security_groups_contract.py -v

# Test database stack outputs
pytest test_database_contract.py -v

# Test storage stack outputs
pytest test_storage_contract.py -v

# Run all contract tests
pytest -v --tb=short
```

### Scenario 4: Disaster Recovery Test
```bash
# Simulate AZ failure
aws ec2 describe-instances --filters "Name=availability-zone,Values=us-east-1a"

# Verify Aurora cluster multi-AZ failover
aws rds describe-db-clusters --db-cluster-identifier <cluster-id> \
  --query 'DBClusters[0].[DBClusterIdentifier,MultiAZ,DBClusterMembers[*].DBInstanceIdentifier]'

# Verify OpenSearch domain resilience
aws opensearch describe-domain --domain-name <domain-name> --query 'DomainStatus.ClusterConfig.ZoneAwarenessEnabled'

# Check ALB target health in remaining AZ
aws elbv2 describe-target-health --target-group-arn <target-group-arn>
```

### Scenario 5: Teardown
```bash
cd cdk

# Destroy stacks in reverse dependency order
cdk destroy MonitoringStack --force
cdk destroy ComputeStack --force
cdk destroy StorageStack --force
cdk destroy DatabaseStack --force
cdk destroy SecurityStack --force
cdk destroy NetworkStack --force

# Verify all resources deleted
aws cloudformation list-stacks --stack-status-filter DELETE_COMPLETE
```

## Validation Procedures

### VPC and Networking
```bash
# Get VPC ID from stack outputs
VPC_ID=$(aws cloudformation describe-stacks --stack-name NetworkStack \
  --query 'Stacks[0].Outputs[?OutputKey==`VpcId`].OutputValue' --output text)

# Validate VPC CIDR
aws ec2 describe-vpcs --vpc-ids $VPC_ID --query 'Vpcs[0].CidrBlock'
# Expected: 10.0.0.0/16

# Validate subnet distribution
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[*].[SubnetId,AvailabilityZone,CidrBlock,MapPublicIpOnLaunch]' --output table
# Expected: 4 subnets (2 public in us-east-1a/1b, 2 private in us-east-1a/1b)

# Validate NAT Gateway redundancy
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" \
  --query 'NatGateways[*].[NatGatewayId,SubnetId,State]' --output table
# Expected: 2 NAT Gateways (one per AZ)

# Validate VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'VpcEndpoints[*].[ServiceName,VpcEndpointType,State]' --output table
# Expected: bedrock-runtime, secretsmanager, ecr-api, ecr-dkr, s3
```

### Security Groups and WAF
```bash
# Get security group IDs
SG_ALB=$(aws cloudformation describe-stacks --stack-name SecurityStack \
  --query 'Stacks[0].Outputs[?OutputKey==`AlbSecurityGroupId`].OutputValue' --output text)

# Validate ALB security group rules
aws ec2 describe-security-groups --group-ids $SG_ALB \
  --query 'SecurityGroups[0].IpPermissions[*].[FromPort,ToPort,IpProtocol,IpRanges]' --output table
# Expected: Ingress 443 from 0.0.0.0/0

# Validate security group chaining
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'SecurityGroups[*].[GroupName,GroupId]' --output table
# Expected: 8 security groups (ALB, ECS, RDS, RDSProxy, OpenSearch, VPCEndpoints, Bastion, Lambda)

# Validate WAF Web ACL
WAF_ARN=$(aws cloudformation describe-stacks --stack-name SecurityStack \
  --query 'Stacks[0].Outputs[?OutputKey==`WafWebAclArn`].OutputValue' --output text)
aws wafv2 get-web-acl --id $(echo $WAF_ARN | cut -d'/' -f3) --scope REGIONAL --region us-east-1
# Expected: Rules for rate limiting, AWS Managed Core Rule Set, Known Bad Inputs
```

### Authentication Layer
```bash
# Get Cognito User Pool ID
COGNITO_POOL_ID=$(aws cloudformation describe-stacks --stack-name SecurityStack \
  --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolId`].OutputValue' --output text)

# Validate Cognito User Pool configuration
aws cognito-idp describe-user-pool --user-pool-id $COGNITO_POOL_ID \
  --query 'UserPool.[Id,Policies.PasswordPolicy,MfaConfiguration,AutoVerifiedAttributes]' --output table
# Expected: MinLength=12, MfaConfiguration=OPTIONAL, AutoVerifiedAttributes=[email]

# Validate Cognito User Pool Client
COGNITO_CLIENT_ID=$(aws cloudformation describe-stacks --stack-name SecurityStack \
  --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolClientId`].OutputValue' --output text)
aws cognito-idp describe-user-pool-client --user-pool-id $COGNITO_POOL_ID --client-id $COGNITO_CLIENT_ID \
  --query 'UserPoolClient.[ClientName,AllowedOAuthFlows,AllowedOAuthScopes,CallbackURLs]' --output table
# Expected: AllowedOAuthFlows=[code], AllowedOAuthScopes=[openid, email, profile]

# Validate Cognito User Pool Domain
COGNITO_DOMAIN=$(aws cloudformation describe-stacks --stack-name SecurityStack \
  --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolDomain`].OutputValue' --output text)
aws cognito-idp describe-user-pool-domain --domain $(echo $COGNITO_DOMAIN | cut -d'.' -f1)
# Expected: Domain status ACTIVE

# Test ALB Cognito integration
ALB_DNS=$(aws cloudformation describe-stacks --stack-name ComputeStack \
  --query 'Stacks[0].Outputs[?OutputKey==`PublicAlbDns`].OutputValue' --output text)
curl -I https://$ALB_DNS/
# Expected: 302 redirect to Cognito hosted UI
```

### Database Layer
```bash
# Get RDS Proxy endpoint
RDS_PROXY_ENDPOINT=$(aws cloudformation describe-stacks --stack-name DatabaseStack \
  --query 'Stacks[0].Outputs[?OutputKey==`RdsProxyEndpoint`].OutputValue' --output text)

# Validate Aurora cluster configuration
aws rds describe-db-clusters \
  --query 'DBClusters[*].[DBClusterIdentifier,Engine,EngineVersion,DBClusterMembers[*].[DBInstanceIdentifier,IsClusterWriter]]' --output table
# Expected: Engine=aurora-postgresql, at least 1 writer + 1 reader instance

# Validate OpenSearch domain configuration
aws opensearch describe-domain --domain-name hackathon-opensearch \
  --query 'DomainStatus.[ClusterConfig.InstanceCount,ClusterConfig.ZoneAwarenessEnabled,EncryptionAtRestOptions.Enabled]' --output table
# Expected: InstanceCount=3, ZoneAwarenessEnabled=true, Encryption=true

# Test database secret retrieval
DB_SECRET_ARN=$(aws cloudformation describe-stacks --stack-name DatabaseStack \
  --query 'Stacks[0].Outputs[?OutputKey==`RdsSecretArn`].OutputValue' --output text)
aws secretsmanager get-secret-value --secret-id $DB_SECRET_ARN --query SecretString --output text
# Expected: JSON with username, password, engine, host
```

### Storage Layer
```bash
# Validate S3 bucket encryption
BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name StorageStack \
  --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' --output text)
aws s3api get-bucket-encryption --bucket $BUCKET_NAME
# Expected: AES256 or aws:kms

# Validate S3 lifecycle policies
aws s3api get-bucket-lifecycle-configuration --bucket $BUCKET_NAME
# Expected: IA transition at 90 days, Glacier at 180 days, deletion at 365 days

# Validate ECR repository
ECR_URI=$(aws cloudformation describe-stacks --stack-name StorageStack \
  --query 'Stacks[0].Outputs[?OutputKey==`EcrRepositoryUri`].OutputValue' --output text)
aws ecr describe-repositories --repository-names $(echo $ECR_URI | cut -d'/' -f2)
# Expected: ImageScanningEnabled=true, LifecyclePolicy configured
```

### Contract Test Execution
```bash
# Set AWS environment variables
export AWS_DEFAULT_REGION=us-east-1
export AWS_PROFILE=<your-profile>

# Run all contract tests
cd tests/contract
pytest -v --tb=short --capture=no

# Run specific contract test
pytest test_vpc_contract.py::test_vpc_cidr_block -v

# Generate contract test report
pytest --html=report.html --self-contained-html
```

## Success Metrics

### Deployment Success
- All 6 stacks deploy without errors (NetworkStack, SecurityStack, DatabaseStack, StorageStack, ComputeStack, MonitoringStack)
- Stack outputs present for all required exports (see contracts/*.yaml)
- All contract tests pass (100% pass rate)

### Security Posture
- No public database access (security group rules verified)
- All traffic encrypted in transit (TLS 1.2+ on ALB)
- Secrets rotation enabled (90-day policy)
- WAF rules active (rate limiting + AWS Managed Rules)

### High Availability
- Resources distributed across us-east-1a and us-east-1b
- Aurora PostgreSQL cluster with writer and reader instances in different AZs
- OpenSearch 3-node cluster with zone awareness
- NAT Gateway redundancy (one per AZ)

### Observability
- CloudWatch Logs enabled for all services
- CloudTrail data events logged
- VPC Flow Logs active
- Alarms configured for critical resources

## Troubleshooting

### Deployment Failures

**Error: "Resource limit exceeded"**
```bash
# Check service quotas
aws service-quotas get-service-quota --service-code vpc --quota-code L-F678F1CE
# Solution: Request quota increase in AWS Console
```

**Error: "VPC endpoint subnet mismatch"**
```bash
# Verify subnets exist before deploying SecurityStack
aws cloudformation describe-stacks --stack-name NetworkStack \
  --query 'Stacks[0].Outputs[?contains(OutputKey, `Subnet`)].OutputValue'
# Solution: Ensure NetworkStack deployed successfully first
```

**Error: "RDS snapshot restore failed"**
```bash
# Check RDS subnet group configuration
aws rds describe-db-subnet-groups
# Solution: Verify private subnets span multiple AZs
```

### Connectivity Issues

**Cannot connect to RDS Proxy**
```bash
# Verify security group rules
aws ec2 describe-security-groups --group-ids <rds-proxy-sg-id>
# Solution: Ensure ECS security group allowed in RDS Proxy security group

# Check proxy status
aws rds describe-db-proxies --db-proxy-name <proxy-name>
# Solution: Wait for proxy status to reach "available"
```

**Cognito authentication not working**
```bash
# Verify ALB listener rule has authenticate-cognito action
aws elbv2 describe-rules --listener-arn <listener-arn> \
  --query 'Rules[*].Actions[?Type==`authenticate-cognito`]'
# Solution: Ensure ComputeStack configured ALB listener with Cognito action

# Check Cognito callback URL matches ALB DNS
aws cognito-idp describe-user-pool-client --user-pool-id <pool-id> --client-id <client-id> \
  --query 'UserPoolClient.CallbackURLs'
# Solution: Update callback URL to match ALB DNS (https://<alb-dns>/oauth2/idpresponse)

# Test Cognito hosted UI directly
COGNITO_DOMAIN=$(aws cloudformation describe-stacks --stack-name SecurityStack \
  --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolDomain`].OutputValue' --output text)
curl -I "https://$COGNITO_DOMAIN/login?client_id=<client-id>&response_type=code&redirect_uri=https://<alb-dns>/oauth2/idpresponse"
# Expected: 200 OK (hosted UI login page)
```

**Bedrock API calls failing**
```bash
# Test VPC endpoint DNS resolution
nslookup bedrock-runtime.us-east-1.amazonaws.com
# Solution: Verify private DNS enabled on VPC endpoint

# Check VPC endpoint security group
aws ec2 describe-vpc-endpoints --filters "Name=service-name,Values=com.amazonaws.us-east-1.bedrock-runtime"
# Solution: Ensure ECS security group allowed in VPC endpoint security group
```

**S3 access denied from ECS tasks**
```bash
# Verify S3 bucket policy allows VPC endpoint
aws s3api get-bucket-policy --bucket <bucket-name>
# Solution: Add VPC endpoint condition to bucket policy

# Check task IAM role permissions
aws iam get-role-policy --role-name <task-role> --policy-name S3Access
# Solution: Grant s3:GetObject, s3:PutObject permissions
```

### Performance Issues

**OpenSearch cluster yellow status**
```bash
# Check cluster health
aws opensearch describe-domain --domain-name hackathon-opensearch \
  --query 'DomainStatus.ClusterConfig'
# Solution: Ensure 3 data nodes and zone awareness enabled

# Verify index replica settings
curl -XGET https://<opensearch-endpoint>/_cluster/health?pretty
# Solution: Set number_of_replicas to 1 or 2
```

**High NAT Gateway costs**
```bash
# Check data transfer metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/NATGateway \
  --metric-name BytesOutToDestination \
  --dimensions Name=NatGatewayId,Value=<nat-gw-id> \
  --start-time 2025-10-01T00:00:00Z \
  --end-time 2025-10-07T23:59:59Z \
  --period 3600 \
  --statistics Sum
# Solution: Use VPC endpoints for AWS services, reduce cross-AZ traffic
```

### Common CDK Issues

**Error: "Stack already exists"**
```bash
# Check existing stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
# Solution: Use `cdk deploy --force` or delete existing stack
```

**Error: "Bootstrap version mismatch"**
```bash
# Check bootstrap stack version
aws cloudformation describe-stacks --stack-name CDKToolkit \
  --query 'Stacks[0].Outputs[?OutputKey==`BootstrapVersion`].OutputValue'
# Solution: Re-run `cdk bootstrap` to update to latest version
```

**Error: "Context value missing"**
```bash
# Verify cdk.json contains required context
cat cdk/cdk.json | jq '.context'
# Solution: Add missing context values for environment-specific config
```

## Additional Resources
- Architecture documentation: `/docs/arch.md`
- Data model reference: `/specs/002-create-python-application/data-model.md`
- Stack contracts: `/specs/002-create-python-application/contracts/`
- Research decisions: `/specs/002-create-python-application/research.md`
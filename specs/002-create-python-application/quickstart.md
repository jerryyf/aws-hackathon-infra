# Quickstart: AWS CDK Infrastructure Deployment

## Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.11+
- Node.js 18+ (for CDK CLI)
- Git

## Installation
```bash
# Clone repository
git clone <repo-url>
cd aws-hackathon-infra

# Install dependencies
pip install -r requirements.txt
npm install -g aws-cdk

# Bootstrap CDK (first time only)
cdk bootstrap
```

## Deployment
```bash
# Synthesize CloudFormation
cdk synth

# Deploy to AWS
cdk deploy --require-approval never
```

## Validation Tests

### Test 1: VPC and Subnets Created
```bash
# Check VPC exists
aws ec2 describe-vpcs --filters Name=tag:Name,Values=HackathonVPC

# Check subnets in correct AZs
aws ec2 describe-subnets --filters Name=vpc-id,Values=<vpc-id>
```

### Test 2: Load Balancer Accessible
```bash
# Get ALB DNS name from stack outputs
curl https://<alb-dns-name>
# Should return 200 or redirect
```

### Test 3: Database Connectivity
```bash
# Test RDS proxy connection (from private subnet)
# Use credentials from Secrets Manager
aws secretsmanager get-secret-value --secret-id <rds-secret>
```

### Test 4: Bedrock Access
```bash
# Test VPC endpoint connectivity
aws bedrock list-foundation-models
```

### Test 5: Multi-AZ Resilience
```bash
# Simulate AZ failure (manually stop resources in one AZ)
# Verify traffic routes to remaining AZ
```

## Cleanup
```bash
# Destroy infrastructure
cdk destroy
```

## Troubleshooting
- Check CloudWatch logs for deployment errors
- Verify IAM permissions for CDK deployment
- Ensure region is us-east-1
- Check VPC endpoint configurations for private access
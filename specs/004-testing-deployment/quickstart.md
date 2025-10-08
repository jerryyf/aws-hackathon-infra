# Quickstart: Deployment Testing

## Prerequisites
- AWS CLI configured with deployment credentials
- CDK CLI installed (`npm install -g aws-cdk`)
- Python 3.8+ with virtual environment
- Access to test AWS account/environment

## Setup
```bash
# Clone repository
git clone <repository-url>
cd aws-hackathon-infra

# Activate virtual environment
source cdk/venv/bin/activate

# Install dependencies
pip install -r cdk/requirements.txt
```

## Test Environment Configuration
```bash
# Set environment variables for test deployment
export CDK_DEPLOY_ACCOUNT=<test-account-id>
export CDK_DEPLOY_REGION=us-east-1
export ENVIRONMENT=test
```

## Running Synthesis Tests
```bash
# Test CDK synthesis (no AWS resources created)
cdk synth

# Run contract tests for template validation
pytest tests/contract/ -v
```

## Running Deployment Tests
```bash
# Deploy to test environment
./scripts/deploy.sh test

# Monitor deployment progress
tail -f deployment.log
```

## Post-Deployment Verification
```bash
# Run integration tests
pytest tests/integration/ -v

# Verify resource accessibility
python -c "
import boto3
ec2 = boto3.client('ec2')
vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Environment', 'Values': ['test']}])
print(f'Found {len(vpcs[\"Vpcs\"])} VPCs in test environment')
"
```

## Rollback Testing
```bash
# Test rollback procedure
./scripts/rollback.sh test

# Verify clean removal
python -c "
import boto3
cf = boto3.client('cloudformation')
stacks = cf.describe_stacks()['Stacks']
test_stacks = [s for s in stacks if 'test' in s.get('Tags', [])]
print(f'Remaining test stacks: {len(test_stacks)}')
"
```

## Expected Results
- ✅ Synthesis completes without errors
- ✅ All stacks deploy in correct order
- ✅ Resources are accessible and configured
- ✅ Rollback removes all resources
- ✅ Test logs show comprehensive coverage

## Troubleshooting
- **Synthesis fails**: Check CDK version compatibility
- **Deployment fails**: Verify AWS permissions and quotas
- **Tests fail**: Check AWS resource state and network connectivity
- **Rollback fails**: Manual cleanup may be required

## Next Steps
- Review test results in CI/CD pipeline
- Configure automated testing in staging environment
- Set up monitoring for production deployments
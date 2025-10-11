# Quickstart: Deploying AWS AgentCore Runtime

**Feature**: AWS AgentCore Runtime Infrastructure  
**Audience**: Platform engineers deploying AI agent runtimes  
**Time to Complete**: ~15 minutes (10 min CDK deploy + 5 min verification)  
**Prerequisites**: AWS account, CDK bootstrapped, Docker installed

---

## Overview

This guide walks through deploying an AWS Bedrock AgentCore runtime using AWS CDK. The runtime deploys a containerized AI agent application that can invoke Amazon Bedrock models and execute custom logic.

**What You'll Deploy**:
- ECR repository for agent container images
- IAM execution role with Bedrock/ECR/CloudWatch permissions
- VPC endpoint for private bedrock-agentcore service access (VPC mode only)
- AgentCore runtime resource in ACTIVE status

---

## Prerequisites

### 1. Verify AWS Environment

```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify region (must be us-east-1 for this project)
aws configure get region  # Should return: us-east-1

# Confirm CDK bootstrap
aws cloudformation describe-stacks --stack-name CDKToolkit
```

### 2. Verify Existing Infrastructure

The AgentCore stack depends on network, security, and storage stacks:

```bash
cd /Users/jerrlin/repos/personal/aws-hackathon-infra

# Check existing stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  | jq '.StackSummaries[] | select(.StackName | test("hackathon-(network|security|storage)-stack"))'

# Expected: 3 stacks (network, security, storage)
```

### 3. Prepare Agent Container Image

You need a container image with an `/invocations` endpoint. For testing, use AWS's starter toolkit:

```bash
# Clone AWS AgentCore starter toolkit
git clone https://github.com/aws-samples/bedrock-agentcore-starter-toolkit.git /tmp/agentcore-starter
cd /tmp/agentcore-starter

# Build sample agent container
docker build -t agent-test:v1.0.0 -f examples/minimal-agent/Dockerfile examples/minimal-agent/

# Verify container runs
docker run --rm -p 8080:8080 agent-test:v1.0.0 &
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "test-123", "prompt": "Hello"}' | jq
docker stop $(docker ps -q --filter ancestor=agent-test:v1.0.0)
```

---

## Deployment Steps

### Step 1: Push Container Image to ECR

```bash
# Set variables
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
REPOSITORY_NAME="agent-images"
IMAGE_TAG="v1.0.0"

# Create ECR repository (if deploying storage stack for first time)
cd /Users/jerrlin/repos/personal/aws-hackathon-infra/cdk
cdk deploy hackathon-storage-stack --require-approval never

# Login to ECR
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Tag and push image
docker tag agent-test:v1.0.0 $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG

# Verify image exists
aws ecr describe-images --repository-name $REPOSITORY_NAME --image-ids imageTag=$IMAGE_TAG
```

### Step 2: Configure Runtime Settings

Edit `cdk/config.py` to add AgentCore runtime configuration:

```python
# Add to cdk/config.py
AGENTCORE_CONFIG = {
    "stack_name": "hackathon-agentcore-stack",
    "runtime_name": f"hackathon-agent-{ENVIRONMENT}-{AWS_REGION}",
    "container_image_tag": "v1.0.0",  # Must match ECR image tag
    "container_cpu": 512,              # 0.5 vCPU (testing), 1024 for prod
    "container_memory": 1024,          # 1 GB (testing), 2048 for prod
    "network_mode": "VPC",             # VPC (recommended) or PUBLIC
}
```

### Step 3: Deploy AgentCore Stack

```bash
cd /Users/jerrlin/repos/personal/aws-hackathon-infra/cdk

# Synthesize CloudFormation template
cdk synth hackathon-agentcore-stack

# Preview changes
cdk diff hackathon-agentcore-stack

# Deploy stack
cdk deploy hackathon-agentcore-stack --require-approval never

# Expected output:
# ✅  hackathon-agentcore-stack
# 
# Outputs:
# hackathon-agentcore-stack.AgentRuntimeArn = arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/xyz123
# hackathon-agentcore-stack.AgentRuntimeEndpointUrl = https://xyz123.runtime.bedrock-agentcore.us-east-1.amazonaws.com
# hackathon-agentcore-stack.AgentRuntimeStatus = ACTIVE
# hackathon-agentcore-stack.ExecutionRoleArn = arn:aws:iam::123456789012:role/hackathon-agent-execution-role-test
```

**Deployment Time**: ~10 minutes (runtime status: CREATING → ACTIVE)

---

## Verification

### Step 4: Verify Runtime Status

```bash
# Get runtime ARN from stack outputs
RUNTIME_ARN=$(aws cloudformation describe-stacks \
  --stack-name hackathon-agentcore-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`AgentRuntimeArn`].OutputValue' \
  --output text)

# Check runtime status (should be ACTIVE)
aws bedrock-agentcore get-agent-runtime --runtime-arn $RUNTIME_ARN

# Expected output:
# {
#   "runtimeArn": "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/xyz123",
#   "runtimeName": "hackathon-agent-test-us-east-1",
#   "status": "ACTIVE",
#   "createdAt": "2025-10-10T14:30:00Z",
#   "updatedAt": "2025-10-10T14:40:00Z"
# }
```

### Step 5: Test Runtime Invocation

```bash
# Invoke runtime with test payload
aws bedrock-agentcore invoke-agent-runtime \
  --runtime-arn $RUNTIME_ARN \
  --session-id "test-session-$(uuidgen)" \
  --prompt "What is the capital of France?" \
  --output json | jq

# Expected response (< 2 seconds per SC-003):
# {
#   "sessionId": "test-session-abc123...",
#   "completion": "The capital of France is Paris.",
#   "responseMetadata": {
#     "httpStatusCode": 200,
#     "requestId": "..."
#   }
# }
```

### Step 6: Verify Network Configuration (VPC mode only)

```bash
# Check VPC endpoint exists
aws ec2 describe-vpc-endpoints \
  --filters "Name=service-name,Values=com.amazonaws.$REGION.bedrock-agentcore" \
  --query 'VpcEndpoints[0].{VpcEndpointId:VpcEndpointId,State:State}' \
  --output table

# Expected: State = available

# Verify runtime ENIs are in PrivateAgent subnets
aws ec2 describe-network-interfaces \
  --filters "Name=description,Values=*bedrock-agentcore*" \
  --query 'NetworkInterfaces[].{SubnetId:SubnetId,PrivateIp:PrivateIpAddress}' \
  --output table

# Expected: Subnets in 10.0.2.0/24 range (PrivateAgent tier)
```

### Step 7: Check CloudWatch Logs

```bash
# View runtime logs
aws logs tail /aws/bedrock-agentcore/hackathon-agent-test-us-east-1 --follow

# Expected log entries:
# [INFO] Runtime started
# [INFO] Processing invocation request sessionId=test-session-abc123...
# [INFO] Invoking Bedrock model: anthropic.claude-3-sonnet-20240229-v1:0
# [INFO] Response returned in 1.2s
```

---

## Contract Validation

Run contract tests to verify stack outputs match specifications:

```bash
cd /Users/jerrlin/repos/personal/aws-hackathon-infra

# Run AgentCore contract tests
PYTHONPATH=. pytest tests/contract/test_agentcore_runtime_contract.py -v

# Expected output:
# tests/contract/test_agentcore_runtime_contract.py::test_runtime_arn_format PASSED
# tests/contract/test_agentcore_runtime_contract.py::test_runtime_status_active PASSED
# tests/contract/test_agentcore_runtime_contract.py::test_endpoint_url_https PASSED
# tests/contract/test_agentcore_runtime_contract.py::test_execution_role_arn_format PASSED
```

---

## Common Issues

### Issue 1: Runtime stuck in CREATING status

**Cause**: Container image fails health check or execution role lacks permissions.

**Solution**:
```bash
# Check CloudWatch logs for errors
aws logs tail /aws/bedrock-agentcore/hackathon-agent-test-us-east-1 --since 10m

# Common errors:
# - "Unable to pull ECR image" → Verify execution role has ecr:BatchGetImage permission
# - "Container exit code 1" → Test container locally (docker run)
# - "Health check timeout" → Verify container exposes /invocations endpoint on port 8080
```

### Issue 2: Invocation fails with "Network error"

**Cause**: VPC mode runtime cannot reach bedrock-agentcore VPC endpoint.

**Solution**:
```bash
# Verify VPC endpoint security group allows ingress from runtime security group
aws ec2 describe-security-groups \
  --filters "Name=tag:Name,Values=*bedrock-agentcore-endpoint*" \
  --query 'SecurityGroups[0].IpPermissions'

# Expected: Ingress rule allowing TCP 443 from agent-runtime security group
```

### Issue 3: Bedrock model invocation fails

**Cause**: Execution role lacks bedrock:InvokeModel permission or model not enabled.

**Solution**:
```bash
# Verify model access in Bedrock console
aws bedrock list-foundation-models --region us-east-1 | \
  jq '.modelSummaries[] | select(.modelId | contains("claude"))'

# Grant model access: AWS Console → Bedrock → Model access → Request access
```

---

## Resource Sizing Guidance

### Testing Environment (P1 - PUBLIC mode)
- **CPU**: 512 units (0.5 vCPU)
- **Memory**: 1024 MiB (1 GB)
- **Network Mode**: PUBLIC (faster deployment, no VPC endpoint required)
- **Use Case**: Development, proof-of-concept, low-traffic testing

### Production Environment (P2 - VPC mode)
- **CPU**: 1024 units (1 vCPU) - 2048 for high-throughput workloads
- **Memory**: 2048 MiB (2 GB) - 4096 for memory-intensive agents
- **Network Mode**: VPC (private connectivity, multi-AZ redundancy)
- **Use Case**: Production workloads, compliance-regulated environments

**Cost Estimation** (us-east-1, 24/7 runtime):
- Testing (512 CPU / 1 GB): ~$15/month
- Production (1024 CPU / 2 GB): ~$30/month
- VPC Endpoint: ~$7/month + $0.01/GB processed

---

## Rollback

If deployment fails or runtime is unhealthy:

```bash
# Delete AgentCore stack
cdk destroy hackathon-agentcore-stack

# Delete ECR images (optional)
aws ecr batch-delete-image \
  --repository-name agent-images \
  --image-ids imageTag=v1.0.0
```

---

## Next Steps

1. **Integrate with Application**: Use runtime ARN in your application code to invoke agents
2. **Add Monitoring**: Configure CloudWatch alarms for invocation errors and latency (see FR-010)
3. **Deploy Multiple Runtimes**: Duplicate stack with different runtime names for A/B testing
4. **Update Container Image**: Push new image tag to ECR, update `config.py`, run `cdk deploy`

---

## Additional Resources

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/agentcore/)
- [AgentCore Starter Toolkit](https://github.com/aws-samples/bedrock-agentcore-starter-toolkit)
- [Contracts Reference](./contracts/agentcore-stack.yaml)
- [Data Model](./data-model.md)
- [Feature Specification](./spec.md)

---

**Last Updated**: 2025-10-10  
**Validated Against**: AWS CDK v2.x, Python 3.11, us-east-1 region

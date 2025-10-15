# Quickstart: Infrastructure Testing Guide

**Feature**: 009-redefine-and-fix  
**Date**: 2025-10-15  
**Purpose**: Developer guide for running and writing infrastructure tests

## Overview

This project uses a three-tier testing approach:
- **Unit Tests**: Fast template validation without AWS deployment
- **Contract Tests**: Validate CloudFormation outputs match contract specifications
- **Integration Tests**: Validate deployed resources and end-to-end behavior

## Running Tests Locally

### Prerequisites

1. **Virtual Environment Setup**:
   ```bash
   source .venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   cd cdk
   pip install -r requirements.txt
   ```

3. **AWS Credentials** (for integration tests only):
   ```bash
   export AWS_PROFILE=hackathon
   export AWS_REGION=us-east-1
   ```

### Running Unit Tests

**No AWS credentials required** - validates CloudFormation templates only.

```bash
PYTHONPATH=. pytest tests/unit/
```

**Run specific test**:
```bash
PYTHONPATH=. pytest tests/unit/test_vpc_construct.py::test_vpc_construct
```

**Expected output**:
```
tests/unit/test_agentcore_stack_synth.py ....        [ 40%]
tests/unit/test_agentcore_validation.py ..           [ 60%]
tests/unit/test_vpc_construct.py .                   [100%]

========== 7 passed in 3.21s ==========
```

**Performance**: <30 seconds for all unit tests

---

### Running Contract Tests

**No AWS credentials required** - validates template outputs against YAML contracts.

```bash
PYTHONPATH=. pytest tests/contract/
```

**Run specific contract test**:
```bash
PYTHONPATH=. pytest tests/contract/test_agentcore_runtime_contract.py
```

**Expected output**:
```
tests/contract/test_agentcore_runtime_contract.py ........  [100%]

========== 8 passed in 2.45s ==========
```

**Performance**: <30 seconds for all contract tests (session-scoped fixtures)

---

### Running Integration Tests

**Requires AWS credentials and deployed stacks** - queries actual AWS resources.

```bash
export AWS_PROFILE=hackathon
export AWS_REGION=us-east-1
PYTHONPATH=. pytest tests/integration/
```

**Run specific integration test**:
```bash
PYTHONPATH=. pytest tests/integration/test_database_connectivity.py
```

**Expected output (stacks deployed)**:
```
tests/integration/test_database_connectivity.py .    [100%]

========== 1 passed in 12.34s ==========
```

**Expected output (stacks NOT deployed)**:
```
tests/integration/test_database_connectivity.py s    [100%]

========== 1 skipped in 0.21s ==========
```

**Performance**: 1-5 minutes per integration test (network calls to AWS)

---

### Running All Tests

```bash
PYTHONPATH=. pytest tests/
```

**Warning**: Integration tests will skip if stacks aren't deployed.

---

## Writing Unit Tests

### Purpose
Validate CloudFormation template structure, resource counts, and properties **without AWS deployment**.

### Pattern

```python
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk
import uuid

def test_vpc_construct():
    app = cdk.App()
    unique_id = str(uuid.uuid4())[:8]
    
    stack = NetworkStack(
        app,
        f"TestNetworkStack{unique_id}",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    
    template = Template.from_stack(stack)
    
    template.resource_count_is("AWS::EC2::VPC", 1)
    
    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.0.0.0/16",
        "EnableDnsHostnames": True,
        "EnableDnsSupport": True,
    })
```

### Key Rules

1. **Unique Stack Names**: Always use UUID suffix to avoid JSII kernel conflicts
   ```python
   import uuid
   unique_id = str(uuid.uuid4())[:8]
   stack_name = f"TestNetworkStack{unique_id}"
   ```

2. **Mock Environment**: Use fake account/region
   ```python
   env=cdk.Environment(account="123456789012", region="us-east-1")
   ```

3. **No AWS Credentials**: Tests must run without `AWS_PROFILE` or `AWS_REGION`

4. **Fast Execution**: Target <5 seconds per test

### Common Assertions

```python
template.resource_count_is("AWS::EC2::VPC", 1)

template.has_resource_properties("AWS::EC2::Subnet", {
    "AvailabilityZone": "us-east-1a",
    "CidrBlock": "10.0.1.0/24",
})

template.has_resource("AWS::EC2::VPC", {
    "Properties": {
        "CidrBlock": "10.0.0.0/16",
    }
})

from aws_cdk.assertions import Match
template.has_resource_properties("AWS::IAM::Role", {
    "AssumeRolePolicyDocument": Match.object_like({
        "Statement": Match.array_with([
            Match.object_like({"Effect": "Allow"})
        ])
    })
})
```

### File Location
`tests/unit/test_<stack_name>.py`

---

## Writing Contract Tests

### Purpose
Validate CloudFormation **outputs** match YAML contract specifications **before deployment**.

### Pattern

```python
import pytest
from aws_cdk.assertions import Template
from cdk.stacks.agentcore_stack import AgentCoreStack
from cdk.stacks.network_stack import NetworkStack
from cdk.stacks.security_stack import SecurityStack
from cdk.stacks.storage_stack import StorageStack
import aws_cdk as cdk


@pytest.fixture(scope="session")
def agentcore_stack():
    app = cdk.App()
    
    network_stack = NetworkStack(
        app,
        "TestNetworkStack",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    
    security_stack = SecurityStack(
        app,
        "TestSecurityStack",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    
    storage_stack = StorageStack(
        app,
        "TestStorageStack",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    
    agentcore_config = {
        "cpu": 512,
        "memory": 1024,
        "network_mode": "VPC",
    }
    
    stack = AgentCoreStack(
        app,
        "TestAgentCoreStack",
        network_stack=network_stack,
        security_stack=security_stack,
        storage_stack=storage_stack,
        agentcore_config=agentcore_config,
        environment="test",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    
    return stack


def test_agentcore_runtime_arn_output(agentcore_stack):
    template = Template.from_stack(agentcore_stack)
    
    outputs = template.find_outputs("AgentRuntimeArn")
    assert len(outputs) == 1, "AgentRuntimeArn output missing"
    
    arn_output = outputs["AgentRuntimeArn"]
    assert arn_output["Description"] == "Bedrock AgentCore runtime ARN"
    assert arn_output["Export"]["Name"] == "test-AgentRuntimeArn"
    assert "Value" in arn_output
```

### Key Rules

1. **Session-Scoped Fixtures**: Reuse stack instances across tests
   ```python
   @pytest.fixture(scope="session")
   def agentcore_stack():
       # Stack created once per test session
   ```

2. **Static Stack Names**: No UUID needed for session-scoped fixtures
   ```python
   stack = AgentCoreStack(app, "TestAgentCoreStack", ...)
   ```

3. **Contract Validation**: Check output description, export name, value existence
   ```python
   outputs = template.find_outputs("OutputKey")
   assert outputs["OutputKey"]["Description"] == "Expected description"
   assert outputs["OutputKey"]["Export"]["Name"] == "expected-export-name"
   ```

4. **No AWS Credentials**: Tests validate template only, not deployed resources

### Contract YAML Reference

Contract files define expected outputs:
```yaml
outputs:
  AgentRuntimeArn:
    description: "Bedrock AgentCore runtime ARN"
    export_name: "${Environment}-AgentRuntimeArn"
    format: "arn:aws:bedrock-agentcore:<region>:<account>:runtime/<runtime-id>"
    required: true
```

**Location**: `specs/008-add-aws-agentcore/contracts/agentcore-stack.yaml`

### File Location
`tests/contract/test_<stack_name>_contract.py`

---

## Writing Integration Tests

### Purpose
Validate **deployed AWS resources** and end-to-end behavior using boto3 queries.

### Pattern

```python
import pytest
import boto3
from botocore.exceptions import ClientError
import os


@pytest.fixture
def cloudformation_client():
    return boto3.client(
        "cloudformation",
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )


@pytest.fixture
def agentcore_stack_outputs(cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
        outputs = {
            o["OutputKey"]: o["OutputValue"]
            for o in response["Stacks"][0]["Outputs"]
        }
        return outputs
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            pytest.skip("AgentCoreStack not deployed - skipping integration tests")
        raise


def test_runtime_arn_exists(agentcore_stack_outputs):
    assert "AgentRuntimeArn" in agentcore_stack_outputs
    
    runtime_arn = agentcore_stack_outputs["AgentRuntimeArn"]
    assert runtime_arn.startswith("arn:aws:bedrock-agentcore:")
    
    import re
    pattern = r"^arn:aws:bedrock-agentcore:[a-z0-9-]+:[0-9]{12}:runtime/[a-zA-Z0-9-]+$"
    assert re.match(pattern, runtime_arn), f"Invalid ARN format: {runtime_arn}"


def test_runtime_status_active(agentcore_stack_outputs):
    status = agentcore_stack_outputs.get("AgentRuntimeStatus")
    assert status == "ACTIVE", f"Expected ACTIVE, got {status}"
```

### Key Rules

1. **Fixture-Level Skipping**: Skip in fixtures when stacks not deployed
   ```python
   try:
       response = client.describe_stacks(StackName="AgentCoreStack")
   except ClientError:
       pytest.skip("AgentCoreStack not deployed")
   ```

2. **AWS Credentials Required**: Tests will fail without proper credentials
   ```bash
   export AWS_PROFILE=hackathon
   export AWS_REGION=us-east-1
   ```

3. **Output Dictionary Pattern**: Extract outputs into dict for easy access
   ```python
   outputs = {o["OutputKey"]: o["OutputValue"] for o in ...}
   runtime_arn = outputs["AgentRuntimeArn"]
   ```

4. **Error Handling**: Differentiate between "not deployed" (skip) vs errors (fail)
   ```python
   except ClientError as e:
       if e.response['Error']['Code'] == 'ValidationError':
           pytest.skip("Stack not found")
       else:
           raise  # Real error - fail the test
   ```

### Common boto3 Patterns

#### IAM Role Validation
```python
@pytest.fixture
def iam_client():
    return boto3.client("iam")


def test_execution_role_trust_policy(agentcore_stack_outputs, iam_client):
    role_arn = agentcore_stack_outputs["ExecutionRoleArn"]
    role_name = role_arn.split("/")[-1]
    
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response["Role"]["AssumeRolePolicyDocument"]
    
    principals = []
    for stmt in trust_policy.get("Statement", []):
        if stmt.get("Effect") == "Allow":
            principal = stmt.get("Principal", {})
            if "Service" in principal:
                services = principal["Service"]
                principals.extend(
                    services if isinstance(services, list) else [services]
                )
    
    assert "bedrock-agentcore.amazonaws.com" in principals
```

#### VPC Endpoint Validation
```python
@pytest.fixture
def ec2_client():
    return boto3.client("ec2", region_name=os.getenv("AWS_REGION", "us-east-1"))


def test_bedrock_vpc_endpoint_active(network_stack_outputs, ec2_client):
    vpc_id = network_stack_outputs["VpcId"]
    
    response = ec2_client.describe_vpc_endpoints(
        Filters=[
            {"Name": "vpc-id", "Values": [vpc_id]},
            {
                "Name": "service-name",
                "Values": ["com.amazonaws.us-east-1.bedrock-agentcore"]
            }
        ]
    )
    
    assert len(response["VpcEndpoints"]) > 0, "Bedrock VPC endpoint not found"
    endpoint = response["VpcEndpoints"][0]
    assert endpoint["State"] == "available", f"Endpoint state: {endpoint['State']}"
```

#### RDS Cluster Validation
```python
@pytest.fixture
def rds_client():
    return boto3.client("rds", region_name=os.getenv("AWS_REGION", "us-east-1"))


def test_rds_cluster_available(database_stack_outputs, rds_client):
    cluster_id = database_stack_outputs["RdsClusterId"]
    
    response = rds_client.describe_db_clusters(DBClusterIdentifier=cluster_id)
    cluster = response["DBClusters"][0]
    
    assert cluster["Status"] == "available", f"Cluster status: {cluster['Status']}"
    assert cluster["Engine"] == "aurora-postgresql"
    assert cluster["StorageEncrypted"] is True
```

### Conditional Skip Patterns

#### State-Based Skip
```python
def test_vpc_mode_configuration(agentcore_stack_outputs):
    network_mode = agentcore_stack_outputs.get("NetworkMode", "PUBLIC")
    
    if network_mode != "VPC":
        pytest.skip("Test only applicable for VPC network mode")
    
    assert "VpcId" in agentcore_stack_outputs
```

#### Dependency Stack Skip
```python
def test_dependency_stacks_deployed(cloudformation_client):
    required_stacks = ["NetworkStack", "SecurityStack", "StorageStack"]
    
    for stack_name in required_stacks:
        try:
            response = cloudformation_client.describe_stacks(StackName=stack_name)
            status = response["Stacks"][0]["StackStatus"]
            assert status in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]
        except ClientError:
            pytest.skip(f"Dependency stack {stack_name} not deployed")
```

### File Location
`tests/integration/test_<feature>_<behavior>.py`

---

## CI/CD Test Execution

### GitHub Actions Workflow

```yaml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r cdk/requirements.txt
      - run: PYTHONPATH=. pytest tests/unit/
  
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r cdk/requirements.txt
      - run: PYTHONPATH=. pytest tests/contract/
  
  deploy-to-staging:
    runs-on: ubuntu-latest
    needs: [unit-tests, contract-tests]
    steps:
      - run: cd cdk && cdk deploy --all --profile staging
  
  integration-tests:
    runs-on: ubuntu-latest
    needs: [deploy-to-staging]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r cdk/requirements.txt
      - env:
          AWS_PROFILE: staging
          AWS_REGION: us-east-1
        run: PYTHONPATH=. pytest tests/integration/
```

### Test Execution Strategy

| Test Type | When | AWS Credentials | Deployment | Execution Time |
|-----------|------|----------------|------------|----------------|
| **Unit** | On every PR | ❌ Not required | ❌ Not required | <30s |
| **Contract** | On every PR | ❌ Not required | ❌ Not required | <30s |
| **Integration** | After deployment to staging | ✅ Required | ✅ Required | 1-10min |

---

## Troubleshooting

### JSII Kernel Conflicts

**Error**:
```
RuntimeError: There is already a Construct with name 'NetworkStack' in App
```

**Cause**: Multiple tests using identical stack names.

**Solution**: Add UUID suffix to stack names in unit tests:
```python
import uuid
unique_id = str(uuid.uuid4())[:8]
stack = NetworkStack(app, f"TestNetworkStack{unique_id}", ...)
```

**Exception**: Session-scoped fixtures don't need UUIDs (stack created once).

---

### Stack Not Deployed (Integration Tests)

**Error**:
```
botocore.exceptions.ClientError: An error occurred (ValidationError) when calling the DescribeStacks operation: Stack with id AgentCoreStack does not exist
```

**Expected**: Integration tests skip gracefully with fixture-level skipping.

**Check fixture implementation**:
```python
@pytest.fixture
def stack_outputs(cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
        return {o["OutputKey"]: o["OutputValue"] for o in response["Stacks"][0]["Outputs"]}
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            pytest.skip("AgentCoreStack not deployed - skipping integration tests")
        raise
```

---

### AWS Credentials Not Found

**Error**:
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Solution**: Set AWS profile and region:
```bash
export AWS_PROFILE=hackathon
export AWS_REGION=us-east-1
```

**Verify credentials**:
```bash
aws sts get-caller-identity --profile hackathon
```

---

### Import Errors

**Error**:
```
ModuleNotFoundError: No module named 'cdk.stacks'
```

**Solution**: Set `PYTHONPATH` to repository root:
```bash
PYTHONPATH=. pytest tests/unit/
```

---

## Test File Naming Conventions

| Test Type | Pattern | Example |
|-----------|---------|---------|
| **Unit** | `test_<stack_name>.py` | `test_vpc_construct.py` |
| **Contract** | `test_<stack_name>_contract.py` | `test_agentcore_runtime_contract.py` |
| **Integration** | `test_<feature>_<behavior>.py` | `test_database_connectivity.py` |

---

## Quick Reference

### Run Tests
```bash
source .venv/bin/activate

PYTHONPATH=. pytest tests/unit/

PYTHONPATH=. pytest tests/contract/

export AWS_PROFILE=hackathon
export AWS_REGION=us-east-1
PYTHONPATH=. pytest tests/integration/
```

### Common pytest Options
```bash
pytest -v                    # Verbose output
pytest -s                    # Show print statements
pytest -k "test_vpc"         # Run tests matching pattern
pytest --tb=short            # Short traceback format
pytest -x                    # Stop on first failure
pytest --maxfail=2           # Stop after 2 failures
```

### Contract YAML Locations
- AgentCore: `specs/008-add-aws-agentcore/contracts/agentcore-stack.yaml`
- IAM Policies: `specs/008-add-aws-agentcore/contracts/execution-role-permissions.json`
- Trust Policies: `specs/008-add-aws-agentcore/contracts/execution-role-trust.json`

### Test Categories Summary

| Category | Tool | AWS Needed | Speed | Purpose |
|----------|------|-----------|-------|---------|
| **Unit** | `Template.from_stack()` | ❌ | <5s | Template structure |
| **Contract** | `Template.from_stack()` + YAML | ❌ | <10s | Output validation |
| **Integration** | boto3 clients | ✅ | 1-5min | Behavior validation |

# Infrastructure-as-Code Testing Best Practices

## Overview

This document covers AWS CDK testing patterns for Python-based infrastructure projects, based on research into AWS CDK, pytest, boto3 documentation and analysis of the existing test suite.

## 1. Unit vs Contract vs Integration Tests

### Unit Tests

**Purpose**: Validate CloudFormation template synthesis without AWS deployment.

**Pattern**: Use `Template.from_stack()` from `aws_cdk.assertions`

**When to Use**:
- Basic resource count validation
- Template property verification
- Fast feedback during development
- No AWS credentials required

**Example** (tests/unit/test_vpc_construct.py:7-29):
```python
def test_vpc_construct():
    app = cdk.App()
    stack = NetworkStack(app, "TestStack")
    template = Template.from_stack(stack)
    
    template.resource_count_is("AWS::EC2::VPC", 1)
    template.resource_count_is("AWS::EC2::Subnet", 8)
    template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 2)
    template.resource_count_is("AWS::EC2::VPCEndpoint", 9)
```

**Key Methods**:
- `resource_count_is(type, count)`: Assert exact resource count
- `has_resource_properties(type, props)`: Verify resource properties
- `find_outputs(key)`: Extract CloudFormation outputs

### Contract Tests

**Purpose**: Verify CloudFormation outputs match YAML contract specifications before deployment.

**Pattern**: Session-scoped fixtures + output validation against contracts

**When to Use**:
- Validating cross-stack references (Export.Name)
- Ensuring output format consistency
- Enforcing infrastructure contracts between teams
- Pre-deployment validation

**Example** (tests/contract/test_agentcore_vpc_endpoint_contract.py:56-66):
```python
@pytest.fixture(scope="session")
def network_stack():
    app = cdk.App()
    stack = NetworkStack(
        app,
        "TestNetworkStack",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    return stack

def test_bedrock_agentcore_endpoint_outputs(network_stack):
    template = Template.from_stack(network_stack)
    
    outputs = template.find_outputs("BedrockAgentCoreEndpointId")
    assert len(outputs) == 1
    
    endpoint_output = outputs["BedrockAgentCoreEndpointId"]
    assert endpoint_output["Description"] == "Bedrock AgentCore VPC Endpoint ID"
    assert endpoint_output["Export"]["Name"] == "BedrockAgentCoreEndpointId"
    assert "Value" in endpoint_output
```

**Contract Validation Patterns**:
- Output existence: `template.find_outputs(key)`
- Export name verification: `output["Export"]["Name"] == expected`
- Description consistency: `output["Description"] == expected`
- Value format: Use `Match.string_like_regexp()` for ARN/URL patterns

### Integration Tests

**Purpose**: Query deployed AWS infrastructure to validate live resources.

**Pattern**: boto3 clients + CloudFormation describe_stacks + pytest.skip for undeployed stacks

**When to Use**:
- Post-deployment validation
- E2E infrastructure testing
- Resource state verification (ACTIVE, available)
- Cross-service connectivity tests
- Trust policy and IAM role validation

**Example** (tests/integration/test_agentcore_e2e_deployment.py:24-31):
```python
@pytest.fixture
def stack_outputs(cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
        outputs = {o["OutputKey"]: o["OutputValue"] for o in response["Stacks"][0]["Outputs"]}
        return outputs
    except ClientError:
        pytest.skip("AgentCoreStack not deployed - skipping E2E tests")
```

**boto3 Query Patterns**:
```python
cloudformation_client.describe_stacks(StackName="StackName")
cloudformation_client.describe_stack_resources(StackName="StackName")
iam_client.get_role(RoleName=role_name)
iam_client.list_attached_role_policies(RoleName=role_name)
ec2_client.describe_vpc_endpoints(Filters=[...])
```

**Output Extraction Pattern** (tests/integration/test_agentcore_e2e_deployment.py:27):
```python
outputs = {o["OutputKey"]: o["OutputValue"] for o in response["Stacks"][0]["Outputs"]}
```

## 2. JSII Kernel State Management

### The Problem

JSII (JavaScript Interop Interface) maintains kernel state across CDK App instances. Reusing identical stack names causes conflicts when multiple tests create `App()` instances.

**Error Pattern**:
```
There is already a Construct with name 'NetworkStack' in App
```

**Root Cause**: The JSII kernel maintains a global registry of construct IDs across all `cdk.App()` instances created during a pytest session. When the same stack ID is reused in multiple tests, the kernel throws a "duplicate construct" error, even though each test creates its own `App()` instance.

### The Solution

Use UUID-based unique stack names in unit tests to avoid JSII kernel conflicts.

**Pattern** (from test_agentcore_validation.py):
```python
import uuid

def test_network_stack_validation():
    app = cdk.App()
    unique_id = str(uuid.uuid4())[:8]
    stack = NetworkStack(
        app,
        f"ValidationTestNetworkStack{unique_id}",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    template = Template.from_stack(stack)
```

**Key Points**:
- Use `uuid.uuid4()[:8]` for 8-character unique suffix
- Apply to ALL unit tests creating `cdk.App()` instances
- Not needed for session-scoped fixtures (see below)

### Session-Scoped Fixtures (Contract Tests)

For contract tests that share stack instances, use `scope="session"` to create the stack once per pytest session.

**Pattern** (tests/contract/test_agentcore_vpc_endpoint_contract.py:7-15):
```python
@pytest.fixture(scope="session")
def network_stack():
    app = cdk.App()
    stack = NetworkStack(
        app,
        "TestNetworkStack",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    return stack
```

**Benefits**:
- Single App/Stack instantiation per test session
- No JSII kernel conflicts across tests
- Faster test execution (stack synthesized once)
- Shared template for all contract tests
- No UUID needed (stack created only once)

### When to Use Each Pattern

| Test Type | Pattern | Reason |
|-----------|---------|--------|
| Unit tests (function scope) | UUID suffix | Multiple `App()` instances per session |
| Contract tests (session scope) | Static name | Single `App()` instance per session |
| Integration tests | N/A (boto3 only) | No CDK App creation |

## 3. Contract Validation Patterns

### YAML Contract Structure

Contracts define required CloudFormation outputs with validation rules.

**Example** (specs/008-add-aws-agentcore/contracts/agentcore-stack.yaml):
```yaml
outputs:
  AgentRuntimeArn:
    description: "ARN of the Bedrock AgentCore Runtime"
    export_name: "${ENVIRONMENT}-AgentRuntimeArn"
    format: "arn:aws:bedrock-agentcore:${AWS_REGION}:${AWS_ACCOUNT_ID}:runtime/${RUNTIME_ID}"
    required: true
  
  AgentRuntimeEndpointUrl:
    description: "HTTPS endpoint URL for the runtime"
    export_name: "AgentRuntimeEndpointUrl"
    format: "https://${RUNTIME_ID}.runtime.bedrock-agentcore.${AWS_REGION}.amazonaws.com"
    required: true
    validation:
      - pattern: "^https://"
      - pattern: "\.amazonaws\.com$"
```

### Test Implementation Patterns

**1. Output Existence**
```python
def test_output_exists(stack):
    template = Template.from_stack(stack)
    outputs = template.find_outputs("OutputKey")
    assert len(outputs) == 1
```

**2. Export Name Validation**
```python
def test_export_name(stack):
    template = Template.from_stack(stack)
    outputs = template.find_outputs("VpcId")
    assert outputs["VpcId"]["Export"]["Name"] == "VpcId"
```

**3. Description Validation**
```python
def test_output_description(stack):
    template = Template.from_stack(stack)
    outputs = template.find_outputs("VpcId")
    assert outputs["VpcId"]["Description"] == "VPC ID for the network stack"
```

**4. Format Validation (ARN/URL patterns)**
```python
import re

def test_arn_format(stack_outputs):
    runtime_arn = stack_outputs["AgentRuntimeArn"]
    pattern = r"^arn:aws:bedrock-agentcore:[a-z0-9-]+:[0-9]{12}:runtime/[a-zA-Z0-9-]+$"
    assert re.match(pattern, runtime_arn), f"Invalid ARN format: {runtime_arn}"

def test_endpoint_format(stack_outputs):
    endpoint_url = stack_outputs["AgentRuntimeEndpointUrl"]
    pattern = r"^https://[a-zA-Z0-9-]+\.runtime\.bedrock-agentcore\.[a-z0-9-]+\.amazonaws\.com$"
    assert re.match(pattern, endpoint_url), f"Invalid URL format: {endpoint_url}"
    assert endpoint_url.startswith("https://"), "Endpoint must use HTTPS"
```

**5. Resource Properties with Match**
```python
from aws_cdk.assertions import Match

def test_vpc_endpoint_properties(network_stack):
    template = Template.from_stack(network_stack)
    
    template.has_resource_properties(
        "AWS::EC2::VPCEndpoint",
        {
            "ServiceName": "com.amazonaws.us-east-1.bedrock-agentcore",
            "VpcEndpointType": "Interface",
            "PrivateDnsEnabled": True,
            "SubnetIds": Match.any_value()
        }
    )
```

**Match Matchers**:
- `Match.any_value()`: Any value acceptable
- `Match.string_like_regexp(pattern)`: Regex matching
- `Match.array_with([...])`: Array contains elements
- `Match.object_like({...})`: Object contains properties

## 4. boto3 Query Patterns

### CloudFormation Clients

**Stack Outputs** (tests/integration/test_agentcore_e2e_deployment.py:24-31):
```python
@pytest.fixture
def cloudformation_client():
    return boto3.client("cloudformation", region_name=os.getenv("AWS_REGION", "us-east-1"))

@pytest.fixture
def stack_outputs(cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
        outputs = {o["OutputKey"]: o["OutputValue"] for o in response["Stacks"][0]["Outputs"]}
        return outputs
    except ClientError:
        pytest.skip("AgentCoreStack not deployed - skipping E2E tests")
```

**Stack Resources**:
```python
response = cloudformation_client.describe_stack_resources(StackName="AgentCoreStack")
runtime_resource = next(
    (r for r in response["StackResources"] if r["ResourceType"] == "AWS::BedrockAgentCore::Runtime"),
    None
)
```

**Stack Exports**:
```python
exports = cloudformation_client.list_exports()
export_names = {e["Name"]: e["Value"] for e in exports["Exports"]}
assert "AgentRuntimeArn" in export_names
```

### IAM Clients

**Role Validation** (tests/integration/test_agentcore_e2e_deployment.py:95-104):
```python
@pytest.fixture
def iam_client():
    return boto3.client("iam", region_name=os.getenv("AWS_REGION", "us-east-1"))

def test_execution_role_exists(stack_outputs, iam_client):
    role_arn = stack_outputs["ExecutionRoleArn"]
    role_name = role_arn.split("/")[-1]
    
    try:
        response = iam_client.get_role(RoleName=role_name)
        assert response["Role"]["Arn"] == role_arn
    except ClientError as e:
        pytest.fail(f"Execution role not found: {e}")
```

**Trust Policy Validation** (tests/integration/test_agentcore_e2e_deployment.py:106-128):
```python
def test_execution_role_trust_policy(stack_outputs, iam_client):
    role_arn = stack_outputs["ExecutionRoleArn"]
    role_name = role_arn.split("/")[-1]
    
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response["Role"]["AssumeRolePolicyDocument"]
    
    principals = []
    for statement in trust_policy.get("Statement", []):
        if statement.get("Effect") == "Allow":
            principal = statement.get("Principal", {})
            if "Service" in principal:
                if isinstance(principal["Service"], list):
                    principals.extend(principal["Service"])
                else:
                    principals.append(principal["Service"])
    
    assert "bedrock-agentcore.amazonaws.com" in principals
```

**Policy Attachment** (tests/integration/test_agentcore_e2e_deployment.py:130-148):
```python
def test_execution_role_has_bedrock_policy(stack_outputs, iam_client):
    role_arn = stack_outputs["ExecutionRoleArn"]
    role_name = role_arn.split("/")[-1]
    
    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
    
    has_bedrock_permission = any("bedrock" in arn.lower() for arn in policy_arns)
    
    inline_policies = iam_client.list_role_policies(RoleName=role_name)
    
    assert has_bedrock_permission or len(inline_policies["PolicyNames"]) > 0
```

### EC2 Clients

**VPC Endpoints** (tests/integration/test_agentcore_e2e_deployment.py:178-210):
```python
@pytest.fixture
def ec2_client():
    return boto3.client("ec2", region_name=os.getenv("AWS_REGION", "us-east-1"))

def test_vpc_endpoints_accessible(stack_outputs, ec2_client):
    network_response = boto3.client("cloudformation").describe_stacks(
        StackName="NetworkStack"
    )
    network_outputs = {
        o["OutputKey"]: o["OutputValue"] 
        for o in network_response["Stacks"][0]["Outputs"]
    }
    
    vpc_id = network_outputs.get("VpcId")
    
    response = ec2_client.describe_vpc_endpoints(
        Filters=[
            {"Name": "vpc-id", "Values": [vpc_id]},
            {"Name": "service-name", "Values": [f"com.amazonaws.{os.getenv('AWS_REGION', 'us-east-1')}.bedrock-runtime"]},
        ]
    )
    
    assert len(response["VpcEndpoints"]) > 0
    
    for endpoint in response["VpcEndpoints"]:
        assert endpoint["State"] == "available"
```

## 5. Test Skip Strategies

### Fixture-Based Skipping (Recommended)

**Pattern**: Skip in fixture when dependency not met (tests/integration/test_agentcore_e2e_deployment.py:24-31):
```python
@pytest.fixture
def stack_outputs(cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
        outputs = {o["OutputKey"]: o["OutputValue"] for o in response["Stacks"][0]["Outputs"]}
        return outputs
    except ClientError:
        pytest.skip("AgentCoreStack not deployed - skipping E2E tests")
```

**Benefits**:
- All tests using the fixture automatically skip
- Single skip message for related tests
- Clean test output

### Test-Level Skipping

**Pattern**: Skip within test when specific condition not met (tests/integration/test_agentcore_e2e_deployment.py:80-87):
```python
def test_agent_runtime_status_active(stack_outputs):
    status = stack_outputs["AgentRuntimeStatus"]
    valid_statuses = ["CREATING", "ACTIVE", "UPDATING", "DELETING", "FAILED"]
    assert status in valid_statuses, f"Invalid status: {status}"
    
    if status != "ACTIVE":
        pytest.skip(f"Runtime status is {status}, expected ACTIVE for full validation")
```

**Use Cases**:
- Conditional validation based on resource state
- Tests that require specific configurations
- Optional validations that depend on deployment mode

### Dependency Stack Skipping

**Pattern**: Skip when dependency stacks not deployed (tests/integration/test_agentcore_e2e_deployment.py:275-288):
```python
def test_dependency_stacks_deployed(cloudformation_client):
    required_stacks = ["NetworkStack", "SecurityStack", "StorageStack"]
    
    for stack_name in required_stacks:
        try:
            response = cloudformation_client.describe_stacks(StackName=stack_name)
            assert len(response["Stacks"]) == 1
            assert response["Stacks"][0]["StackStatus"] in [
                "CREATE_COMPLETE",
                "UPDATE_COMPLETE",
            ]
        except ClientError:
            pytest.skip(f"Dependency stack {stack_name} not deployed")
```

### Network Mode Conditional Skipping

**Pattern**: Skip tests that only apply to specific configurations (tests/integration/test_agentcore_e2e_deployment.py:156-161):
```python
def test_vpc_mode_configuration(stack_outputs, cloudformation_client):
    network_mode = stack_outputs["NetworkMode"]
    
    if network_mode != "VPC":
        pytest.skip("Test only applicable for VPC network mode")
    
    # VPC-specific validation
```

## Best Practices Summary

### 1. Test Organization

```
tests/
├── unit/           # CDK template synthesis tests (no AWS)
├── contract/       # Output contract validation (no deployment)
└── integration/    # Live AWS resource validation (requires deployment)
```

### 2. Fixture Patterns

- **Unit tests**: No fixtures, create App + Stack per test
- **Contract tests**: `scope="session"` fixtures for shared stack instances
- **Integration tests**: boto3 client fixtures + stack_outputs fixture with skip logic

### 3. Common Pitfalls

❌ **Don't**: Reuse stack names across tests
```python
stack = NetworkStack(app, "NetworkStack")
```

✅ **Do**: Use unique names or session fixtures
```python
stack = NetworkStack(app, f"NetworkStack{uuid.uuid4()[:8]}")
```

❌ **Don't**: Assume infrastructure is deployed in integration tests
```python
response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
outputs = response["Stacks"][0]["Outputs"]
```

✅ **Do**: Use try/except with pytest.skip
```python
try:
    response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
    outputs = {o["OutputKey"]: o["OutputValue"] for o in response["Stacks"][0]["Outputs"]}
except ClientError:
    pytest.skip("AgentCoreStack not deployed")
```

❌ **Don't**: Hardcode AWS regions/accounts in tests
```python
env=cdk.Environment(account="123456789012", region="us-east-1")
```

✅ **Do**: Use environment variables or default to test values
```python
env=cdk.Environment(
    account=os.getenv("AWS_ACCOUNT_ID", "123456789012"),
    region=os.getenv("AWS_REGION", "us-east-1")
)
```

### 4. Test Execution

**Run all tests**:
```bash
PYTHONPATH=. pytest
```

**Run unit tests only** (fast, no AWS):
```bash
PYTHONPATH=. pytest tests/unit/
```

**Run contract tests** (medium, no deployment):
```bash
PYTHONPATH=. pytest tests/contract/
```

**Run integration tests** (slow, requires deployment):
```bash
export AWS_PROFILE=hackathon
export AWS_REGION=us-east-1
PYTHONPATH=. pytest tests/integration/
```

**Run specific test**:
```bash
PYTHONPATH=. pytest tests/unit/test_vpc_construct.py::test_vpc_construct -v
```

### 5. Continuous Integration Recommendations

**Pre-commit/PR checks**:
- ✅ Unit tests (always run)
- ✅ Contract tests (always run)
- ⚠️ Integration tests (run on demand or nightly)

**Deployment pipeline**:
1. Unit tests
2. Contract tests
3. CDK synth
4. CDK deploy (to staging)
5. Integration tests (against staging)
6. Promote to production

### 6. Documentation Requirements

Each test should be self-documenting:
- Clear function names: `test_bedrock_agentcore_endpoint_exists`
- Meaningful assertions: `assert status == "ACTIVE", f"Runtime status is {status}"`
- Skip messages: `pytest.skip("AgentCoreStack not deployed - skipping E2E tests")`
- Contract references: Link to YAML contract in test docstrings

### 7. Error Handling

**boto3 ClientError handling**:
```python
from botocore.exceptions import ClientError

try:
    response = client.describe_stacks(StackName="StackName")
except ClientError as e:
    if e.response['Error']['Code'] == 'ValidationError':
        pytest.skip("Stack not found")
    else:
        raise
```

**Assertion messages**:
```python
assert value, f"Expected {expected}, got {value}"
```

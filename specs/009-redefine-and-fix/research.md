# Research: Infrastructure Testing Best Practices

**Date**: 2025-10-15  
**Feature**: 009-redefine-and-fix  
**Purpose**: Resolve technical unknowns for properly categorizing and implementing IaC tests

## 1. Test Categorization in Infrastructure-as-Code

### Decision: Three-Tier Testing Approach

**Unit Tests** → **Contract Tests** → **Integration Tests**

### Rationale

Infrastructure testing requires different levels of validation:

1. **Unit Tests**: Fast feedback during development without AWS deployment
2. **Contract Tests**: Validate CloudFormation outputs match documented contracts (still template-based, no deployment)
3. **Integration Tests**: Validate actual deployed resources and behaviors

### Implementation Details

#### Unit Tests
- **Tool**: `Template.from_stack()` from `aws_cdk.assertions`
- **No AWS credentials required**
- **Speed**: <5 seconds per stack
- **Purpose**: Resource count, property validation, template structure

**Example Pattern**:
```python
def test_vpc_construct():
    app = cdk.App()
    stack = NetworkStack(app, "TestStack")
    template = Template.from_stack(stack)
    
    template.resource_count_is("AWS::EC2::VPC", 1)
    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.0.0.0/16",
        "EnableDnsHostnames": True
    })
```

#### Contract Tests
- **Tool**: `Template.from_stack()` + YAML contract specifications
- **No AWS credentials required**
- **Speed**: <10 seconds per stack (session-scoped fixtures)
- **Purpose**: Validate outputs exist, have correct export names, descriptions, and formats

**Example Pattern**:
```python
@pytest.fixture(scope="session")
def agentcore_stack():
    app = cdk.App()
    stack = AgentCoreStack(app, "TestAgentCoreStack", ...)
    return stack

def test_agentcore_runtime_arn_output(agentcore_stack):
    template = Template.from_stack(agentcore_stack)
    outputs = template.find_outputs("AgentRuntimeArn")
    
    assert len(outputs) == 1
    assert outputs["AgentRuntimeArn"]["Description"] == "ARN of the deployed AWS Bedrock AgentCore runtime"
    assert outputs["AgentRuntimeArn"]["Export"]["Name"] == "${Environment}-AgentRuntimeArn"
```

#### Integration Tests
- **Tool**: boto3 CloudFormation/IAM/EC2 clients
- **Requires AWS credentials and deployed stacks**
- **Speed**: 1-5 minutes (network calls, resource queries)
- **Purpose**: Validate deployed resources, cross-service connectivity, runtime behavior

**Example Pattern**:
```python
@pytest.fixture
def cloudformation_client():
    return boto3.client("cloudformation", region_name="us-east-1")

@pytest.fixture
def stack_outputs(cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
        return {o["OutputKey"]: o["OutputValue"] for o in response["Stacks"][0]["Outputs"]}
    except ClientError:
        pytest.skip("AgentCoreStack not deployed - skipping integration tests")

def test_agent_runtime_active(stack_outputs):
    assert stack_outputs["AgentRuntimeStatus"] == "ACTIVE"
```

### Alternatives Considered

**Two-tier approach (unit + integration)**: Rejected because contract validation is valuable pre-deployment and doesn't require AWS resources. Separating contracts from unit tests makes expectations explicit.

**Four-tier approach (unit + contract + integration + e2e)**: Rejected as overly complex for infrastructure testing. Integration tests can cover e2e scenarios.

---

## 2. JSII Kernel State Management

### Decision: UUID-Based Unique Stack Names

Every test creating a CDK stack must use a unique stack name with UUID suffix.

### Rationale

**The Problem**: JSII (JavaScript Interop) maintains a global Node.js process bridging Python CDK code to TypeScript libraries. When multiple tests create `cdk.App()` instances with identical stack names, JSII sees duplicate construct IDs in the global construct tree, causing:

```
RuntimeError: There is already a Construct with name 'NetworkStack' in App
```

This happens even when:
- Tests run sequentially (not parallel)
- Different `App()` instances are created
- Tests are in different modules

**Root Cause**: The JSII kernel maintains global state across Python `cdk.App()` instances. Stack names must be globally unique within a test session.

### Implementation

```python
import uuid

def test_network_validation():
    app = cdk.App()
    unique_id = str(uuid.uuid4())[:8]  # 8-char UUID suffix
    
    stack = NetworkStack(
        app,
        f"ValidationTestNetworkStack{unique_id}",
        env=cdk.Environment(account="123456789012", region="us-east-1")
    )
    
    template = Template.from_stack(stack)
    # ... assertions
```

**Exception**: Session-scoped fixtures can reuse stack names because they create stacks once per test session:

```python
@pytest.fixture(scope="session")
def network_stack():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack", ...)  # OK - created once
    return stack
```

### Alternatives Considered

1. **Separate JSII processes per test**: Rejected - not supported by aws-cdk Python bindings
2. **Test isolation with subprocess**: Rejected - too slow, complicates fixture sharing
3. **Session-scoped fixtures everywhere**: Rejected - limits test independence, makes debugging harder

---

## 3. Contract Validation Patterns

### Decision: YAML Contracts + Template Assertion Pattern

Define contracts in YAML files under `specs/*/contracts/`, validate using `Template.from_stack()` assertions.

### Rationale

YAML contracts serve as:
- **Documentation**: Single source of truth for required outputs
- **Validation specs**: Machine-readable format for automated testing
- **Cross-team communication**: Contract between infrastructure and application teams

### Implementation Pattern

**Contract YAML** (`specs/008-add-aws-agentcore/contracts/agentcore-stack.yaml`):
```yaml
outputs:
  AgentRuntimeArn:
    description: "ARN of the deployed AWS Bedrock AgentCore runtime"
    exportName: "${Environment}-AgentRuntimeArn"
    format: "arn:aws:bedrock-agentcore:<region>:<account>:runtime/<runtime-id>"
    validation:
      - type: regex
        pattern: "^arn:aws:bedrock-agentcore:[a-z0-9-]+:[0-9]{12}:runtime/[a-zA-Z0-9-]+$"
      - type: required
```

**Contract Test**:
```python
def test_agentcore_runtime_arn_output(agentcore_stack):
    template = Template.from_stack(agentcore_stack)
    outputs = template.find_outputs("AgentRuntimeArn")
    
    # Existence check
    assert len(outputs) == 1, "AgentRuntimeArn output missing"
    
    # Description check
    arn_output = outputs["AgentRuntimeArn"]
    assert arn_output["Description"] == "ARN of the deployed AWS Bedrock AgentCore runtime"
    
    # Export name check
    assert arn_output["Export"]["Name"] == "${Environment}-AgentRuntimeArn"
    
    # Value existence
    assert "Value" in arn_output
```

**Format validation** (integration test using deployed resources):
```python
import re

def test_agentcore_runtime_arn_format(stack_outputs):
    runtime_arn = stack_outputs["AgentRuntimeArn"]
    pattern = r"^arn:aws:bedrock-agentcore:[a-z0-9-]+:[0-9]{12}:runtime/[a-zA-Z0-9-]+$"
    assert re.match(pattern, runtime_arn), f"Invalid ARN format: {runtime_arn}"
```

### Benefits

- **Pre-deployment validation**: Catches missing/misnamed outputs before AWS deployment
- **Contract-driven development**: Outputs defined before implementation
- **Cross-stack references**: Validates export names match consumer expectations
- **Regression prevention**: Contract changes require explicit updates

---

## 4. boto3 Query Patterns for Deployed Infrastructure

### Decision: Fixture-Based boto3 Clients + Output Dictionary Pattern

Use pytest fixtures to create boto3 clients and extract CloudFormation outputs into dictionaries.

### Rationale

Consistent patterns reduce boilerplate, improve readability, and enable fixture-level skipping when stacks aren't deployed.

### Implementation Patterns

#### CloudFormation Stack Outputs

```python
@pytest.fixture
def cloudformation_client():
    return boto3.client("cloudformation", region_name=os.getenv("AWS_REGION", "us-east-1"))

@pytest.fixture
def agentcore_stack_outputs(cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
        outputs = {o["OutputKey"]: o["OutputValue"] for o in response["Stacks"][0]["Outputs"]}
        return outputs
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            pytest.skip("AgentCoreStack not deployed - skipping integration tests")
        raise
```

**Usage**:
```python
def test_runtime_arn_exists(agentcore_stack_outputs):
    assert "AgentRuntimeArn" in agentcore_stack_outputs
    assert agentcore_stack_outputs["AgentRuntimeArn"].startswith("arn:aws:bedrock-agentcore")
```

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
                principals.extend(services if isinstance(services, list) else [services])
    
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
            {"Name": "service-name", "Values": ["com.amazonaws.us-east-1.bedrock-agentcore"]}
        ]
    )
    
    assert len(response["VpcEndpoints"]) > 0, "Bedrock VPC endpoint not found"
    endpoint = response["VpcEndpoints"][0]
    assert endpoint["State"] == "available", f"Endpoint state: {endpoint['State']}"
```

### Error Handling Pattern

```python
from botocore.exceptions import ClientError

try:
    response = client.describe_resource(...)
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'ValidationError':
        pytest.skip("Resource not found - skipping test")
    elif error_code == 'ResourceNotFoundException':
        pytest.fail("Expected resource not found")
    else:
        raise
```

---

## 5. Test Skip Strategies

### Decision: Fixture-Level Skipping for Missing Infrastructure

Skip in fixtures when AWS resources aren't deployed, allowing all dependent tests to skip gracefully.

### Rationale

- **Better UX**: Single clear skip message instead of multiple failures
- **Cleaner output**: `SKIPPED (AgentCoreStack not deployed)` vs `ERROR (Stack not found)`
- **Faster execution**: Tests skip immediately without attempting resource queries
- **Explicit dependencies**: Fixtures document required infrastructure

### Implementation Patterns

#### Fixture-Level Skip (Recommended)

```python
@pytest.fixture
def agentcore_stack_outputs(cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
        return {o["OutputKey"]: o["OutputValue"] for o in response["Stacks"][0]["Outputs"]}
    except ClientError as e:
        pytest.skip("AgentCoreStack not deployed - skipping integration tests")
```

All tests using this fixture automatically skip if the stack doesn't exist.

#### Test-Level Conditional Skip

```python
def test_vpc_mode_configuration(agentcore_stack_outputs):
    network_mode = agentcore_stack_outputs.get("NetworkMode", "PUBLIC")
    
    if network_mode != "VPC":
        pytest.skip("Test only applicable for VPC network mode")
    
    # VPC-specific validation
    assert "VpcId" in agentcore_stack_outputs
```

Use when skip condition depends on deployment configuration, not existence.

#### Dependency Stack Skip

```python
def test_dependency_stacks_deployed(cloudformation_client):
    required_stacks = ["NetworkStack", "SecurityStack", "StorageStack"]
    
    for stack_name in required_stacks:
        try:
            response = cloudformation_client.describe_stacks(StackName=stack_name)
            assert response["Stacks"][0]["StackStatus"] in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]
        except ClientError:
            pytest.skip(f"Dependency stack {stack_name} not deployed")
```

#### State-Based Skip

```python
def test_agent_runtime_invocation(agentcore_stack_outputs, bedrock_client):
    status = agentcore_stack_outputs["AgentRuntimeStatus"]
    
    if status != "ACTIVE":
        pytest.skip(f"Runtime status is {status}, expected ACTIVE for invocation tests")
    
    # Perform runtime invocation
```

### CI/CD Integration

**GitHub Actions workflow**:
```yaml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/unit/  # Always run, no AWS needed
  
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/contract/  # Always run, no AWS needed
  
  integration-tests:
    runs-on: ubuntu-latest
    needs: [deploy-to-staging]
    steps:
      - run: pytest tests/integration/  # Only after deployment
```

---

## Summary of Decisions

| Area | Decision | Key Pattern |
|------|----------|-------------|
| **Test Categories** | Three-tier: Unit/Contract/Integration | `tests/unit/`, `tests/contract/`, `tests/integration/` |
| **JSII Conflicts** | UUID-based unique stack names | `f"Stack{uuid.uuid4()[:8]}"` |
| **Contract Validation** | YAML contracts + Template assertions | `template.find_outputs(key)` + assertions |
| **boto3 Queries** | Fixture-based clients + output dicts | `@pytest.fixture def stack_outputs(...)` |
| **Skip Strategy** | Fixture-level skip for missing stacks | `pytest.skip("Stack not deployed")` in fixture |

## Implementation Checklist

- [x] Categorize existing tests into unit/contract/integration
- [ ] Rewrite contract tests to query deployed resources via boto3
- [x] Fix JSII conflicts with UUID naming (already done in test_agentcore_validation.py)
- [ ] Create integration tests for agent runtime invocation
- [ ] Document patterns in quickstart.md
- [ ] Update CI/CD to separate test execution stages

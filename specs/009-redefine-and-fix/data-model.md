# Data Model: Test Suite Entities

**Feature**: 009-redefine-and-fix  
**Date**: 2025-10-15  
**Purpose**: Define test entity types and their relationships

## Overview

This data model defines the structure and relationships of different test types in the infrastructure testing suite. Tests are categorized by their validation approach and AWS dependency requirements.

## Core Entities

### UnitTest

**Purpose**: Validates CloudFormation template structure without AWS deployment

**Properties**:
- `test_name` (string): Descriptive test function name (e.g., `test_agentcore_stack_synth_public_mode`)
- `stack_type` (string): CDK stack being tested (e.g., `AgentCoreStack`, `NetworkStack`)
- `validates` (list[string]): What the test validates (e.g., `["resource_count", "resource_properties", "outputs"]`)
- `requires_aws` (boolean): Always `false` for unit tests
- `execution_time` (string): Expected duration (e.g., `<5s`)
- `uses_fixtures` (boolean): Whether pytest fixtures are used
- `unique_naming_required` (boolean): Whether stack name must include UUID

**Relationships**:
- Uses **TestAssertion** entities to validate template
- May depend on **TestFixture** for stack creation

**Example**:
```python
test_name = "test_agentcore_stack_synth_public_mode"
stack_type = "AgentCoreStack"
validates = ["resource_count", "network_mode_property"]
requires_aws = False
execution_time = "<5s"
uses_fixtures = False
unique_naming_required = True  # UUID suffix to avoid JSII conflicts
```

**File Location**: `tests/unit/test_*.py`

---

### ContractTest

**Purpose**: Validates deployed CloudFormation outputs and AWS resources match contract specifications

**Properties**:
- `test_name` (string): Descriptive test function name (e.g., `test_agentcore_runtime_arn_output`)
- `contract_file` (string): Path to YAML contract (e.g., `specs/008-add-aws-agentcore/contracts/agentcore-stack.yaml`)
- `stack_name` (string): CloudFormation stack to query (e.g., `AgentCoreStack`)
- `validates` (list[string]): Validation types (e.g., `["output_existence", "arn_format", "export_name"]`)
- `requires_aws` (boolean): Always `true` for contract tests
- `requires_deployment` (boolean): Always `true` - stack must be deployed
- `execution_time` (string): Expected duration (e.g., `<30s`)
- `aws_resource_type` (string): AWS resource queried (e.g., `CloudFormation::Stack`, `IAM::Role`, `EC2::VPCEndpoint`)
- `boto3_client` (string): boto3 client used (e.g., `cloudformation`, `iam`, `ec2`)

**Relationships**:
- References **TestContract** YAML specification
- Uses **boto3Client** fixture
- Depends on **StackOutputs** fixture
- May trigger **SkipCondition** if stack not deployed

**Example**:
```python
test_name = "test_agentcore_runtime_arn_output"
contract_file = "specs/008-add-aws-agentcore/contracts/agentcore-stack.yaml"
stack_name = "AgentCoreStack"
validates = ["output_existence", "arn_format", "export_name"]
requires_aws = True
requires_deployment = True
execution_time = "<30s"
aws_resource_type = "CloudFormation::Stack"
boto3_client = "cloudformation"
```

**File Location**: `tests/contract/test_*_contract.py`

---

### IntegrationTest

**Purpose**: Validates end-to-end behavior and cross-service connectivity

**Properties**:
- `test_name` (string): Descriptive test function name (e.g., `test_agent_runtime_invocation`)
- `operation_type` (string): Type of operation tested (e.g., `invocation`, `connection`, `failover`)
- `dependencies` (list[string]): Required stacks (e.g., `["AgentCoreStack", "NetworkStack"]`)
- `validates` (list[string]): Behaviors validated (e.g., `["runtime_active", "bedrock_accessible", "vpc_connectivity"]`)
- `requires_aws` (boolean): Always `true`
- `requires_deployment` (boolean): Always `true`
- `execution_time` (string): Expected duration (e.g., `1-5min`)
- `aws_operations` (list[string]): AWS operations performed (e.g., `["bedrock:InvokeModel", "ec2:DescribeVpcEndpoints"]`)
- `skip_conditions` (list[string]): Conditions that trigger skip (e.g., `["runtime_status != ACTIVE", "network_mode != VPC"]`)

**Relationships**:
- Depends on multiple **StackOutputs** fixtures
- Uses multiple **boto3Client** fixtures
- May trigger **SkipCondition** based on state
- Validates **TestContract** behavioral requirements

**Example**:
```python
test_name = "test_agent_runtime_vpc_access"
operation_type = "connection"
dependencies = ["AgentCoreStack", "NetworkStack"]
validates = ["vpc_connectivity", "private_subnet_access"]
requires_aws = True
requires_deployment = True
execution_time = "1-5min"
aws_operations = ["ec2:DescribeVpcEndpoints", "sts:AssumeRole"]
skip_conditions = ["network_mode != VPC", "runtime_status != ACTIVE"]
```

**File Location**: `tests/integration/test_*.py`

---

### TestContract

**Purpose**: YAML specification defining required CloudFormation outputs and validation rules

**Properties**:
- `output_name` (string): CloudFormation output key (e.g., `AgentRuntimeArn`)
- `description` (string): Human-readable description (e.g., `"ARN of the deployed AWS Bedrock AgentCore runtime"`)
- `export_name` (string): CloudFormation export name (e.g., `"${Environment}-AgentRuntimeArn"`)
- `format` (string): Expected format pattern (e.g., `"arn:aws:bedrock-agentcore:<region>:<account>:runtime/<runtime-id>"`)
- `required` (boolean): Whether output is mandatory
- `validation_rules` (list[ValidationRule]): Rules to validate against

**ValidationRule Properties**:
- `type` (string): Validation type (e.g., `regex`, `enum`, `required`, `https_only`)
- `pattern` (string): Regex pattern (for `type: regex`)
- `values` (list[string]): Allowed values (for `type: enum`)
- `message` (string): Error message if validation fails

**Relationships**:
- Referenced by **ContractTest** entities
- Validated by **TestAssertion** in contract tests

**Example** (YAML):
```yaml
outputs:
  AgentRuntimeArn:
    description: "ARN of the deployed AWS Bedrock AgentCore runtime"
    export_name: "${Environment}-AgentRuntimeArn"
    format: "arn:aws:bedrock-agentcore:<region>:<account>:runtime/<runtime-id>"
    required: true
    validation_rules:
      - type: regex
        pattern: "^arn:aws:bedrock-agentcore:[a-z0-9-]+:[0-9]{12}:runtime/[a-zA-Z0-9-]+$"
        message: "Invalid ARN format"
      - type: required
        message: "AgentRuntimeArn is required for runtime invocation"
```

**File Location**: `specs/*/contracts/*.yaml`

---

### TestFixture

**Purpose**: pytest fixture providing test dependencies (CDK stacks, boto3 clients, stack outputs)

**Properties**:
- `fixture_name` (string): Fixture function name (e.g., `agentcore_stack`, `cloudformation_client`, `stack_outputs`)
- `scope` (string): pytest fixture scope (e.g., `session`, `function`, `module`)
- `creates_resources` (boolean): Whether fixture creates AWS/CDK resources
- `resource_type` (string): Type of resource created (e.g., `CDK::Stack`, `boto3::Client`, `dict`)
- `naming_strategy` (string): How resources are named (e.g., `uuid_suffix`, `static`, `session_unique`)
- `requires_aws` (boolean): Whether fixture needs AWS credentials
- `skip_condition` (string|null): Condition that triggers pytest.skip (e.g., `"Stack not deployed"`)

**Fixture Types**:

1. **CDK Stack Fixtures** (for unit/contract tests):
   ```python
   @pytest.fixture(scope="session")
   def agentcore_stack():
       app = cdk.App()
       stack = AgentCoreStack(app, "TestAgentCoreStack", ...)
       return stack
   ```

2. **boto3 Client Fixtures** (for contract/integration tests):
   ```python
   @pytest.fixture
   def cloudformation_client():
       return boto3.client("cloudformation", region_name="us-east-1")
   ```

3. **Stack Output Fixtures** (for contract/integration tests):
   ```python
   @pytest.fixture
   def stack_outputs(cloudformation_client):
       try:
           response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
           return {o["OutputKey"]: o["OutputValue"] for o in response["Stacks"][0]["Outputs"]}
       except ClientError:
           pytest.skip("AgentCoreStack not deployed")
   ```

**Relationships**:
- Used by **UnitTest**, **ContractTest**, **IntegrationTest**
- May trigger **SkipCondition**
- Creates **CDKStack** or **boto3Client** instances

---

### TestAssertion

**Purpose**: Validation logic used in tests

**Types**:

1. **Template Assertions** (CDK):
   - `resource_count_is(type, count)`
   - `has_resource_properties(type, properties)`
   - `find_outputs(key)`
   - `Match.string_like_regexp(pattern)`
   - `Match.array_with(items)`
   - `Match.object_like(properties)`

2. **boto3 Assertions**:
   - Output existence: `assert "OutputKey" in outputs`
   - Format validation: `assert re.match(pattern, value)`
   - Status validation: `assert status == "ACTIVE"`
   - Resource state: `assert endpoint["State"] == "available"`

3. **Contract Assertions**:
   - Description check: `assert output["Description"] == expected`
   - Export name check: `assert output["Export"]["Name"] == expected`
   - Value existence: `assert "Value" in output`

**Relationships**:
- Used by all test types
- Validates **TestContract** rules
- Throws **AssertionError** on failure

---

### SkipCondition

**Purpose**: Condition that causes a test to be skipped

**Properties**:
- `condition_type` (string): Type of skip (e.g., `stack_not_deployed`, `wrong_network_mode`, `runtime_not_active`)
- `check_location` (string): Where check occurs (e.g., `fixture`, `test_body`)
- `skip_message` (string): Message shown when skipped (e.g., `"AgentCoreStack not deployed - skipping integration tests"`)
- `exception_type` (string): Exception caught (e.g., `ClientError`, `KeyError`)

**Common Skip Conditions**:

1. **Stack Not Deployed**:
   ```python
   try:
       response = client.describe_stacks(StackName="AgentCoreStack")
   except ClientError:
       pytest.skip("AgentCoreStack not deployed")
   ```

2. **Wrong Configuration**:
   ```python
   if network_mode != "VPC":
       pytest.skip("Test only applicable for VPC network mode")
   ```

3. **Invalid State**:
   ```python
   if status != "ACTIVE":
       pytest.skip(f"Runtime status is {status}, expected ACTIVE")
   ```

**Relationships**:
- Triggered by **TestFixture** or **Test** functions
- Prevents **TestAssertion** execution
- Results in pytest SKIPPED status

---

## Entity Relationships

```
TestContract (YAML)
    ↓ referenced by
ContractTest
    ↓ uses
TestFixture (boto3Client, StackOutputs)
    ↓ may trigger
SkipCondition
    ↓ prevents
TestAssertion

UnitTest
    ↓ uses
TestFixture (CDK Stack - session scope)
    ↓ validates with
TestAssertion (Template.from_stack)

IntegrationTest
    ↓ uses
TestFixture (boto3Client, StackOutputs) × multiple stacks
    ↓ may trigger
SkipCondition
    ↓ validates with
TestAssertion (boto3 queries)
```

## Test Execution Flow

### Unit Test Flow
1. Create `cdk.App()` with unique stack name (UUID suffix)
2. Instantiate CDK stack
3. Generate CloudFormation template via `Template.from_stack()`
4. Execute assertions on template
5. No AWS credentials required

### Contract Test Flow
1. Create CDK stack via session-scoped fixture (once per test session)
2. Generate CloudFormation template
3. Load YAML contract specification
4. Assert outputs exist with correct descriptions, export names
5. No AWS deployment required

### Integration Test Flow
1. Create boto3 client fixtures
2. Query CloudFormation stack outputs (skip if not deployed)
3. Extract output values into dictionary
4. Perform AWS resource queries (IAM, EC2, etc.)
5. Execute behavioral assertions (status, connectivity, policies)
6. Requires AWS deployment and credentials

## Test Organization

```
tests/
├── unit/
│   ├── test_agentcore_stack_synth.py      # UnitTest entities
│   ├── test_agentcore_validation.py       # UnitTest entities (validation logic)
│   └── test_vpc_construct.py              # UnitTest entities
│
├── contract/
│   ├── test_agentcore_runtime_contract.py     # ContractTest entities
│   ├── test_agentcore_execution_role_contract.py  # ContractTest entities
│   └── test_vpc_contract.py                   # ContractTest entities
│
└── integration/
    ├── test_agentcore_e2e_deployment.py   # IntegrationTest entities
    ├── test_agentcore_vpc_access.py       # IntegrationTest entities
    └── test_bedrock_access.py             # IntegrationTest entities
```

## Contract Files

```
specs/008-add-aws-agentcore/contracts/
├── agentcore-stack.yaml               # TestContract entities for AgentCore outputs
├── execution-role-permissions.json    # Expected IAM policy document
├── execution-role-trust.json          # Expected trust policy document
└── vpc-endpoint-policy.json           # Expected VPC endpoint policy
```

## Summary

- **UnitTest**: Fast, no AWS, validates templates
- **ContractTest**: Medium speed, requires deployment, validates outputs match contracts
- **IntegrationTest**: Slow, requires deployment, validates behavior
- **TestContract**: YAML spec defining output requirements
- **TestFixture**: pytest fixture providing dependencies
- **TestAssertion**: Validation logic
- **SkipCondition**: Graceful skip when prerequisites not met

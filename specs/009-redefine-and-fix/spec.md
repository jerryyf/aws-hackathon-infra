# Feature Specification: Redefine and Fix AgentCore Test Suite

**Feature Branch**: `009-redefine-and-fix`  
**Created**: 2025-10-15  
**Status**: Draft  
**Input**: User description: "redefine and fix ALL the tests for 008-add-aws-agentcore"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate CloudFormation Templates During Development (Priority: P1)

As a developer, I need to validate that my CDK code produces correct CloudFormation templates so that I can catch configuration errors before deployment and ensure infrastructure matches specifications.

**Why this priority**: Fastest feedback loop - runs in seconds without AWS credentials or deployed resources. Catches 80% of configuration errors during development. Essential for CI/CD pipeline efficiency.

**Independent Test**: Can be fully tested by running `pytest tests/unit/` which synthesizes CDK stacks and validates template structure without requiring AWS deployment. Delivers immediate feedback on CloudFormation correctness.

**Acceptance Scenarios**:

1. **Given** CDK stack code with syntax or configuration errors, **When** unit tests run, **Then** tests fail with clear error messages identifying the problem
2. **Given** valid CDK stack code, **When** unit tests validate resource properties, **Then** tests verify resources have correct configurations (VPC CIDR, subnet counts, IAM permissions)
3. **Given** CDK stack outputs are required by contract, **When** unit tests check outputs, **Then** tests verify all required outputs exist with correct export names

---

### User Story 2 - Validate Deployed Infrastructure Against Contracts (Priority: P2)

As a DevOps engineer, I need to verify that deployed AWS infrastructure matches documented contracts so that I can ensure production deployments meet architectural requirements and integration expectations.

**Why this priority**: Validates actual AWS resources post-deployment. Critical for production readiness but requires deployed infrastructure (can't run during development). Complements P1 unit tests with real-world validation.

**Independent Test**: Can be tested by deploying stacks to AWS and running `pytest tests/contract/` which queries CloudFormation outputs and AWS resources to validate they match contract specifications. Delivers confidence that deployed infrastructure is correct.

**Acceptance Scenarios**:

1. **Given** a deployed CloudFormation stack, **When** contract tests query stack outputs, **Then** all required outputs exist and match format specifications (ARN patterns, URL formats, enum values)
2. **Given** a contract specifying resource properties (VPC CIDR, subnet AZs), **When** contract tests query AWS resources directly, **Then** actual resources match contract specifications
3. **Given** a stack with missing required outputs, **When** contract tests run, **Then** tests fail with clear messages identifying missing outputs

---

### User Story 3 - Test Cross-Stack Integration Behavior (Priority: P2)

As a platform engineer, I need to verify that multiple stacks integrate correctly so that I can ensure VPC networking, database connectivity, and agent runtime access work end-to-end in deployed environments.

**Why this priority**: Tests realistic scenarios spanning multiple AWS services. Essential for production confidence but slower than unit/contract tests. Can only run after P2 contract tests pass.

**Independent Test**: Can be tested by running `pytest tests/integration/` which performs actual operations (database connections, agent invocations, multi-AZ failover) against deployed infrastructure. Delivers proof that the system works as a whole.

**Acceptance Scenarios**:

1. **Given** a deployed agent runtime in VPC mode, **When** integration tests invoke the runtime from within the VPC, **Then** invocations succeed with valid session IDs
2. **Given** a deployed RDS instance in private subnets, **When** integration tests attempt database connections from agent runtime subnets, **Then** connections succeed with proper security group rules
3. **Given** a multi-AZ deployment, **When** integration tests simulate an AZ failure, **Then** the system continues operating using resources in healthy AZs

---

### User Story 4 - Validate Input Parameters and Error Conditions (Priority: P3)

As a quality engineer, I need to test that infrastructure code properly validates inputs and handles error conditions so that invalid configurations are caught during synthesis rather than causing deployment failures.

**Why this priority**: Improves developer experience by providing fast validation feedback. Not critical for basic functionality but prevents frustrating deployment failures. Can be implemented after P1 works.

**Independent Test**: Can be tested by running validation-specific unit tests that pass invalid parameters to CDK stacks and verify proper error handling. Delivers better error messages and prevents invalid deployments.

**Acceptance Scenarios**:

1. **Given** invalid CPU/memory ratio for agent runtime, **When** CDK synthesis runs, **Then** synthesis fails with clear validation error before attempting deployment
2. **Given** VPC network mode without required VPC stack reference, **When** CDK synthesis runs, **Then** synthesis fails identifying missing dependency
3. **Given** special characters in environment name, **When** stack instantiation occurs, **Then** validation error indicates invalid characters and allowed format

---

### Edge Cases

- **JSII kernel global state pollution**: Multiple test modules creating stacks with identical names causes construct ID conflicts even across different App instances; each test must use unique stack names via UUID suffix
- **Missing AWS credentials**: Unit tests that only validate CloudFormation templates must not require AWS credentials or boto3 calls
- **Contract tests run without deployed infrastructure**: Tests must skip gracefully or fail clearly when CloudFormation stacks don't exist (not generic boto3 errors)
- **Parallel test execution**: Tests creating stacks with same names running in parallel cause JSII conflicts; unique naming prevents this
- **Session-scoped vs function-scoped fixtures**: Session-scoped fixtures creating stacks conflict with function-scoped fixtures; remove duplicate fixtures

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Unit tests MUST validate CloudFormation template synthesis without requiring AWS deployment or credentials
- **FR-002**: Contract tests MUST query actual CloudFormation stack outputs and AWS resources to validate deployed infrastructure
- **FR-003**: Integration tests MUST perform real operations (invocations, connections, failover tests) against deployed resources
- **FR-004**: All test stack names MUST be unique using UUID suffix to prevent JSII kernel construct ID conflicts
- **FR-005**: Tests MUST clearly distinguish between unit tests (template validation), contract tests (deployment validation), and integration tests (behavior validation)
- **FR-006**: Contract tests MUST validate all outputs defined in contract YAML files (`specs/008-add-aws-agentcore/contracts/*.yaml`)
- **FR-007**: Contract tests MUST fail with descriptive error messages when stacks are not deployed rather than generic boto3 exceptions
- **FR-008**: Unit tests MUST validate input parameter validation logic catches invalid configurations during CDK synthesis
- **FR-009**: Integration tests MUST verify multi-AZ resilience by testing AZ failure scenarios
- **FR-010**: Tests MUST follow pytest naming conventions (`test_*.py`) and be organized by test type (`tests/unit/`, `tests/contract/`, `tests/integration/`)
- **FR-011**: All AgentCore-related tests MUST be clearly named to indicate what they validate (e.g., `test_agentcore_execution_role_permissions` not `test_role`)

### Key Entities

- **Unit Test**: Validates CloudFormation template structure using `Template.from_stack()`; runs without AWS deployment; fast (seconds)
- **Contract Test**: Validates deployed CloudFormation outputs and AWS resources match contract specifications; requires deployed stacks; medium speed (10-30 seconds per stack)
- **Integration Test**: Validates end-to-end behavior across multiple AWS services; requires deployed infrastructure; slow (1-5 minutes)
- **Test Contract**: YAML specification defining required CloudFormation outputs, resource properties, and validation rules (stored in `specs/*/contracts/`)
- **Test Fixture**: Pytest fixture creating CDK stacks or AWS clients; must use unique names to avoid JSII conflicts

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Unit tests complete in under 30 seconds for full AgentCore test suite
- **SC-002**: Contract tests complete in under 2 minutes when all stacks are deployed
- **SC-003**: Integration tests complete in under 10 minutes for full end-to-end validation
- **SC-004**: 100% of tests pass when run locally and in GitHub Actions CI without JSII kernel conflicts
- **SC-005**: Contract tests provide clear error messages identifying missing outputs within 5 seconds when stacks are not deployed
- **SC-006**: Tests can run in parallel using `pytest -n auto` without causing JSII construct ID conflicts
- **SC-007**: Zero false positives - contract tests only pass when infrastructure actually matches contracts (no mislabeled unit tests passing without deployment)

## Assumptions

- Developers run unit tests locally during development before pushing to CI
- Contract tests run only after successful CDK deployment (either manual or via CI/CD)
- Integration tests run as final validation step before production deployment
- Test execution order is: unit tests → deployment → contract tests → integration tests
- All test files are discoverable by pytest default discovery (matching `test_*.py` or `*_test.py`)
- Test environment has pytest, aws-cdk, and boto3 installed in virtual environment
- GitHub Actions CI runner has AWS credentials configured for contract and integration tests
- Contract YAML files are the source of truth for required CloudFormation outputs
- Python version 3.13.3 on GitHub Actions CI runner

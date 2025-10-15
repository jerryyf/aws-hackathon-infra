# Implementation Plan: Redefine and Fix AgentCore Test Suite

**Branch**: `009-redefine-and-fix` | **Date**: 2025-10-15 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/009-redefine-and-fix/spec.md`

## Summary

Redefine and restructure the AgentCore test suite to properly separate unit tests (CloudFormation template validation), contract tests (deployed infrastructure validation), and integration tests (end-to-end behavior validation). Current tests in `tests/contract/` are misnamed - they use `Template.from_stack()` and don't query actual AWS resources, making them unit tests. Additionally, fix JSII kernel global state conflicts caused by duplicate stack names across test modules. The result will be a properly organized test suite with clear boundaries: unit tests run without AWS credentials and validate synthesized templates; contract tests query real CloudFormation outputs and AWS resources; integration tests perform actual operations against deployed infrastructure.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: pytest 8.x, aws-cdk 2.x, boto3 1.x, aws-cdk.assertions  
**Storage**: N/A (tests validate infrastructure, don't persist data)  
**Testing**: pytest with parallel execution support (pytest-xdist), contract validation against YAML specs  
**Target Platform**: Linux/macOS development environments, GitHub Actions CI runners  
**Project Type**: Infrastructure testing (single project)  
**Performance Goals**: Unit tests <30s, contract tests <2min (with deployment), integration tests <10min  
**Constraints**: Unit tests must not require AWS credentials; contract tests must fail clearly when stacks not deployed; all tests must support parallel execution  
**Scale/Scope**: ~50 total tests across 3 categories (unit, contract, integration) covering 5 CDK stacks (Network, Security, Storage, Database, AgentCore)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check (Phase 0)

**IV. Code Quality & Maintainability**
- ✅ **Testing Coverage**: Currently ~50 tests exist but misnamed/miscategorized. This feature reorganizes them to meet 80% coverage goal for infrastructure code
- ✅ **Type Safety**: Python type hints already used in CDK stacks; tests will follow same pattern
- ✅ **Consistent Patterns**: Tests currently use inconsistent naming (session vs function fixtures, duplicate names). This feature establishes consistent patterns

**VI. Observability & Operational Excellence**
- ✅ **Testing Gates**: Contract tests will validate deployed infrastructure against YAML contracts
- ✅ **CI/CD Pipeline Requirements**: Tests will run in GitHub Actions with proper separation (unit in PR, contract/integration post-deployment)

**Violations**: None - this feature improves constitutional compliance by fixing test organization

### Post-Design Check (Phase 1)

**IV. Code Quality & Maintainability**
- ✅ **Testing Coverage**: Reorganized tests maintain coverage while fixing categorization
- ✅ **Documentation**: Test contracts documented in YAML files with clear validation rules
- ✅ **Consistent Patterns**: UUID-based unique stack naming prevents JSII conflicts; pytest fixtures follow consistent scope patterns

**Development Standards**
- ✅ **Automated Testing**: All three test types (unit/contract/integration) automated in CI/CD
- ✅ **Contract Testing**: YAML contracts define expected CloudFormation outputs; tests validate against them

**Violations**: None

## Project Structure

### Documentation (this feature)

```
specs/009-redefine-and-fix/
├── plan.md              # This file
├── research.md          # Test categorization best practices, JSII kernel behavior
├── data-model.md        # Test entity definitions (UnitTest, ContractTest, IntegrationTest)
├── quickstart.md        # Developer guide for running/writing tests
├── contracts/           # (Not applicable - using existing contracts in 008-add-aws-agentcore/)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```
tests/
├── unit/
│   ├── test_agentcore_stack_synth.py          # Template validation (PUBLIC/VPC modes, outputs)
│   ├── test_agentcore_validation.py           # Input validation (CPU/memory, network mode) - FIXED: UUID naming
│   ├── test_vpc_construct.py                  # VPC template validation
│   └── test_cdk_synth.py                      # General CDK synthesis
│
├── contract/
│   ├── test_agentcore_runtime_contract.py     # REWRITE: Query actual CloudFormation outputs
│   ├── test_agentcore_execution_role_contract.py  # REWRITE: Query IAM role via boto3
│   ├── test_agentcore_vpc_endpoint_contract.py    # REWRITE: Query VPC endpoints via boto3
│   ├── test_vpc_contract.py                   # REWRITE: Query VPC resources via boto3
│   ├── test_subnets_*.py                      # REWRITE: Query subnet properties via boto3
│   ├── test_rds_endpoint_contract.py          # REWRITE: Query RDS cluster via boto3
│   ├── test_opensearch_endpoint_contract.py   # REWRITE: Query OpenSearch domain via boto3
│   ├── test_ecr_repositories_contract.py      # REWRITE: Query ECR repos via boto3
│   ├── test_s3_buckets_contract.py            # REWRITE: Query S3 buckets via boto3
│   ├── test_alb_dns_contract.py               # REWRITE: Query ALB via boto3
│   └── test_database_deployment_contract.py   # REWRITE: Query database resources via boto3
│
└── integration/
    ├── test_agentcore_e2e_deployment.py       # NEW: End-to-end agent deployment and invocation
    ├── test_agentcore_vpc_access.py           # NEW: VPC mode runtime access from within VPC
    ├── test_bedrock_access.py                 # NEW: Runtime can invoke Bedrock models
    ├── test_database_connectivity.py          # Agent runtime → RDS connectivity
    ├── test_alb_accessibility.py              # ALB health checks and routing
    ├── test_alb_post_deployment.py            # ALB integration validation
    ├── test_database_post_deployment.py       # Database integration validation
    ├── test_multiaz_resilience.py             # Multi-AZ failover testing
    └── test_vpc_subnets.py                    # VPC subnet integration

specs/
└── 008-add-aws-agentcore/
    └── contracts/
        ├── agentcore-stack.yaml               # Contract spec for AgentCore outputs
        ├── execution-role-permissions.json    # Expected IAM policy document
        ├── execution-role-trust.json          # Expected trust policy document
        └── vpc-endpoint-policy.json           # Expected VPC endpoint policy
```

**Structure Decision**: 
- **Unit tests** (`tests/unit/`) validate CloudFormation templates using `Template.from_stack()` - no AWS credentials required
- **Contract tests** (`tests/contract/`) query deployed CloudFormation stacks and AWS resources via boto3 - require deployment first
- **Integration tests** (`tests/integration/`) perform actual operations (invocations, connections) - require fully deployed system
- Contracts defined in YAML files under `specs/008-add-aws-agentcore/contracts/` serve as source of truth for validation

## Complexity Tracking

*No constitutional violations to justify*

## Phase 0: Research & Decisions

**Objective**: Resolve all technical unknowns and establish testing best practices

### Research Tasks

1. **Test Categorization Best Practices**
   - **Question**: What distinguishes unit/contract/integration tests in infrastructure-as-code projects?
   - **Research**: AWS CDK testing best practices, Terraform test patterns, contract testing principles
   - **Decision Needed**: Clear definitions and examples for each test category

2. **JSII Kernel State Management**
   - **Question**: Why do identical stack names across different `cdk.App()` instances cause conflicts?
   - **Research**: JSII architecture, Node.js bridge process behavior, construct tree global state
   - **Decision Needed**: Naming strategy to prevent conflicts (UUID suffix vs test isolation)

3. **Contract Validation Patterns**
   - **Question**: How to validate deployed infrastructure matches YAML contracts efficiently?
   - **Research**: JSON Schema validation, CloudFormation Output parsing, boto3 resource queries
   - **Decision Needed**: Contract validation library/pattern to use

4. **boto3 Query Patterns for Infrastructure Testing**
   - **Question**: What's the most reliable way to query CloudFormation outputs and AWS resources?
   - **Research**: boto3 CloudFormation client patterns, resource vs client APIs, error handling for missing stacks
   - **Decision Needed**: Standard query pattern with clear error messages

5. **Test Execution Strategies**
   - **Question**: How to ensure contract/integration tests skip gracefully when infrastructure not deployed?
   - **Research**: pytest skip conditions, fixture dependency chains, CI/CD test stage separation
   - **Decision Needed**: Skip strategy and CI/CD pipeline organization

**Output**: `research.md` with decisions, rationale, and code examples for each area

## Phase 1: Design

**Prerequisites**: `research.md` complete

### Data Model

**Objective**: Define test entity types and their relationships

**Entities to define**:
- **UnitTest**: Properties (test_name, stack_type, validates), CloudFormation assertions used
- **ContractTest**: Properties (test_name, contract_file, aws_resource_type), boto3 queries performed
- **IntegrationTest**: Properties (test_name, dependencies, operation_type), AWS operations performed
- **TestContract**: Properties (output_name, format, validation_rules), YAML structure
- **TestFixture**: Properties (scope, creates_resources, naming_strategy)

**Output**: `data-model.md`

### Contracts

**Objective**: Define test validation contracts (reuse existing YAML contracts from 008-add-aws-agentcore)

**Contract files** (already exist):
- `specs/008-add-aws-agentcore/contracts/agentcore-stack.yaml` - Required outputs: AgentRuntimeArn, AgentRuntimeId, AgentRuntimeEndpointUrl, ExecutionRoleArn, AgentRuntimeStatus, AgentRuntimeVersion
- `specs/008-add-aws-agentcore/contracts/execution-role-permissions.json` - IAM policy statements
- `specs/008-add-aws-agentcore/contracts/execution-role-trust.json` - IAM trust policy
- `specs/008-add-aws-agentcore/contracts/vpc-endpoint-policy.json` - VPC endpoint policy

**New contracts needed**: None (reuse existing)

**Output**: Documentation of contract usage in `data-model.md`

### Quickstart Guide

**Objective**: Developer guide for running and writing tests

**Content**:
- Running tests locally: `pytest tests/unit/`, `pytest tests/contract/`, `pytest tests/integration/`
- Writing new unit tests: Template validation patterns, unique naming
- Writing new contract tests: boto3 query patterns, contract YAML usage
- Writing new integration tests: Real operation patterns, cleanup strategies
- CI/CD test execution: When each test type runs, required AWS credentials

**Output**: `quickstart.md`

### Agent Context Update

After completing data model and quickstart, run:
```bash
cd /Users/jerrlin/repos/personal/aws-hackathon-infra
./.specify/scripts/bash/update-agent-context.sh opencode
```

This updates `AGENTS.md` with new testing patterns and commands.

## Phase 2: Task Breakdown

**Not executed by `/speckit.plan` - requires separate `/speckit.tasks` command**

Tasks will be generated based on:
- Rewriting 11 misnamed contract tests to use boto3
- Creating 3 new integration tests for AgentCore
- Fixing JSII naming conflicts in validation tests (already done in previous session)
- Documenting test patterns in quickstart guide

---

**Deliverables**:
- ✅ `plan.md` (this file)
- 🔄 `research.md` (Phase 0 output)
- 🔄 `data-model.md` (Phase 1 output)
- 🔄 `quickstart.md` (Phase 1 output)
- 🔄 Updated `AGENTS.md` (Phase 1 agent context update)

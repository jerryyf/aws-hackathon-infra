# Tasks: AWS CDK Infrastructure for Bedrock Agent Platform

**Input**: Design documents from `/specs/002-create-python-application/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.11, AWS CDK v2, aws-cdk-lib, constructs, boto3
2. Load optional design documents:
   → data-model.md: 14 entities → construct tasks
   → contracts/: main-stack.yaml with 9 endpoints → contract test tasks
   → research.md: Technical decisions → setup tasks
3. Generate tasks by category:
   → Setup: CDK project init, dependencies, linting
   → Tests: contract tests for stack outputs, integration tests for scenarios
   → Core: CDK constructs for infrastructure entities
   → Integration: Cross-stack connections, security, monitoring
   → Polish: unit tests, performance validation, documentation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests? Yes
   → All entities have constructs? Yes
   → All scenarios have integration tests? Yes
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **CDK project**: `cdk/` at repository root
- **Tests**: `tests/unit/`, `tests/integration/`
- All paths relative to repository root

## Phase 3.1: Setup
- [x] T001 Create CDK project structure per implementation plan (cdk/ directory with stacks/)
- [x] T002 Initialize Python CDK project with aws-cdk-lib, constructs, boto3 dependencies in requirements.txt
- [x] T003 [P] Configure pylint and black for linting and formatting in pyproject.toml

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Contract test for /vpc endpoint in tests/contract/test_vpc_contract.py
- [x] T005 [P] Contract test for /subnets/public endpoint in tests/contract/test_subnets_public_contract.py
- [x] T006 [P] Contract test for /subnets/private/app endpoint in tests/contract/test_subnets_private_app_contract.py
- [x] T007 [P] Contract test for /subnets/private/agent endpoint in tests/contract/test_subnets_private_agent_contract.py
- [x] T008 [P] Contract test for /subnets/private/data endpoint in tests/contract/test_subnets_private_data_contract.py
- [x] T009 [P] Contract test for /alb/dns endpoint in tests/contract/test_alb_dns_contract.py
- [x] T010 [P] Contract test for /rds/endpoint endpoint in tests/contract/test_rds_endpoint_contract.py
- [x] T011 [P] Contract test for /opensearch/endpoint endpoint in tests/contract/test_opensearch_endpoint_contract.py
- [x] T012 [P] Contract test for /s3/buckets endpoint in tests/contract/test_s3_buckets_contract.py
- [x] T013 [P] Contract test for /ecr/repositories endpoint in tests/contract/test_ecr_repositories_contract.py
- [x] T014 [P] Integration test VPC and subnets creation in tests/integration/test_vpc_subnets.py
- [x] T015 [P] Integration test load balancer accessibility in tests/integration/test_alb_accessibility.py
- [x] T016 [P] Integration test database connectivity in tests/integration/test_database_connectivity.py
- [x] T017 [P] Integration test Bedrock access via VPC endpoint in tests/integration/test_bedrock_access.py
- [x] T018 [P] Integration test multi-AZ resilience in tests/integration/test_multiaz_resilience.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T019 [P] VPC construct in cdk/stacks/network_stack.py
- [x] T020 [P] Public subnets construct in cdk/stacks/network_stack.py
- [x] T021 [P] Private application subnets construct in cdk/stacks/network_stack.py
- [x] T022 [P] Private AgentCore subnets construct in cdk/stacks/network_stack.py
- [x] T023 [P] Private data subnets construct in cdk/stacks/network_stack.py
- [x] T024 [P] Application Load Balancer construct in cdk/stacks/network_stack.py
- [x] T025 [P] RDS PostgreSQL cluster construct in cdk/stacks/database_stack.py
- [x] T026 [P] OpenSearch cluster construct in cdk/stacks/database_stack.py
- [x] T027 [P] S3 buckets construct in cdk/stacks/storage_stack.py
- [x] T028 [P] ECR repositories construct in cdk/stacks/storage_stack.py
- [x] T029 [P] Security groups construct in cdk/stacks/network_stack.py
- [x] T030 [P] VPC endpoints construct in cdk/stacks/network_stack.py
- [x] T031 [P] CloudWatch resources construct in cdk/stacks/monitoring_stack.py
- [x] T032 [P] Route 53 resources construct in cdk/stacks/network_stack.py
- [x] T033 NAT gateways and internet gateway in cdk/stacks/network_stack.py
- [x] T034 WAF and Shield integration in cdk/stacks/network_stack.py

## Phase 3.4: Integration
- [x] T035 RDS proxy configuration in cdk/stacks/database_stack.py
- [x] T036 Secrets Manager integration in cdk/stacks/security_stack.py
- [x] T037 SSM Parameter Store configuration in cdk/stacks/security_stack.py
- [x] T038 Cognito User Pool setup in cdk/stacks/security_stack.py
- [x] T039 CloudTrail audit logging in cdk/stacks/monitoring_stack.py
- [x] T040 ACM certificates for ALB in cdk/stacks/network_stack.py

## Phase 3.5: Polish
- [x] T041 [P] Unit tests for VPC construct in tests/unit/test_vpc_construct.py
- [x] T042 [P] Unit tests for subnet constructs in tests/unit/test_subnet_constructs.py
- [x] T043 [P] Unit tests for ALB construct in tests/unit/test_alb_construct.py
- [x] T044 [P] Unit tests for database constructs in tests/unit/test_database_constructs.py
- [x] T045 Performance validation (<10min deployment) in tests/integration/test_deployment_performance.py
- [x] T046 [P] Update README.md with CDK deployment instructions
- [x] T047 Run quickstart.md validation scenarios
- [x] T048 Final linting and code cleanup

## Dependencies
- Setup (T001-T003) before everything
- Tests (T004-T018) before implementation (T019-T040)
- Core constructs (T019-T034) before integration (T035-T040)
- Implementation before polish (T041-T048)
- Parallel tasks marked [P] can run simultaneously if files are independent

## Parallel Example
```
# Launch T004-T013 together (contract tests):
Task: "Contract test for /vpc endpoint in tests/contract/test_vpc_contract.py"
Task: "Contract test for /subnets/public endpoint in tests/contract/test_subnets_public_contract.py"
Task: "Contract test for /subnets/private/app endpoint in tests/contract/test_subnets_private_app_contract.py"
Task: "Contract test for /subnets/private/agent endpoint in tests/contract/test_subnets_private_agent_contract.py"
Task: "Contract test for /subnets/private/data endpoint in tests/contract/test_subnets_private_data_contract.py"
Task: "Contract test for /alb/dns endpoint in tests/contract/test_alb_dns_contract.py"
Task: "Contract test for /rds/endpoint endpoint in tests/contract/test_rds_endpoint_contract.py"
Task: "Contract test for /opensearch/endpoint endpoint in tests/contract/test_opensearch_endpoint_contract.py"
Task: "Contract test for /s3/buckets endpoint in tests/contract/test_s3_buckets_contract.py"
Task: "Contract test for /ecr/repositories endpoint in tests/contract/test_ecr_repositories_contract.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing core constructs
- Commit after each task completion
- Avoid: vague tasks, same file conflicts
- CDK stacks may share files, so some tasks are sequential within stacks

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - main-stack.yaml with 9 endpoints → 9 contract test tasks [P]

2. **From Data Model**:
   - 14 entities → 14 construct creation tasks [P] (grouped by stack)

3. **From User Stories**:
   - 5 acceptance scenarios → 5 integration test tasks [P]

4. **Ordering**:
   - Setup → Tests → Core Constructs → Integration → Polish
   - Dependencies block parallel execution within same files

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (9/9)
- [x] All entities have construct tasks (14/14)
- [x] All tests come before implementation
- [x] Parallel tasks are file-independent
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
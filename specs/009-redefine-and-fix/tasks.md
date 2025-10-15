# Tasks: Redefine and Fix AgentCore Test Suite

**Input**: Design documents from `/specs/009-redefine-and-fix/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Tests are the PRIMARY DELIVERABLE of this feature - reorganizing and rewriting existing tests to follow proper unit/contract/integration categorization.

**Organization**: Tasks are grouped by user story (test type) to enable independent implementation and testing of each category.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1=Unit, US2=Contract, US3=Integration, US4=Validation)
- Include exact file paths in descriptions

## Path Conventions
- Unit tests: `tests/unit/test_*.py`
- Contract tests: `tests/contract/test_*_contract.py`
- Integration tests: `tests/integration/test_*.py`
- Contract specifications: `specs/008-add-aws-agentcore/contracts/*.yaml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure test infrastructure and dependencies are ready

- [ ] T001 Verify pytest and aws-cdk.assertions installed in virtual environment
- [ ] T002 [P] Verify boto3 and botocore installed for integration tests
- [ ] T003 [P] Create conftest.py with shared fixtures in tests/ directory
- [ ] T004 Document JSII kernel conflict fix (UUID naming) in docs/testing-best-practices.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core test patterns that MUST be established before rewriting tests

**⚠️ CRITICAL**: No test rewriting can begin until these patterns are validated

- [ ] T005 Validate UUID naming pattern prevents JSII conflicts in tests/unit/test_agentcore_validation.py
- [ ] T006 Create shared boto3 client fixtures in tests/conftest.py (cloudformation, iam, ec2, rds, opensearch)
- [ ] T007 Create CloudFormation output extraction fixture pattern in tests/conftest.py
- [ ] T008 Create skip condition fixture for missing stacks in tests/conftest.py
- [ ] T009 [P] Load and parse contract YAML files from specs/008-add-aws-agentcore/contracts/agentcore-stack.yaml
- [ ] T010 [P] Validate quickstart.md test running instructions work for all three test types

**Checkpoint**: Foundation ready - test rewriting can now begin in parallel by test type

---

## Phase 3: User Story 1 - Validate CloudFormation Templates During Development (Priority: P1) 🎯 MVP

**Goal**: Fast unit tests that validate CDK code produces correct CloudFormation templates without AWS deployment

**Independent Test**: Run `PYTHONPATH=. pytest tests/unit/` - all tests pass in <30s without AWS credentials

### Implementation for User Story 1

- [ ] T011 [P] [US1] Fix JSII conflicts in tests/unit/test_agentcore_stack_synth.py using UUID suffix
- [ ] T012 [P] [US1] Fix JSII conflicts in tests/unit/test_cdk_synth.py using UUID suffix
- [ ] T013 [P] [US1] Validate tests/unit/test_vpc_construct.py follows UUID naming pattern
- [ ] T014 [US1] Add resource count validation tests in tests/unit/test_network_stack.py
- [ ] T015 [US1] Add resource property validation tests in tests/unit/test_security_stack.py
- [ ] T016 [US1] Add resource property validation tests in tests/unit/test_storage_stack.py
- [ ] T017 [US1] Add CloudFormation output existence tests in tests/unit/test_database_stack.py
- [ ] T018 [US1] Verify all unit tests run without AWS credentials (no boto3 calls)
- [ ] T019 [US1] Run full unit test suite and verify <30s execution time

**Checkpoint**: Unit tests complete - can validate CloudFormation templates during development without AWS

---

## Phase 4: User Story 2 - Validate Deployed Infrastructure Against Contracts (Priority: P2)

**Goal**: Contract tests that query actual CloudFormation outputs and AWS resources to validate deployments

**Independent Test**: Deploy stacks, then run `PYTHONPATH=. pytest tests/contract/` with AWS credentials - tests query real resources

### Contract Test Rewrites for User Story 2

**CRITICAL**: Current contract tests use `Template.from_stack()` (unit tests) - must rewrite to use boto3 queries

- [ ] T020 [P] [US2] Rewrite tests/contract/test_vpc_contract.py to query CloudFormation outputs via boto3
- [ ] T021 [P] [US2] Rewrite tests/contract/test_vpc_deployment_contract.py to query VPC resources via EC2 client
- [ ] T022 [P] [US2] Rewrite tests/contract/test_subnets_public_contract.py to query subnet properties via EC2 client
- [ ] T023 [P] [US2] Rewrite tests/contract/test_subnets_private_app_contract.py to query subnet properties via EC2 client
- [ ] T024 [P] [US2] Rewrite tests/contract/test_subnets_private_data_contract.py to query subnet properties via EC2 client
- [ ] T025 [P] [US2] Rewrite tests/contract/test_subnets_private_agent_contract.py to query subnet properties via EC2 client
- [ ] T026 [P] [US2] Rewrite tests/contract/test_s3_buckets_contract.py to query S3 bucket properties via boto3
- [ ] T027 [P] [US2] Rewrite tests/contract/test_ecr_repositories_contract.py to query ECR repositories via boto3
- [ ] T028 [P] [US2] Rewrite tests/contract/test_rds_endpoint_contract.py to query RDS cluster via boto3
- [ ] T029 [P] [US2] Rewrite tests/contract/test_opensearch_endpoint_contract.py to query OpenSearch domain via boto3
- [ ] T030 [P] [US2] Rewrite tests/contract/test_database_deployment_contract.py to query database resources via boto3
- [ ] T031 [P] [US2] Rewrite tests/contract/test_alb_dns_contract.py to query ALB resources via boto3
- [ ] T032 [P] [US2] Rewrite tests/contract/test_agentcore_runtime_contract.py to query CloudFormation outputs via boto3
- [ ] T033 [P] [US2] Rewrite tests/contract/test_agentcore_execution_role_contract.py to query IAM role via boto3
- [ ] T034 [P] [US2] Rewrite tests/contract/test_agentcore_vpc_endpoint_contract.py to query VPC endpoints via boto3
- [ ] T035 [US2] Add contract YAML validation to test_agentcore_runtime_contract.py (match specs/008-add-aws-agentcore/contracts/agentcore-stack.yaml)
- [ ] T036 [US2] Add IAM policy validation to test_agentcore_execution_role_contract.py (match specs/008-add-aws-agentcore/contracts/execution-role-permissions.json)
- [ ] T037 [US2] Add trust policy validation to test_agentcore_execution_role_contract.py (match specs/008-add-aws-agentcore/contracts/execution-role-trust.json)
- [ ] T038 [US2] Add VPC endpoint policy validation to test_agentcore_vpc_endpoint_contract.py (match specs/008-add-aws-agentcore/contracts/vpc-endpoint-policy.json)
- [ ] T039 [US2] Add fixture-level skip conditions to all contract tests when stacks not deployed
- [ ] T040 [US2] Verify all contract tests fail clearly with descriptive messages when stacks missing
- [ ] T041 [US2] Run full contract test suite against deployed stacks and verify <2min execution time

**Checkpoint**: Contract tests complete - can validate deployed infrastructure matches specifications

---

## Phase 5: User Story 3 - Test Cross-Stack Integration Behavior (Priority: P2)

**Goal**: Integration tests that perform real operations across multiple AWS services

**Independent Test**: Run `PYTHONPATH=. pytest tests/integration/` after deployment - tests perform actual invocations, connections, failover

### Integration Test Implementation for User Story 3

**NOTE**: Some integration tests already exist but may need boto3 query updates

- [ ] T042 [P] [US3] Verify tests/integration/test_vpc_subnets.py queries actual VPC subnet routing tables via boto3
- [ ] T043 [P] [US3] Verify tests/integration/test_database_connectivity.py performs real RDS connection test
- [ ] T044 [P] [US3] Verify tests/integration/test_database_post_deployment.py validates database schema via SQL queries
- [ ] T045 [P] [US3] Verify tests/integration/test_alb_accessibility.py performs real HTTP requests to ALB
- [ ] T046 [P] [US3] Verify tests/integration/test_alb_post_deployment.py validates ALB routing rules via boto3
- [ ] T047 [P] [US3] Create tests/integration/test_agentcore_e2e_deployment.py for agent runtime invocation tests
- [ ] T048 [P] [US3] Create tests/integration/test_agentcore_vpc_access.py for VPC mode runtime access tests
- [ ] T049 [P] [US3] Create tests/integration/test_bedrock_access.py for Bedrock model invocation tests
- [ ] T050 [US3] Create tests/integration/test_multiaz_resilience.py for multi-AZ failover simulation
- [ ] T051 [US3] Add state-based skip conditions (e.g., skip VPC tests if network_mode=PUBLIC)
- [ ] T052 [US3] Add dependency stack validation (skip if NetworkStack/SecurityStack not deployed)
- [ ] T053 [US3] Verify all integration tests skip gracefully when infrastructure not ready
- [ ] T054 [US3] Run full integration test suite against deployed stacks and verify <10min execution time

**Checkpoint**: Integration tests complete - can validate end-to-end behavior across AWS services

---

## Phase 6: User Story 4 - Validate Input Parameters and Error Conditions (Priority: P3)

**Goal**: Validation tests that verify CDK stacks properly validate inputs and handle errors

**Independent Test**: Run `PYTHONPATH=. pytest tests/unit/test_agentcore_validation.py` - tests verify invalid configs fail fast

### Validation Test Enhancement for User Story 4

- [ ] T055 [P] [US4] Verify tests/unit/test_agentcore_validation.py tests invalid CPU/memory ratios
- [ ] T056 [P] [US4] Add VPC mode validation test (missing VPC stack reference) in tests/unit/test_agentcore_validation.py
- [ ] T057 [P] [US4] Add environment name validation test (special characters) in tests/unit/test_agentcore_validation.py
- [ ] T058 [P] [US4] Add network mode enum validation test in tests/unit/test_agentcore_validation.py
- [ ] T059 [US4] Add missing dependency stack validation tests in tests/unit/test_agentcore_validation.py
- [ ] T060 [US4] Verify all validation tests use UUID naming to prevent JSII conflicts
- [ ] T061 [US4] Verify validation error messages are clear and actionable
- [ ] T062 [US4] Run validation test suite and verify all invalid configs caught during synthesis

**Checkpoint**: Validation tests complete - invalid configurations fail fast with clear error messages

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, CI/CD integration, and final validation

- [ ] T063 [P] Update GitHub Actions workflow in .github/workflows/deploy.yml to separate test execution stages
- [ ] T064 [P] Add unit test job (runs on every PR, no AWS credentials) to CI workflow
- [ ] T065 [P] Add contract test job (runs after deployment, requires AWS credentials) to CI workflow
- [ ] T066 [P] Add integration test job (runs after contract tests, requires deployment) to CI workflow
- [ ] T067 Create pytest.ini configuration for test discovery and parallel execution
- [ ] T068 Add test execution instructions to README.md
- [ ] T069 Verify pytest -n auto (parallel execution) works without JSII conflicts
- [ ] T070 Run full test suite (unit + contract + integration) and verify all success criteria met
- [ ] T071 Validate quickstart.md examples match actual test implementations
- [ ] T072 Update docs/testing-best-practices.md with final patterns and lessons learned

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (Unit Tests) can proceed first - establishes fast feedback loop
  - User Story 2 (Contract Tests) can proceed after US1 - validates deployments
  - User Story 3 (Integration Tests) should follow US2 - requires deployed infrastructure patterns
  - User Story 4 (Validation Tests) can proceed in parallel with US2/US3 - extends US1
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1) - Unit Tests**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2) - Contract Tests**: Can start after Foundational (Phase 2) - Independent but benefits from US1 patterns
- **User Story 3 (P2) - Integration Tests**: Can start after Foundational (Phase 2) - Independent but benefits from US2 boto3 patterns
- **User Story 4 (P3) - Validation Tests**: Can start after Foundational (Phase 2) - Extends US1 unit test patterns

### Within Each User Story

**User Story 1 (Unit Tests)**:
- Fix JSII conflicts in existing tests (T011-T013) before adding new tests
- New stack validation tests (T014-T017) can run in parallel
- Final validation (T018-T019) depends on all unit tests being fixed

**User Story 2 (Contract Tests)**:
- All test rewrites (T020-T034) can run in parallel - different files
- Contract YAML validation (T035-T038) depends on corresponding test rewrites
- Skip conditions (T039-T040) can be added in parallel across all contract tests
- Final validation (T041) depends on all contract tests being rewritten

**User Story 3 (Integration Tests)**:
- Existing test verification (T042-T046) can run in parallel - different files
- New test creation (T047-T050) can run in parallel - different files
- Skip conditions (T051-T052) can be added after tests exist
- Final validation (T053-T054) depends on all integration tests being complete

**User Story 4 (Validation Tests)**:
- All validation test additions (T055-T059) can run in parallel - same file but different test functions
- Validation checks (T060-T062) depend on all validation tests being added

### Parallel Opportunities

**Phase 1 (Setup)**: All tasks can run in parallel
- T001, T002, T003, T004

**Phase 2 (Foundational)**: Some parallelism
- T006, T007, T008 depend on T005 (validate pattern works first)
- T009, T010 can run independently

**Phase 3 (User Story 1)**:
- T011, T012, T013 can run in parallel (different files)
- T014, T015, T016, T017 can run in parallel (different files)

**Phase 4 (User Story 2)**: HIGHLY PARALLEL - 15 test rewrites
- T020-T034 can ALL run in parallel (different files)
- T035-T038 can run in parallel after their dependencies
- T039-T040 can run in parallel across all files

**Phase 5 (User Story 3)**: HIGHLY PARALLEL - 9 test files
- T042-T050 can ALL run in parallel (different files)
- T051-T052 can run in parallel

**Phase 6 (User Story 4)**: HIGHLY PARALLEL - validation tests
- T055-T059 can ALL run in parallel (different test functions)

**Phase 7 (Polish)**: Some parallelism
- T063-T066 can run in parallel (GitHub Actions workflow jobs)
- T067, T068, T071, T072 can run in parallel (different files)

---

## Parallel Example: User Story 2 (Contract Test Rewrites)

```bash
# Launch all contract test rewrites together (15 files):
Task: "Rewrite tests/contract/test_vpc_contract.py to query CloudFormation outputs via boto3"
Task: "Rewrite tests/contract/test_vpc_deployment_contract.py to query VPC resources via EC2 client"
Task: "Rewrite tests/contract/test_subnets_public_contract.py to query subnet properties via EC2 client"
Task: "Rewrite tests/contract/test_subnets_private_app_contract.py to query subnet properties via EC2 client"
Task: "Rewrite tests/contract/test_subnets_private_data_contract.py to query subnet properties via EC2 client"
Task: "Rewrite tests/contract/test_subnets_private_agent_contract.py to query subnet properties via EC2 client"
Task: "Rewrite tests/contract/test_s3_buckets_contract.py to query S3 bucket properties via boto3"
Task: "Rewrite tests/contract/test_ecr_repositories_contract.py to query ECR repositories via boto3"
Task: "Rewrite tests/contract/test_rds_endpoint_contract.py to query RDS cluster via boto3"
Task: "Rewrite tests/contract/test_opensearch_endpoint_contract.py to query OpenSearch domain via boto3"
Task: "Rewrite tests/contract/test_database_deployment_contract.py to query database resources via boto3"
Task: "Rewrite tests/contract/test_alb_dns_contract.py to query ALB resources via boto3"
Task: "Rewrite tests/contract/test_agentcore_runtime_contract.py to query CloudFormation outputs via boto3"
Task: "Rewrite tests/contract/test_agentcore_execution_role_contract.py to query IAM role via boto3"
Task: "Rewrite tests/contract/test_agentcore_vpc_endpoint_contract.py to query VPC endpoints via boto3"

# Then add contract YAML validation (4 files in parallel):
Task: "Add contract YAML validation to test_agentcore_runtime_contract.py"
Task: "Add IAM policy validation to test_agentcore_execution_role_contract.py"
Task: "Add trust policy validation to test_agentcore_execution_role_contract.py"
Task: "Add VPC endpoint policy validation to test_agentcore_vpc_endpoint_contract.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only - Fast Feedback Loop)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T010) - CRITICAL for all stories
3. Complete Phase 3: User Story 1 (T011-T019) - Unit tests only
4. **STOP and VALIDATE**: Run `PYTHONPATH=. pytest tests/unit/` - should pass in <30s without AWS credentials
5. Developers can now use unit tests during development

### Incremental Delivery (Add Contract Tests)

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Unit tests work independently (MVP!)
3. Add User Story 2 → Contract tests work independently after deployment
4. **STOP and VALIDATE**: Deploy stacks, run `PYTHONPATH=. pytest tests/contract/` - validates real infrastructure
5. CI/CD can now validate deployments automatically

### Full Feature Delivery (Add Integration + Validation)

1. Complete User Story 3 → Integration tests validate end-to-end behavior
2. Complete User Story 4 → Validation tests catch invalid configs early
3. Complete Phase 7 → CI/CD integration, documentation, polish
4. **FINAL VALIDATION**: Run all test types, verify success criteria met

### Parallel Team Strategy

With multiple developers after Foundational phase (T005-T010) completes:

1. **Developer A**: User Story 1 (T011-T019) - Unit test fixes
2. **Developer B**: User Story 2 (T020-T041) - Contract test rewrites (15 files!)
3. **Developer C**: User Story 3 (T042-T054) - Integration test implementation
4. **Developer D**: User Story 4 (T055-T062) - Validation test enhancements

All stories can proceed in parallel since they work on different test categories/files.

---

## Task Summary

### Total Task Count: 72 tasks

**By User Story**:
- Setup: 4 tasks
- Foundational: 6 tasks (BLOCKS all stories)
- User Story 1 (Unit Tests): 9 tasks
- User Story 2 (Contract Tests): 22 tasks (15 test rewrites + 7 enhancements)
- User Story 3 (Integration Tests): 13 tasks
- User Story 4 (Validation Tests): 8 tasks
- Polish: 10 tasks

**By Phase**:
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 6 tasks
- Phase 3 (US1 - Unit): 9 tasks
- Phase 4 (US2 - Contract): 22 tasks
- Phase 5 (US3 - Integration): 13 tasks
- Phase 6 (US4 - Validation): 8 tasks
- Phase 7 (Polish): 10 tasks

**Parallel Opportunities**: 58 tasks marked [P] (80% of tasks can run in parallel within their phase)

**Independent Test Criteria**:
- **US1**: Run `PYTHONPATH=. pytest tests/unit/` - passes in <30s without AWS
- **US2**: Deploy stacks, run `PYTHONPATH=. pytest tests/contract/` - validates real resources in <2min
- **US3**: Run `PYTHONPATH=. pytest tests/integration/` - end-to-end tests pass in <10min
- **US4**: Run `PYTHONPATH=. pytest tests/unit/test_agentcore_validation.py` - invalid configs fail fast

**Suggested MVP Scope**: User Story 1 only (fast unit tests) - enables developer feedback loop without AWS deployment

---

## Notes

- [P] tasks = different files or independent test functions, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Current contract tests are MISNAMED - they use `Template.from_stack()` (unit tests) not boto3 (contract tests)
- Major effort is in Phase 4 (User Story 2) - rewriting 15 contract test files to use boto3
- JSII kernel conflicts are already partially fixed in test_agentcore_validation.py - use as reference pattern
- Contract YAML files in specs/008-add-aws-agentcore/contracts/ are source of truth for validation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: running contract/integration tests without deployed infrastructure (should skip gracefully)

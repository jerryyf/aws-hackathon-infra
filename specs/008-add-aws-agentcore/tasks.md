# Tasks: AWS AgentCore Runtime Infrastructure

**Input**: Design documents from `/specs/008-add-aws-agentcore/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/  
**Tech Stack**: Python 3.11, AWS CDK v2, L1 constructs, pytest  

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)  
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)  
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and configuration updates needed for all user stories

- [ ] T001 Add AgentCore stack import to `cdk/stacks/__init__.py`
- [ ] T002 Add AgentCore configuration to `cdk/config.py` with environment-based resource allocation
- [ ] T003 Create `cdk/stacks/agentcore_stack.py` skeleton with basic CDK stack structure
- [ ] T004 Update `cdk/app.py` to wire up AgentCoreStack dependencies (Network → Security → Storage → AgentCore)

**Checkpoint**: Basic project structure ready for implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Add ECR repository for agent images to `cdk/stacks/storage_stack.py`
- [ ] T006 [P] Create IAM execution role in `cdk/stacks/security_stack.py` with trust policy from `contracts/execution-role-trust.json`
- [ ] T007 [P] Add IAM permissions policy to execution role using `contracts/execution-role-permissions.json`
- [ ] T008 Add VPC interface endpoint for bedrock-agentcore service to `cdk/stacks/network_stack.py`
- [ ] T009 Create security group for agent runtime traffic in `cdk/stacks/network_stack.py`
- [ ] T010 Export all required outputs from modified stacks (ECR repository ARN, execution role ARN, VPC endpoint ID, security group ID)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Deploy Agent Runtime Container (Priority: P1) 🎯 MVP

**Goal**: Deploy AWS AgentCore runtime containers so that AI agents can run in a managed, scalable environment

**Independent Test**: Deploy simple agent container to ECR, create agent runtime using CDK, verify runtime status is ACTIVE

### Implementation for User Story 1

- [ ] T011 [US1] Implement CfnRuntime resource in `cdk/stacks/agentcore_stack.py` with PUBLIC network mode
- [ ] T012 [US1] Configure container artifact with ECR image URI and basic resource allocation (512 CPU, 1024 MiB)
- [ ] T013 [US1] Add runtime ARN output to stack per `contracts/agentcore-stack.yaml`
- [ ] T014 [US1] Add runtime endpoint URL output to stack per `contracts/agentcore-stack.yaml`
- [ ] T015 [US1] Add runtime status output to stack per `contracts/agentcore-stack.yaml`
- [ ] T016 [US1] Add runtime ID output to stack per `contracts/agentcore-stack.yaml`
- [ ] T017 [US1] Add execution role ARN output to stack per `contracts/agentcore-stack.yaml`
- [ ] T018 [US1] Add runtime version output to stack per `contracts/agentcore-stack.yaml`
- [ ] T019 [US1] Apply required resource tags (Project, Environment, Owner, CostCenter) per FR-009

**Checkpoint**: User Story 1 complete - basic agent runtime deployment functional

---

## Phase 4: User Story 2 - Configure VPC Networking for Agent Runtimes (Priority: P2)

**Goal**: Enable agent runtimes to run within VPC with proper network isolation for secure access to internal resources

**Independent Test**: Deploy agent runtime with VPC network mode, verify it can access resources in private subnets, confirm it cannot be accessed from public internet

### Implementation for User Story 2

- [ ] T020 [US2] Add VPC network mode configuration to `cdk/stacks/agentcore_stack.py`
- [ ] T021 [US2] Reference PrivateAgent subnets from Network Stack in runtime configuration
- [ ] T022 [US2] Reference agent runtime security group in runtime configuration
- [ ] T023 [US2] Configure security group rules for agent runtime outbound access to AWS services
- [ ] T024 [US2] Add network configuration validation logic to ensure VPC mode has required subnets and security groups
- [ ] T025 [US2] Update runtime deployment to use multi-AZ subnet selection (us-east-1a, us-east-1b)

**Checkpoint**: User Story 2 complete - VPC networking functional and secure

---

## Phase 5: User Story 3 - Manage IAM Permissions for Agent Runtime Execution (Priority: P2)

**Goal**: Configure IAM roles and policies for agent runtimes with least-privilege principles

**Independent Test**: Create execution role with specific permissions, attach to agent runtime, verify agent can only access permitted resources

### Implementation for User Story 3

- [ ] T026 [US3] Add Bedrock model access permissions to execution role using policy from `contracts/execution-role-permissions.json`
- [ ] T027 [US3] Add CloudWatch logs permissions for agent runtime logging using policy from `contracts/execution-role-permissions.json`
- [ ] T028 [US3] Add Secrets Manager access permissions for agent configuration using policy from `contracts/execution-role-permissions.json`
- [ ] T029 [US3] Add KMS decrypt permissions for encrypted resources using policy from `contracts/execution-role-permissions.json`
- [ ] T030 [US3] Implement conditional access controls with source account and ARN restrictions
- [ ] T031 [US3] Add policy validation to ensure all required permissions are attached before runtime deployment

**Checkpoint**: User Story 3 complete - IAM permissions properly configured with least-privilege access

---

## Phase 6: User Story 4 - Enable VPC Interface Endpoints for AgentCore (Priority: P3)

**Goal**: Ensure AgentCore traffic remains within AWS's private network for regulatory compliance

**Independent Test**: Create VPC endpoints, configure endpoint policies, verify agent runtime invocations route through private endpoint

### Implementation for User Story 4

- [ ] T032 [US4] Configure VPC endpoint policy using `contracts/vpc-endpoint-policy.json` in `cdk/stacks/network_stack.py`
- [ ] T033 [US4] Enable private DNS for VPC endpoint to support transparent service access
- [ ] T034 [US4] Add VPC endpoint security group rules to allow ingress from agent runtime security group
- [ ] T035 [US4] Configure multi-AZ VPC endpoint deployment for high availability
- [ ] T036 [US4] Add endpoint policy validation to restrict access to specific IAM principals
- [ ] T037 [US4] Export VPC endpoint DNS names as stack outputs for runtime configuration

**Checkpoint**: User Story 4 complete - private network connectivity established

---

## Phase 7: Contract Validation & Integration

**Purpose**: Ensure all components work together and meet contract specifications

- [ ] T038 [P] Create contract test `tests/contract/test_agentcore_runtime_contract.py` to validate runtime outputs per `contracts/agentcore-stack.yaml`
- [ ] T039 [P] Create contract test `tests/contract/test_agentcore_execution_role_contract.py` to validate IAM role configuration
- [ ] T040 [P] Create contract test `tests/contract/test_vpc_endpoint_contract.py` to validate VPC endpoint configuration
- [ ] T041 Create integration test `tests/integration/test_agentcore_deployment.py` for E2E deployment to ACTIVE status
- [ ] T042 Create integration test `tests/integration/test_agentcore_vpc_access.py` for VPC-mode runtime access validation
- [ ] T043 Create unit test `tests/unit/test_agentcore_stack_synth.py` for CDK synthesis validation

**Checkpoint**: All contract tests passing, deployment validated

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

- [ ] T044 [P] Add CloudWatch monitoring integration per FR-010 (runtime status, invocation count, error rate, latency)
- [ ] T045 [P] Add comprehensive error handling and logging throughout all stacks
- [ ] T046 [P] Implement environment-based resource allocation (dev: 512/1024, prod: 2048/4096) per research findings
- [ ] T047 [P] Add runtime deployment timeout configuration (10 minute limit per SC-001)
- [ ] T048 Add stack dependency validation to ensure proper deployment order
- [ ] T049 Run quickstart.md validation to ensure deployment guide accuracy
- [ ] T050 Validate all resource tagging compliance with AWS Well-Architected Framework requirements

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories  
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed) or sequentially by priority (P1 → P2 → P3)
  - US2 and US3 are both P2 priority - can be done in either order
- **Contract Validation (Phase 7)**: Depends on all desired user stories being complete
- **Polish (Phase 8)**: Depends on contract validation passing

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of other stories  
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Independent of other stories
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - May benefit from US2 VPC setup but not strictly dependent

### Within Each User Story

- Stack modification tasks follow dependency order within AgentCore stack
- Output tasks depend on resource creation tasks
- Validation tasks depend on configuration tasks
- Tagging tasks can be done in parallel with functional implementation

### Parallel Opportunities

- **Setup Phase**: T001-T004 can be done in parallel (different files)
- **Foundational Phase**: T005-T007 can be done in parallel (different stacks), T008-T010 sequential  
- **User Stories**: Once foundational complete, US1-US4 can start in parallel if team capacity allows
- **Contract Tests**: T038-T040 can be written and run in parallel
- **Polish Tasks**: T044-T047 can be done in parallel (different concerns)

---

## Parallel Example: Foundational Phase

```bash
# Launch foundational infrastructure together:
Task: "Add ECR repository for agent images to cdk/stacks/storage_stack.py"
Task: "Create IAM execution role in cdk/stacks/security_stack.py"  
Task: "Add IAM permissions policy to execution role"
```

---

## Parallel Example: User Story 1

```bash
# Launch User Story 1 output tasks together:
Task: "Add runtime ARN output to stack"
Task: "Add runtime endpoint URL output to stack"
Task: "Add runtime status output to stack"
Task: "Add runtime ID output to stack"
Task: "Add execution role ARN output to stack"
Task: "Add runtime version output to stack"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1  
4. **STOP and VALIDATE**: Test User Story 1 independently with PUBLIC mode
5. Deploy/demo basic agent runtime functionality

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - PUBLIC mode agent runtime)
3. Add User Story 2 → Test independently → Deploy/Demo (VPC networking)
4. Add User Story 3 → Test independently → Deploy/Demo (Enhanced IAM security)  
5. Add User Story 4 → Test independently → Deploy/Demo (Full private networking)
6. Each story adds security/compliance value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (P1 - highest priority)
   - Developer B: User Story 2 (P2 - VPC networking)
   - Developer C: User Story 3 (P2 - IAM permissions)
   - Developer D: User Story 4 (P3 - VPC endpoints)
3. Stories complete and integrate independently

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability  
- **Each user story**: Independently completable and testable
- **CDK synthesis**: Run `cdk synth` after each major change to validate CloudFormation
- **Stack dependencies**: Follow Network → Security → Storage → AgentCore deployment order
- **Resource allocation**: Environment-based sizing per research.md recommendations
- **No tests requested**: Focus on implementation and contract validation
- **Commit strategy**: Commit after each task or logical group of parallel tasks
- **Avoid**: Cross-story dependencies that break independence, same-file conflicts when marked [P]
# Tasks: ECS Stack Infrastructure for 2-Service Architecture

**Input**: Design documents from `/specs/010-ecs-stack-implementation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Architecture**: 2-tier system with BFF (public ALB) → AgentCore (Service Discovery, private)

**Tests**: Test tasks are OPTIONAL and not included per project standards (only generate if explicitly requested).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- Infrastructure: `cdk/stacks/`, `cdk/`
- Tests: `tests/unit/`, `tests/contract/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and configuration updates for ECS infrastructure

- [ ] T001 Update config.py to add ECS resource allocation settings per environment (dev: 512 CPU/1024 MiB, test: 1024 CPU/2048 MiB, prod: 2048 CPU/4096 MiB) in cdk/config.py
- [ ] T002 [P] Update requirements.txt to verify aws-cdk-lib dependencies are current (aws-cdk.aws-ecs, aws-cdk.aws-iam) in cdk/requirements.txt

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core IAM roles and security groups that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create task execution role with ECR pull permissions (ecr:GetAuthorizationToken, ecr:BatchCheckLayerAvailability, ecr:GetDownloadUrlForLayer, ecr:BatchGetImage) in cdk/stacks/compute_stack.py
- [ ] T004 Add CloudWatch Logs write permissions to task execution role (logs:CreateLogStream, logs:PutLogEvents) in cdk/stacks/compute_stack.py
- [ ] T005 Add SSM Parameter Store read permissions to task execution role (ssm:GetParameter, ssm:GetParameters) in cdk/stacks/compute_stack.py
- [ ] T006 [P] Create security group for BFF tasks allowing inbound from public ALB on port 3000 in cdk/stacks/compute_stack.py
- [ ] T007 [P] Create security group for AgentCore tasks allowing inbound from BFF security group on port 8080 in cdk/stacks/compute_stack.py
- [ ] T008 Configure all ECS security groups to allow outbound traffic to VPC endpoints on port 443 in cdk/stacks/compute_stack.py
- [ ] T009 Configure all ECS security groups to allow outbound traffic to RDS security group on port 5432 in cdk/stacks/compute_stack.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

**Task Count**: Phase 2 = 9 tasks

---

## Phase 3: User Story 1 - Deploy ECS Cluster with Fargate Support (Priority: P1) 🎯 MVP

**Goal**: Provision ECS cluster with Fargate capacity providers integrating with existing VPC networking

**Independent Test**: Deploy ECS cluster and verify cluster status, Fargate capacity provider configuration, and VPC integration via `aws ecs describe-clusters`

### Implementation for User Story 1

- [ ] T011 [US1] Update ECS cluster in ComputeStack to enable CloudWatch Container Insights in cdk/stacks/compute_stack.py
- [ ] T012 [US1] Create Fargate capacity provider with on-demand compute and assign 70% weight in default strategy in cdk/stacks/compute_stack.py
- [ ] T013 [US1] Create Fargate Spot capacity provider and assign 30% weight in default strategy in cdk/stacks/compute_stack.py
- [ ] T014 [US1] Associate capacity providers with ECS cluster in cdk/stacks/compute_stack.py
- [ ] T015 [US1] Export cluster ARN and cluster name as CloudFormation outputs in cdk/stacks/compute_stack.py
- [ ] T016 [US1] Create contract test validating cluster ARN and cluster name outputs in tests/contract/test_ecs_cluster_contract.py
- [ ] T017 [US1] Update unit tests to verify cluster configuration and capacity providers in tests/unit/test_compute_stack.py

**Checkpoint**: ECS cluster with Fargate capacity providers should be deployable and testable independently

**Task Count**: Phase 3 = 7 tasks

---

## Phase 4: User Story 2 - Create Fargate Task Definitions for Application Services (Priority: P1)

**Goal**: Define ECS task definitions for BFF and AgentCore with appropriate resource allocations and IAM roles

**Independent Test**: Validate task definitions via `aws ecs describe-task-definition` checking IAM roles, resource allocations, and CloudWatch log configuration

### Implementation for User Story 2

- [ ] T018 [P] [US2] Create BFF task role with CloudWatch Logs write and SSM Parameter Store read permissions in cdk/stacks/compute_stack.py
- [ ] T019 [P] [US2] Create AgentCore task role with full Bedrock agent access, S3 read/write, and SSM Parameter Store read permissions in cdk/stacks/compute_stack.py
- [ ] T020 [P] [US2] Create CloudWatch log group for BFF service with 7-day retention in cdk/stacks/compute_stack.py
- [ ] T021 [P] [US2] Create CloudWatch log group for AgentCore service with 7-day retention in cdk/stacks/compute_stack.py
- [ ] T022 [US2] Create Fargate task definition for BFF with environment-based CPU/memory allocation, task execution role, task role, and container definition (port 3000, ECR image URI from storage_stack.app_ecr_repo, CloudWatch logs, environment variables) in cdk/stacks/compute_stack.py
- [ ] T023 [US2] Create Fargate task definition for AgentCore with environment-based CPU/memory allocation, task execution role, task role, and container definition (port 8080, ECR image URI from storage_stack.agent_ecr_repo, CloudWatch logs, environment variables) in cdk/stacks/compute_stack.py
- [ ] T024 [US2] Export task definition ARNs for BFF and AgentCore as CloudFormation outputs in cdk/stacks/compute_stack.py
- [ ] T025 [US2] Create contract test validating task definition ARNs and task role ARNs in tests/contract/test_task_definitions_contract.py
- [ ] T026 [US2] Update unit tests to verify task definition configurations, IAM roles, and CloudWatch log groups in tests/unit/test_compute_stack.py

**Checkpoint**: Task definitions should be created with correct resource allocations, IAM roles, and CloudWatch logging

**Task Count**: Phase 4 = 9 tasks

---

## Phase 5: User Story 4 - Configure Security Groups and Network Isolation (Priority: P1)

**Goal**: Validate security group rules enforce network isolation between service tiers with least privilege

**Independent Test**: Verify security group rules via `aws ec2 describe-security-groups` confirming no 0.0.0.0/0 inbound access to ECS tasks

### Implementation for User Story 4

- [ ] T027 [US4] Create contract test validating BFF security group allows inbound only from public ALB security group on port 3000 in tests/contract/test_security_groups_contract.py
- [ ] T028 [US4] Create contract test validating AgentCore security group allows inbound only from BFF security group on port 8080 in tests/contract/test_security_groups_contract.py
- [ ] T029 [US4] Create contract test validating no security group allows 0.0.0.0/0 inbound access in tests/contract/test_security_groups_contract.py
- [ ] T030 [US4] Update unit tests to verify security group ingress and egress rules in tests/unit/test_compute_stack.py

**Checkpoint**: Security groups should enforce network isolation with zero 0.0.0.0/0 inbound access

**Task Count**: Phase 5 = 4 tasks

---

## Phase 6: User Story 3 - Deploy ECS Services with Load Balancer Integration (Priority: P2)

**Goal**: Deploy ECS services that register with ALB (BFF only), enable Service Discovery for AgentCore, handle health checks, and maintain desired task counts with auto-scaling

**Independent Test**: Verify services via `aws ecs describe-services` checking task health, ALB target registration (BFF), Service Discovery DNS (AgentCore), and auto-scaling policies

### Implementation for User Story 3

- [ ] T031 [US3] Create target group for BFF service with health check on /api/health (30-second interval, 3 failures unhealthy, 2 successes healthy) and attach to public ALB in cdk/stacks/compute_stack.py
- [ ] T032 [US3] Create ECS Service Discovery namespace (private DNS namespace) for internal service-to-service communication in cdk/stacks/compute_stack.py
- [ ] T033 [US3] Create ECS service for BFF with desired count 2, PrivateApp subnets, BFF security group, public ALB target group registration, rolling update strategy (50% min healthy, 200% max) in cdk/stacks/compute_stack.py
- [ ] T034 [US3] Create ECS service for AgentCore with desired count 2, PrivateAgent subnets, agent security group, Service Discovery configuration (agentcore.local DNS), rolling update strategy (50% min healthy, 200% max) in cdk/stacks/compute_stack.py
- [ ] T035 [US3] Configure auto-scaling for BFF service with min 2, max 10 tasks, CPU threshold 70%, memory threshold 80%, 300-second cooldown in cdk/stacks/compute_stack.py
- [ ] T036 [US3] Configure auto-scaling for AgentCore service with min 2, max 10 tasks, CPU threshold 70%, memory threshold 80%, 300-second cooldown in cdk/stacks/compute_stack.py
- [ ] T037 [US3] Export service ARNs for BFF and AgentCore as CloudFormation outputs in cdk/stacks/compute_stack.py
- [ ] T038 [US3] Export Service Discovery namespace ID and AgentCore service DNS name as CloudFormation outputs in cdk/stacks/compute_stack.py
- [ ] T039 [US3] Create contract test validating service ARNs and Service Discovery outputs in tests/contract/test_ecs_services_contract.py
- [ ] T040 [US3] Update unit tests to verify ECS service configurations, target group, Service Discovery, and auto-scaling policies in tests/unit/test_compute_stack.py

**Checkpoint**: ECS services should be deployable with ALB integration (BFF), Service Discovery (AgentCore), health checks, and auto-scaling policies

**Task Count**: Phase 6 = 10 tasks

---

## Phase 7: User Story 5 - Integrate Task IAM Roles for AWS Service Access (Priority: P2)

**Goal**: Validate task IAM roles grant least-privilege access to AWS services without embedded credentials

**Independent Test**: Execute tasks and verify they can access permitted AWS services (SSM Parameter Store, Bedrock, S3) but not unauthorized resources

### Implementation for User Story 5

- [ ] T041 [US5] Update BFF task role to restrict permissions to CloudWatch Logs write and SSM Parameter Store read only (remove any excess permissions) in cdk/stacks/compute_stack.py
- [ ] T042 [US5] Update AgentCore task role to include bedrock-agent-runtime:InvokeAgent, bedrock-runtime:InvokeModel, S3 read/write for agent data, SSM Parameter Store read in cdk/stacks/compute_stack.py
- [ ] T043 [US5] Add resource-level restrictions to task roles to prevent resource deletion or infrastructure modification in cdk/stacks/compute_stack.py
- [ ] T044 [US5] Update unit tests to verify task role permissions follow least privilege principle in tests/unit/test_compute_stack.py

**Checkpoint**: Task IAM roles should enable secure AWS service access with least privilege

**Task Count**: Phase 7 = 4 tasks

---

## Phase 8: Observability & Monitoring

**Goal**: Create CloudWatch alarms for operational metrics

**Independent Test**: Trigger alarms by manually stopping tasks or marking targets unhealthy

### Implementation for Observability

- [ ] T045 [P] Create CloudWatch alarm for BFF service task count below desired count in cdk/stacks/compute_stack.py
- [ ] T046 [P] Create CloudWatch alarm for AgentCore service task count below desired count in cdk/stacks/compute_stack.py
- [ ] T047 [P] Create CloudWatch alarm for unhealthy target count in BFF target group in cdk/stacks/compute_stack.py
- [ ] T048 Update unit tests to verify CloudWatch alarms are configured correctly in tests/unit/test_compute_stack.py

**Checkpoint**: CloudWatch alarms should be created for service task counts and target health

**Task Count**: Phase 8 = 4 tasks

---

## Phase 9: Stack Integration

**Goal**: Update ComputeStack to accept stack dependencies and integrate with existing infrastructure

**Independent Test**: Deploy ComputeStack and verify it correctly references NetworkStack VPC, StorageStack ECR repositories (app_ecr_repo, agent_ecr_repo), and SecurityStack SSM Parameter Store

### Implementation for Stack Integration

- [ ] T049 Update ComputeStack constructor to accept network_stack, storage_stack, security_stack, database_stack as parameters in cdk/stacks/compute_stack.py
- [ ] T050 Update BFF task definition to reference ECR repository URI from storage_stack.app_ecr_repo.repository_uri in cdk/stacks/compute_stack.py
- [ ] T051 Update AgentCore task definition to reference ECR repository URI from storage_stack.agent_ecr_repo.repository_uri in cdk/stacks/compute_stack.py
- [ ] T052 Update task execution role to reference SSM Parameter Store ARNs from SecurityStack in cdk/stacks/compute_stack.py
- [ ] T053 Update security groups to reference RDS security group from DatabaseStack in cdk/stacks/compute_stack.py
- [ ] T054 Update ECS services to reference subnets from NetworkStack (PrivateApp: 10.0.11.0/24, 10.0.12.0/24; PrivateAgent: 10.0.21.0/24, 10.0.22.0/24) in cdk/stacks/compute_stack.py
- [ ] T055 Update BFF service to reference public ALB from NetworkStack in cdk/stacks/compute_stack.py
- [ ] T056 Update app.py to pass network_stack, storage_stack, security_stack, database_stack to ComputeStack constructor in cdk/app.py
- [ ] T057 Update unit tests to verify stack dependencies are correctly wired in tests/unit/test_compute_stack.py

**Checkpoint**: ComputeStack should integrate with all dependency stacks

**Task Count**: Phase 9 = 9 tasks

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements, validation, and documentation

- [ ] T058 Run cdk synth to validate CloudFormation template generation in cdk/
- [ ] T059 Run pyright type checking to ensure type safety in cdk/
- [ ] T060 Run black formatter to ensure code style consistency in cdk/
- [ ] T061 Run pylint to catch code quality issues in cdk/stacks/
- [ ] T062 Run all unit tests via pytest tests/unit/ to ensure ComputeStack tests pass
- [ ] T063 Run all contract tests via pytest tests/contract/ to ensure CloudFormation outputs are correct
- [ ] T064 [P] Create deployment report documenting deployment steps, validation results, and rollback procedure in docs/deployment/ecs-deployment-report_2025-10-18.md
- [ ] T065 [P] Update README.md to include ECS stack deployment commands and validation steps

**Task Count**: Phase 10 = 8 tasks

**Total Tasks**: 65 tasks (reduced from 73 due to simplified 2-service architecture)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User Story 1 (Cluster): Can start after Foundational - No dependencies on other stories
  - User Story 2 (Task Definitions): Can start after Foundational - No dependencies on other stories
  - User Story 4 (Security Groups): Can start after Foundational - Validates security groups created in Phase 2
  - User Story 3 (Services): Depends on User Story 1 (cluster) and User Story 2 (task definitions) completion
  - User Story 5 (IAM Roles): Can start after Foundational - Refines task roles created in Phase 2
- **Observability (Phase 8)**: Depends on User Story 3 (services created)
- **Stack Integration (Phase 9)**: Depends on all user stories being complete
- **Polish (Phase 10)**: Depends on all implementation being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P1)**: Can start after Foundational (Phase 2) - Validates security groups created in Phase 2
- **User Story 3 (P2)**: Depends on User Story 1 and User Story 2 completion
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) - Refines task roles

### Within Each User Story

- Task roles before task definitions
- Security groups before services
- Task definitions before services
- Target groups before services
- Services before auto-scaling policies
- Implementation before contract tests

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- User Story 1, User Story 2, and User Story 4 can start in parallel after Foundational phase
- All task role creation tasks (T018, T019) can run in parallel
- All CloudWatch log group creation tasks (T020, T021) can run in parallel
- All security group contract tests (T027-T029) can run in parallel
- All service auto-scaling configuration tasks (T035, T036) can run in parallel
- All CloudWatch alarm creation tasks (T045-T047) can run in parallel
- Documentation tasks (T064, T065) can run in parallel

---

## Parallel Example: User Story 2

```bash
# Launch all task role creation tasks together:
Task: "Create BFF task role with CloudWatch Logs write and SSM Parameter Store read permissions"
Task: "Create AgentCore task role with full Bedrock agent access, S3 read/write, and SSM Parameter Store read permissions"

# Launch all CloudWatch log group creation tasks together:
Task: "Create CloudWatch log group for BFF service with 7-day retention"
Task: "Create CloudWatch log group for AgentCore service with 7-day retention"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (ECS Cluster)
4. Complete Phase 4: User Story 2 (Task Definitions)
5. **STOP and VALIDATE**: Deploy cluster and task definitions, validate via `aws ecs describe-clusters` and `aws ecs describe-task-definition`

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Cluster) → Test independently → MVP infrastructure ready
3. Add User Story 2 (Task Definitions) → Test independently → Tasks defined
4. Add User Story 4 (Security Groups) → Test independently → Network isolation validated
5. Add User Story 3 (Services) → Test independently → Services running with ALB integration
6. Add User Story 5 (IAM Roles) → Test independently → Least-privilege access validated
7. Add Observability (Phase 8) → Test independently → Monitoring configured
8. Add Stack Integration (Phase 9) → Test independently → Cross-stack dependencies validated
9. Polish (Phase 10) → Final validation and documentation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Cluster)
   - Developer B: User Story 2 (Task Definitions)
   - Developer C: User Story 4 (Security Groups)
3. After US1 & US2 complete:
   - Developer A: User Story 3 (Services)
4. After Foundational:
   - Developer B: User Story 5 (IAM Roles)
5. After US3 completes:
   - Developer C: Observability (Phase 8)
6. After all user stories:
   - Developer A: Stack Integration (Phase 9)
   - Developer B: Polish (Phase 10)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Contract tests validate CloudFormation outputs match expectations
- Unit tests verify CDK resource configuration before deployment
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

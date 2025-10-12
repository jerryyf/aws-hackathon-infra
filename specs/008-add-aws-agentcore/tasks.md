# Task List: AWS AgentCore Runtime Infrastructure

**Feature**: Add AWS Bedrock AgentCore Runtime Infrastructure
**Branch**: `008-add-aws-agentcore`
**Status**: Draft

## Overview

This task list organizes the implementation of AWS Bedrock AgentCore runtime infrastructure following the feature specification. Tasks are organized by user story priority with clear dependencies and parallel execution opportunities.

## Feature Summary

Add AWS Bedrock AgentCore runtime infrastructure to enable containerized AI agent deployments. Implementation creates a new CDK stack (`AgentCoreStack`) using L1 constructs (`CfnRuntime`) to deploy agent containers from ECR within existing VPC infrastructure, with proper IAM roles, network configuration, and multi-AZ support.

## Task Dependencies

1. Config + Storage (no dependencies)
2. Security (no dependencies)
3. Network (no dependencies)
4. AgentCore (depends on Network, Security, Storage)
5. App wiring (depends on all stacks)
6. Tests (depend on implementation)

## Task Execution Order

- Phase 1: Setup (project initialization)
- Phase 2: Foundational (blocking prerequisites for all user stories)
- Phase 3: User Story 1 (Deploy Agent Runtime Container - P1)
- Phase 4: User Story 2 (Configure VPC Networking - P2)
- Phase 5: User Story 3 (Manage IAM Permissions - P2)
- Phase 6: User Story 4 (Enable VPC Interface Endpoints - P3)
- Phase 7: Polish & Cross-Cutting Concerns

---

## Phase 1: Setup Tasks

### T001: Update feature configuration

- **Description**: Add AgentCore stack configuration to config.py
- **File**: `cdk/config.py`
- **Story**: [Setup]
- **Type**: Implementation

### T002: Create ECR repository for agent images

- **Description**: Add ECR repository for storing agent container images with KMS encryption at rest
- **File**: `cdk/stacks/storage_stack.py`
- **Story**: [Setup]
- **Type**: Implementation

### T003: Create IAM execution role

- **Description**: Add IAM execution role with trust policy allowing bedrock-agentcore.amazonaws.com
- **File**: `cdk/stacks/security_stack.py`
- **Story**: [Setup]
- **Type**: Implementation

## Phase 2: Foundational Tasks

### T004: Add VPC interface endpoint for AgentCore

- **Description**: Create VPC interface endpoint for bedrock-agentcore service
- **File**: `cdk/stacks/network_stack.py`
- **Story**: [Foundational]
- **Type**: Implementation

## Phase 3: User Story 1 - Deploy Agent Runtime Container (Priority: P1)

### US1: Deploy Agent Runtime Container

**Goal**: Deploy AWS AgentCore runtime containers to enable AI agent execution within existing infrastructure

**Independent Test Criteria**: Can be fully tested by deploying a simple agent container to ECR, creating the agent runtime using AWS CDK, and verifying the runtime status is ACTIVE

### T005: Create CfnRuntime resource

- **Description**: Create CfnRuntime resource in new stack with required properties
- **File**: `cdk/stacks/agentcore_stack.py`
- **Story**: [US1]
- **Type**: Implementation
- **Dependencies**: T001, T003, T004

### T006: Configure runtime properties

- **Description**: Configure runtime properties including container URI, execution role, and network mode
- **File**: `cdk/stacks/agentcore_stack.py`
- **Story**: [US1]
- **Type**: Implementation
- **Dependencies**: T005

### T007: Define runtime outputs

- **Description**: Define CloudFormation outputs as per contract including RuntimeArn, RuntimeId, RuntimeEndpointUrl, ExecutionRoleArn
- **File**: `cdk/stacks/agentcore_stack.py`
- **Story**: [US1]
- **Type**: Implementation
- **Dependencies**: T006

### T008: Implement runtime status validation

- **Description**: Validate that runtime status is ACTIVE upon successful deployment
- **File**: `cdk/stacks/agentcore_stack.py`
- **Story**: [US1]
- **Type**: Implementation
- **Dependencies**: T007

### T009: Add integration tests for runtime deployment

- **Description**: Write integration test to verify runtime deployment to ACTIVE status
- **File**: `tests/integration/test_agentcore_deployment.py`
- **Story**: [US1]
- **Type**: Testing
- **Dependencies**: T005

## Phase 4: User Story 2 - Configure VPC Networking (Priority: P2)

### US2: Configure VPC Networking for Agent Runtimes

**Goal**: Enable secure access to internal resources while maintaining compliance with network security policies

**Independent Test Criteria**: Can be tested by deploying an agent runtime with VPC network mode, verifying it can access resources in private subnets, and confirming it cannot be accessed from public internet

### T010: Configure VPC network mode

- **Description**: Configure agent runtime to operate within existing VPC infrastructure using designated subnets and security groups
- **File**: `cdk/stacks/agentcore_stack.py`
- **Story**: [US2]
- **Type**: Implementation
- **Dependencies**: T005

### T011: Configure network configuration

- **Description**: Integrate network configuration with existing VPC private subnets
- **File**: `cdk/stacks/agentcore_stack.py`
- **Story**: [US2]
- **Type**: Implementation
- **Dependencies**: T010

### T012: Add VPC access test

- **Description**: Write integration test to verify VPC-mode runtime access to private resources
- **File**: `tests/integration/test_agentcore_vpc_access.py`
- **Story**: [US2]
- **Type**: Testing
- **Dependencies**: T010

## Phase 5: User Story 3 - Manage IAM Permissions (Priority: P2)

### US3: Manage IAM Permissions for Agent Runtime Execution

**Goal**: Configure IAM roles and policies for agent runtimes with least-privilege principles

**Independent Test Criteria**: Can be tested by creating an execution role with specific permissions, attaching it to an agent runtime, and verifying the agent can only access permitted resources

### T013: Implement execution role permissions

- **Description**: Implement IAM permissions for Bedrock, ECR, and CloudWatch access
- **File**: `cdk/stacks/security_stack.py`
- **Story**: [US3]
- **Type**: Implementation
- **Dependencies**: T003

### T014: Add IAM permission validation

- **Description**: Validate that IAM permissions work correctly during CDK synthesis
- **File**: `cdk/stacks/agentcore_stack.py`
- **Story**: [US3]
- **Type**: Implementation
- **Dependencies**: T013

### T015: Add contract test for execution role

- **Description**: Write contract test to verify IAM role trust and permissions
- **File**: `tests/contract/test_agentcore_execution_role_contract.py`
- **Story**: [US3]
- **Type**: Testing
- **Dependencies**: T014

## Phase 6: User Story 4 - Enable VPC Interface Endpoints (Priority: P3)

### US4: Enable VPC Interface Endpoints for AgentCore

**Goal**: Enable private connectivity for compliance requirements and data residency

**Independent Test Criteria**: Can be tested by creating VPC endpoints for bedrock-agentcore service, configuring endpoint policies, and verifying agent runtime invocations route through the private endpoint

### T016: Configure VPC endpoint policy

- **Description**: Configure VPC endpoint policy for bedrock-agentcore service
- **File**: `cdk/stacks/network_stack.py`
- **Story**: [US4]
- **Type**: Implementation
- **Dependencies**: T004

### T017: Add VPC endpoint contract test

- **Description**: Write contract test to verify VPC endpoint configuration
- **File**: `tests/contract/test_vpc_endpoint_contract.py`
- **Story**: [US4]
- **Type**: Testing
- **Dependencies**: T016

## Phase 7: Polish & Cross-Cutting Concerns

### T018: Update README documentation

- **Description**: Update README with AgentCore deployment instructions
- **File**: `README.md`
- **Story**: [Polish]
- **Type**: Documentation

### T019: Add runtime invocation examples

- **Description**: Document runtime invocation examples (synchronous + streaming)
- **File**: `docs/quickstart.md`
- **Story**: [Polish]
- **Type**: Documentation

### T020: Update AGENTS.md with build/test commands

- **Description**: Update AGENTS.md with AgentCore-specific build/test commands
- **File**: `AGENTS.md`
- **Story**: [Polish]
- **Type**: Documentation

### T021: Add resource tagging

- **Description**: Apply resource tags (Project, Environment, Owner, CostCenter) to all AgentCore-related resources
- **File**: `cdk/stacks/agentcore_stack.py`
- **Story**: [Polish]
- **Type**: Implementation
- **Dependencies**: T005


---

## Parallel Execution Examples

### User Story 1 (P1) Parallel Tasks:
- T005, T006, T007, T008 (Creating CfnRuntime and configuring properties)

### User Story 2 (P2) Parallel Tasks:
- T010, T011 (VPC configuration tasks)

### Setup Phase Parallel Tasks:
- T001, T002, T003 (Config, Storage, Security setup)

## Implementation Strategy

- MVP First: Focus on User Story 1 (P1) to enable basic deployment
- Incremental Delivery: Add VPC networking, permissions, and VPC endpoints in subsequent phases
- Independent Testing: Each user story can be tested independently

## Task Summary

- Total Tasks: 21
- Tasks by User Story:
  - US1 (Deploy Agent Runtime Container): 5 tasks
  - US2 (Configure VPC Networking): 3 tasks
  - US3 (Manage IAM Permissions): 3 tasks
  - US4 (Enable VPC Interface Endpoints): 3 tasks
  - Setup/Foundational/Polish: 7 tasks
- Parallel Opportunities: Multiple tasks can run in parallel
- Independent Test Criteria: Each user story has independent test criteria
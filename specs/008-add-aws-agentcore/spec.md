# Feature Specification: AWS AgentCore Runtime Infrastructure

**Feature Branch**: `007-add-aws-agentcore`  
**Created**: 2025-10-10  
**Status**: Draft  
**Input**: User description: "add aws agentcore runtime. use context7 to get more information on aws agentcore"

## Clarifications

### Session 2025-10-11

- Q: The spec assumes AWS Bedrock AgentCore deployment in us-west-2, but existing infrastructure (VPC, RDS, OpenSearch) is in us-east-1 according to AGENTS.md and deployment reports. Which region should be used? → A: us-east-1 (match existing infrastructure)
- Q: For runtime deployment failure due to insufficient IAM permissions, what should the system do? → A: Fail CDK deployment with descriptive error message during synthesis/deploy
- Q: FR-010 states "integrate with existing monitoring stack" but doesn't specify which metrics or alerts are required. What specific AgentCore metrics should be monitored? → A: Runtime status, invocation count, error rate, latency (p50/p99)
- Q: The spec mentions "PrivateAgent subnets" for VPC mode but doesn't specify how many agent runtimes can be deployed concurrently. What is the maximum number of concurrent agent runtimes? → A: 2 concurrent runtimes maximum
- Q: User Story 2 Scenario 2 tests agent access to "private RDS instance" but doesn't specify if this requires additional security group rules. Should agent runtime security groups allow outbound access to RDS security groups? → A: Deferred to implementation phase

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deploy Agent Runtime Container (Priority: P1)

As an infrastructure administrator, I need to deploy AWS AgentCore runtime containers so that AI agents can run in a managed, scalable environment within our existing AWS infrastructure.

**Why this priority**: This is the foundational capability - without the ability to deploy agent runtimes, no other AgentCore features are possible. This provides immediate value by enabling the first agent deployment.

**Independent Test**: Can be fully tested by deploying a simple agent container to ECR, creating the agent runtime using AWS CDK, and verifying the runtime status is ACTIVE. Delivers a functioning agent runtime endpoint that can be invoked.

**Acceptance Scenarios**:

1. **Given** an ECR repository with an agent container image, **When** the infrastructure is deployed, **Then** an AgentCore runtime is created with status ACTIVE
2. **Given** a deployed agent runtime, **When** checking the runtime details, **Then** the runtime ARN, endpoint URL, and network configuration are accessible
3. **Given** the infrastructure is deployed, **When** invoking the agent runtime endpoint, **Then** the agent responds successfully with a valid session ID

---

### User Story 2 - Configure VPC Networking for Agent Runtimes (Priority: P2)

As a security engineer, I need agent runtimes to run within our VPC with proper network isolation so that agents can securely access internal resources while maintaining compliance with our network security policies.

**Why this priority**: Enables secure access to private resources (RDS, OpenSearch, internal APIs) without exposing them publicly. Critical for production deployments but P1 can work with PUBLIC mode for initial testing.

**Independent Test**: Can be tested by deploying an agent runtime with VPC network mode, verifying it can access resources in private subnets, and confirming it cannot be accessed from public internet.

**Acceptance Scenarios**:

1. **Given** a VPC with private subnets and security groups, **When** deploying an agent runtime with VPC network mode, **Then** the runtime is accessible only from within the VPC
2. **Given** an agent runtime in VPC mode, **When** the agent attempts to access a private RDS instance, **Then** the connection succeeds
3. **Given** an agent runtime with VPC configuration, **When** attempting to access from public internet, **Then** the request is denied

---

### User Story 3 - Manage IAM Permissions for Agent Runtime Execution (Priority: P2)

As a DevOps engineer, I need to configure IAM roles and policies for agent runtimes so that agents have exactly the permissions they need to access AWS services while following least-privilege principles.

**Why this priority**: Essential for security and compliance, but P1 can use a basic execution role for initial deployment. Fine-grained permissions can be refined after basic deployment works.

**Independent Test**: Can be tested by creating an execution role with specific permissions, attaching it to an agent runtime, and verifying the agent can only access permitted resources.

**Acceptance Scenarios**:

1. **Given** an agent runtime requiring Bedrock access, **When** the execution role is created with bedrock:InvokeModel permission, **Then** the agent can successfully invoke Bedrock models
2. **Given** an agent runtime execution role without S3 permissions, **When** the agent attempts to access S3, **Then** the request is denied with proper error handling
3. **Given** a trust policy for the execution role, **When** the AgentCore service assumes the role, **Then** the assumption succeeds with proper source account and ARN conditions

---

### User Story 4 - Enable VPC Interface Endpoints for AgentCore (Priority: P3)

As a compliance officer, I need AgentCore traffic to remain within AWS's private network so that we meet regulatory requirements for data residency and network isolation.

**Why this priority**: Important for highly regulated environments but not required for basic functionality. P1-P3 can work with public endpoints initially.

**Independent Test**: Can be tested by creating VPC endpoints for bedrock-agentcore service, configuring endpoint policies, and verifying agent runtime invocations route through the private endpoint.

**Acceptance Scenarios**:

1. **Given** a VPC interface endpoint for bedrock-agentcore, **When** an agent runtime is invoked, **Then** traffic routes through the private endpoint without traversing the internet
2. **Given** an endpoint policy restricting access to specific IAM principals, **When** an unauthorized principal attempts to invoke the runtime, **Then** the request is denied at the VPC endpoint level
3. **Given** VPC endpoints in multiple availability zones, **When** an AZ becomes unavailable, **Then** traffic automatically routes through endpoints in healthy AZs

---

### Edge Cases

- **Insufficient IAM permissions during deployment**: CDK deployment MUST fail with descriptive error message identifying missing permissions during synthesis/deploy phase (prevent runtime in FAILED state)
- **Corrupted or unavailable container image**: Runtime enters FAILED state; CloudWatch logs capture error; operator must update container URI and redeploy
- **VPC configuration errors (missing subnets/security groups)**: CDK synthesis MUST fail with validation error identifying missing resources before deployment
- **Invalid execution role trust policy**: CDK deployment fails during stack creation with IAM policy validation error
- **Concurrent ECR repository access during updates**: ECR handles concurrent pulls; no special handling required (AWS-managed behavior)
- **Invocation payload exceeding 100 MB limit**: AgentCore service returns 413 Payload Too Large error; application must handle retry with smaller payload

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create ECR repositories for storing agent container images with KMS encryption at rest
- **FR-002**: System MUST deploy agent runtimes using AWS CDK with configurable network modes (PUBLIC or VPC)
- **FR-003**: System MUST create IAM execution roles with trust policies allowing bedrock-agentcore.amazonaws.com service principal
- **FR-004**: System MUST configure agent runtimes to operate within existing VPC infrastructure using designated subnets and security groups
- **FR-005**: System MUST enable agent runtimes to access AWS Bedrock models through IAM permissions
- **FR-006**: System MUST provide agent runtime ARNs and endpoint URLs as CDK stack outputs for downstream consumption
- **FR-007**: System MUST support both synchronous and streaming invocation patterns for agent runtimes
- **FR-008**: System MUST configure VPC interface endpoints for bedrock-agentcore service to enable private connectivity
- **FR-009**: System MUST apply resource tags (Project, Environment, Owner, CostCenter) to all AgentCore-related resources
- **FR-010**: System MUST integrate with existing monitoring stack for agent runtime observability, tracking: runtime status (ACTIVE/FAILED), invocation count, error rate, and invocation latency (p50/p99 percentiles)
- **FR-011**: System MUST deploy agent runtimes across multiple availability zones for high availability (maximum 2 concurrent agent runtimes supported)
- **FR-012**: System MUST enforce encryption in transit using TLS 1.2 or higher for all agent runtime communications

### Key Entities *(include if feature involves data)*

- **Agent Runtime**: Represents a deployed containerized agent application managed by AgentCore service; has ARN, endpoint URL, network configuration, execution role, and status (CREATING, ACTIVE, FAILED)
- **Execution Role**: IAM role assumed by the agent runtime; contains trust policy for bedrock-agentcore.amazonaws.com and permissions policies for accessing AWS services
- **Agent Runtime Artifact**: Container configuration including ECR image URI and runtime settings
- **Network Configuration**: Defines how the agent runtime connects to network resources; includes network mode (PUBLIC/VPC), subnets, and security groups
- **VPC Interface Endpoint**: Private connection between VPC and AgentCore service; has endpoint policies controlling access at network level

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Infrastructure can deploy an agent runtime from container image to ACTIVE status in under 10 minutes
- **SC-002**: Agent runtimes can handle invocations with payloads up to 100 MB without errors
- **SC-003**: Agent runtime endpoints respond to health check invocations within 2 seconds
- **SC-004**: VPC-mode agent runtimes can access resources in private subnets with sub-100ms latency overhead compared to PUBLIC mode
- **SC-005**: Agent runtime infrastructure survives single AZ failure without service interruption
- **SC-006**: IAM permission misconfigurations are detected and reported during CDK synthesis before deployment
- **SC-007**: All agent runtime communications use TLS 1.2 or higher encryption as verified by network traffic inspection

## Assumptions

- AWS Bedrock AgentCore service is available in us-east-1 (deployment region matching existing VPC, RDS, and OpenSearch infrastructure)
- Agent container images follow the AgentCore runtime contract (expose /invocations and/or /mcp endpoints)
- Existing VPC infrastructure has sufficient IP address capacity for additional ENIs required by VPC-mode agent runtimes
- Container images are stored in ECR within the same AWS account and region
- Agent runtimes will use the default qualifier (DEFAULT) for initial deployments
- Session management will use 33+ character session IDs as required by the AgentCore service
- Agent runtime invocations will respect the 15-minute timeout limit for synchronous requests
- The bedrock-agentcore-starter-toolkit is not required for infrastructure deployment (infrastructure supports custom agent deployments)

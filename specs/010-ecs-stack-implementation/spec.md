# Feature Specification: ECS Stack Infrastructure for Containerized Workloads

**Feature Branch**: `010-ecs-stack-implementation`  
**Created**: 2025-10-18  
**Status**: Draft  
**Input**: User description: "ECS stack implementation in python CDK"

## User Scenarios & Testing

### User Story 1 - Deploy ECS Cluster with Fargate Support (Priority: P1)

Platform operators need to provision an ECS cluster with Fargate compute capacity to run containerized application workloads (BFF frontend and AgentCore runtime services) without managing EC2 instances. The cluster must integrate with existing VPC networking and security infrastructure.

**Why this priority**: Core infrastructure requirement - without an ECS cluster, no containerized workloads can be deployed. This is the foundational component that enables all application deployments.

**Independent Test**: Can be fully tested by deploying the ECS cluster and verifying cluster status, Fargate capacity provider configuration, and integration with the existing VPC from NetworkStack.

**Acceptance Scenarios**:

1. **Given** NetworkStack is deployed with VPC and subnets, **When** ECS stack is deployed, **Then** an ECS cluster is created with Fargate and Fargate Spot capacity providers
2. **Given** ECS cluster exists, **When** checking cluster configuration, **Then** cluster integrates with existing VPC private subnets (PrivateApp, PrivateAgent, PrivateData)
3. **Given** ECS cluster exists, **When** checking container insights, **Then** CloudWatch Container Insights is enabled for observability
4. **Given** ECS cluster is provisioned, **When** validating capacity providers, **Then** default strategy assigns 70% weight to Fargate and 30% to Fargate Spot for cost optimization

---

### User Story 2 - Create Fargate Task Definitions for Application Services (Priority: P1)

Platform operators need to define ECS task definitions for containerized workloads (BFF frontend and AgentCore runtime) with appropriate CPU/memory allocations, execution roles, and environment-specific resource scaling.

**Why this priority**: Task definitions are required to run any containers on ECS. Without these, the cluster cannot execute workloads. This is a prerequisite for service deployment.

**Independent Test**: Can be tested by creating task definitions and validating their IAM roles, resource allocations, CloudWatch log configuration, and ECR image pull permissions.

**Acceptance Scenarios**:

1. **Given** ECS cluster exists, **When** task definitions are created, **Then** separate task definitions exist for BFF and AgentCore runtime services
2. **Given** task definitions are created, **When** checking IAM configuration, **Then** each task has task execution role with ECR pull, CloudWatch logs, and Secrets Manager access permissions
3. **Given** task definitions exist, **When** validating resource allocation, **Then** CPU and memory settings match environment requirements (dev: 512 CPU/1024 MiB, test: 1024 CPU/2048 MiB, prod: 2048 CPU/4096 MiB)
4. **Given** task definitions are configured, **When** checking logging, **Then** CloudWatch log groups are created with log stream prefix for each service
5. **Given** AgentCore task definition exists, **When** validating Bedrock integration, **Then** task role includes permissions for bedrock-runtime:InvokeModel and bedrock-agent-runtime:InvokeAgent

---

### User Story 3 - Deploy ECS Services with Load Balancer Integration (Priority: P2)

Platform operators need to deploy ECS services that automatically register containers with Application Load Balancer (BFF only), handle health checks, and maintain desired task counts with auto-scaling capabilities.

**Why this priority**: Services manage the lifecycle of tasks and integrate with load balancers for traffic routing. This enables production-ready deployments with high availability and automatic recovery.

**Independent Test**: Can be tested by deploying ECS services, verifying task health checks, load balancer target registration (BFF), and auto-scaling policies respond to CloudWatch metrics.

**Acceptance Scenarios**:

1. **Given** ECS cluster and task definitions exist, **When** services are deployed, **Then** BFF service registers with public ALB and AgentCore service runs without load balancer
2. **Given** services are running, **When** checking deployment configuration, **Then** services use rolling update strategy with minimum 50% healthy tasks during deployment
3. **Given** services are operational, **When** validating high availability, **Then** each service runs minimum 2 tasks distributed across availability zones
4. **Given** BFF service is deployed, **When** monitoring task health, **Then** unhealthy tasks are automatically replaced and deregistered from load balancer
5. **Given** services are under load, **When** CloudWatch metrics exceed thresholds, **Then** auto-scaling policies adjust task count between minimum (2) and maximum (10) tasks

---

### User Story 4 - Configure Security Groups and Network Isolation (Priority: P1)

Platform operators need to configure security groups that enforce network isolation between service tiers (public, application, agent, data) following the principle of least privilege.

**Why this priority**: Security is foundational. Without proper security group configuration, services may be inaccessible or overly exposed to security risks.

**Independent Test**: Can be tested by validating security group rules, verifying inbound/outbound traffic restrictions, and confirming services can only communicate through permitted ports/protocols.

**Acceptance Scenarios**:

1. **Given** ECS services are deployed, **When** checking security groups, **Then** BFF containers allow inbound traffic only from public ALB security group on port 3000
2. **Given** security groups exist, **When** validating agent isolation, **Then** AgentCore containers accept traffic only from BFF security group on port 8080
3. **Given** AgentCore service is running, **When** checking network access, **Then** agent containers can reach VPC endpoints for Bedrock, SSM Parameter Store, and CloudWatch but have no internet access
4. **Given** services need database access, **When** validating data tier connectivity, **Then** application and agent security groups allow outbound traffic to RDS security group on port 5432
5. **Given** security groups are configured, **When** auditing network rules, **Then** no security group allows 0.0.0.0/0 inbound access except public ALB on ports 80/443

---

### User Story 5 - Integrate Task IAM Roles for AWS Service Access (Priority: P2)

Platform operators need to configure IAM task roles that grant containers least-privilege access to AWS services (Bedrock, S3, SSM Parameter Store, RDS) without managing credentials in code.

**Why this priority**: Task IAM roles enable secure, credential-less access to AWS services. This is critical for security and operational simplicity but can be configured after basic service deployment.

**Independent Test**: Can be tested by executing tasks and verifying they can access permitted AWS services (read SSM Parameter Store, invoke Bedrock, write to CloudWatch) but cannot access unauthorized resources.

**Acceptance Scenarios**:

1. **Given** ECS tasks are running, **When** containers access SSM Parameter Store, **Then** tasks retrieve database credentials and API keys without embedded credentials
2. **Given** AgentCore tasks are operational, **When** invoking Bedrock, **Then** tasks successfully call bedrock-runtime:InvokeModel using task role credentials
3. **Given** AgentCore tasks need S3 access, **When** uploading objects, **Then** tasks can write to knowledge base S3 bucket using task role permissions
4. **Given** task roles are configured, **When** auditing permissions, **Then** roles follow least privilege (BFF has no Bedrock access, agent has full Bedrock and S3 access)

---

### Edge Cases

- What happens when task execution role cannot pull images from ECR? (Task launch fails with clear error message; CloudWatch logs capture authentication/permission errors)
- How does the system handle tasks that exceed memory limits? (ECS kills the task with OOM error; service automatically launches replacement task)
- What occurs when all BFF tasks become unhealthy? (Load balancer returns 503 errors; CloudWatch alarms trigger; ECS attempts to launch new tasks until desired count is reached)
- How are tasks distributed when one availability zone fails? (ECS automatically launches replacement tasks in healthy AZ; load balancer routes traffic only to healthy targets for BFF)
- What happens when Fargate capacity is unavailable? (Task placement fails with capacity error; can be mitigated by using Fargate Spot as fallback capacity provider)
- How does the system handle rapid scaling events? (Auto-scaling cooldown periods prevent thrashing; ECS places tasks as capacity becomes available)
- How does BFF communicate with AgentCore? (Direct HTTP calls to AgentCore ECS service discovery endpoint or private IP on port 8080)

## Requirements

### Functional Requirements

**ECS Cluster Configuration**
- **FR-001**: System MUST provision an ECS cluster using Fargate compute capacity (serverless container management)
- **FR-002**: System MUST integrate ECS cluster with existing VPC from NetworkStack
- **FR-003**: System MUST enable CloudWatch Container Insights for cluster-level metrics and logging
- **FR-004**: System MUST configure Fargate capacity provider with default weight of 70% for on-demand capacity
- **FR-005**: System MUST configure Fargate Spot capacity provider with weight of 30% for cost optimization

**Task Definitions**
- **FR-006**: System MUST create task definition for BFF service (Next.js frontend) with environment-based resource allocation
- **FR-007**: System MUST create task definition for AgentCore runtime service with environment-based resource allocation
- **FR-008**: Task definitions MUST specify awsvpc network mode for ENI-based networking in VPC
- **FR-009**: Task definitions MUST include task execution role with permissions for: ECR image pull (ecr:GetAuthorizationToken, ecr:BatchCheckLayerAvailability, ecr:GetDownloadUrlForLayer, ecr:BatchGetImage), CloudWatch logs write (logs:CreateLogStream, logs:PutLogEvents), and SSM Parameter Store read (ssm:GetParameter, ssm:GetParameters)
- **FR-010**: Task definitions MUST configure CloudWatch log groups with log stream prefix matching service name
- **FR-011**: Task definitions MUST specify container image URIs pointing to ECR repositories from StorageStack (BFF uses bidopsai/app repo, AgentCore uses bidopsai/agent repo)
- **FR-012**: Container definitions MUST include essential flag set to true for service-critical containers
- **FR-013**: Container definitions MUST specify environment variables for AWS_REGION, ENVIRONMENT, and service-specific configuration
- **FR-014**: Container definitions MUST mount secrets from SSM Parameter Store as environment variables for database credentials and API keys
- **FR-015**: Containers MUST expose ports: BFF (3000), AgentCore (8080)

**Task IAM Roles**
- **FR-016**: BFF task role MUST allow CloudWatch logs write and SSM Parameter Store read for configuration access
- **FR-017**: AgentCore task role MUST allow full Bedrock agent access (bedrock-agent-runtime:InvokeAgent, bedrock-runtime:InvokeModel), SSM Parameter Store read, and S3 read/write for knowledge base bucket
- **FR-018**: Task roles MUST NOT include permissions for resource deletion or infrastructure modification

**ECS Services**
- **FR-019**: System MUST create ECS service for BFF with desired task count of 2 for high availability
- **FR-020**: System MUST create ECS service for AgentCore runtime with desired task count of 2 for high availability
- **FR-021**: ComputeStack MUST create target group for BFF service and register tasks with public ALB (from NetworkStack) on port 3000
- **FR-022**: AgentCore service MUST enable ECS Service Discovery for private DNS-based service communication from BFF
- **FR-023**: Services MUST deploy tasks across multiple availability zones (us-east-1a and us-east-1b) for resilience
- **FR-024**: Services MUST use rolling update deployment strategy with minimum healthy percentage of 50% and maximum percentage of 200%

**Security Groups**
- **FR-025**: System MUST create security group for BFF tasks allowing inbound traffic from public ALB security group on port 3000
- **FR-026**: System MUST create security group for AgentCore tasks allowing inbound traffic from BFF security group on port 8080
- **FR-027**: BFF security group MUST allow outbound traffic to AgentCore security group on port 8080
- **FR-028**: All ECS security groups MUST allow outbound traffic to VPC endpoints (port 443) for AWS service access
- **FR-029**: ECS security groups MUST allow outbound traffic to RDS security group on port 5432 for database connectivity
- **FR-030**: Security groups MUST NOT allow unrestricted inbound access (0.0.0.0/0) to ECS tasks

**Service Subnet Placement**
- **FR-031**: BFF service MUST deploy tasks to PrivateApp subnets (10.0.11.0/24, 10.0.12.0/24)
- **FR-032**: AgentCore service MUST deploy tasks to PrivateAgent subnets (10.0.21.0/24, 10.0.22.0/24)

**Health Checks & Load Balancing**
- **FR-033**: ComputeStack MUST create BFF target group with health check on path /api/health (30-second interval) and attach to public ALB from NetworkStack
- **FR-034**: Health checks MUST mark tasks unhealthy after 3 consecutive failures and healthy after 2 consecutive successes
- **FR-035**: Load balancer MUST automatically deregister unhealthy targets and route traffic only to healthy tasks

**Auto-Scaling**
- **FR-037**: Services MUST configure auto-scaling policies with minimum task count of 2 and maximum of 10
- **FR-038**: Auto-scaling MUST trigger when average CPU utilization exceeds 70% for 3 consecutive minutes
- **FR-039**: Auto-scaling MUST trigger when average memory utilization exceeds 80% for 3 consecutive minutes
- **FR-040**: Auto-scaling MUST include cooldown period of 300 seconds (5 minutes) to prevent thrashing

**Resource Allocation by Environment**
- **FR-041**: In dev environment, tasks MUST use 512 CPU units (0.5 vCPU) and 1024 MiB memory
- **FR-042**: In test environment, tasks MUST use 1024 CPU units (1 vCPU) and 2048 MiB memory
- **FR-043**: In prod environment, tasks MUST use 2048 CPU units (2 vCPU) and 4096 MiB memory



**Observability**
- **FR-044**: All task definitions MUST configure CloudWatch log groups with 7-day retention period
- **FR-045**: System MUST create CloudWatch alarms for service task count below desired count (indicates service degradation)
- **FR-046**: System MUST create CloudWatch alarms for unhealthy target count in BFF load balancer target group

**Stack Integration**
- **FR-047**: ComputeStack MUST accept NetworkStack as dependency for VPC, subnet, security group, and ALB references
- **FR-048**: ComputeStack MUST accept StorageStack as dependency for ECR repository URIs (bidopsai/app for BFF, bidopsai/agent for AgentCore)
- **FR-049**: ComputeStack MUST accept SecurityStack as dependency for SSM Parameter Store ARNs
- **FR-050**: ComputeStack MUST export service ARNs, cluster ARN, task definition ARNs, and Service Discovery namespace as CloudFormation outputs

### Key Entities

- **ECS Cluster**: Container orchestration cluster providing Fargate compute capacity for running containerized workloads without managing servers
- **Fargate Capacity Provider**: Serverless compute engine for ECS with on-demand and Spot pricing options
- **Task Definition**: Blueprint specifying container image, CPU/memory requirements, IAM roles, networking, and logging configuration
- **ECS Service**: Orchestration layer maintaining desired task count, integrating with load balancers (BFF only), and managing rolling deployments
- **Task Execution Role**: IAM role assumed by ECS agent to pull images, write logs, and retrieve parameters from SSM on behalf of tasks
- **Task Role**: IAM role assumed by application code running in containers to access AWS services (Bedrock, S3, SSM Parameter Store)
- **Container Definition**: Specification within task definition defining Docker image, ports, environment variables, and resource limits
- **Target Group**: Load balancer routing target containing registered ECS tasks (BFF only) with health check configuration
- **Service Security Group**: Network firewall rules controlling inbound/outbound traffic for ECS tasks
- **Auto-Scaling Policy**: Rules defining when and how to adjust task count based on CloudWatch metrics (CPU, memory, request count)
- **CloudWatch Log Group**: Log aggregation destination for container stdout/stderr streams
- **Container Insights**: CloudWatch feature providing cluster, service, and task-level metrics for observability
- **ECS Service Discovery**: Private DNS-based service discovery enabling BFF to discover AgentCore tasks by DNS name

## Success Criteria

### Measurable Outcomes

- **SC-001**: Platform operators can deploy containerized workloads to ECS cluster within 10 minutes of committing container images to ECR
- **SC-002**: ECS services automatically recover from task failures by launching replacement tasks within 60 seconds
- **SC-003**: BFF service maintains 99.9% availability during rolling deployments (measured as percentage of time with at least 1 healthy task running)
- **SC-004**: Auto-scaling policies adjust task count within 5 minutes of sustained metric threshold breach (CPU > 70%, memory > 80%)
- **SC-005**: Load balancer health checks detect unhealthy BFF tasks within 90 seconds (3 failures × 30-second interval)
- **SC-006**: ECS tasks can authenticate to AWS services (Bedrock, S3, SSM Parameter Store) without embedded credentials using task IAM roles
- **SC-007**: Container logs are available in CloudWatch within 30 seconds of log emission from container
- **SC-008**: System cost is reduced by 30% through Fargate Spot capacity provider for non-production workloads
- **SC-009**: ECS services maintain operation during single availability zone failure with automatic task redistribution to healthy AZ
- **SC-010**: All ECS security groups pass compliance scan with no unrestricted inbound access (0.0.0.0/0) to container ports
- **SC-011**: BFF can discover and communicate with AgentCore tasks via ECS Service Discovery DNS within 5 seconds of task startup

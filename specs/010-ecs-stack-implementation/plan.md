# Implementation Plan: ECS Stack Infrastructure for Containerized Workloads

**Branch**: `010-ecs-stack-implementation` | **Date**: 2025-10-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-ecs-stack-implementation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enhance the existing `ComputeStack` to provision production-ready ECS infrastructure with Fargate compute capacity, task definitions for BFF/AgentCore services, ECS services with auto-scaling and load balancer integration (BFF only), security groups enforcing network isolation, ECS Service Discovery for private service communication, and IAM roles for least-privilege AWS service access. This transforms the minimal placeholder ECS cluster into a fully operational container orchestration platform supporting two-tier application architecture (BFF frontend calling AgentCore backend directly).

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: AWS CDK 2.x (aws-cdk-lib), constructs  
**Storage**: RDS Aurora PostgreSQL (from DatabaseStack), OpenSearch (from DatabaseStack), S3 buckets (from StorageStack)  
**Testing**: pytest with CDK Template assertions, contract tests validating CloudFormation outputs  
**Target Platform**: AWS ECS Fargate (us-east-1, multi-AZ deployment)  
**Project Type**: Infrastructure as Code (single CDK application)  
**Performance Goals**: Task launch time <60s, auto-scale response <5 min, 99.9% availability during deployments  
**Constraints**: Fargate-only (no EC2), multi-AZ resilience, <$500/month dev environment cost, security group least-privilege  
**Scale/Scope**: 3 services (BFF, GraphQL, AgentCore), 2-10 tasks per service, 6-30 concurrent containers

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **I. AWS Well-Architected Framework**
- Operational Excellence: CloudWatch Container Insights, structured logging, CloudWatch alarms for operational metrics
- Security: Least-privilege IAM roles, private subnet deployment, VPC endpoints for AWS services, no 0.0.0.0/0 inbound access
- Reliability: Multi-AZ task placement, auto-scaling, automatic unhealthy task replacement, rolling deployments
- Performance Efficiency: Fargate serverless compute, auto-scaling based on CPU/memory metrics, environment-based resource allocation
- Cost Optimization: Fargate Spot (30% weight), right-sized task resources per environment, tagged resources for cost tracking
- Sustainability: Serverless compute maximizes utilization, Spot capacity reduces waste

✅ **II. Infrastructure as Code Excellence**
- All resources defined in CDK Python code (`cdk/stacks/compute_stack.py`)
- Version controlled, peer reviewed pull requests
- No manual console changes (all infrastructure in code)
- Secrets managed via Secrets Manager (from SecurityStack)
- Modular stack design with explicit dependencies

✅ **III. Security & Compliance First**
- Least-privilege IAM: Task execution roles (ECR/CloudWatch/SSM), task roles (service-specific AWS access)
- Defense-in-depth: Security groups per service tier, private subnet deployment, VPC endpoints (no public internet)
- Encryption: Container images in ECR (encrypted at rest), TLS 1.2+ for ALB traffic, SSM Parameter Store encrypted
- Audit trail: CloudWatch Logs (7-day retention), CloudTrail enabled (MonitoringStack)
- Network isolation: BFF → public ALB only, AgentCore → BFF only (no inbound from internet)

✅ **IV. Code Quality & Maintainability**
- Type hints on all functions (Python 3.11+ syntax: `str | None`)
- Black formatting (line-length 88), pylint linting
- Pyright type checking enforced
- Comprehensive unit tests (`tests/unit/test_compute_stack.py`), contract tests (`tests/contract/`)
- Code review required before merge

✅ **V. Extensibility & Modularity**
- Stack accepts dependencies as constructor parameters (`network_stack`, `storage_stack`, `security_stack`, `database_stack`)
- CloudFormation outputs for service ARNs, cluster ARN, task definition ARNs (enables future stack integration)
- Environment-agnostic design (resources sized via `config.py` environment variable)
- Capacity provider strategy supports future scaling patterns

✅ **VI. Observability & Operational Excellence**
- CloudWatch Container Insights enabled on cluster
- Structured logs to CloudWatch with service-specific log groups (7-day retention)
- CloudWatch alarms: task count below desired, unhealthy targets in load balancers
- Health check endpoints: `/api/health` (BFF), `/graphql` (backend)
- AWS X-Ray integration (to be implemented in application code)

✅ **AWS-Specific Standards**
- Multi-AZ: Tasks distributed across us-east-1a and us-east-1b
- Managed services: Fargate (serverless), ALB (from NetworkStack), RDS (from DatabaseStack)
- Right-sizing: Environment-based resource allocation (dev: 0.5 vCPU/1GB, test: 1 vCPU/2GB, prod: 2 vCPU/4GB)
- Tagging: All resources tagged with Project, Environment, Owner, CostCenter (via CDK tags)

✅ **Development Standards**
- Feature branch workflow: `010-ecs-stack-implementation` → PR → code review → main
- Automated testing: Unit tests (`pytest tests/unit/`), contract tests (`pytest tests/contract/`)
- CDK validation: `cdk synth` before deploy, `cdk diff` for change review
- Rollback: CloudFormation stack rollback on failure, versioned task definitions for manual rollback

**CONSTITUTIONAL COMPLIANCE**: ✅ PASSED

## Project Structure

### Documentation (this feature)

```
specs/010-ecs-stack-implementation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (existing CDK patterns, ECS best practices)
├── data-model.md        # Phase 1 output (ECS entities, IAM roles, security groups)
├── quickstart.md        # Phase 1 output (deployment commands, validation steps)
├── contracts/           # Phase 1 output (CloudFormation output contracts)
├── checklists/
│   └── requirements.md  # Quality validation checklist (already created)
└── spec.md              # Feature specification (already created)
```

### Source Code (repository root)

```
cdk/
├── stacks/
│   ├── __init__.py
│   ├── compute_stack.py         # ENHANCE: Transform from placeholder to production ECS stack
│   ├── network_stack.py         # EXISTING: VPC, ALBs, security groups (dependency)
│   ├── database_stack.py        # EXISTING: RDS, OpenSearch (dependency)
│   ├── storage_stack.py         # EXISTING: S3, ECR repositories (dependency)
│   ├── security_stack.py        # EXISTING: Cognito, Secrets Manager (dependency)
│   └── monitoring_stack.py      # EXISTING: CloudWatch, CloudTrail (dependency)
├── app.py                       # MODIFY: Update ComputeStack instantiation with stack dependencies
├── config.py                    # ENHANCE: Add ECS resource configuration (CPU, memory, task counts)
├── cdk.json
├── requirements.txt             # VERIFY: Ensure aws-cdk-lib dependencies are current
├── pyproject.toml
└── pyrightconfig.json

tests/
├── unit/
│   └── test_compute_stack.py    # ENHANCE: Add comprehensive unit tests for ECS resources
├── contract/
│   ├── test_ecs_cluster_contract.py        # NEW: Validate cluster ARN output
│   ├── test_ecs_services_contract.py       # NEW: Validate service ARNs output
│   └── test_task_definitions_contract.py   # NEW: Validate task definition ARNs output
└── conftest.py                  # EXISTING: Pytest fixtures

docs/
└── deployment/
    └── ecs-deployment-report_2025-10-18.md  # NEW: Deployment validation report
```

**Structure Decision**: Single CDK application with modular stacks. The `ComputeStack` will be enhanced from its current minimal state (basic cluster + placeholder nginx task) to a production-ready implementation with:
1. ECS cluster with Fargate capacity providers (on-demand + Spot)
2. Task definitions for BFF and AgentCore (replacing placeholder nginx task)
3. Task execution roles (ECR pull, CloudWatch logs, SSM Parameter Store access)
4. Task roles (service-specific AWS access: Bedrock for AgentCore, limited access for BFF)
5. Target group for BFF (created in ComputeStack, attached to public ALB from NetworkStack)
6. ECS Service Discovery namespace for AgentCore private service communication
7. ECS services with load balancer integration (public ALB for BFF only)
8. Security groups per service tier (BFF allows ALB inbound, AgentCore allows BFF inbound)
9. Auto-scaling policies (CPU, memory thresholds)
10. CloudWatch log groups and alarms

This approach maintains the existing project structure and enhances the already-deployed `ComputeStack` rather than creating a new stack.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

No constitutional violations detected. All complexity is justified by requirements:
- **Two task definitions** (BFF, AgentCore): Required to support two-tier application architecture with distinct security boundaries
- **Multiple IAM roles** (1 shared task execution role, 2 task roles): Required for least-privilege security model per service
- **Environment-based configuration**: Required for cost optimization (dev uses fewer resources than prod)
- **ECS Service Discovery**: Required for private service-to-service communication without exposing AgentCore to load balancer

## Phase 0: Research

**Objective**: Understand existing CDK patterns, ECS best practices, and stack integration points.

**Research Questions**:
1. What ECS constructs are available in `aws-cdk.aws-ecs` for Fargate task definitions, services, and capacity providers?
2. How does the existing `ComputeStack` integrate with `NetworkStack` (VPC, subnets, ALBs)?
3. What IAM policies are required for task execution roles (ECR, CloudWatch, Secrets Manager)?
4. How are task roles configured for AWS service access (Bedrock, S3)?
5. What security group patterns are used in `NetworkStack` for ALB and database access?
6. How are CloudFormation outputs structured in existing stacks for cross-stack references?
7. What environment-specific configuration patterns exist in `config.py`?
8. How are contract tests structured in `tests/contract/` for validating CloudFormation outputs?

**Deliverable**: `research.md` documenting:
- CDK ECS L2 construct patterns (`ecs.FargateTaskDefinition`, `ecs.FargateService`, `ecs.CapacityProvider`)
- Existing stack integration patterns (`network_stack.vpc`, `network_stack.public_alb`, `storage_stack.ecr_repo_uri`)
- IAM role patterns from existing stacks
- Security group reference patterns
- Environment configuration strategy
- Contract test patterns

## Phase 1: Design

**Objective**: Design data model (ECS entities, IAM roles), CloudFormation output contracts, and deployment quickstart.

**Design Artifacts**:
1. **Data Model** (`data-model.md`):
   - ECS Cluster entity (name, capacity providers, VPC reference)
   - Task Definition entities (BFF, AgentCore: CPU, memory, container definitions)
   - Task Execution Role entity (ECR, CloudWatch, SSM Parameter Store policies)
   - Task Role entities (BFF: CloudWatch + SSM, AgentCore: Bedrock full + S3 + CloudWatch + SSM)
   - ECS Service entities (desired count, auto-scaling config, load balancer integration for BFF, Service Discovery for AgentCore)
   - Security Group entities (BFF, AgentCore: ingress/egress rules)
   - Service Discovery Namespace entity (private DNS namespace for AgentCore)
   - CloudWatch Log Group entities (service-specific log groups, 7-day retention)
   - Auto-Scaling Policy entities (CPU threshold, memory threshold, cooldown period)

2. **Contracts** (`contracts/`):
   - `ecs-cluster-contract.yaml`: Cluster ARN, cluster name outputs
   - `ecs-services-contract.yaml`: Service ARNs for BFF, AgentCore
   - `task-definitions-contract.yaml`: Task definition ARNs and revisions
   - `security-groups-contract.yaml`: Security group IDs for BFF and AgentCore
   - `service-discovery-contract.yaml`: Service Discovery namespace ID and DNS name
   - `cloudwatch-logs-contract.yaml`: Log group names and ARNs

3. **Quickstart** (`quickstart.md`):
   - Prerequisites: NetworkStack, DatabaseStack, StorageStack, SecurityStack deployed
   - Build ECR images: `docker build`, `docker push` to ECR repositories
   - Deploy ComputeStack: `cdk deploy ComputeStack --profile bidopsai`
   - Validate deployment: `aws ecs list-services`, `aws ecs describe-services`
   - Test endpoints: `curl https://<alb-dns>/api/health`
   - Rollback procedure: `cdk deploy ComputeStack --previous` or CloudFormation console rollback

**Re-check Constitution**: Verify design maintains least-privilege IAM, multi-AZ resilience, observability requirements.

## Phase 2: Tasks Breakdown

**Objective**: Generate detailed implementation tasks via `/speckit.tasks` command.

**Task Categories** (to be expanded in `tasks.md`):
1. **Configuration Enhancement**: Update `config.py` with ECS resource allocations per environment
2. **Task Execution Role Creation**: IAM role for ECR pull, CloudWatch logs, SSM Parameter Store access
3. **Task Role Creation**: Service-specific IAM roles (BFF minimal, AgentCore with Bedrock/S3)
4. **Security Group Creation**: Security groups for BFF and AgentCore with ingress/egress rules
5. **Task Definition Creation**: Fargate task definitions for BFF and AgentCore
6. **Service Discovery**: ECS Service Discovery namespace for AgentCore private DNS
7. **Target Group Creation**: BFF target group created in ComputeStack, attached to public ALB from NetworkStack
8. **ECS Service Creation**: Services with load balancer integration (BFF only), health checks, auto-scaling
9. **CloudWatch Resources**: Log groups, alarms for task count and target health
10. **Stack Integration**: Update `app.py` to pass stack dependencies to ComputeStack
11. **Unit Testing**: Comprehensive tests for all ECS resources
12. **Contract Testing**: Validate CloudFormation outputs match contracts
13. **Deployment Validation**: Deploy to test environment, verify service health, load balancer integration, service discovery
14. **Documentation**: Deployment report, troubleshooting guide

**Deliverable**: `tasks.md` with granular tasks, acceptance criteria, dependencies, and time estimates.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| ECR repositories empty (no container images) | HIGH: Tasks fail to launch | Create placeholder Dockerfiles with health check endpoints, push to ECR before deployment |
| Task execution role lacks SSM Parameter Store access | HIGH: Tasks cannot retrieve credentials | Explicitly test IAM role policies with `aws iam simulate-principal-policy` before deployment |
| Security group rules block load balancer → BFF traffic | HIGH: Health checks fail, tasks never healthy | Validate security group rules in unit tests, verify ingress from ALB security group |
| Security group rules block BFF → AgentCore traffic | HIGH: BFF cannot communicate with AgentCore | Validate egress from BFF SG to AgentCore SG on port 8080 |
| Service Discovery DNS resolution fails | HIGH: BFF cannot discover AgentCore tasks | Test DNS resolution from BFF container, verify Service Discovery namespace configuration |
| Fargate capacity unavailable in us-east-1 | MEDIUM: Task placement fails | Use Fargate Spot as fallback capacity provider (already 30% weight) |
| Task CPU/memory allocation insufficient | MEDIUM: Tasks crash with OOM or timeout | Start with conservative allocations (prod: 2 vCPU/4GB), monitor CloudWatch metrics, adjust iteratively |
| Auto-scaling policies too aggressive | LOW: Cost spike from rapid scaling | Use 5-minute cooldown, require 3 consecutive metric breaches before scaling |
| Load balancer health checks too strict | LOW: Healthy tasks marked unhealthy | Use 30-second interval, 3 failures before unhealthy, 2 successes before healthy |

## Success Metrics

Deployment success will be validated against specification success criteria:

- **SC-001**: Deploy containerized workloads to ECS within 10 minutes (validated via `aws ecs describe-services` showing RUNNING state)
- **SC-002**: Automatic task recovery within 60 seconds (validated by manually stopping tasks and observing ECS replacement)
- **SC-003**: 99.9% availability during rolling deployments (validated by updating task definition and monitoring load balancer target health)
- **SC-004**: Auto-scaling response within 5 minutes (validated by load testing to trigger CPU threshold)
- **SC-005**: Unhealthy task detection within 90 seconds (validated by deploying task with broken health check endpoint)
- **SC-006**: Task IAM role authentication without credentials (validated by executing Bedrock API call from AgentCore container)
- **SC-007**: Container logs in CloudWatch within 30 seconds (validated by emitting test log and querying CloudWatch Logs Insights)
- **SC-010**: Security group compliance scan (validated via contract test asserting no 0.0.0.0/0 ingress rules)
- **SC-011**: Service Discovery DNS resolution (validated by querying AgentCore DNS from BFF container via `nslookup` or HTTP request)

## Next Steps

1. Run `/speckit.plan` phase 0: Generate `research.md` with CDK ECS patterns and stack integration analysis
2. Run `/speckit.plan` phase 1: Generate `data-model.md`, `contracts/`, and `quickstart.md`
3. Run `/speckit.tasks`: Generate granular implementation tasks
4. Begin implementation: Start with configuration and IAM roles (lowest risk), progress to task definitions and services

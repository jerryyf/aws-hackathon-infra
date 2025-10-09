
# Implementation Plan: AWS CDK Infrastructure for Bedrock Agent Platform

**Branch**: `002-create-python-application` | **Date**: 2025-10-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-create-python-application/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Provision complete AWS infrastructure foundation using CDK for Bedrock agent platform with multi-AZ deployment (us-east-1a/1b), VPC isolation, managed services integration (RDS, OpenSearch, S3, ECR), and comprehensive security controls. Infrastructure supports three-tier architecture (public ALB → BFF/Backend in private subnets → AgentCore → data layer) with VPC endpoints for AWS service access, WAF/Shield protection, encryption at rest/transit, and CloudWatch/CloudTrail observability.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: aws-cdk-lib (2.x), constructs, boto3, pytest  
**Storage**: Aurora PostgreSQL cluster (multi-AZ), OpenSearch Service (3-node), S3 (KMS encrypted), ECR (image scanning)  
**Testing**: pytest with CDK assertions, contract tests for stack outputs  
**Target Platform**: AWS us-east-1 (multi-AZ deployment across us-east-1a, us-east-1b)  
**Project Type**: single (IaC repository with modular CDK stacks)  
**Performance Goals**: <10min full stack deployment, <5min failover (RPO 15min/RTO 30min), ALB <100ms p95 latency  
**Constraints**: Multi-AZ required, encryption at rest/transit mandatory, VPC isolation for all compute, no public internet access for private resources, least privilege IAM  
**Scale/Scope**: 8 CDK stacks (network, compute, database, storage, security, monitoring), ~20 AWS resource types, support for dev/staging/prod environments

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. AWS Well-Architected Framework ✅ PASS
- **Operational Excellence**: CDK IaC enables automated deployments, CloudWatch/CloudTrail provide operational visibility
- **Security**: VPC isolation, encryption at rest/transit, Secrets Manager, WAF/Shield, least privilege IAM - all aligned
- **Reliability**: Multi-AZ deployment, RDS failover (RPO 15min/RTO 30min), NAT gateway redundancy
- **Performance Efficiency**: Managed services (RDS, OpenSearch, Bedrock), ALB for traffic distribution, VPC endpoints reduce latency
- **Cost Optimization**: Tagging strategy defined, right-sized resources (2-node OpenSearch dev, 3-node prod), reserved capacity evaluation deferred to production
- **Sustainability**: Serverless where possible (Lambda potential), managed services reduce over-provisioning

### II. Infrastructure as Code Excellence ✅ PASS
- All infrastructure defined in CDK (Python)
- Version controlled, modular stack design (network, compute, database, storage, security, monitoring)
- No hardcoded secrets (Secrets Manager/Parameter Store via VPC endpoints)
- Environment parameterization (region, CIDR, instance sizes) per spec clarifications

### III. Security & Compliance First ✅ PASS
- Least privilege IAM (stack-specific roles, service-linked roles)
- Defense in depth (WAF, Security Groups, NACLs, private subnets, VPC endpoints)
- Encryption: KMS for S3, RDS encryption at rest, TLS 1.2+ for ALB
- Audit trail: CloudTrail 7-year retention, VPC Flow Logs enabled
- Secrets management: Secrets Manager for DB credentials, no hardcoded values
- Vulnerability scanning: ECR image scanning enabled
- Network isolation: Private subnets for compute, VPC endpoints for AWS services

### IV. Code Quality & Maintainability ✅ PASS
- Python type hints required (PEP 484)
- Linting enforced (ruff/pylint in CI/CD per AGENTS.md)
- Contract tests for stack outputs (VPC ID, subnet IDs, security group IDs)
- Code review required before merge (Git flow per constitution)
- Consistent CDK patterns (L2 constructs preferred, L1 only when necessary)

### V. Extensibility & Modularity ✅ PASS
- Microservices support via modular stacks (network → compute → database)
- API-first: ALB endpoints defined before service implementation
- Event-driven ready: EventBridge/SNS/SQS integration patterns available
- Stack outputs enable cross-stack references (no tight coupling)
- Environment parameterization supports dev/staging/prod without code changes

### VI. Observability & Operational Excellence ✅ PASS
- Structured logging: CloudWatch Logs with VPC endpoint
- Distributed tracing: X-Ray integration planned (FR-042)
- Metrics & alarms: CloudWatch metrics for ALB, RDS, OpenSearch (FR-039 to FR-041)
- Health checks: ALB health check endpoints required for target groups
- Runbooks: Quickstart.md will document deployment and validation procedures
- Chaos testing: Deferred to post-PoC (AZ failure scenarios documented in spec edge cases)

**GATE STATUS**: ✅ PASS - No violations, ready for Phase 0 research

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
cdk/
├── stacks/
│   ├── network_stack.py       # VPC, subnets, NAT, IGW, VPC endpoints
│   ├── security_stack.py      # Security groups, NACLs, WAF, Shield, Cognito User Pool
│   ├── compute_stack.py       # ALB (public/internal), ECS/Fargate placeholder, ALB Cognito auth
│   ├── database_stack.py      # Aurora PostgreSQL cluster, RDS Proxy, OpenSearch
│   ├── storage_stack.py       # S3 buckets, ECR repositories
│   └── monitoring_stack.py    # CloudWatch, CloudTrail, X-Ray
├── app.py                     # CDK app entry point
├── cdk.json                   # CDK configuration
└── requirements.txt           # Python dependencies

tests/
├── contract/                  # Stack output contract tests
│   ├── test_vpc_contract.py
│   ├── test_alb_contract.py
│   └── test_rds_contract.py
├── integration/               # Cross-stack integration tests
└── unit/                      # CDK construct unit tests

specs/002-create-python-application/
├── plan.md                    # This file
├── research.md                # Phase 0 output
├── data-model.md              # Phase 1 output
├── quickstart.md              # Phase 1 output
├── contracts/                 # Phase 1 output
│   ├── network-stack.yaml
│   ├── database-stack.yaml
│   └── storage-stack.yaml
└── tasks.md                   # Phase 2 output (/tasks command)
```

**Structure Decision**: Single project (IaC repository). CDK stacks in `cdk/stacks/` follow modular design with clear separation of concerns (network, security, compute, database, storage, monitoring). Tests organized by type (contract, integration, unit) with contract tests validating stack outputs per constitutional requirements.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh opencode`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base structure
- Generate tasks from Phase 1 design artifacts:
  - Each stack contract (`contracts/*.yaml`) → contract test implementation task [P]
  - Each stack contract → CDK stack implementation task (depends on contract test)
  - Each infrastructure entity (from `data-model.md`) → CDK construct task [P]
  - Integration test scenarios (from `quickstart.md` validation procedures)
  - Documentation tasks (update AGENTS.md, README.md with deployment commands)

**Ordering Strategy** (addressing critical issue from analysis):
1. **Contract tests FIRST** (fix TDD violation from analysis findings)
   - `test_vpc_contract.py` [P]
   - `test_security_groups_contract.py` [P]
   - `test_database_contract.py` [P]
   - `test_storage_contract.py` [P]
   - `test_compute_contract.py` [P]
   - `test_monitoring_contract.py` [P]

2. **CDK stack implementations SECOND** (make contract tests pass)
   - `network_stack.py` (dependency: test_vpc_contract.py)
   - `security_stack.py` [P - parallel with network if outputs mocked]
   - `database_stack.py` (dependency: network_stack.py, security_stack.py)
   - `storage_stack.py` [P - minimal network dependencies]
   - `compute_stack.py` (dependency: network_stack.py, security_stack.py, storage_stack.py)
   - `monitoring_stack.py` (dependency: all other stacks for log group creation)

3. **Integration tests THIRD** (validate cross-stack functionality)
   - VPC endpoint connectivity test (Bedrock, Secrets Manager, S3)
   - RDS Proxy connection test (from ECS security group)
   - Multi-AZ resilience test (simulate AZ failure per quickstart.md DR scenario)

4. **Documentation & CI/CD FOURTH**
   - Update README.md with `cdk deploy` commands
   - Create GitHub Actions workflow for CDK synth/deploy validation (address missing CI/CD from analysis)
   - Update AGENTS.md with finalized stack structure

**Parallelization Opportunities**:
- All 6 contract tests can run in parallel [P]
- Storage stack and security stack implementation (minimal dependencies)
- Contract test execution during CI (independent validation)

**Estimated Output**: 40-50 tasks
- 6 contract test tasks
- 6 CDK stack implementation tasks
- 12-15 supporting construct tasks (VPC endpoints, security groups, RDS Proxy)
- 6 integration test tasks
- 4-6 documentation/CI tasks
- 6-12 validation/troubleshooting tasks

**Dependencies Management**:
- Use task dependency notation: `(depends: task-###)`
- Mark truly parallel tasks with `[P]` to optimize execution
- Group related tasks (e.g., all network-related, all database-related)

**TDD Compliance** (critical fix):
- All contract tests written BEFORE stack implementations
- Integration tests written BEFORE feature implementations
- No implementation task starts until corresponding test exists

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS (re-evaluated after Phase 1)
- [x] All NEEDS CLARIFICATION resolved (12 items clarified on 2025-10-07)
- [x] Complexity deviations documented (none - all principles satisfied)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*

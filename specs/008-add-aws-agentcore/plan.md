# Implementation Plan: AWS AgentCore Runtime Infrastructure

**Branch**: `008-add-aws-agentcore` | **Date**: 2025-10-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-add-aws-agentcore/spec.md`

## Summary

Add AWS Bedrock AgentCore runtime infrastructure to enable containerized AI agent deployments. Implementation creates a new CDK stack (`AgentCoreStack`) using L1 constructs (`CfnRuntime`) to deploy agent containers from ECR within existing VPC infrastructure, with proper IAM roles, network configuration, and multi-AZ support.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: AWS CDK v2, aws_cdk.aws_bedrockagentcore (L1 constructs), boto3  
**Storage**: ECR for agent container images (existing StorageStack), no new databases  
**Testing**: pytest, contract tests for runtime outputs, integration tests for deployment  
**Target Platform**: AWS us-east-1 (existing infrastructure region)  
**Project Type**: Infrastructure-as-Code (AWS CDK Python)  
**Performance Goals**: Runtime deployment <10 min, invocation response <2s, multi-AZ failover <30s  
**Constraints**: TLS 1.2+ encryption, VPC private subnets only, no public endpoints for VPC mode  
**Scale/Scope**: Support 1-10 agent runtimes initially, designed for horizontal scaling

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**AWS Well-Architected Framework Compliance (from AGENTS.md constitution)**:

| Pillar | Requirement | Status |
|--------|-------------|--------|
| **Operational Excellence** | Multi-AZ deployment, CloudWatch monitoring | ✅ Multi-AZ via subnet selection, monitoring stack integration |
| **Security** | Encryption at rest/transit (TLS 1.2+), least-privilege IAM, VPC isolation | ✅ KMS for ECR (existing), TLS enforced, IAM execution role with trust policy, VPC mode |
| **Reliability** | Multi-AZ failover, health checks | ✅ Runtime status monitoring, subnet redundancy |
| **Performance** | <2s response time for health checks | ✅ Covered by SC-003 |
| **Cost** | Resource tagging (Project/Environment/Owner/CostCenter) | ✅ FR-009 mandates tagging |
| **Sustainability** | Right-sizing container resources | ⚠️ NEEDS CLARIFICATION: Container CPU/memory limits not in spec |

**Violations Requiring Justification**: None. Sustainability sizing can be addressed in Phase 1 quickstart.

## Project Structure

### Documentation (this feature)

```
specs/008-add-aws-agentcore/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (existing research summary)
├── data-model.md        # Phase 1 output (runtime entity model)
├── quickstart.md        # Phase 1 output (deployment guide)
├── contracts/           # Phase 1 output (runtime outputs, IAM policies)
│   ├── agentcore-stack.yaml        # CfnRuntime outputs (RuntimeArn, RuntimeId, etc.)
│   ├── execution-role-trust.json   # IAM trust policy for bedrock-agentcore service
│   └── execution-role-permissions.json  # IAM permissions for Bedrock, ECR, CloudWatch
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
cdk/
├── stacks/
│   ├── __init__.py                  # Add agentcore_stack export
│   ├── network_stack.py             # MODIFY: Add VPC endpoint for bedrock-agentcore (FR-008)
│   ├── security_stack.py            # MODIFY: Add execution role + policies (FR-003, FR-005)
│   ├── storage_stack.py             # MODIFY: Add ECR repository for agent images (FR-001)
│   └── agentcore_stack.py           # NEW: CfnRuntime, network config, outputs (FR-002, FR-004, FR-006)
├── app.py                           # MODIFY: Wire up AgentCoreStack dependencies
└── config.py                        # MODIFY: Add agentcore stack name + runtime config

tests/
├── contract/
│   ├── test_agentcore_runtime_contract.py      # NEW: Verify runtime ARN/ID outputs
│   ├── test_agentcore_execution_role_contract.py  # NEW: Verify IAM role trust/permissions
│   └── test_vpc_endpoint_contract.py           # NEW: Verify bedrock-agentcore endpoint
├── integration/
│   ├── test_agentcore_deployment.py            # NEW: E2E deployment to ACTIVE status
│   └── test_agentcore_vpc_access.py            # NEW: Verify VPC-mode runtime access
└── unit/
    └── test_agentcore_stack_synth.py           # NEW: CDK synth validation
```

**Structure Decision**: Single CDK project (existing pattern). New `agentcore_stack.py` follows existing stack organization (network, database, storage, etc.). Modifications to existing stacks follow dependency pattern: Network → Security → Storage → AgentCore. Tests organized by contract/integration/unit (existing pattern).

## Complexity Tracking

*Constitution compliance check shows no violations. No justification required.*

---

## Implementation Phases

### Phase 0: Research ✅ COMPLETE

**Completed Artifacts**:
- Research summary confirming L1 `CfnRuntime` construct availability
- VPC integration pattern identified (network_configuration.network_mode)
- IAM role requirements documented (bedrock-agentcore.amazonaws.com trust policy)
- ECR integration pattern confirmed (container_uri property)

**Key Findings**:
- `aws_cdk.aws_bedrockagentcore.CfnRuntime` is the primary construct (no L2 available)
- VPC endpoint service name: `com.amazonaws.<region>.bedrock-agentcore`
- Required outputs: AgentRuntimeArn, AgentRuntimeId, AgentRuntimeVersion, Status
- Network mode: PUBLIC or VPC (VPC requires subnet/security group configuration)

### Phase 1: Design (NEXT PHASE)

**Objective**: Define data model, contracts, and quickstart deployment guide.

**Deliverables**:
1. **data-model.md**: Entity definitions for AgentRuntime, ExecutionRole, NetworkConfiguration, VPCEndpoint
2. **contracts/agentcore-stack.yaml**: CloudFormation outputs contract
   ```yaml
   outputs:
     AgentRuntimeArn:
       description: ARN of the deployed agent runtime
       exportName: ${Environment}-AgentRuntimeArn
     AgentRuntimeId:
       description: Unique ID for the agent runtime
     AgentRuntimeEndpointUrl:
       description: HTTPS endpoint for invoking the runtime
     ExecutionRoleArn:
       description: ARN of the IAM execution role
   ```
3. **contracts/execution-role-trust.json**: IAM trust policy allowing bedrock-agentcore.amazonaws.com
4. **contracts/execution-role-permissions.json**: IAM permissions for bedrock:InvokeModel, ecr:GetAuthorizationToken, logs:CreateLogGroup
5. **quickstart.md**: Step-by-step deployment guide (build container → push to ECR → deploy stack → verify runtime status)

**Design Questions to Resolve**:
- Container resource limits (CPU/memory) - needed for Sustainability pillar
- Security group ingress/egress rules for VPC mode
- CloudWatch log group naming convention
- VPC endpoint DNS configuration (PrivateDnsEnabled: true/false?)
- Agent runtime naming convention (include environment/region?)

### Phase 2: Tasks

**Objective**: Generate actionable task list using `/speckit.tasks` command.

**Inputs**: spec.md, plan.md (this file), data-model.md, contracts/, quickstart.md

**Expected Output**: tasks.md with sequenced tasks for:
1. Modify config.py (add agentcore stack name + runtime config)
2. Modify storage_stack.py (add ECR repository)
3. Modify security_stack.py (add execution role)
4. Modify network_stack.py (add VPC endpoint)
5. Create agentcore_stack.py (CfnRuntime resource)
6. Modify app.py (wire dependencies)
7. Write contract tests (runtime outputs, IAM role, VPC endpoint)
8. Write integration tests (deployment, VPC access)
9. Write unit tests (CDK synth validation)
10. Update README with AgentCore deployment instructions

### Phase 3: Implementation

**Prerequisites**:
- All Phase 1 deliverables completed and approved
- tasks.md generated via `/speckit.tasks`
- Feature branch `008-add-aws-agentcore` created

**Implementation Order** (follows CDK dependency graph):
1. **Config + Storage** (no dependencies): Update config.py, add ECR repo to storage_stack.py
2. **Security** (depends on nothing): Add execution role to security_stack.py
3. **Network** (depends on nothing): Add VPC endpoint to network_stack.py
4. **AgentCore** (depends on Network, Security, Storage): Create agentcore_stack.py
5. **App wiring** (depends on all stacks): Update app.py
6. **Tests** (depends on implementation): Contract → Unit → Integration

**Success Criteria for Phase Completion**:
- All tests pass: `PYTHONPATH=. pytest`
- CDK synth succeeds: `cd cdk && cdk synth`
- Black formatting passes: `cd cdk && black .`
- pylint passes: `cd cdk && pylint cdk/`
- Contract tests verify all outputs defined in contracts/agentcore-stack.yaml
- Integration test deploys runtime to ACTIVE status
- Deployment report generated in docs/deployments/deployment_reports/

### Phase 4: Testing & Validation

**Test Execution Plan**:
1. **Unit tests** (fast feedback): `pytest tests/unit/test_agentcore_stack_synth.py`
2. **Contract tests** (validate outputs): `pytest tests/contract/test_agentcore_*`
3. **Integration tests** (E2E deployment): `pytest tests/integration/test_agentcore_*`
   - Requires: Sample agent container image in ECR (use bedrock-agentcore-starter-toolkit or minimal test image)
   - Duration: ~10 minutes (runtime deployment time)
   - Cleanup: Automatic via CDK destroy in test teardown

**Acceptance Validation** (maps to spec.md scenarios):
- User Story 1, Scenario 1: Integration test verifies runtime.status == "ACTIVE"
- User Story 1, Scenario 2: Contract test verifies RuntimeArn/EndpointUrl outputs exist
- User Story 2, Scenario 1: Integration test attempts public access (should fail in VPC mode)
- User Story 3, Scenario 1: Integration test invokes Bedrock model via runtime
- User Story 4, Scenario 1: Network traffic analysis confirms VPC endpoint usage

### Phase 5: Documentation & Handoff

**Deliverables**:
1. Update README.md with AgentCore deployment section (reference quickstart.md)
2. Generate deployment report in docs/deployments/deployment_reports/
3. Update AGENTS.md with AgentCore-specific build/test commands
4. Create example agent container Dockerfile (optional, for testing)
5. Document runtime invocation examples (synchronous + streaming)

**Handoff Checklist**:
- [ ] All tests passing in CI/CD (GitHub Actions)
- [ ] Code reviewed and approved
- [ ] Constitution compliance verified (tagging, encryption, multi-AZ)
- [ ] Deployment tested in test environment
- [ ] Documentation complete (README, quickstart, contracts)
- [ ] Feature branch merged to main

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AgentCore service not available in us-east-1 | Low | High | Verify service availability before Phase 3; spec assumes availability |
| VPC endpoint for bedrock-agentcore doesn't exist | Medium | Medium | Phase 1 research will test endpoint creation; fallback to PUBLIC mode |
| Container image exceeds AgentCore limits | Low | Medium | Document size/timeout limits in quickstart.md; validate in integration test |
| IAM permissions insufficient for runtime | Medium | Low | Contract tests validate trust policy; integration tests catch permission issues early |
| Multi-AZ subnet configuration errors | Low | Medium | Leverage existing network_stack subnet selection pattern; unit tests validate config |

## Open Questions for Phase 1

1. **Container resource limits**: What CPU/memory should be allocated to agent runtimes? (Sustainability pillar requirement)
2. **VPC endpoint policy**: Should we restrict access to specific IAM principals or allow full VPC access?
3. **Agent container source**: Use bedrock-agentcore-starter-toolkit for testing, or create minimal test image?
4. **Runtime naming**: Include environment/region in runtime name? (e.g., `hackathon-agent-test-us-east-1`)
5. **Monitoring integration**: Should agent runtime metrics flow to existing CloudWatch dashboard or separate dashboard?
6. **Security group rules**: What ingress/egress ports are required for VPC-mode runtimes?
7. **Session management**: How will session IDs (33+ chars) be generated for testing?

---

**Next Command**: `/speckit.plan` (to trigger Phase 1 data-model.md and contracts generation)

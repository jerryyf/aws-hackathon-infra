# Implementation Plan: AWS AgentCore Runtime Infrastructure

**Branch**: `008-add-aws-agentcore` | **Date**: 2025-10-13 | **Spec**: [spec.md](./spec.md)
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

## Phase Status

### ✅ Phase 0: Research - COMPLETED (2025-10-13)
- Researched container resource sizing (dev vs prod)
- Investigated VPC endpoint configuration for bedrock-agentcore service
- Analyzed IAM trust policy requirements with source account/ARN restrictions
- Generated comprehensive research.md with decisions and recommendations

### ✅ Phase 1: Design - COMPLETED (2025-10-13)
- Updated data-model.md with minor date corrections
- Verified contracts/ directory with 4 API contracts:
  - agentcore-stack.yaml (CloudFormation outputs contract)
  - execution-role-trust.json (IAM trust policy)
  - execution-role-permissions.json (IAM permissions policy) 
  - vpc-endpoint-policy.json (VPC endpoint access policy)
- Verified quickstart.md deployment guide (15-minute deployment walkthrough)
- Updated agent context via .specify/scripts/bash/update-agent-context.sh

**Phase 1 Deliverables Generated**:
- `/specs/008-add-aws-agentcore/data-model.md` ✅
- `/specs/008-add-aws-agentcore/contracts/` ✅ (4 files)
- `/specs/008-add-aws-agentcore/quickstart.md` ✅ 
- Updated AGENTS.md context ✅

**Ready for**: `/tasks` command to generate implementation task breakdown

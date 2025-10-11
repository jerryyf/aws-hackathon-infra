# Agent Development Guidelines

## Project Context
Infrastructure-as-Code for AWS Hackathon AgentCore using AWS CDK (Python). Architecture in `docs/arch.mermaid`, ER diagrams in `docs/er.mermaid`. Constitution in `.specify/memory/constitution.md` defines AWS Well-Architected Framework compliance requirements. **Development platform: macOS**.

## Build/Test/Lint Commands
- **Test all**: `PYTHONPATH=. pytest` (from repo root)
- **Single test**: `PYTHONPATH=. pytest tests/unit/test_vpc_construct.py::test_vpc_construct`
- **Contract tests**: `PYTHONPATH=. pytest tests/contract/` (validates CloudFormation outputs)
- **CDK synth**: `cd cdk && cdk synth` (validates CloudFormation templates)
- **CDK synth single stack**: `cd cdk && cdk synth hackathon-agentcore-stack`
- **Format**: `cd cdk && black .` (88 char line length)
- **Lint**: `cd cdk && pylint cdk/` (docstrings disabled, see pyproject.toml)

## Code Style (Python 3.11+, AWS CDK v2)
- **Imports**: Group stdlib → third-party → aws_cdk → constructs → local (alphabetical within groups). Use `from aws_cdk import (..., aws_x as x)` style.
- **Types**: Type hints required on all functions/methods (e.g., `def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None`)
- **Naming**: `snake_case` (functions/vars), `PascalCase` (classes), `UPPER_SNAKE` (constants)
- **Formatting**: Black (88 chars), no manual docstrings (pylint disabled C0114/C0115/C0116)
- **Error Handling**: Use AWS CDK exceptions, no bare try/except, always validate stack dependencies
- **Security**: NEVER hardcode secrets—use Secrets Manager/SSM. All S3 buckets KMS-encrypted, VPC endpoints for AWS services.
- **Architecture**: Multi-AZ (2 AZs min), VPC 10.0.0.0/16, 4 subnet tiers (Public/24, PrivateApp/24, PrivateAgent/24, PrivateData/24)

## AWS Services
- **AWS Bedrock AgentCore**: Deploy containerized AI agents via `aws_cdk.aws_bedrockagentcore.CfnRuntime` (L1 construct). Requires ECR container URI, IAM execution role with `bedrock-agentcore.amazonaws.com` trust policy. Supports VPC mode (PrivateAgent subnets) or PUBLIC mode. Runtime status must reach ACTIVE before invocation.

## .specify Workflow
- Feature branches: `00X-feature-name` (3-digit prefix). Check prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json`
- Slash commands: `/constitution`, `/spec`, `/plan`, `/tasks`, `/implement`, `/analyze`, `/clarify`

## Constitution Compliance (NON-NEGOTIABLE)
- All code MUST pass AWS Well-Architected Framework checks (6 pillars: Operational Excellence, Security, Reliability, Performance, Cost, Sustainability)
- Tagging: All resources tagged with Project/Environment/Owner/CostCenter. Encryption at rest/transit (TLS 1.2+). Multi-AZ failover tested.

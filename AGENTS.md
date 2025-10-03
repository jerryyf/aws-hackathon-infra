# Agent Development Guidelines

## Project Context
Infrastructure-as-Code repository for AWS Hackathon AgentCore using AWS CDK (Python). Architecture documented in `docs/arch.md`, data model in `docs/er.md`.

## Build/Test Commands
- No build/test commands yet - infrastructure code not implemented
- When implemented: `pytest` for Python tests, `cdk synth` to validate stacks, `cdk deploy` to provision
- Run single test: `pytest path/to/test_file.py::test_function_name`

## Specification Workflow (.specify framework)
- Check prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json`
- Custom slash commands available: `/constitution`, `/spec`, `/plan`, `/tasks`, `/implement`, `/analyze`, `/clarify`
- Feature branches: `001-feature-name` format (3-digit prefix)

## Code Style (When CDK Code is Added)
- **Language**: Python 3.x with AWS CDK v2
- **Imports**: Group stdlib, third-party, aws-cdk, local (alphabetical within groups)
- **Types**: Use type hints for all functions and class methods
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE for constants
- **Architecture**: Multi-AZ deployment (us-east-1a, us-east-1b), VPC 10.0.0.0/16, private subnets for services
- **Security**: No secrets in code - use AWS Secrets Manager/SSM Parameter Store, reference via VPC endpoints

## Documentation
- Architecture diagrams in Mermaid format (see `docs/arch.md`)
- ER diagrams for data model (see `docs/er.md`)
- Constitution/principles in `.specify/memory/constitution.md` (currently template)

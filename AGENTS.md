# Agent Guidelines

## Git

DO NOT run any `git` or `gh` commands unless specifically granted permission to by the user.

## Workflow

This project uses spec-kit. Always follow workflows outlined in specs, plans, tasks.

### Subagents

Use the `@general` subagent wherever possible. A general-purpose agent for researching complex questions, searching for code, and executing multi-step tasks. Use when searching for keywords or files and you’re not confident you’ll find the right match in the first few tries.

## Research

Always use context7 to fetch up-to-date documentation. Always use `webfetch` with URLs provided by either the user, or by context7.

## Virtual Environment

Check for existence of venv/ or .venv/ in the project. If not exist, create with `python3 -m venv ./.venv`. Always ensure the virtual environment is activated before anything:

```bash
source .venv/bin/activate
```

## Environment Variables

Set AWS profile before running CDK commands:
```bash
export AWS_PROFILE=hackathon
export AWS_REGION=us-east-1
```

## Commands

- **Synth**: `cd cdk && cdk synth --profile hackathon`
- **Run all tests**: `PYTHONPATH=. pytest`
- **Run single test**: `PYTHONPATH=. pytest tests/unit/test_vpc_construct.py::test_vpc_construct`
- **Deploy stack**: `cd cdk && cdk deploy NetworkStack --profile hackathon`
- **Type check**: `cd cdk && pyright`
- **Lint**: `cd cdk && black . && pylint stacks/`

## Code Style

- **Python 3.11+** with type hints (`str | None` not `Optional[str]`)
- **Imports**: AWS CDK from `aws_cdk`, group by stdlib → third-party → local, use `as` aliases (`aws_ec2 as ec2`)
- **Formatting**: Black (line-length 88), no module/class docstrings per pylint config
- **Types**: Always use type hints on function signatures (`:` for params, `->` for returns)
- **Naming**: snake_case for variables/functions, PascalCase for classes, ALL_CAPS for constants
- **Error handling**: Let exceptions propagate unless specific handling needed
- **CDK patterns**: Use L2 constructs, `CfnOutput` for exports, `Construct` scope pattern
- **Testing**: pytest with `Template.from_stack()` assertions, contract tests validate CloudFormation outputs
- **Environment**: Check `self.account`/`self.region` before context lookups (hosted zones, VPCs)

## Project Structure

All documentation can be found in docs/. Place any ad-hoc reports, troubleshooting summaries, deployments, here.
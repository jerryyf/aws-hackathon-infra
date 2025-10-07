# OpenCode Configuration

This directory contains OpenCode AI assistant configuration for the AWS Hackathon Infrastructure project.

## Configuration Files

### `config.json`
Main OpenCode configuration file following the [OpenCode schema](https://opencode.ai/config.json).

**Key settings:**
- **Model**: Claude Sonnet 4 (primary), Claude Haiku 3.5 (small tasks)
- **Instructions**: Loads project constitution, deployment analysis, and agent guidelines
- **Modes**: `build`, `fix`, `analyze`, `docs` - specialized prompts for different tasks
- **Commands**: Custom commands for common CDK operations (`/synth`, `/test-contract`, `/fix-blockers`)
- **Formatters**: Black and Ruff for Python code formatting

### `config.yaml`
Project-specific context and metadata (not part of OpenCode standard format).

Contains:
- Stack structure and file locations
- Critical blocker details from deployment analysis
- Architecture summary (VPC, databases, storage)
- Constitution principles and violations
- Next priority actions

## Usage

### Running OpenCode
```bash
# Start interactive session
opencode

# Run specific command
opencode run "/synth"
opencode run "/test-contract"
opencode run "/fix-blockers"

# Use specialized mode
opencode --mode fix
opencode --mode analyze
```

### Custom Commands

- `/synth` - Validate CDK stacks with synthesis
- `/test-contract` - Run infrastructure contract tests
- `/fix-blockers` - Fix all CRITICAL deployment blockers
- `/validate` - Full deployment readiness validation

### Modes

- `build` - Full tool access for implementation work
- `fix` - Focused on resolving CRITICAL blockers (optimized prompt)
- `analyze` - Read-only investigation mode (no file changes)
- `docs` - Documentation generation (no bash access)

## Project Context

**Status**: 🔴 NOT READY FOR DEPLOYMENT (25% readiness)

**Must fix before deployment:**
- 11 CRITICAL blockers (C1-C11)
- 1 HIGH-severity issue (H2)
- 2 failing contract tests

**Key files loaded as instructions:**
1. `AGENTS.md` - Agent development guidelines
2. `.specify/memory/constitution.md` - Project constitution (AWS Well-Architected Framework)
3. `docs/deployment-readiness-analysis.md` - Comprehensive blocker analysis

## Environment Variables

Set these for AWS operations:
```bash
export AWS_PROFILE=your-profile
export AWS_REGION=us-east-1
```

## Integration with .specify Framework

This project uses the `.specify` framework for specification-driven development:
- `/constitution` - Review project constitution
- `/spec` - Create/update specifications
- `/plan` - Generate implementation plans
- `/tasks` - Break down work into tasks
- `/implement` - Begin implementation
- `/analyze` - Run deployment readiness analysis

## Tips

1. **Check blockers first**: Review `docs/deployment-readiness-analysis.md` before starting work
2. **Run contract tests**: Always validate changes with `pytest tests/contract/ -v`
3. **Follow constitution**: All changes must align with `.specify/memory/constitution.md`
4. **Test synthesis**: Run `cd cdk && npx aws-cdk synth --all` to validate stacks
5. **Use modes**: Switch to appropriate mode for your task (`--mode fix` for blockers)

## References

- [OpenCode Documentation](https://opencode.ai)
- [OpenCode Configuration Schema](https://opencode.ai/config.json)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- Project Constitution: `.specify/memory/constitution.md`
- Architecture Docs: `docs/arch.md`, `docs/er.md`

# aws-hackathon-infra

> Warning: contains AI-generated content.

Repository for AWS Hackathon AgentCore infrastructure. See docs/SETUP.md for detailed setup instructions.

## Spec-driven Development Toolkit

- opencode, copilot
- spec-kit

### Running Tests

The test suite includes unit tests, contract tests (validate deployed infrastructure), and integration tests (end-to-end scenarios).

**Prerequisites:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Set AWS profile for contract/integration tests
export AWS_PROFILE=hackathon
export AWS_REGION=us-east-1
```

**Quick Commands:**
```bash
# Run all unit tests (fast, no AWS required)
PYTHONPATH=. pytest tests/unit/

# Run contract tests (requires deployed infrastructure)
PYTHONPATH=. pytest tests/contract/ -v

# Run integration tests (requires deployed infrastructure)
PYTHONPATH=. pytest tests/integration/ -v

# Run all tests
PYTHONPATH=. pytest

# Run specific test
PYTHONPATH=. pytest tests/unit/test_vpc_construct.py::test_vpc_construct

# Run with coverage
PYTHONPATH=. pytest --cov=cdk --cov-report=html
```

**Test Markers:**
```bash
# Run only unit tests
pytest -m unit

# Run only contract tests
pytest -m contract

# Run only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

**Parallel Execution:**
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

**CI/CD Pipeline:**
The GitHub Actions workflow runs tests in stages:
1. **Lint** (black, pyright, pylint) - runs on all PRs
2. **Unit Tests** - runs on all PRs (no AWS credentials)
3. **Deploy** - runs on main branch only
4. **Contract Tests** - validates deployed infrastructure
5. **Integration Tests** - end-to-end validation

### Local workflow

For a fully local deployment:
```bash
# Run unit tests first
PYTHONPATH=. pytest tests/unit

# deploy
export AWS_PROFILE=hackathon
export AWS_REGION=us-east-1
cd cdk && cdk deploy --all

# run contract and integration tests
PYTHONPATH=. pytest tests/contract
PYTHONPATH=. pytest tests/integration
```

## Environment Variables

The following environment variables can be set to customize CDK deployments:

| Variable | Description | Default | Valid Values | Required |
|----------|-------------|---------|--------------|----------|
| `ENVIRONMENT` | Deployment environment (affects AgentCore resource allocation) | `test` | `dev`, `test`, `prod` | No |
| `AWS_REGION` | AWS region for deployments | `us-east-1` | Any valid AWS region | No |
| `CDK_DEFAULT_ACCOUNT` | AWS account ID for CDK deployment | Auto-detected from AWS credentials | Valid AWS account ID | No* |
| `CDK_DEFAULT_REGION` | AWS region for CDK deployment | `us-east-1` | Any valid AWS region | No |
| `DOMAIN_NAME` | Public domain name for ALB (creates ACM certificate + Route53 record) | Auto-discovered from Route53 | Valid domain with existing Route53 hosted zone | No |
| `AWS_PROFILE` | AWS CLI profile to use for deployment | `default` | Any configured AWS profile | No |

**Note:** `CDK_DEFAULT_ACCOUNT` is auto-detected from AWS credentials but must be explicitly set for context lookups (Route53, VPC, etc.) during `cdk synth`.

### Environment-Specific Configuration

The `ENVIRONMENT` variable controls AgentCore runtime resource allocation:

| Environment | CPU | Memory | Network Mode |
|-------------|-----|--------|--------------|
| `dev` | 512 (0.5 vCPU) | 1024 MiB | PUBLIC |
| `test` | 1024 (1 vCPU) | 2048 MiB | VPC |
| `prod` | 2048 (2 vCPU) | 4096 MiB | VPC |

### Setting Environment Variables

**macOS/Linux:**
```bash
export ENVIRONMENT=prod
export AWS_REGION=us-east-1
export DOMAIN_NAME=bidopsai.com
export AWS_PROFILE=hackathon
```

**Windows (PowerShell):**
```powershell
$env:ENVIRONMENT="prod"
$env:AWS_REGION="us-east-1"
$env:DOMAIN_NAME="bidopsai.com"
$env:AWS_PROFILE="hackathon"
```

**Deployment Example:**
```bash
# Deploy to production environment with custom domain
ENVIRONMENT=prod DOMAIN_NAME=bidopsai.com cdk deploy --all --profile hackathon

# Deploy to test environment (default)
cdk deploy NetworkStack --profile hackathon

# Deploy without domain name (skips ACM certificate creation)
DOMAIN_NAME="" cdk deploy NetworkStack --profile hackathon
```
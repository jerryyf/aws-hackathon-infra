# aws-bidopsai-infra

> Warning: contains AI-generated content.

Repository for AWS Hackathon AgentCore infrastructure. See docs/SETUP.md for detailed setup instructions.

## Architecture Overview

This CDK application provisions a complete AWS infrastructure for containerized workloads using ECS Fargate, organized into 6 modular stacks with clear dependency relationships.

### Stack Architecture

```
ComputeStack (ECS Cluster, Services, Task Definitions)
├── NetworkStack (VPC, ALB, Subnets, Security Groups)
├── StorageStack (ECR Repositories, S3 Buckets)
├── SecurityStack (IAM Roles, SSM Parameter Store)
└── DatabaseStack (RDS PostgreSQL, OpenSearch)

MonitoringStack (CloudWatch Dashboards, Alarms)
```

### Stack Dependencies

**ComputeStack** integrates with other stacks via constructor parameters:
- **NetworkStack**: VPC, ALB, subnets (PrivateApp, PrivateAgent), security groups
- **StorageStack**: ECR repositories (bidopsai/app, bidopsai/agent), S3 buckets
- **SecurityStack**: Reserved for future IAM role integration
- **DatabaseStack**: RDS security group for database access rules

**Deployment Order**:
1. NetworkStack → 2. StorageStack → 3. SecurityStack → 4. DatabaseStack → 5. ComputeStack → 6. MonitoringStack

### Key Components

| Stack | Resources | Purpose |
|-------|-----------|---------|
| **NetworkStack** | VPC, ALB, Subnets (Public, PrivateApp, PrivateAgent, PrivateData) | Network isolation and load balancing |
| **StorageStack** | ECR repos (app/agent), S3 buckets (data, logs) | Container image registry and data storage |
| **SecurityStack** | IAM roles, SSM Parameter Store | Identity and secrets management |
| **DatabaseStack** | RDS PostgreSQL, OpenSearch | Persistent data and search |
| **ComputeStack** | ECS cluster, services (BFF, Agent), task definitions | Containerized workload orchestration |
| **MonitoringStack** | CloudWatch dashboards, alarms | Observability and alerting |

For detailed architecture diagrams, see `docs/diagrams/`.

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
export AWS_PROFILE=bidopsai
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

# Deploy stacks in dependency order
export AWS_PROFILE=bidopsai
export AWS_REGION=us-east-1

cd cdk

# Deploy infrastructure stacks first (can run in parallel)
cdk deploy NetworkStack StorageStack SecurityStack DatabaseStack --profile bidopsai

# Deploy compute stack (requires NetworkStack, StorageStack, DatabaseStack)
cdk deploy ComputeStack --profile bidopsai

# Deploy monitoring stack last
cdk deploy MonitoringStack --profile bidopsai

# Run contract and integration tests
cd ..
PYTHONPATH=. pytest tests/contract
PYTHONPATH=. pytest tests/integration
```

**Note**: ComputeStack depends on NetworkStack, StorageStack, and DatabaseStack. Deploy these stacks before deploying ComputeStack.

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
export AWS_PROFILE=bidopsai
```

**Windows (PowerShell):**
```powershell
$env:ENVIRONMENT="prod"
$env:AWS_REGION="us-east-1"
$env:DOMAIN_NAME="bidopsai.com"
$env:AWS_PROFILE="bidopsai"
```

**Deployment Example:**
```bash
# Deploy to production environment with custom domain
ENVIRONMENT=prod DOMAIN_NAME=bidopsai.com cdk deploy --all --profile bidopsai

# Deploy to test environment (default)
cdk deploy NetworkStack --profile bidopsai

# Deploy without domain name (skips ACM certificate creation)
DOMAIN_NAME="" cdk deploy NetworkStack --profile bidopsai
```
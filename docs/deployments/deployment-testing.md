# Deployment Testing Guide

This document describes the deployment testing process for the AWS Hackathon Infrastructure.

## Overview

The infrastructure uses AWS CDK for Infrastructure as Code and includes automated testing for deployment validation.

## Test Categories

### Unit Tests
- **CDK Synth Test**: Validates that all stacks can be synthesized without errors
- Location: `tests/unit/test_cdk_synth.py`

### Contract Tests
- **VPC Deployment Contract**: Validates VPC stack template and outputs
- **Database Deployment Contract**: Validates database stack template and outputs
- Location: `tests/contract/`

### Integration Tests
- **ALB Post-Deployment**: Validates ALB accessibility after deployment
- **Database Post-Deployment**: Validates database connectivity after deployment
- Location: `tests/integration/`

## Deployment Scripts

### Deploy Script
```bash
./scripts/deploy.sh
```
Deploys all CDK stacks in the correct order with monitoring.

### Rollback Script
```bash
./scripts/rollback.sh
```
Destroys all stacks in reverse order.

## Running Tests

### Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.11+ installed
- CDK CLI installed

### Run All Tests
```bash
cd cdk
pip install -r requirements.txt
python -m pytest ../tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests
python -m pytest ../tests/unit/ -v

# Contract tests
python -m pytest ../tests/contract/ -v

# Integration tests (requires deployed infrastructure)
python -m pytest ../tests/integration/ -v
```

## CI/CD Integration

The deployment is integrated with GitHub Actions. See `.github/workflows/deploy.yml` for the CI pipeline that:
- Runs all tests
- Deploys to AWS on main branch pushes
- Monitors deployment status

## Monitoring

Deployment success/failure is logged and can be monitored through:
- Console output
- CloudWatch Logs (future enhancement)
- GitHub Actions logs

## Troubleshooting

### Common Issues
1. **CDK Synth Fails**: Check CDK version and dependencies
2. **Deployment Fails**: Verify AWS permissions and quotas
3. **Post-Deployment Tests Fail**: Ensure infrastructure is deployed and accessible

### Logs
Check deployment logs in the console output or CloudWatch for detailed error information.
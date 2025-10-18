# Configuration for CDK deployments

import os

# Environment settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "test")

# AWS Region
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Stack names
STACK_NAMES = {
    "network": "NetworkStack",
    "database": "DatabaseStack",
    "compute": "ComputeStack",
    "storage": "StorageStack",
    "monitoring": "MonitoringStack",
}

# ECS resource allocations per environment
ECS_RESOURCE_ALLOCATIONS = {
    "dev": {
        "cpu": 512,
        "memory": 1024,
    },
    "test": {
        "cpu": 1024,
        "memory": 2048,
    },
    "prod": {
        "cpu": 2048,
        "memory": 4096,
    },
}

# Test environment settings
if ENVIRONMENT == "test":
    # Use test-specific settings
    pass

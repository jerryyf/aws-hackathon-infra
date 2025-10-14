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
    "agentcore": "AgentCoreStack",
}

# Bedrock AgentCore configuration
AGENTCORE_CONFIG = {
    "dev": {"cpu": "512", "memory": "1024", "network_mode": "PUBLIC"},
    "test": {"cpu": "1024", "memory": "2048", "network_mode": "VPC"},
    "prod": {"cpu": "2048", "memory": "4096", "network_mode": "VPC"},
}

# Test environment settings
if ENVIRONMENT == "test":
    # Use test-specific settings
    pass

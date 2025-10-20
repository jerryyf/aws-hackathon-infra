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

# Domain configuration per environment
# Public domain names are safe to commit (already publicly visible in DNS)
# Can be overridden with DOMAIN_NAME env var or --context domain_name=...
DOMAIN_CONFIG = {
    "dev": "bidopsai.com",
    "test": "bidopsai.com",
    "prod": "bidopsai.com",
}


def get_domain_name(context_domain: str | None = None) -> str | None:
    """
    Get domain name with fallback priority order.

    Priority:
    1. CDK context (--context domain_name=...)
    2. Environment variable (DOMAIN_NAME)
    3. Config file based on ENVIRONMENT

    Args:
        context_domain: Domain from CDK context (app.node.try_get_context("domain_name"))

    Returns:
        Domain name string or None if not configured
    """
    # Priority 1: CDK context (--context domain_name=...)
    if context_domain:
        return context_domain

    # Priority 2: Environment variable
    env_domain = os.getenv("DOMAIN_NAME")
    if env_domain:
        return env_domain

    # Priority 3: Config file based on environment
    return DOMAIN_CONFIG.get(ENVIRONMENT)


# Test environment settings
if ENVIRONMENT == "test":
    # Use test-specific settings
    pass

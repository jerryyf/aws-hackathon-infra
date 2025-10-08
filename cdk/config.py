# Configuration for CDK deployments

import os

# Environment settings
ENVIRONMENT = os.getenv('ENVIRONMENT', 'test')

# AWS Region
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Stack names
STACK_NAMES = {
    'network': 'NetworkStack',
    'database': 'DatabaseStack',
    'compute': 'ComputeStack',
    'storage': 'StorageStack',
    'monitoring': 'MonitoringStack'
}

# Test environment settings
if ENVIRONMENT == 'test':
    # Use test-specific settings
    pass
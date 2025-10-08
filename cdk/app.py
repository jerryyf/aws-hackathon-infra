#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.network_stack import NetworkStack
from stacks.database_stack import DatabaseStack
from stacks.compute_stack import ComputeStack
from stacks.storage_stack import StorageStack
from stacks.security_stack import SecurityStack
from stacks.monitoring_stack import MonitoringStack

app = cdk.App()

# Environment configuration
env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION', 'us-east-1')
)

# Create stacks
network_stack = NetworkStack(app, "NetworkStack", env=env)
database_stack = DatabaseStack(app, "DatabaseStack", env=env, network_stack=network_stack)
compute_stack = ComputeStack(app, "ComputeStack", env=env, network_stack=network_stack)
storage_stack = StorageStack(app, "StorageStack", env=env)
security_stack = SecurityStack(app, "SecurityStack", env=env)
monitoring_stack = MonitoringStack(app, "MonitoringStack", env=env, logs_bucket=storage_stack.logs_bucket)

# Add dependencies between stacks
database_stack.add_dependency(network_stack)
compute_stack.add_dependency(network_stack)
storage_stack.add_dependency(network_stack)
security_stack.add_dependency(network_stack)
monitoring_stack.add_dependency(network_stack)

app.synth()
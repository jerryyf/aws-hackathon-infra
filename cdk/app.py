#!/usr/bin/env python3
import os
import aws_cdk as cdk

try:
    from cdk.stacks.network_stack import NetworkStack
    from cdk.stacks.database_stack import DatabaseStack
    from cdk.stacks.compute_stack import ComputeStack
    from cdk.stacks.storage_stack import StorageStack
    from cdk.stacks.security_stack import SecurityStack
    from cdk.stacks.monitoring_stack import MonitoringStack
    from cdk.config import get_domain_name
except ModuleNotFoundError:
    from stacks.network_stack import NetworkStack
    from stacks.database_stack import DatabaseStack
    from stacks.compute_stack import ComputeStack
    from stacks.storage_stack import StorageStack
    from stacks.security_stack import SecurityStack
    from stacks.monitoring_stack import MonitoringStack
    from config import get_domain_name

app = cdk.App()

# Get environment from context or default to 'dev'
environment = app.node.try_get_context("environment") or "dev"

# Get domain name with priority: context > env var > config
context_domain = app.node.try_get_context("domain_name")
domain_name = get_domain_name(context_domain)

# Environment configuration (only set if account available)
cdk_account = os.getenv("CDK_DEFAULT_ACCOUNT")
env = None
if cdk_account:
    env = cdk.Environment(account=cdk_account, region="us-east-1")

# Create stacks. Pass env only when available to avoid context provider lookups
if env:
    network_stack = NetworkStack(app, "NetworkStack", env=env, domain_name=domain_name)
    database_stack = DatabaseStack(
        app, "DatabaseStack", env=env, network_stack=network_stack
    )
    compute_stack = ComputeStack(
        app, "ComputeStack", env=env, network_stack=network_stack
    )
    storage_stack = StorageStack(app, "StorageStack", env=env)
    security_stack = SecurityStack(app, "SecurityStack", env=env)
    monitoring_stack = MonitoringStack(
        app, "MonitoringStack", env=env, logs_bucket=storage_stack.logs_bucket
    )
else:
    network_stack = NetworkStack(app, "NetworkStack", domain_name=domain_name)
    database_stack = DatabaseStack(app, "DatabaseStack", network_stack=network_stack)
    compute_stack = ComputeStack(app, "ComputeStack", network_stack=network_stack)
    storage_stack = StorageStack(app, "StorageStack")
    security_stack = SecurityStack(app, "SecurityStack")
    monitoring_stack = MonitoringStack(
        app, "MonitoringStack", logs_bucket=storage_stack.logs_bucket
    )

# Add dependencies between stacks
database_stack.add_dependency(network_stack)
compute_stack.add_dependency(network_stack)
storage_stack.add_dependency(network_stack)
security_stack.add_dependency(network_stack)
monitoring_stack.add_dependency(network_stack)

# Apply resource tags per FR-009 requirement
# All four tags (Project, Environment, Owner, CostCenter) are required
cdk.Tags.of(app).add("Project", "aws-hackathon")
cdk.Tags.of(app).add("Environment", environment)
cdk.Tags.of(app).add("Owner", os.getenv("OWNER", "hackathon-team"))
cdk.Tags.of(app).add("CostCenter", os.getenv("COST_CENTER", "hackathon"))

app.synth()

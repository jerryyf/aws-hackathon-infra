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

# Optional domain name can be provided via cdk context: cdk --context domain_name=example.com
domain_name = app.node.try_get_context('domain_name') or os.getenv('DOMAIN_NAME')

# Only attempt Route53 discovery if CDK_DEFAULT_ACCOUNT is set (i.e. env provided)
cdk_account = os.getenv('CDK_DEFAULT_ACCOUNT')
if not domain_name and cdk_account:
    try:
        import boto3

        client = boto3.client('route53')
        resp = client.list_hosted_zones()
        # pick first public hosted zone (IsPrivateZone == False)
        public_zones = [z for z in resp.get('HostedZones', []) if not z.get('Config', {}).get('PrivateZone')]
        if public_zones:
            # HostedZone Name has trailing dot, strip it
            zone_name = public_zones[0].get('Name', '')
            if zone_name.endswith('.'):
                zone_name = zone_name[:-1]
            domain_name = zone_name
    except Exception:
        # Ignore discovery failures; synth will continue without a public domain.
        domain_name = domain_name

# Environment configuration (only set if account available)
cdk_account = os.getenv('CDK_DEFAULT_ACCOUNT')
env = None
if cdk_account:
    env = cdk.Environment(account=cdk_account, region='us-east-1')

# Create stacks. Pass env only when available to avoid context provider lookups
if env:
    network_stack = NetworkStack(app, "NetworkStack", env=env, domain_name=domain_name)
    database_stack = DatabaseStack(app, "DatabaseStack", env=env, network_stack=network_stack)
    compute_stack = ComputeStack(app, "ComputeStack", env=env, network_stack=network_stack)
    storage_stack = StorageStack(app, "StorageStack", env=env)
    security_stack = SecurityStack(app, "SecurityStack", env=env)
    monitoring_stack = MonitoringStack(app, "MonitoringStack", env=env, logs_bucket=storage_stack.logs_bucket)
else:
    network_stack = NetworkStack(app, "NetworkStack", domain_name=domain_name)
    database_stack = DatabaseStack(app, "DatabaseStack", network_stack=network_stack)
    compute_stack = ComputeStack(app, "ComputeStack", network_stack=network_stack)
    storage_stack = StorageStack(app, "StorageStack")
    security_stack = SecurityStack(app, "SecurityStack")
    monitoring_stack = MonitoringStack(app, "MonitoringStack", logs_bucket=storage_stack.logs_bucket)

# Add dependencies between stacks
database_stack.add_dependency(network_stack)
compute_stack.add_dependency(network_stack)
storage_stack.add_dependency(network_stack)
security_stack.add_dependency(network_stack)
monitoring_stack.add_dependency(network_stack)

app.synth()
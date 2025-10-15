#!/usr/bin/env python3
"""
BidOps.AI CDK Application

Main entry point for the BidOps.AI CDK infrastructure.
"""

import os
import aws_cdk as cdk
from stacks.cognito_stack import CognitoStack


app = cdk.App()

# Get environment from context or default to 'dev'
environment = app.node.try_get_context("environment") or "dev"

# Get AWS account and region from environment or use defaults
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

# Create Cognito Stack
cognito_stack = CognitoStack(
    app,
    f"BidOpsAI-Cognito-{environment}",
    environment=environment,
    env=env,
    description=f"BidOps.AI Cognito User Pool Stack for {environment}",
    tags={
        "Environment": environment,
        "Project": "BidOpsAI",
        "ManagedBy": "CDK",
    },
)

app.synth()

#!/bin/bash

# Deployment script for AWS Hackathon Infrastructure
# Deploys CDK stacks to AWS

set -e

echo "Starting deployment of AWS Hackathon Infrastructure..."

# Function to log deployment status
log_deployment() {
    local stack=$1
    local status=$2
    echo "$(date): $stack deployment $status"
    # In a real scenario, send to CloudWatch or monitoring system
}

# Change to CDK directory
cd cdk

# Install dependencies if not already installed
pip install -r requirements.txt

# Synthesize CloudFormation templates
echo "Synthesizing CloudFormation templates..."
if cdk synth; then
    log_deployment "Synth" "succeeded"
else
    log_deployment "Synth" "failed"
    exit 1
fi

# Deploy stacks in order
echo "Deploying NetworkStack..."
if cdk deploy NetworkStack --require-approval never; then
    log_deployment "NetworkStack" "succeeded"
else
    log_deployment "NetworkStack" "failed"
    exit 1
fi

echo "Deploying DatabaseStack..."
if cdk deploy DatabaseStack --require-approval never; then
    log_deployment "DatabaseStack" "succeeded"
else
    log_deployment "DatabaseStack" "failed"
    exit 1
fi

echo "Deploying ComputeStack..."
if cdk deploy ComputeStack --require-approval never; then
    log_deployment "ComputeStack" "succeeded"
else
    log_deployment "ComputeStack" "failed"
    exit 1
fi

echo "Deploying StorageStack..."
if cdk deploy StorageStack --require-approval never; then
    log_deployment "StorageStack" "succeeded"
else
    log_deployment "StorageStack" "failed"
    exit 1
fi

echo "Deploying MonitoringStack..."
if cdk deploy MonitoringStack --require-approval never; then
    log_deployment "MonitoringStack" "succeeded"
else
    log_deployment "MonitoringStack" "failed"
    exit 1
fi

log_deployment "AllStacks" "completed successfully"
echo "Deployment completed successfully!"
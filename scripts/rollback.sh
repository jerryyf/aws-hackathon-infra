#!/bin/bash

# Rollback script for AWS Hackathon Infrastructure
# Destroys CDK stacks from AWS

set -e

echo "Starting rollback of AWS Hackathon Infrastructure..."

# Change to CDK directory
cd cdk

# Destroy stacks in reverse order
echo "Destroying MonitoringStack..."
cdk destroy MonitoringStack --force

echo "Destroying StorageStack..."
cdk destroy StorageStack --force

echo "Destroying ComputeStack..."
cdk destroy ComputeStack --force

echo "Destroying DatabaseStack..."
cdk destroy DatabaseStack --force

echo "Destroying NetworkStack..."
cdk destroy NetworkStack --force

echo "Rollback completed successfully!"
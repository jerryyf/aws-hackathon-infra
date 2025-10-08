import json
import pytest
from aws_cdk.assertions import Template
from cdk.stacks.storage_stack import StorageStack
import aws_cdk as cdk


def test_s3_buckets_contract():
    """Test that S3 buckets stack outputs match contract specification"""
    app = cdk.App()

    # Create stack
    stack = StorageStack(app, "TestStorageStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Check that bucket outputs exist with correct descriptions and exports
    outputs = template.find_outputs("*")
    
    # Check knowledge base bucket
    assert "KnowledgeBaseBucketName" in outputs
    kb_output = outputs["KnowledgeBaseBucketName"]
    assert kb_output["Description"] == "Knowledge base bucket name"
    assert kb_output["Export"]["Name"] == "KnowledgeBaseBucketName"
    
    # Check logs bucket
    assert "LogsBucketName" in outputs
    logs_output = outputs["LogsBucketName"]
    assert logs_output["Description"] == "Logs bucket name"
    assert logs_output["Export"]["Name"] == "LogsBucketName"
    
    # Check BDA bucket
    assert "BdaBucketName" in outputs
    bda_output = outputs["BdaBucketName"]
    assert bda_output["Description"] == "BDA bucket name"
    assert bda_output["Export"]["Name"] == "BdaBucketName"


def test_s3_bucket_properties():
    """Test S3 bucket properties"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = Template.from_stack(stack)

    # Check all buckets have encryption, versioning, and block public access
    template.resource_count_is("AWS::S3::Bucket", 3)
    
    template.has_resource_properties("AWS::S3::Bucket", {
        "VersioningConfiguration": {
            "Status": "Enabled"
        },
        "BucketEncryption": {
            "ServerSideEncryptionConfiguration": [
                {
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "aws:kms"
                        }
                }
            ]
        },
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True,
            "BlockPublicPolicy": True,
            "IgnorePublicAcls": True,
            "RestrictPublicBuckets": True
        }
    })
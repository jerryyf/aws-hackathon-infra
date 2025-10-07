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

    # Knowledge base bucket
    assert "KnowledgeBaseBucketName" in outputs
    kb_output = outputs["KnowledgeBaseBucketName"]
    assert kb_output["Description"] == "Knowledge base bucket name"
    assert kb_output["Export"]["Name"] == "KnowledgeBaseBucketName"
    assert "Value" in kb_output

    # Logs bucket
    assert "LogsBucketName" in outputs
    logs_output = outputs["LogsBucketName"]
    assert logs_output["Description"] == "Logs bucket name"
    assert logs_output["Export"]["Name"] == "LogsBucketName"
    assert "Value" in logs_output

    # BDA bucket
    assert "BdaBucketName" in outputs
    bda_output = outputs["BdaBucketName"]
    assert bda_output["Description"] == "BDA bucket name"
    assert bda_output["Export"]["Name"] == "BdaBucketName"
    assert "Value" in bda_output


def test_s3_buckets_properties():
    """Test S3 bucket properties"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = Template.from_stack(stack)

    # Check bucket encryption and versioning
    template.has_resource_properties("AWS::S3::Bucket", {
        "BucketEncryption": {
            "ServerSideEncryptionConfiguration": [
                {
                    "ServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        },
        "VersioningConfiguration": {
            "Status": "Enabled"
        },
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True,
            "BlockPublicPolicy": True,
            "IgnorePublicAcls": True,
            "RestrictPublicBuckets": True
        }
    })
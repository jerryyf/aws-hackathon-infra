import json
import pytest
from aws_cdk.assertions import Template
from cdk.stacks.storage_stack import StorageStack
import aws_cdk as cdk


def test_ecr_repositories_contract():
    """Test that ECR repositories stack output matches contract specification"""
    app = cdk.App()

    # Create stack
    stack = StorageStack(app, "TestStorageStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Check that ECR repository output exists with correct description and export
    outputs = template.find_outputs("EcrRepositoryUri")
    assert len(outputs) == 1
    repo_output = outputs["EcrRepositoryUri"]
    assert repo_output["Description"] == "ECR repository URI"
    assert repo_output["Export"]["Name"] == "EcrRepositoryUri"
    assert "Value" in repo_output


def test_ecr_repositories_properties():
    """Test ECR repository properties"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = Template.from_stack(stack)

    # Check ECR repository has image scanning enabled
    template.has_resource_properties("AWS::ECR::Repository", {
        "ImageScanningConfiguration": {
            "ScanOnPush": True
        }
    })
import json
import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_public_subnets_contract():
    """Test that public subnets stack output matches contract specification"""
    app = cdk.App()

    # Create stack
    stack = NetworkStack(app, "TestNetworkStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Check that public subnets output exists with correct description and export
    outputs = template.find_outputs("PublicSubnetIds")
    assert len(outputs) == 1
    subnet_output = outputs["PublicSubnetIds"]
    assert subnet_output["Description"] == "Public subnet IDs"
    assert subnet_output["Export"]["Name"] == "PublicSubnetIds"
    assert "Value" in subnet_output


def test_public_subnets_properties():
    """Test public subnet properties"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    # Check subnet resources exist
    template.resource_count_is("AWS::EC2::Subnet", 8)  # 2 AZs * 4 subnet types

    # Check that public subnets have MapPublicIpOnLaunch enabled
    # (CDK assigns CIDRs and AZs automatically)
    template.has_resource_properties("AWS::EC2::Subnet", {
        "MapPublicIpOnLaunch": True
    })
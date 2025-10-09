import json
import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_private_app_subnets_contract():
    """Test that private app subnets stack output matches contract specification"""
    app = cdk.App()

    # Create stack
    stack = NetworkStack(app, "TestNetworkStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Check that private app subnets output exists with correct description and export
    outputs = template.find_outputs("PrivateAppSubnetIds")
    assert len(outputs) == 1
    subnet_output = outputs["PrivateAppSubnetIds"]
    assert subnet_output["Description"] == "Private app subnet IDs"
    assert subnet_output["Export"]["Name"] == "PrivateAppSubnetIds"
    assert "Value" in subnet_output


def test_private_app_subnets_properties():
    """Test private app subnet properties"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    # Check that private app subnets have MapPublicIpOnLaunch disabled
    # (CDK assigns CIDRs and AZs automatically, but we can check the type)
    template.has_resource_properties("AWS::EC2::Subnet", {
        "MapPublicIpOnLaunch": False
    })
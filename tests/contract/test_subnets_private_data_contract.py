import json
import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_private_data_subnets_contract():
    """Test that private data subnets stack output matches contract specification"""
    app = cdk.App()

    # Create stack
    stack = NetworkStack(app, "TestNetworkStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Check that private data subnets output exists with correct description and export
    outputs = template.find_outputs("PrivateDataSubnetIds")
    assert len(outputs) == 1
    subnet_output = outputs["PrivateDataSubnetIds"]
    assert subnet_output["Description"] == "Private data subnet IDs"
    assert subnet_output["Export"]["Name"] == "PrivateDataSubnetIds"
    assert "Value" in subnet_output


def test_private_data_subnets_properties():
    """Test private data subnet properties"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    # Check that private data subnets have MapPublicIpOnLaunch disabled
    template.has_resource_properties("AWS::EC2::Subnet", {
        "MapPublicIpOnLaunch": False
    })
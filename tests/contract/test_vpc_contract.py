import json
import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_vpc_endpoint_contract():
    """Test that VPC stack output matches contract specification"""
    app = cdk.App()

    # Create stack
    stack = NetworkStack(app, "TestNetworkStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Check that VPC output exists with correct description and export
    outputs = template.find_outputs("VpcId")
    assert len(outputs) == 1
    vpc_output = outputs["VpcId"]
    assert vpc_output["Description"] == "VPC ID"
    assert vpc_output["Export"]["Name"] == "VpcId"
    assert "Value" in vpc_output

    # Check VPC properties
    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.0.0.0/16",
        "EnableDnsHostnames": True,
        "EnableDnsSupport": True
    })


def test_vpc_output_schema():
    """Test VPC output matches contract schema"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    # Validate output structure matches contract
    outputs = template.find_outputs("*")
    assert "VpcId" in outputs

    vpc_output = outputs["VpcId"]
    assert "Description" in vpc_output
    assert "Value" in vpc_output
    assert vpc_output["Description"] == "VPC ID"
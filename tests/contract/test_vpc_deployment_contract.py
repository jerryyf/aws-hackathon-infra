import json
import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_vpc_deployment_readiness():
    """Test that VPC stack is ready for deployment with correct outputs"""
    app = cdk.App()

    # Create stack
    stack = NetworkStack(app, "TestNetworkStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Check that VPC output exists with correct export for cross-stack references
    outputs = template.find_outputs("VpcId")
    assert len(outputs) == 1
    vpc_output = outputs["VpcId"]
    assert vpc_output["Description"] == "VPC ID"
    assert "Export" in vpc_output
    assert vpc_output["Export"]["Name"] == "VpcId"
    assert "Value" in vpc_output

    # Check VPC properties for deployment
    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.0.0.0/16",
        "EnableDnsHostnames": True,
        "EnableDnsSupport": True
    })

    # Check that all required subnets are created for deployment
    subnets = template.find_resources("AWS::EC2::Subnet")
    assert len(subnets) == 8  # 2 AZs * 4 subnet types

    # Check that internet gateway exists for public access
    igw = template.find_resources("AWS::EC2::InternetGateway")
    assert len(igw) == 1

    # Check that NAT gateways exist for private subnet internet access
    nat_gws = template.find_resources("AWS::EC2::NatGateway")
    assert len(nat_gws) == 2  # One per AZ


def test_vpc_deployment_outputs():
    """Test VPC deployment outputs match contract for dependent stacks"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    # Validate all required outputs are present for deployment
    outputs = template.find_outputs("*")
    required_outputs = [
        "VpcId", "PublicSubnetIds", "PrivateAppSubnetIds",
        "PrivateAgentSubnetIds", "PrivateDataSubnetIds", "AlbDnsName"
    ]

    for output_name in required_outputs:
        assert output_name in outputs
        assert "Export" in outputs[output_name]
        assert "Value" in outputs[output_name]
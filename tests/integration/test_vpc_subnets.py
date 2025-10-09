import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_vpc_subnets_integration():
    """Integration test for VPC and subnets creation"""
    app = cdk.App()

    # Create network stack
    stack = NetworkStack(app, "TestNetworkStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Verify VPC exists
    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.0.0.0/16",
        "EnableDnsSupport": True,
        "EnableDnsHostnames": True
    })

    # Verify subnets are created (8 total: 2 public + 2 private app + 2 private agent + 2 private data)
    template.resource_count_is("AWS::EC2::Subnet", 8)

    # Verify public subnets
    template.has_resource_properties("AWS::EC2::Subnet", {
        "MapPublicIpOnLaunch": True
    })

    # Verify private subnets
    template.has_resource_properties("AWS::EC2::Subnet", {
        "MapPublicIpOnLaunch": False
    })

    # Verify outputs
    outputs = template.find_outputs("*")
    required_outputs = [
        "VpcId", "PublicSubnetIds", "PrivateAppSubnetIds",
        "PrivateAgentSubnetIds", "PrivateDataSubnetIds", "AlbDnsName"
    ]
    for output_name in required_outputs:
        assert output_name in outputs

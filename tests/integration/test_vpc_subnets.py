import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_vpc_subnets_integration():
    """Integration test for VPC and subnets creation"""
    app = cdk.App()

    # Create network stack
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    # Verify VPC exists
    template.has_resource("AWS::EC2::VPC", {})

    # Verify all subnet types exist (8 subnets: 4 types * 2 AZs)
    template.resource_count_is("AWS::EC2::Subnet", 8)

    # Verify internet gateway exists
    template.has_resource("AWS::EC2::InternetGateway", {})

    # Verify NAT gateways exist (2 for 2 AZs)
    template.resource_count_is("AWS::EC2::NatGateway", 2)

    # Verify VPC endpoints exist (S3 gateway + 6 interface endpoints)
    template.resource_count_is("AWS::EC2::VPCEndpoint", 7)
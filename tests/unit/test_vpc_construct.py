import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_vpc_construct():
    """Test VPC construct creation"""
    app = cdk.App()
    stack = NetworkStack(app, "TestStack")

    template = Template.from_stack(stack)

    # Check VPC exists
    template.resource_count_is("AWS::EC2::VPC", 1)

    # Check subnets
    # NetworkStack defines 4 subnet tiers (Public, PrivateApp, PrivateAgent, PrivateData)
    # across 2 AZs -> 4 * 2 = 8 subnets (2 public + 6 private)
    template.resource_count_is("AWS::EC2::Subnet", 8)

    # Check ALBs (public + internal)
    template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 2)

    # Check VPC endpoints
    template.resource_count_is("AWS::EC2::VPCEndpoint", 7)  # S3 + 6 interface
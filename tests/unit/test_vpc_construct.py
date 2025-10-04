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
    template.resource_count_is("AWS::EC2::Subnet", 6)  # 2 public + 4 private

    # Check ALB
    template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)

    # Check VPC endpoints
    template.resource_count_is("AWS::EC2::VPCEndpoint", 7)  # S3 + 6 interface
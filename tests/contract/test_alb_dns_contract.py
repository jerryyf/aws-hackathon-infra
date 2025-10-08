import json
import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_alb_dns_contract():
    """Test that ALB DNS stack output matches contract specification"""
    app = cdk.App()

    # Create stack
    stack = NetworkStack(app, "TestNetworkStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Check that ALB DNS output exists with correct description and export
    outputs = template.find_outputs("AlbDnsName")
    assert len(outputs) == 1
    alb_output = outputs["AlbDnsName"]
    assert alb_output["Description"] == "Public ALB DNS name"
    assert alb_output["Export"]["Name"] == "AlbDnsName"
    assert "Value" in alb_output


def test_alb_properties():
    """Test ALB properties"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    # Check ALB is internet-facing
    template.has_resource_properties("AWS::ElasticLoadBalancingV2::LoadBalancer", {
        "Scheme": "internet-facing",
        "Type": "application"
    })

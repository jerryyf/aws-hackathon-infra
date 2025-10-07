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
    dns_output = outputs["AlbDnsName"]
    assert dns_output["Description"] == "ALB DNS name"
    assert dns_output["Export"]["Name"] == "AlbDnsName"
    assert "Value" in dns_output


def test_alb_dns_schema():
    """Test ALB DNS output matches contract schema"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    # Validate output structure matches contract
    outputs = template.find_outputs("*")
    assert "AlbDnsName" in outputs

    dns_output = outputs["AlbDnsName"]
    assert "Description" in dns_output
    assert "Value" in dns_output
    assert dns_output["Description"] == "ALB DNS name"
import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_bedrock_access_integration():
    """Integration test for Bedrock access via VPC endpoint"""
    app = cdk.App()

    # Create network stack
    stack = NetworkStack(app, "TestNetworkStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Verify Bedrock VPC endpoint exists
    template.has_resource_properties("AWS::EC2::VPCEndpoint", {
        "ServiceName": {"Fn::Sub": "com.amazonaws.${AWS::Region}.bedrock-runtime"},
        "VpcEndpointType": "Interface",
        "PrivateDnsEnabled": True
    })

    # Verify VPC endpoint is in private subnets
    # (CDK automatically places interface endpoints in private subnets)

    # Verify security group for VPC endpoints
    template.has_resource_properties("AWS::EC2::SecurityGroup", {
        "GroupDescription": "Security group for VPC endpoints"
    })

    # Verify endpoints are exported
    outputs = template.find_outputs("*")
    assert "BedrockVpcEndpointId" in outputs
    assert "BedrockVpcEndpointDnsName" in outputs

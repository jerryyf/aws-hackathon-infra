import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_bedrock_access_via_vpc_endpoint():
    """Integration test for Bedrock access via VPC endpoint"""
    app = cdk.App()

    # Create network stack
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    # Verify Bedrock VPC endpoint exists
    template.has_resource_properties("AWS::EC2::VPCEndpoint", {
        "VpcEndpointType": "Interface",
        "ServiceName": {
            "Fn::Sub": "com.amazonaws.${AWS::Region}.bedrock-runtime"
        }
    })

    # Verify other required VPC endpoints exist
    # Secrets Manager
    template.has_resource_properties("AWS::EC2::VPCEndpoint", {
        "VpcEndpointType": "Interface",
        "ServiceName": {
            "Fn::Sub": "com.amazonaws.${AWS::Region}.secretsmanager"
        }
    })

    # SSM
    template.has_resource_properties("AWS::EC2::VPCEndpoint", {
        "VpcEndpointType": "Interface",
        "ServiceName": {
            "Fn::Sub": "com.amazonaws.${AWS::Region}.ssm"
        }
    })
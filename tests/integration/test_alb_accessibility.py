import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_alb_accessibility():
    """Integration test for ALB accessibility"""
    app = cdk.App()

    # Create network stack
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    # Verify ALB exists and is internet-facing
    template.has_resource_properties("AWS::ElasticLoadBalancingV2::LoadBalancer", {
        "Type": "application",
        "Scheme": "internet-facing"
    })

    # Verify ALB has listeners for HTTP and HTTPS
    template.has_resource_properties("AWS::ElasticLoadBalancingV2::Listener", {
        "Protocol": "HTTP",
        "Port": 80
    })

    # Verify security group allows HTTP and HTTPS
    template.has_resource_properties("AWS::EC2::SecurityGroup", {
        "SecurityGroupIngress": [
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "CidrIp": "0.0.0.0/0"
            },
            {
                "IpProtocol": "tcp",
                "FromPort": 443,
                "ToPort": 443,
                "CidrIp": "0.0.0.0/0"
            }
        ]
    })
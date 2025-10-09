import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


def test_alb_accessibility_integration():
    """Integration test for load balancer accessibility"""
    app = cdk.App()

    # Create network stack
    stack = NetworkStack(app, "TestNetworkStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Verify ALB is internet-facing
    template.has_resource_properties("AWS::ElasticLoadBalancingV2::LoadBalancer", {
        "Scheme": "internet-facing",
        "Type": "application"
    })

    # Verify ALB has security group
    alb_sg_ref = template.find_resources("AWS::ElasticLoadBalancingV2::LoadBalancer")["Alb"]["Properties"]["SecurityGroups"]
    assert len(alb_sg_ref) == 1

    # Verify security group allows HTTPS from internet
    template.has_resource_properties("AWS::EC2::SecurityGroup", {
        "GroupDescription": "Security group for ALB",
        "SecurityGroupIngress": [
            {
                "IpProtocol": "tcp",
                "FromPort": 443,
                "ToPort": 443,
                "CidrIp": "0.0.0.0/0"
            }
        ]
    })

    # Verify WAF is associated
    template.has_resource_properties("AWS::WAFv2::WebACLAssociation", {
        "ResourceArn": {"Ref": "Alb"}
    })
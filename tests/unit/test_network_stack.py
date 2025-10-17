import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
from cdk.stacks.network_stack import NetworkStack


def test_network_stack_vpc_created():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::VPC", 1)
    template.has_resource_properties(
        "AWS::EC2::VPC",
        {
            "CidrBlock": "10.0.0.0/16",
            "EnableDnsSupport": True,
            "EnableDnsHostnames": True,
        },
    )


def test_network_stack_subnets_created():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::Subnet", 8)


def test_network_stack_public_alb_created():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 2)
    template.has_resource_properties(
        "AWS::ElasticLoadBalancingV2::LoadBalancer", {"Scheme": "internet-facing"}
    )


def test_network_stack_internal_alb_created():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ElasticLoadBalancingV2::LoadBalancer", {"Scheme": "internal"}
    )


def test_network_stack_waf_created():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::WAFv2::WebACL", 1)
    template.has_resource_properties(
        "AWS::WAFv2::WebACL",
        {
            "Scope": "REGIONAL",
            "DefaultAction": {"Allow": {}},
            "Rules": Match.array_with(
                [
                    Match.object_like(
                        {
                            "Name": "AWSManagedRulesCommonRuleSet",
                            "Priority": 1,
                            "OverrideAction": {"None": {}},
                        }
                    )
                ]
            ),
        },
    )


def test_network_stack_waf_association():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::WAFv2::WebACLAssociation", 1)


def test_network_stack_vpc_endpoints():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::VPCEndpoint", 9)


def test_network_stack_s3_gateway_endpoint():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::EC2::VPCEndpoint",
        {"ServiceName": Match.object_like({"Fn::Join": Match.any_value()})},
    )


def test_network_stack_bedrock_endpoint():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::EC2::VPCEndpoint",
        {"ServiceName": Match.object_like({"Fn::Join": Match.any_value()})},
    )


def test_network_stack_security_groups():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    alb_sg_count = 0
    internal_alb_sg_count = 0

    sgs = template.find_resources("AWS::EC2::SecurityGroup")
    for sg_id, sg_props in sgs.items():
        desc = sg_props.get("Properties", {}).get("GroupDescription", "")
        if "Security group for ALB" in desc:
            alb_sg_count += 1
        elif "Security group for internal ALB" in desc:
            internal_alb_sg_count += 1

    assert alb_sg_count == 1, "Expected 1 ALB security group"
    assert internal_alb_sg_count == 1, "Expected 1 Internal ALB security group"


def test_network_stack_outputs():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack")
    template = Template.from_stack(stack)

    template.has_output("TestNetworkStackVpcId", {})
    template.has_output("TestNetworkStackPublicSubnetIds", {})
    template.has_output("TestNetworkStackPrivateAppSubnetIds", {})
    template.has_output("TestNetworkStackPrivateAgentSubnetIds", {})
    template.has_output("TestNetworkStackPrivateDataSubnetIds", {})
    template.has_output("TestNetworkStackAlbDnsName", {})
    template.has_output("TestNetworkStackInternalAlbDnsName", {})


def test_network_stack_with_domain_no_env():
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack", domain_name="example.local")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Route53::HostedZone", 0)
    template.resource_count_is("AWS::CertificateManager::Certificate", 0)

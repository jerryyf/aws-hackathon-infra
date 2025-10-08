from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_route53 as route53,
    aws_certificatemanager as acm,
    aws_wafv2 as wafv2,
    aws_shield as shield,
    CfnOutput,
)
from constructs import Construct


class NetworkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC
        self.vpc = ec2.Vpc(
            self, "Vpc",
            cidr="10.0.0.0/16",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateApp",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateAgent",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateData",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
            ]
        )

        # Security Groups
        self.alb_security_group = ec2.SecurityGroup(
            self, "AlbSecurityGroup",
            vpc=self.vpc,
            description="Security group for ALB"
        )
        self.alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP"
        )
        self.alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow HTTPS"
        )

        # Public ALB
        self.alb = elbv2.ApplicationLoadBalancer(
            self, "Alb",
            vpc=self.vpc,
            internet_facing=True,
            security_group=self.alb_security_group
        )

        # Internal ALB Security Group
        self.internal_alb_security_group = ec2.SecurityGroup(
            self, "InternalAlbSecurityGroup",
            vpc=self.vpc,
            description="Security group for internal ALB"
        )
        self.internal_alb_security_group.add_ingress_rule(
            ec2.Peer.ipv4(self.vpc.vpc_cidr_block), ec2.Port.tcp(80), "Allow HTTP from VPC"
        )
        self.internal_alb_security_group.add_ingress_rule(
            ec2.Peer.ipv4(self.vpc.vpc_cidr_block), ec2.Port.tcp(443), "Allow HTTPS from VPC"
        )

        # Internal ALB
        self.internal_alb = elbv2.ApplicationLoadBalancer(
            self, "InternalAlb",
            vpc=self.vpc,
            internet_facing=False,
            security_group=self.internal_alb_security_group
        )

        # WAF
        self.waf = wafv2.CfnWebACL(
            self, "WafAcl",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            scope="REGIONAL",
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesCommonRuleSet",
                    priority=1,
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesCommonRuleSet"
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWSManagedRulesCommonRuleSetMetric",
                        sampled_requests_enabled=True
                    )
                )
            ],
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="WafAcl",
                sampled_requests_enabled=True
            )
        )

        # Associate WAF with ALB
        wafv2.CfnWebACLAssociation(
            self, "WafAssociation",
            resource_arn=self.alb.load_balancer_arn,
            web_acl_arn=self.waf.attr_arn
        )

        # Shield Standard is enabled by default for ALBs

        # Route 53 Hosted Zone
        self.hosted_zone = route53.HostedZone(
            self, "HostedZone",
            zone_name="hackathon.local"
        )

        # ACM Certificate
        self.certificate = acm.Certificate(
            self, "Certificate",
            domain_name="hackathon.local",
            validation=acm.CertificateValidation.from_dns(self.hosted_zone)
        )

        # VPC Endpoints
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3
        )

        # Bedrock endpoint
        self.vpc.add_interface_endpoint(
            "BedrockEndpoint",
            service=ec2.InterfaceVpcEndpointService("bedrock-runtime")
        )

        self.vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER
        )

        self.vpc.add_interface_endpoint(
            "SsmEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SSM
        )

        self.vpc.add_interface_endpoint(
            "EcrApiEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.ECR
        )

        self.vpc.add_interface_endpoint(
            "EcrDockerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER
        )

        self.vpc.add_interface_endpoint(
            "CloudWatchLogsEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS
        )

        # Outputs
        CfnOutput(
            self, "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID",
            export_name="VpcId"
        )

        CfnOutput(
            self, "PublicSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
            description="Public subnet IDs",
            export_name="PublicSubnetIds"
        )

        CfnOutput(
            self, "PrivateAppSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.private_subnets if "PrivateApp" in subnet.node.id]),
            description="Private app subnet IDs",
            export_name="PrivateAppSubnetIds"
        )

        CfnOutput(
            self, "PrivateAgentSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.private_subnets if "PrivateAgent" in subnet.node.id]),
            description="Private agent subnet IDs",
            export_name="PrivateAgentSubnetIds"
        )

        CfnOutput(
            self, "PrivateDataSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.private_subnets if "PrivateData" in subnet.node.id]),
            description="Private data subnet IDs",
            export_name="PrivateDataSubnetIds"
        )

        CfnOutput(
            self, "AlbDnsName",
            value=self.alb.load_balancer_dns_name,
            description="Public ALB DNS name",
            export_name="AlbDnsName"
        )

        CfnOutput(
            self, "InternalAlbDnsName",
            value=self.internal_alb.load_balancer_dns_name,
            description="Internal ALB DNS name",
            export_name="InternalAlbDnsName"
        )

        CfnOutput(
            self, "HostedZoneId",
            value=self.hosted_zone.hosted_zone_id,
            description="Route 53 hosted zone ID",
            export_name="HostedZoneId"
        )

        CfnOutput(
            self, "CertificateArn",
            value=self.certificate.certificate_arn,
            description="ACM certificate ARN",
            export_name="CertificateArn"
        )
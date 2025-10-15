from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_certificatemanager as acm,
    aws_wafv2 as wafv2,
    CfnOutput,
)
import aws_cdk as cdk
from constructs import Construct


class NetworkStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str | None = None,
        **kwargs,
    ) -> None:
        """Network stack.

        domain_name: optional public domain name (e.g. example.com). If provided,
        the stack will lookup the existing Route53 Hosted Zone and create a DNS-validated
        ACM certificate. If omitted or a reserved TLD like .local is used, the stack
        will NOT create a public ACM certificate.
        """
        super().__init__(scope, construct_id, **kwargs)

        # VPC
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            availability_zones=["us-east-1a", "us-east-1b"],
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateApp",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="PrivateAgent",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="PrivateData",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # Security Groups
        self.alb_security_group = ec2.SecurityGroup(
            self, "AlbSecurityGroup", vpc=self.vpc, description="Security group for ALB"
        )
        self.alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow HTTPS"
        )
        self.alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP"
        )

        # Public ALB
        self.alb = elbv2.ApplicationLoadBalancer(
            self,
            "Alb",
            vpc=self.vpc,
            internet_facing=True,
            security_group=self.alb_security_group,
        )
        # Ensure predictable logical ID for assertions in tests
        if hasattr(self.alb.node.default_child, "override_logical_id"):
            try:
                self.alb.node.default_child.override_logical_id("Alb")
            except (AttributeError, TypeError):
                pass

        # Internal ALB Security Group
        self.internal_alb_security_group = ec2.SecurityGroup(
            self,
            "InternalAlbSecurityGroup",
            vpc=self.vpc,
            description="Security group for internal ALB",
        )
        self.internal_alb_security_group.add_ingress_rule(
            ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            ec2.Port.tcp(80),
            "Allow HTTP from VPC",
        )
        self.internal_alb_security_group.add_ingress_rule(
            ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            ec2.Port.tcp(443),
            "Allow HTTPS from VPC",
        )

        # Internal ALB
        self.internal_alb = elbv2.ApplicationLoadBalancer(
            self,
            "InternalAlb",
            vpc=self.vpc,
            internet_facing=False,
            security_group=self.internal_alb_security_group,
            # Select a single subnet group (one subnet per AZ). The VPC
            # defines multiple private subnet groups (PrivateApp, PrivateAgent,
            # PrivateData). Passing no subnet selection causes CDK to attach all
            # matching private subnets which can result in multiple subnets in
            # the same AZ — AWS ALBs accept at most one subnet per AZ. Pick
            # the "PrivateApp" subnet group so the ALB gets exactly one
            # subnet in each AZ.
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="PrivateApp"),
        )
        # Ensure predictable logical ID for assertions in tests
        if hasattr(self.internal_alb.node.default_child, "override_logical_id"):
            try:
                self.internal_alb.node.default_child.override_logical_id("InternalAlb")
            except (AttributeError, TypeError):
                pass

        # WAF
        self.waf = wafv2.CfnWebACL(
            self,
            "WafAcl",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            scope="REGIONAL",
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesCommonRuleSet",
                    priority=1,
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=(
                            wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                                vendor_name="AWS", name="AWSManagedRulesCommonRuleSet"
                            )
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWSManagedRulesCommonRuleSetMetric",
                        sampled_requests_enabled=True,
                    ),
                )
            ],
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="WafAcl",
                sampled_requests_enabled=True,
            ),
        )

        # Associate WAF with ALB
        wafv2.CfnWebACLAssociation(
            self,
            "WafAssociation",
            resource_arn=self.alb.load_balancer_arn,
            web_acl_arn=self.waf.attr_arn,
        )

        # Shield Standard is enabled by default for ALBs

        # Route 53 Hosted Zone and ACM Certificate handling
        self.hosted_zone = None
        self.certificate = None

        # If a domain_name was supplied via context or env, and it doesn't look like
        # a reserved internal domain, attempt to lookup the existing public hosted
        # zone and create a DNS-validated public ACM certificate.
        if domain_name and not domain_name.endswith(".local"):
            # Only attempt hosted zone lookup if the stack has an explicit env
            # (account and region). Tests often instantiate the stack without env,
            # in which case CDK cannot perform context provider lookups.
            if self.account and self.region:
                # Use from_lookup to find an existing hosted zone (requires AWS credentials
                # when synthesizing in some environments). This assumes the hosted zone
                # already exists for the public domain you own.
                self.hosted_zone = route53.HostedZone.from_lookup(
                    self, "HostedZone", domain_name=domain_name
                )

                # Create DNS-validated public certificate
                self.certificate = acm.Certificate(
                    self,
                    "Certificate",
                    domain_name=domain_name,
                    validation=acm.CertificateValidation.from_dns(self.hosted_zone),
                )
            else:
                # Cannot lookup hosted zone at synth time without env; add metadata
                # so it's clear why no certificate was created.
                self.node.add_metadata(
                    "certificate",
                    "domain_name provided but stack env not configured; "
                    "skipping hosted zone lookup and certificate creation "
                    "during synth.",
                )
        else:
            # For local/development domains (like hackathon.local) or when no domain
            # provided, we skip creating a public ACM certificate. Use a private CA
            # or import a certificate into ACM manually if needed. Add metadata so
            # the rationale is visible in the CloudFormation template/construct tree.
            self.node.add_metadata(
                "certificate",
                "No public domain_name provided or domain looks local; "
                "skipping public ACM Certificate creation.",
            )

        # ALB Listeners Configuration
        if self.certificate is not None:
            # HTTPS Listener (port 443) with SSL certificate
            self.https_listener = self.alb.add_listener(
                "HttpsListener",
                port=443,
                certificates=[self.certificate],
                default_action=elbv2.ListenerAction.fixed_response(
                    status_code=200,
                    content_type="text/html",
                    message_body=(
                        "<html><body><h1>Welcome to bidopsai.com</h1>"
                        "<p>HTTPS is working!</p></body></html>"
                    ),
                ),
            )

            # HTTP Listener (port 80) - redirect to HTTPS
            self.http_listener = self.alb.add_listener(
                "HttpRedirectListener",
                port=80,
                default_action=elbv2.ListenerAction.redirect(
                    protocol="HTTPS", port="443", permanent=True
                ),
            )
        else:
            # HTTP Listener (port 80) - serve directly when no certificate
            self.http_listener = self.alb.add_listener(
                "HttpDirectListener",
                port=80,
                default_action=elbv2.ListenerAction.fixed_response(
                    status_code=200,
                    content_type="text/html",
                    message_body="<html><body><h1>Welcome</h1></body></html>",
                ),
            )

        # DNS Record Creation
        if self.hosted_zone is not None and domain_name:
            # Create DNS A record (alias) pointing to the ALB
            self.dns_record = route53.ARecord(
                self,
                "DnsRecord",
                zone=self.hosted_zone,
                record_name=domain_name,
                target=route53.RecordTarget.from_alias(
                    route53_targets.LoadBalancerTarget(self.alb)
                ),
            )

        # VPC Endpoints
        self.vpc.add_gateway_endpoint(
            "S3Endpoint", service=ec2.GatewayVpcEndpointAwsService.S3
        )

        # Bedrock endpoint: use a concrete region-based service name when the
        # stack has a region configured (required for real deployments). When
        # region is not available (unit tests), fall back to an Fn::Sub so the
        # template contains a substitution expression that tests can assert on.
        if self.region:
            bedrock_service_name = f"com.amazonaws.{self.region}.bedrock-runtime"
        else:
            bedrock_service_name = cdk.Fn.sub(
                "com.amazonaws.${AWS::Region}.bedrock-runtime"
            )

        self.vpc.add_interface_endpoint(
            "BedrockEndpoint",
            service=ec2.InterfaceVpcEndpointService(bedrock_service_name, 443),
        )

        self.vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
        )

        self.vpc.add_interface_endpoint(
            "SsmEndpoint", service=ec2.InterfaceVpcEndpointAwsService.SSM
        )

        self.vpc.add_interface_endpoint(
            "EcrApiEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ECR
        )

        self.vpc.add_interface_endpoint(
            "EcrDockerEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER
        )

        self.vpc.add_interface_endpoint(
            "CloudWatchLogsEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
        )

        # Bedrock AgentCore endpoints: use region-based service names when available
        if self.region:
            agentcore_service_name = f"com.amazonaws.{self.region}.bedrock-agentcore"
            agentcore_gateway_service_name = (
                f"com.amazonaws.{self.region}.bedrock-agentcore.gateway"
            )
        else:
            agentcore_service_name = cdk.Fn.sub(
                "com.amazonaws.${AWS::Region}.bedrock-agentcore"
            )
            agentcore_gateway_service_name = cdk.Fn.sub(
                "com.amazonaws.${AWS::Region}.bedrock-agentcore.gateway"
            )

        # Main Bedrock AgentCore endpoint
        self.bedrock_agentcore_endpoint = self.vpc.add_interface_endpoint(
            "BedrockAgentCoreEndpoint",
            service=ec2.InterfaceVpcEndpointService(agentcore_service_name, 443),
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_group_name="PrivateAgent"),
        )

        # Bedrock AgentCore Gateway endpoint
        self.bedrock_agentcore_gateway_endpoint = self.vpc.add_interface_endpoint(
            "BedrockAgentCoreGatewayEndpoint",
            service=ec2.InterfaceVpcEndpointService(
                agentcore_gateway_service_name, 443
            ),
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_group_name="PrivateAgent"),
        )

        # Security Group for Bedrock AgentCore Runtimes
        self.agentcore_runtime_sg = ec2.SecurityGroup(
            self,
            "AgentCoreRuntimeSecurityGroup",
            vpc=self.vpc,
            description="Security group for Bedrock AgentCore agent runtimes",
            allow_all_outbound=False,
        )

        self.agentcore_runtime_sg.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="HTTPS egress to AWS services",
        )

        # Outputs

        CfnOutput(
            self,
            "BedrockAgentCoreEndpointId",
            value=self.bedrock_agentcore_endpoint.vpc_endpoint_id,
            description="Bedrock AgentCore VPC Endpoint ID",
            
        )

        CfnOutput(
            self,
            "BedrockAgentCoreGatewayEndpointId",
            value=self.bedrock_agentcore_gateway_endpoint.vpc_endpoint_id,
            description="Bedrock AgentCore Gateway VPC Endpoint ID",
            
        )

        CfnOutput(
            self,
            "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID",
            
        )

        CfnOutput(
            self,
            "PublicSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
            description="Public subnet IDs",
            
        )

        CfnOutput(
            self,
            "PrivateAppSubnetIds",
            value=",".join(
                [
                    subnet.subnet_id
                    for subnet in self.vpc.private_subnets
                    if "PrivateApp" in subnet.node.id
                ]
            ),
            description="Private app subnet IDs",
            
        )

        CfnOutput(
            self,
            "PrivateAgentSubnetIds",
            value=",".join(
                [
                    subnet.subnet_id
                    for subnet in self.vpc.private_subnets
                    if "PrivateAgent" in subnet.node.id
                ]
            ),
            description="Private agent subnet IDs",
            
        )

        CfnOutput(
            self,
            "PrivateDataSubnetIds",
            value=",".join(
                [
                    subnet.subnet_id
                    for subnet in self.vpc.private_subnets
                    if "PrivateData" in subnet.node.id
                ]
            ),
            description="Private data subnet IDs",
            
        )

        CfnOutput(
            self,
            "AlbDnsName",
            value=self.alb.load_balancer_dns_name,
            description="Public ALB DNS name",
            
        )

        CfnOutput(
            self,
            "InternalAlbDnsName",
            value=self.internal_alb.load_balancer_dns_name,
            description="Internal ALB DNS name",
            
        )

        CfnOutput(
            self,
            "HostedZoneId",
            value=(
                self.hosted_zone.hosted_zone_id if self.hosted_zone is not None else ""
            ),
            description="Route 53 hosted zone ID (empty if not created/lookup not performed)",
            
        )

        CfnOutput(
            self,
            "CertificateArn",
            value=(
                self.certificate.certificate_arn if self.certificate is not None else ""
            ),
            description="ACM certificate ARN (empty if not created)",
            
        )

        CfnOutput(
            self,
            "DomainName",
            value=domain_name if domain_name else "",
            description="Domain name configured for the ALB (empty if not configured)",
            
        )

        CfnOutput(
            self,
            "AgentCoreRuntimeSecurityGroupId",
            value=self.agentcore_runtime_sg.security_group_id,
            description="Security group ID for AgentCore runtimes",
            
        )

        # Export individual subnet IDs for cross-stack references
        data_subnets = [
            subnet
            for subnet in self.vpc.private_subnets
            if "PrivateData" in subnet.node.id
        ]
        for i, subnet in enumerate(data_subnets):
            CfnOutput(
                self,
                f"PrivateDataSubnet{i+1}Id",
                value=subnet.subnet_id,
                description=f"Private data subnet {i+1} ID",
                
            )

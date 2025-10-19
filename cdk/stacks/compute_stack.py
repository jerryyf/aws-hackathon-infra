from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_servicediscovery as servicediscovery,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    Duration,
    CfnOutput,
)
from constructs import Construct
from config import ECS_RESOURCE_ALLOCATIONS, ENVIRONMENT


class ComputeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        network_stack = kwargs.pop("network_stack", None)
        storage_stack = kwargs.pop("storage_stack", None)
        _ = kwargs.pop("security_stack", None)
        _ = kwargs.pop("database_stack", None)

        super().__init__(scope, construct_id, **kwargs)
        if network_stack:
            vpc = network_stack.vpc
        else:
            vpc = ec2.Vpc(self, "TestVpc", cidr="10.0.0.0/16", max_azs=2)

        task_execution_role = iam.Role(
            self,
            "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="ECS task execution role for BidOpsAI services",
        )

        task_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                ],
                resources=["*"],
            )
        )

        task_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=["*"],
            )
        )

        task_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter", "ssm:GetParameters"],
                resources=["*"],
            )
        )
        self.task_execution_role = task_execution_role

        bff_security_group = ec2.SecurityGroup(
            self,
            "BffSecurityGroup",
            vpc=vpc,
            description="Security group for BFF tasks",
            allow_all_outbound=False,
        )
        self.bff_security_group = bff_security_group

        agent_security_group = ec2.SecurityGroup(
            self,
            "AgentSecurityGroup",
            vpc=vpc,
            description="Security group for AgentCore tasks",
            allow_all_outbound=False,
        )
        self.agent_security_group = agent_security_group

        bff_security_group.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="Allow outbound HTTPS to VPC endpoints",
        )
        agent_security_group.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="Allow outbound HTTPS to VPC endpoints",
        )

        database_stack = kwargs.get("database_stack", None)
        if database_stack and hasattr(database_stack, "rds_security_group"):
            bff_security_group.add_egress_rule(
                peer=database_stack.rds_security_group,
                connection=ec2.Port.tcp(5432),
                description="Allow outbound PostgreSQL to RDS",
            )
            agent_security_group.add_egress_rule(
                peer=database_stack.rds_security_group,
                connection=ec2.Port.tcp(5432),
                description="Allow outbound PostgreSQL to RDS",
            )

        self.cluster = ecs.Cluster(
            self,
            "EcsCluster",
            vpc=vpc,
            cluster_name="bidopsai-cluster",
            container_insights=True,
            enable_fargate_capacity_providers=True,
        )

        self.cluster.add_default_capacity_provider_strategy(
            [
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE", weight=70, base=0
                ),
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE_SPOT", weight=30, base=0
                ),
            ]
        )

        self.task_definition = ecs.FargateTaskDefinition(
            self, "TaskDefinition", cpu=256, memory_limit_mib=512
        )

        self.task_definition.add_container(
            "AppContainer",
            image=ecs.ContainerImage.from_registry("nginx:latest"),
            memory_limit_mib=256,
            cpu=128,
            essential=True,
        )

        CfnOutput(
            self,
            "EcsClusterName",
            value=self.cluster.cluster_name,
            description="ECS cluster name",
            export_name="EcsClusterName",
        )

        CfnOutput(
            self,
            "EcsClusterArn",
            value=self.cluster.cluster_arn,
            description="ECS cluster ARN",
            export_name="EcsClusterArn",
        )

        cpu = ECS_RESOURCE_ALLOCATIONS.get(ENVIRONMENT, {"cpu": 1024})["cpu"]
        memory = ECS_RESOURCE_ALLOCATIONS.get(ENVIRONMENT, {"memory": 2048})["memory"]

        bff_task_role = iam.Role(
            self,
            "BffTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Task role for BFF service",
        )

        bff_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/ecs/bidopsai/bff-{ENVIRONMENT}:*"
                ],
            )
        )

        bff_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter", "ssm:GetParameters"],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/bidopsai/{ENVIRONMENT}/*"
                ],
            )
        )

        bff_task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                actions=[
                    "logs:DeleteLogGroup",
                    "logs:DeleteLogStream",
                    "ssm:DeleteParameter",
                    "ssm:DeleteParameters",
                    "iam:*",
                    "ec2:*",
                    "ecs:DeleteCluster",
                    "ecs:DeleteService",
                    "ecs:UpdateService",
                    "ecs:DeregisterTaskDefinition",
                ],
                resources=["*"],
            )
        )
        self.bff_task_role = bff_task_role

        agent_task_role = iam.Role(
            self,
            "AgentTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Task role for AgentCore service",
        )

        agent_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock-agent-runtime:InvokeAgent",
                    "bedrock-runtime:InvokeModel",
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}:{self.account}:agent/*",
                    f"arn:aws:bedrock:{self.region}::foundation-model/*",
                ],
            )
        )

        agent_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject"],
                resources=[
                    f"arn:aws:s3:::bidopsai-{ENVIRONMENT}-agent-data/*",
                ],
                effect=iam.Effect.ALLOW,
            )
        )

        agent_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket"],
                resources=[
                    f"arn:aws:s3:::bidopsai-{ENVIRONMENT}-agent-data",
                ],
            )
        )

        agent_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter", "ssm:GetParameters"],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/bidopsai/{ENVIRONMENT}/*"
                ],
            )
        )

        agent_task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                actions=[
                    "s3:DeleteBucket",
                    "s3:DeleteObject",
                    "ssm:DeleteParameter",
                    "ssm:DeleteParameters",
                    "bedrock:DeleteAgent",
                    "bedrock:UpdateAgent",
                    "iam:*",
                    "ec2:*",
                    "ecs:DeleteCluster",
                    "ecs:DeleteService",
                    "ecs:UpdateService",
                    "ecs:DeregisterTaskDefinition",
                ],
                resources=["*"],
            )
        )
        self.agent_task_role = agent_task_role

        bff_log_group = logs.LogGroup(
            self,
            "BffLogGroup",
            log_group_name=f"/ecs/bidopsai/bff-{ENVIRONMENT}",
            retention=logs.RetentionDays.ONE_WEEK,
        )
        self.bff_log_group = bff_log_group

        agent_log_group = logs.LogGroup(
            self,
            "AgentLogGroup",
            log_group_name=f"/ecs/bidopsai/agent-{ENVIRONMENT}",
            retention=logs.RetentionDays.ONE_WEEK,
        )
        self.agent_log_group = agent_log_group

        bff_image_uri = (
            storage_stack.app_ecr_repo.repository_uri
            if storage_stack
            else "nginx:latest"
        )

        self.bff_task_definition = ecs.FargateTaskDefinition(
            self,
            "BffTaskDefinition",
            cpu=cpu,
            memory_limit_mib=memory,
            execution_role=task_execution_role,
            task_role=bff_task_role,
        )

        self.bff_task_definition.add_container(
            "bff",
            image=ecs.ContainerImage.from_registry(bff_image_uri),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="bff", log_group=bff_log_group
            ),
            port_mappings=[
                ecs.PortMapping(container_port=3000, protocol=ecs.Protocol.TCP)
            ],
            essential=True,
            environment={
                "AWS_REGION": self.region,
                "ENVIRONMENT": ENVIRONMENT,
                "LOG_LEVEL": "info",
            },
        )

        agent_image_uri = (
            storage_stack.agent_ecr_repo.repository_uri
            if storage_stack
            else "nginx:latest"
        )

        self.agent_task_definition = ecs.FargateTaskDefinition(
            self,
            "AgentTaskDefinition",
            cpu=cpu,
            memory_limit_mib=memory,
            execution_role=task_execution_role,
            task_role=agent_task_role,
        )

        self.agent_task_definition.add_container(
            "agent",
            image=ecs.ContainerImage.from_registry(agent_image_uri),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="agent", log_group=agent_log_group
            ),
            port_mappings=[
                ecs.PortMapping(container_port=8080, protocol=ecs.Protocol.TCP)
            ],
            essential=True,
            environment={
                "AWS_REGION": self.region,
                "ENVIRONMENT": ENVIRONMENT,
                "LOG_LEVEL": "info",
            },
        )

        CfnOutput(
            self,
            "BffTaskDefinitionArn",
            value=self.bff_task_definition.task_definition_arn,
            description="BFF task definition ARN",
            export_name="BffTaskDefinitionArn",
        )

        CfnOutput(
            self,
            "AgentTaskDefinitionArn",
            value=self.agent_task_definition.task_definition_arn,
            description="AgentCore task definition ARN",
            export_name="AgentTaskDefinitionArn",
        )

        if network_stack and hasattr(network_stack, "alb"):
            bff_target_group = elbv2.ApplicationTargetGroup(
                self,
                "BffTargetGroup",
                vpc=vpc,
                port=3000,
                protocol=elbv2.ApplicationProtocol.HTTP,
                target_type=elbv2.TargetType.IP,
                health_check=elbv2.HealthCheck(
                    path="/api/health",
                    interval=Duration.seconds(30),
                    healthy_threshold_count=2,
                    unhealthy_threshold_count=3,
                ),
            )
            self.bff_target_group = bff_target_group

            if hasattr(network_stack, "https_listener") and network_stack.https_listener:
                elbv2.ApplicationListenerRule(
                    self,
                    "BffListenerRule",
                    listener=network_stack.https_listener,
                    priority=10,
                    conditions=[
                        elbv2.ListenerCondition.path_patterns(["/api/*"])
                    ],
                    target_groups=[bff_target_group],
                )

        service_discovery_namespace = servicediscovery.PrivateDnsNamespace(
            self,
            "ServiceDiscoveryNamespace",
            name="bidopsai.local",
            vpc=vpc,
            description="Service discovery namespace for BidOpsAI services",
        )
        self.service_discovery_namespace = service_discovery_namespace

        if network_stack:
            private_app_subnets = vpc.select_subnets(
                subnet_group_name="PrivateApp"
            ).subnets
            private_agent_subnets = vpc.select_subnets(
                subnet_group_name="PrivateAgent"
            ).subnets
        else:
            private_app_subnets = vpc.select_subnets(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ).subnets
            private_agent_subnets = vpc.select_subnets(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ).subnets

        if network_stack and hasattr(network_stack, "alb"):
            bff_service = ecs.FargateService(
                self,
                "BffService",
                cluster=self.cluster,
                task_definition=self.bff_task_definition,
                desired_count=2,
                security_groups=[bff_security_group],
                vpc_subnets=ec2.SubnetSelection(subnets=private_app_subnets),
                min_healthy_percent=50,
                max_healthy_percent=200,
            )

            bff_service.attach_to_application_target_group(bff_target_group)

            network_stack.alb_security_group.add_egress_rule(
                peer=bff_security_group,
                connection=ec2.Port.tcp(3000),
                description="Allow ALB to BFF on port 3000",
            )

            bff_security_group.add_ingress_rule(
                peer=network_stack.alb_security_group,
                connection=ec2.Port.tcp(3000),
                description="Allow inbound from ALB on port 3000",
            )

            self.bff_service = bff_service

        agent_service = ecs.FargateService(
            self,
            "AgentService",
            cluster=self.cluster,
            task_definition=self.agent_task_definition,
            desired_count=2,
            security_groups=[agent_security_group],
            vpc_subnets=ec2.SubnetSelection(subnets=private_agent_subnets),
            min_healthy_percent=50,
            max_healthy_percent=200,
            cloud_map_options=ecs.CloudMapOptions(
                name="agentcore",
                cloud_map_namespace=service_discovery_namespace,
                dns_record_type=servicediscovery.DnsRecordType.A,
            ),
        )

        bff_security_group.add_egress_rule(
            peer=agent_security_group,
            connection=ec2.Port.tcp(8080),
            description="Allow BFF to AgentCore on port 8080",
        )

        agent_security_group.add_ingress_rule(
            peer=bff_security_group,
            connection=ec2.Port.tcp(8080),
            description="Allow inbound from BFF on port 8080",
        )

        self.agent_service = agent_service

        if network_stack and hasattr(network_stack, "alb"):
            bff_scaling = bff_service.auto_scale_task_count(
                min_capacity=2, max_capacity=10
            )

            bff_scaling.scale_on_cpu_utilization(
                "BffCpuScaling",
                target_utilization_percent=70,
                scale_in_cooldown=Duration.seconds(300),
                scale_out_cooldown=Duration.seconds(300),
            )

            bff_scaling.scale_on_memory_utilization(
                "BffMemoryScaling",
                target_utilization_percent=80,
                scale_in_cooldown=Duration.seconds(300),
                scale_out_cooldown=Duration.seconds(300),
            )

            CfnOutput(
                self,
                "BffServiceArn",
                value=bff_service.service_arn,
                export_name=f"{ENVIRONMENT}-BffServiceArn",
            )
        else:
            self.bff_service = None

        agent_scaling = agent_service.auto_scale_task_count(
            min_capacity=2, max_capacity=10
        )

        agent_scaling.scale_on_cpu_utilization(
            "AgentCpuScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.seconds(300),
            scale_out_cooldown=Duration.seconds(300),
        )

        agent_scaling.scale_on_memory_utilization(
            "AgentMemoryScaling",
            target_utilization_percent=80,
            scale_in_cooldown=Duration.seconds(300),
            scale_out_cooldown=Duration.seconds(300),
        )

        CfnOutput(
            self,
            "AgentServiceArn",
            value=agent_service.service_arn,
            export_name=f"{ENVIRONMENT}-AgentServiceArn",
        )

        CfnOutput(
            self,
            "ServiceDiscoveryNamespaceId",
            value=service_discovery_namespace.namespace_id,
            export_name=f"{ENVIRONMENT}-ServiceDiscoveryNamespaceId",
        )

        CfnOutput(
            self,
            "AgentCoreServiceDiscoveryDns",
            value=f"agentcore.{service_discovery_namespace.namespace_name}",
            export_name=f"{ENVIRONMENT}-AgentCoreServiceDiscoveryDns",
        )

        alarm_topic = sns.Topic(
            self, "AlarmTopic", display_name=f"{ENVIRONMENT}-ECS-Alarms"
        )

        if self.bff_service is not None:
            bff_cpu_alarm = cloudwatch.Alarm(
                self,
                "BffHighCpuAlarm",
                metric=self.bff_service.metric_cpu_utilization(),
                threshold=85,
                evaluation_periods=2,
                datapoints_to_alarm=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description="Alert when BFF service CPU exceeds 85%",
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            bff_cpu_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

            bff_memory_alarm = cloudwatch.Alarm(
                self,
                "BffHighMemoryAlarm",
                metric=self.bff_service.metric_memory_utilization(),
                threshold=85,
                evaluation_periods=2,
                datapoints_to_alarm=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description="Alert when BFF service memory exceeds 85%",
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            bff_memory_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

            bff_task_count_alarm = cloudwatch.Alarm(
                self,
                "BffLowTaskCountAlarm",
                metric=cloudwatch.Metric(
                    namespace="AWS/ECS",
                    metric_name="RunningTaskCount",
                    dimensions_map={
                        "ServiceName": self.bff_service.service_name,
                        "ClusterName": self.cluster.cluster_name,
                    },
                    statistic="Average",
                    period=Duration.minutes(5),
                ),
                threshold=1,
                evaluation_periods=2,
                datapoints_to_alarm=2,
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
                alarm_description="Alert when BFF service has less than 1 running task",
                treat_missing_data=cloudwatch.TreatMissingData.BREACHING,
            )
            bff_task_count_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        if self.agent_service is not None:
            agent_cpu_alarm = cloudwatch.Alarm(
                self,
                "AgentHighCpuAlarm",
                metric=self.agent_service.metric_cpu_utilization(),
                threshold=85,
                evaluation_periods=2,
                datapoints_to_alarm=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description="Alert when AgentCore service CPU exceeds 85%",
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            agent_cpu_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

            agent_memory_alarm = cloudwatch.Alarm(
                self,
                "AgentHighMemoryAlarm",
                metric=self.agent_service.metric_memory_utilization(),
                threshold=85,
                evaluation_periods=2,
                datapoints_to_alarm=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description="Alert when AgentCore service memory exceeds 85%",
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            agent_memory_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

            agent_task_count_alarm = cloudwatch.Alarm(
                self,
                "AgentLowTaskCountAlarm",
                metric=cloudwatch.Metric(
                    namespace="AWS/ECS",
                    metric_name="RunningTaskCount",
                    dimensions_map={
                        "ServiceName": self.agent_service.service_name,
                        "ClusterName": self.cluster.cluster_name,
                    },
                    statistic="Average",
                    period=Duration.minutes(5),
                ),
                threshold=2,
                evaluation_periods=2,
                datapoints_to_alarm=2,
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
                alarm_description="Alert when AgentCore service has less than 2 running tasks",
                treat_missing_data=cloudwatch.TreatMissingData.BREACHING,
            )
            agent_task_count_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        if network_stack and hasattr(network_stack, "alb"):
            alb_target_response_time_alarm = cloudwatch.Alarm(
                self,
                "AlbHighResponseTimeAlarm",
                metric=network_stack.alb.metric_target_response_time(),
                threshold=3,
                evaluation_periods=2,
                datapoints_to_alarm=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description="Alert when ALB target response time exceeds 3 seconds",
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            alb_target_response_time_alarm.add_alarm_action(
                cw_actions.SnsAction(alarm_topic)
            )

            alb_unhealthy_target_alarm = cloudwatch.Alarm(
                self,
                "AlbUnhealthyTargetAlarm",
                metric=cloudwatch.Metric(
                    namespace="AWS/ApplicationELB",
                    metric_name="UnHealthyHostCount",
                    dimensions_map={
                        "LoadBalancer": network_stack.alb.load_balancer_full_name,
                    },
                    statistic="Average",
                    period=Duration.minutes(5),
                ),
                threshold=1,
                evaluation_periods=2,
                datapoints_to_alarm=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
                alarm_description="Alert when ALB has unhealthy targets",
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            alb_unhealthy_target_alarm.add_alarm_action(
                cw_actions.SnsAction(alarm_topic)
            )

            alb_5xx_alarm = cloudwatch.Alarm(
                self,
                "AlbHigh5xxAlarm",
                metric=cloudwatch.Metric(
                    namespace="AWS/ApplicationELB",
                    metric_name="HTTPCode_Target_5XX_Count",
                    dimensions_map={
                        "LoadBalancer": network_stack.alb.load_balancer_full_name,
                    },
                    statistic="Sum",
                    period=Duration.minutes(5),
                ),
                threshold=10,
                evaluation_periods=2,
                datapoints_to_alarm=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description="Alert when ALB target 5XX error count exceeds 10 in 5 minutes",
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            alb_5xx_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

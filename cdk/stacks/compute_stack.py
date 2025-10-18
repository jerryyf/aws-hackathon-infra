from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    CfnOutput,
)
from constructs import Construct
from cdk.config import ECS_RESOURCE_ALLOCATIONS, ENVIRONMENT


class ComputeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        network_stack = kwargs.pop("network_stack", None)
        storage_stack = kwargs.pop("storage_stack", None)

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
                resources=["*"],
            )
        )

        bff_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter", "ssm:GetParameters"],
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
                resources=["*"],
            )
        )

        agent_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
                resources=["*"],
            )
        )

        agent_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter", "ssm:GetParameters"],
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
            port_mappings=[ecs.PortMapping(container_port=3000, protocol=ecs.Protocol.TCP)],
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
            port_mappings=[ecs.PortMapping(container_port=8080, protocol=ecs.Protocol.TCP)],
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

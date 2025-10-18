from aws_cdk import Stack, aws_ecs as ecs, aws_ec2 as ec2, aws_iam as iam, CfnOutput
from constructs import Construct


class ComputeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        network_stack = kwargs.pop("network_stack", None)

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

        self.cluster = ecs.Cluster(
            self, "EcsCluster", vpc=vpc, cluster_name="bidopsai-cluster"
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

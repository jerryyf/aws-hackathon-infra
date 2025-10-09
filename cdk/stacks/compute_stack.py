from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    CfnOutput,
)
from constructs import Construct


class ComputeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        # Get VPC from network stack
        network_stack = kwargs.pop('network_stack', None)

        super().__init__(scope, construct_id, **kwargs)
        if network_stack:
            vpc = network_stack.vpc
            app_subnets = [subnet for subnet in vpc.private_subnets if "PrivateApp" in subnet.node.id]
        else:
            # For testing
            vpc = ec2.Vpc(self, "TestVpc", cidr="10.0.0.0/16", max_azs=2)
            app_subnets = vpc.private_subnets

        # ECS Cluster
        self.cluster = ecs.Cluster(
            self, "EcsCluster",
            vpc=vpc,
            cluster_name="hackathon-cluster"
        )

        # Task Definition
        self.task_definition = ecs.FargateTaskDefinition(
            self, "TaskDefinition",
            cpu=256,
            memory_limit_mib=512
        )

        # Add a placeholder container
        self.task_definition.add_container(
            "AppContainer",
            image=ecs.ContainerImage.from_registry("nginx:latest"),
            memory_limit_mib=256,
            cpu=128,
            essential=True
        )

        # Outputs
        CfnOutput(
            self, "EcsClusterName",
            value=self.cluster.cluster_name,
            description="ECS cluster name",
            export_name="EcsClusterName"
        )
import aws_cdk as cdk
from aws_cdk.assertions import Template
from cdk.stacks.compute_stack import ComputeStack
from cdk.stacks.network_stack import NetworkStack


def test_compute_stack_ecs_cluster_created():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::ECS::Cluster", 1)
    template.has_resource_properties(
        "AWS::ECS::Cluster", {"ClusterName": "bidopsai-cluster"}
    )


def test_compute_stack_task_definition_created():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::ECS::TaskDefinition", 1)
    template.has_resource_properties(
        "AWS::ECS::TaskDefinition",
        {
            "Cpu": "256",
            "Memory": "512",
            "NetworkMode": "awsvpc",
            "RequiresCompatibilities": ["FARGATE"],
        },
    )


def test_compute_stack_task_has_container():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ECS::TaskDefinition",
        {
            "ContainerDefinitions": [
                {
                    "Name": "AppContainer",
                    "Image": "nginx:latest",
                    "Cpu": 128,
                    "Memory": 256,
                    "Essential": True,
                }
            ]
        },
    )


def test_compute_stack_outputs():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_output("EcsClusterName", {"Export": {"Name": "EcsClusterName"}})


def test_compute_stack_without_network_stack():
    app = cdk.App()
    stack = ComputeStack(app, "TestComputeStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::VPC", 1)
    template.resource_count_is("AWS::ECS::Cluster", 1)

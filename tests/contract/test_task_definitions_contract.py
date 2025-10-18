import boto3
import pytest


@pytest.fixture(scope="module")
def cloudformation():
    return boto3.client("cloudformation", region_name="us-east-1")


def test_bff_task_definition_arn_output(cloudformation):
    response = cloudformation.describe_stacks(StackName="ComputeStack")
    outputs = response["Stacks"][0]["Outputs"]

    bff_task_definition_arn = next(
        (
            output["OutputValue"]
            for output in outputs
            if output["OutputKey"] == "BffTaskDefinitionArn"
        ),
        None,
    )

    assert (
        bff_task_definition_arn is not None
    ), "BffTaskDefinitionArn output not found"
    assert bff_task_definition_arn.startswith(
        "arn:aws:ecs:us-east-1"
    ), "Invalid BFF task definition ARN format"
    assert "task-definition/TestComputeStack-BffTaskDefinition" in bff_task_definition_arn


def test_agent_task_definition_arn_output(cloudformation):
    response = cloudformation.describe_stacks(StackName="ComputeStack")
    outputs = response["Stacks"][0]["Outputs"]

    agent_task_definition_arn = next(
        (
            output["OutputValue"]
            for output in outputs
            if output["OutputKey"] == "AgentTaskDefinitionArn"
        ),
        None,
    )

    assert (
        agent_task_definition_arn is not None
    ), "AgentTaskDefinitionArn output not found"
    assert agent_task_definition_arn.startswith(
        "arn:aws:ecs:us-east-1"
    ), "Invalid AgentCore task definition ARN format"
    assert "task-definition/TestComputeStack-AgentTaskDefinition" in agent_task_definition_arn


def test_bff_task_role_arn(cloudformation):
    response = cloudformation.describe_stacks(StackName="ComputeStack")
    resources = cloudformation.describe_stack_resources(StackName="ComputeStack")

    bff_task_role_arn = next(
        (
            resource["PhysicalResourceId"]
            for resource in resources["StackResources"]
            if resource["LogicalResourceId"] == "BffTaskRole"
        ),
        None,
    )

    assert bff_task_role_arn is not None, "BFF task role not found in stack resources"
    assert bff_task_role_arn.startswith(
        "arn:aws:iam::"
    ), "Invalid BFF task role ARN format"


def test_agent_task_role_arn(cloudformation):
    response = cloudformation.describe_stacks(StackName="ComputeStack")
    resources = cloudformation.describe_stack_resources(StackName="ComputeStack")

    agent_task_role_arn = next(
        (
            resource["PhysicalResourceId"]
            for resource in resources["StackResources"]
            if resource["LogicalResourceId"] == "AgentTaskRole"
        ),
        None,
    )

    assert (
        agent_task_role_arn is not None
    ), "AgentCore task role not found in stack resources"
    assert agent_task_role_arn.startswith(
        "arn:aws:iam::"
    ), "Invalid AgentCore task role ARN format"

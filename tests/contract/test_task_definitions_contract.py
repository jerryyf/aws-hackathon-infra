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

    assert bff_task_definition_arn is not None, "BffTaskDefinitionArn output not found"
    assert bff_task_definition_arn.startswith(
        "arn:aws:ecs:us-east-1"
    ), "Invalid BFF task definition ARN format"
    assert (
        "task-definition/ComputeStack" in bff_task_definition_arn
        and "BffTaskDefinition" in bff_task_definition_arn
    ), f"Unexpected BFF task definition ARN format: {bff_task_definition_arn}"


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
    assert (
        "task-definition/ComputeStack" in agent_task_definition_arn
        and "AgentTaskDefinition" in agent_task_definition_arn
    ), f"Unexpected Agent task definition ARN format: {agent_task_definition_arn}"


def test_bff_task_role_arn(cloudformation):
    import boto3

    response = cloudformation.describe_stacks(StackName="ComputeStack")
    resources = cloudformation.describe_stack_resources(StackName="ComputeStack")

    bff_task_role_name = next(
        (
            resource["PhysicalResourceId"]
            for resource in resources["StackResources"]
            if resource["ResourceType"] == "AWS::IAM::Role"
            and "BffTaskRole" in resource["LogicalResourceId"]
        ),
        None,
    )

    assert (
        bff_task_role_name is not None
    ), "BFF task role not found in stack resources"

    iam_client = boto3.client("iam", region_name="us-east-1")
    bff_task_role = iam_client.get_role(RoleName=bff_task_role_name)
    bff_task_role_arn = bff_task_role["Role"]["Arn"]

    assert bff_task_role_arn.startswith(
        "arn:aws:iam::"
    ), "Invalid BFF task role ARN format"


def test_agent_task_role_arn(cloudformation):
    import boto3

    response = cloudformation.describe_stacks(StackName="ComputeStack")
    resources = cloudformation.describe_stack_resources(StackName="ComputeStack")

    agent_task_role_name = next(
        (
            resource["PhysicalResourceId"]
            for resource in resources["StackResources"]
            if resource["ResourceType"] == "AWS::IAM::Role"
            and "AgentTaskRole" in resource["LogicalResourceId"]
        ),
        None,
    )

    assert (
        agent_task_role_name is not None
    ), "AgentCore task role not found in stack resources"

    iam_client = boto3.client("iam", region_name="us-east-1")
    agent_task_role = iam_client.get_role(RoleName=agent_task_role_name)
    agent_task_role_arn = agent_task_role["Role"]["Arn"]

    assert agent_task_role_arn.startswith(
        "arn:aws:iam::"
    ), "Invalid AgentCore task role ARN format"

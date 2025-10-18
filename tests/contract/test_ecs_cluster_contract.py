import boto3
import pytest


@pytest.fixture(scope="module")
def cfn_client():
    return boto3.client("cloudformation", region_name="us-east-1")


@pytest.fixture(scope="module")
def compute_stack_outputs(cfn_client):
    response = cfn_client.describe_stacks(StackName="ComputeStack")
    outputs = {}
    for output in response["Stacks"][0]["Outputs"]:
        outputs[output["OutputKey"]] = output["OutputValue"]
    return outputs


def test_cluster_name_output_exists(compute_stack_outputs):
    assert "EcsClusterName" in compute_stack_outputs
    assert compute_stack_outputs["EcsClusterName"] == "bidopsai-cluster"


def test_cluster_arn_output_exists(compute_stack_outputs):
    assert "EcsClusterArn" in compute_stack_outputs
    assert "arn:aws:ecs:" in compute_stack_outputs["EcsClusterArn"]
    assert "cluster/bidopsai-cluster" in compute_stack_outputs["EcsClusterArn"]

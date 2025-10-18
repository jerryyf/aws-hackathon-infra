import json
import os
from pathlib import Path
from typing import Any

import boto3
import pytest
import yaml
from botocore.exceptions import ClientError


PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def contracts_dir() -> Path:
    return PROJECT_ROOT / "specs"


@pytest.fixture(scope="session")
def load_contract():
    def _load(contract_path: str) -> dict[str, Any]:
        path = PROJECT_ROOT / contract_path
        with open(path) as f:
            return yaml.safe_load(f)

    return _load





@pytest.fixture(scope="session")
def aws_region() -> str:
    return os.getenv("AWS_REGION", "us-east-1")


@pytest.fixture(scope="session")
def aws_profile() -> str:
    return os.getenv("AWS_PROFILE", "bidopsai")


@pytest.fixture
def cloudformation_client(aws_region: str):
    return boto3.client("cloudformation", region_name=aws_region)


@pytest.fixture
def ec2_client(aws_region: str):
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture
def iam_client(aws_region: str):
    return boto3.client("iam", region_name=aws_region)


@pytest.fixture
def opensearch_client(aws_region: str):
    return boto3.client("opensearch", region_name=aws_region)


@pytest.fixture
def rds_client(aws_region: str):
    return boto3.client("rds", region_name=aws_region)


@pytest.fixture
def s3_client(aws_region: str):
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture
def ecr_client(aws_region: str):
    return boto3.client("ecr", region_name=aws_region)


@pytest.fixture
def elbv2_client(aws_region: str):
    return boto3.client("elbv2", region_name=aws_region)


@pytest.fixture
def bedrock_agent_client(aws_region: str):
    return boto3.client("bedrock-agent", region_name=aws_region)


def get_stack_outputs(cloudformation_client, stack_name: str) -> dict[str, Any]:
    try:
        response = cloudformation_client.describe_stacks(StackName=stack_name)
        stacks = response.get("Stacks", [])
        if not stacks:
            pytest.skip(f"{stack_name} not deployed - no stacks found")

        outputs = stacks[0].get("Outputs", [])
        return {o["OutputKey"]: o["OutputValue"] for o in outputs}
    except ClientError as e:
        if e.response["Error"]["Code"] == "ValidationError":
            pytest.skip(f"{stack_name} not deployed - {e}")
        raise


@pytest.fixture
def network_stack_outputs(cloudformation_client):
    return get_stack_outputs(cloudformation_client, "NetworkStack")


@pytest.fixture
def stack_outputs(cloudformation_client):
    """Dynamic fixture to get outputs from any stack"""

    def _get_outputs(stack_name: str) -> dict[str, Any]:
        return get_stack_outputs(cloudformation_client, stack_name)

    return _get_outputs


@pytest.fixture
def security_stack_outputs(cloudformation_client):
    return get_stack_outputs(cloudformation_client, "SecurityStack")


@pytest.fixture
def storage_stack_outputs(cloudformation_client):
    return get_stack_outputs(cloudformation_client, "StorageStack")


@pytest.fixture
def database_stack_outputs(cloudformation_client):
    return get_stack_outputs(cloudformation_client, "DatabaseStack")


@pytest.fixture
def compute_stack_outputs(cloudformation_client):
    return get_stack_outputs(cloudformation_client, "ComputeStack")


@pytest.fixture
def monitoring_stack_outputs(cloudformation_client):
    return get_stack_outputs(cloudformation_client, "MonitoringStack")

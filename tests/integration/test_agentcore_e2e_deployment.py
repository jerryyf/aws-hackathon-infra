import os
import re
import time
from datetime import datetime, timedelta
import pytest
import boto3
from botocore.exceptions import ClientError


@pytest.fixture
def cloudformation_client():
    return boto3.client(
        "cloudformation", region_name=os.getenv("AWS_REGION", "us-east-1")
    )


@pytest.fixture
def iam_client():
    return boto3.client("iam", region_name=os.getenv("AWS_REGION", "us-east-1"))


@pytest.fixture
def ec2_client():
    return boto3.client("ec2", region_name=os.getenv("AWS_REGION", "us-east-1"))


@pytest.fixture
def stack_outputs(cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
        outputs = {
            o["OutputKey"]: o["OutputValue"] for o in response["Stacks"][0]["Outputs"]
        }
        return outputs
    except ClientError:
        pytest.skip("AgentCoreStack not deployed - skipping E2E tests")


def test_agentcore_stack_deployed(cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
        assert len(response["Stacks"]) == 1
        assert response["Stacks"][0]["StackStatus"] in [
            "CREATE_COMPLETE",
            "UPDATE_COMPLETE",
        ]
    except ClientError:
        pytest.skip("AgentCoreStack not deployed")


def test_all_required_outputs_exist(stack_outputs):
    required_outputs = [
        "AgentRuntimeArn",
        "AgentRuntimeId",
        "AgentRuntimeEndpointUrl",
        "AgentRuntimeStatus",
        "AgentRuntimeVersion",
        "ExecutionRoleArn",
        "NetworkMode",
    ]

    for output_key in required_outputs:
        assert output_key in stack_outputs, f"Required output {output_key} missing"
        assert stack_outputs[output_key], f"Output {output_key} is empty"


def test_agent_runtime_arn_format(stack_outputs):
    runtime_arn = stack_outputs["AgentRuntimeArn"]
    pattern = r"^arn:aws:bedrock-agentcore:[a-z0-9-]+:[0-9]{12}:runtime/[a-zA-Z0-9-]+$"
    assert re.match(
        pattern, runtime_arn
    ), f"AgentRuntimeArn format invalid: {runtime_arn}"


def test_agent_runtime_id_format(stack_outputs):
    runtime_id = stack_outputs["AgentRuntimeId"]
    pattern = r"^[a-zA-Z0-9-]+$"
    assert re.match(pattern, runtime_id), f"AgentRuntimeId format invalid: {runtime_id}"


def test_agent_runtime_endpoint_https(stack_outputs):
    endpoint_url = stack_outputs["AgentRuntimeEndpointUrl"]
    pattern = r"^https://[a-zA-Z0-9-]+\.runtime\.bedrock-agentcore\.[a-z0-9-]+\.amazonaws\.com$"
    assert re.match(
        pattern, endpoint_url
    ), f"EndpointUrl format invalid: {endpoint_url}"
    assert endpoint_url.startswith("https://"), "Endpoint must use HTTPS"


def test_agent_runtime_status_active(stack_outputs):
    status = stack_outputs["AgentRuntimeStatus"]
    valid_statuses = ["CREATING", "ACTIVE", "UPDATING", "DELETING", "FAILED"]
    assert status in valid_statuses, f"Invalid status: {status}"

    if status != "ACTIVE":
        pytest.skip(f"Runtime status is {status}, expected ACTIVE for full validation")


def test_execution_role_arn_format(stack_outputs):
    role_arn = stack_outputs["ExecutionRoleArn"]
    pattern = r"^arn:aws:iam::[0-9]{12}:role/[a-zA-Z0-9-_+=,.@]+$"
    assert re.match(pattern, role_arn), f"ExecutionRoleArn format invalid: {role_arn}"


def test_execution_role_exists(stack_outputs, iam_client):
    role_arn = stack_outputs["ExecutionRoleArn"]
    role_name = role_arn.split("/")[-1]

    try:
        response = iam_client.get_role(RoleName=role_name)
        assert response["Role"]["Arn"] == role_arn
    except ClientError as e:
        pytest.fail(f"Execution role not found: {e}")


def test_execution_role_trust_policy(stack_outputs, iam_client):
    role_arn = stack_outputs["ExecutionRoleArn"]
    role_name = role_arn.split("/")[-1]

    try:
        response = iam_client.get_role(RoleName=role_name)
        trust_policy = response["Role"]["AssumeRolePolicyDocument"]

        principals = []
        for statement in trust_policy.get("Statement", []):
            if statement.get("Effect") == "Allow":
                principal = statement.get("Principal", {})
                if "Service" in principal:
                    if isinstance(principal["Service"], list):
                        principals.extend(principal["Service"])
                    else:
                        principals.append(principal["Service"])

        assert (
            "bedrock-agentcore.amazonaws.com" in principals
        ), "Execution role must trust bedrock-agentcore.amazonaws.com"
    except ClientError as e:
        pytest.fail(f"Failed to retrieve role trust policy: {e}")


def test_execution_role_has_bedrock_policy(stack_outputs, iam_client):
    role_arn = stack_outputs["ExecutionRoleArn"]
    role_name = role_arn.split("/")[-1]

    try:
        response = iam_client.list_attached_role_policies(RoleName=role_name)
        policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]

        has_bedrock_permission = any("bedrock" in arn.lower() for arn in policy_arns)

        inline_policies = iam_client.list_role_policies(RoleName=role_name)

        assert (
            has_bedrock_permission or len(inline_policies["PolicyNames"]) > 0
        ), "Execution role must have Bedrock permissions"
    except ClientError as e:
        pytest.fail(f"Failed to retrieve role policies: {e}")


def test_network_mode_valid(stack_outputs):
    network_mode = stack_outputs["NetworkMode"]
    valid_modes = ["PUBLIC", "VPC"]
    assert network_mode in valid_modes, f"Invalid network mode: {network_mode}"


def test_vpc_mode_configuration(stack_outputs, cloudformation_client):
    network_mode = stack_outputs["NetworkMode"]

    if network_mode != "VPC":
        pytest.skip("Test only applicable for VPC network mode")

    try:
        response = cloudformation_client.describe_stack_resources(
            StackName="AgentCoreStack"
        )

        runtime_resource = None
        for resource in response["StackResources"]:
            if resource["ResourceType"] == "AWS::BedrockAgentCore::Runtime":
                runtime_resource = resource
                break

        assert runtime_resource is not None, "Runtime resource not found in stack"
    except ClientError as e:
        pytest.fail(f"Failed to retrieve stack resources: {e}")


def test_vpc_endpoints_accessible(stack_outputs, ec2_client):
    network_mode = stack_outputs["NetworkMode"]

    if network_mode != "VPC":
        pytest.skip("VPC endpoint test only applicable for VPC network mode")

    try:
        network_response = boto3.client("cloudformation").describe_stacks(
            StackName="NetworkStack"
        )
        network_outputs = {
            o["OutputKey"]: o["OutputValue"]
            for o in network_response["Stacks"][0]["Outputs"]
        }

        vpc_id = network_outputs.get("VpcId")
        if not vpc_id:
            pytest.skip("VPC not found in NetworkStack outputs")

        response = ec2_client.describe_vpc_endpoints(
            Filters=[
                {"Name": "vpc-id", "Values": [vpc_id]},
                {
                    "Name": "service-name",
                    "Values": [
                        f"com.amazonaws.{os.getenv('AWS_REGION', 'us-east-1')}.bedrock-runtime"
                    ],
                },
            ]
        )

        assert len(response["VpcEndpoints"]) > 0, "Bedrock VPC endpoint not found"

        for endpoint in response["VpcEndpoints"]:
            assert (
                endpoint["State"] == "available"
            ), f"VPC endpoint {endpoint['VpcEndpointId']} not in available state"
    except ClientError:
        pytest.skip("NetworkStack not deployed or VPC endpoint not found")


def test_resource_tagging(stack_outputs, cloudformation_client):
    try:
        response = cloudformation_client.describe_stack_resources(
            StackName="AgentCoreStack"
        )

        runtime_resource = None
        for resource in response["StackResources"]:
            if resource["ResourceType"] == "AWS::BedrockAgentCore::Runtime":
                runtime_resource = resource
                break

        if not runtime_resource:
            pytest.skip("Runtime resource not found")

        required_tags = {
            "Project": "aws-hackathon",
            "Owner": "platform-team",
            "CostCenter": "engineering",
            "ManagedBy": "cdk",
            "Stack": "agentcore-stack",
        }

        tags_response = cloudformation_client.describe_stacks(
            StackName="AgentCoreStack"
        )
        stack_tags = {
            tag["Key"]: tag["Value"]
            for tag in tags_response["Stacks"][0].get("Tags", [])
        }

        for key, value in required_tags.items():
            if key in stack_tags:
                assert stack_tags[key] == value, f"Tag {key} has incorrect value"
    except ClientError as e:
        pytest.skip(f"Unable to verify resource tags: {e}")


def test_runtime_version_exists(stack_outputs):
    runtime_version = stack_outputs["AgentRuntimeVersion"]
    assert runtime_version, "Runtime version must be set"
    assert len(runtime_version) > 0, "Runtime version cannot be empty"


def test_stack_exports_configured(cloudformation_client, stack_outputs):
    environment = os.getenv("ENVIRONMENT", "test")

    try:
        exports = cloudformation_client.list_exports()
        export_names = {e["Name"]: e["Value"] for e in exports["Exports"]}

        expected_exports = [
            f"{environment}-AgentRuntimeArn",
            "AgentRuntimeId",
            "AgentRuntimeEndpointUrl",
            "AgentRuntimeStatus",
            "AgentRuntimeVersion",
            f"{environment}-AgentExecutionRoleArn",
            "AgentRuntimeNetworkMode",
        ]

        for export_name in expected_exports:
            assert export_name in export_names, f"Export {export_name} not found"
    except ClientError as e:
        pytest.skip(f"Unable to verify stack exports: {e}")


def test_dependency_stacks_deployed(cloudformation_client):
    required_stacks = ["NetworkStack", "SecurityStack", "StorageStack"]

    for stack_name in required_stacks:
        try:
            response = cloudformation_client.describe_stacks(StackName=stack_name)
            assert len(response["Stacks"]) == 1
            assert response["Stacks"][0]["StackStatus"] in [
                "CREATE_COMPLETE",
                "UPDATE_COMPLETE",
            ], f"Stack {stack_name} not in valid state"
        except ClientError:
            pytest.skip(f"Dependency stack {stack_name} not deployed")


def test_e2e_deployment_complete(stack_outputs):
    runtime_status = stack_outputs["AgentRuntimeStatus"]
    runtime_arn = stack_outputs["AgentRuntimeArn"]
    runtime_id = stack_outputs["AgentRuntimeId"]
    endpoint_url = stack_outputs["AgentRuntimeEndpointUrl"]
    execution_role = stack_outputs["ExecutionRoleArn"]

    assert (
        runtime_status == "ACTIVE"
    ), f"E2E deployment incomplete: runtime status is {runtime_status}"
    assert runtime_arn.startswith("arn:aws:bedrock-agentcore:"), "Invalid runtime ARN"
    assert len(runtime_id) > 0, "Runtime ID is empty"
    assert endpoint_url.startswith("https://"), "Endpoint URL must be HTTPS"
    assert execution_role.startswith("arn:aws:iam::"), "Invalid execution role ARN"


def test_runtime_deployment_timeout(cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName="AgentCoreStack")
        stack = response["Stacks"][0]

        creation_time = stack.get("CreationTime") or stack.get("LastUpdatedTime")
        if not creation_time:
            pytest.skip("Unable to determine stack deployment time")

        current_time = datetime.now(creation_time.tzinfo)
        deployment_duration = current_time - creation_time

        timeout_limit = timedelta(minutes=10)

        assert (
            deployment_duration <= timeout_limit
        ), f"Runtime deployment exceeded 10 minute timeout: {deployment_duration.total_seconds() / 60:.2f} minutes"

        events_response = cloudformation_client.describe_stack_events(
            StackName="AgentCoreStack"
        )

        runtime_events = [
            e
            for e in events_response["StackEvents"]
            if e.get("ResourceType") == "AWS::BedrockAgentCore::Runtime"
        ]

        if runtime_events:
            create_events = [
                e
                for e in runtime_events
                if e.get("ResourceStatus") in ["CREATE_IN_PROGRESS", "CREATE_COMPLETE"]
            ]

            if len(create_events) >= 2:
                start_event = next(
                    (
                        e
                        for e in create_events
                        if e["ResourceStatus"] == "CREATE_IN_PROGRESS"
                    ),
                    None,
                )
                complete_event = next(
                    (
                        e
                        for e in create_events
                        if e["ResourceStatus"] == "CREATE_COMPLETE"
                    ),
                    None,
                )

                if start_event and complete_event:
                    runtime_creation_duration = (
                        complete_event["Timestamp"] - start_event["Timestamp"]
                    )
                    assert (
                        runtime_creation_duration <= timeout_limit
                    ), f"Runtime resource creation exceeded 10 minute timeout: {runtime_creation_duration.total_seconds() / 60:.2f} minutes"

    except ClientError:
        pytest.skip("AgentCoreStack not deployed - skipping timeout validation")

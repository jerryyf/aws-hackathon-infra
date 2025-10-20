import boto3
import pytest


@pytest.fixture(scope="module")
def cfn_client():
    return boto3.client("cloudformation", region_name="us-east-1")


@pytest.fixture(scope="module")
def ecs_client():
    return boto3.client("ecs", region_name="us-east-1")


@pytest.fixture(scope="module")
def elbv2_client():
    return boto3.client("elbv2", region_name="us-east-1")


@pytest.fixture(scope="module")
def compute_stack_outputs(cfn_client):
    stack_name = "ComputeStack"
    response = cfn_client.describe_stacks(StackName=stack_name)
    outputs = {}
    for output in response["Stacks"][0]["Outputs"]:
        outputs[output["OutputKey"]] = output["OutputValue"]
    return outputs


def test_agent_service_arn_output_exists(compute_stack_outputs):
    assert (
        "AgentServiceArn" in compute_stack_outputs
    ), "AgentServiceArn output not found"
    agent_service_arn = compute_stack_outputs["AgentServiceArn"]
    assert agent_service_arn.startswith(
        "arn:aws:ecs:us-east-1:"
    ), f"Invalid AgentService ARN format: {agent_service_arn}"


def test_bff_service_arn_output_exists(compute_stack_outputs):
    assert "BffServiceArn" in compute_stack_outputs, "BffServiceArn output not found"
    bff_service_arn = compute_stack_outputs["BffServiceArn"]
    assert bff_service_arn.startswith(
        "arn:aws:ecs:us-east-1:"
    ), f"Invalid BffService ARN format: {bff_service_arn}"


def test_service_discovery_namespace_id_output_exists(compute_stack_outputs):
    assert (
        "ServiceDiscoveryNamespaceId" in compute_stack_outputs
    ), "ServiceDiscoveryNamespaceId output not found"
    namespace_id = compute_stack_outputs["ServiceDiscoveryNamespaceId"]
    assert namespace_id.startswith(
        "ns-"
    ), f"Invalid Service Discovery namespace ID format: {namespace_id}"


def test_agent_core_service_discovery_dns_output_exists(compute_stack_outputs):
    assert (
        "AgentCoreServiceDiscoveryDns" in compute_stack_outputs
    ), "AgentCoreServiceDiscoveryDns output not found"
    dns_name = compute_stack_outputs["AgentCoreServiceDiscoveryDns"]
    assert (
        dns_name == "agentcore.bidopsai.local"
    ), f"Expected agentcore.bidopsai.local but got {dns_name}"


def test_agent_service_running(compute_stack_outputs, ecs_client):
    agent_service_arn = compute_stack_outputs["AgentServiceArn"]
    cluster_arn = compute_stack_outputs["EcsClusterArn"]

    response = ecs_client.describe_services(
        cluster=cluster_arn, services=[agent_service_arn]
    )

    assert len(response["services"]) == 1, "AgentService not found in ECS cluster"
    service = response["services"][0]

    assert (
        service["status"] == "ACTIVE"
    ), f"AgentService status is not ACTIVE: {service['status']}"
    assert (
        service["desiredCount"] == 2
    ), f"AgentService desired count is not 2: {service['desiredCount']}"


def test_bff_service_running(compute_stack_outputs, ecs_client):
    bff_service_arn = compute_stack_outputs["BffServiceArn"]
    cluster_arn = compute_stack_outputs["EcsClusterArn"]

    response = ecs_client.describe_services(
        cluster=cluster_arn, services=[bff_service_arn]
    )

    assert len(response["services"]) == 1, "BffService not found in ECS cluster"
    service = response["services"][0]

    assert (
        service["status"] == "ACTIVE"
    ), f"BffService status is not ACTIVE: {service['status']}"
    assert (
        service["desiredCount"] == 2
    ), f"BffService desired count is not 2: {service['desiredCount']}"


def test_bff_service_target_group_health(compute_stack_outputs, elbv2_client):
    bff_service_arn = compute_stack_outputs["BffServiceArn"]

    target_groups = elbv2_client.describe_target_groups()
    bff_target_group_arn = None
    for tg in target_groups["TargetGroups"]:
        if "Bff" in tg["TargetGroupName"]:
            bff_target_group_arn = tg["TargetGroupArn"]
            break

    assert (
        bff_target_group_arn is not None
    ), "BFF target group not found in load balancer"

    health = elbv2_client.describe_target_health(TargetGroupArn=bff_target_group_arn)

    target_health_states = [
        t["TargetHealth"]["State"] for t in health["TargetHealthDescriptions"]
    ]
    healthy_count = target_health_states.count("healthy")

    assert (
        healthy_count >= 1
    ), f"No healthy targets in BFF target group (states: {target_health_states})"


def test_agent_service_has_service_discovery(compute_stack_outputs, ecs_client):
    agent_service_arn = compute_stack_outputs["AgentServiceArn"]
    cluster_arn = compute_stack_outputs["EcsClusterArn"]

    response = ecs_client.describe_services(
        cluster=cluster_arn, services=[agent_service_arn]
    )

    service = response["services"][0]
    service_registries = service.get("serviceRegistries", [])

    assert (
        len(service_registries) > 0
    ), "AgentService does not have Service Discovery configuration"
    assert service_registries[0][
        "registryArn"
    ], "AgentService Service Discovery registry ARN is empty"


def test_bff_service_has_load_balancer_attachment(compute_stack_outputs, ecs_client):
    bff_service_arn = compute_stack_outputs["BffServiceArn"]
    cluster_arn = compute_stack_outputs["EcsClusterArn"]

    response = ecs_client.describe_services(
        cluster=cluster_arn, services=[bff_service_arn]
    )

    service = response["services"][0]
    load_balancers = service.get("loadBalancers", [])

    assert len(load_balancers) > 0, "BffService does not have load balancer attachment"
    assert load_balancers[0]["targetGroupArn"], "BffService target group ARN is empty"

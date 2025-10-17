import re


def test_private_app_subnets_contract(network_stack_outputs):
    assert (
        "PrivateAppSubnetIds" in network_stack_outputs
    ), "PrivateAppSubnetIds output not found in NetworkStack"

    subnet_ids = network_stack_outputs["PrivateAppSubnetIds"].split(",")

    assert (
        len(subnet_ids) == 2
    ), f"Expected 2 private app subnet IDs, got {len(subnet_ids)}"

    subnet_pattern = re.compile(r"^subnet-[a-f0-9]{17}$")
    for subnet_id in subnet_ids:
        assert subnet_pattern.match(
            subnet_id
        ), f"Subnet ID {subnet_id} does not match pattern subnet-[a-f0-9]{{17}}"


def test_private_app_subnets_properties(network_stack_outputs, ec2_client):
    subnet_ids = network_stack_outputs["PrivateAppSubnetIds"].split(",")

    response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
    assert (
        len(response["Subnets"]) == 2
    ), f"Expected 2 private app subnets, found {len(response['Subnets'])}"

    for subnet in response["Subnets"]:
        assert (
            subnet["MapPublicIpOnLaunch"] is False
        ), f"Private app subnet {subnet['SubnetId']} must have MapPublicIpOnLaunch disabled"

        cidr = subnet["CidrBlock"]
        assert cidr.startswith("10.0.") and cidr.endswith(
            "/24"
        ), f"Private app subnet CIDR {cidr} must be in 10.0.x.0/24 range"

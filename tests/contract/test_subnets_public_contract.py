import re


def test_public_subnets_contract(network_stack_outputs):
    assert (
        "PublicSubnetIds" in network_stack_outputs
    ), "PublicSubnetIds output not found in NetworkStack"

    subnet_ids = network_stack_outputs["PublicSubnetIds"].split(",")

    assert len(subnet_ids) == 2, f"Expected 2 public subnet IDs, got {len(subnet_ids)}"

    subnet_pattern = re.compile(r"^subnet-[a-f0-9]{17}$")
    for subnet_id in subnet_ids:
        assert subnet_pattern.match(
            subnet_id
        ), f"Subnet ID {subnet_id} does not match pattern subnet-[a-f0-9]{{17}}"


def test_public_subnets_properties(network_stack_outputs, ec2_client):
    subnet_ids = network_stack_outputs["PublicSubnetIds"].split(",")

    response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
    assert (
        len(response["Subnets"]) == 2
    ), f"Expected 2 public subnets, found {len(response['Subnets'])}"

    for subnet in response["Subnets"]:
        assert (
            subnet["MapPublicIpOnLaunch"] is True
        ), f"Public subnet {subnet['SubnetId']} must have MapPublicIpOnLaunch enabled"

        cidr = subnet["CidrBlock"]
        assert cidr.startswith("10.0.") and cidr.endswith(
            "/24"
        ), f"Public subnet CIDR {cidr} must be in 10.0.x.0/24 range"

import re


def test_private_data_subnets_contract(network_stack_outputs):
    """Test that private data subnets stack output matches contract specification"""

    assert (
        "PrivateDataSubnetIds" in network_stack_outputs
    ), "PrivateDataSubnetIds output not found in NetworkStack"

    subnet_ids = network_stack_outputs["PrivateDataSubnetIds"].split(",")
    assert (
        len(subnet_ids) == 2
    ), f"Expected 2 private data subnet IDs, got {len(subnet_ids)}"

    subnet_pattern = re.compile(r"^subnet-[a-f0-9]{17}$")
    for subnet_id in subnet_ids:
        assert subnet_pattern.match(
            subnet_id
        ), f"Subnet ID {subnet_id} does not match pattern subnet-[a-f0-9]{{17}}"


def test_private_data_subnets_properties(network_stack_outputs, ec2_client):
    """Test private data subnet properties"""

    subnet_ids = network_stack_outputs["PrivateDataSubnetIds"].split(",")

    response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
    assert (
        len(response["Subnets"]) == 2
    ), f"Expected 2 private data subnets, found {len(response['Subnets'])}"

    for subnet in response["Subnets"]:
        assert (
            subnet["MapPublicIpOnLaunch"] is False
        ), f"Private data subnet {subnet['SubnetId']} must have MapPublicIpOnLaunch disabled"

        # Validate CIDR blocks are /24 subnets in 10.0.x.0 range
        cidr = subnet["CidrBlock"]
        assert cidr.startswith("10.0.") and cidr.endswith(
            "/24"
        ), f"Private data subnet CIDR {cidr} must be in 10.0.x.0/24 range"

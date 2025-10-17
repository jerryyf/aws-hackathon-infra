import re


def test_vpc_deployment_readiness(network_stack_outputs, ec2_client):
    assert "VpcId" in network_stack_outputs, "VpcId output not found in NetworkStack"
    vpc_id = network_stack_outputs["VpcId"]

    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    assert len(response["Vpcs"]) == 1, f"VPC {vpc_id} not found in AWS"

    vpc = response["Vpcs"][0]

    assert (
        vpc["CidrBlock"] == "10.0.0.0/16"
    ), f"VPC CIDR must be 10.0.0.0/16, got {vpc['CidrBlock']}"

    dns_hostnames_attr = ec2_client.describe_vpc_attribute(
        VpcId=vpc_id, Attribute="enableDnsHostnames"
    )
    assert (
        dns_hostnames_attr["EnableDnsHostnames"]["Value"] is True
    ), "VPC must have DNS hostnames enabled"

    dns_support_attr = ec2_client.describe_vpc_attribute(
        VpcId=vpc_id, Attribute="enableDnsSupport"
    )
    assert (
        dns_support_attr["EnableDnsSupport"]["Value"] is True
    ), "VPC must have DNS support enabled"

    subnets_response = ec2_client.describe_subnets(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    )
    assert (
        len(subnets_response["Subnets"]) == 8
    ), f"Expected 8 subnets, found {len(subnets_response['Subnets'])}"

    igw_response = ec2_client.describe_internet_gateways(
        Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
    )
    assert len(igw_response["InternetGateways"]) == 1, "Expected 1 internet gateway"

    nat_response = ec2_client.describe_nat_gateways(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    )
    active_nats = [
        nat
        for nat in nat_response["NatGateways"]
        if nat["State"] in ["available", "pending"]
    ]
    assert len(active_nats) == 2, f"Expected 2 NAT gateways, found {len(active_nats)}"


def test_vpc_deployment_outputs(network_stack_outputs):
    required_outputs = [
        "VpcId",
        "PublicSubnetIds",
        "PrivateAppSubnetIds",
        "PrivateAgentSubnetIds",
        "PrivateDataSubnetIds",
        "AlbDnsName",
    ]

    for output_name in required_outputs:
        assert (
            output_name in network_stack_outputs
        ), f"Required output {output_name} missing from NetworkStack"

    subnet_outputs = [
        "PublicSubnetIds",
        "PrivateAppSubnetIds",
        "PrivateAgentSubnetIds",
        "PrivateDataSubnetIds",
    ]
    subnet_pattern = re.compile(r"^subnet-[a-f0-9]{17}$")

    for subnet_output in subnet_outputs:
        subnet_ids = network_stack_outputs[subnet_output].split(",")
        assert (
            len(subnet_ids) == 2
        ), f"{subnet_output} must contain exactly 2 subnet IDs, got {len(subnet_ids)}"

        for subnet_id in subnet_ids:
            assert subnet_pattern.match(
                subnet_id
            ), f"Subnet ID {subnet_id} does not match pattern subnet-[a-f0-9]{{17}}"

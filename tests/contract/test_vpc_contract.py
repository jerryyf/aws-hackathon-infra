import re


def test_vpc_contract(network_stack_outputs):
    assert "VpcId" in network_stack_outputs, "VpcId output not found in NetworkStack"

    vpc_id = network_stack_outputs["VpcId"]

    vpc_pattern = re.compile(r"^vpc-[a-f0-9]{17}$")
    assert vpc_pattern.match(
        vpc_id
    ), f"VpcId {vpc_id} does not match pattern vpc-[a-f0-9]{{17}}"


def test_vpc_properties(network_stack_outputs, ec2_client):
    assert "VpcId" in network_stack_outputs, "VpcId output missing from NetworkStack"

    vpc_id = network_stack_outputs["VpcId"]
    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    vpc = response["Vpcs"][0]

    assert (
        vpc["CidrBlock"] == "10.0.0.0/16"
    ), f"VpcCidr must be 10.0.0.0/16, got {vpc['CidrBlock']}"

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

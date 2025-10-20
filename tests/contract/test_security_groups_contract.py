import boto3
import pytest


@pytest.fixture(scope="module")
def ec2():
    return boto3.client("ec2", region_name="us-east-1")


@pytest.fixture(scope="module")
def cloudformation():
    return boto3.client("cloudformation", region_name="us-east-1")


def get_security_group_id(cloudformation, logical_resource_id):
    resources = cloudformation.describe_stack_resources(StackName="ComputeStack")
    sg_id = next(
        (
            resource["PhysicalResourceId"]
            for resource in resources["StackResources"]
            if resource["LogicalResourceId"] == logical_resource_id
        ),
        None,
    )
    return sg_id


def test_bff_security_group_allows_inbound_from_alb_only(ec2, cloudformation):
    resources = cloudformation.describe_stack_resources(StackName="ComputeStack")
    bff_sg_id = next(
        (
            resource["PhysicalResourceId"]
            for resource in resources["StackResources"]
            if resource["ResourceType"] == "AWS::EC2::SecurityGroup"
            and "Bff" in resource["LogicalResourceId"]
        ),
        None,
    )
    assert bff_sg_id is not None, "BFF security group not found"

    response = ec2.describe_security_groups(GroupIds=[bff_sg_id])
    sg = response["SecurityGroups"][0]

    ingress_rules = sg.get("IpPermissions", [])

    for rule in ingress_rules:
        assert "0.0.0.0/0" not in [
            cidr.get("CidrIp") for cidr in rule.get("IpRanges", [])
        ], "BFF security group allows inbound from 0.0.0.0/0"

        if rule.get("FromPort") == 3000:
            assert (
                len(rule.get("UserIdGroupPairs", [])) > 0
            ), "BFF security group port 3000 should only allow inbound from other security groups"


def test_agent_security_group_allows_inbound_from_bff_only(ec2, cloudformation):
    resources = cloudformation.describe_stack_resources(StackName="ComputeStack")
    agent_sg_id = next(
        (
            resource["PhysicalResourceId"]
            for resource in resources["StackResources"]
            if resource["ResourceType"] == "AWS::EC2::SecurityGroup"
            and "Agent" in resource["LogicalResourceId"]
        ),
        None,
    )
    assert agent_sg_id is not None, "AgentCore security group not found"

    bff_sg_id = next(
        (
            resource["PhysicalResourceId"]
            for resource in resources["StackResources"]
            if resource["ResourceType"] == "AWS::EC2::SecurityGroup"
            and "Bff" in resource["LogicalResourceId"]
        ),
        None,
    )
    assert bff_sg_id is not None, "BFF security group not found"

    response = ec2.describe_security_groups(GroupIds=[agent_sg_id])
    sg = response["SecurityGroups"][0]

    ingress_rules = sg.get("IpPermissions", [])

    for rule in ingress_rules:
        assert "0.0.0.0/0" not in [
            cidr.get("CidrIp") for cidr in rule.get("IpRanges", [])
        ], "AgentCore security group allows inbound from 0.0.0.0/0"

        if rule.get("FromPort") == 8080:
            source_groups = [
                pair["GroupId"] for pair in rule.get("UserIdGroupPairs", [])
            ]
            assert (
                bff_sg_id in source_groups
            ), f"AgentCore security group port 8080 should allow inbound from BFF security group {bff_sg_id}"


def test_no_security_group_allows_unrestricted_inbound_access(ec2, cloudformation):
    resources = cloudformation.describe_stack_resources(StackName="ComputeStack")

    security_group_ids = [
        resource["PhysicalResourceId"]
        for resource in resources["StackResources"]
        if resource["ResourceType"] == "AWS::EC2::SecurityGroup"
    ]

    for sg_id in security_group_ids:
        response = ec2.describe_security_groups(GroupIds=[sg_id])
        sg = response["SecurityGroups"][0]

        ingress_rules = sg.get("IpPermissions", [])

        for rule in ingress_rules:
            cidr_blocks = [cidr.get("CidrIp") for cidr in rule.get("IpRanges", [])]
            assert (
                "0.0.0.0/0" not in cidr_blocks
            ), f"Security group {sg_id} ({sg['GroupName']}) allows unrestricted inbound access from 0.0.0.0/0"

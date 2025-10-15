import re


def test_vpc_endpoint_contract(network_stack_outputs):
    """Test that VPC stack output matches contract specification"""
    
    # Verify VpcId output exists
    assert "VpcId" in network_stack_outputs, "VpcId output not found in NetworkStack"
    
    vpc_id = network_stack_outputs["VpcId"]
    
    # Validate VpcId matches pattern vpc-[a-f0-9]{17}
    vpc_pattern = re.compile(r"^vpc-[a-f0-9]{17}$")
    assert vpc_pattern.match(vpc_id), f"VpcId {vpc_id} does not match pattern vpc-[a-f0-9]{{17}}"


def test_vpc_output_schema(network_stack_outputs, ec2_client):
    """Test VPC output matches contract schema"""
    
    # Validate VpcId output exists
    assert "VpcId" in network_stack_outputs, "VpcId output missing from NetworkStack"
    
    vpc_id = network_stack_outputs["VpcId"]
    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    vpc = response["Vpcs"][0]
    
    # Validate CIDR is 10.0.0.0/16 per contract
    assert vpc["CidrBlock"] == "10.0.0.0/16", f"VpcCidr must be 10.0.0.0/16, got {vpc['CidrBlock']}"

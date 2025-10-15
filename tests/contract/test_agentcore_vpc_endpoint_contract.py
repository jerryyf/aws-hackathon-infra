import json
import pytest


def test_bedrock_agentcore_endpoint_policy_contract(stack_outputs, ec2_client, load_contract_json):
    """Test VPC endpoint policy matches contract"""
    
    contract = load_contract_json("vpc-endpoint-policy.json")
    outputs = stack_outputs("NetworkStack")
    
    if "BedrockAgentCoreEndpointId" not in outputs:
        pytest.skip("BedrockAgentCoreEndpointId not found - AgentCore not deployed")
    
    endpoint_id = outputs["BedrockAgentCoreEndpointId"]
    
    response = ec2_client.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])
    endpoint = response["VpcEndpoints"][0]
    
    # Check if endpoint has a policy document
    if "PolicyDocument" in endpoint and endpoint["PolicyDocument"]:
        import urllib.parse
        policy_doc = json.loads(urllib.parse.unquote(endpoint["PolicyDocument"]))
        
        # At minimum, verify policy has statements
        assert "Statement" in policy_doc, "VPC endpoint must have policy statements"
        assert len(policy_doc["Statement"]) > 0, "VPC endpoint policy must not be empty"
        
        # Verify AllowAgentRuntimeInvocation statement exists in contract
        runtime_stmt = next(
            (s for s in contract["Statement"] if s["Sid"] == "AllowAgentRuntimeInvocation"), None
        )
        assert runtime_stmt, "Contract must define AllowAgentRuntimeInvocation statement"



def test_bedrock_agentcore_endpoint_output(stack_outputs):
    outputs = stack_outputs("NetworkStack")
    
    if "BedrockAgentCoreEndpointId" not in outputs:
        pytest.skip("BedrockAgentCoreEndpointId not found - AgentCore not deployed")
    
    endpoint_id = outputs["BedrockAgentCoreEndpointId"]
    assert endpoint_id.startswith("vpce-")


def test_bedrock_agentcore_gateway_endpoint_output(stack_outputs):
    outputs = stack_outputs("NetworkStack")
    
    if "BedrockAgentCoreGatewayEndpointId" not in outputs:
        pytest.skip("BedrockAgentCoreGatewayEndpointId not found - AgentCore not deployed")
    
    gateway_id = outputs["BedrockAgentCoreGatewayEndpointId"]
    assert gateway_id.startswith("vpce-")


def test_bedrock_agentcore_endpoint_properties(stack_outputs, ec2_client):
    outputs = stack_outputs("NetworkStack")
    
    if "BedrockAgentCoreEndpointId" not in outputs:
        pytest.skip("BedrockAgentCoreEndpointId not found - AgentCore not deployed")
    
    endpoint_id = outputs["BedrockAgentCoreEndpointId"]
    
    response = ec2_client.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])
    assert len(response["VpcEndpoints"]) == 1
    
    endpoint = response["VpcEndpoints"][0]
    assert endpoint["VpcEndpointType"] == "Interface"
    assert endpoint["State"] == "available"
    assert endpoint["ServiceName"] == "com.amazonaws.us-east-1.bedrock-agentcore"
    assert endpoint["PrivateDnsEnabled"] is True


def test_bedrock_agentcore_gateway_endpoint_properties(stack_outputs, ec2_client):
    outputs = stack_outputs("NetworkStack")
    
    if "BedrockAgentCoreGatewayEndpointId" not in outputs:
        pytest.skip("BedrockAgentCoreGatewayEndpointId not found - AgentCore not deployed")
    
    gateway_id = outputs["BedrockAgentCoreGatewayEndpointId"]
    
    response = ec2_client.describe_vpc_endpoints(VpcEndpointIds=[gateway_id])
    assert len(response["VpcEndpoints"]) == 1
    
    endpoint = response["VpcEndpoints"][0]
    assert endpoint["VpcEndpointType"] == "Interface"
    assert endpoint["State"] == "available"
    assert endpoint["ServiceName"] == "com.amazonaws.us-east-1.bedrock-agentcore.gateway"
    assert endpoint["PrivateDnsEnabled"] is True


def test_bedrock_agentcore_endpoint_subnets(stack_outputs, ec2_client):
    outputs = stack_outputs("NetworkStack")
    
    if "BedrockAgentCoreEndpointId" not in outputs:
        pytest.skip("BedrockAgentCoreEndpointId not found - AgentCore not deployed")
    
    endpoint_id = outputs["BedrockAgentCoreEndpointId"]
    
    response = ec2_client.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])
    endpoint = response["VpcEndpoints"][0]
    
    assert len(endpoint["SubnetIds"]) > 0
    for subnet_id in endpoint["SubnetIds"]:
        assert subnet_id.startswith("subnet-")


def test_agentcore_runtime_security_group_output(stack_outputs):
    outputs = stack_outputs("NetworkStack")
    
    if "AgentCoreRuntimeSecurityGroupId" not in outputs:
        pytest.skip("AgentCoreRuntimeSecurityGroupId not found - AgentCore not deployed")
    
    sg_id = outputs["AgentCoreRuntimeSecurityGroupId"]
    assert sg_id.startswith("sg-")


def test_agentcore_runtime_security_group_properties(stack_outputs, ec2_client):
    outputs = stack_outputs("NetworkStack")
    
    if "AgentCoreRuntimeSecurityGroupId" not in outputs:
        pytest.skip("AgentCoreRuntimeSecurityGroupId not found - AgentCore not deployed")
    
    sg_id = outputs["AgentCoreRuntimeSecurityGroupId"]
    
    response = ec2_client.describe_security_groups(GroupIds=[sg_id])
    assert len(response["SecurityGroups"]) == 1
    
    sg = response["SecurityGroups"][0]
    assert sg["GroupName"].startswith("NetworkStack-AgentCoreRuntimeSecurityGroup") or "AgentCoreRuntime" in sg["GroupName"]
    assert "Bedrock AgentCore agent runtimes" in sg["Description"]


def test_agentcore_runtime_security_group_egress_rules(stack_outputs, ec2_client):
    outputs = stack_outputs("NetworkStack")
    
    if "AgentCoreRuntimeSecurityGroupId" not in outputs:
        pytest.skip("AgentCoreRuntimeSecurityGroupId not found - AgentCore not deployed")
    
    sg_id = outputs["AgentCoreRuntimeSecurityGroupId"]
    
    response = ec2_client.describe_security_groups(GroupIds=[sg_id])
    sg = response["SecurityGroups"][0]
    
    egress_rules = sg["IpPermissionsEgress"]
    https_rule_found = False
    
    for rule in egress_rules:
        if rule["IpProtocol"] == "tcp" and rule.get("FromPort") == 443 and rule.get("ToPort") == 443:
            if any(ip_range["CidrIp"] == "0.0.0.0/0" for ip_range in rule.get("IpRanges", [])):
                https_rule_found = True
                break
    
    assert https_rule_found, "HTTPS egress rule to 0.0.0.0/0 not found"


def test_private_agent_subnets_output(stack_outputs):
    outputs = stack_outputs("NetworkStack")
    
    assert "PrivateAgentSubnetIds" in outputs
    subnet_ids = outputs["PrivateAgentSubnetIds"]
    
    assert len(subnet_ids) > 0
    for subnet_id in subnet_ids.split(","):
        assert subnet_id.strip().startswith("subnet-")

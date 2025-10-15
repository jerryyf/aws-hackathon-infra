import pytest
from aws_cdk.assertions import Template, Match
from cdk.stacks.network_stack import NetworkStack
import aws_cdk as cdk


@pytest.fixture(scope="session")
def network_stack():
    app = cdk.App()
    stack = NetworkStack(
        app,
        "TestNetworkStack",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    return stack


def test_bedrock_agentcore_endpoint_exists(network_stack):
    template = Template.from_stack(network_stack)
    
    template.has_resource_properties(
        "AWS::EC2::VPCEndpoint",
        {
            "ServiceName": "com.amazonaws.us-east-1.bedrock-agentcore",
            "VpcEndpointType": "Interface",
            "PrivateDnsEnabled": True,
        }
    )


def test_bedrock_agentcore_gateway_endpoint_exists(network_stack):
    template = Template.from_stack(network_stack)
    
    template.has_resource_properties(
        "AWS::EC2::VPCEndpoint",
        {
            "ServiceName": "com.amazonaws.us-east-1.bedrock-agentcore.gateway",
            "VpcEndpointType": "Interface",
            "PrivateDnsEnabled": True,
        }
    )


def test_bedrock_agentcore_endpoint_subnets(network_stack):
    template = Template.from_stack(network_stack)
    
    template.has_resource_properties(
        "AWS::EC2::VPCEndpoint",
        {
            "ServiceName": "com.amazonaws.us-east-1.bedrock-agentcore",
            "SubnetIds": Match.any_value()
        }
    )


def test_bedrock_agentcore_endpoint_outputs(network_stack):
    template = Template.from_stack(network_stack)
    
    outputs = template.find_outputs("BedrockAgentCoreEndpointId")
    assert len(outputs) == 1
    
    endpoint_output = outputs["BedrockAgentCoreEndpointId"]
    assert endpoint_output["Description"] == "Bedrock AgentCore VPC Endpoint ID"
    assert endpoint_output["Export"]["Name"] == "BedrockAgentCoreEndpointId"
    assert "Value" in endpoint_output


def test_bedrock_agentcore_gateway_endpoint_outputs(network_stack):
    template = Template.from_stack(network_stack)
    
    outputs = template.find_outputs("BedrockAgentCoreGatewayEndpointId")
    assert len(outputs) == 1
    
    gateway_output = outputs["BedrockAgentCoreGatewayEndpointId"]
    assert gateway_output["Description"] == "Bedrock AgentCore Gateway VPC Endpoint ID"
    assert gateway_output["Export"]["Name"] == "BedrockAgentCoreGatewayEndpointId"
    assert "Value" in gateway_output


def test_agentcore_runtime_security_group_exists(network_stack):
    template = Template.from_stack(network_stack)
    
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "GroupDescription": "Security group for Bedrock AgentCore agent runtimes",
            "VpcId": Match.any_value(),
        }
    )


def test_agentcore_runtime_security_group_egress(network_stack):
    template = Template.from_stack(network_stack)
    
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "GroupDescription": "Security group for Bedrock AgentCore agent runtimes",
            "SecurityGroupEgress": Match.array_with([
                {
                    "IpProtocol": "tcp",
                    "FromPort": 443,
                    "ToPort": 443,
                    "CidrIp": "0.0.0.0/0",
                    "Description": "HTTPS egress to AWS services"
                }
            ])
        }
    )


def test_agentcore_runtime_security_group_output(network_stack):
    template = Template.from_stack(network_stack)
    
    outputs = template.find_outputs("AgentCoreRuntimeSecurityGroupId")
    assert len(outputs) == 1
    
    sg_output = outputs["AgentCoreRuntimeSecurityGroupId"]
    assert sg_output["Description"] == "Security group ID for AgentCore runtimes"
    assert sg_output["Export"]["Name"] == "AgentCoreRuntimeSecurityGroupId"
    assert "Value" in sg_output


def test_private_agent_subnets_output(network_stack):
    template = Template.from_stack(network_stack)
    
    outputs = template.find_outputs("PrivateAgentSubnetIds")
    assert len(outputs) == 1
    
    subnet_output = outputs["PrivateAgentSubnetIds"]
    assert subnet_output["Description"] == "Private agent subnet IDs"
    assert subnet_output["Export"]["Name"] == "PrivateAgentSubnetIds"
    assert "Value" in subnet_output

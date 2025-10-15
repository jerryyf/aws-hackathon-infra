import pytest
from aws_cdk.assertions import Template, Match
from cdk.stacks.network_stack import NetworkStack
from cdk.stacks.security_stack import SecurityStack
from cdk.stacks.storage_stack import StorageStack
from cdk.stacks.agentcore_stack import AgentCoreStack
import aws_cdk as cdk


@pytest.fixture(scope="session")
def agentcore_stack():
    app = cdk.App()
    
    network_stack = NetworkStack(
        app,
        "TestNetworkStack",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    
    security_stack = SecurityStack(
        app,
        "TestSecurityStack",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    
    storage_stack = StorageStack(
        app,
        "TestStorageStack",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    
    agentcore_config = {
        "cpu": 512,
        "memory": 1024,
        "network_mode": "VPC",
    }
    
    stack = AgentCoreStack(
        app,
        "TestAgentCoreStack",
        network_stack=network_stack,
        security_stack=security_stack,
        storage_stack=storage_stack,
        agentcore_config=agentcore_config,
        environment="test",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    
    return stack


def test_agentcore_runtime_outputs_exist(agentcore_stack):
    template = Template.from_stack(agentcore_stack)
    
    outputs = template.find_outputs("*")
    
    required_outputs = [
        "AgentRuntimeArn",
        "AgentRuntimeId",
        "AgentRuntimeEndpointUrl",
        "AgentRuntimeStatus",
        "AgentRuntimeVersion",
        "ExecutionRoleArn",
    ]
    
    for output_name in required_outputs:
        assert output_name in outputs, f"Required output {output_name} not found"


def test_agentcore_runtime_arn_output(agentcore_stack):
    template = Template.from_stack(agentcore_stack)
    
    outputs = template.find_outputs("AgentRuntimeArn")
    assert len(outputs) == 1
    
    arn_output = outputs["AgentRuntimeArn"]
    assert arn_output["Description"] == "Bedrock AgentCore runtime ARN"
    assert arn_output["Export"]["Name"] == "test-AgentRuntimeArn"
    assert "Value" in arn_output


def test_agentcore_runtime_id_output(agentcore_stack):
    template = Template.from_stack(agentcore_stack)
    
    outputs = template.find_outputs("AgentRuntimeId")
    assert len(outputs) == 1
    
    id_output = outputs["AgentRuntimeId"]
    assert id_output["Description"] == "Bedrock AgentCore runtime ID"
    assert id_output["Export"]["Name"] == "AgentRuntimeId"
    assert "Value" in id_output


def test_agentcore_runtime_endpoint_output(agentcore_stack):
    template = Template.from_stack(agentcore_stack)
    
    outputs = template.find_outputs("AgentRuntimeEndpointUrl")
    assert len(outputs) == 1
    
    endpoint_output = outputs["AgentRuntimeEndpointUrl"]
    assert endpoint_output["Description"] == "Bedrock AgentCore runtime endpoint URL"
    assert endpoint_output["Export"]["Name"] == "AgentRuntimeEndpointUrl"
    assert "Value" in endpoint_output


def test_agentcore_runtime_status_output(agentcore_stack):
    template = Template.from_stack(agentcore_stack)
    
    outputs = template.find_outputs("AgentRuntimeStatus")
    assert len(outputs) == 1
    
    status_output = outputs["AgentRuntimeStatus"]
    assert status_output["Description"] == "Bedrock AgentCore runtime status"
    assert status_output["Export"]["Name"] == "AgentRuntimeStatus"
    assert "Value" in status_output


def test_agentcore_runtime_version_output(agentcore_stack):
    template = Template.from_stack(agentcore_stack)
    
    outputs = template.find_outputs("AgentRuntimeVersion")
    assert len(outputs) == 1
    
    version_output = outputs["AgentRuntimeVersion"]
    assert version_output["Description"] == "Bedrock AgentCore runtime version"
    assert version_output["Export"]["Name"] == "AgentRuntimeVersion"
    assert "Value" in version_output


def test_execution_role_arn_output(agentcore_stack):
    template = Template.from_stack(agentcore_stack)
    
    outputs = template.find_outputs("ExecutionRoleArn")
    assert len(outputs) == 1
    
    role_output = outputs["ExecutionRoleArn"]
    assert role_output["Description"] == "Bedrock AgentCore execution role ARN"
    assert role_output["Export"]["Name"] == "test-AgentExecutionRoleArn"
    assert "Value" in role_output


def test_agentcore_runtime_properties(agentcore_stack):
    template = Template.from_stack(agentcore_stack)
    
    template.has_resource_properties(
        "AWS::BedrockAgentCore::Runtime",
        {
            "AgentRuntimeName": "hackathon-agent-test-us-east-1",
            "RoleArn": {
                "Fn::ImportValue": Match.string_like_regexp(".*AgentCoreExecutionRole.*Arn.*")
            },
            "AgentRuntimeArtifact": {
                "ContainerConfiguration": {
                    "Cpu": 512,
                    "Memory": 1024,
                }
            },
            "NetworkConfiguration": {
                "NetworkMode": "VPC",
            },
        }
    )


def test_agentcore_runtime_tags(agentcore_stack):
    template = Template.from_stack(agentcore_stack)
    
    template.has_resource_properties(
        "AWS::BedrockAgentCore::Runtime",
        {
            "Tags": [
                {"Key": "Project", "Value": "aws-hackathon"},
                {"Key": "Environment", "Value": "test"},
                {"Key": "Owner", "Value": "platform-team"},
                {"Key": "CostCenter", "Value": "engineering"},
                {"Key": "ManagedBy", "Value": "cdk"},
                {"Key": "Stack", "Value": "agentcore-stack"},
            ]
        }
    )

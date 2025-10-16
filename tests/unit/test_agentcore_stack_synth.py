import uuid
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
from cdk.stacks.security_stack import SecurityStack
from cdk.stacks.storage_stack import StorageStack
from cdk.stacks.agentcore_stack import AgentCoreStack
import aws_cdk as cdk


def test_agentcore_stack_synth_public_mode():
    app = cdk.App()
    unique_id = str(uuid.uuid4())[:8]

    network_stack = NetworkStack(
        app,
        f"TestNetworkStack{unique_id}",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )

    security_stack = SecurityStack(
        app,
        f"TestSecurityStack{unique_id}",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )

    storage_stack = StorageStack(
        app,
        f"TestStorageStack{unique_id}",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )

    agentcore_config = {
        "cpu": 512,
        "memory": 1024,
        "network_mode": "PUBLIC",
    }

    stack = AgentCoreStack(
        app,
        f"TestAgentCoreStack{unique_id}",
        network_stack=network_stack,
        security_stack=security_stack,
        storage_stack=storage_stack,
        agentcore_config=agentcore_config,
        environment="test",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::BedrockAgentCore::Runtime", 1)

    template.has_resource_properties(
        "AWS::BedrockAgentCore::Runtime",
        {"NetworkConfiguration": {"NetworkMode": "PUBLIC"}},
    )


def test_agentcore_stack_synth_vpc_mode():
    app = cdk.App()
    unique_id = str(uuid.uuid4())[:8]

    network_stack = NetworkStack(
        app,
        f"TestNetworkStack{unique_id}",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )

    security_stack = SecurityStack(
        app,
        f"TestSecurityStack{unique_id}",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )

    storage_stack = StorageStack(
        app,
        f"TestStorageStack{unique_id}",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )

    agentcore_config = {
        "cpu": 2048,
        "memory": 4096,
        "network_mode": "VPC",
    }

    stack = AgentCoreStack(
        app,
        f"TestAgentCoreStack{unique_id}",
        network_stack=network_stack,
        security_stack=security_stack,
        storage_stack=storage_stack,
        agentcore_config=agentcore_config,
        environment="prod",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::BedrockAgentCore::Runtime", 1)

    template.has_resource_properties(
        "AWS::BedrockAgentCore::Runtime",
        {"NetworkConfiguration": {"NetworkMode": "VPC"}},
    )


def test_agentcore_stack_synth_outputs():
    app = cdk.App()
    unique_id = str(uuid.uuid4())[:8]

    network_stack = NetworkStack(
        app,
        f"TestNetworkStack{unique_id}",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )

    security_stack = SecurityStack(
        app,
        f"TestSecurityStack{unique_id}",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )

    storage_stack = StorageStack(
        app,
        f"TestStorageStack{unique_id}",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )

    agentcore_config = {
        "cpu": 512,
        "memory": 1024,
        "network_mode": "PUBLIC",
    }

    stack = AgentCoreStack(
        app,
        f"TestAgentCoreStack{unique_id}",
        network_stack=network_stack,
        security_stack=security_stack,
        storage_stack=storage_stack,
        agentcore_config=agentcore_config,
        environment="test",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )

    template = Template.from_stack(stack)

    outputs = template.find_outputs("*")

    assert "AgentRuntimeArn" in outputs
    assert "AgentRuntimeId" in outputs
    assert "AgentRuntimeEndpointUrl" in outputs
    assert "AgentRuntimeStatus" in outputs
    assert "AgentRuntimeVersion" in outputs
    assert "ExecutionRoleArn" in outputs
    assert "NetworkMode" in outputs

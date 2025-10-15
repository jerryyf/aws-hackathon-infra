import pytest
from aws_cdk import App, Stack
from cdk.stacks.agentcore_stack import AgentCoreStack
from cdk.stacks.network_stack import NetworkStack
from cdk.stacks.security_stack import SecurityStack
from cdk.stacks.storage_stack import StorageStack


@pytest.fixture(scope="function")
def app():
    return App()


@pytest.fixture(scope="session")
def network_stack_session():
    app = App()
    return NetworkStack(app, "ValidationTestNetworkStack")


@pytest.fixture(scope="session")
def security_stack_session():
    app = App()
    return SecurityStack(app, "ValidationTestSecurityStack")


@pytest.fixture(scope="session")
def storage_stack_session():
    app = App()
    return StorageStack(app, "ValidationTestStorageStack")


# For validation tests that create AgentCoreStack,  need fresh instances each time
@pytest.fixture(scope="function")
def network_stack(app):
    return NetworkStack(app, "ValidationTestNetworkStack")


@pytest.fixture(scope="function")
def security_stack(app):
    return SecurityStack(app, "ValidationTestSecurityStack")


@pytest.fixture(scope="function")
def storage_stack(app):
    return StorageStack(app, "ValidationTestStorageStack")


def test_invalid_environment_empty(app, network_stack, security_stack, storage_stack):
    with pytest.raises(ValueError, match="environment parameter is required"):
        AgentCoreStack(
            app,
            "TestAgentCoreStack",
            network_stack=network_stack,
            security_stack=security_stack,
            storage_stack=storage_stack,
            agentcore_config={"cpu": 1024, "memory": 2048},
            environment="",
        )


def test_invalid_environment_special_chars(
    app, network_stack, security_stack, storage_stack
):
    with pytest.raises(ValueError, match="must be alphanumeric"):
        AgentCoreStack(
            app,
            "TestAgentCoreStack",
            network_stack=network_stack,
            security_stack=security_stack,
            storage_stack=storage_stack,
            agentcore_config={"cpu": 1024, "memory": 2048},
            environment="test@env!",
        )


def test_invalid_network_mode(app, network_stack, security_stack, storage_stack):
    with pytest.raises(ValueError, match="Invalid network_mode"):
        AgentCoreStack(
            app,
            "TestAgentCoreStack",
            network_stack=network_stack,
            security_stack=security_stack,
            storage_stack=storage_stack,
            agentcore_config={"cpu": 1024, "memory": 2048, "network_mode": "INVALID"},
            environment="test",
        )


def test_missing_cpu(app, network_stack, security_stack, storage_stack):
    with pytest.raises(KeyError, match="missing required key 'cpu'"):
        AgentCoreStack(
            app,
            "TestAgentCoreStack",
            network_stack=network_stack,
            security_stack=security_stack,
            storage_stack=storage_stack,
            agentcore_config={"memory": 2048},
            environment="test",
        )


def test_missing_memory(app, network_stack, security_stack, storage_stack):
    with pytest.raises(KeyError, match="missing required key 'memory'"):
        AgentCoreStack(
            app,
            "TestAgentCoreStack",
            network_stack=network_stack,
            security_stack=security_stack,
            storage_stack=storage_stack,
            agentcore_config={"cpu": 1024},
            environment="test",
        )


def test_invalid_cpu_value(app, network_stack, security_stack, storage_stack):
    with pytest.raises(ValueError, match="Invalid CPU value"):
        AgentCoreStack(
            app,
            "TestAgentCoreStack",
            network_stack=network_stack,
            security_stack=security_stack,
            storage_stack=storage_stack,
            agentcore_config={"cpu": 999, "memory": 2048},
            environment="test",
        )


def test_invalid_memory_value(app, network_stack, security_stack, storage_stack):
    with pytest.raises(ValueError, match="Invalid memory value"):
        AgentCoreStack(
            app,
            "TestAgentCoreStack",
            network_stack=network_stack,
            security_stack=security_stack,
            storage_stack=storage_stack,
            agentcore_config={"cpu": 1024, "memory": 1500},
            environment="test",
        )


def test_invalid_cpu_memory_ratio(app, network_stack, security_stack, storage_stack):
    with pytest.raises(ValueError, match="Memory must be at least 2x CPU"):
        AgentCoreStack(
            app,
            "TestAgentCoreStack",
            network_stack=network_stack,
            security_stack=security_stack,
            storage_stack=storage_stack,
            agentcore_config={"cpu": 2048, "memory": 2048},
            environment="test",
        )


def test_string_cpu_memory_values(app, network_stack, security_stack, storage_stack):
    stack = AgentCoreStack(
        app,
        "TestAgentCoreStack",
        network_stack=network_stack,
        security_stack=security_stack,
        storage_stack=storage_stack,
        agentcore_config={"cpu": "1024", "memory": "2048"},
        environment="test",
    )
    assert stack is not None


def test_missing_security_stack(app, network_stack, storage_stack):
    with pytest.raises(ValueError, match="security_stack is required"):
        AgentCoreStack(
            app,
            "TestAgentCoreStack",
            network_stack=network_stack,
            security_stack=None,
            storage_stack=storage_stack,
            agentcore_config={"cpu": 1024, "memory": 2048},
            environment="test",
        )


def test_missing_storage_stack(app, network_stack, security_stack):
    with pytest.raises(ValueError, match="storage_stack is required"):
        AgentCoreStack(
            app,
            "TestAgentCoreStack",
            network_stack=network_stack,
            security_stack=security_stack,
            storage_stack=None,
            agentcore_config={"cpu": 1024, "memory": 2048},
            environment="test",
        )


def test_vpc_mode_without_network_stack(app, security_stack, storage_stack):
    with pytest.raises(ValueError, match="VPC mode requires a valid network_stack"):
        AgentCoreStack(
            app,
            "TestAgentCoreStack",
            network_stack=None,
            security_stack=security_stack,
            storage_stack=storage_stack,
            agentcore_config={"cpu": 1024, "memory": 2048, "network_mode": "VPC"},
            environment="test",
        )


def test_public_mode_without_network_stack(app, security_stack, storage_stack):
    stack = AgentCoreStack(
        app,
        "TestAgentCoreStack",
        network_stack=None,
        security_stack=security_stack,
        storage_stack=storage_stack,
        agentcore_config={"cpu": 1024, "memory": 2048, "network_mode": "PUBLIC"},
        environment="test",
    )
    assert stack is not None


def test_valid_cpu_memory_combinations(
    app, network_stack, security_stack, storage_stack
):
    valid_combos = [
        (512, 1024),
        (512, 2048),
        (1024, 2048),
        (1024, 4096),
        (2048, 4096),
        (2048, 8192),
        (4096, 8192),
        (4096, 16384),
    ]

    for cpu, memory in valid_combos:
        stack = AgentCoreStack(
            app,
            f"TestAgentCoreStack-{cpu}-{memory}",
            network_stack=network_stack,
            security_stack=security_stack,
            storage_stack=storage_stack,
            agentcore_config={"cpu": cpu, "memory": memory},
            environment="test",
        )
        assert stack is not None

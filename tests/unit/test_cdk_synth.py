import pytest
import aws_cdk as cdk
from cdk.stacks.network_stack import NetworkStack
from cdk.stacks.database_stack import DatabaseStack
from cdk.stacks.compute_stack import ComputeStack
from cdk.stacks.storage_stack import StorageStack
from cdk.stacks.security_stack import SecurityStack
from cdk.stacks.monitoring_stack import MonitoringStack


def test_synth_all_stacks():
    """Test that all CDK stacks can be synthesized without errors"""
    app = cdk.App()

    network_stack = NetworkStack(app, "TestNetworkStack")
    DatabaseStack(app, "TestDatabaseStack", network_stack=network_stack)
    ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    storage_stack = StorageStack(app, "TestStorageStack")
    SecurityStack(app, "TestSecurityStack")
    MonitoringStack(app, "TestMonitoringStack", logs_bucket=storage_stack.logs_bucket)

    try:
        app.synth()
    except Exception as e:
        pytest.fail(f"CDK synthesis failed: {e}")

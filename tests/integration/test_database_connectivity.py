import pytest
from aws_cdk.assertions import Template
from cdk.stacks.database_stack import DatabaseStack
import aws_cdk as cdk


def test_database_connectivity_integration():
    """Integration test for database connectivity"""
    app = cdk.App()

    # Create database stack
    stack = DatabaseStack(app, "TestDatabaseStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Verify RDS cluster
    template.has_resource_properties("AWS::RDS::DBCluster", {
        "Engine": "aurora-postgresql",
        "DatabaseName": "hackathon",
        "StorageEncrypted": True
    })

    # Verify RDS Proxy
    template.has_resource_properties("AWS::RDS::DBProxy", {
        "EngineFamily": "POSTGRESQL",
        "RequireTLS": True
    })

    # Verify proxy targets cluster
    proxy_target_groups = template.find_resources("AWS::RDS::DBProxyTargetGroup")
    assert len(proxy_target_groups) >= 1

    # Verify outputs
    outputs = template.find_outputs("*")
    assert "RdsEndpoint" in outputs
    assert "RdsPort" in outputs
    assert outputs["RdsPort"]["Value"] == "5432"

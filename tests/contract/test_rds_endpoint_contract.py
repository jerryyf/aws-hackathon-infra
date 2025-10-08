import json
import pytest
from aws_cdk.assertions import Template
from cdk.stacks.database_stack import DatabaseStack
import aws_cdk as cdk


def test_rds_endpoint_contract():
    """Test that RDS endpoint stack output matches contract specification"""
    app = cdk.App()

    # Create stack
    stack = DatabaseStack(app, "TestDatabaseStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Check that RDS endpoint output exists with correct description and export
    outputs = template.find_outputs("RdsEndpoint")
    assert len(outputs) == 1
    rds_output = outputs["RdsEndpoint"]
    assert rds_output["Description"] == "RDS proxy endpoint"
    assert rds_output["Export"]["Name"] == "RdsEndpoint"
    assert "Value" in rds_output

    # Check port output
    port_outputs = template.find_outputs("RdsPort")
    assert len(port_outputs) == 1
    port_output = port_outputs["RdsPort"]
    assert port_output["Description"] == "RDS port"
    assert port_output["Export"]["Name"] == "RdsPort"
    assert port_output["Value"] == "5432"


def test_rds_cluster_properties():
    """Test RDS cluster properties"""
    app = cdk.App()
    stack = DatabaseStack(app, "TestDatabaseStack")
    template = Template.from_stack(stack)

    # Check Aurora PostgreSQL cluster
    template.has_resource_properties("AWS::RDS::DBCluster", {
        "Engine": "aurora-postgresql",
        "DatabaseName": "hackathon",
        "BackupRetentionPeriod": 7,
        "StorageEncrypted": True
    })

    # Check RDS Proxy
    template.has_resource_properties("AWS::RDS::DBProxy", {
        "EngineFamily": "POSTGRESQL",
        "RequireTLS": True
    })

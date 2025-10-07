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
    endpoint_output = outputs["RdsEndpoint"]
    assert endpoint_output["Description"] == "RDS proxy endpoint"
    assert endpoint_output["Export"]["Name"] == "RdsEndpoint"
    assert "Value" in endpoint_output

    # Check RDS port output
    port_outputs = template.find_outputs("RdsPort")
    assert len(port_outputs) == 1
    port_output = port_outputs["RdsPort"]
    assert port_output["Description"] == "RDS port"
    assert port_output["Export"]["Name"] == "RdsPort"
    assert port_output["Value"] == "5432"


def test_rds_endpoint_schema():
    """Test RDS endpoint outputs match contract schema"""
    app = cdk.App()
    stack = DatabaseStack(app, "TestDatabaseStack")
    template = Template.from_stack(stack)

    # Validate output structure matches contract
    outputs = template.find_outputs("*")
    assert "RdsEndpoint" in outputs
    assert "RdsPort" in outputs

    endpoint_output = outputs["RdsEndpoint"]
    assert "Description" in endpoint_output
    assert "Value" in endpoint_output
    assert endpoint_output["Description"] == "RDS proxy endpoint"

    port_output = outputs["RdsPort"]
    assert "Description" in port_output
    assert "Value" in port_output
    assert port_output["Description"] == "RDS port"
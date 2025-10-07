import json
import pytest
from aws_cdk.assertions import Template
from cdk.stacks.database_stack import DatabaseStack
import aws_cdk as cdk


def test_opensearch_endpoint_contract():
    """Test that OpenSearch endpoint stack output matches contract specification"""
    app = cdk.App()

    # Create stack
    stack = DatabaseStack(app, "TestDatabaseStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Check that OpenSearch endpoint output exists with correct description and export
    outputs = template.find_outputs("OpenSearchEndpoint")
    assert len(outputs) == 1
    endpoint_output = outputs["OpenSearchEndpoint"]
    assert endpoint_output["Description"] == "OpenSearch endpoint"
    assert endpoint_output["Export"]["Name"] == "OpenSearchEndpoint"
    assert "Value" in endpoint_output


def test_opensearch_endpoint_schema():
    """Test OpenSearch endpoint output matches contract schema"""
    app = cdk.App()
    stack = DatabaseStack(app, "TestDatabaseStack")
    template = Template.from_stack(stack)

    # Validate output structure matches contract
    outputs = template.find_outputs("*")
    assert "OpenSearchEndpoint" in outputs

    endpoint_output = outputs["OpenSearchEndpoint"]
    assert "Description" in endpoint_output
    assert "Value" in endpoint_output
    assert endpoint_output["Description"] == "OpenSearch endpoint"
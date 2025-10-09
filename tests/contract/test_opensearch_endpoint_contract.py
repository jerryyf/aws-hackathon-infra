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
    os_output = outputs["OpenSearchEndpoint"]
    assert os_output["Description"] == "OpenSearch endpoint"
    assert os_output["Export"]["Name"] == "OpenSearchEndpoint"
    assert "Value" in os_output


def test_opensearch_domain_properties():
    """Test OpenSearch domain properties"""
    app = cdk.App()
    stack = DatabaseStack(app, "TestDatabaseStack")
    template = Template.from_stack(stack)

    # Check OpenSearch domain
    template.has_resource_properties("AWS::OpenSearchService::Domain", {
        "EngineVersion": "OpenSearch_2.11",
        "ClusterConfig": {
            "InstanceCount": 2,
            "ZoneAwarenessEnabled": True,
            "ZoneAwarenessConfig": {
                "AvailabilityZoneCount": 2
            }
        },
        "EncryptionAtRestOptions": {
            "Enabled": True
        },
        "NodeToNodeEncryptionOptions": {
            "Enabled": True
        }
    })

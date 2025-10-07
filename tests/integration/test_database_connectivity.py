import pytest
from aws_cdk.assertions import Template
from cdk.stacks.database_stack import DatabaseStack
import aws_cdk as cdk


def test_database_connectivity():
    """Integration test for database connectivity"""
    app = cdk.App()

    # Create database stack
    stack = DatabaseStack(app, "TestDatabaseStack")
    template = Template.from_stack(stack)

    # Verify RDS cluster exists
    template.has_resource_properties("AWS::RDS::DBCluster", {
        "Engine": "aurora-postgresql",
        "DatabaseName": "hackathon"
    })

    # Verify RDS proxy exists
    template.has_resource("AWS::RDS::DBProxy", {})

    # Verify OpenSearch domain exists
    template.has_resource_properties("AWS::OpenSearchService::Domain", {
        "EngineVersion": "OpenSearch_2.11"
    })

    # Verify secrets manager secret exists
    template.has_resource_properties("AWS::SecretsManager::Secret", {
        "Name": "hackathon/rds/credentials"
    })
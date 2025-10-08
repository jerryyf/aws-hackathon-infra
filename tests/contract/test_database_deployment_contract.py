import pytest
from aws_cdk.assertions import Template
from cdk.stacks.database_stack import DatabaseStack
import aws_cdk as cdk


def test_database_deployment_readiness():
    """Test that database stack is ready for deployment with correct resources"""
    app = cdk.App()

    # Create stack
    stack = DatabaseStack(app, "TestDatabaseStack")

    # Get CloudFormation template
    template = Template.from_stack(stack)

    # Check that RDS cluster is created
    template.has_resource_properties("AWS::RDS::DBCluster", {
        "Engine": "aurora-postgresql",
        "DatabaseName": "hackathon"
    })

    # Check that RDS proxy is created
    template.has_resource_properties("AWS::RDS::DBProxy", {
        "EngineFamily": "POSTGRESQL"
    })

    # Check that OpenSearch domain is created
    template.has_resource_properties("AWS::OpenSearchService::Domain", {
        "EngineVersion": "OpenSearch_2.11"
    })

    # Check that secret is created
    template.has_resource_properties("AWS::SecretsManager::Secret", {
        "Name": "hackathon/rds/credentials"
    })


def test_database_deployment_outputs():
    """Test database deployment outputs for dependent stacks"""
    app = cdk.App()
    stack = DatabaseStack(app, "TestDatabaseStack")
    template = Template.from_stack(stack)

    # Validate required outputs
    outputs = template.find_outputs("*")
    required_outputs = ["RdsEndpoint", "RdsPort", "OpenSearchEndpoint"]

    for output_name in required_outputs:
        assert output_name in outputs
        assert "Export" in outputs[output_name]
        assert "Value" in outputs[output_name]
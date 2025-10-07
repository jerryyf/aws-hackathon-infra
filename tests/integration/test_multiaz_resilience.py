import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
from cdk.stacks.database_stack import DatabaseStack
import aws_cdk as cdk


def test_multiaz_resilience():
    """Integration test for multi-AZ resilience"""
    app = cdk.App()

    # Create stacks
    network_stack = NetworkStack(app, "TestNetworkStack")
    database_stack = DatabaseStack(app, "TestDatabaseStack", network_stack=network_stack)

    # Test network stack multi-AZ
    network_template = Template.from_stack(network_stack)
    # Verify subnets across 2 AZs (8 total subnets)
    network_template.resource_count_is("AWS::EC2::Subnet", 8)
    # Verify NAT gateways in 2 AZs
    network_template.resource_count_is("AWS::EC2::NatGateway", 2)

    # Test database stack multi-AZ
    database_template = Template.from_stack(database_stack)
    # Verify RDS cluster has 2 instances (multi-AZ)
    database_template.has_resource_properties("AWS::RDS::DBCluster", {
        "Engine": "aurora-postgresql"
    })
    # Verify OpenSearch has zone awareness
    database_template.has_resource_properties("AWS::OpenSearchService::Domain", {
        "ClusterConfig": {
            "InstanceCount": 3,
            "ZoneAwarenessEnabled": True,
            "ZoneAwarenessConfig": {
                "AvailabilityZoneCount": 2
            }
        }
    })
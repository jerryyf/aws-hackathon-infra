import pytest
from aws_cdk.assertions import Template
from cdk.stacks.network_stack import NetworkStack
from cdk.stacks.database_stack import DatabaseStack
import aws_cdk as cdk


def test_multiaz_resilience_integration():
    """Integration test for multi-AZ resilience"""
    app = cdk.App()

    # Create stacks
    network_stack = NetworkStack(app, "TestNetworkStack")
    database_stack = DatabaseStack(app, "TestDatabaseStack")

    # Test network stack multi-AZ
    network_template = Template.from_stack(network_stack)

    # Verify subnets across AZs
    subnets = network_template.find_resources("AWS::EC2::Subnet")
    azs = set()
    for subnet in subnets.values():
        az = subnet["Properties"]["AvailabilityZone"]
        azs.add(az)
    assert len(azs) == 2  # us-east-1a, us-east-1b
    assert "us-east-1a" in azs
    assert "us-east-1b" in azs

    # Test database stack multi-AZ
    db_template = Template.from_stack(database_stack)

    # Verify Aurora instances in different AZs
    aurora_instances = db_template.find_resources("AWS::RDS::DBInstance")
    instance_azs = set()
    for instance in aurora_instances.values():
        if "AvailabilityZone" in instance["Properties"]:
            instance_azs.add(instance["Properties"]["AvailabilityZone"])
    assert len(instance_azs) >= 2

    # Verify OpenSearch zone awareness
    opensearch_domains = db_template.find_resources("AWS::OpenSearchService::Domain")
    for domain in opensearch_domains.values():
        cluster_config = domain["Properties"]["ClusterConfig"]
        assert cluster_config["ZoneAwarenessEnabled"] == True
        assert cluster_config["ZoneAwarenessConfig"]["AvailabilityZoneCount"] == 2

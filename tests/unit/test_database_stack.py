import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
from cdk.stacks.database_stack import DatabaseStack
from cdk.stacks.network_stack import NetworkStack


def test_database_stack_rds_cluster_created():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = DatabaseStack(app, "TestDatabaseStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::RDS::DBCluster", 1)
    template.has_resource_properties(
        "AWS::RDS::DBCluster",
        {
            "Engine": "aurora-postgresql",
            "EngineVersion": "15.4",
            "DatabaseName": "hackathon",
            "StorageEncrypted": True,
        },
    )


def test_database_stack_rds_instances():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = DatabaseStack(app, "TestDatabaseStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::RDS::DBInstance", 2)


def test_database_stack_rds_secret():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = DatabaseStack(app, "TestDatabaseStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::SecretsManager::Secret", 1)
    template.has_resource_properties(
        "AWS::SecretsManager::Secret",
        {"Name": "hackathon/rds/credentials"},
    )


def test_database_stack_rds_proxy():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = DatabaseStack(app, "TestDatabaseStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::RDS::DBProxy", 1)


def test_database_stack_opensearch_domain():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = DatabaseStack(app, "TestDatabaseStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::OpenSearchService::Domain", 1)
    template.has_resource_properties(
        "AWS::OpenSearchService::Domain",
        {
            "EngineVersion": "OpenSearch_2.11",
            "ClusterConfig": {
                "DedicatedMasterEnabled": False,
                "InstanceCount": 2,
                "InstanceType": "t3.small.search",
                "ZoneAwarenessEnabled": True,
                "ZoneAwarenessConfig": {"AvailabilityZoneCount": 2},
            },
            "EncryptionAtRestOptions": {"Enabled": True},
            "NodeToNodeEncryptionOptions": {"Enabled": True},
            "DomainEndpointOptions": {"EnforceHTTPS": True},
        },
    )


def test_database_stack_outputs():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = DatabaseStack(app, "TestDatabaseStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_output("RdsEndpoint", {"Export": {"Name": "RdsEndpoint"}})
    template.has_output("RdsPort", {"Export": {"Name": "RdsPort"}})
    template.has_output("OpenSearchEndpoint", {"Export": {"Name": "OpenSearchEndpoint"}})


def test_database_stack_without_network_stack():
    app = cdk.App()
    stack = DatabaseStack(app, "TestDatabaseStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::VPC", 1)
    template.resource_count_is("AWS::RDS::DBCluster", 1)
    template.resource_count_is("AWS::OpenSearchService::Domain", 1)

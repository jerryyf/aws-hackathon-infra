from aws_cdk import (
    Stack,
    aws_rds as rds,
    aws_opensearchservice as opensearch,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
)
from constructs import Construct


class DatabaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get VPC from network stack
        network_stack = kwargs.pop('network_stack', None)
        if network_stack:
            vpc = network_stack.vpc
            data_subnets = [subnet for subnet in vpc.private_subnets if "PrivateData" in subnet.node.id]
        else:
            # For testing, create minimal VPC
            from aws_cdk import aws_ec2 as ec2
            vpc = ec2.Vpc(self, "TestVpc", cidr="10.0.0.0/16", max_azs=2)
            data_subnets = vpc.private_subnets

        # RDS Secret
        self.rds_secret = secretsmanager.Secret(
            self, "RdsSecret",
            secret_name="hackathon/rds/credentials",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "postgres"}',
                generate_string_key="password",
                exclude_characters="/@\""
            )
        )

        # RDS PostgreSQL
        self.rds_cluster = rds.DatabaseCluster(
            self, "RdsCluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_4
            ),
            credentials=rds.Credentials.from_secret(self.rds_secret),
            instance_props=rds.InstanceProps(
                vpc=vpc,
                vpc_subnets=ec2.SubnetSelection(subnets=data_subnets),
                publicly_accessible=False
            ),
            default_database_name="hackathon",
            instances=2,
            backup=rds.BackupProps(
                retention=7
            )
        )

        # RDS Proxy
        self.rds_proxy = rds.DatabaseProxy(
            self, "RdsProxy",
            proxy_target=rds.ProxyTarget.from_cluster(self.rds_cluster),
            secrets=[self.rds_secret],
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=data_subnets),
            security_groups=[self.rds_cluster.connections.security_groups[0]]
        )

        # OpenSearch
        self.opensearch_domain = opensearch.Domain(
            self, "OpenSearchDomain",
            version=opensearch.EngineVersion.OPENSEARCH_2_11,
            capacity=opensearch.CapacityConfig(
                master_nodes=0,
                data_nodes=3,
                data_node_instance_type="t3.small.search"
            ),
            vpc=vpc,
            vpc_subnets=[ec2.SubnetSelection(subnets=data_subnets)],
            zone_awareness=opensearch.ZoneAwarenessConfig(
                availability_zone_count=2
            ),
            encryption_at_rest=opensearch.EncryptionAtRestOptions(enabled=True),
            node_to_node_encryption=True,
            enforce_https=True
        )

        # Outputs
        CfnOutput(
            self, "RdsEndpoint",
            value=self.rds_proxy.endpoint,
            description="RDS proxy endpoint",
            export_name="RdsEndpoint"
        )

        CfnOutput(
            self, "RdsPort",
            value="5432",
            description="RDS port",
            export_name="RdsPort"
        )

        CfnOutput(
            self, "OpenSearchEndpoint",
            value=self.opensearch_domain.domain_endpoint,
            description="OpenSearch endpoint",
            export_name="OpenSearchEndpoint"
        )
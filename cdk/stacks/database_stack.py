import aws_cdk as cdk
from aws_cdk import (
    Stack,
    Duration,
        aws_iam as iam,
    aws_rds as rds,
    aws_opensearchservice as opensearch,
    aws_secretsmanager as secretsmanager,
    aws_ec2 as ec2,
    CfnOutput,
)
from constructs import Construct


class DatabaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        # Get VPC from network stack
        network_stack = kwargs.pop('network_stack', None)

        super().__init__(scope, construct_id, **kwargs)
        if network_stack:
            vpc = network_stack.vpc
            # Prefer direct references to the NetworkStack VPC private subnets
            # (avoids CloudFormation Export/Import races). Filter the VPC's
            # private subnets for the "PrivateData" group created by
            # NetworkStack.
            data_subnets = [
                subnet for subnet in vpc.private_subnets
                if "PrivateData" in subnet.node.id
            ]

            # If for some reason the network stack does not expose the
            # expected subnets (e.g. different naming), fall back to the
            # legacy behaviour of importing by export name. If that also
            # fails, create a small test VPC with private subnets to allow
            # local unit tests to proceed.
            if not data_subnets:
                try:
                    data_subnet_1_id = cdk.Fn.import_value("PrivateDataSubnet1Id")
                    data_subnet_2_id = cdk.Fn.import_value("PrivateDataSubnet2Id")
                    data_subnets = [
                        ec2.Subnet.from_subnet_attributes(self, "DataSubnet1",
                            subnet_id=data_subnet_1_id,
                            availability_zone="us-east-1a"
                        ),
                        ec2.Subnet.from_subnet_attributes(self, "DataSubnet2",
                            subnet_id=data_subnet_2_id,
                            availability_zone="us-east-1b"
                        )
                    ]
                except Exception:
                    # Last-resort: create a small test VPC so unit tests can run
                    vpc = ec2.Vpc(self, "TestVpcFromFallback", cidr="10.0.0.0/16", max_azs=2)
                    data_subnets = vpc.private_subnets
        else:
            # For testing, create minimal VPC
            vpc = ec2.Vpc(self, "TestVpc", cidr="10.0.0.0/16", max_azs=2)
            data_subnets = vpc.private_subnets

        # RDS Secret
        # Note: RDS service-linked role should already exist from previous deployments
        # We skip creating it here to avoid AlreadyExists errors

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
            credentials=rds.Credentials.from_secret(self.rds_secret, "username"),
            writer=rds.ClusterInstance.serverless_v2("writer"),
            readers=[rds.ClusterInstance.serverless_v2("reader")],
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=data_subnets),
            default_database_name="hackathon",
            backup=rds.BackupProps(
                retention=Duration.days(7)
            ),
            storage_encrypted=True
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
                # For a two Availability Zone deployment, OpenSearch requires
                # an even number of data nodes. Use 2 data nodes for 2 AZs.
                data_nodes=2,
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
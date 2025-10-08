from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_ecr as ecr,
    CfnOutput,
)
from constructs import Construct


class StorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Buckets
        self.knowledge_base_bucket = s3.Bucket(
            self, "KnowledgeBaseBucket",
            encryption=s3.BucketEncryption.KMS_MANAGED,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY
        )

        self.logs_bucket = s3.Bucket(
            self, "LogsBucket",
            encryption=s3.BucketEncryption.KMS_MANAGED,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY
        )

        self.bda_bucket = s3.Bucket(
            self, "BdaBucket",
            encryption=s3.BucketEncryption.KMS_MANAGED,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY
        )

        # ECR Repositories
        self.ecr_repo = ecr.Repository(
            self, "EcrRepository",
            repository_name="hackathon/app",
            image_scan_on_push=True,
            image_tag_mutability=ecr.TagMutability.IMMUTABLE,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Outputs
        CfnOutput(
            self, "KnowledgeBaseBucketName",
            value=self.knowledge_base_bucket.bucket_name,
            description="Knowledge base bucket name",
            export_name="KnowledgeBaseBucketName"
        )

        CfnOutput(
            self, "LogsBucketName",
            value=self.logs_bucket.bucket_name,
            description="Logs bucket name",
            export_name="LogsBucketName"
        )

        CfnOutput(
            self, "BdaBucketName",
            value=self.bda_bucket.bucket_name,
            description="BDA bucket name",
            export_name="BdaBucketName"
        )

        CfnOutput(
            self, "EcrRepositoryUri",
            value=self.ecr_repo.repository_uri,
            description="ECR repository URI",
            export_name="EcrRepositoryUri"
        )
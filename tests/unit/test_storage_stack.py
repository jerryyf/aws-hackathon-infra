import aws_cdk as cdk
from aws_cdk.assertions import Template
from cdk.stacks.storage_stack import StorageStack


def test_storage_stack_s3_buckets_created():
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::S3::Bucket", 3)


def test_storage_stack_knowledge_base_bucket():
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {"ServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms"}}
                ]
            },
            "VersioningConfiguration": {"Status": "Enabled"},
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            },
        },
    )


def test_storage_stack_all_buckets_block_public_access():
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = Template.from_stack(stack)

    buckets = template.find_resources("AWS::S3::Bucket")
    assert len(buckets) == 3, "Expected 3 S3 buckets"

    for bucket_id, bucket_props in buckets.items():
        props = bucket_props.get("Properties", {})
        public_access = props.get("PublicAccessBlockConfiguration", {})
        assert (
            public_access.get("BlockPublicAcls") is True
        ), f"Bucket {bucket_id} must block public ACLs"
        assert (
            public_access.get("BlockPublicPolicy") is True
        ), f"Bucket {bucket_id} must block public policy"
        assert (
            public_access.get("IgnorePublicAcls") is True
        ), f"Bucket {bucket_id} must ignore public ACLs"
        assert (
            public_access.get("RestrictPublicBuckets") is True
        ), f"Bucket {bucket_id} must restrict public buckets"


def test_storage_stack_ecr_repositories_created():
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::ECR::Repository", 2)


def test_storage_stack_app_ecr_repository():
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ECR::Repository",
        {
            "RepositoryName": "bidopsai/app",
            "ImageScanningConfiguration": {"ScanOnPush": True},
            "ImageTagMutability": "IMMUTABLE",
        },
    )


def test_storage_stack_agent_ecr_repository():
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ECR::Repository",
        {
            "RepositoryName": "bidopsai/agent",
            "ImageScanningConfiguration": {"ScanOnPush": True},
            "ImageTagMutability": "IMMUTABLE",
        },
    )


def test_storage_stack_all_ecr_repos_have_scanning():
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = Template.from_stack(stack)

    repos = template.find_resources("AWS::ECR::Repository")
    assert len(repos) == 2, "Expected 2 ECR repositories"

    for repo_id, repo_props in repos.items():
        props = repo_props.get("Properties", {})
        scanning = props.get("ImageScanningConfiguration", {})
        assert (
            scanning.get("ScanOnPush") is True
        ), f"Repository {repo_id} must have scan on push enabled"


def test_storage_stack_all_ecr_repos_are_immutable():
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = Template.from_stack(stack)

    repos = template.find_resources("AWS::ECR::Repository")
    assert len(repos) == 2, "Expected 2 ECR repositories"

    for repo_id, repo_props in repos.items():
        props = repo_props.get("Properties", {})
        mutability = props.get("ImageTagMutability")
        assert (
            mutability == "IMMUTABLE"
        ), f"Repository {repo_id} must have IMMUTABLE tag mutability"


def test_storage_stack_outputs():
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = Template.from_stack(stack)

    template.has_output("KnowledgeBaseBucketName", {"Export": {"Name": "KnowledgeBaseBucketName"}})
    template.has_output("LogsBucketName", {"Export": {"Name": "LogsBucketName"}})
    template.has_output("BdaBucketName", {"Export": {"Name": "BdaBucketName"}})
    template.has_output("AppEcrRepositoryUri", {"Export": {"Name": "AppEcrRepositoryUri"}})
    template.has_output("AgentEcrRepositoryUri", {"Export": {"Name": "AgentEcrRepositoryUri"}})

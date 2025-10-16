"""
Unit tests for StorageStack S3 buckets and ECR repositories
"""
import sys
from pathlib import Path

cdk_dir = Path(__file__).parent.parent.parent / "cdk"
sys.path.insert(0, str(cdk_dir))

import aws_cdk as cdk
from aws_cdk import assertions
from stacks.storage_stack import StorageStack


def test_storage_stack_s3_buckets_created():
    """Test that all required S3 buckets are created"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::S3::Bucket", 3)


def test_storage_stack_knowledge_base_bucket():
    """Test Knowledge Base bucket configuration"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::S3::Bucket", {
        "BucketEncryption": {
            "ServerSideEncryptionConfiguration": [
                {
                    "ServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "aws:kms"
                    }
                }
            ]
        },
        "VersioningConfiguration": {
            "Status": "Enabled"
        },
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True,
            "BlockPublicPolicy": True,
            "IgnorePublicAcls": True,
            "RestrictPublicBuckets": True
        }
    })


def test_storage_stack_logs_bucket():
    """Test Logs bucket configuration"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::S3::Bucket", {
        "BucketEncryption": {
            "ServerSideEncryptionConfiguration": [
                {
                    "ServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "aws:kms"
                    }
                }
            ]
        },
        "VersioningConfiguration": {
            "Status": "Enabled"
        }
    })


def test_storage_stack_bda_bucket():
    """Test BDA bucket configuration"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::S3::Bucket", {
        "BucketEncryption": {
            "ServerSideEncryptionConfiguration": [
                {
                    "ServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "aws:kms"
                    }
                }
            ]
        },
        "VersioningConfiguration": {
            "Status": "Enabled"
        }
    })


def test_storage_stack_all_buckets_block_public_access():
    """Test that all buckets block public access"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    buckets = template.find_resources("AWS::S3::Bucket")
    assert len(buckets) == 3, "Expected 3 S3 buckets"

    for bucket_id, bucket_props in buckets.items():
        props = bucket_props.get("Properties", {})
        public_access = props.get("PublicAccessBlockConfiguration", {})
        assert public_access.get("BlockPublicAcls") is True, f"Bucket {bucket_id} must block public ACLs"
        assert public_access.get("BlockPublicPolicy") is True, f"Bucket {bucket_id} must block public policy"
        assert public_access.get("IgnorePublicAcls") is True, f"Bucket {bucket_id} must ignore public ACLs"
        assert public_access.get("RestrictPublicBuckets") is True, f"Bucket {bucket_id} must restrict public buckets"


def test_storage_stack_ecr_repositories_created():
    """Test that all required ECR repositories are created"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::ECR::Repository", 4)


def test_storage_stack_app_ecr_repository():
    """Test App ECR repository configuration"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::ECR::Repository", {
        "RepositoryName": "bidopsai/app",
        "ImageScanningConfiguration": {
            "ScanOnPush": True
        },
        "ImageTagMutability": "IMMUTABLE"
    })


def test_storage_stack_api_ecr_repository():
    """Test API ECR repository configuration"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::ECR::Repository", {
        "RepositoryName": "bidopsai/api",
        "ImageScanningConfiguration": {
            "ScanOnPush": True
        },
        "ImageTagMutability": "IMMUTABLE"
    })


def test_storage_stack_agent_ecr_repository():
    """Test Agent ECR repository configuration"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::ECR::Repository", {
        "RepositoryName": "bidopsai/agent",
        "ImageScanningConfiguration": {
            "ScanOnPush": True
        },
        "ImageTagMutability": "IMMUTABLE"
    })


def test_storage_stack_subagent_ecr_repository():
    """Test Subagent ECR repository configuration"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::ECR::Repository", {
        "RepositoryName": "bidopsai/subagent",
        "ImageScanningConfiguration": {
            "ScanOnPush": True
        },
        "ImageTagMutability": "IMMUTABLE"
    })


def test_storage_stack_all_ecr_repos_have_scanning():
    """Test that all ECR repositories have image scanning enabled"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    repos = template.find_resources("AWS::ECR::Repository")
    assert len(repos) == 4, "Expected 4 ECR repositories"

    for repo_id, repo_props in repos.items():
        props = repo_props.get("Properties", {})
        scanning = props.get("ImageScanningConfiguration", {})
        assert scanning.get("ScanOnPush") is True, f"Repository {repo_id} must have scan on push enabled"


def test_storage_stack_all_ecr_repos_are_immutable():
    """Test that all ECR repositories have immutable tags"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    repos = template.find_resources("AWS::ECR::Repository")
    assert len(repos) == 4, "Expected 4 ECR repositories"

    for repo_id, repo_props in repos.items():
        props = repo_props.get("Properties", {})
        mutability = props.get("ImageTagMutability")
        assert mutability == "IMMUTABLE", f"Repository {repo_id} must have IMMUTABLE tag mutability"


def test_storage_stack_s3_outputs_created():
    """Test that S3 bucket CloudFormation outputs are created"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.has_output("KnowledgeBaseBucketName", {})
    template.has_output("LogsBucketName", {})
    template.has_output("BdaBucketName", {})


def test_storage_stack_ecr_outputs_created():
    """Test that ECR repository CloudFormation outputs are created"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.has_output("AppEcrRepositoryUri", {})
    template.has_output("ApiEcrRepositoryUri", {})
    template.has_output("AgentEcrRepositoryUri", {})
    template.has_output("SubagentEcrRepositoryUri", {})


def test_storage_stack_s3_outputs_have_exports():
    """Test that S3 bucket outputs have export names"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.has_output("KnowledgeBaseBucketName", {
        "Export": {
            "Name": "KnowledgeBaseBucketName"
        }
    })

    template.has_output("LogsBucketName", {
        "Export": {
            "Name": "LogsBucketName"
        }
    })

    template.has_output("BdaBucketName", {
        "Export": {
            "Name": "BdaBucketName"
        }
    })


def test_storage_stack_ecr_outputs_have_exports():
    """Test that ECR repository outputs have export names"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    template.has_output("AppEcrRepositoryUri", {
        "Export": {
            "Name": "AppEcrRepositoryUri"
        }
    })

    template.has_output("ApiEcrRepositoryUri", {
        "Export": {
            "Name": "ApiEcrRepositoryUri"
        }
    })

    template.has_output("AgentEcrRepositoryUri", {
        "Export": {
            "Name": "AgentEcrRepositoryUri"
        }
    })

    template.has_output("SubagentEcrRepositoryUri", {
        "Export": {
            "Name": "SubagentEcrRepositoryUri"
        }
    })


def test_storage_stack_removal_policy():
    """Test that all resources have DESTROY removal policy for easier cleanup"""
    app = cdk.App()
    stack = StorageStack(app, "TestStorageStack")
    template = assertions.Template.from_stack(stack)

    buckets = template.find_resources("AWS::S3::Bucket")
    for bucket_id, bucket_props in buckets.items():
        assert "DeletionPolicy" in bucket_props, f"Bucket {bucket_id} must have DeletionPolicy"
        assert bucket_props["DeletionPolicy"] == "Delete", f"Bucket {bucket_id} should have Delete policy"

    repos = template.find_resources("AWS::ECR::Repository")
    for repo_id, repo_props in repos.items():
        assert "DeletionPolicy" in repo_props, f"Repository {repo_id} must have DeletionPolicy"
        assert repo_props["DeletionPolicy"] == "Delete", f"Repository {repo_id} should have Delete policy"

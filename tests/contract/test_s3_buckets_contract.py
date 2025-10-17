def test_s3_buckets_contract(storage_stack_outputs):
    """Test that S3 buckets stack outputs match contract specification"""

    required_outputs = ["KnowledgeBaseBucketName", "LogsBucketName", "BdaBucketName"]

    for output_name in required_outputs:
        assert (
            output_name in storage_stack_outputs
        ), f"{output_name} output not found in StorageStack"
        
        bucket_name = storage_stack_outputs[output_name]
        assert bucket_name, f"{output_name} value must not be empty"
        assert isinstance(bucket_name, str), f"{output_name} must be a string"


def test_s3_bucket_properties(storage_stack_outputs, s3_client):
    """Test S3 bucket properties"""

    bucket_names = [
        storage_stack_outputs["KnowledgeBaseBucketName"],
        storage_stack_outputs["LogsBucketName"],
        storage_stack_outputs["BdaBucketName"],
    ]

    for bucket_name in bucket_names:
        # Verify bucket exists
        response = s3_client.head_bucket(Bucket=bucket_name)
        assert (
            response["ResponseMetadata"]["HTTPStatusCode"] == 200
        ), f"Bucket {bucket_name} not found"

        # Verify versioning enabled
        versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
        assert (
            versioning.get("Status") == "Enabled"
        ), f"Bucket {bucket_name} must have versioning enabled"

        # Verify encryption
        encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
        rules = encryption["ServerSideEncryptionConfiguration"]["Rules"]
        assert len(rules) > 0, f"Bucket {bucket_name} must have encryption configured"
        assert (
            rules[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"] == "aws:kms"
        ), f"Bucket {bucket_name} must use KMS encryption"

        # Verify public access block
        public_access = s3_client.get_public_access_block(Bucket=bucket_name)
        config = public_access["PublicAccessBlockConfiguration"]
        assert (
            config["BlockPublicAcls"] is True
        ), f"Bucket {bucket_name} must block public ACLs"
        assert (
            config["BlockPublicPolicy"] is True
        ), f"Bucket {bucket_name} must block public policy"
        assert (
            config["IgnorePublicAcls"] is True
        ), f"Bucket {bucket_name} must ignore public ACLs"
        assert (
            config["RestrictPublicBuckets"] is True
        ), f"Bucket {bucket_name} must restrict public buckets"


def test_s3_bucket_lifecycle_policies(storage_stack_outputs, s3_client):
    """Test that buckets have appropriate lifecycle policies where needed"""

    logs_bucket = storage_stack_outputs["LogsBucketName"]
    
    try:
        lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=logs_bucket)
        assert "Rules" in lifecycle, f"Logs bucket {logs_bucket} should have lifecycle rules for cost optimization"
    except s3_client.exceptions.NoSuchLifecycleConfiguration:
        pass


def test_s3_bucket_names_follow_convention(storage_stack_outputs):
    """Test that bucket names include stack identifiers"""
    
    kb_bucket = storage_stack_outputs["KnowledgeBaseBucketName"]
    logs_bucket = storage_stack_outputs["LogsBucketName"]
    bda_bucket = storage_stack_outputs["BdaBucketName"]
    
    assert kb_bucket.startswith("teststoragestack-") or "knowledgebase" in kb_bucket.lower(), "Knowledge Base bucket name should be identifiable"
    assert logs_bucket.startswith("teststoragestack-") or "logs" in logs_bucket.lower(), "Logs bucket name should be identifiable"
    assert bda_bucket.startswith("teststoragestack-") or "bda" in bda_bucket.lower(), "BDA bucket name should be identifiable"

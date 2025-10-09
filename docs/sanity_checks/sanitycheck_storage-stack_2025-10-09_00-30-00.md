# Storage Stack Sanity Checks

Timestamp: 2025-10-09 00:30:00 UTC
Stack: StorageStack

Checklist
---------
- CloudFormation: StorageStack = CREATE_COMPLETE
- S3 buckets: KnowledgeBaseBucket, LogsBucket, BdaBucket exist and are encrypted
- ECR: repository `hackathon/app` exists and image scan on push enabled

Commands
--------
- List buckets:
  ```bash
  aws s3 ls
  ```

# Compute Stack Sanity Checks

Timestamp: 2025-10-09 00:30:00 UTC
Stack: ComputeStack

Checklist
---------
- CloudFormation: ComputeStack = CREATE_COMPLETE
- ECS Cluster: `hackathon-cluster` exists
- Task Definition: `TaskDefinition` exists and container defined
- Networking: tasks can be scheduled in `PrivateApp` subnets

Commands
--------
- List ECS clusters:
  ```bash
  aws ecs list-clusters --query "clusterArns" --output json
  ```

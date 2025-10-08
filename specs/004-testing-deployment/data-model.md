# Data Model: Deployment Testing

## Entity: Deployment
Represents a complete CDK infrastructure deployment operation.

**Attributes:**
- `id`: UUID, primary key
- `status`: Enum (pending, synthesizing, deploying, verifying, completed, failed, rolled_back)
- `start_time`: Timestamp
- `end_time`: Timestamp (nullable)
- `environment`: String (dev, staging, prod)
- `stacks_order`: List<String> (ordered list of stack names)
- `logs`: List<LogEntry> (deployment progress logs)
- `rollback_reason`: String (nullable, reason for rollback)

**Relationships:**
- 1:N with Stack (deployment contains multiple stacks)
- 1:N with Resource (deployment creates multiple resources)

**Validation Rules:**
- Status transitions must follow: pending → synthesizing → deploying → verifying → completed/failed
- Failed deployments must have rollback_reason
- Stacks_order must respect dependency constraints

## Entity: Stack
Represents a CDK stack within a deployment.

**Attributes:**
- `id`: UUID, primary key
- `name`: String (CDK stack name)
- `deployment_id`: UUID, foreign key to Deployment
- `status`: Enum (pending, synthesizing, deploying, deployed, failed)
- `template_path`: String (path to synthesized CloudFormation template)
- `outputs`: Map<String, String> (stack outputs for cross-stack references)
- `dependencies`: List<String> (stack names this stack depends on)
- `error_message`: String (nullable)

**Relationships:**
- N:1 with Deployment
- 1:N with Resource

**Validation Rules:**
- Dependencies must be deployed before this stack
- Outputs must match expected contract
- Template must be valid CloudFormation

## Entity: Resource
Represents an AWS resource created by a stack.

**Attributes:**
- `id`: UUID, primary key
- `stack_id`: UUID, foreign key to Stack
- `resource_type`: String (AWS resource type, e.g., AWS::RDS::DBInstance)
- `resource_id`: String (AWS physical resource ID)
- `logical_id`: String (CloudFormation logical ID)
- `status`: Enum (creating, available, failed)
- `properties`: Map<String, Any> (resource configuration)
- `tags`: Map<String, String> (AWS resource tags)

**Relationships:**
- N:1 with Stack

**Validation Rules:**
- Resource must be accessible via AWS API
- Properties must match contract specifications
- Tags must include required governance tags

## State Transitions

### Deployment States
```
pending → synthesizing (CDK synth all stacks)
synthesizing → deploying (start stack deployments in order)
deploying → verifying (run post-deployment tests)
verifying → completed (all tests pass)
any → failed (error occurred)
failed → rolled_back (rollback executed)
```

### Stack States
```
pending → synthesizing (CDK synth single stack)
synthesizing → deploying (deploy to AWS)
deploying → deployed (deployment successful)
any → failed (deployment failed)
```

### Resource States
```
creating → available (resource created and accessible)
creating → failed (resource creation failed)
```
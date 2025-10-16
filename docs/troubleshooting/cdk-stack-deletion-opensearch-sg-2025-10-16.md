# CDK Stack Deletion Blocked by OpenSearch Security Group - 2025-10-16

## Issue Summary

CDK stack destruction failed due to orphaned OpenSearch domain blocking security group deletion. The DatabaseStack could not be deleted because security group `sg-031b8c424699093ea` had dependent objects (OpenSearch ENIs).

**Date**: 2025-10-16  
**Branch**: `009-cognito-stack`  
**AWS Profile**: `hackathon`  
**Region**: `us-east-1`

## Root Cause

**Orphaned OpenSearch Domain**: An OpenSearch domain (`opensearchdomai-igfnw07fpevg`) was still active and using security group `sg-031b8c424699093ea`, preventing CloudFormation from deleting the security group during DatabaseStack destruction.

**Secondary Issue**: A second OpenSearch domain (`opensearchdomai-tbay0anyur41`) was being created during the deletion process, indicating potential deployment or testing artifacts.

## Error Details

### Initial Error
```
DatabaseStack | DELETE_FAILED | AWS::EC2::SecurityGroup | OpenSearchDomain/SecurityGroup 
resource sg-031b8c424699093ea has a dependent object 
(Service: Ec2, Status Code: 400, Request ID: d4882963-a915-405d-8fb0-8666fdf01d57)
```

### CloudFormation Stack State
```
DatabaseStack: DELETE_FAILED
The following resource(s) failed to delete: [OpenSearchDomainSecurityGroupBA9F90EC]
```

### Network Interfaces Blocking Deletion
```
eni-0ea158bd8fab44acb | in-use | ES opensearchdomai-igfnw07fpevg | amazon-elasticsearch
eni-0a10df092913043d7 | in-use | ES opensearchdomai-igfnw07fpevg | amazon-elasticsearch
```

## Investigation Steps

1. **Identified Blocking Resource**
   ```bash
   aws ec2 describe-network-interfaces \
     --filters "Name=group-id,Values=sg-031b8c424699093ea" \
     --query 'NetworkInterfaces[*].[NetworkInterfaceId,Status,Description,RequesterId]'
   ```
   Found 2 ENIs attached to OpenSearch domain

2. **Verified OpenSearch Domain Status**
   ```bash
   aws opensearch describe-domain --domain-name opensearchdomai-igfnw07fpevg
   ```
   Result: Domain active, not in deletion state

3. **Discovered Multiple Domains**
   ```bash
   aws opensearch list-domain-names
   ```
   Found:
   - `opensearchdomai-igfnw07fpevg` (blocking deletion)
   - `opensearchdomai-tbay0anyur41` (being created - unexpected)

4. **Attempted CDK Destroy**
   ```bash
   cd cdk && cdk destroy DatabaseStack --force
   ```
   Failed with security group dependency error

## Resolution Steps

### 1. Manual OpenSearch Domain Deletion
```bash
# Delete the orphaned domain
aws opensearch delete-domain --domain-name opensearchdomai-igfnw07fpevg

# Verify deletion initiated
aws opensearch describe-domain --domain-name opensearchdomai-igfnw07fpevg
# Output: "Deleted": true, "DomainProcessingStatus": "Deleting"
```

### 2. Retry DatabaseStack Deletion
After initiating OpenSearch deletion (30 seconds wait):
```bash
cd cdk && cdk destroy DatabaseStack --force
```
✅ Success - Stack deleted once OpenSearch ENIs were released

### 3. Clean Up Second Domain
```bash
# Delete the newly created domain
aws opensearch delete-domain --domain-name opensearchdomai-tbay0anyur41
```

### 4. Complete Stack Destruction (Reverse Dependency Order)
```bash
# All stacks destroyed successfully in order:
cdk destroy AgentCoreStack --force      # ✅
cdk destroy MonitoringStack --force     # ✅
cdk destroy ComputeStack --force        # ✅
cdk destroy DatabaseStack --force       # ✅ (after OpenSearch cleanup)
cdk destroy StorageStack --force        # ✅
cdk destroy SecurityStack --force       # ✅
cdk destroy NetworkStack --force        # ✅
```

### 5. Verification
```bash
# Confirm no stacks remain
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE DELETE_FAILED

# Verify VPC deleted
aws ec2 describe-vpcs --vpc-ids vpc-050f1274c9ee43709
# Output: InvalidVpcID.NotFound

# Verify security group deleted
aws ec2 describe-security-groups --group-ids sg-031b8c424699093ea
# Output: InvalidGroup.NotFound

# Verify OpenSearch deletion in progress
aws opensearch list-domain-names
# Both domains: "Deleted": true, "DomainProcessingStatus": "Deleting"
```

## Final State

✅ **All CDK Stacks Destroyed**:
- AgentCoreStack
- MonitoringStack
- ComputeStack
- DatabaseStack
- StorageStack
- SecurityStack
- NetworkStack

✅ **Resources Cleaned Up**:
- VPC `vpc-050f1274c9ee43709` - Deleted
- Security Group `sg-031b8c424699093ea` - Deleted
- OpenSearch domains - Deletion in progress (async)

✅ **Remaining in AWS**:
- CDKToolkit (bootstrap stack - expected)
- Organizational StackSets (managed separately)

## Prevention Strategies

### 1. Always Check for Orphaned Resources
Before stack deletion:
```bash
# Check for orphaned OpenSearch domains
aws opensearch list-domain-names

# Check for resources using security groups
aws ec2 describe-network-interfaces \
  --filters "Name=group-id,Values=<sg-id>"

# Check VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=<vpc-id>"
```

### 2. Destroy Stacks in Reverse Dependency Order
```
AgentCoreStack → Monitoring → Compute → Database → Storage → Security → Network
```

### 3. Handle OpenSearch Deletion Gracefully
OpenSearch deletion is **asynchronous** - ENIs remain until domain is fully deleted:
- Manually delete orphaned domains first
- Wait 30-60 seconds before retrying stack deletion
- Monitor deletion status: `aws opensearch describe-domain`

### 4. Use Stack Dependencies Properly
Ensure CDK stacks have proper dependencies defined so CloudFormation handles deletion order automatically.

### 5. Clean Up Failed Stacks
If stack is in `DELETE_FAILED` state:
1. Manually delete blocking resources
2. Retry `cdk destroy` - CDK handles failed stacks gracefully
3. Don't try to delete from AWS Console while CDK is managing the stack

## Stack Deletion Command Reference

```bash
# Set AWS credentials
export AWS_PROFILE=hackathon
export AWS_REGION=us-east-1

# Destroy all stacks (reverse order)
cd cdk
cdk destroy AgentCoreStack --force
cdk destroy MonitoringStack --force
cdk destroy ComputeStack --force
cdk destroy DatabaseStack --force
cdk destroy StorageStack --force
cdk destroy SecurityStack --force
cdk destroy NetworkStack --force

# Or destroy all at once (CDK handles dependencies)
cdk destroy --all --force
```

## Lessons Learned

1. **OpenSearch ENIs Are Persistent**: Security groups can't be deleted while OpenSearch domain ENIs exist, even if the stack is being deleted

2. **Manual Intervention May Be Required**: When CloudFormation fails to delete resources, manual cleanup followed by retry is often the solution

3. **Async Deletion**: OpenSearch domains delete asynchronously - don't expect immediate cleanup

4. **Multiple Domain Detection**: Always check for duplicate/orphaned domains that may have been created during testing or failed deployments

5. **Security Group Dependencies**: Use `describe-network-interfaces` to identify what's blocking security group deletion

6. **CDK Handles Failed Stacks**: `cdk destroy` on a `DELETE_FAILED` stack will retry deletion - no need to manually intervene in CloudFormation console

## Related Files

- `cdk/stacks/database_stack.py` - OpenSearch domain definition
- `cdk/stacks/network_stack.py` - VPC and security group configuration
- `cdk/app.py` - Stack dependency chain

## References

- AWS OpenSearch deletion: https://docs.aws.amazon.com/opensearch-service/latest/developerguide/createupdatedomains.html#deletedomains
- Security group deletion issues: https://docs.aws.amazon.com/vpc/latest/userguide/working-with-security-groups.html#deleting-security-group
- CDK stack deletion: https://docs.aws.amazon.com/cdk/v2/guide/stack_how_to_delete.html

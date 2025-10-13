# Research Summary: AWS AgentCore Runtime Infrastructure

**Feature**: AWS Bedrock AgentCore Runtime Infrastructure  
**Research Date**: 2025-10-13  
**Purpose**: Resolve technical unknowns identified during plan phase

## Overview

This research addresses the technical clarifications needed to implement AWS Bedrock AgentCore runtime infrastructure while maintaining compliance with AWS Well-Architected Framework principles. Key areas investigated: container resource sizing, VPC endpoint configuration, and IAM security requirements.

## Research Areas

### 1. Container Resource Limits (Sustainability Pillar Compliance)

**Decision**: Implement environment-based resource allocation with monitoring-driven optimization

**Rationale**: 
- AWS Well-Architected Sustainability pillar requires right-sizing resources
- Current AWS CDK v2 lacks native `aws_cdk.aws_bedrockagentcore` module
- Container resources must be configured via L1 constructs or CloudFormation

**Configuration Approach**:
```python
RESOURCE_CONFIGS = {
    "development": {"cpu": 512, "memory": 1024},
    "staging": {"cpu": 1024, "memory": 2048}, 
    "production": {"cpu": 2048, "memory": 4096}
}
```

**Implementation Strategy**:
- Start with minimal resources (512 CPU, 1024 MiB memory) for development
- Use CloudWatch monitoring to track resource utilization
- Scale based on actual usage patterns
- Maximum 2 concurrent runtimes as per spec requirement

**Alternatives Considered**:
- Fixed high-resource allocation: Rejected due to sustainability concerns and cost
- Auto-scaling: Deferred to future iteration due to complexity

### 2. VPC Interface Endpoint Configuration

**Decision**: Deploy dual endpoint configuration with private DNS enabled

**Rationale**:
- FR-008 requires private connectivity for compliance
- Multi-AZ deployment needed for reliability 
- Private DNS simplifies application configuration

**Service Endpoints**:
- Primary: `com.amazonaws.us-east-1.bedrock-agentcore`
- Gateway: `com.amazonaws.us-east-1.bedrock-agentcore.gateway`

**Network Configuration**:
- Placement: PrivateAgent subnets (10.0.4.0/24, 10.0.5.0/24)
- Security: VPC-only access on port 443
- DNS: PrivateDnsEnabled=true for transparent service access
- Multi-AZ: Automatic deployment across us-east-1a and us-east-1b

**Alternatives Considered**:
- Public endpoint access: Rejected due to compliance requirements
- Single AZ deployment: Rejected due to reliability concerns

### 3. IAM Trust Policy and Permissions

**Decision**: Implement least-privilege execution role with source account restrictions

**Rationale**:
- Security pillar requires least-privilege access
- Trust policy must restrict to bedrock-agentcore.amazonaws.com service
- Source account validation prevents cross-account access

**Trust Policy Structure**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {"aws:SourceAccount": "${AWS::AccountId}"},
      "ArnLike": {"aws:SourceArn": "arn:aws:bedrock-agentcore:${AWS::Region}:${AWS::AccountId}:runtime/*"}
    }
  }]
}
```

**Required Permissions**:
- **Bedrock**: `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`
- **ECR**: `ecr:GetAuthorizationToken`, `ecr:BatchCheckLayerAvailability`, `ecr:GetDownloadUrlForLayer`, `ecr:BatchGetImage`
- **CloudWatch**: `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

**Security Conditions**:
- Region restrictions via `aws:RequestedRegion`
- Resource-specific ARN patterns
- KMS key access via service conditions

**Alternatives Considered**:
- Broader permissions: Rejected for security reasons
- Cross-account access: Rejected due to security requirements

### 4. CDK Implementation Strategy

**Decision**: Use L1 constructs with CloudFormation resources pending native CDK support

**Rationale**:
- `aws_cdk.aws_bedrockagentcore` module not available in current CDK v2
- L1 constructs provide immediate implementation path
- CloudFormation templates ensure proper resource management

**Implementation Approach**:
```python
runtime = CfnResource(
    self, "AgentRuntime",
    type="AWS::BedrockAgentCore::Runtime",
    properties={
        "AgentRuntimeArtifact": {
            "ContainerConfiguration": {
                "ContainerUri": container_uri,
                "Cpu": resource_config["cpu"],
                "MemoryLimitMiB": resource_config["memory"]
            }
        },
        "NetworkConfiguration": {
            "NetworkMode": "VPC",
            "NetworkModeConfig": {
                "Subnets": private_agent_subnets,
                "SecurityGroups": [runtime_security_group]
            }
        },
        "RoleArn": execution_role.role_arn
    }
)
```

**Alternatives Considered**:
- Wait for native CDK support: Rejected due to timeline requirements
- Direct API calls: Rejected due to infrastructure-as-code principles

## Monitoring and Observability Strategy

**CloudWatch Metrics**:
- Runtime status (ACTIVE/FAILED)
- Invocation count and error rate
- Latency percentiles (p50/p99)
- Container resource utilization

**Alerting**:
- Runtime failure alerts
- Resource utilization thresholds
- Performance degradation notifications

## Security Considerations

**Network Security**:
- VPC-only access for runtime communications
- Security groups restricting traffic to necessary ports
- Private subnets for runtime deployment

**IAM Security**:
- Least-privilege execution roles
- Source account and ARN restrictions
- Region-specific resource access

**Encryption**:
- TLS 1.2+ for all runtime communications
- KMS encryption for ECR repositories (existing)
- CloudWatch logs encryption (recommended)

## Open Questions Resolved

1. **Container resource limits**: Implemented environment-based allocation with monitoring
2. **VPC endpoint service names**: Confirmed dual endpoint configuration required
3. **IAM trust policy format**: Validated with source account restrictions
4. **CDK implementation path**: L1 constructs with CloudFormation resources
5. **DNS configuration**: Private DNS enabled for transparent access
6. **Multi-AZ deployment**: Automatic via subnet selection across availability zones

## Next Steps

1. Implement environment-based resource configuration in config.py
2. Add VPC endpoints to network_stack.py  
3. Create execution role in security_stack.py
4. Implement AgentCore stack with L1 constructs
5. Add monitoring and alerting configuration
6. Create contract tests for all outputs
7. Implement integration tests for deployment validation

## References

- AWS Well-Architected Framework Documentation
- AWS Bedrock AgentCore Service Documentation  
- AWS CDK v2 Python Reference
- Project AGENTS.md constitution requirements
- Existing VPC and security infrastructure patterns
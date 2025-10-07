# Research: AWS CDK Infrastructure for Bedrock Agent Platform

**Feature**: `002-create-python-application`  
**Date**: 2025-10-07  
**Status**: Complete

## Research Objectives
From Technical Context analysis, all primary dependencies and architectural patterns have been clarified through prior specification sessions. This research consolidates technology choices, validates CDK patterns, and documents best practices for AWS managed services integration.

## Technology Decisions

### 1. CDK Stack Organization Pattern

**Decision**: Modular stack architecture with cross-stack references  
**Rationale**: 
- Enables independent stack updates (network changes don't require database redeployment)
- Supports parallel development (teams can work on different stacks)
- Aligns with AWS Well-Architected operational excellence (smaller blast radius for changes)
- Facilitates environment-specific overrides (dev uses smaller RDS instances, prod uses larger)

**Alternatives Considered**:
- **Monolithic single stack**: Rejected - violates modularity principle, slow deployments, difficult rollbacks
- **Nested stacks**: Rejected - adds complexity, harder to test in isolation, CloudFormation template size limits
- **CDK Pipelines with stages**: Deferred to post-PoC - adds CI/CD complexity, requires CodePipeline setup

**Implementation Approach**:
```python
# Network stack exports VPC, subnet IDs via CfnOutput
network_stack = NetworkStack(app, "NetworkStack", env=env)

# Database stack imports network stack outputs via properties
database_stack = DatabaseStack(
    app, "DatabaseStack",
    vpc=network_stack.vpc,
    private_subnets=network_stack.private_data_subnets,
    env=env
)
```

### 2. VPC Endpoint Strategy

**Decision**: Interface endpoints for AWS services, gateway endpoint for S3  
**Rationale**:
- Interface endpoints (PrivateLink) required for Bedrock, Secrets Manager, ECR, CloudWatch (no internet gateway access)
- Gateway endpoints for S3 are free (no hourly charges) and support on-premises connectivity
- Reduces data transfer costs (traffic stays within AWS network)
- Meets security requirement: no public internet access for private resources

**Alternatives Considered**:
- **NAT Gateway for AWS service access**: Rejected - violates private subnet isolation, higher latency, data transfer costs
- **VPC Peering to shared services VPC**: Rejected - over-engineered for single-account PoC, adds networking complexity

**Cost Implications**:
- Interface endpoints: ~$7.20/month per endpoint × 6 endpoints = ~$43/month base cost
- Data processing: $0.01/GB (typically negligible for control plane operations)
- S3 gateway endpoint: $0 (free)

### 3. Aurora PostgreSQL vs RDS Multi-AZ

**Decision**: Aurora PostgreSQL with RDS Proxy  
**Rationale**:
- **AWS Bedrock AgentCore requirement**: Bedrock Agents with memory feature requires Aurora PostgreSQL for conversational context storage (AWS managed service limitation)
- Aurora provides superior availability with 6-way replication across 3 AZs (storage-level redundancy)
- Aurora meets RPO <1min/RTO 30min requirements (faster recovery than RDS Multi-AZ)
- RDS Proxy provides connection pooling (essential for Lambda/Fargate burst scaling)
- Aurora auto-scaling storage (10GB to 128TB) eliminates capacity planning
- Better performance for read-heavy workloads (up to 15 read replicas, low-latency read scaling)
- Aurora backtrack capability for point-in-time recovery without restore operations

**Alternatives Considered**:
- **RDS PostgreSQL Multi-AZ**: Rejected - not supported by Bedrock AgentCore memory feature, single standby replica (vs Aurora's 6 copies), slower failover (60-120s vs 30s), no storage auto-scaling
- **Aurora Serverless V2**: Rejected - higher cost for steady-state workloads, ACU scaling complexity, unpredictable billing
- **DynamoDB**: Rejected - data model includes relational entities (Agent-Model relationships), graph-like associations, not supported by Bedrock AgentCore

**Failover Testing**:
- Aurora automatic failover: typically 30-60 seconds (faster than RDS Multi-AZ)
- RDS Proxy maintains connection pool during failover (application-transparent)
- Planned chaos test: `aws rds failover-db-cluster` in staging environment

### 4. OpenSearch Sizing Strategy

**Decision**: 3-node cluster (2 in AZ-1, 1 in AZ-2) with dedicated master nodes for prod, 2-node for dev  
**Rationale**:
- 3 nodes minimum for production quorum (prevents split-brain scenarios)
- Dedicated master nodes (3×t3.small.search) provide cluster stability for >10 data nodes (future scale)
- 2-node dev cluster acceptable (no HA requirement for development environment)
- Instance type: r6g.large.search (memory-optimized for indexing, Graviton2 cost savings)

**Alternatives Considered**:
- **Single-node domain**: Rejected - no HA, violates multi-AZ requirement for prod
- **Elasticsearch on EC2**: Rejected - operational overhead (patching, upgrades), violates "managed services first" principle
- **CloudSearch**: Rejected - limited vector search capabilities needed for Bedrock agent embeddings

**Indexing Strategy**:
- Primary index: Agent runtime logs (timestamp, agent_id, conversation_id, tokens_used)
- Secondary index: Bedrock invocation metrics (model_id, latency_ms, input_tokens, output_tokens)
- Retention: 30 days hot storage (UltraWarm for long-term analytics deferred to prod optimization)

### 5. WAF Rule Configuration

**Decision**: AWS Managed Rules (Core, Known Bad Inputs) + custom rate limiting  
**Rationale**:
- Core Rule Set protects against OWASP Top 10 (SQL injection, XSS, path traversal)
- Known Bad Inputs blocks requests with malicious patterns (known CVE exploits)
- Rate limiting: 2000 requests per 5 minutes per IP (prevents DDoS, credential stuffing)
- Managed rules auto-update (AWS threat intelligence integration)

**Alternatives Considered**:
- **CloudFront with AWS WAF**: Deferred - adds CDN layer complexity, not required for API-first platform
- **Third-party WAF (Cloudflare, Imperva)**: Rejected - vendor lock-in, additional integration complexity, cost
- **Application-level rate limiting (Kong, Envoy)**: Rejected - shifts security left, operational overhead

**Cost**: ~$5/month base + $1/million requests (negligible for PoC traffic volume)

### 6. Secrets Management Pattern

**Decision**: AWS Secrets Manager with automatic rotation for RDS, Parameter Store for non-sensitive config  
**Rationale**:
- Secrets Manager supports automatic password rotation for RDS (Lambda function auto-generated)
- Versioning enables safe rollback (previous secret versions retained for 7 days)
- VPC endpoint ensures private subnet access (no NAT gateway required)
- Parameter Store for environment config (region, CIDR blocks) - no rotation overhead

**Alternatives Considered**:
- **Parameter Store SecureString only**: Rejected - manual rotation, no integration with RDS/Aurora
- **HashiCorp Vault**: Rejected - operational complexity (HA Vault cluster), over-engineered for PoC
- **Environment variables in ECS task definitions**: Rejected - violates "no secrets in code/config" principle

**Rotation Schedule**:
- RDS master password: 90 days (configurable via CDK `automaticallyAfter` property)
- Application API keys: Manual rotation (deferred to production security hardening)

### 7. CDK Testing Strategy

**Decision**: Three-tier testing (contract, integration, unit) with CDK Assertions  
**Rationale**:
- Contract tests validate stack outputs (VPC ID, subnet IDs, security group IDs) - critical for cross-stack references
- Integration tests use CDK `Template.fromStack()` to assert resource properties (encryption enabled, multi-AZ configured)
- Unit tests for custom constructs (L3 constructs wrapping common patterns)

**Test Framework**:
```python
# Contract test example
def test_network_stack_exports_vpc_id():
    app = cdk.App()
    stack = NetworkStack(app, "TestStack")
    template = Template.from_stack(stack)
    
    # Assert VPC exists with correct CIDR
    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.0.0.0/16"
    })
    
    # Assert VPC ID exported for cross-stack reference
    outputs = template.find_outputs("*", {})
    assert "VpcId" in outputs
```

**Alternatives Considered**:
- **CloudFormation template snapshots**: Rejected - brittle tests (breaks on unrelated changes), poor error messages
- **Manual testing only**: Rejected - violates code quality principle (80% coverage requirement)
- **End-to-end deployment tests**: Deferred to CI/CD pipeline (requires AWS account, slow feedback loop)

### 8. Environment Parameterization

**Decision**: CDK context variables + environment-specific configuration files  
**Rationale**:
- CDK context (`cdk.json`) for deployment-time parameters (account, region)
- Python dataclasses for environment-specific configs (instance sizes, retention periods)
- Type-safe configuration (Pydantic validation) prevents misconfigurations
- Supports local development (`cdk synth --context env=dev`), CI/CD (`cdk deploy --context env=prod`)

**Configuration Structure**:
```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class EnvironmentConfig:
    env_name: Literal["dev", "staging", "prod"]
    vpc_cidr: str
    rds_instance_class: str
    opensearch_instance_type: str
    opensearch_instance_count: int
    cloudtrail_retention_days: int

dev_config = EnvironmentConfig(
    env_name="dev",
    vpc_cidr="10.0.0.0/16",
    rds_instance_class="db.t4g.medium",
    opensearch_instance_type="t3.small.search",
    opensearch_instance_count=2,
    cloudtrail_retention_days=30
)

prod_config = EnvironmentConfig(
    env_name="prod",
    vpc_cidr="10.0.0.0/16",
    rds_instance_class="db.r6g.xlarge",
    opensearch_instance_type="r6g.large.search",
    opensearch_instance_count=3,
    cloudtrail_retention_days=2555  # 7 years
)
```

**Alternatives Considered**:
- **AWS AppConfig**: Rejected - runtime configuration service, not deployment-time IaC parameters
- **Hardcoded values per environment branch**: Rejected - violates DRY principle, merge conflicts, drift risk
- **AWS CDK Environment context lookup**: Rejected - asynchronous lookups slow synthesis, CloudFormation dependency

### 9. Cognito User Pool for Authentication

**Decision**: Cognito User Pool with ALB authentication integration using OAuth 2.0 flow  
**Rationale**:
- Native ALB integration eliminates need for custom authentication middleware in application code
- Supports OAuth 2.0/OIDC standard flows (authorization code grant for web apps)
- Managed user directory with built-in security features (MFA, password policies, account recovery)
- Session management handled entirely by ALB (no application-level session store required)
- Scales automatically with user load (managed service, no capacity planning)
- Supports identity federation (can add Google, Facebook, SAML providers later without code changes)

**Alternatives Considered**:
- **Custom JWT validation in application**: Rejected - requires authentication middleware in every service, increases attack surface, difficult to audit
- **Third-party IdP only (e.g., Okta, Auth0)**: Deferred - Cognito can federate to external IdPs later, avoiding vendor lock-in while maintaining ALB integration
- **AWS IAM for user authentication**: Rejected - IAM designed for AWS resource access, not end-user authentication, no session management
- **API Gateway Lambda authorizer**: Rejected - requires API Gateway (not using for this architecture), adds latency vs ALB native auth

**Implementation Approach**:
```python
# Security stack creates User Pool and App Client
user_pool = cognito.UserPool(self, "UserPool",
    user_pool_name="bedrock-agents-users",
    password_policy=cognito.PasswordPolicy(
        min_length=12,
        require_uppercase=True,
        require_lowercase=True,
        require_digits=True,
        require_symbols=True
    ),
    mfa=cognito.Mfa.OPTIONAL,
    account_recovery=cognito.AccountRecovery.EMAIL_ONLY
)

user_pool_client = user_pool.add_client("ALBClient",
    o_auth=cognito.OAuthSettings(
        flows=cognito.OAuthFlows(authorization_code_grant=True),
        scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL, cognito.OAuthScope.PROFILE],
        callback_urls=[f"https://{alb.load_balancer_dns_name}/oauth2/idpresponse"]
    )
)

# Compute stack uses Cognito action in ALB listener rules
listener.add_action("AuthenticateCognito",
    action=elbv2.ListenerAction.authenticate_cognito(
        user_pool=user_pool,
        user_pool_client=user_pool_client,
        user_pool_domain=user_pool_domain,
        next=elbv2.ListenerAction.forward([target_group])
    )
)
```

**Security Considerations**:
- User Pool domain: Use custom domain with ACM certificate (not Cognito prefix domain) for production
- Token validation: ALB validates ID token signature automatically, no application logic needed
- Session duration: ALB session cookie TTL configurable (default 7 days, recommend 24 hours for security)
- Logout: Requires custom logout endpoint to invalidate Cognito session and ALB cookie

## Best Practices & Patterns

### CDK L2 Construct Preferences
- Use L2 constructs (e.g., `ec2.Vpc`, `rds.DatabaseInstance`) for readability and safety
- L1 constructs (e.g., `CfnVpc`) only when L2 missing (rare) or fine-grained control required (escape hatch)
- Custom L3 constructs for repeated patterns (e.g., `MultiAzVpcEndpoint` wrapping endpoint + security group)

### Security Group Design
- **Principle of least privilege**: Deny all by default, explicit allow rules only
- **Layered security groups**: ALB SG → ECS Service SG → RDS SG (progressive restriction)
- **No wildcard source IPs**: Use security group references (e.g., `sources=[alb_sg]`) instead of `0.0.0.0/0`
- **Separate management and data plane**: Dedicated SG for VPC endpoints, avoid reuse across tiers

### Tagging Strategy
All resources tagged with:
- `Project: "AgentCore"`
- `Environment: "dev|staging|prod"`
- `ManagedBy: "CDK"`
- `CostCenter: "Engineering"` (future allocation)
- Stack-specific tags: `Stack: "NetworkStack"` (auto-applied by CDK)

### CloudFormation Stack Dependencies
- Explicit dependencies via `add_dependency()` when implicit dependencies insufficient
- Avoid circular dependencies: Network → Security → Compute → Database (directed acyclic graph)
- Use `Fn.import_value()` sparingly (tight coupling, difficult stack deletion)

## Open Questions (Resolved)
All technical unknowns from specification have been resolved:
- ✅ RPO/RTO targets: 15min/30min (spec session 2025-10-07)
- ✅ S3 encryption: AWS managed KMS keys (spec session 2025-10-07)
- ✅ WAF protection: AWS Managed Rules + rate limiting (spec session 2025-10-07)
- ✅ CloudTrail retention: 7 years (spec session 2025-10-07)
- ✅ Configurable parameters: Environment name, region, CIDR, instance sizes (spec session 2025-10-07)
- ✅ CDK stack organization: Modular stacks with cross-stack references (this research)
- ✅ RDS vs Aurora: Aurora PostgreSQL with RDS Proxy (this research)
- ✅ OpenSearch sizing: 3-node prod, 2-node dev (this research)

## References
- [AWS CDK Best Practices](https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html)
- [AWS Well-Architected Framework - Reliability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html)
- [VPC Endpoints Pricing](https://aws.amazon.com/privatelink/pricing/)
- [Aurora PostgreSQL Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.AuroraPostgreSQL.html)
- [Aurora High Availability](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Concepts.AuroraHighAvailability.html)
- [OpenSearch Best Practices](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/bp.html)
- [AWS Managed Rules for WAF](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups.html)

---
**Research Complete** - Ready for Phase 1 (Design & Contracts)

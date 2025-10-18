"""
AWS Hackathon Security Stack

Manages:
- SSM Parameters (app config, endpoints)
- Cognito User Pool with RBAC groups
- User authentication and authorization
"""

from aws_cdk import (
    Stack,
    aws_ssm as ssm,
    aws_cognito as cognito,
    CfnOutput,
    Duration,
    RemovalPolicy,
    Tags,
)
from constructs import Construct


class SecurityStack(Stack):
    """Security stack with SSM parameters and Cognito User Pool"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: str = "dev",
        domain_name: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = environment
        self.domain_name = domain_name
        domain_prefix = f"bidopsai-{environment}"

        # SSM Parameters (existing functionality)
        self._create_ssm_parameters()

        # Create Cognito User Pool
        self.user_pool = self._create_user_pool()

        # Create User Pool Domain
        self.user_pool_domain = self.user_pool.add_domain(
            "UserPoolDomain",
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=domain_prefix),
        )

        # Create User Pool Client
        self.user_pool_client = self._create_user_pool_client()

        # Create User Groups for RBAC
        self._create_user_groups()

        # Create CloudFormation outputs
        self._create_outputs(domain_prefix)

        # Add tags
        Tags.of(self).add("Environment", environment)
        Tags.of(self).add("Project", "AWSHackathon")
        Tags.of(self).add("ManagedBy", "CDK")

    def _create_ssm_parameters(self) -> None:
        """Create SSM parameters for app configuration"""

        self.app_config_param = ssm.StringParameter(
            self,
            "AppConfigParam",
            parameter_name=f"/bidopsai/{self.env_name}/app/config",
            string_value='{"environment": "' + self.env_name + '", "version": "1.0"}',
            description="Application configuration",
        )

        self.endpoint_params = ssm.StringParameter(
            self,
            "EndpointParams",
            parameter_name=f"/bidopsai/{self.env_name}/endpoints",
            string_value=(
                '{"api": "https://api.example.com", '
                '"bedrock": "https://bedrock.us-east-1.amazonaws.com"}'
            ),
            description="Service endpoints",
        )

    def _create_user_pool(self) -> cognito.UserPool:
        """Create and configure Cognito User Pool with enhanced security"""

        return cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"bidopsai-users-{self.env_name}",
            # Sign-in configuration
            sign_in_aliases=cognito.SignInAliases(
                username=True,
                email=True,
                phone=False,
            ),
            sign_in_case_sensitive=False,
            # Self sign-up configuration
            self_sign_up_enabled=True,
            # Auto-verification
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            # Standard attributes
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                given_name=cognito.StandardAttribute(required=True, mutable=True),
                family_name=cognito.StandardAttribute(required=True, mutable=True),
                profile_picture=cognito.StandardAttribute(required=False, mutable=True),
                preferred_username=cognito.StandardAttribute(
                    required=False, mutable=True
                ),
            ),
            # Custom attributes
            custom_attributes={
                "preferred_language": cognito.StringAttribute(
                    min_len=2, max_len=10, mutable=True
                ),
                "theme_preference": cognito.StringAttribute(
                    min_len=2, max_len=20, mutable=True
                ),
            },
            # Password policy
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(3),
            ),
            # MFA configuration
            mfa=cognito.Mfa.OPTIONAL,
            mfa_second_factor=cognito.MfaSecondFactor(
                sms=True,
                otp=True,
            ),
            # Account recovery
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            # Email configuration
            email=cognito.UserPoolEmail.with_cognito(
                reply_to="noreply@"
                + (self.domain_name if self.domain_name else "bidopsai.local")
            ),
            # User invitation
            user_invitation=cognito.UserInvitationConfig(
                email_subject="Welcome to AWS Hackathon Platform",
                email_body=(
                    "Hello {username},<br/><br/>"
                    "You have been invited to join the AWS Hackathon Platform.<br/>"
                    "Your temporary password is: {####}<br/><br/>"
                    "Please sign in and change your password.<br/><br/>"
                    "Best regards,<br/>"
                    "AWS Hackathon Team"
                ),
            ),
            # User verification
            user_verification=cognito.UserVerificationConfig(
                email_subject="Verify your email for AWS Hackathon",
                email_body=(
                    "Thank you for signing up to AWS Hackathon Platform!<br/><br/>"
                    "Your verification code is: {####}<br/><br/>"
                    "Please enter this code to complete your registration."
                ),
                email_style=cognito.VerificationEmailStyle.CODE,
            ),
            # Deletion protection
            deletion_protection=self.env_name == "prod",
            # Removal policy
            removal_policy=(
                RemovalPolicy.RETAIN
                if self.env_name == "prod"
                else RemovalPolicy.DESTROY
            ),
        )

    def _create_user_pool_client(self) -> cognito.UserPoolClient:
        """Create and configure User Pool Client for web application"""

        return self.user_pool.add_client(
            "UserPoolClient",
            user_pool_client_name=f"bidopsai-web-{self.env_name}",
            # OAuth configuration
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=False,
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE,
                    cognito.OAuthScope.PHONE,
                ],
                callback_urls=self._get_callback_urls(),
                logout_urls=self._get_logout_urls(),
            ),
            # Supported identity providers
            # Note: Add GOOGLE after manually creating the Google identity provider
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO,
            ],
            # Auth flows
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                custom=False,
                admin_user_password=False,
            ),
            # Prevent user existence errors
            prevent_user_existence_errors=True,
            # Token validity
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30),
            # Generate secret
            generate_secret=False,
            # Read/write attributes
            read_attributes=cognito.ClientAttributes()
            .with_standard_attributes(
                email=True,
                email_verified=True,
                given_name=True,
                family_name=True,
                profile_picture=True,
                preferred_username=True,
            )
            .with_custom_attributes("preferred_language", "theme_preference"),
            write_attributes=cognito.ClientAttributes()
            .with_standard_attributes(
                email=True,
                given_name=True,
                family_name=True,
                profile_picture=True,
                preferred_username=True,
            )
            .with_custom_attributes("preferred_language", "theme_preference"),
        )

    def _create_user_groups(self) -> None:
        """Create user groups for role-based access control"""

        # ADMIN Group - Full access to everything
        cognito.CfnUserPoolGroup(
            self,
            "AdminGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="ADMIN",
            description="Full access to all features and settings",
            precedence=1,
        )

        # DRAFTER Group - Can continue process till QA
        cognito.CfnUserPoolGroup(
            self,
            "DrafterGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="DRAFTER",
            description="Can work on drafts up to QA process",
            precedence=2,
        )

        # BIDDER Group - Full agentic flow + local KBs
        cognito.CfnUserPoolGroup(
            self,
            "BidderGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="BIDDER",
            description="Full workflow access and local knowledge base management",
            precedence=3,
        )

        # KB_ADMIN Group - Full KB access
        cognito.CfnUserPoolGroup(
            self,
            "KBAdminGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="KB_ADMIN",
            description="Full CRUD access to all knowledge bases",
            precedence=4,
        )

        # KB_VIEW Group - Read-only KB access
        cognito.CfnUserPoolGroup(
            self,
            "KBViewGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="KB_VIEW",
            description="Read-only access to knowledge bases",
            precedence=5,
        )

    def _get_callback_urls(self) -> list[str]:
        """Get callback URLs based on environment"""

        if self.env_name == "prod":
            if self.domain_name:
                return [
                    f"https://{self.domain_name}/callback",
                    f"https://app.{self.domain_name}/callback",
                ]
            return ["https://app.example.com/callback"]
        if self.env_name == "staging":
            if self.domain_name:
                return [f"https://staging.{self.domain_name}/callback"]
            return ["https://staging.example.com/callback"]
        # dev
        urls = [
            "http://localhost:3000/callback",
            "http://localhost:3000/api/auth/callback/cognito",
        ]
        # Add domain URLs if provided (for dev testing with real domain)
        if self.domain_name:
            urls.extend(
                [
                    f"https://{self.domain_name}/callback",
                    f"https://www.{self.domain_name}/callback",
                    f"https://{self.domain_name}/api/auth/callback/cognito",
                    f"https://www.{self.domain_name}/api/auth/callback/cognito",
                ]
            )
        return urls

    def _get_logout_urls(self) -> list[str]:
        """Get logout URLs based on environment"""

        if self.env_name == "prod":
            if self.domain_name:
                return [
                    f"https://{self.domain_name}",
                    f"https://{self.domain_name}/signin",
                ]
            return ["https://app.example.com", "https://app.example.com/signin"]
        if self.env_name == "staging":
            if self.domain_name:
                return [
                    f"https://staging.{self.domain_name}",
                    f"https://staging.{self.domain_name}/signin",
                ]
            return ["https://staging.example.com", "https://staging.example.com/signin"]
        # dev
        urls = [
            "http://localhost:3000",
            "http://localhost:3000/signin",
        ]
        # Add domain URLs if provided (for dev testing with real domain)
        if self.domain_name:
            urls.extend(
                [
                    f"https://{self.domain_name}",
                    f"https://www.{self.domain_name}",
                    f"https://{self.domain_name}/signin",
                    f"https://www.{self.domain_name}/signin",
                ]
            )
        return urls

    def _create_outputs(self, domain_prefix: str) -> None:
        """Create CloudFormation outputs"""

        # SSM Parameter outputs
        CfnOutput(
            self,
            "AppConfigParamName",
            value=self.app_config_param.parameter_name,
            description="App config parameter name",
            export_name=f"AppConfigParamName-{self.env_name}",
        )

        # Cognito outputs
        CfnOutput(
            self,
            "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID",
            export_name=f"UserPoolId-{self.env_name}",
        )

        CfnOutput(
            self,
            "UserPoolArn",
            value=self.user_pool.user_pool_arn,
            description="Cognito User Pool ARN",
            export_name=f"UserPoolArn-{self.env_name}",
        )

        CfnOutput(
            self,
            "UserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID",
            export_name=f"UserPoolClientId-{self.env_name}",
        )

        CfnOutput(
            self,
            "UserPoolDomain",
            value=f"{domain_prefix}.auth.{self.region}.amazoncognito.com",
            description="Cognito User Pool Domain",
            export_name=f"UserPoolDomain-{self.env_name}",
        )

        CfnOutput(
            self,
            "CognitoRegion",
            value=self.region,
            description="AWS Region for Cognito",
            export_name=f"CognitoRegion-{self.env_name}",
        )

from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_cognito as cognito,
    CfnOutput,
)
from constructs import Construct


class SecurityStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # IAM Execution Role for Bedrock AgentCore
        self.agentcore_execution_role = iam.Role(
            self,
            "AgentCoreExecutionRole",
            role_name="bedrock-agentcore-execution-role",
            assumed_by=iam.ServicePrincipal(
                "bedrock-agentcore.amazonaws.com",
                conditions={
                    "StringEquals": {"aws:SourceAccount": Stack.of(self).account},
                    "ArnLike": {
                        "aws:SourceArn": (
                            f"arn:aws:bedrock-agentcore:"
                            f"{Stack.of(self).region}:{Stack.of(self).account}:runtime/*"
                        )
                    },
                },
            ),
            description="Execution role for Bedrock AgentCore runtimes",
        )

        self.agentcore_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockModelAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=["arn:aws:bedrock:*::foundation-model/*"],
                conditions={
                    "StringEquals": {"aws:RequestedRegion": Stack.of(self).region}
                },
            )
        )

        self.agentcore_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="ECRImageAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                ],
                resources=["*"],
            )
        )

        self.agentcore_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchLogsAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    (
                        f"arn:aws:logs:{Stack.of(self).region}:{Stack.of(self).account}:"
                        f"log-group:/aws/bedrock-agentcore/*"
                    )
                ],
            )
        )

        self.agentcore_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="SecretsManagerAccess",
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    (
                        f"arn:aws:secretsmanager:{Stack.of(self).region}:"
                        f"{Stack.of(self).account}:secret:agentcore/*"
                    )
                ],
                conditions={
                    "StringEquals": {
                        "secretsmanager:ResourceTag/Project": "aws-hackathon"
                    }
                },
            )
        )

        self.agentcore_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="KMSDecryptAccess",
                effect=iam.Effect.ALLOW,
                actions=["kms:Decrypt", "kms:DescribeKey"],
                resources=[
                    f"arn:aws:kms:{Stack.of(self).region}:{Stack.of(self).account}:key/*"
                ],
                conditions={
                    "StringEquals": {
                        "kms:ViaService": [
                            f"ecr.{Stack.of(self).region}.amazonaws.com",
                            f"secretsmanager.{Stack.of(self).region}.amazonaws.com",
                        ]
                    }
                },
            )
        )

        # SSM Parameters
        self.app_config_param = ssm.StringParameter(
            self,
            "AppConfigParam",
            parameter_name="/hackathon/app/config",
            string_value='{"environment": "dev", "version": "1.0"}',
            description="Application configuration",
        )

        self.endpoint_params = ssm.StringParameter(
            self,
            "EndpointParams",
            parameter_name="/hackathon/endpoints",
            string_value=(
                '{"api": "https://api.example.com", '
                '"bedrock": "https://bedrock.us-east-1.amazonaws.com"}'
            ),
            description="Service endpoints",
        )

        # Cognito User Pool
        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name="hackathon-users",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
        )

        # Outputs
        CfnOutput(
            self,
            "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID",
            export_name="UserPoolId",
        )

        CfnOutput(
            self,
            "AppConfigParamName",
            value=self.app_config_param.parameter_name,
            description="App config parameter name",
            export_name="AppConfigParamName",
        )

        CfnOutput(
            self,
            "AgentCoreExecutionRoleArn",
            value=self.agentcore_execution_role.role_arn,
            description="Bedrock AgentCore execution role ARN",
            export_name="AgentCoreExecutionRoleArn",
        )

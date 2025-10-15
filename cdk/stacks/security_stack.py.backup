from aws_cdk import (
    Stack,
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
    aws_cognito as cognito,
    CfnOutput,
)
from constructs import Construct


class SecurityStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # SSM Parameters
        self.app_config_param = ssm.StringParameter(
            self, "AppConfigParam",
            parameter_name="/hackathon/app/config",
            string_value='{"environment": "dev", "version": "1.0"}',
            description="Application configuration"
        )

        self.endpoint_params = ssm.StringParameter(
            self, "EndpointParams",
            parameter_name="/hackathon/endpoints",
            string_value='{"api": "https://api.example.com", "bedrock": "https://bedrock.us-east-1.amazonaws.com"}',
            description="Service endpoints"
        )

        # Cognito User Pool
        self.user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name="hackathon-users",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            )
        )

        # Outputs
        CfnOutput(
            self, "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID",
            export_name="UserPoolId"
        )

        CfnOutput(
            self, "AppConfigParamName",
            value=self.app_config_param.parameter_name,
            description="App config parameter name",
            export_name="AppConfigParamName"
        )
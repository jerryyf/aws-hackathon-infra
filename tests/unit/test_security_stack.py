import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
from cdk.stacks.security_stack import SecurityStack


def test_security_stack_cognito_created():
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Cognito::UserPool", 1)
    template.has_resource_properties(
        "AWS::Cognito::UserPool", {"UserPoolName": "bidopsai-users-dev"}
    )


def test_security_stack_password_policy():
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::Cognito::UserPool",
        {
            "Policies": {
                "PasswordPolicy": {
                    "MinimumLength": 12,
                    "RequireLowercase": True,
                    "RequireNumbers": True,
                    "RequireSymbols": True,
                    "RequireUppercase": True,
                    "TemporaryPasswordValidityDays": 3,
                }
            }
        },
    )


def test_security_stack_mfa_optional():
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::Cognito::UserPool", {"MfaConfiguration": "OPTIONAL"}
    )


def test_security_stack_user_groups_created():
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Cognito::UserPoolGroup", 5)

    template.has_resource_properties(
        "AWS::Cognito::UserPoolGroup",
        {
            "GroupName": "ADMIN",
            "Precedence": 1,
            "Description": "Full access to all features and settings",
        },
    )

    template.has_resource_properties(
        "AWS::Cognito::UserPoolGroup", {"GroupName": "DRAFTER", "Precedence": 2}
    )

    template.has_resource_properties(
        "AWS::Cognito::UserPoolGroup", {"GroupName": "BIDDER", "Precedence": 3}
    )

    template.has_resource_properties(
        "AWS::Cognito::UserPoolGroup", {"GroupName": "KB_ADMIN", "Precedence": 4}
    )

    template.has_resource_properties(
        "AWS::Cognito::UserPoolGroup", {"GroupName": "KB_VIEW", "Precedence": 5}
    )


def test_security_stack_user_pool_client_created():
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Cognito::UserPoolClient", 1)

    template.has_resource_properties(
        "AWS::Cognito::UserPoolClient",
        {"AllowedOAuthScopes": ["email", "openid", "profile", "phone"]},
    )

    template.has_resource_properties(
        "AWS::Cognito::UserPoolClient",
        {"AllowedOAuthFlows": ["code"], "AllowedOAuthFlowsUserPoolClient": True},
    )


def test_security_stack_user_pool_domain_created():
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Cognito::UserPoolDomain", 1)
    template.has_resource_properties(
        "AWS::Cognito::UserPoolDomain", {"Domain": "bidopsai-dev"}
    )


def test_security_stack_ssm_parameters_created():
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::SSM::Parameter", 2)

    template.has_resource_properties(
        "AWS::SSM::Parameter",
        {"Name": "/bidopsai/dev/app/config", "Description": "Application configuration"},
    )

    template.has_resource_properties(
        "AWS::SSM::Parameter",
        {"Name": "/bidopsai/dev/endpoints", "Description": "Service endpoints"},
    )


def test_security_stack_outputs():
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = Template.from_stack(stack)

    template.has_output("UserPoolId", {})
    template.has_output("UserPoolArn", {})
    template.has_output("UserPoolClientId", {})
    template.has_output("UserPoolDomain", {})
    template.has_output("CognitoRegion", {})
    template.has_output("AppConfigParamName", {})


def test_security_stack_prod_has_deletion_protection():
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="prod")
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::Cognito::UserPool", {"DeletionProtection": "ACTIVE"}
    )


def test_security_stack_dev_no_deletion_protection():
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::Cognito::UserPool", {"DeletionProtection": "INACTIVE"}
    )

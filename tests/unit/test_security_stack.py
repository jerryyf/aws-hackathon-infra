"""
Unit tests for SecurityStack Cognito configuration
"""
import sys
from pathlib import Path

# Add cdk directory to Python path
cdk_dir = Path(__file__).parent.parent.parent / "cdk"
sys.path.insert(0, str(cdk_dir))

import aws_cdk as cdk
from aws_cdk import assertions
from stacks.security_stack import SecurityStack


def test_security_stack_cognito_created():
    """Test that Cognito User Pool is created"""
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = assertions.Template.from_stack(stack)

    # Assert User Pool exists
    template.resource_count_is("AWS::Cognito::UserPool", 1)
    
    # Assert User Pool has correct name
    template.has_resource_properties("AWS::Cognito::UserPool", {
        "UserPoolName": "hackathon-users-dev"
    })


def test_security_stack_password_policy():
    """Test that password policy meets security requirements"""
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = assertions.Template.from_stack(stack)

    # Assert password policy
    template.has_resource_properties("AWS::Cognito::UserPool", {
        "Policies": {
            "PasswordPolicy": {
                "MinimumLength": 12,
                "RequireLowercase": True,
                "RequireNumbers": True,
                "RequireSymbols": True,
                "RequireUppercase": True,
                "TemporaryPasswordValidityDays": 3
            }
        }
    })


def test_security_stack_mfa_optional():
    """Test that MFA is optional"""
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = assertions.Template.from_stack(stack)

    # Assert MFA is optional
    template.has_resource_properties("AWS::Cognito::UserPool", {
        "MfaConfiguration": "OPTIONAL"
    })


def test_security_stack_user_groups_created():
    """Test that all 5 user groups are created"""
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = assertions.Template.from_stack(stack)

    # Assert 5 user groups exist
    template.resource_count_is("AWS::Cognito::UserPoolGroup", 5)
    
    # Assert ADMIN group
    template.has_resource_properties("AWS::Cognito::UserPoolGroup", {
        "GroupName": "ADMIN",
        "Precedence": 1,
        "Description": "Full access to all features and settings"
    })
    
    # Assert DRAFTER group
    template.has_resource_properties("AWS::Cognito::UserPoolGroup", {
        "GroupName": "DRAFTER",
        "Precedence": 2
    })
    
    # Assert BIDDER group
    template.has_resource_properties("AWS::Cognito::UserPoolGroup", {
        "GroupName": "BIDDER",
        "Precedence": 3
    })
    
    # Assert KB_ADMIN group
    template.has_resource_properties("AWS::Cognito::UserPoolGroup", {
        "GroupName": "KB_ADMIN",
        "Precedence": 4
    })
    
    # Assert KB_VIEW group
    template.has_resource_properties("AWS::Cognito::UserPoolGroup", {
        "GroupName": "KB_VIEW",
        "Precedence": 5
    })


def test_security_stack_user_pool_client_created():
    """Test that User Pool Client is created with OAuth"""
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = assertions.Template.from_stack(stack)

    # Assert User Pool Client exists
    template.resource_count_is("AWS::Cognito::UserPoolClient", 1)
    
    # Assert OAuth scopes (in correct order as CloudFormation outputs them)
    template.has_resource_properties("AWS::Cognito::UserPoolClient", {
        "AllowedOAuthScopes": [
            "email",
            "openid",
            "profile",
            "phone"
        ]
    })
    
    # Assert OAuth flows
    template.has_resource_properties("AWS::Cognito::UserPoolClient", {
        "AllowedOAuthFlows": ["code"],
        "AllowedOAuthFlowsUserPoolClient": True
    })


def test_security_stack_user_pool_domain_created():
    """Test that Cognito domain is created"""
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = assertions.Template.from_stack(stack)

    # Assert User Pool Domain exists
    template.resource_count_is("AWS::Cognito::UserPoolDomain", 1)
    
    # Assert domain prefix
    template.has_resource_properties("AWS::Cognito::UserPoolDomain", {
        "Domain": "hackathon-dev"
    })


def test_security_stack_ssm_parameters_created():
    """Test that SSM parameters are created"""
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = assertions.Template.from_stack(stack)

    # Assert SSM parameters exist
    template.resource_count_is("AWS::SSM::Parameter", 2)
    
    # Assert app config parameter
    template.has_resource_properties("AWS::SSM::Parameter", {
        "Name": "/hackathon/dev/app/config",
        "Description": "Application configuration"
    })
    
    # Assert endpoints parameter
    template.has_resource_properties("AWS::SSM::Parameter", {
        "Name": "/hackathon/dev/endpoints",
        "Description": "Service endpoints"
    })


def test_security_stack_outputs_created():
    """Test that CloudFormation outputs are created"""
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = assertions.Template.from_stack(stack)

    # Assert outputs exist
    template.has_output("UserPoolId", {})
    template.has_output("UserPoolArn", {})
    template.has_output("UserPoolClientId", {})
    template.has_output("UserPoolDomain", {})
    template.has_output("CognitoRegion", {})
    template.has_output("AppConfigParamName", {})


def test_security_stack_prod_has_deletion_protection():
    """Test that production environment has deletion protection"""
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="prod")
    template = assertions.Template.from_stack(stack)

    # Assert deletion protection is ACTIVE for prod
    template.has_resource_properties("AWS::Cognito::UserPool", {
        "DeletionProtection": "ACTIVE"
    })


def test_security_stack_dev_no_deletion_protection():
    """Test that dev environment does not have deletion protection"""
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = assertions.Template.from_stack(stack)

    # Assert deletion protection is INACTIVE for dev
    template.has_resource_properties("AWS::Cognito::UserPool", {
        "DeletionProtection": "INACTIVE"
    })


def test_security_stack_custom_attributes():
    """Test that custom attributes are configured"""
    app = cdk.App()
    stack = SecurityStack(app, "TestSecurityStack", environment="dev")
    template = assertions.Template.from_stack(stack)

    # Assert custom attributes exist
    template.has_resource_properties("AWS::Cognito::UserPool", {
        "Schema": assertions.Match.array_with([
            {
                "Name": "preferred_language",
                "AttributeDataType": "String",
                "Mutable": True,
                "StringAttributeConstraints": {
                    "MinLength": "2",
                    "MaxLength": "10"
                }
            },
            {
                "Name": "theme_preference",
                "AttributeDataType": "String",
                "Mutable": True,
                "StringAttributeConstraints": {
                    "MinLength": "2",
                    "MaxLength": "20"
                }
            }
        ])
    })

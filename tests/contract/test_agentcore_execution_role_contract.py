import pytest
from aws_cdk.assertions import Template, Match
from cdk.stacks.security_stack import SecurityStack
import aws_cdk as cdk


@pytest.fixture
def security_stack():
    app = cdk.App()
    stack = SecurityStack(
        app,
        "TestSecurityStack",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    return stack


def test_agentcore_execution_role_exists(security_stack):
    template = Template.from_stack(security_stack)
    
    template.resource_count_is("AWS::IAM::Role", 1)


def test_agentcore_execution_role_trust_policy(security_stack):
    template = Template.from_stack(security_stack)
    
    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "bedrock-agentcore.amazonaws.com"
                        },
                        "Condition": {
                            "StringEquals": {
                                "aws:SourceAccount": "123456789012"
                            },
                            "ArnLike": {
                                "aws:SourceArn": "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/*"
                            }
                        }
                    }
                ]
            }
        }
    )


def test_agentcore_execution_role_bedrock_permissions(security_stack):
    template = Template.from_stack(security_stack)
    
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with([
                    Match.object_like({
                        "Sid": "BedrockModelAccess",
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream"
                        ],
                        "Resource": "arn:aws:bedrock:*::foundation-model/*",
                        "Condition": {
                            "StringEquals": {
                                "aws:RequestedRegion": "us-east-1"
                            }
                        }
                    })
                ])
            }
        }
    )


def test_agentcore_execution_role_ecr_permissions(security_stack):
    template = Template.from_stack(security_stack)
    
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with([
                    Match.object_like({
                        "Sid": "ECRImageAccess",
                        "Effect": "Allow",
                        "Action": [
                            "ecr:GetAuthorizationToken",
                            "ecr:BatchCheckLayerAvailability",
                            "ecr:GetDownloadUrlForLayer",
                            "ecr:BatchGetImage"
                        ],
                        "Resource": "*"
                    })
                ])
            }
        }
    )


def test_agentcore_execution_role_cloudwatch_permissions(security_stack):
    template = Template.from_stack(security_stack)
    
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with([
                    Match.object_like({
                        "Sid": "CloudWatchLogsAccess",
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": "arn:aws:logs:us-east-1:123456789012:log-group:/aws/bedrock-agentcore/*"
                    })
                ])
            }
        }
    )


def test_agentcore_execution_role_secrets_manager_permissions(security_stack):
    template = Template.from_stack(security_stack)
    
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with([
                    Match.object_like({
                        "Sid": "SecretsManagerAccess",
                        "Effect": "Allow",
                        "Action": "secretsmanager:GetSecretValue",
                        "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:agentcore/*",
                        "Condition": {
                            "StringEquals": {
                                "secretsmanager:ResourceTag/Project": "aws-hackathon"
                            }
                        }
                    })
                ])
            }
        }
    )


def test_agentcore_execution_role_kms_permissions(security_stack):
    template = Template.from_stack(security_stack)
    
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with([
                    Match.object_like({
                        "Sid": "KMSDecryptAccess",
                        "Effect": "Allow",
                        "Action": ["kms:Decrypt", "kms:DescribeKey"],
                        "Resource": "arn:aws:kms:us-east-1:123456789012:key/*",
                        "Condition": {
                            "StringEquals": {
                                "kms:ViaService": [
                                    "ecr.us-east-1.amazonaws.com",
                                    "secretsmanager.us-east-1.amazonaws.com"
                                ]
                            }
                        }
                    })
                ])
            }
        }
    )


def test_agentcore_execution_role_output(security_stack):
    template = Template.from_stack(security_stack)
    
    outputs = template.find_outputs("AgentCoreExecutionRoleArn")
    assert len(outputs) == 1
    
    role_output = outputs["AgentCoreExecutionRoleArn"]
    assert role_output["Description"] == "Bedrock AgentCore execution role ARN"
    assert role_output["Export"]["Name"] == "AgentCoreExecutionRoleArn"
    assert "Value" in role_output

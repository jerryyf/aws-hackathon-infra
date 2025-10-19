import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
from cdk.stacks.compute_stack import ComputeStack
from cdk.stacks.network_stack import NetworkStack


def test_compute_stack_ecs_cluster_created():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::ECS::Cluster", 1)
    template.has_resource_properties(
        "AWS::ECS::Cluster", {"ClusterName": "bidopsai-cluster"}
    )


def test_compute_stack_bff_task_definition():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    from aws_cdk.assertions import Match

    template.has_resource_properties(
        "AWS::ECS::TaskDefinition",
        {
            "Cpu": "1024",
            "Memory": "2048",
            "NetworkMode": "awsvpc",
            "RequiresCompatibilities": ["FARGATE"],
            "ContainerDefinitions": [
                {
                    "Name": "bff",
                    "Image": "nginx:latest",
                    "Essential": True,
                    "PortMappings": [
                        {
                            "ContainerPort": 3000,
                            "Protocol": "tcp",
                        }
                    ],
                    "Environment": Match.array_with(
                        [
                            {"Name": "ENVIRONMENT", "Value": "test"},
                            {"Name": "LOG_LEVEL", "Value": "info"},
                        ]
                    ),
                }
            ],
        },
    )


def test_compute_stack_agent_task_definition():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    from aws_cdk.assertions import Match

    template.has_resource_properties(
        "AWS::ECS::TaskDefinition",
        {
            "Cpu": "1024",
            "Memory": "2048",
            "NetworkMode": "awsvpc",
            "RequiresCompatibilities": ["FARGATE"],
            "ContainerDefinitions": [
                {
                    "Name": "agent",
                    "Image": "nginx:latest",
                    "Essential": True,
                    "PortMappings": [
                        {
                            "ContainerPort": 8080,
                            "Protocol": "tcp",
                        }
                    ],
                    "Environment": Match.array_with(
                        [
                            {"Name": "ENVIRONMENT", "Value": "test"},
                            {"Name": "LOG_LEVEL", "Value": "info"},
                        ]
                    ),
                }
            ],
        },
    )


def test_compute_stack_outputs():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_output("EcsClusterName", {"Export": {"Name": "EcsClusterName"}})


def test_compute_stack_without_network_stack():
    app = cdk.App()
    stack = ComputeStack(app, "TestComputeStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::VPC", 1)
    template.resource_count_is("AWS::ECS::Cluster", 1)


def test_compute_stack_cluster_container_insights():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ECS::Cluster",
        {"ClusterSettings": [{"Name": "containerInsights", "Value": "enabled"}]},
    )


def test_compute_stack_cluster_arn_output():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_output("EcsClusterArn", {"Export": {"Name": "EcsClusterArn"}})


def test_compute_stack_task_execution_role_permissions():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    }
                ]
            }
        },
    )

    from aws_cdk.assertions import Match

    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        {
                            "Action": [
                                "ecr:GetAuthorizationToken",
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                            ],
                            "Effect": "Allow",
                            "Resource": "*",
                        },
                        {
                            "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                            "Effect": "Allow",
                            "Resource": "*",
                        },
                        {
                            "Action": ["ssm:GetParameter", "ssm:GetParameters"],
                            "Effect": "Allow",
                            "Resource": "*",
                        },
                    ]
                )
            }
        },
    )


def test_compute_stack_security_groups():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::SecurityGroup", 2)

    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "GroupDescription": "Security group for BFF tasks",
        },
    )

    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "GroupDescription": "Security group for AgentCore tasks",
        },
    )


def test_compute_stack_security_group_egress_rules():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    from aws_cdk.assertions import Match

    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "SecurityGroupEgress": Match.array_with(
                [
                    {
                        "CidrIp": "0.0.0.0/0",
                        "Description": "Allow outbound HTTPS to VPC endpoints",
                        "FromPort": 443,
                        "IpProtocol": "tcp",
                        "ToPort": 443,
                    }
                ]
            )
        },
    )


def test_compute_stack_bff_task_role_permissions():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    from aws_cdk.assertions import Match

    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        {
                            "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                            "Effect": "Allow",
                            "Resource": Match.object_like(
                                {"Fn::Join": Match.any_value()}
                            ),
                        },
                        {
                            "Action": ["ssm:GetParameter", "ssm:GetParameters"],
                            "Effect": "Allow",
                            "Resource": Match.object_like(
                                {"Fn::Join": Match.any_value()}
                            ),
                        },
                        {
                            "Action": [
                                "logs:DeleteLogGroup",
                                "logs:DeleteLogStream",
                                "ssm:DeleteParameter",
                                "ssm:DeleteParameters",
                                "iam:*",
                                "ec2:*",
                                "ecs:DeleteCluster",
                                "ecs:DeleteService",
                                "ecs:UpdateService",
                                "ecs:DeregisterTaskDefinition",
                            ],
                            "Effect": "Deny",
                            "Resource": "*",
                        },
                    ]
                )
            },
            "Roles": Match.array_with(
                [{"Ref": Match.string_like_regexp(r"BffTaskRole.*")}]
            ),
        },
    )


def test_compute_stack_agent_task_role_permissions():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    from aws_cdk.assertions import Match

    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        {
                            "Action": [
                                "bedrock-agent-runtime:InvokeAgent",
                                "bedrock-runtime:InvokeModel",
                            ],
                            "Effect": "Allow",
                            "Resource": Match.array_with(
                                [Match.object_like({"Fn::Join": Match.any_value()})]
                            ),
                        },
                        {
                            "Action": ["s3:GetObject", "s3:PutObject"],
                            "Effect": "Allow",
                            "Resource": Match.string_like_regexp(
                                r"arn:aws:s3:::bidopsai-.+-agent-data/\*"
                            ),
                        },
                        {
                            "Action": "s3:ListBucket",
                            "Effect": "Allow",
                            "Resource": Match.string_like_regexp(
                                r"arn:aws:s3:::bidopsai-.+-agent-data"
                            ),
                        },
                        {
                            "Action": ["ssm:GetParameter", "ssm:GetParameters"],
                            "Effect": "Allow",
                            "Resource": Match.object_like(
                                {"Fn::Join": Match.any_value()}
                            ),
                        },
                        {
                            "Action": [
                                "s3:DeleteBucket",
                                "s3:DeleteObject",
                                "ssm:DeleteParameter",
                                "ssm:DeleteParameters",
                                "bedrock:DeleteAgent",
                                "bedrock:UpdateAgent",
                                "iam:*",
                                "ec2:*",
                                "ecs:DeleteCluster",
                                "ecs:DeleteService",
                                "ecs:UpdateService",
                                "ecs:DeregisterTaskDefinition",
                            ],
                            "Effect": "Deny",
                            "Resource": "*",
                        },
                    ]
                )
            },
            "Roles": Match.array_with(
                [{"Ref": Match.string_like_regexp(r"AgentTaskRole.*")}]
            ),
        },
    )


def test_compute_stack_cloudwatch_log_groups():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::Logs::LogGroup",
        {
            "LogGroupName": "/ecs/bidopsai/bff-test",
            "RetentionInDays": 7,
        },
    )

    template.has_resource_properties(
        "AWS::Logs::LogGroup",
        {
            "LogGroupName": "/ecs/bidopsai/agent-test",
            "RetentionInDays": 7,
        },
    )


def test_compute_stack_task_definition_arn_outputs():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")
    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_output(
        "BffTaskDefinitionArn", {"Export": {"Name": "BffTaskDefinitionArn"}}
    )
    template.has_output(
        "AgentTaskDefinitionArn", {"Export": {"Name": "AgentTaskDefinitionArn"}}
    )


def test_compute_stack_bff_target_group(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ElasticLoadBalancingV2::TargetGroup",
        {
            "Port": 3000,
            "Protocol": "HTTP",
            "TargetType": "ip",
            "HealthCheckPath": "/api/health",
            "HealthCheckIntervalSeconds": 30,
            "HealthyThresholdCount": 2,
            "UnhealthyThresholdCount": 3,
        },
    )


def test_compute_stack_service_discovery_namespace(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ServiceDiscovery::PrivateDnsNamespace",
        {"Name": "bidopsai.local"},
    )


def test_compute_stack_bff_service(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ECS::Service",
        {
            "ServiceName": Match.absent(),
            "DesiredCount": 2,
            "LaunchType": "FARGATE",
            "DeploymentConfiguration": {
                "MaximumPercent": 200,
                "MinimumHealthyPercent": 50,
            },
        },
    )


def test_compute_stack_agent_service(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::ECS::Service", 2)

    template.has_resource_properties(
        "AWS::ECS::Service",
        {
            "DesiredCount": 2,
            "LaunchType": "FARGATE",
            "ServiceRegistries": Match.any_value(),
        },
    )


def test_compute_stack_bff_auto_scaling(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ApplicationAutoScaling::ScalableTarget",
        {
            "MinCapacity": 2,
            "MaxCapacity": 10,
            "ServiceNamespace": "ecs",
        },
    )

    template.has_resource_properties(
        "AWS::ApplicationAutoScaling::ScalingPolicy",
        {
            "PolicyType": "TargetTrackingScaling",
            "TargetTrackingScalingPolicyConfiguration": {
                "PredefinedMetricSpecification": {
                    "PredefinedMetricType": Match.string_like_regexp("ECS.*Utilization")
                },
                "ScaleInCooldown": 300,
                "ScaleOutCooldown": 300,
            },
        },
    )


def test_compute_stack_service_outputs(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_output("AgentServiceArn", {})
    template.has_output("ServiceDiscoveryNamespaceId", {})
    template.has_output("AgentCoreServiceDiscoveryDns", {})


def test_compute_stack_sns_alarm_topic(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::SNS::Topic", {"DisplayName": "test-ECS-Alarms"}
    )


def test_compute_stack_bff_cpu_alarm(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "AlarmDescription": "Alert when BFF service CPU exceeds 85%",
            "Threshold": 85,
            "EvaluationPeriods": 2,
            "DatapointsToAlarm": 2,
            "ComparisonOperator": "GreaterThanThreshold",
            "TreatMissingData": "notBreaching",
        },
    )


def test_compute_stack_bff_memory_alarm(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "AlarmDescription": "Alert when BFF service memory exceeds 85%",
            "Threshold": 85,
            "EvaluationPeriods": 2,
            "DatapointsToAlarm": 2,
            "ComparisonOperator": "GreaterThanThreshold",
            "TreatMissingData": "notBreaching",
        },
    )


def test_compute_stack_bff_task_count_alarm(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "AlarmDescription": "Alert when BFF service has less than 1 running task",
            "Threshold": 1,
            "EvaluationPeriods": 2,
            "DatapointsToAlarm": 2,
            "ComparisonOperator": "LessThanThreshold",
            "TreatMissingData": "breaching",
        },
    )


def test_compute_stack_agent_cpu_alarm(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "AlarmDescription": "Alert when AgentCore service CPU exceeds 85%",
            "Threshold": 85,
            "EvaluationPeriods": 2,
            "DatapointsToAlarm": 2,
            "ComparisonOperator": "GreaterThanThreshold",
            "TreatMissingData": "notBreaching",
        },
    )


def test_compute_stack_agent_memory_alarm(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "AlarmDescription": "Alert when AgentCore service memory exceeds 85%",
            "Threshold": 85,
            "EvaluationPeriods": 2,
            "DatapointsToAlarm": 2,
            "ComparisonOperator": "GreaterThanThreshold",
            "TreatMissingData": "notBreaching",
        },
    )


def test_compute_stack_agent_task_count_alarm(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "AlarmDescription": "Alert when AgentCore service has less than 2 running tasks",
            "Threshold": 2,
            "EvaluationPeriods": 2,
            "DatapointsToAlarm": 2,
            "ComparisonOperator": "LessThanThreshold",
            "TreatMissingData": "breaching",
        },
    )


def test_compute_stack_alb_response_time_alarm(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "AlarmDescription": "Alert when ALB target response time exceeds 3 seconds",
            "Threshold": 3,
            "EvaluationPeriods": 2,
            "DatapointsToAlarm": 2,
            "ComparisonOperator": "GreaterThanThreshold",
            "TreatMissingData": "notBreaching",
        },
    )


def test_compute_stack_alb_unhealthy_target_alarm(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "AlarmDescription": "Alert when ALB has unhealthy targets",
            "Threshold": 1,
            "EvaluationPeriods": 2,
            "DatapointsToAlarm": 2,
            "ComparisonOperator": "GreaterThanOrEqualToThreshold",
            "TreatMissingData": "notBreaching",
        },
    )


def test_compute_stack_alb_5xx_alarm(network_stack, test_app):
    stack = ComputeStack(test_app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "AlarmDescription": "Alert when ALB target 5XX error count exceeds 10 in 5 minutes",
            "Threshold": 10,
            "EvaluationPeriods": 2,
            "DatapointsToAlarm": 2,
            "ComparisonOperator": "GreaterThanThreshold",
            "TreatMissingData": "notBreaching",
        },
    )


def test_compute_stack_accepts_all_stack_dependencies():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")

    from cdk.stacks.storage_stack import StorageStack
    from cdk.stacks.security_stack import SecurityStack
    from cdk.stacks.database_stack import DatabaseStack

    storage_stack = StorageStack(app, "TestStorageStack")
    security_stack = SecurityStack(app, "TestSecurityStack", environment="test")
    database_stack = DatabaseStack(
        app, "TestDatabaseStack", network_stack=network_stack
    )

    stack = ComputeStack(
        app,
        "TestComputeStack",
        network_stack=network_stack,
        storage_stack=storage_stack,
        security_stack=security_stack,
        database_stack=database_stack,
    )
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::ECS::Cluster", 1)


def test_compute_stack_s3_bucket_arn_uses_storage_stack():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")

    from cdk.stacks.storage_stack import StorageStack

    storage_stack = StorageStack(app, "TestStorageStack")

    stack = ComputeStack(
        app,
        "TestComputeStack",
        network_stack=network_stack,
        storage_stack=storage_stack,
    )
    template = Template.from_stack(stack)

    from aws_cdk.assertions import Match

    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        {
                            "Action": ["s3:GetObject", "s3:PutObject"],
                            "Effect": "Allow",
                            "Resource": Match.object_like(
                                {"Fn::Join": Match.any_value()}
                            ),
                        }
                    ]
                )
            },
            "Roles": Match.array_with(
                [{"Ref": Match.string_like_regexp(r"AgentTaskRole.*")}]
            ),
        },
    )


def test_compute_stack_s3_bucket_arn_fallback_without_storage_stack():
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack")

    stack = ComputeStack(app, "TestComputeStack", network_stack=network_stack)
    template = Template.from_stack(stack)

    from aws_cdk.assertions import Match

    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        {
                            "Action": ["s3:GetObject", "s3:PutObject"],
                            "Effect": "Allow",
                            "Resource": Match.string_like_regexp(
                                r"arn:aws:s3:::bidopsai-.+-agent-data/\*"
                            ),
                        }
                    ]
                )
            },
            "Roles": Match.array_with(
                [{"Ref": Match.string_like_regexp(r"AgentTaskRole.*")}]
            ),
        },
    )

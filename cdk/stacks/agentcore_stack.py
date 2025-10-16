import logging
from aws_cdk import (
    Stack,
    CfnOutput,
    CfnResource,
    RemovalPolicy,
    Duration,
    aws_cloudwatch as cloudwatch,
    aws_logs as logs,
    aws_kms as kms,
)
from constructs import Construct

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AgentCoreStack(Stack):
    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        scope: Construct,
        construct_id: str,
        network_stack,
        security_stack,
        storage_stack,
        agentcore_config: dict,
        environment: str = "test",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        logger.info(
            "[AgentCoreStack] Initializing AgentCore stack for environment: %s",
            environment,
        )

        self._validate_environment(environment)
        self._validate_dependencies(network_stack, security_stack, storage_stack)
        self._validate_config(agentcore_config)

        network_mode = agentcore_config.get("network_mode", "PUBLIC")
        self._validate_network_mode(network_mode)

        if network_mode == "VPC" and network_stack is None:
            raise ValueError(
                "network_mode is 'VPC' but network_stack is None. "
                "VPC mode requires a valid network_stack parameter."
            )

        logger.info(
            "[AgentCoreStack] Configuration validated: network_mode=%s",
            network_mode,
        )

        runtime_name = f"hackathon-agent-{environment}-{Stack.of(self).region}"
        logger.info("[AgentCoreStack] Creating runtime: %s", runtime_name)

        logger.info("[AgentCoreStack] Creating CloudWatch log group")
        log_group = logs.LogGroup(
            self,
            "AgentRuntimeLogGroup",
            log_group_name=f"/aws/bedrock-agentcore/{environment}/{runtime_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
            encryption_key=kms.Alias.from_alias_name(
                self, "LogsKmsKey", "alias/aws/logs"
            ),
        )
        logger.info("[AgentCoreStack] Log group created: %s", log_group.log_group_name)

        ecr_uri = (
            f"{Stack.of(self).account}.dkr.ecr.{Stack.of(self).region}"
            f".amazonaws.com/{storage_stack.ecr_repo.repository_name}:latest"
        )
        logger.info("[AgentCoreStack] Container URI: %s", ecr_uri)

        runtime_properties = {
            "AgentRuntimeName": runtime_name,
            "Description": f"AWS Hackathon AgentCore runtime ({network_mode} mode)",
            "AgentRuntimeArtifact": {
                "ContainerConfiguration": {
                    "ContainerUri": ecr_uri,
                }
            },
            "RoleArn": security_stack.agentcore_execution_role.role_arn,
            "Tags": {
                "Project": "aws-hackathon",
                "Environment": environment,
                "Owner": "platform-team",
                "CostCenter": "engineering",
                "ManagedBy": "cdk",
                "Stack": "agentcore-stack",
            },
        }

        if network_mode == "VPC":
            logger.info("[AgentCoreStack] Configuring VPC networking")
            agent_subnets = [
                subnet
                for subnet in network_stack.vpc.private_subnets
                if "PrivateAgent" in subnet.node.id
            ]

            if not agent_subnets:
                raise ValueError(
                    "network_mode is 'VPC' but no PrivateAgent subnets found in network_stack. "
                    "Ensure the VPC has subnets with 'PrivateAgent' in their ID."
                )

            logger.info(
                "[AgentCoreStack] Found %d PrivateAgent subnets", len(agent_subnets)
            )

            runtime_properties["NetworkConfiguration"] = {
                "NetworkMode": "VPC",
                "NetworkModeConfig": {
                    "Subnets": [subnet.subnet_id for subnet in agent_subnets],
                    "SecurityGroups": [
                        network_stack.agentcore_runtime_sg.security_group_id
                    ],
                },
            }
        else:
            logger.info("[AgentCoreStack] Configuring PUBLIC networking")
            runtime_properties["NetworkConfiguration"] = {"NetworkMode": "PUBLIC"}

        logger.info("[AgentCoreStack] Creating AgentCore runtime resource")
        self.agent_runtime = CfnResource(
            self,
            "AgentRuntime",
            type="AWS::BedrockAgentCore::Runtime",
            properties=runtime_properties,
        )
        logger.info("[AgentCoreStack] AgentCore runtime resource created")
        logger.info(
            "[AgentCoreStack] Deployment expectation: Runtime should reach ACTIVE status within 10 minutes (SC-001)"
        )

        logger.info("[AgentCoreStack] Setting up CloudWatch metrics and alarms")

        error_metric = cloudwatch.Metric(
            namespace="AWS/BedrockAgentCore",
            metric_name="RuntimeErrors",
            dimensions_map={"RuntimeName": runtime_name},
            statistic="Sum",
            period=Duration.minutes(5),
        )

        invocation_metric = cloudwatch.Metric(
            namespace="AWS/BedrockAgentCore",
            metric_name="RuntimeInvocations",
            dimensions_map={"RuntimeName": runtime_name},
            statistic="Sum",
            period=Duration.minutes(5),
        )

        error_rate_metric = cloudwatch.MathExpression(
            expression="(errors / invocations) * 100",
            using_metrics={"errors": error_metric, "invocations": invocation_metric},
            period=Duration.minutes(5),
        )

        cloudwatch.Alarm(
            self,
            "HighErrorRateAlarm",
            alarm_name=f"{runtime_name}-high-error-rate",
            alarm_description="AgentCore runtime error rate exceeds 5%",
            metric=error_rate_metric,
            threshold=5,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        latency_metric = cloudwatch.Metric(
            namespace="AWS/BedrockAgentCore",
            metric_name="RuntimeLatency",
            dimensions_map={"RuntimeName": runtime_name},
            statistic="p99",
            period=Duration.minutes(5),
        )

        cloudwatch.Alarm(
            self,
            "HighLatencyAlarm",
            alarm_name=f"{runtime_name}-high-latency",
            alarm_description="AgentCore runtime p99 latency exceeds 5000ms",
            metric=latency_metric,
            threshold=5000,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        logger.info("[AgentCoreStack] Creating CloudWatch dashboard")
        dashboard = cloudwatch.Dashboard(
            self,
            "AgentRuntimeDashboard",
            dashboard_name=f"{runtime_name}-dashboard",
        )

        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Runtime Invocations",
                left=[invocation_metric],
                width=12,
            ),
            cloudwatch.GraphWidget(
                title="Runtime Errors",
                left=[error_metric],
                width=12,
            ),
        )

        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Error Rate (%)",
                left=[error_rate_metric],
                width=12,
            ),
            cloudwatch.GraphWidget(
                title="Runtime Latency (p50, p90, p99)",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/BedrockAgentCore",
                        metric_name="RuntimeLatency",
                        dimensions_map={"RuntimeName": runtime_name},
                        statistic="p50",
                        period=Duration.minutes(5),
                        label="p50",
                    ),
                    cloudwatch.Metric(
                        namespace="AWS/BedrockAgentCore",
                        metric_name="RuntimeLatency",
                        dimensions_map={"RuntimeName": runtime_name},
                        statistic="p90",
                        period=Duration.minutes(5),
                        label="p90",
                    ),
                    latency_metric,
                ],
                width=12,
            ),
        )

        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Model Invocations",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/BedrockAgentCore",
                        metric_name="ModelInvocations",
                        dimensions_map={"RuntimeName": runtime_name},
                        statistic="Sum",
                        period=Duration.minutes(5),
                    )
                ],
                width=12,
            ),
            cloudwatch.GraphWidget(
                title="Token Usage",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/BedrockAgentCore",
                        metric_name="InputTokens",
                        dimensions_map={"RuntimeName": runtime_name},
                        statistic="Sum",
                        period=Duration.minutes(5),
                        label="Input Tokens",
                    ),
                    cloudwatch.Metric(
                        namespace="AWS/BedrockAgentCore",
                        metric_name="OutputTokens",
                        dimensions_map={"RuntimeName": runtime_name},
                        statistic="Sum",
                        period=Duration.minutes(5),
                        label="Output Tokens",
                    ),
                ],
                width=12,
            ),
        )

        logger.info("[AgentCoreStack] Exporting stack outputs")
        self._export_outputs(
            runtime_name, log_group, security_stack, network_mode, environment
        )

        logger.info(
            "[AgentCoreStack] AgentCore stack initialization complete for environment: %s",
            environment,
        )

    def _validate_environment(self, environment: str) -> None:
        if not environment:
            raise ValueError(
                "environment parameter is required and cannot be empty. "
                "Provide a valid environment name (e.g., 'test', 'dev', 'prod')."
            )

        if not environment.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                f"Invalid environment name: '{environment}'. "
                "Environment must be alphanumeric (hyphens and underscores allowed)."
            )

        logger.info("[AgentCoreStack] Environment validation passed: %s", environment)

    def _validate_dependencies(
        self, network_stack, security_stack, storage_stack
    ) -> None:
        if security_stack is None:
            raise ValueError(
                "security_stack is required but was None. "
                "AgentCore requires a SecurityStack with execution role."
            )

        if not hasattr(security_stack, "agentcore_execution_role"):
            raise AttributeError(
                "security_stack does not have 'agentcore_execution_role' attribute. "
                "Ensure SecurityStack creates the AgentCore execution role."
            )

        if storage_stack is None:
            raise ValueError(
                "storage_stack is required but was None. "
                "AgentCore requires a StorageStack with ECR repository."
            )

        if not hasattr(storage_stack, "ecr_repo"):
            raise AttributeError(
                "storage_stack does not have 'ecr_repo' attribute. "
                "Ensure StorageStack creates an ECR repository."
            )

        logger.info("[AgentCoreStack] Cross-stack dependencies validated")

    def _validate_network_mode(self, mode: str) -> None:
        valid_modes = ["PUBLIC", "VPC"]
        if mode not in valid_modes:
            raise ValueError(
                f"Invalid network_mode: '{mode}'. Must be one of {valid_modes}. "
                f"Got '{mode}' instead."
            )
        logger.info("[AgentCoreStack] Network mode validation passed: %s", mode)

    def _validate_config(self, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(
                f"agentcore_config must be a dict, got {type(config).__name__}"
            )

        if "cpu" not in config:
            raise KeyError(
                "agentcore_config missing required key 'cpu'. "
                "Valid values: 512, 1024, 2048, 4096"
            )

        if "memory" not in config:
            raise KeyError(
                "agentcore_config missing required key 'memory'. "
                "Valid values: 1024, 2048, 4096, 8192, 16384"
            )

        try:
            cpu = int(config["cpu"])
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"CPU value must be an integer or integer string, got: {config['cpu']}"
            ) from e

        try:
            memory = int(config["memory"])
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Memory value must be an integer or integer string, got: {config['memory']}"
            ) from e

        valid_cpu = [512, 1024, 2048, 4096]
        if cpu not in valid_cpu:
            raise ValueError(
                f"Invalid CPU value: {cpu}. Must be one of {valid_cpu}. "
                "See AWS Fargate task definitions for valid combinations."
            )

        valid_memory = [1024, 2048, 4096, 8192, 16384]
        if memory not in valid_memory:
            raise ValueError(
                f"Invalid memory value: {memory}. Must be one of {valid_memory}. "
                "See AWS Fargate task definitions for valid combinations."
            )

        if memory < cpu * 2:
            raise ValueError(
                f"Invalid CPU/memory combination: CPU={cpu}, Memory={memory}. "
                f"Memory must be at least 2x CPU (minimum {cpu * 2} MB for {cpu} CPU units). "
                "See AWS Fargate documentation for valid task size combinations."
            )

        logger.info(
            "[AgentCoreStack] Configuration validation passed: cpu=%d, memory=%d",
            cpu,
            memory,
        )

    def _export_outputs(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        runtime_name: str,
        log_group,
        security_stack,
        network_mode: str,
        environment: str,
    ) -> None:
        CfnOutput(
            self,
            "AgentRuntimeArn",
            value=self.agent_runtime.get_att("AgentRuntimeArn").to_string(),
            description="Bedrock AgentCore runtime ARN",
            export_name=f"{environment}-AgentRuntimeArn",
        )

        CfnOutput(
            self,
            "AgentRuntimeId",
            value=self.agent_runtime.get_att("AgentRuntimeId").to_string(),
            description="Bedrock AgentCore runtime ID",
            export_name="AgentRuntimeId",
        )

        CfnOutput(
            self,
            "AgentRuntimeEndpointUrl",
            value=self.agent_runtime.get_att("EndpointUrl").to_string(),
            description="Bedrock AgentCore runtime endpoint URL",
            export_name="AgentRuntimeEndpointUrl",
        )

        CfnOutput(
            self,
            "AgentRuntimeStatus",
            value=self.agent_runtime.get_att("Status").to_string(),
            description="Bedrock AgentCore runtime status",
            export_name="AgentRuntimeStatus",
        )

        CfnOutput(
            self,
            "AgentRuntimeVersion",
            value=self.agent_runtime.get_att("AgentRuntimeVersion").to_string(),
            description="Bedrock AgentCore runtime version",
            export_name="AgentRuntimeVersion",
        )

        CfnOutput(
            self,
            "ExecutionRoleArn",
            value=security_stack.agentcore_execution_role.role_arn,
            description="Bedrock AgentCore execution role ARN",
            export_name=f"{environment}-AgentExecutionRoleArn",
        )

        CfnOutput(
            self,
            "NetworkMode",
            value=network_mode,
            description="Network mode (PUBLIC or VPC)",
            export_name="AgentRuntimeNetworkMode",
        )

        CfnOutput(
            self,
            "AgentRuntimeLogGroupArn",
            value=log_group.log_group_arn,
            description="AgentCore runtime log group ARN",
            export_name=f"{environment}-AgentRuntimeLogGroupArn",
        )

        CfnOutput(
            self,
            "AgentRuntimeLogGroupName",
            value=log_group.log_group_name,
            description="AgentCore runtime log group name",
            export_name=f"{environment}-AgentRuntimeLogGroupName",
        )

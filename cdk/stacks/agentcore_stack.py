from aws_cdk import (
    Stack,
    CfnOutput,
    CfnResource,
)
from constructs import Construct


class AgentCoreStack(Stack):
    def __init__(
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

        ecr_uri = (
            f"{Stack.of(self).account}.dkr.ecr.{Stack.of(self).region}"
            f".amazonaws.com/{storage_stack.ecr_repo.repository_name}:latest"
        )

        network_mode = agentcore_config.get("network_mode", "PUBLIC")

        runtime_properties = {
            "AgentRuntimeName": f"hackathon-agent-{environment}-{Stack.of(self).region}",
            "Description": f"AWS Hackathon AgentCore runtime ({network_mode} mode)",
            "AgentRuntimeArtifact": {
                "ContainerConfiguration": {
                    "ContainerUri": ecr_uri,
                    "Cpu": agentcore_config["cpu"],
                    "Memory": agentcore_config["memory"],
                }
            },
            "RoleArn": security_stack.agentcore_execution_role.role_arn,
            "Tags": [
                {"Key": "Project", "Value": "aws-hackathon"},
                {"Key": "Environment", "Value": environment},
                {"Key": "Owner", "Value": "platform-team"},
                {"Key": "CostCenter", "Value": "engineering"},
                {"Key": "ManagedBy", "Value": "cdk"},
                {"Key": "Stack", "Value": "agentcore-stack"},
            ],
        }

        if network_mode == "VPC":
            agent_subnets = [
                subnet
                for subnet in network_stack.vpc.private_subnets
                if "PrivateAgent" in subnet.node.id
            ]
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
            runtime_properties["NetworkConfiguration"] = {"NetworkMode": "PUBLIC"}

        self.agent_runtime = CfnResource(
            self,
            "AgentRuntime",
            type="AWS::BedrockAgentCore::Runtime",
            properties=runtime_properties,
        )

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

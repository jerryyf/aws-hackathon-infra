from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_cloudwatch as cloudwatch,
    aws_logs as logs,
    aws_cloudtrail as cloudtrail,
    CfnOutput,
)
from constructs import Construct


class MonitoringStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        # Get logs bucket from storage stack
        logs_bucket = kwargs.pop('logs_bucket', None)

        super().__init__(scope, construct_id, **kwargs)

        # CloudWatch Log Groups
        self.app_log_group = logs.LogGroup(
            self, "AppLogGroup",
            log_group_name="/hackathon/app",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        self.alb_log_group = logs.LogGroup(
            self, "AlbLogGroup",
            log_group_name="/hackathon/alb",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        # CloudWatch Alarms
        self.alb_healthy_hosts_alarm = cloudwatch.Alarm(
            self, "AlbHealthyHostsAlarm",
            alarm_name="ALB Healthy Hosts",
            alarm_description="ALB has unhealthy targets",
            metric=cloudwatch.Metric(
                namespace="AWS/ApplicationELB",
                metric_name="HealthyHostCount",
                dimensions_map={
                    "LoadBalancer": "hackathon-alb",
                    "TargetGroup": "hackathon-targets"
                },
                statistic="Average"
            ),
            threshold=1,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD
        )

        # CloudTrail
        self.cloudtrail = cloudtrail.Trail(
            self, "CloudTrail",
            trail_name="hackathon-trail",
            bucket=logs_bucket,  # From storage stack
            is_multi_region_trail=True,
            enable_file_validation=True,
            include_global_service_events=True,
            is_organization_trail=False
        )

        # Outputs
        CfnOutput(
            self, "AppLogGroupName",
            value=self.app_log_group.log_group_name,
            description="Application log group name",
            export_name="AppLogGroupName"
        )

        CfnOutput(
            self, "CloudTrailArn",
            value=self.cloudtrail.trail_arn,
            description="CloudTrail ARN",
            export_name="CloudTrailArn"
        )
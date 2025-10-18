import aws_cdk as cdk
from aws_cdk.assertions import Template
from cdk.stacks.monitoring_stack import MonitoringStack
from cdk.stacks.storage_stack import StorageStack


def test_monitoring_stack_log_groups_created():
    app = cdk.App()
    storage_stack = StorageStack(app, "TestStorageStack")
    stack = MonitoringStack(
        app, "TestMonitoringStack", logs_bucket=storage_stack.logs_bucket
    )
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Logs::LogGroup", 2)


def test_monitoring_stack_app_log_group():
    app = cdk.App()
    storage_stack = StorageStack(app, "TestStorageStack")
    stack = MonitoringStack(
        app, "TestMonitoringStack", logs_bucket=storage_stack.logs_bucket
    )
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::Logs::LogGroup",
        {"LogGroupName": "/bidopsai/app", "RetentionInDays": 7},
    )


def test_monitoring_stack_alb_log_group():
    app = cdk.App()
    storage_stack = StorageStack(app, "TestStorageStack")
    stack = MonitoringStack(
        app, "TestMonitoringStack", logs_bucket=storage_stack.logs_bucket
    )
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::Logs::LogGroup",
        {"LogGroupName": "/bidopsai/alb", "RetentionInDays": 7},
    )


def test_monitoring_stack_cloudwatch_alarm():
    app = cdk.App()
    storage_stack = StorageStack(app, "TestStorageStack")
    stack = MonitoringStack(
        app, "TestMonitoringStack", logs_bucket=storage_stack.logs_bucket
    )
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::CloudWatch::Alarm", 1)
    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "AlarmName": "ALB Healthy Hosts",
            "MetricName": "HealthyHostCount",
            "Namespace": "AWS/ApplicationELB",
            "Threshold": 1,
            "ComparisonOperator": "LessThanThreshold",
        },
    )


def test_monitoring_stack_cloudtrail():
    app = cdk.App()
    storage_stack = StorageStack(app, "TestStorageStack")
    stack = MonitoringStack(
        app, "TestMonitoringStack", logs_bucket=storage_stack.logs_bucket
    )
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::CloudTrail::Trail", 1)
    template.has_resource_properties(
        "AWS::CloudTrail::Trail",
        {
            "TrailName": "bidopsai-trail",
            "IsMultiRegionTrail": True,
            "EnableLogFileValidation": True,
            "IncludeGlobalServiceEvents": True,
        },
    )


def test_monitoring_stack_outputs():
    app = cdk.App()
    storage_stack = StorageStack(app, "TestStorageStack")
    stack = MonitoringStack(
        app, "TestMonitoringStack", logs_bucket=storage_stack.logs_bucket
    )
    template = Template.from_stack(stack)

    template.has_output("AppLogGroupName", {"Export": {"Name": "AppLogGroupName"}})
    template.has_output("CloudTrailArn", {"Export": {"Name": "CloudTrailArn"}})

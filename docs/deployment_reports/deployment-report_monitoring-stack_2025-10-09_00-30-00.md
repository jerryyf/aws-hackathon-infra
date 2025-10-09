# Monitoring Stack Deployment Report

Timestamp: 2025-10-09 00:30:00 UTC
Stack: MonitoringStack

Key resources
-------------
- CloudWatch Log Groups:
  - `/hackathon/app` (1 week retention)
  - `/hackathon/alb` (1 week retention)
- CloudWatch Alarm: `ALB Healthy Hosts` (threshold < 1 triggers)
- CloudTrail: `hackathon-trail` (multi-region, file validation enabled), logs to StorageStack logs bucket

Important file/artifact
-----------------------
- Synth template: `cdk/cdk.out/MonitoringStack.template.json`

Sanity checks (Console)
-----------------------
- CloudWatch Logs: Log groups exist and have retention configured.
- CloudWatch Alarms: Alarm exists and is configured for the correct metric and threshold.
- CloudTrail: Trail exists and is configured with the logs bucket, multi-region enabled.

Next steps
----------
- Wire ALB access logs to CloudWatch or S3 as desired.
- Add SNS/Slack alerting for critical alarms.

# Monitoring Stack Sanity Checks

Timestamp: 2025-10-09 00:30:00 UTC
Stack: MonitoringStack

Checklist
---------
- CloudFormation: MonitoringStack = CREATE_COMPLETE
- CloudWatch Log Groups: `/bidopsai/app`, `/bidopsai/alb` exist and retention set
- CloudWatch Alarm: `ALB Healthy Hosts` exists
- CloudTrail: `bidopsai-trail` exists and logs to StorageStack logs bucket

Commands
--------
- Describe CloudTrail:
  ```bash
  aws cloudtrail describe-trails --trail-name-list bidopsai-trail
  ```

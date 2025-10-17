import pytest
import boto3


def test_alb_accessibility():
    """Test that ALB is deployed and in active state"""
    cloudformation = boto3.client("cloudformation")
    elbv2 = boto3.client("elbv2")

    try:
        response = cloudformation.describe_stacks(StackName="NetworkStack")
        outputs = {
            o["OutputKey"]: o["OutputValue"] for o in response["Stacks"][0]["Outputs"]
        }
        alb_dns = outputs["AlbDnsName"]
    except Exception as e:
        pytest.fail(f"NetworkStack not deployed or AlbDnsName not found: {e}")

    assert alb_dns, "ALB DNS name must not be empty"

    load_balancers = elbv2.describe_load_balancers()["LoadBalancers"]
    alb = next((lb for lb in load_balancers if lb["DNSName"] == alb_dns), None)

    assert alb is not None, f"ALB with DNS {alb_dns} not found"
    assert alb["State"]["Code"] == "active", f"ALB state is {alb['State']['Code']}"
    assert alb["Scheme"] == "internet-facing", "ALB must be internet-facing"

    listeners = elbv2.describe_listeners(LoadBalancerArn=alb["LoadBalancerArn"])[
        "Listeners"
    ]
    assert len(listeners) > 0, "ALB must have at least one listener"

    https_listener = next((l for l in listeners if l["Port"] == 443), None)
    assert https_listener is not None, "ALB must have HTTPS listener on port 443"

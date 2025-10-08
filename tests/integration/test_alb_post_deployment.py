import pytest
import requests
import boto3
from cdk.app import app


def test_alb_accessibility():
    """Test that ALB is accessible after deployment"""
    # This test assumes the infrastructure is deployed
    # It will fail until deployment scripts are implemented and run

    # Get ALB DNS name from deployed stack
    # For now, this will fail as stacks are not deployed
    cloudformation = boto3.client('cloudformation')
    try:
        response = cloudformation.describe_stacks(StackName='ComputeStack')
        outputs = {o['OutputKey']: o['OutputValue'] for o in response['Stacks'][0]['Outputs']}
        alb_dns = outputs['AlbDnsName']
    except:
        pytest.fail("ComputeStack not deployed or ALB DNS not found")

    # Test ALB responds
    response = requests.get(f"http://{alb_dns}", timeout=10)
    assert response.status_code == 200
    assert "hackathon" in response.text.lower()  # Assuming some content
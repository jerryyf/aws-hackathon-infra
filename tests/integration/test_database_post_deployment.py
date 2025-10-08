import pytest
import psycopg2
import boto3
import json
from cdk.app import app


def test_database_connectivity():
    """Test that database is accessible after deployment"""
    # This test assumes the infrastructure is deployed
    # It will fail until deployment scripts are implemented and run

    # Get database connection details from deployed stack
    cloudformation = boto3.client('cloudformation')
    try:
        response = cloudformation.describe_stacks(StackName='DatabaseStack')
        outputs = {o['OutputKey']: o['OutputValue'] for o in response['Stacks'][0]['Outputs']}
        db_endpoint = outputs['RdsEndpoint']
        db_port = int(outputs['RdsPort'])
    except:
        pytest.fail("DatabaseStack not deployed or outputs not found")

    # Get credentials from Secrets Manager
    secrets_client = boto3.client('secretsmanager')
    secret = secrets_client.get_secret_value(SecretId='hackathon/rds/credentials')
    creds = json.loads(secret['SecretString'])
    username = creds['username']
    password = creds['password']

    # Test database connection
    try:
        conn = psycopg2.connect(
            host=db_endpoint,
            port=db_port,
            database='hackathon',
            user=username,
            password=password,
            connect_timeout=10
        )
        conn.close()
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")
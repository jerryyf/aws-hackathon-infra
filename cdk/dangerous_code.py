"""
This file simulates a developer accidentally committing secrets
"""

# OOPS! Accidentally hardcoded an ARN
ROLE_ARN = "arn:aws:iam::123456789012:role/MyProductionRole"

# OOPS! Accidentally hardcoded an AWS access key
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"

# OOPS! Accidentally hardcoded a secret key
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"


def get_aws_credentials():
    """This is the WRONG way - hardcoded credentials"""
    return {
        "role": ROLE_ARN,
        "key": AWS_ACCESS_KEY_ID,
        "secret": AWS_SECRET_ACCESS_KEY
    }

import pytest
import aws_cdk as cdk
from cdk.app import app


def test_synth_all_stacks():
    """Test that all CDK stacks can be synthesized without errors"""
    # This test will fail if there are any issues with stack definitions
    # or missing dependencies during synthesis
    try:
        app.synth()
    except Exception as e:
        pytest.fail(f"CDK synthesis failed: {e}")
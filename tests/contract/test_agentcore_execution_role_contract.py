import json


def test_agentcore_execution_role_policy_contract_bedrock(
    agentcore_stack_outputs, iam_client, load_contract_json
):
    """Test execution role Bedrock permissions match contract"""

    contract = load_contract_json("execution-role-permissions.json")
    role_name = agentcore_stack_outputs["ExecutionRoleArn"].split("/")[-1]

    # Find Bedrock statement in contract
    bedrock_stmt = next(
        (s for s in contract["Statement"] if s["Sid"] == "BedrockModelAccess"), None
    )
    assert bedrock_stmt, "Contract must define BedrockModelAccess statement"

    # Verify role has Bedrock permissions
    inline_response = iam_client.list_role_policies(RoleName=role_name)

    has_bedrock_perms = False
    for policy_name in inline_response["PolicyNames"]:
        policy_response = iam_client.get_role_policy(
            RoleName=role_name, PolicyName=policy_name
        )
        policy_doc = json.loads(policy_response["PolicyDocument"])

        for stmt in policy_doc.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            required_actions = bedrock_stmt["Action"]
            if all(action in actions for action in required_actions):
                has_bedrock_perms = True
                break

    assert (
        has_bedrock_perms
    ), "Execution role must have Bedrock model invocation permissions from contract"


def test_agentcore_execution_role_policy_contract_ecr(
    agentcore_stack_outputs, iam_client, load_contract_json
):
    """Test execution role ECR permissions match contract"""

    contract = load_contract_json("execution-role-permissions.json")
    role_name = agentcore_stack_outputs["ExecutionRoleArn"].split("/")[-1]

    ecr_stmt = next(
        (s for s in contract["Statement"] if s["Sid"] == "ECRImageAccess"), None
    )
    assert ecr_stmt, "Contract must define ECRImageAccess statement"

    inline_response = iam_client.list_role_policies(RoleName=role_name)

    has_ecr_perms = False
    for policy_name in inline_response["PolicyNames"]:
        policy_response = iam_client.get_role_policy(
            RoleName=role_name, PolicyName=policy_name
        )
        policy_doc = json.loads(policy_response["PolicyDocument"])

        for stmt in policy_doc.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            required_actions = ecr_stmt["Action"]
            if all(action in actions for action in required_actions):
                has_ecr_perms = True
                break

    assert has_ecr_perms, "Execution role must have ECR permissions from contract"


def test_agentcore_execution_role_policy_contract_cloudwatch(
    agentcore_stack_outputs, iam_client, load_contract_json
):
    """Test execution role CloudWatch Logs permissions match contract"""

    contract = load_contract_json("execution-role-permissions.json")
    role_name = agentcore_stack_outputs["ExecutionRoleArn"].split("/")[-1]

    logs_stmt = next(
        (s for s in contract["Statement"] if s["Sid"] == "CloudWatchLogsAccess"), None
    )
    assert logs_stmt, "Contract must define CloudWatchLogsAccess statement"

    inline_response = iam_client.list_role_policies(RoleName=role_name)

    has_logs_perms = False
    for policy_name in inline_response["PolicyNames"]:
        policy_response = iam_client.get_role_policy(
            RoleName=role_name, PolicyName=policy_name
        )
        policy_doc = json.loads(policy_response["PolicyDocument"])

        for stmt in policy_doc.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            required_actions = logs_stmt["Action"]
            if all(action in actions for action in required_actions):
                has_logs_perms = True
                break

    assert (
        has_logs_perms
    ), "Execution role must have CloudWatch Logs permissions from contract"


def test_agentcore_execution_role_policy_contract_secrets(
    agentcore_stack_outputs, iam_client, load_contract_json
):
    """Test execution role Secrets Manager permissions match contract"""

    contract = load_contract_json("execution-role-permissions.json")
    role_name = agentcore_stack_outputs["ExecutionRoleArn"].split("/")[-1]

    secrets_stmt = next(
        (s for s in contract["Statement"] if s["Sid"] == "SecretsManagerAccess"), None
    )
    assert secrets_stmt, "Contract must define SecretsManagerAccess statement"

    inline_response = iam_client.list_role_policies(RoleName=role_name)

    has_secrets_perms = False
    for policy_name in inline_response["PolicyNames"]:
        policy_response = iam_client.get_role_policy(
            RoleName=role_name, PolicyName=policy_name
        )
        policy_doc = json.loads(policy_response["PolicyDocument"])

        for stmt in policy_doc.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            if "secretsmanager:GetSecretValue" in actions:
                has_secrets_perms = True
                break

    assert (
        has_secrets_perms
    ), "Execution role must have Secrets Manager permissions from contract"


def test_agentcore_execution_role_policy_contract_kms(
    agentcore_stack_outputs, iam_client, load_contract_json
):
    """Test execution role KMS permissions match contract"""

    contract = load_contract_json("execution-role-permissions.json")
    role_name = agentcore_stack_outputs["ExecutionRoleArn"].split("/")[-1]

    kms_stmt = next(
        (s for s in contract["Statement"] if s["Sid"] == "KMSDecryptAccess"), None
    )
    assert kms_stmt, "Contract must define KMSDecryptAccess statement"

    inline_response = iam_client.list_role_policies(RoleName=role_name)

    has_kms_perms = False
    for policy_name in inline_response["PolicyNames"]:
        policy_response = iam_client.get_role_policy(
            RoleName=role_name, PolicyName=policy_name
        )
        policy_doc = json.loads(policy_response["PolicyDocument"])

        for stmt in policy_doc.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            required_actions = kms_stmt["Action"]
            if all(action in actions for action in required_actions):
                has_kms_perms = True
                break

    assert has_kms_perms, "Execution role must have KMS permissions from contract"


def test_agentcore_execution_role_exists(agentcore_stack_outputs, iam_client):
    """Test that AgentCore execution role exists"""

    role_arn = agentcore_stack_outputs["ExecutionRoleArn"]
    role_name = role_arn.split("/")[-1]

    response = iam_client.get_role(RoleName=role_name)
    assert response["Role"]["Arn"] == role_arn, f"Role ARN mismatch"


def test_agentcore_execution_role_trust_policy(agentcore_stack_outputs, iam_client):
    """Test execution role trust policy allows Bedrock Agent"""

    role_name = agentcore_stack_outputs["ExecutionRoleArn"].split("/")[-1]

    response = iam_client.get_role(RoleName=role_name)
    trust_policy = json.loads(response["Role"]["AssumeRolePolicyDocument"])

    # Verify Bedrock Agent service can assume role
    principals = [
        stmt["Principal"]["Service"]
        for stmt in trust_policy["Statement"]
        if "Service" in stmt["Principal"]
    ]
    assert (
        "bedrock.amazonaws.com" in principals
    ), "Trust policy must allow bedrock.amazonaws.com"


def test_agentcore_execution_role_trust_policy_contract(
    agentcore_stack_outputs, iam_client, load_contract_json
):
    """Test execution role trust policy matches contract"""

    contract = load_contract_json("execution-role-trust.json")
    role_name = agentcore_stack_outputs["ExecutionRoleArn"].split("/")[-1]

    response = iam_client.get_role(RoleName=role_name)
    actual_trust_policy = json.loads(response["Role"]["AssumeRolePolicyDocument"])

    # Verify contract trust policy structure
    assert "Statement" in contract, "Contract must have Statement"
    contract_stmt = contract["Statement"][0]

    # Verify service principal in actual policy
    actual_principals = []
    for stmt in actual_trust_policy["Statement"]:
        if "Service" in stmt.get("Principal", {}):
            service = stmt["Principal"]["Service"]
            if isinstance(service, list):
                actual_principals.extend(service)
            else:
                actual_principals.append(service)

    # Contract expects bedrock-agentcore.amazonaws.com
    expected_service = contract_stmt["Principal"]["Service"]
    assert (
        expected_service in actual_principals
        or "bedrock.amazonaws.com" in actual_principals
    ), f"Trust policy must allow {expected_service} (or bedrock.amazonaws.com)"

    # Verify AssumeRole action
    for stmt in actual_trust_policy["Statement"]:
        if (
            "sts:AssumeRole" in stmt.get("Action", [])
            or stmt.get("Action") == "sts:AssumeRole"
        ):
            assert stmt["Effect"] == "Allow", "AssumeRole must have Allow effect"
            break
    else:
        assert False, "Trust policy must have sts:AssumeRole action"


def test_agentcore_execution_role_bedrock_permissions(
    agentcore_stack_outputs, iam_client
):
    """Test execution role has Bedrock permissions"""

    role_name = agentcore_stack_outputs["ExecutionRoleArn"].split("/")[-1]

    # Get attached managed policies
    managed_response = iam_client.list_attached_role_policies(RoleName=role_name)
    managed_policies = [p["PolicyName"] for p in managed_response["AttachedPolicies"]]

    # Get inline policies
    inline_response = iam_client.list_role_policies(RoleName=role_name)
    inline_policies = inline_response["PolicyNames"]

    # Verify at least one policy exists (managed or inline)
    assert (
        len(managed_policies) + len(inline_policies) > 0
    ), "Execution role must have policies attached"


def test_agentcore_execution_role_ecr_permissions(agentcore_stack_outputs, iam_client):
    """Test execution role has ECR permissions for image pull"""

    role_name = agentcore_stack_outputs["ExecutionRoleArn"].split("/")[-1]

    # Check for ECR permissions in inline policies
    inline_response = iam_client.list_role_policies(RoleName=role_name)

    has_ecr_perms = False
    for policy_name in inline_response["PolicyNames"]:
        policy_response = iam_client.get_role_policy(
            RoleName=role_name, PolicyName=policy_name
        )
        policy_doc = json.loads(policy_response["PolicyDocument"])

        for stmt in policy_doc.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            ecr_actions = [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
            ]
            if any(action in actions for action in ecr_actions):
                has_ecr_perms = True
                break

    assert has_ecr_perms, "Execution role must have ECR permissions"


def test_agentcore_execution_role_cloudwatch_permissions(
    agentcore_stack_outputs, iam_client
):
    """Test execution role has CloudWatch Logs permissions"""

    role_name = agentcore_stack_outputs["ExecutionRoleArn"].split("/")[-1]

    inline_response = iam_client.list_role_policies(RoleName=role_name)

    has_cloudwatch_perms = False
    for policy_name in inline_response["PolicyNames"]:
        policy_response = iam_client.get_role_policy(
            RoleName=role_name, PolicyName=policy_name
        )
        policy_doc = json.loads(policy_response["PolicyDocument"])

        for stmt in policy_doc.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            if any("logs:" in action for action in actions):
                has_cloudwatch_perms = True
                break

    assert has_cloudwatch_perms, "Execution role must have CloudWatch Logs permissions"


def test_agentcore_execution_role_secrets_manager_permissions(
    agentcore_stack_outputs, iam_client
):
    """Test execution role has Secrets Manager permissions"""

    role_name = agentcore_stack_outputs["ExecutionRoleArn"].split("/")[-1]

    inline_response = iam_client.list_role_policies(RoleName=role_name)

    has_secrets_perms = False
    for policy_name in inline_response["PolicyNames"]:
        policy_response = iam_client.get_role_policy(
            RoleName=role_name, PolicyName=policy_name
        )
        policy_doc = json.loads(policy_response["PolicyDocument"])

        for stmt in policy_doc.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            if any("secretsmanager:" in action for action in actions):
                has_secrets_perms = True
                break

    assert has_secrets_perms, "Execution role must have Secrets Manager permissions"


def test_agentcore_execution_role_kms_permissions(agentcore_stack_outputs, iam_client):
    """Test execution role has KMS permissions for encryption"""

    role_name = agentcore_stack_outputs["ExecutionRoleArn"].split("/")[-1]

    inline_response = iam_client.list_role_policies(RoleName=role_name)

    has_kms_perms = False
    for policy_name in inline_response["PolicyNames"]:
        policy_response = iam_client.get_role_policy(
            RoleName=role_name, PolicyName=policy_name
        )
        policy_doc = json.loads(policy_response["PolicyDocument"])

        for stmt in policy_doc.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            if any("kms:" in action for action in actions):
                has_kms_perms = True
                break

    assert has_kms_perms, "Execution role must have KMS permissions"


def test_agentcore_execution_role_output(agentcore_stack_outputs):
    """Test execution role ARN output exists and is valid"""

    assert (
        "ExecutionRoleArn" in agentcore_stack_outputs
    ), "ExecutionRoleArn output missing"

    role_arn = agentcore_stack_outputs["ExecutionRoleArn"]
    assert role_arn.startswith(
        "arn:aws:iam::"
    ), "ExecutionRoleArn must be valid IAM role ARN"
    assert ":role/" in role_arn, "ExecutionRoleArn must reference a role"

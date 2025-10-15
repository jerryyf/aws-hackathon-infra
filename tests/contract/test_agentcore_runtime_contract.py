import re


def test_agentcore_runtime_contract_outputs(
    agentcore_stack_outputs, load_contract_yaml
):
    """Test that all required outputs from contract YAML exist"""

    contract = load_contract_yaml("agentcore-stack.yaml")

    required_outputs = [
        output_name
        for output_name, spec in contract["outputs"].items()
        if any(v.get("type") == "required" for v in spec.get("validation", []))
    ]

    for output_name in required_outputs:
        assert (
            output_name in agentcore_stack_outputs
        ), f"Required output {output_name} not found (contract: agentcore-stack.yaml)"


def test_agentcore_runtime_arn_contract_validation(
    agentcore_stack_outputs, load_contract_yaml
):
    """Test AgentCore runtime ARN matches contract regex"""

    contract = load_contract_yaml("agentcore-stack.yaml")
    arn = agentcore_stack_outputs["AgentRuntimeArn"]

    arn_spec = contract["outputs"]["AgentRuntimeArn"]
    regex_validation = next(
        (v for v in arn_spec["validation"] if v["type"] == "regex"), None
    )

    assert regex_validation, "Contract must define regex validation for AgentRuntimeArn"
    pattern = re.compile(regex_validation["pattern"])
    assert pattern.match(arn), f"AgentRuntimeArn {arn} does not match contract pattern"


def test_agentcore_runtime_id_contract_validation(
    agentcore_stack_outputs, load_contract_yaml
):
    """Test AgentCore runtime ID matches contract regex"""

    contract = load_contract_yaml("agentcore-stack.yaml")
    runtime_id = agentcore_stack_outputs["AgentRuntimeId"]

    id_spec = contract["outputs"]["AgentRuntimeId"]
    regex_validation = next(
        (v for v in id_spec["validation"] if v["type"] == "regex"), None
    )

    assert regex_validation, "Contract must define regex validation for AgentRuntimeId"
    pattern = re.compile(regex_validation["pattern"])
    assert pattern.match(
        runtime_id
    ), f"AgentRuntimeId {runtime_id} does not match contract pattern"


def test_agentcore_runtime_endpoint_contract_validation(
    agentcore_stack_outputs, load_contract_yaml
):
    """Test AgentCore runtime endpoint matches contract regex and HTTPS requirement"""

    contract = load_contract_yaml("agentcore-stack.yaml")
    endpoint = agentcore_stack_outputs["AgentRuntimeEndpointUrl"]

    endpoint_spec = contract["outputs"]["AgentRuntimeEndpointUrl"]

    regex_validation = next(
        (v for v in endpoint_spec["validation"] if v["type"] == "regex"), None
    )
    assert regex_validation, "Contract must define regex validation for endpoint"
    pattern = re.compile(regex_validation["pattern"])
    assert pattern.match(
        endpoint
    ), f"Endpoint {endpoint} does not match contract pattern"

    https_validation = next(
        (v for v in endpoint_spec["validation"] if v["type"] == "https_only"), None
    )
    assert https_validation, "Contract must define HTTPS validation"
    assert endpoint.startswith("https://"), "Endpoint must use HTTPS"


def test_agentcore_runtime_status_contract_validation(
    agentcore_stack_outputs, load_contract_yaml
):
    """Test AgentCore runtime status matches contract enum"""

    contract = load_contract_yaml("agentcore-stack.yaml")
    status = agentcore_stack_outputs["AgentRuntimeStatus"]

    status_spec = contract["outputs"]["AgentRuntimeStatus"]
    enum_validation = next(
        (v for v in status_spec["validation"] if v["type"] == "enum"), None
    )

    assert enum_validation, "Contract must define enum validation for status"
    valid_values = enum_validation["values"]
    assert (
        status in valid_values
    ), f"Status {status} not in contract enum: {valid_values}"


def test_execution_role_arn_contract_validation(
    agentcore_stack_outputs, load_contract_yaml
):
    """Test execution role ARN matches contract regex"""

    contract = load_contract_yaml("agentcore-stack.yaml")
    arn = agentcore_stack_outputs["ExecutionRoleArn"]

    role_spec = contract["outputs"]["ExecutionRoleArn"]
    regex_validation = next(
        (v for v in role_spec["validation"] if v["type"] == "regex"), None
    )

    assert (
        regex_validation
    ), "Contract must define regex validation for ExecutionRoleArn"
    pattern = re.compile(regex_validation["pattern"])
    assert pattern.match(arn), f"ExecutionRoleArn {arn} does not match contract pattern"


def test_agentcore_runtime_outputs_exist(agentcore_stack_outputs):
    """Test that AgentCore runtime outputs exist"""

    required_outputs = [
        "AgentRuntimeArn",
        "AgentRuntimeId",
        "AgentRuntimeEndpointUrl",
        "AgentRuntimeStatus",
        "AgentRuntimeVersion",
        "ExecutionRoleArn",
    ]

    for output_name in required_outputs:
        assert (
            output_name in agentcore_stack_outputs
        ), f"Required output {output_name} not found in AgentCoreStack"


def test_agentcore_runtime_arn_output(agentcore_stack_outputs):
    """Test AgentCore runtime ARN output format"""

    arn = agentcore_stack_outputs["AgentRuntimeArn"]
    arn_pattern = re.compile(r"^arn:aws:bedrock:[a-z0-9-]+:\d{12}:agent/[A-Z0-9]{10}$")
    assert arn_pattern.match(
        arn
    ), f"AgentRuntimeArn {arn} does not match expected format"


def test_agentcore_runtime_id_output(agentcore_stack_outputs):
    """Test AgentCore runtime ID output format"""

    runtime_id = agentcore_stack_outputs["AgentRuntimeId"]
    id_pattern = re.compile(r"^[A-Z0-9]{10}$")
    assert id_pattern.match(
        runtime_id
    ), f"AgentRuntimeId {runtime_id} does not match expected format"


def test_agentcore_runtime_endpoint_output(agentcore_stack_outputs):
    """Test AgentCore runtime endpoint output format"""

    endpoint = agentcore_stack_outputs["AgentRuntimeEndpointUrl"]
    assert endpoint.startswith("https://"), f"AgentRuntimeEndpointUrl must use HTTPS"
    assert (
        "bedrock-agent-runtime" in endpoint
    ), f"Endpoint must be a Bedrock Agent Runtime URL"


def test_agentcore_runtime_status_output(agentcore_stack_outputs):
    """Test AgentCore runtime status output"""

    status = agentcore_stack_outputs["AgentRuntimeStatus"]
    valid_statuses = ["CREATING", "PREPARED", "FAILED", "DELETING", "NOT_PREPARED"]
    assert (
        status in valid_statuses
    ), f"AgentRuntimeStatus must be one of {valid_statuses}, got {status}"


def test_agentcore_runtime_version_output(agentcore_stack_outputs):
    """Test AgentCore runtime version output format"""

    version = agentcore_stack_outputs["AgentRuntimeVersion"]
    # Version can be DRAFT or a number
    assert (
        version == "DRAFT" or version.isdigit()
    ), f"AgentRuntimeVersion must be 'DRAFT' or numeric, got {version}"


def test_execution_role_arn_output(agentcore_stack_outputs):
    """Test execution role ARN output format"""

    arn = agentcore_stack_outputs["ExecutionRoleArn"]
    arn_pattern = re.compile(r"^arn:aws:iam::\d{12}:role/[a-zA-Z0-9-_]+$")
    assert arn_pattern.match(
        arn
    ), f"ExecutionRoleArn {arn} does not match expected format"


def test_agentcore_runtime_properties(agentcore_stack_outputs, bedrock_agent_client):
    """Test AgentCore runtime properties via Bedrock Agent API"""

    agent_id = agentcore_stack_outputs["AgentRuntimeId"]

    response = bedrock_agent_client.get_agent(agentId=agent_id)
    agent = response["agent"]

    assert agent["agentStatus"] in [
        "CREATING",
        "PREPARED",
        "FAILED",
        "NOT_PREPARED",
    ], f"Agent status must be valid"
    assert "agentArn" in agent, "Agent must have ARN"
    assert "agentVersion" in agent, "Agent must have version"


def test_agentcore_runtime_tags(agentcore_stack_outputs, bedrock_agent_client):
    """Test AgentCore runtime tags"""

    agent_arn = agentcore_stack_outputs["AgentRuntimeArn"]

    response = bedrock_agent_client.list_tags_for_resource(resourceArn=agent_arn)
    tags = response.get("tags", {})

    # Verify environment tag exists
    assert (
        "Environment" in tags or "environment" in tags
    ), "Agent must have Environment tag"

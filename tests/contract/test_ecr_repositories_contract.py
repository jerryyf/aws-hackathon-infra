def test_ecr_repositories_contract(storage_stack_outputs):
    """Test that ECR repositories stack outputs match contract specification"""

    required_outputs = [
        "AppEcrRepositoryUri",
        "ApiEcrRepositoryUri",
        "AgentEcrRepositoryUri",
    ]

    for output_name in required_outputs:
        assert (
            output_name in storage_stack_outputs
        ), f"{output_name} output not found in StorageStack"


def test_ecr_repository_properties(storage_stack_outputs, ecr_client):
    """Test ECR repository properties"""

    # Extract repository names from URIs (format: account.dkr.ecr.region.amazonaws.com/repo-name)
    app_repo_name = storage_stack_outputs["AppEcrRepositoryUri"].split("/")[-1]
    api_repo_name = storage_stack_outputs["ApiEcrRepositoryUri"].split("/")[-1]
    agent_repo_name = storage_stack_outputs["AgentEcrRepositoryUri"].split("/")[-1]

    for repo_name in [app_repo_name, api_repo_name, agent_repo_name]:
        response = ecr_client.describe_repositories(repositoryNames=[repo_name])
        assert (
            len(response["repositories"]) == 1
        ), f"ECR repository {repo_name} not found"

        repo = response["repositories"][0]
        assert (
            repo["imageScanningConfiguration"]["scanOnPush"] is True
        ), f"ECR repository {repo_name} must have scan on push enabled"
        
        assert (
            repo["imageTagMutability"] == "IMMUTABLE"
        ), f"ECR repository {repo_name} must have IMMUTABLE tag mutability"


def test_ecr_repository_names(storage_stack_outputs):
    """Test that ECR repository names follow naming convention"""
    
    app_repo_uri = storage_stack_outputs["AppEcrRepositoryUri"]
    api_repo_uri = storage_stack_outputs["ApiEcrRepositoryUri"]
    agent_repo_uri = storage_stack_outputs["AgentEcrRepositoryUri"]
    
    assert "bidopsai/app" in app_repo_uri, "App repository must be named bidopsai/app"
    assert "bidopsai/api" in api_repo_uri, "API repository must be named bidopsai/api"
    assert "bidopsai/agent" in agent_repo_uri, "Agent repository must be named bidopsai/agent"

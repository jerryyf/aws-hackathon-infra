def test_ecr_repositories_contract(storage_stack_outputs):
    required_outputs = [
        "AppEcrRepositoryUri",
        "AgentEcrRepositoryUri",
    ]

    for output_name in required_outputs:
        assert (
            output_name in storage_stack_outputs
        ), f"{output_name} output not found in StorageStack"


def test_ecr_repository_properties(storage_stack_outputs, ecr_client):
    app_repo_name = "/".join(storage_stack_outputs["AppEcrRepositoryUri"].split("/")[-2:])
    agent_repo_name = "/".join(
        storage_stack_outputs["AgentEcrRepositoryUri"].split("/")[-2:]
    )

    for repo_name in [app_repo_name, agent_repo_name]:
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
    app_repo_uri = storage_stack_outputs["AppEcrRepositoryUri"]
    agent_repo_uri = storage_stack_outputs["AgentEcrRepositoryUri"]

    assert "bidopsai/app" in app_repo_uri, "App repository must be named bidopsai/app"
    assert (
        "bidopsai/agent" in agent_repo_uri
    ), "Agent repository must be named bidopsai/agent"

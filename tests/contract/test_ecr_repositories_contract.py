def test_ecr_repositories_contract(compute_stack_outputs):
    """Test that ECR repositories stack outputs match contract specification"""
    
    required_outputs = ["BffEcrRepoUri", "BackendEcrRepoUri"]
    
    for output_name in required_outputs:
        assert output_name in compute_stack_outputs, f"{output_name} output not found in ComputeStack"


def test_ecr_repository_properties(compute_stack_outputs, ecr_client):
    """Test ECR repository properties"""
    
    # Extract repository names from URIs (format: account.dkr.ecr.region.amazonaws.com/repo-name)
    bff_repo_name = compute_stack_outputs["BffEcrRepoUri"].split("/")[-1]
    backend_repo_name = compute_stack_outputs["BackendEcrRepoUri"].split("/")[-1]
    
    for repo_name in [bff_repo_name, backend_repo_name]:
        response = ecr_client.describe_repositories(repositoryNames=[repo_name])
        assert len(response["repositories"]) == 1, f"ECR repository {repo_name} not found"
        
        repo = response["repositories"][0]
        assert repo["imageScanningConfiguration"]["scanOnPush"] is True, \
            f"ECR repository {repo_name} must have scan on push enabled"

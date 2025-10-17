import re


def test_opensearch_endpoint_contract(database_stack_outputs):
    assert (
        "OpenSearchEndpoint" in database_stack_outputs
    ), "OpenSearchEndpoint output not found in DatabaseStack"

    endpoint = database_stack_outputs["OpenSearchEndpoint"]
    endpoint_pattern = re.compile(r"^vpc-[a-z0-9-]+\.[a-z0-9-]+\.es\.amazonaws\.com$")
    assert endpoint_pattern.match(
        endpoint
    ), f"OpenSearch endpoint {endpoint} does not match expected format"


def test_opensearch_domain_properties(database_stack_outputs, opensearch_client):
    endpoint = database_stack_outputs["OpenSearchEndpoint"]

    domains = opensearch_client.list_domain_names()["DomainNames"]

    domain_name = None
    for domain in domains:
        domain_info = opensearch_client.describe_domain(DomainName=domain["DomainName"])
        domain_status = domain_info["DomainStatus"]

        if (
            domain_status.get("Endpoint") == endpoint
            or domain_status.get("Endpoints", {}).get("vpc") == endpoint
        ):
            domain_name = domain["DomainName"]
            break

    assert (
        domain_name is not None
    ), f"Could not find OpenSearch domain for endpoint {endpoint}"

    response = opensearch_client.describe_domain(DomainName=domain_name)
    domain = response["DomainStatus"]

    assert (
        domain["EncryptionAtRestOptions"]["Enabled"] is True
    ), "OpenSearch domain must have encryption at rest enabled"
    assert (
        domain["NodeToNodeEncryptionOptions"]["Enabled"] is True
    ), "OpenSearch domain must have node-to-node encryption enabled"
    assert domain["VPCOptions"] is not None, "OpenSearch domain must be in VPC"

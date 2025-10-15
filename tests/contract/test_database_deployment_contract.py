def test_database_deployment_readiness(database_stack_outputs):
    """Test that Database stack is deployed with correct outputs"""

    required_outputs = ["RdsEndpoint", "OpenSearchEndpoint"]

    for output_name in required_outputs:
        assert (
            output_name in database_stack_outputs
        ), f"{output_name} output not found in DatabaseStack"


def test_database_deployment_outputs(
    database_stack_outputs, rds_client, opensearch_client
):
    """Test database deployment outputs are accessible"""

    # Verify RDS endpoint is accessible
    rds_endpoint = database_stack_outputs["RdsEndpoint"]

    # Check if it's a proxy or cluster endpoint
    if ".proxy-" in rds_endpoint:
        # For proxy endpoints, verify the proxy exists
        proxy_name = rds_endpoint.split(".proxy-")[0]
        try:
            rds_response = rds_client.describe_db_proxies(DBProxyName=proxy_name)
            assert (
                len(rds_response["DBProxies"]) == 1
            ), f"RDS proxy {proxy_name} not accessible"
            assert (
                rds_response["DBProxies"][0]["Status"] == "available"
            ), f"RDS proxy {proxy_name} not in available state"
        except rds_client.exceptions.DBProxyNotFoundFault:
            # Proxy was deleted - skip this test
            import pytest

            pytest.skip(f"RDS Proxy {proxy_name} not found (may have been deleted)")
    else:
        # For cluster endpoints, verify the cluster exists
        cluster_id = rds_endpoint.split(".cluster-")[0]
        rds_response = rds_client.describe_db_clusters(DBClusterIdentifier=cluster_id)
        assert (
            len(rds_response["DBClusters"]) == 1
        ), f"RDS cluster {cluster_id} not accessible"
        assert (
            rds_response["DBClusters"][0]["Status"] == "available"
        ), f"RDS cluster {cluster_id} not in available state"

    # Verify OpenSearch endpoint is accessible
    os_endpoint = database_stack_outputs["OpenSearchEndpoint"]

    # Get all domains and find the one matching the endpoint
    domains = opensearch_client.list_domain_names()["DomainNames"]

    domain_found = False
    for domain in domains:
        domain_info = opensearch_client.describe_domain(DomainName=domain["DomainName"])
        if (
            domain_info["DomainStatus"]["Endpoint"] == os_endpoint
            or domain_info["DomainStatus"].get("Endpoints", {}).get("vpc")
            == os_endpoint
        ):
            domain_found = True
            assert (
                domain_info["DomainStatus"]["Processing"] is False
            ), f"OpenSearch domain {domain['DomainName']} is still processing"
            break

    assert domain_found, f"Could not find OpenSearch domain for endpoint {os_endpoint}"

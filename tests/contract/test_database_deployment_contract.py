def test_database_deployment_readiness(database_stack_outputs):
    required_outputs = ["RdsEndpoint", "OpenSearchEndpoint"]

    for output_name in required_outputs:
        assert (
            output_name in database_stack_outputs
        ), f"{output_name} output not found in DatabaseStack"


def test_database_deployment_outputs(
    database_stack_outputs, rds_client, opensearch_client
):
    rds_endpoint = database_stack_outputs["RdsEndpoint"]

    if ".proxy-" in rds_endpoint:
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
            import pytest

            pytest.skip(f"RDS Proxy {proxy_name} not found (may have been deleted)")
    else:
        cluster_id = rds_endpoint.split(".cluster-")[0]
        rds_response = rds_client.describe_db_clusters(DBClusterIdentifier=cluster_id)
        assert (
            len(rds_response["DBClusters"]) == 1
        ), f"RDS cluster {cluster_id} not accessible"
        assert (
            rds_response["DBClusters"][0]["Status"] == "available"
        ), f"RDS cluster {cluster_id} not in available state"

    os_endpoint = database_stack_outputs["OpenSearchEndpoint"]

    domains = opensearch_client.list_domain_names()["DomainNames"]

    domain_found = False
    for domain in domains:
        domain_info = opensearch_client.describe_domain(DomainName=domain["DomainName"])
        domain_status = domain_info["DomainStatus"]
        domain_endpoint = domain_status.get("Endpoint") or domain_status.get(
            "Endpoints", {}
        ).get("vpc")

        if domain_endpoint == os_endpoint:
            domain_found = True
            assert (
                domain_status["Processing"] is False
            ), f"OpenSearch domain {domain['DomainName']} is still processing"
            break

    assert domain_found, f"Could not find OpenSearch domain for endpoint {os_endpoint}"

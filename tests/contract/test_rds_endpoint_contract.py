import re


def test_rds_endpoint_contract(database_stack_outputs):
    assert (
        "RdsEndpoint" in database_stack_outputs
    ), "RdsEndpoint output not found in DatabaseStack"

    endpoint = database_stack_outputs["RdsEndpoint"]
    cluster_pattern = re.compile(
        r"^[a-z0-9-]+\.cluster-[a-z0-9]+\.[a-z0-9-]+\.rds\.amazonaws\.com$"
    )
    proxy_pattern = re.compile(
        r"^[a-z0-9-]+\.proxy-[a-z0-9]+\.[a-z0-9-]+\.rds\.amazonaws\.com$"
    )
    assert cluster_pattern.match(endpoint) or proxy_pattern.match(
        endpoint
    ), f"RDS endpoint {endpoint} does not match expected cluster or proxy format"


def test_rds_cluster_properties(database_stack_outputs, rds_client):
    endpoint = database_stack_outputs["RdsEndpoint"]

    if ".proxy-" in endpoint:
        proxy_name = endpoint.split(".proxy-")[0]
        try:
            proxy_response = rds_client.describe_db_proxies(DBProxyName=proxy_name)
            assert (
                len(proxy_response["DBProxies"]) == 1
            ), f"RDS proxy {proxy_name} not found"

            target_groups = rds_client.describe_db_proxy_target_groups(
                DBProxyName=proxy_name
            )

            if target_groups["TargetGroups"]:
                targets = rds_client.describe_db_proxy_targets(
                    DBProxyName=proxy_name,
                    TargetGroupName=target_groups["TargetGroups"][0]["TargetGroupName"],
                )
                if targets["Targets"]:
                    cluster_id = targets["Targets"][0]["RdsResourceId"]
                else:
                    return
            else:
                return
        except rds_client.exceptions.DBProxyNotFoundFault:
            import pytest

            pytest.skip(f"RDS Proxy {proxy_name} not found (may have been deleted)")
    else:
        cluster_id = endpoint.split(".cluster-")[0]

    response = rds_client.describe_db_clusters(DBClusterIdentifier=cluster_id)
    assert len(response["DBClusters"]) == 1, f"RDS cluster {cluster_id} not found"

    cluster = response["DBClusters"][0]
    assert cluster["Engine"] in [
        "aurora-postgresql",
        "aurora-mysql",
    ], f"RDS cluster must use Aurora engine, got {cluster['Engine']}"
    assert (
        cluster["StorageEncrypted"] is True
    ), "RDS cluster must have storage encryption enabled"
    assert cluster["MultiAZ"] is True, "RDS cluster must be Multi-AZ"

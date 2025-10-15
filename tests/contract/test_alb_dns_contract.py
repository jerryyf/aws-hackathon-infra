def test_alb_dns_contract(network_stack_outputs):
    """Test that ALB DNS stack output matches contract specification"""
    
    assert "AlbDnsName" in network_stack_outputs, "AlbDnsName output not found in NetworkStack"
    
    alb_dns = network_stack_outputs["AlbDnsName"]
    # ALB DNS format: name-id.region.elb.amazonaws.com
    assert ".elb.amazonaws.com" in alb_dns, f"ALB DNS {alb_dns} does not match expected format"


def test_alb_properties(network_stack_outputs, elbv2_client):
    """Test ALB properties"""
    
    alb_dns = network_stack_outputs["AlbDnsName"]
    
    # Query ALB by DNS name
    response = elbv2_client.describe_load_balancers()
    albs = [alb for alb in response["LoadBalancers"] if alb["DNSName"] == alb_dns]
    
    assert len(albs) == 1, f"ALB with DNS {alb_dns} not found"
    
    alb = albs[0]
    assert alb["Scheme"] == "internet-facing", "ALB must be internet-facing"
    assert alb["Type"] == "application", "Load balancer must be Application Load Balancer"
    assert len(alb["AvailabilityZones"]) >= 2, "ALB must be in at least 2 AZs"

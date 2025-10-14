import pytest
import boto3
from botocore.exceptions import ClientError


@pytest.fixture
def cloudformation_client():
    return boto3.client('cloudformation', region_name='us-east-1')


@pytest.fixture
def ec2_client():
    return boto3.client('ec2', region_name='us-east-1')


@pytest.fixture
def network_stack_outputs(cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName='NetworkStack')
        outputs = {o['OutputKey']: o['OutputValue'] for o in response['Stacks'][0]['Outputs']}
        return outputs
    except ClientError:
        pytest.skip("NetworkStack not deployed")


def test_vpc_exists(ec2_client, network_stack_outputs):
    vpc_id = network_stack_outputs['VpcId']
    
    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    assert len(response['Vpcs']) == 1
    
    vpc = response['Vpcs'][0]
    assert vpc['CidrBlock'] == '10.0.0.0/16'
    assert vpc['EnableDnsSupport'] is True
    assert vpc['EnableDnsHostnames'] is True


def test_bedrock_agentcore_endpoint_exists(ec2_client, network_stack_outputs):
    endpoint_id = network_stack_outputs['BedrockAgentCoreEndpointId']
    vpc_id = network_stack_outputs['VpcId']
    
    response = ec2_client.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])
    assert len(response['VpcEndpoints']) == 1
    
    endpoint = response['VpcEndpoints'][0]
    assert endpoint['VpcEndpointType'] == 'Interface'
    assert endpoint['ServiceName'] == 'com.amazonaws.us-east-1.bedrock-agentcore'
    assert endpoint['VpcId'] == vpc_id
    assert endpoint['State'] == 'available'
    assert endpoint['PrivateDnsEnabled'] is True


def test_bedrock_agentcore_gateway_endpoint_exists(ec2_client, network_stack_outputs):
    endpoint_id = network_stack_outputs['BedrockAgentCoreGatewayEndpointId']
    vpc_id = network_stack_outputs['VpcId']
    
    response = ec2_client.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])
    assert len(response['VpcEndpoints']) == 1
    
    endpoint = response['VpcEndpoints'][0]
    assert endpoint['VpcEndpointType'] == 'Interface'
    assert endpoint['ServiceName'] == 'com.amazonaws.us-east-1.bedrock-agentcore.gateway'
    assert endpoint['VpcId'] == vpc_id
    assert endpoint['State'] == 'available'
    assert endpoint['PrivateDnsEnabled'] is True


def test_agentcore_endpoints_use_private_agent_subnets(ec2_client, network_stack_outputs):
    endpoint_id = network_stack_outputs['BedrockAgentCoreEndpointId']
    gateway_endpoint_id = network_stack_outputs['BedrockAgentCoreGatewayEndpointId']
    private_agent_subnet_ids = network_stack_outputs['PrivateAgentSubnetIds'].split(',')
    
    response = ec2_client.describe_vpc_endpoints(
        VpcEndpointIds=[endpoint_id, gateway_endpoint_id]
    )
    
    for endpoint in response['VpcEndpoints']:
        endpoint_subnets = endpoint['SubnetIds']
        for subnet_id in endpoint_subnets:
            assert subnet_id in private_agent_subnet_ids, f"Endpoint subnet {subnet_id} not in PrivateAgent subnets"


def test_agentcore_endpoints_span_multiple_azs(ec2_client, network_stack_outputs):
    endpoint_id = network_stack_outputs['BedrockAgentCoreEndpointId']
    
    response = ec2_client.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])
    endpoint = response['VpcEndpoints'][0]
    subnet_ids = endpoint['SubnetIds']
    
    assert len(subnet_ids) >= 2, "AgentCore endpoint should span at least 2 subnets for HA"
    
    subnet_response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
    azs = {subnet['AvailabilityZone'] for subnet in subnet_response['Subnets']}
    
    assert len(azs) >= 2, "AgentCore endpoint should span multiple availability zones"


def test_agentcore_runtime_security_group_exists(ec2_client, network_stack_outputs):
    sg_id = network_stack_outputs['AgentCoreRuntimeSecurityGroupId']
    vpc_id = network_stack_outputs['VpcId']
    
    response = ec2_client.describe_security_groups(GroupIds=[sg_id])
    assert len(response['SecurityGroups']) == 1
    
    sg = response['SecurityGroups'][0]
    assert sg['VpcId'] == vpc_id
    assert sg['GroupDescription'] == 'Security group for Bedrock AgentCore agent runtimes'


def test_agentcore_runtime_security_group_egress_rules(ec2_client, network_stack_outputs):
    sg_id = network_stack_outputs['AgentCoreRuntimeSecurityGroupId']
    
    response = ec2_client.describe_security_groups(GroupIds=[sg_id])
    sg = response['SecurityGroups'][0]
    
    egress_rules = sg['IpPermissionsEgress']
    
    https_rule_found = False
    for rule in egress_rules:
        if (rule.get('IpProtocol') == 'tcp' and 
            rule.get('FromPort') == 443 and 
            rule.get('ToPort') == 443):
            if any(ip_range.get('CidrIp') == '0.0.0.0/0' for ip_range in rule.get('IpRanges', [])):
                https_rule_found = True
                break
    
    assert https_rule_found, "Security group should allow HTTPS (443) egress to 0.0.0.0/0"


def test_agentcore_runtime_security_group_no_default_egress(ec2_client, network_stack_outputs):
    sg_id = network_stack_outputs['AgentCoreRuntimeSecurityGroupId']
    
    response = ec2_client.describe_security_groups(GroupIds=[sg_id])
    sg = response['SecurityGroups'][0]
    
    egress_rules = sg['IpPermissionsEgress']
    
    all_traffic_rule_found = False
    for rule in egress_rules:
        if rule.get('IpProtocol') == '-1':
            if any(ip_range.get('CidrIp') == '0.0.0.0/0' for ip_range in rule.get('IpRanges', [])):
                all_traffic_rule_found = True
                break
    
    assert not all_traffic_rule_found, "Security group should not have default allow-all egress rule"


def test_private_agent_subnets_exist(ec2_client, network_stack_outputs):
    private_agent_subnet_ids = network_stack_outputs['PrivateAgentSubnetIds'].split(',')
    vpc_id = network_stack_outputs['VpcId']
    
    assert len(private_agent_subnet_ids) >= 2, "Should have at least 2 private agent subnets"
    
    response = ec2_client.describe_subnets(SubnetIds=private_agent_subnet_ids)
    
    for subnet in response['Subnets']:
        assert subnet['VpcId'] == vpc_id
        assert subnet['MapPublicIpOnLaunch'] is False, "Private agent subnets should not auto-assign public IPs"


def test_private_agent_subnets_span_multiple_azs(ec2_client, network_stack_outputs):
    private_agent_subnet_ids = network_stack_outputs['PrivateAgentSubnetIds'].split(',')
    
    response = ec2_client.describe_subnets(SubnetIds=private_agent_subnet_ids)
    
    azs = {subnet['AvailabilityZone'] for subnet in response['Subnets']}
    assert len(azs) >= 2, "Private agent subnets should span multiple availability zones"


def test_private_agent_subnets_have_nat_gateway_routes(ec2_client, network_stack_outputs):
    private_agent_subnet_ids = network_stack_outputs['PrivateAgentSubnetIds'].split(',')
    
    response = ec2_client.describe_subnets(SubnetIds=private_agent_subnet_ids)
    
    for subnet in response['Subnets']:
        route_table_response = ec2_client.describe_route_tables(
            Filters=[
                {'Name': 'association.subnet-id', 'Values': [subnet['SubnetId']]}
            ]
        )
        
        assert len(route_table_response['RouteTables']) > 0, f"Subnet {subnet['SubnetId']} should have associated route table"
        
        route_table = route_table_response['RouteTables'][0]
        routes = route_table['Routes']
        
        nat_gateway_route_found = False
        for route in routes:
            if route.get('DestinationCidrBlock') == '0.0.0.0/0' and 'NatGatewayId' in route:
                nat_gateway_route_found = True
                break
        
        assert nat_gateway_route_found, f"Private agent subnet {subnet['SubnetId']} should have NAT gateway route"


def test_vpc_endpoint_security_groups(ec2_client, network_stack_outputs):
    endpoint_id = network_stack_outputs['BedrockAgentCoreEndpointId']
    
    response = ec2_client.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])
    endpoint = response['VpcEndpoints'][0]
    
    assert len(endpoint.get('Groups', [])) > 0, "VPC endpoint should have security groups attached"


def test_vpc_dns_resolution_enabled(ec2_client, network_stack_outputs):
    vpc_id = network_stack_outputs['VpcId']
    
    response = ec2_client.describe_vpc_attribute(
        VpcId=vpc_id,
        Attribute='enableDnsSupport'
    )
    assert response['EnableDnsSupport']['Value'] is True
    
    response = ec2_client.describe_vpc_attribute(
        VpcId=vpc_id,
        Attribute='enableDnsHostnames'
    )
    assert response['EnableDnsHostnames']['Value'] is True

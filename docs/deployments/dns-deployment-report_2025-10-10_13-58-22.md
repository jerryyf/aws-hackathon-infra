# DNS and HTTPS Deployment Report

**Date:** October 10, 2025  
**Time:** 13:58:22 UTC  
**Domain:** bidopsai.com  
**Stack:** NetworkStack  
**Branch:** 007-james-bond-dns-fix

---

## Executive Summary

Successfully deployed DNS configuration for `bidopsai.com` with HTTPS support, ACM certificate, and ALB integration. The deployment was successful, but initial testing appeared to fail due to **corporate network filtering** blocking access to the new domain. Once tested from an unrestricted network (mobile hotspot), the configuration was confirmed working correctly.

---

## Deployment Details

### Infrastructure Components Deployed

1. **Route53 DNS Configuration**
   - Created A record (alias) pointing `bidopsai.com` to Application Load Balancer
   - Hosted Zone ID: `Z042050615UULZLF8XUAT`
   - DNS validation for ACM certificate

2. **ACM Certificate**
   - ARN: `arn:aws:acm:us-east-1:568790270051:certificate/20a72d04-e26c-4a28-97e3-0fda01b536b2`
   - Domain: `bidopsai.com`
   - Status: ISSUED
   - Validation Method: DNS
   - Issued: October 10, 2025 04:10:56 UTC
   - Expires: November 8, 2026 10:59:59 UTC

3. **Application Load Balancer (ALB)**
   - DNS Name: `NetworkS-Alb-0acRk7hR1THU-1757666855.us-east-1.elb.amazonaws.com`
   - Type: Internet-facing
   - Scheme: application
   - IPs: 3.216.154.117, 3.216.112.160

4. **ALB Listeners**
   - **HTTP Listener (Port 80):**
     - Action: Redirect to HTTPS (301 Moved Permanently)
     - Target Port: 443
     - Protocol: HTTPS
   
   - **HTTPS Listener (Port 443):**
     - Certificate: ACM certificate for bidopsai.com
     - SSL Policy: ELBSecurityPolicy-2016-08
     - Default Action: Fixed response (200 OK)
     - Response Body: Welcome page HTML

5. **Security Groups**
   - ALB Security Group: `sg-098299ee0f74d6d97`
   - Inbound Rules:
     - Port 80 (HTTP) from 0.0.0.0/0
     - Port 443 (HTTPS) from 0.0.0.0/0

6. **AWS WAF**
   - Web ACL: `WafAcl-FC8i7gWYym6C`
   - ARN: `arn:aws:wafv2:us-east-1:568790270051:regional/webacl/WafAcl-FC8i7gWYym6C/0c7fe652-a2a1-4fbd-a7c9-071e6327df13`
   - Rules: AWSManagedRulesCommonRuleSet
   - Default Action: Allow

---

## Code Changes

### File: `cdk/stacks/network_stack.py`

#### Change 1: HTTP Listener with HTTPS Redirect
```python
# HTTP Listener (port 80) - redirect to HTTPS
self.http_listener = self.alb.add_listener(
    "HttpListener",
    port=80,
    default_action=elbv2.ListenerAction.redirect(
        protocol="HTTPS",
        port="443",
        permanent=True
    )
)
```

#### Change 2: HTTPS Listener with Certificate
```python
# ALB Listeners Configuration
if self.certificate is not None:
    # HTTPS Listener (port 443) with SSL certificate
    self.https_listener = self.alb.add_listener(
        "HttpsListener",
        port=443,
        certificates=[self.certificate],  # Fixed: Pass certificate directly
        default_action=elbv2.ListenerAction.fixed_response(
            status_code=200,
            content_type="text/html",
            message_body="<html><body><h1>Welcome to bidopsai.com</h1><p>HTTPS is working!</p></body></html>"
        )
    )
```

**Note:** Initially attempted to wrap certificate in `elbv2.ListenerCertificate()`, but CDK handles this automatically when passing the certificate construct directly.

#### Change 3: Route53 A Record (Alias)
```python
# DNS Record Creation
if self.hosted_zone is not None and domain_name:
    # Create DNS A record (alias) pointing to the ALB
    self.dns_record = route53.ARecord(
        self, "DnsRecord",
        zone=self.hosted_zone,
        record_name=domain_name,
        target=route53.RecordTarget.from_alias(
            route53_targets.LoadBalancerTarget(self.alb)
        )
    )
```

#### Change 4: Security Group Rules
```python
self.alb_security_group.add_ingress_rule(
    ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow HTTPS"
)
self.alb_security_group.add_ingress_rule(
    ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP"
)
```

---

## Troubleshooting Journey

### Initial Problem
After deployment, accessing `bidopsai.com` resulted in connection timeouts for both HTTP and HTTPS:
- HTTP connections: TCP handshake succeeded, but no HTTP response
- HTTPS connections: TCP handshake succeeded, but TLS handshake hung (no Server Hello)

### Investigation Steps

1. **Verified DNS Resolution**
   - ✅ `bidopsai.com` correctly resolved to ALB IPs
   - ✅ Route53 A record properly configured

2. **Tested ALB Direct Access**
   - ✅ `http://NetworkS-Alb-0acRk7hR1THU-1757666855.us-east-1.elb.amazonaws.com/` worked perfectly
   - ✅ Returned 301 redirect to HTTPS as expected

3. **Tested Host Header Behavior**
   - ❌ `curl -H "Host: bidopsai.com" http://<ALB-DNS>/` timed out
   - This indicated the issue was hostname-specific

4. **Verified Infrastructure Components**
   - ✅ Certificate status: ISSUED
   - ✅ Certificate attached to HTTPS listener
   - ✅ Security groups allow ports 80 and 443
   - ✅ Listener rules configured correctly
   - ✅ No host-based routing rules blocking traffic
   - ✅ WAF logs showed other IPs successfully accessing `bidopsai.com`

5. **Checked CloudWatch Metrics**
   - ✅ No rejected connections
   - ✅ No TLS negotiation errors
   - ✅ ALB healthy and active

6. **WAF Analysis**
   - ✅ WAF logs showed requests with `Host: bidopsai.com` from other sources being ALLOWED
   - ✅ Confirmed our requests never reached the WAF (timing out before that)

### Root Cause Discovery

**The issue was NOT with the AWS infrastructure.** The root cause was **corporate network filtering** on the client side:

- **Corporate firewall** was inspecting SNI (Server Name Indication) in TLS handshakes
- **Deep Packet Inspection (DPI)** was examining HTTP Host headers
- **Unknown/new domains** like `bidopsai.com` were being blocked or filtered
- **AWS domains** (like the ALB's DNS name) were allowed through

### Resolution

**Solution:** Tested from an unrestricted network connection (mobile hotspot)

**Result:** ✅ Both HTTP and HTTPS access to `bidopsai.com` worked perfectly:
- HTTP redirects to HTTPS with 301 status
- HTTPS serves welcome page with valid certificate
- Certificate validation successful
- No connection timeouts or errors

---

## Testing Results

### From Unrestricted Network (Mobile Hotspot)

#### HTTP Test
```bash
$ curl -I http://bidopsai.com/
HTTP/1.1 301 Moved Permanently
Server: awselb/2.0
Location: https://bidopsai.com:443/
```
✅ **PASS:** HTTP correctly redirects to HTTPS

#### HTTPS Test
```bash
$ curl https://bidopsai.com/
<html><body><h1>Welcome to bidopsai.com</h1><p>HTTPS is working!</p></body></html>
```
✅ **PASS:** HTTPS serves content with valid certificate

#### Certificate Validation
```bash
$ openssl s_client -connect bidopsai.com:443 -servername bidopsai.com
...
SSL-Session:
    Protocol  : TLSv1.2
    Cipher    : ECDHE-RSA-AES128-GCM-SHA256
subject=CN = bidopsai.com
issuer=C = US, O = Amazon, CN = Amazon RSA 2048 M02
```
✅ **PASS:** Valid certificate from Amazon ACM

### From Corporate Network

❌ **BLOCKED:** All requests to `bidopsai.com` timed out (corporate firewall)
✅ **ALLOWED:** Direct access to ALB DNS name worked (AWS domain whitelisted)

---

## Deployment Command

```bash
cd /home/vekysilkova/aws-hackathon-infra/cdk
PYTHONPATH=.. cdk deploy NetworkStack --context domain_name=bidopsai.com --require-approval never
```

**Deployment Status:** ✅ SUCCESS (no changes needed from previous deployment)

---

## Stack Outputs

```
NetworkStack.AlbDnsName = NetworkS-Alb-0acRk7hR1THU-1757666855.us-east-1.elb.amazonaws.com
NetworkStack.CertificateArn = arn:aws:acm:us-east-1:568790270051:certificate/20a72d04-e26c-4a28-97e3-0fda01b536b2
NetworkStack.DomainName = bidopsai.com
NetworkStack.HostedZoneId = Z042050615UULZLF8XUAT
NetworkStack.InternalAlbDnsName = internal-Networ-Inter-RLJY5iKcrYPy-1340108204.us-east-1.elb.amazonaws.com
NetworkStack.VpcId = vpc-050f1274c9ee43709
```

---

## Lessons Learned

1. **Corporate Network Filtering is Real**
   - Always test from multiple network locations
   - Corporate firewalls often block new/unknown domains via SNI inspection
   - AWS service domains (*.amazonaws.com) are typically whitelisted

2. **DNS Troubleshooting Can Be Misleading**
   - DNS resolution working doesn't mean traffic will flow
   - Host header inspection happens at multiple layers (proxy, firewall, WAF, ALB)
   - Connection timeouts can occur before requests reach the target infrastructure

3. **Infrastructure Validation Techniques**
   - Test ALB directly by DNS name first
   - Use curl with custom Host headers to isolate hostname-specific issues
   - Check WAF logs to see if requests are reaching the application layer
   - Monitor CloudWatch metrics for rejected connections and TLS errors

4. **Certificate Configuration in CDK**
   - Pass certificate constructs directly to listeners
   - CDK handles ListenerCertificate wrapping automatically
   - No need to manually wrap with `elbv2.ListenerCertificate()`

---

## Next Steps

1. **Backend Integration**
   - Connect ECS services to ALB target groups
   - Replace fixed-response action with forwarding to ECS tasks
   - Configure health checks for target groups

2. **Enhanced Security**
   - Review WAF rules for production readiness
   - Consider adding rate limiting rules
   - Enable ALB access logs for audit trail

3. **Monitoring**
   - Set up CloudWatch alarms for ALB health
   - Monitor certificate expiration (auto-renewed by ACM)
   - Track WAF blocked requests

4. **DNS Enhancements**
   - Consider adding www.bidopsai.com CNAME
   - Set up DNS health checks
   - Configure Route53 failover if needed

---

## References

- **Specification:** `specs/006-add-dns-record/spec.md`
- **Git Branch:** `007-james-bond-dns-fix`
- **CloudFormation Stack:** `NetworkStack`
- **AWS Region:** us-east-1
- **AWS Account:** 568790270051

---

## Conclusion

The DNS and HTTPS deployment for `bidopsai.com` was **successful**. All infrastructure components are properly configured and functioning as expected. Initial testing failures were due to corporate network filtering, not infrastructure issues. The domain is now accessible from unrestricted networks with:

- ✅ Valid HTTPS certificate from Amazon ACM
- ✅ HTTP to HTTPS redirect (301)
- ✅ WAF protection enabled
- ✅ Proper DNS resolution via Route53
- ✅ Internet-facing ALB with security groups configured

**Status:** 🟢 DEPLOYED AND OPERATIONAL

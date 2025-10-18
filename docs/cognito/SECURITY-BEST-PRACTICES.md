# 🔐 Security Best Practices Guide
**For: AWS Hackathon Infrastructure - Cognito Test Users**

## ⚠️ Current Security Issues

### **Problem:**
We have hardcoded test user passwords in multiple places:
- `scripts/create-test-users.sh` - Contains passwords like `AdminPass123!@#`
- `docs/cognito-deployment-readiness_2025-10-15.md` - Lists all passwords
- `docs/cognito-testing-guide_2025-10-15.md` - Contains password table
- `docs/cognito-integration-analysis_2025-10-15.md` - Shows example passwords

**These files should NOT be committed to a public repository!**

---

## ✅ Recommended Solutions

### **Option 1: Environment Variables (BEST for team sharing)**

#### Step 1: Create a `.env` file (NOT in git)
```bash
# File: .env
# DO NOT COMMIT THIS FILE!

COGNITO_ADMIN_PASSWORD="YourSecurePassword123!@#"
COGNITO_DRAFTER_PASSWORD="YourSecurePassword456!@#"
COGNITO_BIDDER_PASSWORD="YourSecurePassword789!@#"
COGNITO_KBADMIN_PASSWORD="YourSecurePassword012!@#"
COGNITO_VIEWER_PASSWORD="YourSecurePassword345!@#"
```

#### Step 2: Update `scripts/create-test-users.sh`
```bash
#!/bin/bash
# Load environment variables
if [ -f .env ]; then
  export $(cat .env | xargs)
fi

# Use environment variables instead of hardcoded passwords
if create_user "admin" "admin@bidopsai.local" "Admin" "User" "ADMIN" "$COGNITO_ADMIN_PASSWORD"; then
  USERS_CREATED+=("admin")
fi
```

#### Step 3: Share passwords securely
- Use **AWS Secrets Manager** (costs ~$0.40/month per secret)
- Use **1Password**, **LastPass**, or **Bitwarden** for team sharing
- Share via encrypted email/Slack DM (NOT in repo)

---

### **Option 2: AWS Secrets Manager (BEST for production)**

#### Step 1: Store secrets in AWS
```bash
# Store each password in Secrets Manager
aws secretsmanager create-secret \
  --name /bidopsai/dev/cognito/admin-password \
  --secret-string "YourSecurePassword123!@#" \
  --region us-east-1

aws secretsmanager create-secret \
  --name /bidopsai/dev/cognito/drafter-password \
  --secret-string "YourSecurePassword456!@#" \
  --region us-east-1

# ... repeat for all users
```

#### Step 2: Update script to fetch from Secrets Manager
```bash
#!/bin/bash

# Fetch passwords from AWS Secrets Manager
ADMIN_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id /bidopsai/dev/cognito/admin-password \
  --query SecretString \
  --output text \
  --region us-east-1)

# Use fetched password
if create_user "admin" "admin@bidopsai.local" "Admin" "User" "ADMIN" "$ADMIN_PASSWORD"; then
  USERS_CREATED+=("admin")
fi
```

**Cost:** ~$2/month (5 secrets × $0.40/month)

---

### **Option 3: Generate Random Passwords (BEST for dev/test)**

#### Update script to auto-generate passwords
```bash
#!/bin/bash

# Function to generate random password
generate_password() {
  openssl rand -base64 16 | tr -dc 'A-Za-z0-9!@#$%^&*' | head -c 16
  echo "!@#"  # Add special chars to meet policy
}

# Generate random passwords
ADMIN_PASSWORD=$(generate_password)
DRAFTER_PASSWORD=$(generate_password)
BIDDER_PASSWORD=$(generate_password)
KBADMIN_PASSWORD=$(generate_password)
VIEWER_PASSWORD=$(generate_password)

# Create users with generated passwords
if create_user "admin" "admin@bidopsai.local" "Admin" "User" "ADMIN" "$ADMIN_PASSWORD"; then
  USERS_CREATED+=("admin")
  echo "Admin password: $ADMIN_PASSWORD" >> .test-passwords  # Save locally, gitignored
fi
```

**Pros:**
- No hardcoded passwords
- Each run creates new passwords
- Passwords saved to `.test-passwords` (gitignored)

---

### **Option 4: FORCE_CHANGE_PASSWORD (Acceptable for dev)**

Keep hardcoded passwords BUT force users to change on first login:

```bash
# Don't use --permanent flag
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username admin \
  --password "TempPassword123!@#" \
  --region $REGION
  # NO --permanent flag = user MUST change password on first login
```

**Pros:**
- Simple for dev/test
- Hardcoded password only works once
- Each user sets their own secure password

**Cons:**
- Still exposes temp password in repo
- Not suitable for production

---

## 🎯 **Recommended Approach for Your Use Case**

### **For Development/Testing (NOW):**
Use **Option 4 (FORCE_CHANGE_PASSWORD)**

```bash
# Update scripts/create-test-users.sh - remove --permanent flag
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username "$username" \
  --password "$password" \
  --region $REGION
  # Removed: --permanent
```

**Why:**
- ✅ Simple to implement
- ✅ Hardcoded passwords are temporary only
- ✅ Each team member sets their own password
- ✅ Good enough for bidopsai/dev environment

### **For Production (LATER):**
Use **Option 2 (AWS Secrets Manager)**

**Why:**
- ✅ Centralized secret management
- ✅ Automatic rotation support
- ✅ Audit trail (who accessed what/when)
- ✅ IAM-based access control
- ✅ Industry best practice

---

## 📝 **Immediate Action Items**

### 1. Update `.gitignore` ✅ (DONE)
Already added:
```
docs/*credentials*.md
docs/*passwords*.md
scripts/test-user-credentials.txt
scripts/.test-passwords
```

### 2. Remove Passwords from Docs (OPTIONAL)
You have 3 options:

**Option A: Keep docs but add warning**
Add this to top of each doc:
```markdown
⚠️ **WARNING:** This document contains test credentials for DEV ONLY.
DO NOT use these passwords in production. Change them immediately after first login.
```

**Option B: Move to separate file**
```bash
# Create a separate credentials file (gitignored)
mv docs/cognito-testing-guide_2025-10-15.md docs/.credentials/testing-guide.md
mv docs/cognito-deployment-readiness_2025-10-15.md docs/.credentials/deployment-readiness.md
```

**Option C: Remove passwords entirely**
Replace passwords with:
```markdown
| Username | Password |
|----------|----------|
| admin@bidopsai.local | [See team password manager] |
| drafter@bidopsai.local | [See team password manager] |
```

### 3. Update Test User Script

**Quick Fix (5 min):**
```bash
# Edit scripts/create-test-users.sh
# Line 88: Remove --permanent flag
# This forces password change on first login
```

**Better Fix (15 min):**
```bash
# Add environment variable support
# Check if COGNITO_ADMIN_PASSWORD is set, else use default
PASSWORD="${COGNITO_ADMIN_PASSWORD:-AdminPass123!@#}"
```

---

## 🔒 **Additional Security Best Practices**

### 1. Rotate Test User Passwords Regularly
```bash
# Every 90 days, run:
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_3tjXn7pNM \
  --username admin \
  --password "NewPassword123!@#" \
  --permanent \
  --region us-east-1
```

### 2. Delete Test Users in Production
```bash
# Before going to production, delete ALL test users
aws cognito-idp admin-delete-user \
  --user-pool-id $PROD_USER_POOL_ID \
  --username admin \
  --region us-east-1
```

### 3. Enable MFA for Admin Users
```bash
# Require MFA for ADMIN group in production
# Update security_stack.py:
mfa_configuration=cognito.Mfa.REQUIRED  # For prod environment
```

### 4. Monitor Failed Login Attempts
```bash
# Set up CloudWatch alarm
aws cloudwatch put-metric-alarm \
  --alarm-name cognito-failed-signins \
  --metric-name UserAuthenticationFailures \
  --namespace AWS/Cognito \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

### 5. Use IP Whitelisting (If Possible)
For admin accounts, consider restricting access to office/VPN IPs using Lambda triggers.

---

## 📊 **Security Comparison Table**

| Solution | Security | Ease of Use | Cost | Recommended For |
|----------|----------|-------------|------|-----------------|
| **Hardcoded (current)** | ❌ Low | ✅ Easy | Free | ❌ Never |
| **Env Variables** | ⚠️ Medium | ✅ Easy | Free | Dev/Test |
| **AWS Secrets Manager** | ✅ High | ⚠️ Medium | $2/mo | Production |
| **FORCE_CHANGE_PASSWORD** | ⚠️ Medium | ✅ Easy | Free | Dev/Test |
| **Random Generation** | ✅ High | ⚠️ Medium | Free | CI/CD |

---

## 🚀 **Quick Win: 5-Minute Security Improvement**

Run these commands NOW:

```bash
cd /home/vekysilkova/aws-bidopsai-infra

# 1. Make all test users change password on next login
USER_POOL_ID="us-east-1_3tjXn7pNM"
REGION="us-east-1"

for username in admin drafter bidder kbadmin viewer; do
  aws cognito-idp admin-reset-user-password \
    --user-pool-id $USER_POOL_ID \
    --username $username \
    --region $REGION
  echo "✓ Reset password for $username - will be prompted to change on next login"
done

# 2. Add warning to README
echo "⚠️ **Test Credentials:** Change all test user passwords after first login!" >> README.md
```

This invalidates all hardcoded passwords and forces everyone to set new ones! 🎯

---

## 📚 **Additional Resources**

- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [AWS Cognito Security Best Practices](https://docs.aws.amazon.com/cognito/latest/developerguide/security-best-practices.html)

---

**Last Updated:** October 15, 2025  
**Status:** 🟡 Needs attention before production deployment

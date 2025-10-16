# How to Test Cognito with bidopsai.com

**Date:** October 15, 2025  
**Environment:** dev  
**Domain:** bidopsai.com  

## 🎉 Deployment Complete!

Your Cognito User Pool is now deployed and configured to work with **bidopsai.com**!

---

## 📋 Cognito Configuration Details

### User Pool Information
- **User Pool ID:** `us-east-1_3tjXn7pNM`
- **User Pool ARN:** `arn:aws:cognito-idp:us-east-1:568790270051:userpool/us-east-1_3tjXn7pNM`
- **App Client ID:** `4uci08tqhijkrncjbebr3hu60q`
- **Domain:** `hackathon-dev.auth.us-east-1.amazoncognito.com`
- **Region:** `us-east-1`

### Callback URLs (Configured)
✅ http://localhost:3000/callback  
✅ http://localhost:3000/api/auth/callback/cognito  
✅ **https://bidopsai.com/callback**  
✅ **https://www.bidopsai.com/callback**  
✅ **https://bidopsai.com/api/auth/callback/cognito**  
✅ **https://www.bidopsai.com/api/auth/callback/cognito**  

### Logout URLs (Configured)
✅ http://localhost:3000  
✅ http://localhost:3000/signin  
✅ **https://bidopsai.com**  
✅ **https://www.bidopsai.com**  
✅ **https://bidopsai.com/signin**  
✅ **https://www.bidopsai.com/signin**  

---

## 👥 Test Users Created

All 5 test users have been created with the following credentials:

| Username | Email | Password | Group | Precedence |
|----------|-------|----------|-------|------------|
| admin | admin@hackathon.local | AdminPass123!@# | ADMIN | 1 |
| drafter | drafter@hackathon.local | DrafterPass123!@# | DRAFTER | 2 |
| bidder | bidder@hackathon.local | BidderPass123!@# | BIDDER | 3 |
| kbadmin | kbadmin@hackathon.local | KbadminPass123!@# | KB_ADMIN | 4 |
| viewer | viewer@hackathon.local | ViewerPass123!@# | KB_VIEW | 5 |

⚠️ **Note:** These passwords are permanent (no forced change required on first login).

---

## 🧪 Option 1: Test via Cognito Hosted UI (Easiest - No Frontend Needed)

### Step 1: Build the Login URL

Use this URL pattern (replace `{REDIRECT_URI}` with your callback):

```
https://hackathon-dev.auth.us-east-1.amazoncognito.com/login?client_id=4uci08tqhijkrncjbebr3hu60q&response_type=code&scope=email+openid+profile+phone&redirect_uri={REDIRECT_URI}
```

### Example URLs:

**For bidopsai.com:**
```
https://hackathon-dev.auth.us-east-1.amazoncognito.com/login?client_id=4uci08tqhijkrncjbebr3hu60q&response_type=code&scope=email+openid+profile+phone&redirect_uri=https://bidopsai.com/callback
```

**For localhost:**
```
https://hackathon-dev.auth.us-east-1.amazoncognito.com/login?client_id=4uci08tqhijkrncjbebr3hu60q&response_type=code&scope=email+openid+profile+phone&redirect_uri=http://localhost:3000/callback
```

### Step 2: Open the URL in Browser

1. Open the login URL in your browser
2. You'll see the Cognito Hosted UI login page with "hackathon-dev" branding
3. Login with any test user (e.g., `admin@hackathon.local` / `AdminPass123!@#`)
4. Click "Sign In"

### Step 3: Handle the Redirect

After successful login, you'll be redirected to your callback URL with an authorization code:

```
https://bidopsai.com/callback?code=abc123xyz789...
```

This code can be exchanged for JWT tokens using the Cognito Token endpoint.

---

## 🌐 Option 2: Test with Real Frontend at bidopsai.com

### Prerequisites
- Frontend application deployed at bidopsai.com
- AWS Amplify (or similar) installed in frontend
- Application Load Balancer routing to frontend

### Step 1: Configure AWS Amplify in Frontend

Add this to your frontend application (e.g., in `src/aws-exports.js` or config file):

```javascript
import { Amplify } from 'aws-amplify';

Amplify.configure({
  Auth: {
    region: 'us-east-1',
    userPoolId: 'us-east-1_3tjXn7pNM',
    userPoolWebClientId: '4uci08tqhijkrncjbebr3hu60q',
    oauth: {
      domain: 'hackathon-dev.auth.us-east-1.amazoncognito.com',
      scope: ['email', 'openid', 'profile', 'phone'],
      redirectSignIn: 'https://bidopsai.com/callback',
      redirectSignOut: 'https://bidopsai.com',
      responseType: 'code'
    }
  }
});
```

### Step 2: Add Sign-In Button to Frontend

```javascript
import { Auth } from 'aws-amplify';

// Sign in button handler
const handleSignIn = async () => {
  try {
    await Auth.federatedSignIn();
  } catch (error) {
    console.error('Error signing in:', error);
  }
};

// In your component
<button onClick={handleSignIn}>Sign In</button>
```

### Step 3: Handle Callback in Frontend

Create a callback route (e.g., `/callback`):

```javascript
import { Auth } from 'aws-amplify';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function CallbackPage() {
  const navigate = useNavigate();

  useEffect(() => {
    // Amplify automatically handles the OAuth callback
    Auth.currentAuthenticatedUser()
      .then(user => {
        console.log('User logged in:', user);
        navigate('/dashboard'); // Redirect to your app
      })
      .catch(err => {
        console.error('Auth error:', err);
        navigate('/'); // Redirect to home on error
      });
  }, []);

  return <div>Processing login...</div>;
}
```

### Step 4: Get Current User Info

```javascript
import { Auth } from 'aws-amplify';

// Get current authenticated user
const getCurrentUser = async () => {
  try {
    const user = await Auth.currentAuthenticatedUser();
    console.log('User:', user);
    console.log('Username:', user.username);
    console.log('Email:', user.attributes.email);
    console.log('Groups:', user.signInUserSession.accessToken.payload['cognito:groups']);
    return user;
  } catch (error) {
    console.log('Not authenticated:', error);
    return null;
  }
};

// Sign out
const handleSignOut = async () => {
  try {
    await Auth.signOut();
    console.log('Signed out successfully');
  } catch (error) {
    console.error('Error signing out:', error);
  }
};
```

### Step 5: Test the Full Flow

1. Navigate to `https://bidopsai.com`
2. Click "Sign In" button
3. Browser redirects to Cognito Hosted UI
4. Login with test credentials (e.g., admin@hackathon.local)
5. After successful login, redirected back to `https://bidopsai.com/callback`
6. Frontend exchanges code for tokens automatically
7. User is now authenticated and can access protected routes

---

## 🖥️ Option 3: Test via AWS Console (Manual Verification)

### Step 1: Open Cognito Console

1. Go to AWS Console: https://console.aws.amazon.com/cognito
2. Region: **us-east-1**
3. Click on "User Pools"
4. Select `hackathon-users-dev`

### Step 2: Verify Configuration

Check the following tabs:

**Users tab:**
- ✅ 5 users should be visible (admin, drafter, bidder, kbadmin, viewer)
- ✅ All users should have status "CONFIRMED" or "FORCE_CHANGE_PASSWORD"

**Groups tab:**
- ✅ 5 groups should exist: ADMIN, DRAFTER, BIDDER, KB_ADMIN, KB_VIEW
- ✅ Each user should be assigned to their respective group

**App integration tab:**
- ✅ Domain: `hackathon-dev.auth.us-east-1.amazoncognito.com`
- ✅ App client: `hackathon-web-dev`
- ✅ Callback URLs include bidopsai.com
- ✅ OAuth flows: Authorization code grant

**Sign-in experience tab:**
- ✅ Password policy: 12 characters minimum
- ✅ MFA: Optional
- ✅ Self-service account recovery: Enabled

### Step 3: Test User Login via Console

1. In the "App integration" tab, scroll to "App clients and analytics"
2. Click on `hackathon-web-dev`
3. Click "View Hosted UI"
4. This opens the Cognito Hosted UI
5. Login with test credentials
6. You'll be redirected to your callback URL

---

## 🔧 Option 4: Test with Postman/cURL (OAuth Flow)

### Step 1: Get Authorization Code

Open this URL in browser:
```
https://hackathon-dev.auth.us-east-1.amazoncognito.com/login?client_id=4uci08tqhijkrncjbebr3hu60q&response_type=code&scope=email+openid+profile+phone&redirect_uri=https://bidopsai.com/callback
```

After login, copy the `code` parameter from the redirect URL.

### Step 2: Exchange Code for Tokens

```bash
curl -X POST \
  https://hackathon-dev.auth.us-east-1.amazoncognito.com/oauth2/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=authorization_code' \
  -d 'client_id=4uci08tqhijkrncjbebr3hu60q' \
  -d 'code=<YOUR_CODE_HERE>' \
  -d 'redirect_uri=https://bidopsai.com/callback'
```

### Step 3: Parse Token Response

Response will contain:
```json
{
  "id_token": "eyJraWQiOiI...",
  "access_token": "eyJraWQiOiI...",
  "refresh_token": "eyJjdHki...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

### Step 4: Decode ID Token

Go to https://jwt.io and paste the `id_token` to see user information:

```json
{
  "sub": "448854e8-c0b1-7087-94c4-93c5cbe0fcec",
  "cognito:groups": ["ADMIN"],
  "email_verified": true,
  "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_3tjXn7pNM",
  "cognito:username": "admin",
  "origin_jti": "...",
  "aud": "4uci08tqhijkrncjbebr3hu60q",
  "token_use": "id",
  "auth_time": 1729031234,
  "exp": 1729034834,
  "iat": 1729031234,
  "email": "admin@hackathon.local"
}
```

---

## 📱 Testing Checklist

### Basic Authentication
- [ ] Can access Cognito Hosted UI
- [ ] Can login with admin user
- [ ] Can login with drafter user
- [ ] Can login with bidder user
- [ ] Can login with kbadmin user
- [ ] Can login with viewer user
- [ ] Redirected to correct callback URL after login
- [ ] Authorization code present in redirect URL

### Token Validation
- [ ] Can exchange authorization code for tokens
- [ ] ID token contains correct user email
- [ ] ID token contains correct cognito:groups claim
- [ ] Access token is valid JWT
- [ ] Refresh token can be used to get new tokens

### Group Permissions (Frontend Implementation Required)
- [ ] ADMIN user can access all features
- [ ] DRAFTER user can create/edit drafts
- [ ] BIDDER user can view/respond to opportunities
- [ ] KB_ADMIN user can manage knowledge base
- [ ] KB_VIEW user can only read knowledge base

### Logout
- [ ] Can sign out via Amplify
- [ ] Redirected to logout URL
- [ ] Cannot access protected routes after logout
- [ ] Can sign in again after logout

### Error Handling
- [ ] Invalid credentials show error message
- [ ] Expired tokens are refreshed automatically
- [ ] Network errors are handled gracefully

---

## 🚀 Next Steps

### 1. Deploy Frontend to bidopsai.com

If you don't have a frontend deployed yet:

```bash
# Example for Next.js app
cd your-frontend-repo
npm install aws-amplify
# Add Amplify configuration (see Option 2 above)
npm run build
# Deploy to S3 or use existing ALB setup
```

### 2. Update ALB to Route to Frontend

Your ALB is already set up:
- **ALB DNS:** NetworkS-Alb-0acRk7hR1THU-1757666855.us-east-1.elb.amazonaws.com
- **Domain:** bidopsai.com (already pointing to ALB)

Make sure your target group routes to your frontend application.

### 3. Add Protected Routes

In your frontend, protect routes based on authentication:

```javascript
import { Auth } from 'aws-amplify';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

function ProtectedRoute({ children, requiredGroup }) {
  const [isAuthorized, setIsAuthorized] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const user = await Auth.currentAuthenticatedUser();
      const groups = user.signInUserSession.accessToken.payload['cognito:groups'] || [];
      
      if (requiredGroup && !groups.includes(requiredGroup)) {
        navigate('/unauthorized');
        return;
      }
      
      setIsAuthorized(true);
    } catch (error) {
      navigate('/login');
    }
  };

  return isAuthorized ? children : <div>Loading...</div>;
}

// Usage:
<ProtectedRoute requiredGroup="ADMIN">
  <AdminDashboard />
</ProtectedRoute>
```

### 4. Add User Profile Page

Show logged-in user information:

```javascript
import { Auth } from 'aws-amplify';
import { useEffect, useState } from 'react';

function ProfilePage() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const currentUser = await Auth.currentAuthenticatedUser();
      setUser({
        username: currentUser.username,
        email: currentUser.attributes.email,
        groups: currentUser.signInUserSession.accessToken.payload['cognito:groups'] || []
      });
    } catch (error) {
      console.error('Error loading user:', error);
    }
  };

  if (!user) return <div>Loading...</div>;

  return (
    <div>
      <h1>Profile</h1>
      <p>Username: {user.username}</p>
      <p>Email: {user.email}</p>
      <p>Groups: {user.groups.join(', ')}</p>
    </div>
  );
}
```

### 5. Production Checklist (Before Going Live)

- [ ] Change environment to `prod` in deployment
- [ ] Update callback URLs to production domain (remove localhost)
- [ ] Enable deletion protection on User Pool
- [ ] Set up CloudWatch alarms for failed logins
- [ ] Enable AWS WAF on ALB
- [ ] Set up CloudTrail logging for Cognito
- [ ] Require MFA for ADMIN users
- [ ] Configure custom email templates
- [ ] Set up SES for email delivery (higher limits)
- [ ] Add custom domain for Cognito (e.g., auth.bidopsai.com)
- [ ] Review and update password policy if needed
- [ ] Set up user backup/export process
- [ ] Document disaster recovery procedure

---

## 🐛 Troubleshooting

### Issue: "Redirect URI mismatch" error

**Solution:** Make sure the redirect_uri in your request exactly matches one of the configured callback URLs (case-sensitive, including protocol).

### Issue: "Invalid client_id" error

**Solution:** Verify you're using the correct App Client ID: `4uci08tqhijkrncjbebr3hu60q`

### Issue: Can't access Hosted UI

**Solution:** Check that the domain `hackathon-dev.auth.us-east-1.amazoncognito.com` is active in Cognito console.

### Issue: bidopsai.com not loading

**Solution:** Verify:
1. ALB is healthy: `aws elbv2 describe-target-health --target-group-arn <ARN>`
2. Route53 pointing to ALB
3. Frontend application is deployed to target group

### Issue: CORS errors in browser

**Solution:** Configure CORS in your API/backend to allow requests from bidopsai.com:

```python
# Example for Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['https://bidopsai.com', 'https://www.bidopsai.com'])
```

### Issue: Tokens not being saved

**Solution:** Amplify stores tokens in browser storage. Check:
1. Browser allows localStorage/sessionStorage
2. Not in private/incognito mode
3. No browser extensions blocking storage

---

## 📞 Support & Resources

### AWS Documentation
- [Cognito User Pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html)
- [AWS Amplify Auth](https://docs.amplify.aws/lib/auth/getting-started/q/platform/js/)
- [OAuth 2.0 Authorization Code Flow](https://oauth.net/2/grant-types/authorization-code/)

### Quick Links
- **AWS Console (Cognito):** https://console.aws.amazon.com/cognito
- **JWT Debugger:** https://jwt.io
- **OAuth Debugger:** https://oauthdebugger.com

### CloudFormation Stack
- **Stack Name:** SecurityStack
- **Region:** us-east-1
- **Status:** ✅ CREATE_COMPLETE

---

## 🎉 Summary

Your Cognito User Pool is **fully configured and ready to use** with bidopsai.com!

### Quick Test (No Frontend Needed):

**1. Open this URL in your browser:**
```
https://hackathon-dev.auth.us-east-1.amazoncognito.com/login?client_id=4uci08tqhijkrncjbebr3hu60q&response_type=code&scope=email+openid+profile+phone&redirect_uri=https://bidopsai.com/callback
```

**2. Login with:**
- **Username:** `admin@hackathon.local`
- **Password:** `AdminPass123!@#`

**3. After login, you'll be redirected to:**
```
https://bidopsai.com/callback?code=<authorization_code>
```

That authorization code is what your frontend will exchange for JWT tokens!

---

**Generated:** October 15, 2025  
**Stack:** SecurityStack  
**Environment:** dev  
**Status:** ✅ Deployed and Ready

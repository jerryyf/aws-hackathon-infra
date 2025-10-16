# 🔑 Cognito User IDs for Frontend Seed File

**Generated:** October 15, 2025  
**User Pool:** us-east-1_3tjXn7pNM  
**Region:** us-east-1

---

## 📋 **1. Environment Variables for Frontend**

Copy these to your frontend repo's `.env.local`:

```bash
# AWS Cognito Configuration (NEW - Updated Oct 15, 2025)
NEXT_PUBLIC_AWS_REGION=us-east-1
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_3tjXn7pNM
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=4uci08tqhijkrncjbebr3hu60q
NEXT_PUBLIC_COGNITO_DOMAIN=hackathon-dev.auth.us-east-1.amazoncognito.com

# GraphQL API Endpoint (keep existing)
NEXT_PUBLIC_API_URL=http://localhost:4000/graphql

# Agent Core API Endpoint (keep existing)
NEXT_PUBLIC_AGENT_CORE_URL=http://localhost:8000

# Application Settings (keep existing)
NEXT_PUBLIC_APP_NAME=BidOps.AI
NEXT_PUBLIC_APP_VERSION=1.0.0
NEXT_PUBLIC_ENABLE_DEBUG=false
NEXT_PUBLIC_ENABLE_ANALYTICS=false
```

---

## 👥 **2. Cognito User IDs (for Prisma Seed)**

Use these exact IDs in your `prisma/seed.ts` file:

| Username | Email | Cognito ID (sub) | Group |
|----------|-------|------------------|-------|
| admin | admin@hackathon.local | `0458b4f8-6061-702c-6c6a-38b488fa7ab3` | ADMIN |
| drafter | drafter@hackathon.local | `6458e4c8-5041-70d1-a27c-d7017f823697` | DRAFTER |
| bidder | bidder@hackathon.local | `c4787458-50a1-70fe-1689-de097c06e9f3` | BIDDER |
| kbadmin | kbadmin@hackathon.local | `24088408-c041-70cc-8502-2e8cf144f168` | KB_ADMIN |
| viewer | viewer@hackathon.local | `448854e8-c0b1-7087-94c4-93c5cbe0fcec` | KB_VIEW |

---

## 📝 **3. Ready-to-Use Seed File Code**

Copy/paste this into your `prisma/seed.ts`:

```typescript
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  console.log('🌱 Starting database seed...')

  // Admin User
  const admin = await prisma.user.upsert({
    where: { email: 'admin@hackathon.local' },
    update: {
      cognitoId: '0458b4f8-6061-702c-6c6a-38b488fa7ab3',
    },
    create: {
      cognitoId: '0458b4f8-6061-702c-6c6a-38b488fa7ab3',
      email: 'admin@hackathon.local',
      firstName: 'Admin',
      lastName: 'User',
      role: 'ADMIN',
      isActive: true,
    },
  })
  console.log('✓ Created admin user')

  // Drafter User
  const drafter = await prisma.user.upsert({
    where: { email: 'drafter@hackathon.local' },
    update: {
      cognitoId: '6458e4c8-5041-70d1-a27c-d7017f823697',
    },
    create: {
      cognitoId: '6458e4c8-5041-70d1-a27c-d7017f823697',
      email: 'drafter@hackathon.local',
      firstName: 'Draft',
      lastName: 'Creator',
      role: 'DRAFTER',
      isActive: true,
    },
  })
  console.log('✓ Created drafter user')

  // Bidder User
  const bidder = await prisma.user.upsert({
    where: { email: 'bidder@hackathon.local' },
    update: {
      cognitoId: 'c4787458-50a1-70fe-1689-de097c06e9f3',
    },
    create: {
      cognitoId: 'c4787458-50a1-70fe-1689-de097c06e9f3',
      email: 'bidder@hackathon.local',
      firstName: 'Bid',
      lastName: 'Manager',
      role: 'BIDDER',
      isActive: true,
    },
  })
  console.log('✓ Created bidder user')

  // KB Admin User
  const kbadmin = await prisma.user.upsert({
    where: { email: 'kbadmin@hackathon.local' },
    update: {
      cognitoId: '24088408-c041-70cc-8502-2e8cf144f168',
    },
    create: {
      cognitoId: '24088408-c041-70cc-8502-2e8cf144f168',
      email: 'kbadmin@hackathon.local',
      firstName: 'KB',
      lastName: 'Admin',
      role: 'KB_ADMIN',
      isActive: true,
    },
  })
  console.log('✓ Created kbadmin user')

  // Viewer User
  const viewer = await prisma.user.upsert({
    where: { email: 'viewer@hackathon.local' },
    update: {
      cognitoId: '448854e8-c0b1-7087-94c4-93c5cbe0fcec',
    },
    create: {
      cognitoId: '448854e8-c0b1-7087-94c4-93c5cbe0fcec',
      email: 'viewer@hackathon.local',
      firstName: 'Knowledge',
      lastName: 'Viewer',
      role: 'KB_VIEW',
      isActive: true,
    },
  })
  console.log('✓ Created viewer user')

  console.log('✅ Database seeded successfully!')
  console.log({
    admin: admin.email,
    drafter: drafter.email,
    bidder: bidder.email,
    kbadmin: kbadmin.email,
    viewer: viewer.email,
  })
}

main()
  .catch((e) => {
    console.error('❌ Seed failed:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
```

---

## 🔐 **4. Test User Login Credentials**

After seeding, test login with these credentials:

| Email | Password | Role |
|-------|----------|------|
| admin@hackathon.local | AdminPass123!@# | ADMIN |
| drafter@hackathon.local | DrafterPass123!@# | DRAFTER |
| bidder@hackathon.local | BidderPass123!@# | BIDDER |
| kbadmin@hackathon.local | KbadminPass123!@# | KB_ADMIN |
| viewer@hackathon.local | ViewerPass123!@# | KB_VIEW |

**⚠️ Note:** You'll be prompted to change password on first login.

---

## 🚀 **5. Step-by-Step Setup**

### **In your FRONTEND repo:**

```bash
# 1. Update environment variables
nano .env.local
# (Paste the env vars from section 1 above)

# 2. Update seed file
nano prisma/seed.ts
# (Paste the code from section 3 above)

# 3. Start all services
podman-compose -f infra/docker/docker-compose.dev.yml up --build

# Wait for services to start (you'll see "Server listening on port 4000")

# 4. In a NEW terminal - Run migrations
podman exec bidopsai-core-api-dev npm run prisma:migrate

# 5. In a NEW terminal - Seed database
podman exec bidopsai-core-api-dev npm run prisma:seed

# You should see:
# ✓ Created admin user
# ✓ Created drafter user
# ✓ Created bidder user
# ✓ Created kbadmin user
# ✓ Created viewer user
# ✅ Database seeded successfully!

# 6. In a NEW terminal - Restart backend
podman restart bidopsai-core-api-dev
```

---

## ✅ **6. Verify Everything Works**

### **Test 1: Check Database**
```bash
podman exec -it bidopsai-postgres-dev psql -U postgres -d bidopsai

SELECT email, "cognitoId", role FROM users;

# Should show all 5 users with their Cognito IDs
```

### **Test 2: Test Login**
1. Open http://localhost:3000
2. Click "Sign In"
3. Should redirect to: `hackathon-dev.auth.us-east-1.amazoncognito.com`
4. Login with: `admin@hackathon.local` / `AdminPass123!@#`
5. Set new password when prompted
6. Should redirect back to localhost:3000
7. You're logged in! ✅

### **Test 3: GraphQL Query**
Open http://localhost:4000/graphql and run:

```graphql
query {
  me {
    id
    email
    cognitoId
    role
    firstName
    lastName
  }
}

# Should return your user info with the matching Cognito ID
```

---

## 🔍 **7. Troubleshooting**

### **Issue: "User not found after login"**
**Cause:** Database user's cognitoId doesn't match Cognito user's sub  
**Fix:** Double-check the IDs in seed file match the table above

### **Issue: "Invalid redirect URI"**
**Cause:** Cognito not configured for localhost:3000  
**Fix:** Already fixed! We added localhost callbacks in deployment

### **Issue: "Wrong user pool"**
**Cause:** Frontend still using old pool (ap-southeast-2_pEbKG4pjd)  
**Fix:** Update .env.local with values from section 1

### **Issue: "Cannot execute prisma:seed"**
**Cause:** Backend container not running  
**Fix:** Make sure step 3 (up --build) completed successfully

---

## 📊 **8. Architecture Flow**

```
User visits localhost:3000
    ↓
Clicks "Sign In"
    ↓
Redirects to: hackathon-dev.auth.us-east-1.amazoncognito.com
    ↓
Enters: admin@hackathon.local / AdminPass123!@#
    ↓
Cognito validates credentials ✅
    ↓
Redirects back to: localhost:3000/callback?code=abc123...
    ↓
Frontend exchanges code for JWT tokens
    ↓
Frontend calls GraphQL: query { me { ... } }
    ↓
Backend validates JWT token
    ↓
Backend extracts cognitoId from token (sub claim)
    ↓
Backend queries database: SELECT * FROM users WHERE cognitoId = '0458b4f8-...'
    ↓
Returns user data ✅
    ↓
User is logged in and sees their dashboard!
```

---

## 📝 **9. Quick Copy-Paste Checklist**

For your senior or team members:

**Step 1: Update .env.local**
```bash
NEXT_PUBLIC_AWS_REGION=us-east-1
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_3tjXn7pNM
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=4uci08tqhijkrncjbebr3hu60q
NEXT_PUBLIC_COGNITO_DOMAIN=hackathon-dev.auth.us-east-1.amazoncognito.com
```

**Step 2: Update prisma/seed.ts Cognito IDs**
```typescript
admin:   '0458b4f8-6061-702c-6c6a-38b488fa7ab3'
drafter: '6458e4c8-5041-70d1-a27c-d7017f823697'
bidder:  'c4787458-50a1-70fe-1689-de097c06e9f3'
kbadmin: '24088408-c041-70cc-8502-2e8cf144f168'
viewer:  '448854e8-c0b1-7087-94c4-93c5cbe0fcec'
```

**Step 3: Run commands**
```bash
podman-compose -f infra/docker/docker-compose.dev.yml up --build
podman exec bidopsai-core-api-dev npm run prisma:migrate
podman exec bidopsai-core-api-dev npm run prisma:seed
podman restart bidopsai-core-api-dev
```

**Step 4: Test**
- Open http://localhost:3000
- Login with: admin@hackathon.local / AdminPass123!@#
- ✅ Done!

---

**Generated:** October 15, 2025  
**Valid for:** Hackathon development environment  
**User Pool:** us-east-1_3tjXn7pNM (us-east-1)

---

**Questions?** Check `docs/FRONTEND-SETUP-COMMANDS-EXPLAINED.md` for detailed explanations!

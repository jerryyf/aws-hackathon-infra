# 🎯 Frontend Setup Commands Explained (ELI5)

## **Command Breakdown**

### **1. Start All Services**
```bash
podman-compose -f infra/docker/docker-compose.dev.yml up --build
```

**What it does:**
- `podman-compose` = Like Docker, runs containers (isolated mini-computers)
- `-f infra/docker/docker-compose.dev.yml` = "Use this recipe file"
- `up` = "Start all the services"
- `--build` = "Rebuild from scratch if needed"

**In simple terms:**
🚀 **Starts your entire application stack:**
- Frontend (Next.js UI)
- Backend API (GraphQL)
- Agent Core (AI workflow engine)
- Database (PostgreSQL)
- Any other services defined in the compose file

**Like:** Turning on all the lights in a house at once

**What you'll see:**
- Lots of terminal output
- Services starting up
- Database initializing
- "Server listening on port 4000" or similar

---

### **2. Run Database Migrations**
```bash
podman exec bidopsai-core-api-dev npm run prisma:migrate
```

**What it does:**
- `podman exec` = "Run a command INSIDE a running container"
- `bidopsai-core-api-dev` = The name of the backend API container
- `npm run prisma:migrate` = Run Prisma migrations

**In simple terms:**
🗄️ **Creates/updates your database tables:**
- Reads migration files (like blueprints)
- Creates tables: `users`, `bids`, `documents`, etc.
- Adds columns, indexes, relationships
- Updates database schema to match your code

**Like:** Building the filing cabinets before you can store files

**What you'll see:**
```
✔ Generated Prisma Client
✔ Applied migration: 20251015_create_users
✔ Applied migration: 20251015_create_bids
Database is now up to date!
```

---

### **3. Seed the Database** ⚠️ (THIS IS WHERE YOU UPDATE COGNITO USERS)
```bash
podman exec bidopsai-core-api-dev npm run prisma:seed
```

**What it does:**
- Runs the seed script: `prisma/seed.ts` (or similar)
- Populates database with **initial test data**

**In simple terms:**
🌱 **Plants starter data in your database:**
- Creates test users
- Creates sample bids/documents
- Sets up initial roles/permissions
- Links users to Cognito IDs

**IMPORTANT:** This is where your senior said to **"update user details > COGNITO USERS"**

**What the seed script probably does:**
```typescript
// prisma/seed.ts (example)
await prisma.user.create({
  data: {
    cognitoId: 'OLD_USER_ID_FROM_OLD_COGNITO',  // ❌ NEEDS UPDATING
    email: 'admin@bidopsai.com',
    role: 'ADMIN',
    // ...
  }
})
```

**You need to update it to:**
```typescript
await prisma.user.create({
  data: {
    cognitoId: 'NEW_USER_ID_FROM_OUR_COGNITO',  // ✅ NEW VALUE
    email: 'admin@bidopsai.local',  // Match our Cognito users
    role: 'ADMIN',
    // ...
  }
})
```

**Like:** Planting seeds in a garden - but you need to plant the RIGHT seeds!

---

### **4. Restart Backend API**
```bash
podman restart bidopsai-core-api-dev
```

**What it does:**
- Stops the backend API container
- Starts it again fresh

**In simple terms:**
🔄 **Reboots the backend API** to pick up changes:
- Reloads environment variables
- Reconnects to database
- Clears any cached data
- Applies new Cognito config

**Like:** Turning it off and on again (the universal IT fix!)

**What you'll see:**
```
bidopsai-core-api-dev
```
(Just the container name, then it restarts)

---

## 🔗 **How They Work Together**

```
Step 1: Start Everything
   ↓
   [Frontend] [Backend API] [Database] [Agent Core]
   
Step 2: Prepare Database
   ↓
   [Create tables: users, bids, documents, etc.]
   
Step 3: Add Test Data ⚠️ (UPDATE COGNITO IDs HERE!)
   ↓
   [Insert users with Cognito IDs]
   [Insert sample bids/documents]
   
Step 4: Restart Backend
   ↓
   [Backend reloads with new Cognito config]
   ✅ Everything connected!
```

---

## 🎯 **What You Need to Update (Step 3)**

### **Before Step 3, you need to:**

1. **Find the seed file:**
   - Probably in: `prisma/seed.ts` or `prisma/seed.js`
   - Or: `src/prisma/seed.ts` in your frontend repo

2. **Get Cognito User IDs from AWS:**
   ```bash
   # Get the real Cognito user IDs (sub values)
   aws cognito-idp list-users \
     --user-pool-id us-east-1_3tjXn7pNM \
     --region us-east-1 \
     --query 'Users[*].[Username, Attributes[?Name==`sub`].Value | [0]]' \
     --output table
   ```

3. **Update the seed file:**
   ```typescript
   // OLD (probably uses old Cognito IDs)
   const users = [
     {
       cognitoId: 'OLD_ID_FROM_OLD_POOL',
       email: 'admin@bidopsai.com',
       role: 'ADMIN'
     }
   ]
   
   // NEW (use IDs from our Cognito)
   const users = [
     {
       cognitoId: '24088408-c041-70cc-8502-2e8cf144f168',  // From AWS list
       email: 'admin@bidopsai.local',  // Match our users
       role: 'ADMIN',
       firstName: 'Admin',
       lastName: 'User'
     },
     {
       cognitoId: '6458e4c8-5041-70d1-a27c-d7017f823697',
       email: 'drafter@bidopsai.local',
       role: 'DRAFTER',
       firstName: 'Draft',
       lastName: 'Creator'
     },
     // ... etc for all 5 users
   ]
   ```

---

## 📋 **Full Workflow with Real Values**

### **Step 0: Update Environment Variables** (Do this first!)

In your frontend repo, update `.env.local`:
```bash
# OLD
NEXT_PUBLIC_AWS_REGION=ap-southeast-2
NEXT_PUBLIC_COGNITO_USER_POOL_ID=ap-southeast-2_pEbKG4pjd
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=65o9d0v0lcquh23bqsi3ck6711

# NEW ✅
NEXT_PUBLIC_AWS_REGION=us-east-1
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_3tjXn7pNM
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=4uci08tqhijkrncjbebr3hu60q
NEXT_PUBLIC_COGNITO_DOMAIN=bidopsai-dev.auth.us-east-1.amazoncognito.com
```

### **Step 1: Get Cognito User IDs**
```bash
cd /home/vekysilkova/aws-bidopsai-infra

# List all users with their Cognito IDs (sub)
aws cognito-idp list-users \
  --user-pool-id us-east-1_3tjXn7pNM \
  --region us-east-1 \
  --query 'Users[*].[Username, Attributes[?Name==`sub`].Value | [0], Attributes[?Name==`email`].Value | [0]]' \
  --output table
```

**Example output:**
```
-------------------------------------------------------------------------------------------------
|                                           ListUsers                                           |
+----------+--------------------------------------+---------------------------+
| admin    | 24088408-c041-70cc-8502-2e8cf144f168 | admin@bidopsai.local     |
| drafter  | 6458e4c8-5041-70d1-a27c-d7017f823697 | drafter@bidopsai.local   |
| bidder   | c4787458-50a1-70fe-1689-de097c06e9f3 | bidder@bidopsai.local    |
| kbadmin  | 24088408-c041-70cc-8502-2e8cf144f168 | kbadmin@bidopsai.local   |
| viewer   | 448854e8-c0b1-7087-94c4-93c5cbe0fcec | viewer@bidopsai.local    |
+----------+--------------------------------------+---------------------------+
```

### **Step 2: Update Seed File**

In your **frontend repo**, find and edit `prisma/seed.ts`:

```typescript
// Example seed file update
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  // Create users with REAL Cognito IDs from our deployment
  const admin = await prisma.user.upsert({
    where: { email: 'admin@bidopsai.local' },
    update: {},
    create: {
      cognitoId: '24088408-c041-70cc-8502-2e8cf144f168',  // ✅ From AWS
      email: 'admin@bidopsai.local',
      firstName: 'Admin',
      lastName: 'User',
      role: 'ADMIN',
    },
  })

  const drafter = await prisma.user.upsert({
    where: { email: 'drafter@bidopsai.local' },
    update: {},
    create: {
      cognitoId: '6458e4c8-5041-70d1-a27c-d7017f823697',  // ✅ From AWS
      email: 'drafter@bidopsai.local',
      firstName: 'Draft',
      lastName: 'Creator',
      role: 'DRAFTER',
    },
  })

  // ... repeat for other users

  console.log('✅ Seeded users:', { admin, drafter })
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
```

### **Step 3: Run the Commands**

```bash
cd /path/to/your/frontend/repo

# 1. Start everything
podman-compose -f infra/docker/docker-compose.dev.yml up --build

# Wait for services to start (30-60 seconds)
# You should see: "Server listening on port 4000" or similar

# 2. In a NEW terminal - Run migrations
podman exec bidopsai-core-api-dev npm run prisma:migrate

# 3. In a NEW terminal - Seed database (with updated Cognito IDs)
podman exec bidopsai-core-api-dev npm run prisma:seed

# 4. In a NEW terminal - Restart backend
podman restart bidopsai-core-api-dev
```

---

## ✅ **How to Know It Worked**

### **After Step 1 (up --build):**
- Services are running
- Can access http://localhost:3000 (frontend)
- Can access http://localhost:4000/graphql (backend)

### **After Step 2 (migrate):**
- Database tables created
- Can connect to DB and see empty tables

### **After Step 3 (seed):**
- Database has test users
- Users have Cognito IDs matching our deployment
- Can query users in database

### **After Step 4 (restart):**
- Backend reconnects with new env vars
- Authentication works with our Cognito
- Can login with: admin@bidopsai.local / AdminPass123!@#

---

## 🔍 **Testing the Integration**

### **Test 1: Check Database**
```bash
# Connect to database container
podman exec -it bidopsai-postgres-dev psql -U postgres -d bidopsai

# Query users
SELECT email, "cognitoId", role FROM users;

# Should see:
# admin@bidopsai.local | 24088408-c041-70cc-8502-2e8cf144f168 | ADMIN
# drafter@bidopsai.local | 6458e4c8-5041-70d1-a27c-d7017f823697 | DRAFTER
# ...
```

### **Test 2: Login Flow**
1. Open http://localhost:3000
2. Click "Sign In"
3. Should redirect to: `bidopsai-dev.auth.us-east-1.amazoncognito.com`
4. Login with: `admin@bidopsai.local` / `AdminPass123!@#`
5. Should redirect back to localhost:3000 with auth token
6. Should see user profile/dashboard

### **Test 3: GraphQL Query**
```graphql
# At http://localhost:4000/graphql
query {
  me {
    id
    email
    cognitoId
    role
  }
}

# Should return your logged-in user info
```

---

## 🚨 **Common Issues**

### **Issue 1: "User not found in database"**
**Cause:** Cognito IDs in seed don't match Cognito IDs in AWS  
**Fix:** Re-run the AWS command to get real IDs, update seed file

### **Issue 2: "Invalid redirect URI"**
**Cause:** Frontend trying to use http://localhost:3000/callback but not in Cognito  
**Fix:** Already fixed! We added localhost callbacks in our deployment

### **Issue 3: "Wrong region"**
**Cause:** Frontend still using ap-southeast-2  
**Fix:** Update .env.local to use us-east-1

### **Issue 4: "Cannot connect to database"**
**Cause:** Database not started or wrong connection string  
**Fix:** Check docker-compose logs, ensure postgres container running

---

## 📝 **Quick Checklist**

Before running the commands:
- [ ] Updated `.env.local` with new Cognito values
- [ ] Got Cognito user IDs from AWS
- [ ] Updated `prisma/seed.ts` with real Cognito IDs
- [ ] Emails match: use `@bidopsai.local` not `@bidopsai.com`

After running commands:
- [ ] All services started successfully
- [ ] Database migrations applied
- [ ] Seed data inserted
- [ ] Backend restarted
- [ ] Can login at localhost:3000
- [ ] User data shows in database

---

## 🎯 **TL;DR (Too Long; Didn't Read)**

```bash
# What the commands do:
1. up --build        → Start all services (frontend, backend, database)
2. prisma:migrate    → Create database tables
3. prisma:seed       → Add test users (UPDATE COGNITO IDs BEFORE THIS!)
4. restart           → Reboot backend with new config

# What YOU need to do:
1. Get Cognito IDs from AWS (run aws cognito-idp list-users)
2. Update seed file with those IDs
3. Update .env.local with our Cognito settings
4. Run the 4 commands
5. Test login!
```

---

**Need help with any specific step?** Let me know! 🚀

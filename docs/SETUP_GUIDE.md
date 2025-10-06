# SIONYX Setup Guide - Simplified Security Model

## Overview

This setup uses a **single super admin** (you) who has full control over all organizations.

### Permission Model

```
┌────────────────────────────────────┐
│     YOU (Super Admin)              │
│  - Create/delete organizations     │
│  - Full access to all orgs         │
└────────────────────────────────────┘
           ↓ creates/manages
┌────────────────────────────────────┐
│     Organization Admins            │
│  - Manage users in their org       │
│  - Create/edit packages            │
│  - View purchases                  │
└────────────────────────────────────┘
           ↓ manages
┌────────────────────────────────────┐
│     Regular Users                  │
│  - Access own data                 │
│  - Make purchases                  │
└────────────────────────────────────┘
```

---

## Initial Setup

### Step 1: Create Your Super Admin Account

1. **Go to Firebase Console**
   - URL: https://console.firebase.google.com
   - Select your project

2. **Create Super Admin User**
   - Go to: **Authentication → Users**
   - Click **"Add user"**
   - Email: `your-email@example.com` (use your real email)
   - Password: Create a strong password (save it securely!)
   - Click **"Add user"**
   - **Copy the User UID** (e.g., `abc123xyz456...`)

3. **Set Super Admin UID in Database**
   - Go to: **Realtime Database**
   - Click the **"+"** at root level
   - Add:
     ```
     Name: config
     Value: [Leave as object]
     ```
   - Click the **"+"** next to `config`
   - Add:
     ```
     Name: superAdminUid
     Value: [Paste your User UID here]
     ```

4. **Save Your Credentials Securely**
   ```
   Super Admin Email: your-email@example.com
   Super Admin Password: [Your password]
   Super Admin UID: abc123xyz456...
   ```
   Store in password manager or secure location!

---

### Step 2: Deploy Security Rules

```bash
# From project root directory
firebase deploy --only database
```

**Verify deployment:**
- Firebase Console → **Realtime Database → Rules**
- Check "Last deployed" timestamp
- Rules should reference `config/superAdminUid`

---

### Step 3: Deploy Cloud Functions (Optional)

```bash
cd functions
npm install
firebase deploy --only functions
```

This deploys the payment callback handler.

---

## Creating Organizations

### Method: Interactive Script

```bash
python tests/install_organization.py
```

**What the script does:**

1. **Authenticates you as super admin**
   - Prompts for your super admin email/password
   - Verifies you're the configured super admin
   - Gets full database access

2. **Collects organization details**
   - Organization ID (e.g., `tech-lab`)
   - Organization display name (e.g., `Tech Lab`)
   - Checks if org already exists

3. **Creates admin user for the org**
   - Admin first/last name
   - Admin phone number
   - Admin password
   - Sets `isAdmin: true` for this user

4. **Optionally seeds starter packages**
   - 3 pre-configured packages
   - Can skip if you want custom packages

5. **Verifies installation**
   - Checks org metadata exists
   - Confirms admin user created
   - Lists any packages created

### Example Session

```
============================================================
  🚀 SIONYX Organization Installation
============================================================

⚠️  SUPER ADMIN AUTHENTICATION REQUIRED
This script requires super admin credentials to create organizations.

============================================================
  Super Admin Login
============================================================

Super Admin Email: admin@sionyx.com
Super Admin Password: ********

ℹ️  Authenticating as super admin...
✅ Authenticated as super admin (UID: abc123...)
✅ Super admin verified

============================================================
  Organization Details
============================================================

Enter the organization ID (lowercase, letters/numbers/hyphens only)
Examples: myorg, tech-lab, school123
Organization ID: tech-lab

ℹ️  Checking if organization 'tech-lab' exists...

Organization ID: tech-lab
Database: https://your-project.firebaseio.com

Continue with installation for 'tech-lab'? (y/n): y

Organization Display Name: Tech Lab

ℹ️  Creating organization metadata...
✅ Organization metadata created: Tech Lab

============================================================
  Create Admin User
============================================================

This admin will be able to manage packages and users.

Admin First Name: John
Admin Last Name: Doe
Admin Phone (e.g., 0501234567): 0501234567
Admin Password (min 6 chars): ******

ℹ️  Creating admin account...
✅ Admin account created (UID: def456...)
✅ Admin user created: John Doe
ℹ️  Login with phone: 0501234567

============================================================
  Create Starter Packages
============================================================

Create starter packages? (y/n): y

ℹ️  Creating 3 starter packages...

  📦 Package 1/3: Quick Session
     Price: ₪25 | Time: 30min | Prints: 5
     ✅ Created with ID: -Nxyz123

  📦 Package 2/3: Standard Hour
     Price: ₪40 | Time: 60min | Prints: 10
     ✅ Created with ID: -Nxyz124

  📦 Package 3/3: Power User
     Price: ₪100 | Time: 180min | Prints: 30
     ✅ Created with ID: -Nxyz125

✅ Starter packages created

============================================================
  Verification
============================================================

✅ Organization metadata
✅ Admin user (1 found)
✅ Packages (3 found)

============================================================
  Installation Complete! 🎉
============================================================

Your organization is ready to use!

Next steps:
  1. Login with phone: 0501234567
  2. Launch the app: python src/main.py
  3. Create additional users through registration

Firebase Console:
  https://console.firebase.google.com/
  Check: Realtime Database → organizations/tech-lab/

✅ Installation successful!
```

---

## Database Structure Created

After running the installation script:

```
Firebase Realtime Database
│
├── config/
│   └── superAdminUid: "your-uid"
│
└── organizations/
    └── tech-lab/                    ← Your organization
        ├── metadata/
        │   ├── name: "Tech Lab"
        │   ├── createdAt: "2025-10-06..."
        │   └── status: "active"
        │
        ├── users/
        │   └── {adminUid}/
        │       ├── firstName: "John"
        │       ├── lastName: "Doe"
        │       ├── phoneNumber: "0501234567"
        │       ├── isAdmin: true        ← Can manage org
        │       ├── remainingTime: 0
        │       └── remainingPrints: 0
        │
        └── packages/
            ├── {pkgId1}/
            │   ├── name: "Quick Session"
            │   ├── minutes: 30
            │   ├── prints: 5
            │   └── price: 25
            │
            ├── {pkgId2}/
            └── {pkgId3}/
```

---

## Configuring Client Apps

On each organization's computers, create a `.env` file:

```bash
# Organization Configuration
ORG_ID=tech-lab

# Firebase Configuration
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_PROJECT_ID=your-project-id

# Payment Gateway
NEDARIM_MOSAD_ID=your_mosad_id
NEDARIM_API_VALID=your_api_valid
NEDARIM_CALLBACK_URL=https://your-function-url/nedarimCallback
```

**Important:** Each organization must have a unique `ORG_ID` matching what you created!

---

## Security Rules Explained

### Super Admin Access

```javascript
"organizations": {
  ".read": "root.child('config').child('superAdminUid').val() == auth.uid",
  ".write": "root.child('config').child('superAdminUid').val() == auth.uid"
}
```

- You (super admin) can read/write ALL organizations
- Used for creating orgs and troubleshooting

### Organization Admin Access

```javascript
"packages": {
  ".read": "auth != null",
  "$packageId": {
    ".write": "root.child('organizations').child($orgId).child('users').child(auth.uid).child('isAdmin').val() === true"
  }
}
```

- Org admins can create/modify packages
- Regular users can only read packages

### Regular User Access

```javascript
"users": {
  "$userId": {
    ".read": "auth.uid == $userId || [org admin check]",
    ".write": "auth.uid == $userId || [org admin check]"
  }
}
```

- Users can read/write their own data
- Org admins can read/write all users in their org
- Cannot make themselves admin

---

## Managing Organizations

### View All Organizations

As super admin, you can see all orgs in Firebase Console:
- **Realtime Database → organizations/**
- Each child is an organization

### Add More Organizations

Simply run the installation script again:
```bash
python tests/install_organization.py
```

Provide a different organization ID each time.

### Delete an Organization

**⚠️ WARNING: This deletes all data!**

1. Login to Firebase Console as yourself
2. Go to: **Realtime Database**
3. Navigate to: `organizations/{orgId}`
4. Click the **"X"** to delete
5. Confirm deletion

Or via script (TODO - can create if needed).

### Modify Organization Data

As super admin, you can directly edit in Firebase Console:
- Go to: **organizations/{orgId}/**
- Click any field to edit
- Changes save automatically

---

## Adding Packages to Existing Org

### Option 1: Via Firebase Console

1. Login to Firebase Console
2. Go to: **organizations/{orgId}/packages**
3. Click **"+"** to add new package
4. Add fields:
   ```
   name: "Package Name"
   description: "Description"
   minutes: 60
   prints: 10
   price: 50
   discountPercent: 0
   isActive: true
   createdAt: "2025-10-06T..."
   updatedAt: "2025-10-06T..."
   ```

### Option 2: Via Script (as org admin)

```bash
python tests/seed_packages.py
```

This script prompts for org admin login and adds packages.

---

## Troubleshooting

### Error: "Super admin authentication failed"

**Cause:** Wrong email/password or user doesn't exist

**Fix:**
1. Verify credentials are correct
2. Check user exists in Firebase Auth
3. Try resetting password in Console

### Error: "You are not the configured super admin"

**Cause:** Your UID doesn't match `config/superAdminUid`

**Fix:**
1. Check your UID in Firebase Auth
2. Update `config/superAdminUid` in Database
3. Make sure you're using the correct account

### Error: "Organization already exists"

**Cause:** Organization ID is already taken

**Fix:**
- Use a different organization ID
- Or delete the existing organization first

### Error: "Permission denied"

**Cause:** Security rules not deployed or super admin not configured

**Fix:**
1. Deploy rules: `firebase deploy --only database`
2. Verify `config/superAdminUid` is set in database
3. Check you're authenticated as super admin

---

## Best Practices

### Security

✅ **DO:**
- Use strong password for super admin account
- Keep super admin credentials secure
- Limit org admin privileges to trusted users
- Review organizations periodically
- Monitor Firebase Console for unusual activity

❌ **DON'T:**
- Share super admin credentials
- Use super admin account for daily operations
- Commit credentials to Git
- Give everyone admin access

### Organization Management

✅ **DO:**
- Use descriptive organization IDs (`tech-lab`, `school-main`)
- Document each organization's purpose
- Keep admin contact info updated
- Test new orgs before deploying to users

❌ **DON'T:**
- Use confusing org IDs (`org1`, `test`, `temp`)
- Create organizations without planning
- Forget to configure `.env` on client PCs

---

## Quick Reference

### Commands

```bash
# Deploy security rules
firebase deploy --only database

# Create new organization
python tests/install_organization.py

# Launch app (as user)
python src/main.py

# Add packages to existing org
python tests/seed_packages.py
```

### File Locations

```
SIONYX/
├── database.rules.json          ← Security rules
├── .env                          ← Firebase config (don't commit!)
├── tests/
│   └── install_organization.py  ← Org creation script
└── src/
    └── main.py                   ← Main app
```

### Important URLs

- Firebase Console: https://console.firebase.google.com
- Realtime Database: Console → Realtime Database
- Authentication: Console → Authentication → Users
- Rules: Console → Realtime Database → Rules

---

## Next Steps

After setup:

1. ✅ Create your super admin account
2. ✅ Deploy security rules
3. ✅ Test organization creation
4. ✅ Configure client PC with `.env`
5. ✅ Test login as org admin
6. ✅ Register test users
7. ✅ Test purchase flow

---

**Last Updated:** October 6, 2025  
**Status:** ✅ Ready to use  
**Support:** See `database.rules.json` for security rules


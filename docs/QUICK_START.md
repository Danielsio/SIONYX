# Quick Start - Simplified Security Model

## What I've Set Up

✅ **Simplified security rules** - Only YOU (super admin) can create/manage organizations  
✅ **Updated installation script** - Uses your super admin credentials to create orgs  
✅ **Removed complex settings** - Minimal org metadata (can add more later)  
✅ **Clean database structure** - Simple and easy to understand

---

## How It Works

### 1. You Are the Super Admin

```
YOU (Super Admin)
  ↓ creates organizations
ORGANIZATION ADMINS
  ↓ manage users/packages
REGULAR USERS
```

**Your powers:**
- Create/delete any organization
- Access all organization data
- Manage everything

---

## Getting Started (3 Steps)

### Step 1: Create Your Account (One Time)

1. Go to [Firebase Console](https://console.firebase.google.com) → Your Project
2. **Authentication → Users → Add user**
   - Email: `your-email@example.com`
   - Password: `[strong password]`
   - **Copy your User UID** (looks like: `abc123xyz456...`)

3. **Realtime Database → Add at root:**
   ```
   config/
     superAdminUid: "abc123xyz456..."  ← Your UID here
   ```

4. **Save your credentials securely!**

---

### Step 2: Deploy Security Rules

```bash
firebase deploy --only database
```

Verify in Console → Realtime Database → Rules

---

### Step 3: Create Organizations

```bash
python tests/install_organization.py
```

**Script will ask for:**
1. Your super admin email/password (authenticates you)
2. Organization ID (e.g., `tech-lab`)
3. Organization name (e.g., `Tech Lab`)
4. Admin user details (for that org)
5. Whether to create starter packages

**That's it!** Organization is ready to use.

---

## What Gets Created

```
Firebase Database
│
├── config/
│   └── superAdminUid: "your-uid"       ← YOU
│
└── organizations/
    └── tech-lab/                        ← Organization you created
        ├── metadata/
        │   ├── name: "Tech Lab"
        │   ├── createdAt: "..."
        │   └── status: "active"
        │
        ├── users/
        │   └── {adminUid}/              ← Org admin
        │       ├── firstName: "John"
        │       ├── isAdmin: true        ← Can manage this org
        │       └── ...
        │
        └── packages/                    ← Optional starter packages
            ├── {pkgId1}/
            ├── {pkgId2}/
            └── {pkgId3}/
```

---

## Security Rules Explained

### Super Admin (You)

```javascript
"organizations": {
  ".read": "root.child('config').child('superAdminUid').val() == auth.uid",
  ".write": "root.child('config').child('superAdminUid').val() == auth.uid"
}
```

✅ You can read/write **ALL** organizations  
✅ Used by installation script to create orgs  
✅ No one else can create organizations

### Organization Admins

```javascript
"packages": {
  "$packageId": {
    ".write": "...isAdmin.val() === true"
  }
}
```

✅ Can create/edit packages in their org  
✅ Can manage users in their org  
❌ Cannot create organizations  
❌ Cannot access other organizations

### Regular Users

```javascript
"users": {
  "$userId": {
    ".read": "auth.uid == $userId || ...",
    ".write": "auth.uid == $userId || ..."
  }
}
```

✅ Can read/write their own data  
✅ Can make purchases  
❌ Cannot access other users' data  
❌ Cannot make themselves admin

---

## Adding More Organizations

Just run the script again:

```bash
python tests/install_organization.py
```

Provide a different organization ID each time.

---

## Client Setup

On each organization's computers:

**Create `.env` file:**
```bash
# Must match the org you created!
ORG_ID=tech-lab

# Firebase config (same for all)
FIREBASE_API_KEY=...
FIREBASE_DATABASE_URL=...
FIREBASE_PROJECT_ID=...

# Payment gateway
NEDARIM_MOSAD_ID=...
NEDARIM_API_VALID=...
```

---

## What's Different from Complex Setup

### ❌ Removed
- Complex super admin system
- Multiple super admins
- Cloud Functions for org creation
- Per-org settings structure
- Complex permission checks

### ✅ Kept
- Single super admin (you)
- Organization admins (per org)
- Data isolation between orgs
- Payment integration
- User management

### 🎯 Result
- **Simpler** - Less moving parts
- **Faster** - Direct database writes
- **Flexible** - Easy to add features later
- **Secure** - Still protected

---

## Files Created/Updated

| File | Purpose |
|------|---------|
| `database.rules.json` | Simplified security rules |
| `tests/install_organization.py` | Uses your super admin credentials |
| `SETUP_GUIDE.md` | Detailed step-by-step guide |
| `QUICK_START.md` | This file - quick reference |

---

## Next Steps

1. ✅ Create your super admin account in Firebase
2. ✅ Deploy security rules
3. ✅ Run installation script to create first org
4. ✅ Test login as org admin
5. ✅ Configure client PCs with `.env`

---

## Need Help?

- **Detailed guide:** See `SETUP_GUIDE.md`
- **Security rules:** See `database.rules.json`
- **Installation script:** See `tests/install_organization.py`

---

**Status:** ✅ Ready to deploy  
**Complexity:** Simple (as requested)  
**Flexibility:** Can add more features later when needed


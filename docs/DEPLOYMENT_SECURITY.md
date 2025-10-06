# Security Deployment Guide

## Quick Start Checklist

Follow these steps to deploy the secure multi-tenant system:

---

## Step 1: Deploy Security Rules ⚠️ CRITICAL

```bash
# Deploy database security rules
firebase deploy --only database
```

**Verify deployment:**
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Navigate to: **Realtime Database → Rules**
3. Confirm rules are active
4. Check "Last deployed" timestamp

**Expected rules structure:**
```javascript
{
  "rules": {
    "organizations": { ... },
    "superAdmins": { ... }
  }
}
```

---

## Step 2: Deploy Cloud Functions

```bash
# Navigate to functions directory
cd functions

# Install dependencies (if not already)
npm install

# Deploy functions
firebase deploy --only functions
```

**Expected output:**
```
✔ functions[createOrganization]: Successful create operation.
✔ functions[makeSuperAdmin]: Successful create operation.
✔ functions[nedarimCallback]: Successful update operation.
```

**Verify deployment:**
1. Firebase Console → **Functions**
2. Confirm these functions exist:
   - `createOrganization`
   - `makeSuperAdmin`
   - `nedarimCallback`

---

## Step 3: Create First Super Admin 🔐

**⚠️ IMPORTANT:** This must be done manually via Firebase Console

### Option A: Using Firebase Console (Recommended)

1. **Create a user in Firebase Authentication:**
   - Firebase Console → **Authentication → Users**
   - Click "Add user"
   - Email: `your-email@example.com`
   - Password: `[Strong password - save securely!]`
   - Copy the **User UID** (e.g., `abc123xyz456`)

2. **Add to superAdmins in Database:**
   - Firebase Console → **Realtime Database**
   - Click the **"+"** at root level
   - Add:
     ```
     Name: superAdmins
     Value: [Leave empty, will add child next]
     ```
   - Click the **"+"** next to `superAdmins`
   - Add:
     ```
     Name: [Paste your User UID]
     Value: [Leave as object]
     ```
   - Click the **"+"** next to your UID
   - Add these fields:
     ```
     Name: addedBy        Value: "system"
     Name: email          Value: "your-email@example.com"
     Name: addedAt        Value: 1696588800000
     Name: note           Value: "Initial super admin"
     ```

3. **Test super admin access:**
   ```bash
   # Login with your super admin credentials
   # Try calling createOrganization function
   ```

### Option B: Using Firebase Admin SDK (Advanced)

```python
import firebase_admin
from firebase_admin import credentials, auth, db

# Initialize Firebase Admin SDK
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-project.firebaseio.com'
})

# Create super admin user
user = auth.create_user(
    email='superadmin@example.com',
    password='YourStrongPassword123!',
    display_name='Super Admin'
)

print(f"Created user: {user.uid}")

# Add to superAdmins in database
ref = db.reference('superAdmins')
ref.child(user.uid).set({
    'addedBy': 'system',
    'email': 'superadmin@example.com',
    'addedAt': db.ServerValue.TIMESTAMP,
    'note': 'Initial super admin via SDK'
})

print("Super admin created successfully!")
```

---

## Step 4: Test Security Rules

### Test 1: Verify Super Admin Can Create Org

```bash
python tests/create_organization_secure.py
```

**Expected behavior:**
- ✅ Authenticates as super admin
- ✅ Calls `createOrganization` successfully
- ✅ Creates org structure in database

### Test 2: Verify Regular User Cannot Create Org

```python
# Login as non-super-admin user
from firebase_admin import auth, db

# Try to create organization directly
ref = db.reference('organizations/testorg')
try:
    ref.set({'name': 'Test Org'})
    print("❌ FAIL: Should have been denied")
except Exception as e:
    print("✅ PASS: Permission denied as expected")
```

### Test 3: Verify Cross-Org Isolation

```python
# User in Org A tries to access Org B
ref_org_b = db.reference('organizations/orgB/users')
try:
    data = ref_org_b.get()
    print("❌ FAIL: Should not access other org")
except Exception as e:
    print("✅ PASS: Access denied as expected")
```

---

## Step 5: Create Your First Organization

```bash
python tests/create_organization_secure.py
```

**Interactive prompts:**
1. Super Admin Email: `[Your super admin email]`
2. Super Admin Password: `[Your super admin password]`
3. Organization ID: `myorg`
4. Organization Name: `My Organization`
5. Admin First Name: `John`
6. Admin Last Name: `Doe`
7. Admin Phone: `0501234567`
8. Admin Password: `secure123`

**Verify in Firebase Console:**
```
organizations/
  └── myorg/
      ├── metadata/
      │   ├── orgId: "myorg"
      │   ├── orgName: "My Organization"
      │   └── status: "active"
      ├── settings/
      │   └── orgName: "My Organization"
      └── users/
          └── {adminUid}/
              ├── firstName: "John"
              ├── isAdmin: true
              └── ...
```

---

## Step 6: Configure App for Organization

Create `.env` file on client PCs:

```bash
# Organization Configuration
ORG_ID=myorg

# Firebase Configuration
FIREBASE_API_KEY=AIza...
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_PROJECT_ID=your-project-id

# Payment Gateway
NEDARIM_MOSAD_ID=your_mosad_id
NEDARIM_API_VALID=your_api_valid
NEDARIM_CALLBACK_URL=https://your-function-url/nedarimCallback
```

---

## Step 7: Test End-to-End

### Login as Organization Admin

```bash
python src/main.py
```

1. Login with admin phone: `0501234567`
2. Login with admin password: `secure123`
3. ✅ Should login successfully
4. ✅ Should see main dashboard

### Register New User

1. Click "Register"
2. Fill in user details
3. ✅ User should be created in correct org
4. ✅ User should NOT be admin by default

### Test Org Admin Functions

1. Create packages (admin only)
2. View all users (admin only)
3. Verify regular users cannot access admin features

---

## Security Checklist

Before going live, verify:

- [ ] ✅ Security rules deployed
- [ ] ✅ Cloud Functions deployed and tested
- [ ] ✅ First super admin created securely
- [ ] ✅ Super admin credentials stored safely
- [ ] ✅ Test organization created successfully
- [ ] ✅ Regular users cannot create orgs
- [ ] ✅ Cross-org access blocked
- [ ] ✅ Package creation restricted to admins
- [ ] ✅ Firebase API key restrictions configured
- [ ] ✅ Monitoring enabled
- [ ] ✅ Backup strategy in place

---

## Common Issues & Solutions

### Issue: "Permission denied" when deploying rules

**Solution:**
```bash
# Ensure you're logged in to Firebase
firebase login

# Check current project
firebase use --add

# Select correct project
firebase use your-project-id

# Deploy again
firebase deploy --only database
```

### Issue: Cloud Function not found

**Solution:**
```bash
# Check function deployment status
firebase functions:list

# Redeploy specific function
firebase deploy --only functions:createOrganization

# Check logs
firebase functions:log
```

### Issue: Super admin cannot create org

**Solution:**
1. Verify super admin exists in database:
   - Firebase Console → Database → `superAdmins/`
2. Verify super admin is authenticated:
   - Check auth token includes correct UID
3. Check Cloud Function logs:
   - Firebase Console → Functions → Logs

### Issue: "CORS error" when calling Cloud Function

**Solution:**
Add to Cloud Function:
```javascript
res.set('Access-Control-Allow-Origin', '*');
res.set('Access-Control-Allow-Methods', 'GET, POST');
```

---

## Monitoring & Maintenance

### Daily

- Check Firebase Console for errors
- Review authentication logs
- Monitor unusual activity

### Weekly

- Review super admin list
- Check organization creation logs
- Verify security rules are active

### Monthly

- Audit all admin accounts
- Review package changes
- Test security rules with new scenarios
- Update dependencies

---

## Rollback Procedure

If you need to rollback security changes:

```bash
# Rollback database rules
firebase deploy --only database --force

# Rollback Cloud Functions
firebase deploy --only functions --force

# Or rollback to specific version
firebase functions:rollback createOrganization 1
```

**⚠️ WARNING:** Rolling back security rules may expose vulnerabilities!

---

## Support

### Documentation

- `SECURITY_SUMMARY.md` - Quick overview
- `SECURITY_GUIDE.md` - Detailed guide
- `database.rules.json` - Security rules
- `functions/index.js` - Cloud Functions

### Firebase Resources

- [Console](https://console.firebase.google.com)
- [Security Rules Docs](https://firebase.google.com/docs/database/security)
- [Cloud Functions Docs](https://firebase.google.com/docs/functions)

### Emergency

If security breach detected:
1. Disable affected accounts immediately
2. Deploy stricter security rules
3. Review logs for breach point
4. Notify affected users
5. Document incident

---

**Deployment Status:** 🔄 Ready to Deploy  
**Last Updated:** October 6, 2025  
**Critical:** ⚠️ Follow steps in order


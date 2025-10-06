# SIONYX Test & Installation Scripts

This directory contains test scripts and installation utilities for SIONYX.

## Installation Scripts

### `install_organization.py` - Organization Setup Script

**Purpose:** Set up a new organization in Firebase with all necessary data structures.

**What it does:**
- ✅ Creates an admin user for the organization
- ✅ Sets up organization settings
- ✅ Optionally creates starter packages
- ✅ Verifies the installation
- ✅ Provides detailed feedback at each step

**When to use:**
- First time setting up SIONYX for a new organization
- Migrating an organization to the multi-tenant structure
- Setting up a test/demo organization

**Requirements:**
- `.env` file configured with `ORG_ID` and Firebase credentials
- Internet connection
- Firebase project properly configured

**Usage:**

```bash
# Make sure you have the .env file set up
# ORG_ID=myorg
# FIREBASE_API_KEY=...
# etc.

python tests/install_organization.py
```

**Interactive prompts:**
1. Admin First Name
2. Admin Last Name  
3. Admin Phone Number (e.g., 0501234567)
4. Admin Password (min 6 characters)
5. Organization Display Name
6. Create starter packages? (y/n)

**Example session:**

```
============================================================
  🚀 SIONYX Organization Installation
============================================================

Organization ID: myorg
Database: https://myproject.firebaseio.com

Continue with installation for 'myorg'? (y/n): y
✅ Firebase client initialized

============================================================
  Create Admin User
============================================================

This admin will be able to manage packages and users.

Admin First Name: John
Admin Last Name: Doe
Admin Phone (e.g., 0501234567): 0501234567
Admin Password (min 6 chars): ******

ℹ️  Creating admin account...
✅ Admin account created (UID: abc123...)
✅ Admin user created: John Doe
ℹ️  Login with phone: 0501234567

============================================================
  Organization Settings
============================================================

Organization Display Name: My Computer Lab
✅ Organization settings created: My Computer Lab

============================================================
  Create Starter Packages
============================================================

Create starter packages? (y/n): y

ℹ️  Creating 3 starter packages...

  📦 Package 1/3: Quick Session
     Price: ₪25 | Time: 30min | Prints: 5
     ✅ Created with ID: -NxYzAbc123

  📦 Package 2/3: Standard Hour
     Price: ₪40 | Time: 60min | Prints: 10
     ✅ Created with ID: -NxYzAbc124

  📦 Package 3/3: Power User
     Price: ₪100 | Time: 180min | Prints: 30
     ✅ Created with ID: -NxYzAbc125

✅ Starter packages created

============================================================
  Verification
============================================================

✅ Organization structure
✅ Admin user (1 found)
✅ Organization settings
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
  Check: Realtime Database → organizations/myorg/

✅ Installation successful!
```

**What gets created in Firebase:**

```
organizations/
  └── myorg/
      ├── users/
      │   └── {adminUid}/
      │       ├── firstName: "John"
      │       ├── lastName: "Doe"
      │       ├── phoneNumber: "0501234567"
      │       ├── isAdmin: true
      │       ├── remainingTime: 0
      │       └── remainingPrints: 0
      │
      ├── settings/
      │   ├── orgName: "My Computer Lab"
      │   ├── createdAt: "2025-10-06T..."
      │   └── features/
      │       ├── enablePayments: true
      │       ├── enablePrinting: true
      │       └── enableHistory: true
      │
      └── packages/
          ├── {pkgId1}/
          │   ├── name: "Quick Session"
          │   ├── minutes: 30
          │   ├── prints: 5
          │   └── price: 25
          │
          ├── {pkgId2}/
          │   └── ...
          │
          └── {pkgId3}/
              └── ...
```

**Troubleshooting:**

| Error | Solution |
|-------|----------|
| `ORG_ID not found in environment!` | Create `.env` file with `ORG_ID=yourorg` |
| `Failed to initialize Firebase` | Check Firebase credentials in `.env` |
| `Failed to create admin` | Check internet connection and Firebase Auth is enabled |
| `EMAIL_EXISTS` | User already exists, try different phone number |
| `WEAK_PASSWORD` | Password must be at least 6 characters |

---

## Test Scripts

### `seed_packages.py` - Add Packages to Existing Organization

Creates sample packages in Firebase for an existing organization.

**Usage:**
```bash
python tests/seed_packages.py
```

**Requirements:**
- Existing admin user to authenticate
- Active organization

### `test_auth.py` - Test Authentication

Tests authentication functionality.

**Usage:**
```bash
python tests/test_auth.py
```

### `test_firebase.py` - Test Firebase Connection

Simple test to verify Firebase client can connect.

**Usage:**
```bash
python tests/test_firebase.py
```

---

## Best Practices

### Setting Up Multiple Organizations

For each organization:

1. **Create unique `.env` file:**
   ```bash
   ORG_ID=org1  # Different for each org!
   FIREBASE_API_KEY=...  # Same for all
   FIREBASE_DATABASE_URL=...  # Same for all
   ```

2. **Run installation script:**
   ```bash
   python tests/install_organization.py
   ```

3. **Verify in Firebase Console:**
   - Check `organizations/org1/` exists
   - Verify admin user created
   - Test login with admin credentials

### Security Notes

- ⚠️ **Never commit `.env` files** to version control
- ⚠️ **Keep admin credentials secure**
- ⚠️ **Use strong passwords** (8+ characters, mixed case, numbers)
- ⚠️ **Rotate admin passwords** periodically
- ⚠️ **Limit admin access** to trusted users only

### Migration Tips

If you have existing data at root level:

1. **Backup first:**
   ```bash
   # Firebase Console → Database → Export JSON
   ```

2. **Install new org structure:**
   ```bash
   python tests/install_organization.py
   ```

3. **Manually migrate data:**
   - Copy `/users/` to `/organizations/myorg/users/`
   - Copy `/packages/` to `/organizations/myorg/packages/`
   - Copy `/purchases/` to `/organizations/myorg/purchases/`

4. **Verify and test:**
   - Login as admin
   - Check all data is accessible
   - Test purchase flow

5. **Clean up old data:**
   - Delete root-level `/users/`, `/packages/`, etc.
   - Only after verifying everything works!

---

## Common Workflows

### Setup New Organization
```bash
# 1. Configure environment
echo "ORG_ID=neworg" > .env
# Add other Firebase credentials...

# 2. Run installation
python tests/install_organization.py

# 3. Test login
python src/main.py
```

### Add More Packages
```bash
# After organization is set up
python tests/seed_packages.py
# Or manually through admin interface (if implemented)
```

### Reset Organization (Development)
```bash
# ⚠️ WARNING: This deletes all data!
# Use Firebase Console to delete:
# organizations/{orgId}/
# Then run installation script again
python tests/install_organization.py
```

---

## Support

For issues or questions:
1. Check Firebase Console logs
2. Review `MULTI_TENANCY_GUIDE.md`
3. Verify `.env` configuration
4. Check Firebase Auth and Database are enabled in console

---

**Last Updated:** October 6, 2025


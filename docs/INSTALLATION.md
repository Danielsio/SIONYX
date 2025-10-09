# SIONYX Installation Guide

This guide will help you install and configure SIONYX for your organization.

## Architecture Overview

**SIONYX uses a multi-tenant architecture:**
- **ONE Firebase project** serves ALL organizations
- **Multiple organizations** coexist in the same database
- **Data isolation** is achieved through organization ID paths: `organizations/{org_id}/`
- Each installation only needs to set a unique `ORG_ID` in `.env`

This means you can:
- Run the same codebase for multiple organizations
- Share Firebase infrastructure costs
- Manage everything from a single Firebase project
- Keep complete data isolation between organizations

## Prerequisites

Before you begin, ensure you have:

- **Python 3.8+** installed
- **pip** package manager
- **Firebase account** with a project created (ONE project for all organizations)
- **Super Admin credentials** for your Firebase project
- **Nedarim Plus account** (optional, for payment processing)

## Installation Methods

### Method 1: Automated Installation (Recommended)

The automated installer will guide you through the entire setup process:

```bash
# Clone the repository
git clone https://github.com/your-repo/SIONYX.git
cd SIONYX

# Install Python dependencies
pip install -r requirements.txt

# Run the installer
python install.py
```

The installer will:
1. ✅ Collect your Firebase configuration
2. ✅ Configure payment gateway (optional)
3. ✅ Create your organization
4. ✅ Create an admin user
5. ✅ Seed starter packages
6. ✅ Generate `.env` configuration file

Follow the on-screen prompts and provide the requested information.

### Method 2: Manual Installation

If you prefer to set up manually:

#### Step 1: Create Configuration File

```bash
# Copy the example environment file
cp env.example .env
```

Edit `.env` and fill in your values:

```bash
# Organization
ORG_ID=your-org-id

# Firebase
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_PROJECT_ID=your-project-id

# Payment (optional)
NEDARIM_MOSAD_ID=your_mosad_id
NEDARIM_API_VALID=your_api_valid_key
NEDARIM_CALLBACK_URL=https://your-function-url/nedarimCallback
```

#### Step 2: Run Organization Setup

```bash
python tests/install_organization.py
```

This will:
- Create your organization in Firebase
- Create an admin user
- Seed starter packages

## Configuration Details

### Firebase Configuration

**Important**: These are the credentials for your ROOT Firebase project that serves all organizations.

Get these values from [Firebase Console](https://console.firebase.google.com/):

1. Go to **Project Settings** → **General**
2. Scroll to "Your apps" section
3. Copy the configuration values

**Note**: You'll use the SAME Firebase credentials for all organizations. Only the `ORG_ID` will differ.

### Organization ID

The Organization ID is a unique identifier for your organization:

- **Format**: Lowercase letters, numbers, and hyphens only
- **Examples**: `tech-lab`, `school123`, `mycompany`
- **Important**: Cannot be changed after creation!

### Payment Gateway (Nedarim Plus)

If you want to enable online payments:

1. Sign up for a [Nedarim Plus](https://www.nedarimplus.com/) account
2. Get your **Mosad ID** and **API Valid Key**
3. Deploy the Firebase Cloud Function (see below)
4. Set the **Callback URL** to your function URL

If you don't have Nedarim credentials yet:
- Leave the payment fields empty in `.env`
- Payment features will be disabled
- You can add them later

## Post-Installation Setup

### 1. Launch Desktop Application

```bash
python src/main.py
```

Login with the admin phone number you created during installation.

### 2. Set Up Admin Dashboard

The admin dashboard is a web application for managing packages and viewing users.

```bash
cd admin-dashboard
npm install
```

Edit `src/config/firebase.js` with your Firebase configuration:

```javascript
export const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  databaseURL: "https://your-project.firebaseio.com",
  projectId: "your-project-id"
};
```

Run the dashboard:

```bash
npm run dev
```

Access at `http://localhost:5173`

### 3. Deploy Firebase Cloud Function (for payments)

If you're using Nedarim Plus payments:

```bash
cd functions
npm install

# Deploy the payment callback function
firebase deploy --only functions:nedarimCallback
```

Copy the deployed function URL and add it to your `.env`:

```bash
NEDARIM_CALLBACK_URL=https://your-region-your-project.cloudfunctions.net/nedarimCallback
```

## Security Checklist

After installation, verify these security measures:

- [ ] `.env` file is in `.gitignore`
- [ ] Never committed `.env` to version control
- [ ] Super admin credentials are secure
- [ ] Firebase security rules are properly configured
- [ ] Payment credentials (if used) are kept secret

## Troubleshooting

### "ORG_ID missing in .env"

Make sure your `.env` file:
1. Exists in the project root
2. Contains `ORG_ID=your-org-id`
3. Has no extra spaces around the `=` sign

### "Organization already exists"

The organization ID is already in use. You must:
1. Choose a different organization ID, or
2. Use the existing organization

### "Super admin authentication failed"

Verify that:
1. You're using the correct super admin email/password
2. The super admin UID is configured in Firebase
3. Firebase security rules allow super admin access

### "Payment features not working"

Check that:
1. Nedarim credentials are in `.env`
2. Callback URL is correct
3. Firebase Cloud Function is deployed
4. Function has proper permissions

### Firebase connection issues

Verify:
1. All Firebase credentials in `.env` are correct
2. Firebase project is active
3. Internet connection is working
4. Firebase Realtime Database is enabled

## Multi-Organization Setup

SIONYX supports multiple organizations in the **same Firebase project**. Here's how to set up additional organizations:

### Architecture

```
Firebase Project (ONE)
├── organizations/
│   ├── tech-lab/          ← Organization 1
│   │   ├── users/
│   │   ├── packages/
│   │   └── sessions/
│   ├── school123/         ← Organization 2
│   │   ├── users/
│   │   ├── packages/
│   │   └── sessions/
│   └── mycompany/         ← Organization 3
│       ├── users/
│       ├── packages/
│       └── sessions/
```

### Adding a New Organization

1. **Run the installer again**:
   ```bash
   python install.py
   ```

2. **Reuse Firebase credentials**:
   - When prompted, select "Yes" to use existing Firebase configuration
   - The installer will detect your existing `.env` and offer to reuse it

3. **Choose a different Organization ID**:
   - Enter a new, unique organization ID (e.g., `school123`)
   - This ID must be different from existing organizations

4. **Save configuration separately**:
   ```bash
   # After installation completes, save the .env for this org
   cp .env .env.school123
   
   # To switch between organizations:
   cp .env.tech-lab .env      # Use tech-lab
   # or
   cp .env.school123 .env     # Use school123
   ```

### Managing Multiple Organizations

**Option 1: Separate Machines**
- Install on different computers
- Each has its own `.env` with unique `ORG_ID`
- All connect to the same Firebase project

**Option 2: Single Machine (Development)**
- Keep multiple `.env` files: `.env.org1`, `.env.org2`, etc.
- Copy the appropriate one to `.env` before running:
  ```bash
  cp .env.tech-lab .env
  python src/main.py
  ```

**Option 3: Script Switching**
Create a simple launcher script:
```bash
#!/bin/bash
# launch_org.sh
ORG_NAME=$1
cp .env.$ORG_NAME .env
python src/main.py
```

Usage:
```bash
./launch_org.sh tech-lab
./launch_org.sh school123
```

### Important Notes

- ✅ **Same Firebase credentials** for all organizations
- ✅ **Different ORG_ID** for each organization  
- ✅ **Complete data isolation** via database paths
- ✅ **Shared infrastructure** (lower costs)
- ⚠️ **One admin dashboard** per Firebase project (can manage all orgs)
- ⚠️ **Super admin** has access to all organizations

## Upgrading

To upgrade SIONYX:

```bash
# Backup your .env file
cp .env .env.backup

# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Restore .env
cp .env.backup .env

# Run the application
python src/main.py
```

## Getting Help

If you encounter issues:

1. Check this guide and troubleshooting section
2. Review the [Setup Guide](SETUP_GUIDE.md)
3. Check Firebase Console for error messages
4. Review application logs in `logs/` directory

## Next Steps

After successful installation:

1. **Test the desktop app**: Login and verify functionality
2. **Access admin dashboard**: Manage packages and view users
3. **Configure packages**: Customize pricing and offerings
4. **Set up payment**: If not done already
5. **Create regular users**: Test the full user flow

Congratulations! Your SIONYX installation is complete. 🎉


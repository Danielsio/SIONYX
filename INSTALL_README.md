# Quick Installation Guide

## 🏗️ Architecture

**SIONYX uses a multi-tenant architecture:**
- ONE Firebase project serves ALL organizations
- Each organization has a unique ID (e.g., `tech-lab`, `school123`)
- Data is isolated in the database: `organizations/{org_id}/`
- You can run the installer multiple times for different organizations

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.8+ installed
- Firebase project created
- Super admin credentials

### Installation Steps

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the installer**
   ```bash
   python install.py
   ```

3. **Follow the wizard**
   - Enter Firebase configuration
   - Configure payment gateway (optional)
   - Create organization
   - Create admin user
   - Done! 🎉

4. **Launch the app**
   ```bash
   python src/main.py
   ```

### What You'll Need

#### Firebase Configuration (Same for ALL organizations)
Get from [Firebase Console](https://console.firebase.google.com/) → Project Settings:
- API Key
- Auth Domain  
- Database URL
- Project ID

**Note**: If you're setting up a second organization, you can reuse existing Firebase credentials!

#### Super Admin Credentials
- Email and password of your Firebase super admin account

#### Payment Gateway (Optional)
- Nedarim Mosad ID
- Nedarim API Valid Key
- Callback URL (after deploying Firebase Functions)

### Configuration Files

After installation, you'll have:

- **`.env`** - Your configuration file (DO NOT COMMIT!)
- **`env.example`** - Template for reference

### Multiple Organizations

To add another organization to the same Firebase project:

```bash
# Run installer again
python install.py

# When prompted, reuse existing Firebase configuration
# Choose a different organization ID
# Save the new .env separately
cp .env .env.my-second-org
```

### Need More Help?

See the full [Installation Guide](docs/INSTALLATION.md) for detailed instructions, troubleshooting, and multi-organization setup.

---

**Note**: The `.env` file contains sensitive credentials. Never commit it to version control!


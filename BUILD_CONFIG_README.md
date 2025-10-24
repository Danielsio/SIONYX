# SIONYX Build Configuration

## 🔧 **Configuration System**

The build system now uses a configuration file to keep sensitive data secure and make the build process more flexible.

## 📁 **Files**

- `build-config.json` - **Your actual configuration** (DO NOT COMMIT)
- `build-config.example.json` - **Template file** (safe to commit)
- `.gitignore` - **Excludes build-config.json** from version control

## 🚀 **Setup**

### **1. Copy the Template**
```bash
cp build-config.example.json build-config.json
```

### **2. Update Your Configuration**
Edit `build-config.json` with your actual values:

```json
{
  "firebase": {
    "project_id": "your-actual-project-id",
    "storage_bucket": "your-actual-bucket.firebasestorage.app",
    "service_account_key": "serviceAccountKey.json"
  },
  "build": {
    "app_name": "SIONYX",
    "version_file": "version.json",
    "upload_filename": "sionyx-installer.exe"
  },
  "paths": {
    "web_app": "sionyx-web",
    "src": "src",
    "dist": "distribution"
  }
}
```

## 🔒 **Security Benefits**

### **Before (Hard-coded)**
```python
# ❌ Hard-coded in build.py
bucket_name = "sionyx-19636.firebasestorage.app"
upload_filename = "sionyx-installer.exe"
```

### **After (Configuration)**
```python
# ✅ Loaded from config
config = load_config()
bucket_name = config['firebase']['storage_bucket']
upload_filename = config['build']['upload_filename']
```

## 🎯 **Configuration Options**

### **Firebase Settings**
- `project_id` - Your Firebase project ID
- `storage_bucket` - Your Firebase Storage bucket name
- `service_account_key` - Path to your service account JSON file

### **Build Settings**
- `app_name` - Name of your application
- `version_file` - Path to version tracking file
- `upload_filename` - Name of the uploaded file

### **Path Settings**
- `web_app` - Path to web application directory
- `src` - Path to source code directory
- `dist` - Path to distribution directory

## 🚀 **Usage**

The build script automatically loads the configuration:

```bash
# Build and upload (uses config automatically)
python build.py --upload --skip-installer
```

## 🔄 **Environment Variables (Alternative)**

You can also override configuration with environment variables:

```bash
# Override bucket name
export FIREBASE_STORAGE_BUCKET="my-custom-bucket.firebasestorage.app"
python build.py --upload --skip-installer
```

## 📋 **Best Practices**

### **1. Never Commit Sensitive Data**
- ✅ `build-config.example.json` - Safe to commit
- ❌ `build-config.json` - Contains real credentials
- ❌ `serviceAccountKey.json` - Contains Firebase credentials

### **2. Use Different Configs for Different Environments**
```bash
# Development
cp build-config.example.json build-config.dev.json
# Update with dev settings
python build.py --config build-config.dev.json --upload

# Production
cp build-config.example.json build-config.prod.json
# Update with prod settings
python build.py --config build-config.prod.json --upload
```

### **3. Team Setup**
1. **New team member**: Copy `build-config.example.json` to `build-config.json`
2. **Update with their credentials**: Edit `build-config.json`
3. **Never commit**: `build-config.json` is in `.gitignore`

## 🛠️ **Troubleshooting**

### **"Configuration file not found"**
```bash
cp build-config.example.json build-config.json
# Edit build-config.json with your settings
```

### **"Invalid JSON in configuration file"**
- Check JSON syntax in `build-config.json`
- Use a JSON validator online

### **"Firebase service account key not found"**
- Make sure `serviceAccountKey.json` exists
- Check the path in `build-config.json`

## 🎉 **Benefits**

- ✅ **Security**: No hard-coded credentials
- ✅ **Flexibility**: Easy to change settings
- ✅ **Team-friendly**: Each developer has their own config
- ✅ **Environment-specific**: Different configs for dev/prod
- ✅ **Version control safe**: Sensitive data not committed

## 📝 **Example Workflow**

```bash
# 1. Setup (first time)
cp build-config.example.json build-config.json
# Edit build-config.json with your settings

# 2. Build and upload
python build.py --upload --skip-installer

# 3. Check what was uploaded
# File: https://storage.googleapis.com/YOUR_BUCKET/sionyx-installer.exe
```

Your build system is now secure and flexible! 🚀

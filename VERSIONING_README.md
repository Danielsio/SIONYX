# SIONYX Versioning & Firebase Storage

This document explains the automatic versioning and Firebase Storage integration features.

## 🚀 **Quick Start**

### **1. Setup Firebase Storage**
```bash
# Interactive setup (recommended)
python setup_firebase.py

# Or manually:
# 1. Get service account key from Firebase Console
# 2. Save as 'serviceAccountKey.json' in project root
# 3. Set Storage rules for public read access
```

### **2. Build and Upload**
```bash
# Build, upload to Firebase, clean local files
build.bat --upload

# Build, upload both executable and installer
build.bat --upload --upload-installer
```

## 📋 **Features**

### **Automatic Versioning**
- ✅ **Auto-increment** version numbers (1.0.0 → 1.0.1 → 1.0.2...)
- ✅ **Version tracking** in `version.json`
- ✅ **Build metadata** (date, build number, etc.)
- ✅ **Versioned filenames** (`SIONYX_v1.0.1.exe`)

### **Firebase Storage Integration**
- ✅ **Automatic upload** to Firebase Storage
- ✅ **Public download URLs** for web app
- ✅ **Version metadata** stored in Firebase
- ✅ **Latest release info** (`releases/latest.json`)

### **Local Cleanup**
- ✅ **Auto-cleanup** after successful upload
- ✅ **No local artifacts** left behind
- ✅ **Clean workspace** for next build

## 📁 **File Organization**

### **Local Files (Temporary)**
```
SIONYX/
├── version.json              # Version tracking
├── upload_info.json          # Upload metadata
├── serviceAccountKey.json    # Firebase credentials
└── (build artifacts cleaned up after upload)
```

### **Firebase Storage**
```
releases/
├── SIONYX_v1.0.1.exe         # Versioned executable
├── SIONYX-Setup_v1.0.1.exe   # Versioned installer
├── latest.json               # Latest release info
└── versions/
    ├── v1.0.1.json           # Version 1.0.1 metadata
    ├── v1.0.2.json           # Version 1.0.2 metadata
    └── ...
```

## 🔧 **Version Management**

### **Version Format**
- **Format**: `major.minor.patch` (e.g., `1.0.1`)
- **Auto-increment**: Patch version increments on each build
- **Manual override**: Edit `version.json` to set specific version

### **Version File Structure**
```json
{
  "version": "1.0.1",
  "build_date": "2024-12-01T14:30:22.123456",
  "build_number": 1701432622
}
```

### **Version History**
- Each build creates a new version
- Previous versions remain in Firebase Storage
- `latest.json` always points to the newest version
- Version-specific metadata in `releases/versions/`

## 🌐 **Web App Integration**

### **Download Service**
The web app automatically fetches the latest version:

```javascript
// Get latest release info
const releaseInfo = await getLatestRelease();
// Returns: { version, downloadUrl, fileSize, etc. }
```

### **Version Display**
- Shows current version in download UI
- Displays file size and release date
- Handles download progress and errors

## 🛠️ **Build Commands**

### **Basic Commands**
```bash
# Regular build (local files kept)
build.bat

# Build and upload (local files cleaned)
build.bat --upload

# Build executable only and upload
build.bat --executable-only --upload
```

### **Advanced Commands**
```bash
# Upload both executable and installer
build.bat --upload --upload-installer

# Use custom Firebase bucket
build.bat --upload --bucket my-custom-bucket

# Skip web build, upload executable
build.bat --skip-web --upload
```

## 📊 **Build Process Flow**

### **With Upload (`--upload`)**
1. **Get version** from `version.json` (increment if needed)
2. **Build web app** (if not skipped)
3. **Create executable** with PyInstaller
4. **Create installer** (if not skipped)
5. **Upload to Firebase** with versioned filenames
6. **Upload version metadata** to Firebase
7. **Clean up local files** (build/, dist/, etc.)
8. **Save upload info** to `upload_info.json`

### **Without Upload**
1. **Get version** from `version.json`
2. **Build web app** (if not skipped)
3. **Create executable** with PyInstaller
4. **Create installer** (if not skipped)
5. **Create distribution package**
6. **Clean up temporary files** only

## 🔒 **Security**

### **Firebase Storage Rules**
```javascript
rules_version = '2';

// Craft rules based on data in your Firestore database
// allow write: if firestore.get(
//    /databases/(default)/documents/users/$(request.auth.uid)).data.isAdmin;
service firebase.storage {
  match /b/{bucket}/o {
    // Public read access for releases (for SIONYX downloads)
    match /releases/{allPaths=**} {
      allow read: if true;
      allow write: if false; // Only admin can write via service account
    }
    
    // Keep existing rules for other paths
    match /{allPaths=**} {
      allow read, write: if false;
    }
  }
}
```

### **Service Account**
- Keep `serviceAccountKey.json` secure
- Never commit to version control
- Rotate keys periodically

## 🚨 **Troubleshooting**

### **Common Issues**

**"Service account key not found"**
```bash
# Run setup script
python setup_firebase.py
```

**"Upload failed"**
- Check internet connection
- Verify Firebase Storage rules
- Check service account permissions

**"Version not incrementing"**
- Check `version.json` exists and is valid
- Ensure write permissions in project directory

**"Local files not cleaned"**
- Upload must be successful for cleanup
- Check Firebase connection
- Verify upload permissions

### **Debug Mode**
```bash
# Enable debug logging
set PYTHONPATH=%PYTHONPATH%;.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
build.bat --upload
```

## 📈 **Benefits**

### **For Developers**
- ✅ **No manual versioning** - automatic increment
- ✅ **No local clutter** - files cleaned after upload
- ✅ **Easy distribution** - upload once, available everywhere
- ✅ **Version history** - track all releases

### **For Users**
- ✅ **Always latest version** - web app shows current version
- ✅ **Fast downloads** - Firebase CDN
- ✅ **Reliable delivery** - no broken links
- ✅ **Version info** - know what you're downloading

## 🎯 **Best Practices**

### **Development Workflow**
1. **Make changes** to your code
2. **Test locally** with `build.bat --executable-only`
3. **Upload to Firebase** with `build.bat --upload`
4. **Test download** from web app
5. **Deploy** when satisfied

### **Version Management**
- **Major version** (1.0.0 → 2.0.0): Breaking changes
- **Minor version** (1.0.0 → 1.1.0): New features
- **Patch version** (1.0.0 → 1.0.1): Bug fixes (auto-increment)

### **Firebase Storage**
- **Regular cleanup** of old versions (optional)
- **Monitor storage usage** in Firebase Console
- **Set up alerts** for storage limits

## 🔄 **Migration from Manual Builds**

If you're currently using manual builds:

1. **Run setup**: `python setup_firebase.py`
2. **Test upload**: `build.bat --upload`
3. **Update web app** to use new download service
4. **Remove old build artifacts** from version control
5. **Enjoy automated builds!** 🎉

---

**Need help?** Check the main `PACKAGING_README.md` or run `build.bat --help`

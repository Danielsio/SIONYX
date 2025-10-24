# 🖥️ SIONYX DESKTOP APPLICATION  
*(Python 3.10+)*

A modern kiosk management system with time-tracking, package purchases, and multi-tenant support.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the installer (creates organization, admin user, and .env)
python install.py

# 3. Launch the application
python src/main.py

# OR use the launcher (for multiple organizations)
python launch_org.py
```

For detailed installation instructions, see **[INSTALL_README.md](INSTALL_README.md)** or the full **[Installation Guide](docs/INSTALLATION.md)**.

### Multi-Organization Setup

SIONYX supports multiple organizations in a single Firebase project:
- **ONE Firebase project** serves all organizations
- **Complete data isolation** via organization IDs
- **Easy switching** between organizations

See **[Multi-Organization Guide](docs/MULTI_ORGANIZATION_SUMMARY.md)** for details.

---

## 🔧 System Architecture

### 🪟 Main Application Window (PyQt6 QMainWindow)
- Login / Registration UI  
- Dashboard (Quota Display)  
- Package Purchase Screen  
- Settings  
- System Tray Integration  

---

### ⏱️ Always-On-Top Timer Overlay Window (PyQt6 QWidget - Frameless)
- Semi-transparent background  
- Draggable  
- Shows **Remaining Time & Prints**  
- Click-through option  

---

### ⚙️ Business Logic Layer
- **SessionManager** → time tracking  
- **AuthService** → login / registration  
- **SyncManager** → 10-second heartbeat  
- **PackageService** → purchases  
- **LocalCache** → SQLite operations  

---

### 🌐 Firebase Client Layer (HTTP/REST)
- Uses `requests` library for API calls  
- JWT token management  
- Retry logic & offline queue  

---

### 🗄️ Local SQLite Database
- Encrypted credentials  
- Session cache  
- Offline sync queue  

---

➡️ **Communication via HTTPS REST API**  

---

## 🔥 Firebase Backend

### 🔑 Firebase Authentication
- Phone Number Verification (SMS OTP)  
- Password Authentication  
- JWT Token Management (auto refresh)  

---

### 📂 Cloud Firestore Database
**Collections:**  
- `users/`  
- `sessions/`  
- `packages/`  
- `transactions/`  

---

### ⚡ Firebase Cloud Functions
- **onUserCreate** → initialize user quotas  
- **registerUser** → handle phone verification  
- **startSession** → initialize tracking  
- **syncSessionTime** → validate & update  
- **purchasePackage** → transaction handling  
- **decrementPrintQuota**  
- **validateSession** → anti-fraud checks  

---

## 🏗️ Build & Distribution System

### **Simple Build Process**
```bash
# Build and upload to Firebase Storage
python build.py --upload --skip-installer --skip-web

# Build everything (web + executable + installer)
python build.py

# Build only executable
python build.py --executable-only
```

### **Configuration System**
The build system uses a secure configuration file:

1. **Copy template**: `cp build-config.example.json build-config.json`
2. **Edit configuration**: Update `build-config.json` with your settings
3. **Build**: `python build.py --upload --skip-installer --skip-web`

### **Build Options**
- `--upload` - Upload to Firebase Storage
- `--skip-web` - Skip web application build
- `--skip-installer` - Skip NSIS installer creation
- `--executable-only` - Create only the executable
- `--force-web` - Force rebuild web application

### **Firebase Storage Integration**
- **Automatic upload** to configured bucket
- **Version management** with auto-increment
- **Local cleanup** after successful upload
- **Constant filename** for reliable downloads

### **Security Features**
- **No hard-coded credentials** - All sensitive data in config
- **Git ignored** - `build-config.json` not committed
- **Team-friendly** - Each developer has their own config

---

## 📂 Project Structure

```bash
sionyx-desktop/
├── src/                                # Main application source
│   ├── main.py                         # Application entry point
│   ├── ui/                             # User Interface Components
│   │   ├── main_window.py              # Main application window
│   │   ├── auth_window.py              # Login/registration
│   │   ├── installer_wizard.py         # First-time setup wizard
│   │   └── components/                 # UI components
│   ├── services/                       # Business Logic Services
│   │   ├── auth_service.py             # Authentication logic
│   │   ├── session_manager.py          # Session tracking
│   │   ├── firebase_client.py          # Firebase REST API client
│   │   └── package_service.py          # Package operations
│   ├── database/                       # Local Database Layer
│   │   └── local_db.py                 # SQLite operations
│   └── utils/                          # Utility Functions
│       ├── device_info.py              # Hardware ID generation
│       └── firebase_config.py          # Configuration management
│
├── sionyx-web/                         # React web application
│   ├── src/
│   │   ├── pages/                      # React pages
│   │   ├── components/                 # React components
│   │   ├── services/                   # API services
│   │   └── config/                     # Firebase config
│   └── dist/                           # Built web assets
│
├── functions/                          # Firebase Cloud Functions
│   ├── index.js                        # Main functions entry
│   └── package.json                    # Node.js dependencies
│
├── build.py                            # Main build script
├── build-config.json                   # Build configuration (secure)
├── build-config.example.json           # Configuration template
├── sionyx.spec                         # PyInstaller specification
├── installer.nsi                       # NSIS installer script
├── version.json                        # Version tracking
├── requirements.txt                    # Python dependencies
├── build-requirements.txt              # Build dependencies
├── firebase.json                       # Firebase configuration
├── database.rules.json                 # Firestore security rules
├── serviceAccountKey.json              # Firebase credentials (secure)
├── env.example                         # Environment variables template
└── README.md                           # This file
```

---

## 🔒 Security & Configuration

### **Environment Variables**
Create `.env` file from `env.example`:
```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_STORAGE_BUCKET=your-project.appspot.com

# Organization
ORG_ID=your-organization-id

# Nedarim Payment Gateway
NEDARIM_CALLBACK_URL=https://us-central1-your-project.cloudfunctions.net/nedarimCallback
```

### **Firebase Storage Rules**
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Public read access for installer
    match /sionyx-installer.exe {
      allow read: if true;
      allow write: if false;
    }
    
    // Keep existing rules for other paths
    match /{allPaths=**} {
      allow read, write: if false;
    }
  }
}
```

### **Build Configuration**
The build system uses `build-config.json` for secure configuration:

```json
{
  "firebase": {
    "project_id": "your-project-id",
    "storage_bucket": "your-project.firebasestorage.app",
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

---

## 🚀 Deployment

### **1. Development Setup**
```bash
# Clone repository
git clone <repository-url>
cd sionyx

# Install dependencies
pip install -r requirements.txt
pip install -r build-requirements.txt

# Setup configuration
cp build-config.example.json build-config.json
# Edit build-config.json with your settings

# Setup Firebase
cp env.example .env
# Edit .env with your Firebase settings
```

### **2. Build & Deploy**
```bash
# Build and upload
python build.py --upload --skip-installer --skip-web

# Check upload
# File available at: https://storage.googleapis.com/YOUR_BUCKET/sionyx-installer.exe
```

### **3. Web Application**
```bash
# Build web app
cd sionyx-web
npm install
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting
```

---

## 📋 Dependencies

### **Python Dependencies**
- `PyQt6` - GUI framework
- `requests` - HTTP client
- `cryptography` - Encryption
- `psutil` - System monitoring
- `pyinstaller` - Executable creation
- `firebase-admin` - Firebase integration

### **Build Dependencies**
- `Node.js 16+` - Web application build
- `NSIS` - Windows installer creation
- `PyInstaller` - Python executable creation

### **Firebase Dependencies**
- `firebase-admin` - Server-side Firebase SDK
- `firebase` - Client-side Firebase SDK

---

## 🛠️ Troubleshooting

### **Build Issues**
- **"Configuration file not found"**: Copy `build-config.example.json` to `build-config.json`
- **"NSIS not found"**: Install NSIS and add to PATH
- **"Firebase upload failed"**: Check `serviceAccountKey.json` and bucket permissions

### **Runtime Issues**
- **"Firebase connection failed"**: Check `.env` file and network connectivity
- **"Database error"**: Check Firebase project configuration
- **"Authentication failed"**: Verify Firebase Auth settings

### **Web App Issues**
- **"Build failed"**: Check Node.js version and dependencies
- **"Download not working"**: Verify Firebase Storage rules and file existence

---

## 📚 Documentation

- **[Installation Guide](INSTALL_README.md)** - Detailed setup instructions
- **[Multi-Organization Guide](docs/MULTI_ORGANIZATION_SUMMARY.md)** - Multi-tenant setup
- **[API Documentation](docs/API.md)** - API reference
- **[Security Guide](docs/SECURITY.md)** - Security considerations

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

For support and questions:
- Check the documentation
- Review the troubleshooting section
- Open an issue on GitHub

---

**SIONYX** - Modern kiosk management made simple! 🚀
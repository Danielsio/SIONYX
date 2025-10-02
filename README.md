# 🖥️ SIONYX DESKTOP APPLICATION  
*(Python 3.10+)*

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

## 📂 Project Structure

```bash
sionyx-desktop/
├── src/
│   ├── main.py                      # Application entry point
│   │
│   ├── ui/                          # User Interface Components
│   │   ├── __init__.py
│   │   ├── main_window.py           # Main application window
│   │   ├── login_window.py          # Login/registration
│   │   ├── dashboard.py             # User dashboard
│   │   ├── timer_overlay.py         # Always-on-top timer
│   │   ├── package_selection.py     # Package purchase UI
│   │   └── settings_dialog.py       # Settings
│   │
│   ├── services/                    # Business Logic Services
│   │   ├── __init__.py
│   │   ├── auth_service.py          # Authentication logic
│   │   ├── session_manager.py       # Session tracking
│   │   ├── sync_manager.py          # 10-second sync
│   │   ├── package_service.py       # Package operations
│   │   └── firebase_client.py       # Firebase REST API client
│   │
│   ├── models/                      # Data Models
│   │   ├── __init__.py
│   │   ├── user.py                  # User data model
│   │   ├── session.py               # Session data model
│   │   ├── package.py               # Package data model
│   │   └── transaction.py           # Transaction data model
│   │
│   ├── database/                    # Local Database Layer
│   │   ├── __init__.py
│   │   ├── local_db.py              # SQLite operations
│   │   └── schema.sql               # Database schema
│   │
│   ├── utils/                       # Utility Functions
│   │   ├── __init__.py
│   │   ├── crypto.py                # Encryption utilities
│   │   ├── device_info.py           # Hardware ID generation
│   │   ├── config.py                # Configuration management
│   │   └── validators.py            # Input validation
│   │
│   └── resources/                   # Application Resources
│       ├── styles/
│       │   ├── main.qss             # PyQt6 stylesheets
│       │   └── overlay.qss          # Overlay styles
│       ├── icons/
│       │   ├── app_icon.ico         # Application icon
│       │   ├── tray_icon.png        # System tray icon
│       │   └── logo.png             # App logo
│       ├── config.ini               # Default configuration
│       └── fonts/                   # Custom fonts (optional)
│
├── firebase/                        # Firebase Backend
│   ├── functions/                   # Cloud Functions
│   │   ├── src/
│   │   │   ├── index.ts             # Main functions entry
│   │   │   ├── auth.ts              # Auth-related functions
│   │   │   ├── session.ts           # Session management
│   │   │   ├── package.ts           # Package operations
│   │   │   └── utils.ts             # Helper functions
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── firestore.rules              # Firestore security rules
│   ├── firestore.indexes.json       # Firestore indexes
│   └── firebase.json                # Firebase config
│
├── tests/                           # Unit & Integration Tests
│   ├── unit/
│   │   ├── test_auth.py
│   │   ├── test_session.py
│   │   ├── test_sync.py
│   │   └── test_crypto.py
│   ├── integration/
│   │   ├── test_firebase_client.py
│   │   └── test_session_flow.py
│   └── conftest.py                  # Pytest configuration
│
├── docs/                            # Documentation
│   ├── API.md                       # API documentation
│   ├── DEPLOYMENT.md                # Deployment guide
│   ├── SECURITY.md                  # Security considerations
│   └── USER_GUIDE.md                # End-user guide
│
├── scripts/                         # Build & Deployment Scripts
│   ├── build_windows.bat            # Windows build script
│   ├── build_mac.sh                 # macOS build script
│   ├── deploy_firebase.sh           # Firebase deployment
│   └── setup_dev.py                 # Development setup
│
├── requirements.txt                 # Python dependencies
├── requirements-dev.txt             # Development dependencies
├── setup.py                         # Package setup
├── build.spec                       # PyInstaller spec file
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── LICENSE                          # Software license
└── README.md                        # Project documentation

# WIP: Migrate from .env to Windows Registry

## Overview

Replace `.env` file-based configuration with Windows Registry for production builds.
This improves reliability (files can be deleted) and follows Windows best practices.

## Current State

### Files using .env:
| File | Usage |
|------|-------|
| `src/utils/firebase_config.py` | Loads all Firebase config + ORG_ID via `load_dotenv` |
| `src/main.py` | Checks if `.env` exists before starting |
| `src/ui/payment_dialog.py` | Reads `NEDARIM_CALLBACK_URL` (optional) |
| `src/utils/firebase_config_test.py` | Mocks `load_dotenv` |
| `src/main_test.py` | Mocks `Path.exists` for .env check |

### Current installer registry usage:
```nsis
WriteRegStr HKLM "Software\SIONYX" "Install_Dir" "$INSTDIR"
WriteRegStr HKLM "SOFTWARE\SIONYX" "KioskUsername" "KioskUser"
```

---

## New Architecture

### Development Mode (Script)
- Continue using `.env` file for fast iteration
- No registry dependency on dev machines
- Detected via: `getattr(sys, "frozen", False) == False`

### Production Mode (Frozen/PyInstaller)
- Read ALL config from Windows Registry
- No `.env` file needed
- Detected via: `getattr(sys, "frozen", False) == True`

### Registry Structure
```
HKEY_LOCAL_MACHINE\SOFTWARE\SIONYX\
├── Install_Dir        = "C:\Program Files\SIONYX"      (existing)
├── KioskUsername      = "KioskUser"                    (existing)
├── OrgId              = "sionov"                       (NEW)
├── FirebaseApiKey     = "AIzaSyDS5h..."                (NEW)
├── FirebaseAuthDomain = "sionyx-19636.firebaseapp.com" (NEW)
├── FirebaseProjectId  = "sionyx-19636"                 (NEW)
├── FirebaseDatabaseUrl= "https://sionyx-..."           (NEW)
├── FirebaseStorageBucket = "..."                       (NEW - optional)
├── FirebaseMessagingSenderId = "..."                   (NEW - optional)
├── FirebaseAppId      = "..."                          (NEW - optional)
└── FirebaseMeasurementId = "..."                       (NEW - optional)
```

---

## Implementation Steps

### Step 1: Create registry reader utility
**File:** `src/utils/registry_config.py`

```python
import winreg
import sys

REGISTRY_KEY = r"SOFTWARE\SIONYX"

def is_production():
    """Check if running as PyInstaller executable"""
    return getattr(sys, "frozen", False)

def read_registry_value(name: str, default: str = None) -> str:
    """Read a value from SIONYX registry key"""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY_KEY)
        value, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return value
    except (WindowsError, FileNotFoundError):
        return default

def get_all_config() -> dict:
    """Read all SIONYX config from registry"""
    return {
        "org_id": read_registry_value("OrgId"),
        "api_key": read_registry_value("FirebaseApiKey"),
        "auth_domain": read_registry_value("FirebaseAuthDomain"),
        "project_id": read_registry_value("FirebaseProjectId"),
        "database_url": read_registry_value("FirebaseDatabaseUrl"),
        # Optional values
        "storage_bucket": read_registry_value("FirebaseStorageBucket"),
        "messaging_sender_id": read_registry_value("FirebaseMessagingSenderId"),
        "app_id": read_registry_value("FirebaseAppId"),
        "measurement_id": read_registry_value("FirebaseMeasurementId"),
    }
```

### Step 2: Refactor FirebaseConfig
**File:** `src/utils/firebase_config.py`

```python
class FirebaseConfig:
    def __init__(self):
        if is_production():
            self._load_from_registry()
        else:
            self._load_from_env()
        self._validate()
    
    def _load_from_registry(self):
        """Load config from Windows Registry (production)"""
        from utils.registry_config import get_all_config
        config = get_all_config()
        self.api_key = config["api_key"]
        self.auth_domain = config["auth_domain"]
        self.database_url = config["database_url"]
        self.project_id = config["project_id"]
        self.org_id = config["org_id"]
    
    def _load_from_env(self):
        """Load config from .env file (development)"""
        # Current implementation
        load_dotenv(...)
        self.api_key = os.getenv("FIREBASE_API_KEY")
        # ... etc
```

### Step 3: Update main.py
**File:** `src/main.py`

Remove `.env` file existence check for production mode:
```python
# Only check .env in development mode
if not getattr(sys, "frozen", False):
    # Development - check .env exists
    env_path = ...
    if not env_path.exists():
        # Show error
else:
    # Production - config comes from registry
    # Will fail at FirebaseConfig._validate() if missing
    pass
```

### Step 4: Update installer.nsi
**File:** `installer.nsi`

Add registry writes for all config:
```nsis
; Write Firebase config to registry (in Section "Install")
WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "OrgId" "$OrgNameText"
WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseApiKey" "AIzaSyDS5hMOBeo1WtZdzP4L0WtpzLL0gI-S0-c"
WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseAuthDomain" "sionyx-19636.firebaseapp.com"
WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseProjectId" "sionyx-19636"
WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseDatabaseUrl" "https://sionyx-19636-default-rtdb.europe-west1.firebasedatabase.app"
WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseStorageBucket" "sionyx-19636.firebasestorage.app"
WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseMessagingSenderId" "961130757239"
WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseAppId" "1:961130757239:web:1a87dffcea40aac13f1a72"
WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseMeasurementId" "G-ZEM9LH1301"
```

Remove `.env` file creation (lines 69-94).

Update uninstaller to clean registry:
```nsis
DeleteRegKey HKLM "SOFTWARE\${APP_NAME}"
```

### Step 5: Update tests
**Files:** `*_test.py`

Mock registry reads instead of dotenv:
```python
@patch("utils.registry_config.read_registry_value")
def test_loads_from_registry(self, mock_reg):
    mock_reg.side_effect = lambda k: {"OrgId": "test-org", ...}.get(k)
    config = FirebaseConfig()
    assert config.org_id == "test-org"
```

### Step 6: Handle payment_dialog.py
The `NEDARIM_CALLBACK_URL` is optional and only used in payment dialog.
Options:
- Add to registry if needed
- Remove if not used
- Keep as environment variable (set by scheduled task if needed)

---

## Testing Checklist

- [x] Development mode: App starts with .env file
- [x] Development mode: App fails gracefully if .env missing
- [x] Production mode: App reads config from registry
- [x] Production mode: App shows clear error if registry keys missing
- [x] Installer: Creates all registry keys correctly
- [x] Uninstaller: Removes all registry keys
- [x] Unit tests: All pass with mocked registry (1516 tests)
- [ ] KioskUser: Can read registry (read-only access) - manual test needed

---

## Rollback Plan

If issues arise:
1. Revert to previous release (v1.5.x)
2. Previous installer creates .env file
3. No registry dependency

---

## Files Changed

| File | Change |
|------|--------|
| `src/utils/registry_config.py` | NEW - Registry reader utility |
| `src/utils/registry_config_test.py` | NEW - Tests for registry reader |
| `src/utils/firebase_config.py` | Refactor to use registry in production |
| `src/utils/firebase_config_test.py` | Update mocks |
| `src/main.py` | Remove .env check for production |
| `src/main_test.py` | Update mocks |
| `installer.nsi` | Add registry writes, remove .env creation |

---

## Release

- Version: **1.6.0** (minor version bump - new feature)
- Breaking change: No (old .env still works in dev mode)

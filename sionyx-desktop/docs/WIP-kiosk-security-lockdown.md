# 🔒 WIP: Kiosk Security Lockdown

> **Status**: Merged to Main ✅  
> **Branch**: `feature/kiosk-security-lockdown` → `main`  
> **Created**: 2026-01-04  
> **Updated**: 2026-01-08

## Overview

Comprehensive security for SIONYX kiosk deployments (cybercafes, gaming centers).
Prevent users from escaping kiosk mode, accessing system tools, or running unauthorized software.

**Key Features:**
- Auto-start on Windows login
- One-click installer with guided kiosk setup
- Creates restricted Windows user account automatically
- No technical knowledge required

---

## Implementation Steps

### Step 1: ✅ Create Keyboard Restriction Service
- [x] `keyboard_restriction_service.py` - Block Alt+Tab, Win key, Alt+F4, etc.
- [x] Unit tests (18 tests)

### Step 2: ✅ Create Process Restriction Service  
- [x] `process_restriction_service.py` - Kill cmd, regedit, powershell, etc.
- [x] Unit tests (28 tests)

### Step 3: ✅ Integrate Services into main.py
- [x] Import and initialize both services
- [x] Start services on app launch (kiosk mode flag)
- [x] Stop services on cleanup
- [x] Add `--kiosk` command line argument

### Step 4: ✅ Windows Auto-Start (via Installer)
- [x] Add to registry: `HKLM\Software\Microsoft\Windows\CurrentVersion\Run`
- [x] Create shortcut in All Users Startup folder (backup)
- [x] Create shortcut in KioskUser Startup folder
- [x] Uninstaller removes auto-start entries

### Step 5: ⬜ Add Kiosk Configuration (optional)
- [ ] Make restrictions configurable (enable/disable per feature)
- [ ] Config file for custom process blacklist

### Step 6: ✅ Integrated Kiosk Setup in Installer
- [x] User-friendly wizard with explanations
- [x] Create `KioskUser` standard account with custom password
- [x] Apply registry restrictions automatically
- [x] Uninstaller optionally removes user account
- [x] ~~PowerShell script~~ (deprecated - now built into installer)

### Step 7: ⬜ Final Testing & Documentation
- [ ] Test all restrictions work
- [ ] Test auto-start on login
- [ ] Document setup process for cafe owners

---

## Installation Flow (User Experience)

The installer now guides non-technical users through the complete kiosk setup:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SIONYX INSTALLER WIZARD                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Page 1: Welcome                                                    │
│  ────────────────                                                   │
│  "Welcome to SIONYX Installation"                                   │
│                                                                     │
│  Page 2: License Agreement                                          │
│  ────────────────────────────                                       │
│  Standard EULA                                                      │
│                                                                     │
│  Page 3: Install Location                                           │
│  ────────────────────────────                                       │
│  Default: C:\Program Files\SIONYX                                   │
│                                                                     │
│  Page 4: Organization Setup                                         │
│  ────────────────────────────                                       │
│  "Step 1 of 2: Organization Setup"                                  │
│  Enter your organization name: [____________]                       │
│  Examples: 'City Gaming Center', 'Tech Hub Cafe'                    │
│                                                                     │
│  Page 5: Kiosk Security Setup                                       │
│  ────────────────────────────────                                   │
│  "Step 2 of 2: Kiosk Security Setup"                                │
│                                                                     │
│  ┌─ What happens in this step? ──────────────────────────────────┐  │
│  │ We will create a special Windows user account called          │  │
│  │ 'KioskUser'. This account has limited permissions so          │  │
│  │ customers cannot:                                             │  │
│  │ - Access system settings                                      │  │
│  │ - Install software                                            │  │
│  │ - Open command prompt                                         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Create a password for the KioskUser account:                       │
│  [●●●●●●●●●●●●]                                                     │
│                                                                     │
│  Confirm password:                                                  │
│  [●●●●●●●●●●●●]                                                     │
│                                                                     │
│  NOTE: This password is for the KIOSK account (what customers       │
│  use). Your administrator account remains unchanged.                │
│                                                                     │
│  Page 6: Installing...                                              │
│  ────────────────────────                                           │
│  ============================================                       │
│    STEP 1: Creating Kiosk User Account                              │
│  ============================================                       │
│  Creating a restricted Windows user account...                      │
│  [OK] Kiosk user account ready!                                     │
│                                                                     │
│  ============================================                       │
│    STEP 2: Applying Security Restrictions                           │
│  ============================================                       │
│  [APPLYING] Disabling Run dialog (Win+R)...                         │
│  [APPLYING] Blocking Registry Editor...                             │
│  [APPLYING] Blocking Command Prompt...                              │
│  [APPLYING] Blocking Task Manager...                                │
│  [OK] Security restrictions applied!                                │
│                                                                     │
│  ============================================                       │
│    STEP 3: Setting Up Auto-Start                                    │
│  ============================================                       │
│  [OK] Added to Windows startup (all users)                          │
│  [OK] Created startup shortcut                                      │
│                                                                     │
│  ============================================                       │
│    SETUP COMPLETE!                                                  │
│  ============================================                       │
│                                                                     │
│  NEXT STEPS:                                                        │
│  1. Log out of your admin account                                   │
│  2. Log in as 'KioskUser'                                           │
│  3. SIONYX will start automatically                                 │
│                                                                     │
│  Page 7: Finish                                                     │
│  ────────────────                                                   │
│  "Installation Complete!"                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## What the Installer Does

### 1. Creates KioskUser Account
```powershell
New-LocalUser -Name "KioskUser" -Password $password 
  -FullName "SIONYX Kiosk User" 
  -Description "Restricted kiosk account for SIONYX"
  -PasswordNeverExpires
```

### 2. Ensures Limited Permissions
```powershell
# Remove from Administrators (if somehow added)
Remove-LocalGroupMember -Group "Administrators" -Member "KioskUser"

# Add to standard Users group
Add-LocalGroupMember -Group "Users" -Member "KioskUser"
```

### 3. Applies Registry Restrictions
| Restriction | Registry Key | Value |
|-------------|--------------|-------|
| Disable Run dialog (Win+R) | `NoRun` | 1 |
| Block Registry Editor | `DisableRegistryTools` | 1 |
| Block Command Prompt | `DisableCMD` | 2 |
| Block Task Manager | `DisableTaskMgr` | 1 |

### 4. Configures Auto-Start
- Adds `SIONYX.exe --kiosk` to Windows Run registry
- Creates startup shortcut for KioskUser
- Creates backup shortcut in All Users Startup

---

## Uninstaller

The uninstaller asks the user:
1. "Do you want to remove the KioskUser account?" (Yes/No)
2. If Yes: "Delete user profile folder too?" (Yes/No - warns about data loss)

Removes:
- Registry restrictions
- Auto-start entries
- Application files
- Optionally: KioskUser account and profile

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SIONYX SECURITY LAYERS                         │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 1: Windows User Accounts (CRITICAL) ← INSTALLER HANDLES     │
│    - Creates 'KioskUser' standard account (NOT admin)              │
│    - Can't install software, modify registry, etc.                  │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 2: Registry Restrictions ← INSTALLER HANDLES                 │
│    - Block Registry Editor, CMD, Task Manager                       │
│    - Disable Run dialog                                             │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 3: SIONYX Desktop App ← APP HANDLES                          │
│    - Fullscreen kiosk window (BaseKioskWindow)                      │
│    - Low-level keyboard hook (blocks Alt+Tab, Win key)              │
│    - Process monitor (kills cmd, regedit, etc.)                     │
│    - Admin exit requires password (Ctrl+Alt+Q)                      │
│    - Auto-start on Windows login                                    │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 4: Physical Security (optional, manual)                      │
│    - BIOS password                                                  │
│    - Disable USB/CD boot                                            │
│    - Lock PC case                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Files

```
sionyx-desktop/
├── docs/
│   └── WIP-kiosk-security-lockdown.md  # This file
├── scripts/
│   └── setup-kiosk-restrictions.ps1    # DEPRECATED - now in installer
├── installer.nsi                        # NSIS installer with kiosk setup
└── src/
    ├── main.py                          # Updated to start security services
    └── services/
        ├── keyboard_restriction_service.py  # Block dangerous keys
        └── process_restriction_service.py   # Kill unauthorized processes
```

---

## Current Progress

| Step | Status | Commit |
|------|--------|--------|
| Step 1 | ✅ Done | `feat: Add kiosk security lockdown services (WIP)` |
| Step 2 | ✅ Done | `feat: Add kiosk security lockdown services (WIP)` |
| Step 3 | ✅ Done | `feat(desktop): integrate kiosk services into main.py` |
| Step 4 | ✅ Done | `feat(installer): add kiosk mode with auto-start` |
| Step 5 | ⬜ Optional | - |
| Step 6 | ✅ Done | `feat(installer): integrate kiosk user setup wizard` |
| Step 7 | ⬜ TODO | - |
| Tests | ✅ Done | `Add more tests to increase coverage to 89%` |

---

*Last updated: 2026-01-08*

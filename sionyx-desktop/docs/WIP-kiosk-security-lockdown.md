# 🔒 WIP: Kiosk Security Lockdown

> **Status**: In Development  
> **Branch**: `feature/kiosk-security-lockdown`  
> **Created**: 2026-01-04  
> **Updated**: 2026-01-07

## Overview

Comprehensive security for SIONYX kiosk deployments (cybercafes, gaming centers).
Prevent users from escaping kiosk mode, accessing system tools, or running unauthorized software.

**Includes auto-start on Windows login** so users cannot log out and bypass the kiosk.

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
- [x] Add kiosk mode checkbox to installer
- [x] Add to registry: `HKLM\Software\Microsoft\Windows\CurrentVersion\Run`
- [x] Create shortcut in All Users Startup folder (backup)
- [x] Uninstaller removes auto-start entries

### Step 5: ⬜ Add Kiosk Configuration (optional)
- [ ] Make restrictions configurable (enable/disable per feature)
- [ ] Config file for custom process blacklist

### Step 6: ⬜ PowerShell Setup Script
- [ ] Create `KioskUser` standard account
- [ ] Apply registry restrictions
- [ ] Configure auto-login
- [ ] Document Group Policy settings

### Step 7: ⬜ Final Testing & Documentation
- [ ] Test all restrictions work
- [ ] Test auto-start on login
- [ ] Document setup process for cafe owners

---

## Current Progress

| Step | Status | Commit |
|------|--------|--------|
| Step 1 | ✅ Done | `feat: Add kiosk security lockdown services (WIP)` |
| Step 2 | ✅ Done | `feat: Add kiosk security lockdown services (WIP)` |
| Step 3 | ✅ Done | `feat(desktop): integrate kiosk services into main.py` |
| Step 4 | ✅ Done | `feat(installer): add kiosk mode with auto-start` |
| Step 5 | ⬜ Optional | - |
| Step 6 | ✅ Done | (PowerShell script already exists) |
| Step 7 | ⬜ TODO | - |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SIONYX SECURITY LAYERS                         │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 1: Windows User Accounts (CRITICAL)                          │
│    - Standard user accounts (NOT admin)                             │
│    - Can't install software, modify registry, etc.                  │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 2: Group Policy (GPO)                                        │
│    - Block Registry Editor, CMD, PowerShell                         │
│    - Remove Task Manager from Ctrl+Alt+Del                          │
│    - Restrict Control Panel access                                  │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 3: SIONYX Desktop App                                        │
│    - Fullscreen kiosk window (BaseKioskWindow)                      │
│    - Low-level keyboard hook (blocks Alt+Tab, Win key)              │
│    - Process monitor (kills cmd, regedit, etc.)                     │
│    - Admin exit requires password (Ctrl+Alt+Q)                      │
│    - Auto-start on Windows login                                    │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 4: Physical Security (optional)                              │
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
│   └── setup-kiosk-restrictions.ps1    # Windows setup script
└── src/
    ├── main.py                          # Updated to start security services
    └── services/
        ├── keyboard_restriction_service.py  # Block dangerous keys
        └── process_restriction_service.py   # Kill unauthorized processes
```

---

*Last updated: 2026-01-07*

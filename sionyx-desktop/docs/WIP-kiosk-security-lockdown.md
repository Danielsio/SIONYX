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
- [ ] Unit tests for keyboard service

### Step 2: ✅ Create Process Restriction Service  
- [x] `process_restriction_service.py` - Kill cmd, regedit, powershell, etc.
- [ ] Unit tests for process service

### Step 3: 🔄 Integrate Services into main.py
- [ ] Import and initialize both services
- [ ] Start services on app launch (kiosk mode flag)
- [ ] Stop services on cleanup
- [ ] Add `--kiosk` command line argument

### Step 4: ⬜ Add Kiosk Configuration
- [ ] Add `kiosk_mode` flag to config/settings
- [ ] Make restrictions configurable (enable/disable per feature)
- [ ] Log blocked attempts for security auditing

### Step 5: ⬜ Windows Auto-Start
- [ ] Add to Windows Startup folder or registry on install
- [ ] Create startup registry entry: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- [ ] Update installer (NSIS) to optionally enable auto-start

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
| Step 3 | 🔄 In Progress | - |
| Step 4 | ⬜ TODO | - |
| Step 5 | ⬜ TODO | - |
| Step 6 | ⬜ TODO | - |
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

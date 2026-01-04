# 🔒 WIP: Kiosk Security Lockdown

> **Status**: In Development  
> **Branch**: `feature/kiosk-security-lockdown`  
> **Created**: 2026-01-04  

## Overview

This feature implements comprehensive security restrictions for SIONYX kiosk deployments (cybercafes, gaming centers, etc.). The goal is to prevent users from escaping the kiosk environment, accessing system tools, or running malicious software.

---

## Architecture: Multi-Layer Defense

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
├─────────────────────────────────────────────────────────────────────┤
│  Layer 4: Physical Security (optional)                              │
│    - BIOS password                                                  │
│    - Disable USB/CD boot                                            │
│    - Lock PC case                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Sub-Tasks Checklist

### 🟡 Layer 1: Windows User Account Setup

| Task | Status | Notes |
|------|--------|-------|
| Create PowerShell setup script | ⬜ TODO | Creates standard "KioskUser" account |
| Document account setup process | ⬜ TODO | Step-by-step guide |
| Test standard user restrictions | ⬜ TODO | Verify can't install, access registry, etc. |
| Auto-login configuration | ⬜ TODO | netplwiz method |

### 🟡 Layer 2: Group Policy Configuration

| Task | Status | Notes |
|------|--------|-------|
| Document GPO settings | ⬜ TODO | Full list of required policies |
| Block Registry Editor | ⬜ TODO | `DisableRegistryTools` |
| Block Command Prompt | ⬜ TODO | `DisableCMD` |
| Block PowerShell | ⬜ TODO | Software Restriction Policy |
| Remove Task Manager | ⬜ TODO | From Ctrl+Alt+Del menu |
| Block Control Panel | ⬜ TODO | `NoControlPanel` |
| Block Settings app | ⬜ TODO | Settings Page Visibility policy |
| Test GPO restrictions | ⬜ TODO | Verify all blocked correctly |

### 🟡 Layer 3: SIONYX App Enhancements

| Task | Status | Notes |
|------|--------|-------|
| Keyboard Restriction Service | ⬜ TODO | Block Alt+Tab, Win key, Alt+F4 |
| Process Restriction Service | ⬜ TODO | Monitor and kill blacklisted processes |
| Integrate services into main.py | ⬜ TODO | Start on app launch |
| Add service unit tests | ⬜ TODO | Test keyboard hook, process killing |
| Configuration options | ⬜ TODO | Enable/disable via config file |
| Logging for blocked attempts | ⬜ TODO | Track escape attempts |

### 🟡 Layer 4: Installer & Deployment

| Task | Status | Notes |
|------|--------|-------|
| Auto-start on Windows login | ⬜ TODO | Startup folder or registry |
| Setup script in installer | ⬜ TODO | Optional "kiosk mode" during install |
| Documentation for deployment | ⬜ TODO | Full setup guide for cafe owners |

---

## Detailed Implementation Plan

### 1. Keyboard Restriction Service

**File**: `src/services/keyboard_restriction_service.py`

**Purpose**: Block dangerous keyboard shortcuts that could allow users to escape kiosk mode.

**Blocked Combinations**:
- `Alt+Tab` - Window switching
- `Alt+F4` - Close current window
- `Alt+Esc` - Cycle through windows
- `Windows Key` - Open Start menu
- `Ctrl+Shift+Esc` - Open Task Manager
- `Ctrl+Esc` - Open Start menu (alternative)

**Implementation**:
- Uses Windows Low-Level Keyboard Hook (`WH_KEYBOARD_LL`)
- Runs in separate thread with its own message loop
- Returns `1` to block key, or passes to next hook

**Note**: `Ctrl+Alt+Delete` CANNOT be blocked programmatically - it's handled by the Windows kernel. Use Group Policy to remove options from that screen.

```python
# Key constants
WH_KEYBOARD_LL = 13
VK_TAB = 0x09
VK_LWIN = 0x5B
VK_RWIN = 0x5C
# etc.
```

### 2. Process Restriction Service

**File**: `src/services/process_restriction_service.py`

**Purpose**: Monitor running processes and terminate any that are blacklisted.

**Default Blacklist**:
```python
BLACKLIST = {
    # System tools
    "regedit.exe",        # Registry Editor
    "cmd.exe",            # Command Prompt
    "powershell.exe",     # PowerShell
    "pwsh.exe",           # PowerShell Core
    "taskmgr.exe",        # Task Manager
    "control.exe",        # Control Panel
    "mmc.exe",            # Management Console
    
    # Script hosts
    "wscript.exe",        # Windows Script Host
    "cscript.exe",        # Console Script Host
    
    # Remote access
    "teamviewer.exe",
    "anydesk.exe",
}
```

**Implementation**:
- Uses `psutil` to enumerate processes
- Polls every 2 seconds
- Calls `proc.terminate()` then `proc.kill()` if needed
- Emits signal when process is blocked

### 3. Windows Setup Script

**File**: `scripts/setup-kiosk-restrictions.ps1`

**Purpose**: Automate Windows configuration for kiosk mode.

**Actions**:
1. Create `KioskUser` standard account
2. Apply registry restrictions
3. Configure auto-login (optional)
4. Set SIONYX to auto-start
5. Display Group Policy instructions

---

## Group Policy Settings Reference

Run `gpedit.msc` as Administrator and configure:

### User Configuration > Administrative Templates

#### System
| Policy | Setting |
|--------|---------|
| Prevent access to registry editing tools | **Enabled** |
| Prevent access to the command prompt | **Enabled** (Disable script processing: Yes) |
| Don't run specified Windows applications | **Enabled** (Add: powershell.exe, cmd.exe) |

#### System > Ctrl+Alt+Del Options
| Policy | Setting |
|--------|---------|
| Remove Task Manager | **Enabled** |
| Remove Lock Computer | **Enabled** |
| Remove Change Password | **Enabled** |
| Remove Logoff | **Enabled** (optional) |

#### Control Panel
| Policy | Setting |
|--------|---------|
| Prohibit access to Control Panel and PC settings | **Enabled** |

#### Windows Components > File Explorer
| Policy | Setting |
|--------|---------|
| Hide these specified drives in My Computer | **Enabled** (restrict C:) |
| Prevent access to drives from My Computer | **Enabled** |
| Remove "Map Network Drive" and "Disconnect Network Drive" | **Enabled** |

---

## Testing Checklist

Before deploying, verify each restriction works:

- [ ] Try pressing Alt+Tab → Should be blocked
- [ ] Try pressing Windows key → Should be blocked
- [ ] Try pressing Ctrl+Shift+Esc → Should be blocked (or Task Manager killed)
- [ ] Try running `cmd.exe` → Should be killed immediately
- [ ] Try running `regedit.exe` → Should be killed immediately
- [ ] Try Ctrl+Alt+Delete → Task Manager option should be missing
- [ ] Try opening Control Panel → Should be blocked by GPO
- [ ] Try installing software → Should fail (standard user)
- [ ] App remains fullscreen → Cannot be minimized
- [ ] App cannot be closed → Except via Ctrl+Alt+Q + password

---

## Security Considerations

### What This CANNOT Protect Against

1. **Physical access attacks** - USB boot, removing hard drive
2. **Admin credentials** - If attacker knows admin password
3. **Kernel exploits** - Zero-day vulnerabilities
4. **BIOS access** - Boot to Safe Mode or USB

### Mitigations

1. **Physical security**: Lock PC cases, disable USB boot in BIOS
2. **Strong passwords**: Use complex admin passwords
3. **Keep updated**: Windows updates patch vulnerabilities
4. **Monitor logs**: Review blocked attempts regularly

---

## Files in This Branch

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

## References

- [Windows Low-Level Keyboard Hook](https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelkeyboardproc)
- [Windows Group Policy](https://learn.microsoft.com/en-us/windows/client-management/group-policies-overview)
- [AppLocker Documentation](https://learn.microsoft.com/en-us/windows/security/threat-protection/windows-defender-application-control/applocker/applocker-overview)
- [psutil Documentation](https://psutil.readthedocs.io/)

---

*Last updated: 2026-01-04*


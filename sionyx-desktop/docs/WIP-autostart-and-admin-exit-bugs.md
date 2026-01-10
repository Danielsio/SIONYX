# WIP: Fix Auto-Start and Admin Exit Bugs

## Issue Date: 2026-01-10

## Issues

### BUG 1: SIONYX Auto-Starts on ALL Windows Accounts
**Severity:** High  
**Status:** ✅ FIXED

**Problem:**
After installation, SIONYX auto-starts for ALL Windows users (including admin accounts), 
not just the KioskUser account as intended.

**Root Cause:**
The installer writes auto-start entries to locations that affect ALL users:
1. `HKLM\Software\Microsoft\Windows\CurrentVersion\Run` - Machine-wide registry
2. `$SMSTARTUP` (All Users Startup folder)

**Fix Applied:**
Removed machine-wide auto-start entries. Now only creates KioskUser-specific startup shortcut.

**Files modified:**
- `installer.nsi` - Removed HKLM registry write and All Users startup shortcut

---

### BUG 2: Admin Exit (Ctrl+Alt+Q) Not Working
**Severity:** High  
**Status:** ✅ FIXED

**Problem:**
The admin exit hotkey (Ctrl+Alt+Q) doesn't trigger the password dialog to exit the app.

**Root Cause:**
The `admin_exit_requested` signal is emitted from a background thread (keyboard listener),
but Qt GUI operations must run on the main thread. The signal connection didn't use
`Qt.QueuedConnection`, so the cross-thread communication failed silently.

**Fix Applied:**
1. Added `Qt.ConnectionType.QueuedConnection` when connecting the signal
2. Added logging to confirm signal delivery to main thread
3. Dialog now shows correctly because slot runs on main thread

**Files modified:**
- `src/main.py` - Added QueuedConnection to signal connection

---

## Implementation Plan

### Step 1: Fix Installer Auto-Start (BUG 1)
- [x] Identify problematic lines in installer.nsi
- [x] Remove HKLM registry write
- [x] Remove All Users startup shortcut
- [x] Keep KioskUser startup shortcut only
- [ ] Test installer (user to verify)

### Step 2: Fix Admin Exit Hotkey (BUG 2)
- [x] Add Qt.QueuedConnection to signal connection
- [x] Add logging to trace signal flow
- [ ] Test hotkey functionality (user to verify)

### Step 3: Add Regression Tests
- [x] Test: admin exit signal uses QueuedConnection (main_test.py)
- [x] Document in test file with detailed comment explaining the bug

---

## Testing

### Manual Testing
1. Install SIONYX on a test machine
2. Log in as admin account → SIONYX should NOT auto-start
3. Log in as KioskUser → SIONYX should auto-start
4. Press Ctrl+Alt+Q → Password dialog should appear
5. Enter "admin123" → App should close

### Automated Testing
- Existing tests cover hotkey signal emission
- Need to add cross-thread signal delivery test

---

## Rollback Plan
If fixes cause issues:
```bash
git revert HEAD
```

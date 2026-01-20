# SIONYX Desktop Issues Tracker

This document tracks known issues, bugs, and their resolution status.

---

## Open Issues

### ISSUE-001: PyQt6-WebEngine Missing from Requirements
**Status:** FIXED  
**Severity:** Critical  
**Date Found:** 2026-01-21  
**Component:** `ui/payment_dialog.py`

**Description:**  
Clicking "Buy Package" crashes the app with `ModuleNotFoundError: No module named 'PyQt6.QtWebEngineWidgets'`.

**Root Cause:**  
`PyQt6-WebEngine` package was not listed in `requirements.txt` but is required by `payment_dialog.py`.

**Fix Applied:**
1. Added `PyQt6-WebEngine` to `requirements.txt`
2. Added graceful error handling in `payment_dialog.py` to catch ImportError and log it properly
3. PaymentDialog now raises a clear error message if WebEngine is not available

**Note:**  
This error was NOT logged to the log file because it happened during module import (before logging was initialized). The fix now logs the error if the import fails.

---

### ISSUE-002: Duplicated org path in get_admin_contact()
**Status:** FIXED  
**Severity:** Medium  
**Date Found:** 2026-01-21  
**Component:** `services/organization_metadata_service.py`

**Description:**  
Error in logs: `401 Unauthorized` for URL with duplicated path:
```
organizations/sionov/organizations/sionov/metadata.json
```

**Root Cause:**  
The `get_admin_contact(org_id)` method was using the full path `organizations/{org_id}/metadata`, but `firebase_client.db_get()` already prefixes paths with `organizations/{org_id}/` automatically (multi-tenancy). This resulted in a duplicated path.

**Fix Applied:**
1. Changed `get_admin_contact()` to use just `"metadata"` as the path (not the full org path)
2. Removed the `org_id` parameter since firebase_client handles it automatically
3. Updated all callers (`help_page.py`, `auth_window.py`) and tests

---

### ISSUE-003: Import Errors Not Logged
**Status:** Open - Design Improvement Needed  
**Severity:** Low  
**Date Found:** 2026-01-21  
**Component:** Logging System

**Description:**  
When a module fails to import (like PyQt6-WebEngine), the error is not captured in the log files because:
1. The import happens at module load time
2. Logging is not yet configured when the import fails
3. Python exits before any logging can occur

**Recommendation:**  
Consider wrapping critical imports in try-except blocks with early logging initialization, as done for `payment_dialog.py`.

---

## Resolved Issues Archive

### ISSUE-R001: Package Purchase Crash - Missing User UID
**Status:** RESOLVED  
**Date Fixed:** 2026-01-20  
**Component:** `ui/payment_dialog.py`, `ui/pages/packages_page.py`

**Description:**  
App crashed when clicking "Buy Package" due to `KeyError` when accessing `self.user["uid"]` with empty user dict.

**Fix:**  
Added validation for user UID in PaymentDialog, with graceful error handling in PackagesPage.

---

## How to Add New Issues

Use this template:

```markdown
### ISSUE-XXX: Brief Title
**Status:** Open | In Progress | Fixed | Resolved  
**Severity:** Critical | High | Medium | Low  
**Date Found:** YYYY-MM-DD  
**Component:** file/path.py

**Description:**  
What happened and how to reproduce.

**Root Cause:**  
Why it happened.

**Fix Applied:**  
What was changed to fix it.
```

---

## Log Analysis Commands

To search for errors in logs:

```powershell
# View recent errors
Get-Content "logs\sionyx_errors_*.log" | Select-Object -Last 50

# Search for specific error
Select-String -Path "logs\*.log" -Pattern "ERROR"

# Search for exceptions
Select-String -Path "logs\*.log" -Pattern "exception|traceback" -CaseSensitive:$false
```

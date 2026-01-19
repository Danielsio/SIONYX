# WIP: Session Improvements & Bug Fixes

## Overview
Implementing multiple session-related improvements and bug fixes in a single development session.

**Date Started:** 2026-01-19
**Current Version:** v1.7.2

---

## Task List

| # | Task | Type | Status | Branch | Release |
|---|------|------|--------|--------|---------|
| 1 | Remove redundant "החשבון שלי" button | Bug Fix | ✅ Done | `fix/redundant-timer-button` | v1.7.3 |
| 2 | Clear browser cookies on session end | Feature | ✅ Done | `feature/session-end-cleanup` | v1.8.0 |
| 3 | Close all programs on session start | Feature | ⏳ Pending | `feature/session-start-cleanup` | Minor |
| 4 | Package expiration/deadline | Feature | ⏳ Pending | `feature/package-expiration` | Minor |

---

## Task 1: Remove Redundant Button

### Problem
The floating timer has a "החשבון שלי" (My Account) button that is redundant if "יציאה" (Exit) does the same thing.

### Files to Modify
- `src/ui/floating_timer.py` - Remove button
- `src/ui/floating_timer_test.py` - Update tests

### Implementation Steps
- [ ] Step 1.1: Analyze current button behavior
- [ ] Step 1.2: Remove redundant button from UI
- [ ] Step 1.3: Update/remove related tests
- [ ] Step 1.4: Verify functionality
- [ ] Step 1.5: Commit and merge

### Progress Log
```
[2026-01-19] Started Task 1
[2026-01-19] Created branch: fix/redundant-timer-button
[2026-01-19] Removed account_button from floating_timer.py
[2026-01-19] Reduced widget height from 140 to 110
[2026-01-19] Removed 3 related tests
[2026-01-19] All 56 tests passing
[2026-01-19] ✅ COMPLETED - Merged and released as v1.7.3
```

---

## Task 2: Clear Browser Cookies on Session End

### Problem
When a session ends, the previous user's browser sessions (Gmail, etc.) remain logged in, allowing the next user to access their accounts.

### Solution
Clear browser cookies/data when session ends. Options:
1. Delete cookie folders for Chrome/Edge/Firefox
2. Use browser-specific cleanup commands
3. Clear user profile data

### Files to Modify
- `src/services/session_service.py` - Add cleanup on session end
- `src/services/browser_cleanup_service.py` - NEW: Browser cleanup logic
- `src/ui/main_window.py` - Trigger cleanup on session end

### Implementation Steps
- [ ] Step 2.1: Create BrowserCleanupService
- [ ] Step 2.2: Implement Chrome cookie cleanup
- [ ] Step 2.3: Implement Edge cookie cleanup
- [ ] Step 2.4: Implement Firefox cookie cleanup
- [ ] Step 2.5: Integrate with session end flow
- [ ] Step 2.6: Add comprehensive tests
- [ ] Step 2.7: Commit and merge

### Progress Log
```
[2026-01-19] Started Task 2
[2026-01-19] Created branch: feature/session-end-cleanup
[2026-01-19] Created BrowserCleanupService with Chrome/Edge/Firefox support
[2026-01-19] Integrated cleanup into SessionService.end_session()
[2026-01-19] Added 24 tests for BrowserCleanupService
[2026-01-19] Added 4 tests for session service integration
[2026-01-19] All tests passing
[2026-01-19] ✅ COMPLETED - Merged and released as v1.8.0
```

---

## Task 3: Close All Programs on Session Start

### Problem
When a new session starts, previous user's programs may still be open, creating a messy/insecure experience.

### Solution
Close all non-essential programs when a session starts, leaving only SIONYX and system processes.

### Files to Modify
- `src/services/session_service.py` - Add cleanup on session start
- `src/services/process_cleanup_service.py` - NEW: Process cleanup logic
- `src/ui/main_window.py` - Trigger cleanup on session start

### Implementation Steps
- [ ] Step 3.1: Create ProcessCleanupService
- [ ] Step 3.2: Define whitelist of allowed processes
- [ ] Step 3.3: Implement graceful process termination
- [ ] Step 3.4: Integrate with session start flow
- [ ] Step 3.5: Add comprehensive tests
- [ ] Step 3.6: Commit and merge

### Progress Log
```
[Pending]
```

---

## Task 4: Package Expiration/Deadline

### Problem
Packages currently have no expiration. Admin wants to sell time-limited packages (e.g., "100 hours valid for 30 days").

### Solution
Add optional expiration to packages. When user buys, countdown starts. After deadline, remaining time resets.

### Database Changes
- `packages/{id}`: Add `validityDays` field (optional, 0 = no expiration)
- `users/{id}`: Add `timeExpiresAt` field (ISO timestamp, null = no expiration)

### Files to Modify (Desktop)
- `src/services/session_service.py` - Check expiration before session start
- `src/services/purchase_service.py` - Set expiration on purchase
- `src/ui/pages/home_page.py` - Show expiration warning

### Files to Modify (Web Admin)
- `src/pages/PackagesPage.jsx` - Add validity days input
- `src/pages/UsersPage.jsx` - Show expiration in user details
- `src/services/packageService.js` - Handle validity days

### Files to Modify (Firebase Functions)
- `functions/index.js` - Handle expiration in purchase flow

### Implementation Steps
- [ ] Step 4.1: Update database rules for new fields
- [ ] Step 4.2: Update package creation (web admin)
- [ ] Step 4.3: Update purchase flow to set expiration
- [ ] Step 4.4: Check expiration on session start (desktop)
- [ ] Step 4.5: Add expiration UI in home page
- [ ] Step 4.6: Add comprehensive tests
- [ ] Step 4.7: Deploy functions and merge

### Progress Log
```
[Pending]
```

---

## Release Plan

After each task:
1. Run tests to ensure coverage
2. Merge to main
3. Create appropriate release (patch/minor)
4. Tag and push

| Task | Release Type | Expected Version |
|------|--------------|------------------|
| Task 1 | Patch | v1.7.3 |
| Task 2 | Minor | v1.8.0 |
| Task 3 | Minor | v1.9.0 |
| Task 4 | Minor | v1.10.0 |

---

## Recovery Instructions

If the session crashes, tell the AI:
> "Continue from WIP-session-improvements.md - check the Progress Log for each task to see where we left off."

---

*Last Updated: 2026-01-19*

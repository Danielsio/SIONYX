# SIONYX - TODO & Roadmap

## 🎨 UI/UX Improvements

- [x] **App Logo** - Add application logo/icon
  - ✅ Taskbar icon, window title bar (BaseKioskWindow sets icon)
  - ✅ Desktop shortcut icon (installer uses app-logo.ico)
  - ✅ Executable icon (PyInstaller embeds icon)
  - ✅ Installer icon (NSIS uses icon)

- [ ] **UI Makeover** - Pages currently look awful, need full redesign
  - HomePage, PackagesPage, HistoryPage, HelpPage
  - Modern design, better layout, improved visuals

- [ ] **Notification UI** - Improve desktop notification appearance
  - Better styling, animations, positioning
  - Different styles for success/warning/error

- [x] **Loading Animations** (v1.4.0) - Show loading spinner during API operations
  - ✅ Display loading overlay when login/register is in progress
  - ✅ Block UI interactions while loading
  - ✅ Modern animated spinner with fade effects

- [x] **Session Return Flow** - Improve handling when returning to app during session
  - ✅ `return_from_session()` handles smooth transition from floating timer
  - ✅ Session state properly managed via SessionService
  - ✅ Home page data refreshed on return

## 🚀 Features (Planned)

- [x] **Kiosk Security Lockdown** 🔒 - Prevent users from escaping kiosk mode (v1.2.0)
  - ✅ `KeyboardRestrictionService` - Low-level hooks block Alt+Tab, Win key, Ctrl+Shift+Esc, Alt+F4
  - ✅ `ProcessRestrictionService` - Monitors and kills cmd, regedit, powershell, taskmgr
  - ✅ Integrated into main.py with `--kiosk` flag
  - ✅ 100% test coverage on process service, 50% on keyboard service
  - ⬜ Optional: Config file for custom process blacklist
  - 📄 PowerShell setup script exists: `scripts/setup-kiosk-restrictions.ps1`

- [x] **Kiosk Mode / Auto-Run** - App runs automatically on system startup (v1.2.0)
  - ✅ Installer adds to Windows registry: `HKLM\Software\Microsoft\Windows\CurrentVersion\Run`
  - ✅ Installer creates shortcut in All Users Startup folder (backup)
  - ✅ Launches with `--kiosk` flag by default
  - ✅ Only admin can exit (Ctrl+Alt+Q + password)
  - ✅ Uninstaller removes auto-start entries

- [ ] **Media Blocker** - Block video players and streaming sites during sessions
  - Monitor processes (VLC, Netflix, etc.)
  - Detect browser tabs with YouTube, Netflix via window titles
  - Configurable: warn vs block mode

- [x] **Color Print Detection** - Detect if print job is color vs B&W
  - ✅ Uses DEVMODE.Color to detect color vs B&W
  - ✅ Different pricing for color prints (via org metadata)

## 🏗️ Code Architecture

- [x] **Design Patterns** - Applied design patterns where they provide real value

  ### ✅ Singleton Pattern (v1.1.2 & v1.1.3)
  - `FirebaseClient` - Thread-safe singleton, `get_instance()`, `reset_instance()`
  - `LocalDatabase` - Prevents multiple SQLite connections, consistent encryption
  - Files: `services/firebase_client.py`, `database/local_db.py`

  ### ✅ Decorator Pattern (v1.1.2)
  - Created `services/decorators.py` with reusable decorators
  - `@authenticated`, `@log_operation`, `@handle_firebase_errors`, `@service_method`
  - Refactored `DatabaseService` - 6 methods now use decorators
  - 22 tests for decorator functionality

  ### ❌ Not Implemented (Evaluated, not needed)
  - **Factory Pattern** - Services are simple, `FirebaseClient` singleton is enough
  - **State Pattern** - Session code is clean (~100 lines), would add complexity
  - **Strategy Pattern** - Print pricing comes from DB, no multiple strategies needed
  - **Command Pattern** - No undo/redo requirements currently
  - **Event Bus** - PyQt signals work well, no decoupling issues

## ⚡ Performance

- [x] **Firebase Polling Optimization** - Replaced polling with SSE streaming
  - Added `StreamListener` class to `FirebaseClient` for real-time SSE connections
  - Refactored `ChatService` to use SSE instead of polling
  - Instant message notifications (no 5-60 second delay)
  - Single persistent connection instead of repeated HTTP requests
  - Auto-reconnect with exponential backoff on connection errors

## 🐛 Known Issues

- [ ] **Hebrew encoding in console** - Document names with Hebrew show as gibberish in PowerShell
  - Workaround: `chcp 65001` before running
  - Functionality works fine, just display issue

## ✅ Recently Completed

- [x] **Kiosk Security Lockdown** (v1.2.0) - Full kiosk mode implementation
  - Keyboard hooks block system shortcuts (Alt+Tab, Win key, etc.)
  - Process monitor kills unauthorized apps (cmd, regedit, powershell)
  - Auto-start on Windows login via installer
  - Admin exit with Ctrl+Alt+Q + password
  - 89% test coverage maintained

- [x] **Release Workflow** (v1.3.0) - Single-command releases
  - `make release-minor` does full flow: branch → build → merge → tag → push
  - `make merge-feature` with coverage regression check
  - Prevents merging if test coverage drops

- [x] **Single Session Enforcement** - Prevent user from logging in on multiple computers
  - If already logged in elsewhere, reject new login attempt with message "המשתמש כבר מחובר במחשב אחר"
  - Allow re-login on the same computer (for app restart scenarios)
  - Uses isLoggedIn and currentComputerId from Firebase
- [x] **Active Users Card Layout** - Unified users display with computers
  - Converted "משתמשים פעילים" table to card-based layout
  - Matching style with "סקירת מחשבים" cards
  - Click to expand for details (phone, computer, session time)
  - Responsive and clean UI
- [x] **Computer Data Simplification** - Minimal data model for computers
  - `isActive` now derived from `currentUserId` (no separate field)
  - Removed: `lastSeen`, `lastUserLogin`, `lastUserLogout`, `osInfo`, `macAddress`, `hardwareId`, `networkInfo`
  - User: removed `currentComputerName`, `lastComputerLogout`
  - Only store: `computerName`, `deviceId`, `currentUserId`, `createdAt`, `updatedAt`
- [x] **Computers Page Redesign** - Improved admin dashboard computers view
  - Removed unused columns (מיקום, נראה לאחרונה) - data not collected
  - Fixed "משתמש נוכחי" to show actual username or "לא בשימוש כעת"
  - Converted table to responsive card-based layout
  - Unified "כל המחשבים" tab to use same card layout
- [x] **Registration Login State Fix** - Fixed bug where signup didn't set isLoggedIn
  - register() now calls _handle_computer_registration() like login()
  - User is now properly associated with computer after signup
  - isLoggedIn is set to true in Firebase after signup
  - Enables single-session enforcement to work for newly registered users
- [x] **User Field Refactor** - Cleaned up user data structure
  - Fixed orphan session recovery bug (wasn't clearing computer association)
  - Removed unused fields: computerHistory, sessionComputerName, lastComputerLogin
  - Reduces Firebase writes and simplifies data model
- [x] **Print Monitor Service** - WMI event-driven + polling fallback
- [x] **Page count detection** - Wait for spooling to complete
- [x] **Multiple copies support** - Detect copies from DEVMODE
- [x] **Refactor remainingPrints → printBalance** - All apps + Firebase
- [x] **Handle empty Firebase collections** - No crash on missing data

---
*Last updated: 2026-01-07*


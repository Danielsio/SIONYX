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

- [x] **Session Return Flow** - Improve handling when returning to app during session
  - ✅ `return_from_session()` handles smooth transition from floating timer
  - ✅ Session state properly managed via SessionService
  - ✅ Home page data refreshed on return

## 🚀 Features (Planned)

- [ ] **Kiosk Security Lockdown** 🔒 - Prevent users from escaping kiosk mode
  - **Branch**: `feature/kiosk-security-lockdown`
  - **WIP Doc**: `sionyx-desktop/docs/WIP-kiosk-security-lockdown.md`
  - Multi-layer defense: Windows user accounts + Group Policy + app restrictions
  - Keyboard hooks to block Alt+Tab, Win key, Ctrl+Shift+Esc
  - Process monitor to kill cmd, regedit, powershell, taskmgr
  - PowerShell setup script for kiosk PC configuration
  - Group Policy documentation for system admins

- [ ] **Kiosk Mode / Auto-Run** - App runs automatically on system startup
  - Add to Windows startup registry on install
  - Only admin can exit the application
  - Prevent regular users from closing/killing the app

- [ ] **Media Blocker** - Block video players and streaming sites during sessions
  - Monitor processes (VLC, Netflix, etc.)
  - Detect browser tabs with YouTube, Netflix via window titles
  - Configurable: warn vs block mode

- [x] **Color Print Detection** - Detect if print job is color vs B&W
  - ✅ Uses DEVMODE.Color to detect color vs B&W
  - ✅ Different pricing for color prints (via org metadata)

## 🏗️ Code Architecture

- [ ] **Design Patterns** - Apply consistent design patterns across the codebase

  ### 1. ✅ Singleton Pattern (DONE)

  #### FirebaseClient
  - ✅ `FirebaseClient` now uses Singleton pattern
  - ✅ `__new__` controls instance creation, returns same object
  - ✅ Thread-safe with `_lock` for concurrent access
  - ✅ `get_instance()` method for explicit singleton access
  - ✅ `reset_instance()` for testing
  - File: `services/firebase_client.py`

  #### LocalDatabase
  - ✅ `LocalDatabase` now uses Singleton pattern
  - ✅ Prevents multiple SQLite connections to same file
  - ✅ Ensures consistent encryption state
  - ✅ Thread-safe with `_lock` for concurrent access
  - ✅ `get_instance()` and `reset_instance()` methods
  - ✅ 6 tests for singleton behavior
  - File: `database/local_db.py`

  ### 2. Factory Pattern - Service Creation
  - Services are created manually in `main.py`, `AuthService`, `MainWindow`
  - Create `ServiceFactory` to centralize service instantiation
  - Benefits: dependency injection, easier testing, single source of truth

  ### 3. State Pattern - Session States
  - `SessionService` uses boolean flags (`is_active`, `warned_5min`, etc.)
  - States: Inactive → Active → Warning → Critical → Expired
  - Cleaner transitions, each state handles its own behavior

  ### 4. Command Pattern - User Actions
  - Actions like start_session, end_session, logout could be Command objects
  - Benefits: undo/redo capability, action history, command queuing
  - Useful for offline-first features

  ### 5. ✅ Decorator Pattern - Cross-Cutting Concerns (DONE)
  - ✅ Created `services/decorators.py` with reusable decorators
  - ✅ `@authenticated` - checks auth before method runs
  - ✅ `@log_operation` - auto-logs method entry with args
  - ✅ `@handle_firebase_errors` - catches exceptions, returns error response
  - ✅ `@service_method` - composite decorator combining all three
  - ✅ Refactored `DatabaseService` - 6 methods now use decorators
  - ✅ 22 tests for decorator functionality

  ### 6. Event Bus - Centralized Events
  - Currently signals are scattered across services
  - Create `EventBus` singleton for app-wide events
  - Events: USER_LOGGED_IN, SESSION_STARTED, PRINT_COMPLETED, etc.
  - Better decoupling between components

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
*Last updated: 2026-01-04*


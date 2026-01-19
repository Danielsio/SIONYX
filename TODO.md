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

## ✅ Recently Completed (v1.7.0)

- [x] **Admin-Assisted Password Reset** - Users can request password reset through admin
  - **Problem**: Users have fake phone-to-email (e.g., `0501234567@sionyx.app`), can't use standard Firebase reset
  - **Solution**: When user forgets password, notify admin who can reset it manually
  
  ### Implementation:
  - [x] Desktop: Update "שכחת את הסיסמה?" to show admin contact info (phone number in Hebrew)
  - [x] Desktop: Fetch admin contact from organization metadata via `get_admin_contact()`
  - [x] Firebase Function: `resetUserPassword` - allows admin to set new password for user
  - [x] Organization registration stores admin_phone and admin_email in metadata
  - [x] Web Admin: Add "איפוס סיסמה" button in UsersPage user details drawer
  - [x] Add tests for all new functionality (14 new tests)
  
  ### User Flow:
  1. User clicks "שכחת את הסיסמה?" on login screen
  2. Desktop shows: "לאיפוס סיסמה, אנא פנה למנהל: [phone]" (Hebrew)
  3. User calls/contacts admin
  4. Admin opens web dashboard → Users → finds user → clicks "איפוס סיסמה"
  5. Admin sets new password, tells user
  6. User logs in with new password

## 🐛 Known Issues / Bugs

- [ ] **Print Monitor - First Print No Reaction** 🔴 HIGH PRIORITY
  - First time someone prints, there is no reaction from the system
  - Second time there is a reaction but no actual charge is deducted
  - Needs investigation: WMI event subscription timing? Job detection race condition?
  - Related: `services/print_monitor_service.py`

- [x] **Floating Timer - Redundant Button** ✅ FIXED (v1.7.3)
  - Removed "החשבון שלי" button from floating timer
  - "יציאה" button does the same thing (emit return_clicked)
  - Widget height reduced from 140 to 110 for compact design

- [ ] **Hebrew encoding in console** - Document names with Hebrew show as gibberish in PowerShell
  - Workaround: `chcp 65001` before running
  - Functionality works fine, just display issue

## 🚀 Features (Planned)

### Session Management Improvements

- [x] **Session Start - Close All Programs** ✅ COMPLETED (v1.9.0)
  - Created `ProcessCleanupService` with whitelist/targets
  - Closes browsers, Office apps, media players, etc. on session start
  - Whitelist protects SIONYX, system processes, Windows core
  - 22 tests added for cleanup service

- [x] **Session End - Logout from Gmail/Websites** ✅ COMPLETED (v1.8.0)
  - Created `BrowserCleanupService` for cookie/session cleanup
  - Clears Chrome, Edge, Firefox cookies and login data
  - Closes browsers before cleanup for clean deletion
  - 24 tests added for cleanup service

### Package System Enhancements

- [x] **Package Expiration/Deadline** ✅ COMPLETED (v1.10.0)
  - Packages now have optional `validityDays` field
  - Users have `timeExpiresAt` set when purchasing expiring packages
  - Session start checks expiration and resets time if expired
  - Web admin: Package creation shows validity days input
  - Web admin: User details show expiration date
  - Firebase function sets expiration on purchase completion
  - 5 tests added for expiration checking

## 🧪 Testing

- [x] **Integration Tests** - Complete user flow testing ✅
  - 📄 See: `sionyx-desktop/docs/WIP-integration-tests.md`
  - ✅ Created test structure: `src/tests/integration/`
  - ✅ Service integration tests: 9/9 passing (registration, login, session, logout flows)
  - ✅ UI integration tests: 16/16 passing (auth window, navigation, floating timer)
  - ✅ Full user journey test (registration → login → session → logout)
  - ⬜ Add to CI pipeline (optional future work)

- [x] **Unit Test Coverage** - Improved from 92% to 93%
  - ✅ Added tests for device_info exception paths
  - ✅ Added tests for ModernMessageBox static methods
  - ✅ Added tests for PrintMonitorService exception handling
  - ✅ Added tests for logger ColoredFormatter
  - ✅ Added tests for base_window icon path logic

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
*Last updated: 2026-01-19*


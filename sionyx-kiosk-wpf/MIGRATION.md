# SIONYX Kiosk - WPF Migration: Comprehensive Gap Analysis & Plan

> Last updated: 2026-02-13
> Original: `sionyx-kiosk/` (Python/PyQt6)
> Target: `sionyx-kiosk-wpf/` (C#/WPF/.NET 8)

---

## How This Document Works

Each item below maps a **specific piece of Python logic** to its WPF equivalent.
- Status: `TODO` | `IN PROGRESS` | `DONE`
- Commit type: `LOGIC` (pure Python→C# conversion) or `UI/UX` (visual/interaction)
- Each item = 1 commit when completed

---

## Part A: LOGIC Commits (Python → C# Conversion)

### A1. Authentication Flow

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| A1.1 | Login (phone→email, Firebase sign-in) | `auth_service.py:login()` | `AuthService.cs:LoginAsync()` | DONE | Phone converted to email, Firebase REST sign-in |
| A1.2 | Register (validate, sign-up, create user in RTDB) | `auth_service.py:register()` | `AuthService.cs:RegisterAsync()` | DONE | Creates user node at `users/{uid}` |
| A1.3 | **Token persistence (store REAL refresh token)** | `local_db.py:store_credentials()` with Fernet encryption | `AuthService.cs` stores `"stored"` instead of real token | **TODO** | Python encrypts and stores the actual refresh token. WPF stores the string "stored" — auto-login after restart is broken. Must store `_firebase.RefreshToken` in `LocalDatabase` and restore it on startup. |
| A1.4 | **Auto-login (restore session from stored token)** | `auth_service.py:is_logged_in()` → refresh token → load user → recover orphaned session → register computer | `App.xaml.cs:TryAutoLoginAsync()` calls `AuthService.IsLoggedInAsync()` | **TODO** | Python's `is_logged_in()` does: (1) get stored token, (2) refresh Firebase token, (3) load user data, (4) check orphaned session, (5) register computer. WPF's `IsLoggedInAsync()` needs to restore the token to `FirebaseClient` then do the same chain. |
| A1.5 | **Single-session enforcement** | `auth_service.py:login()` checks `isSessionActive` on user node | `AuthService.cs:LoginAsync()` | **TODO** | Python checks if user already has an active session on another PC and blocks login. WPF login doesn't check this. |
| A1.6 | **Orphaned session recovery** | `auth_service.py:_recover_orphaned_session()` | Not implemented | **TODO** | If a previous session crashed, Python detects the orphan (isSessionActive=true but no computer associated) and recovers the remaining time. |
| A1.7 | Logout (disassociate computer, clear tokens, end session) | `auth_service.py:logout()` | `AuthService.cs:LogoutAsync()` | DONE | Clears local DB and Firebase user association |
| A1.8 | **Forgot password (show admin contact)** | `auth_window.py` shows admin contact from metadata | Not implemented | **TODO** | Python auth window has a "forgot password?" link that shows admin phone/email from `OrganizationMetadataService`. |

### A2. Session Management

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| A2.1 | Start session (time check, cleanup, update Firebase) | `session_service.py:start_session()` | `SessionService.cs:StartSessionAsync()` | DONE | Sets `isSessionActive`, `sessionStartTime` |
| A2.2 | Countdown timer (1s interval, decrement remaining time) | `session_service.py:_countdown_timer` | `SessionService.cs` uses `DispatcherTimer` | DONE | Fires `TimeUpdated` event |
| A2.3 | Sync timer (60s interval, push remaining time to Firebase) | `session_service.py:_sync_timer` | `SessionService.cs` uses `DispatcherTimer` | DONE | Pushes `remainingTime` + `updatedAt` |
| A2.4 | End session (stop timers, final sync, browser cleanup) | `session_service.py:end_session()` | `SessionService.cs:EndSessionAsync()` | DONE | Calls `BrowserCleanupService`, resets Firebase |
| A2.5 | 5-minute / 1-minute warnings | `session_service.py` emits `warning_5min`, `warning_1min` | `SessionService.cs` fires `Warning5Min`, `Warning1Min` events | DONE | |
| A2.6 | **Sync failure/recovery detection** | `session_service.py` emits `sync_failed`, `sync_restored` | `SessionService.cs` fires events | **TODO** | Python tracks consecutive sync failures and emits a signal when sync fails/recovers. WPF has the events defined but the `_SyncToFirebase` method doesn't track failures. |
| A2.7 | Time expiration check before start | `session_service.py:start_session()` checks remaining time > 0 | `SessionService.cs:StartSessionAsync()` | DONE | |
| A2.8 | **Operating hours integration in session** | `session_service.py` starts `OperatingHoursService`, handles `hours_ending_soon`/`hours_ended` | `SessionService.cs` | **TODO** | Python starts operating hours monitoring inside `start_session()` and wires up the signals. WPF creates the service but doesn't wire the events to session behavior. |

### A3. Print Monitoring

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| A3.1 | Printer change notification (primary detection) | `print_monitor_service.py:_monitor_thread()` with `FindFirstPrinterChangeNotification` | `PrintMonitorService.cs:MonitorPrintJobs()` | DONE | P/Invoke implementation |
| A3.2 | Fallback polling (QTimer every 2s) | `print_monitor_service.py:_check_print_jobs()` | `PrintMonitorService.cs` | DONE | `DispatcherTimer` fallback |
| A3.3 | Pause job → check budget → approve/deny | `print_monitor_service.py:_process_job()` | `PrintMonitorService.cs:ProcessPrintJob()` | DONE | Pause, budget check, resume/cancel |
| A3.4 | Cost calculation (pages × copies × price per page) | `print_monitor_service.py:_calculate_cost()` | `PrintMonitorService.cs:CalculateCost()` | DONE | B&W vs color pricing |
| A3.5 | **Budget deduction on Firebase** | `print_monitor_service.py` updates `users/{uid}/printBalance` | `PrintMonitorService.cs` | **TODO** | Python deducts the cost from the user's `printBalance` on Firebase after allowing a job. WPF calculates cost but may not correctly update Firebase. Need to verify the Firebase write path. |
| A3.6 | **Escaped job handling (charge retroactively)** | `print_monitor_service.py` detects jobs that bypass pause and charges retroactively (allows debt) | `PrintMonitorService.cs` | **TODO** | Critical: some jobs escape the pause. Python handles this by charging after the fact. WPF needs this safety net. |
| A3.7 | **PrintMonitorService not started** | Started in `session_service.py:start_session()` | Not started anywhere | **TODO** | `PrintMonitorService.StartMonitoring()` is never called. Must be started when session starts. |

### A4. Package & Payment Flow

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| A4.1 | Fetch packages from Firebase | `package_service.py:get_all_packages()` | `PackageService.cs:GetAllPackagesAsync()` | DONE | |
| A4.2 | Calculate final price with discount | `package_service.py:calculate_final_price()` | `PackageService.cs` | DONE | |
| A4.3 | Create pending purchase | `purchase_service.py:create_pending_purchase()` | `PurchaseService.cs:CreatePendingPurchaseAsync()` | DONE | |
| A4.4 | Get purchase history | `purchase_service.py:get_user_purchase_history()` | `PurchaseService.cs:GetUserPurchaseHistoryAsync()` | DONE | |
| A4.5 | Get purchase statistics | `purchase_service.py:get_purchase_statistics()` | `PurchaseService.cs:GetPurchaseStatisticsAsync()` | DONE | |
| A4.6 | **Payment bridge (Python↔JS communication)** | `payment_bridge.py` uses QWebChannel: JS calls `createPendingPurchase()`, Python responds with `purchase_created` signal | Not implemented | **TODO** | Python uses QWebChannel for bidirectional JS↔Python. WPF must use WebView2's `CoreWebView2.WebMessageReceived` and `PostWebMessageAsString` for the same flow. |
| A4.7 | **Payment dialog (load URL, inject config, listen for completion)** | `payment_dialog.py:_load_payment_page()` starts local server, loads payment.html, injects Firebase config | `PaymentDialog.xaml.cs` has WebView2 but never loads URL | **TODO** | Python starts `LocalFileServer`, navigates to `http://localhost:{port}/payment.html?...`, and monitors purchase status via Firebase stream or polling. WPF has an empty shell. |
| A4.8 | **Purchase completion detection (SSE or polling)** | `payment_dialog.py` listens for purchase status change via Firebase stream | Not implemented | **TODO** | When payment completes externally, Python detects the status change on the purchase node and closes the dialog. |
| A4.9 | **Wire PurchaseRequested to PaymentDialog** | `packages_page.py` opens `PaymentDialog` on package select | `PackagesViewModel.PurchaseRequested` event exists but nothing subscribes | **TODO** | The event fires but no UI code catches it to open the payment dialog. |

### A5. Chat / Messaging

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| A5.1 | SSE listener for messages | `chat_service.py:start_listening()` with `db_listen("messages")` | `ChatService.cs:StartListening()` | DONE | |
| A5.2 | Get unread messages | `chat_service.py:get_unread_messages()` | `ChatService.cs:GetUnreadMessagesAsync()` | DONE | |
| A5.3 | Mark message as read | `chat_service.py:mark_message_as_read()` | `ChatService.cs:MarkMessageAsReadAsync()` | DONE | |
| A5.4 | Mark all messages as read | `chat_service.py:mark_all_messages_as_read()` | `ChatService.cs:MarkAllAsReadAsync()` | DONE | |
| A5.5 | Update last seen | `chat_service.py:update_last_seen()` | `ChatService.cs:UpdateLastSeenAsync()` | DONE | |
| A5.6 | **ChatService never started** | Started in `home_page.py` on page load | Not started anywhere | **TODO** | `ChatService.StartListening()` is never called. Should start after login with the user's ID. |
| A5.7 | **HomeViewModel doesn't show unread count** | `home_page.py` updates unread badge from `ChatService` | `HomeViewModel.cs` has `UnreadMessages` property but never updates it | **TODO** | Need to subscribe to `ChatService.MessagesReceived` event and update the count. |
| A5.8 | **Message modal not wired** | `home_page.py` opens `MessageModal` when messages clicked | No connection between Home UI and MessageDialog | **TODO** | Need to wire a button/click on Home to open MessageDialog. |

### A6. Force Logout

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| A6.1 | SSE listener on force logout path | `force_logout_listener.py` listens on `users/{uid}/forceLogout` | `ForceLogoutService.cs` listens on `force_logout/{userId}` | **TODO** | **Path mismatch!** Python listens on `organizations/{orgId}/users/{uid}/forceLogout`. WPF listens on `force_logout/{userId}`. Must align to the actual Firebase schema. |
| A6.2 | Force logout triggers session end + return to auth | `force_logout_listener.py` emits `force_logout_received` → `main_window` handles it | `ForceLogoutService.cs` fires `ForceLogoutReceived` | **TODO** | Event exists but nothing in App.xaml.cs or MainWindow subscribes to it to actually force-logout the user. |

### A7. Keyboard & Process Restrictions

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| A7.1 | Low-level keyboard hook (block Alt+Tab, Win, etc.) | `keyboard_restriction_service.py:start()` | `KeyboardRestrictionService.cs:Start()` | DONE | P/Invoke `SetWindowsHookEx` |
| A7.2 | **KeyboardRestrictionService never started** | Started in `main.py` for kiosk mode | Not started in `App.xaml.cs` | **TODO** | Should start when `--kiosk` flag is present. |
| A7.3 | Process blacklist monitoring | `process_restriction_service.py:start()` | `ProcessRestrictionService.cs:Start()` | DONE | |
| A7.4 | Process cleanup before session | `process_cleanup_service.py:cleanup_user_processes()` | `ProcessCleanupService.cs:CleanupUserProcesses()` | DONE | |
| A7.5 | **GlobalHotkeyService never started** | Started in `main.py` | Not started in `App.xaml.cs` | **TODO** | Needs a window handle (`HWND`). Must start after MainWindow is shown. |
| A7.6 | **Admin exit hotkey handler** | `global_hotkey_service.py` emits `admin_exit_requested` → shows password dialog → exits | Event exists but nothing handles it | **TODO** | When hotkey pressed, should show password dialog. If correct password entered, close kiosk and return to normal Windows. |

### A8. Operating Hours

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| A8.1 | Fetch operating hours from metadata | `operating_hours_service.py:_load_settings()` | `OperatingHoursService.cs` loads from Firebase | DONE | |
| A8.2 | Check if currently within hours | `operating_hours_service.py:is_within_operating_hours()` | `OperatingHoursService.cs:IsWithinOperatingHours()` | DONE | |
| A8.3 | Grace period handling | `operating_hours_service.py` handles `gracePeriodMinutes`, `graceBehavior` | `OperatingHoursService.cs` | DONE | |
| A8.4 | **Wire hours_ending/hours_ended to session** | `session_service.py` subscribes to operating hours signals | Events defined but not wired | **TODO** | When hours end, session should end gracefully. |

### A9. Computer Registration

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| A9.1 | Register computer in Firebase | `computer_service.py:register_computer()` | `ComputerService.cs:RegisterComputerAsync()` | DONE | |
| A9.2 | Associate user with computer | `computer_service.py:associate_user_with_computer()` | `ComputerService.cs:AssociateUserAsync()` | DONE | |
| A9.3 | Disassociate user from computer | `computer_service.py:disassociate_user_from_computer()` | `ComputerService.cs:DisassociateUserAsync()` | DONE | |
| A9.4 | **Computer registration called on login** | `auth_service.py:login()` calls `computer_service.register_computer()` then `associate_user_with_computer()` | Not called in WPF login flow | **TODO** | After successful login, WPF must register the computer and associate the user. |

### A10. Browser Cleanup

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| A10.1 | Close browsers | `browser_cleanup_service.py:close_browsers()` | `BrowserCleanupService.cs:CloseBrowsers()` | DONE | |
| A10.2 | Clear browser data (cookies, history, sessions) | `browser_cleanup_service.py:cleanup_all_browsers()` for Chrome, Edge, Firefox | `BrowserCleanupService.cs:CleanupAllBrowsers()` | DONE | |
| A10.3 | **Cleanup with browser close (close first, then clean)** | `browser_cleanup_service.py:cleanup_with_browser_close()` | `BrowserCleanupService.cs` | **TODO** | Python has a specific method that first closes browsers, waits, then cleans data. Verify WPF does the same sequence. |

### A11. Configuration & Infrastructure

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| A11.1 | Firebase config from registry (production) | `firebase_config.py` + `registry_config.py` | `FirebaseConfig.cs` + `RegistryConfig.cs` | DONE | |
| A11.2 | Firebase config from .env (development) | `firebase_config.py` uses `python-dotenv` | `DotEnvLoader.cs` + `FirebaseConfig.cs` | DONE | |
| A11.3 | Structured logging with rotation | `logger.py` with file rotation, context, request ID | `Serilog` in `App.xaml.cs` | DONE | Serilog handles rotation natively |
| A11.4 | **Log directory: AppData in prod, ./logs in dev** | `logger.py` uses `AppData/Local/SIONYX/logs` in prod | Serilog writes to `logs/` always | **TODO** | Should use `AppData` path in production/kiosk mode. |
| A11.5 | **Old log cleanup (7 days)** | `logger.py:cleanup_old_logs(days_to_keep=7)` | Not implemented | **TODO** | Serilog's `retainedFileCountLimit` can handle this but it's not configured. |
| A11.6 | **Crash log writing** | `main.py:_write_crash_log()` | `App.xaml.cs` has global exception handlers but no crash file | **TODO** | Python writes a specific crash log file. WPF should do the same for debugging in production. |
| A11.7 | Device ID (MAC-based hash) | `device_info.py:get_device_id()` | `DeviceInfo.cs:GetDeviceId()` | DONE | |
| A11.8 | Error translations (Firebase → Hebrew) | `error_translations.py` | `ErrorTranslations.cs` | DONE | |

### A12. App Lifecycle & DI

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| A12.1 | Single-instance enforcement | `main.py` (not explicitly, but implied) | `App.xaml.cs` uses `Mutex` | DONE | |
| A12.2 | **Auth→Main window transition** | `main.py:_show_main_window()` | `App.xaml.cs:ShowMainWindow()` | **TODO** | Currently crashes after login. Need to debug: likely missing resource `BgPrimaryBrush` in MainWindow.xaml, or DI resolution failure for MainWindow dependencies. |
| A12.3 | **Main→Auth transition (logout)** | `main_window.py` emits logout → `main.py` shows auth window | `MainViewModel.LogoutRequested` event | **TODO** | Event exists but the subscription in `ShowMainWindow` to handle it may not work correctly. |
| A12.4 | **Start system services after login** | `main.py:_start_services()` starts keyboard, hotkey, process restriction | `App.xaml.cs:StartSystemServices()` only starts ForceLogout, OperatingHours, ProcessRestriction | **TODO** | Missing: KeyboardRestriction, GlobalHotkey (needs HWND), ChatService, PrintMonitor (on session start). |
| A12.5 | **Stop system services on logout** | Python stops all services on logout | `App.xaml.cs:StopSystemServices()` | **TODO** | Must cleanly stop all services (SSE listeners, timers, hooks) when user logs out. |
| A12.6 | CLI args (--kiosk, --verbose) | `main.py` parses args | `App.xaml.cs` parses args | DONE | |
| A12.7 | **Kiosk mode fullscreen** | `main_window.py` sets fullscreen, no frame, always on top | `MainWindow.xaml` has `WindowStyle="None"` but not fullscreen logic | **TODO** | In kiosk mode: `WindowState="Maximized"`, `Topmost="True"`, no taskbar. |

---

## Part B: UI/UX Commits (Visual & Interaction)

### B1. Auth Window

| # | Feature | Python Source | Status | Notes |
|---|---------|-------------|--------|-------|
| B1.1 | Sliding panel animation (login↔register) | `auth_window.py` with QPropertyAnimation | **TODO** | Currently just shows/hides fields. Should have smooth slide transition. |
| B1.2 | Loading state on buttons (spinner inside button) | `auth_window.py` shows loading spinner | **TODO** | Buttons should show a spinner when `IsLoading=true`. |
| B1.3 | Input validation visual feedback | `auth_window.py` highlights invalid fields | **TODO** | Red border on empty required fields. |
| B1.4 | Password visibility toggle | Not in Python | **TODO** | Nice UX addition: eye icon to show/hide password. |
| B1.5 | Smooth gradient animation on left panel | Not in Python | **TODO** | Subtle gradient shift animation for polish. |
| B1.6 | **Forgot password link** | `auth_window.py` has forgot password section | **TODO** | Shows admin contact info from metadata service. |

### B2. Main Window & Navigation

| # | Feature | Python Source | Status | Notes |
|---|---------|-------------|--------|-------|
| B2.1 | **Missing `BgPrimaryBrush` resource** | N/A | **TODO** | `MainWindow.xaml` references `BgPrimaryBrush` which doesn't exist in `Colors.xaml`. App crashes on navigation. |
| B2.2 | Sidebar with active page indicator | `main_window.py` highlights active nav button | **TODO** | Active page should have highlighted/selected state on sidebar button. |
| B2.3 | Page transition animations (fade/slide) | `main_window.py` with QPropertyAnimation | **TODO** | Smooth fade or slide when switching pages in the Frame. |
| B2.4 | User info in sidebar (name, avatar placeholder) | `main_window.py` shows user name in sidebar | **TODO** | Display logged-in user name and phone in sidebar. |
| B2.5 | Unread messages badge on sidebar | `main_window.py` shows message count badge | **TODO** | Red badge with count on the Messages/Home nav item. |
| B2.6 | **Kiosk mode UI (fullscreen, no chrome)** | `main_window.py` kiosk-specific styling | **TODO** | Fullscreen, no title bar, no close button in kiosk mode. |

### B3. Home Page

| # | Feature | Python Source | Status | Notes |
|---|---------|-------------|--------|-------|
| B3.1 | Stats cards (time, print balance, messages) | `home_page.py` with StatCard components | DONE | StatCard controls exist |
| B3.2 | **Live stat updates from services** | `home_page.py` subscribes to `SessionService.time_updated`, `ChatService` | **TODO** | Stats should update in real-time as session counts down, print balance changes, new messages arrive. |
| B3.3 | Start/End session buttons with state management | `home_page.py` toggle between start/end | **TODO** | Button text and behavior should change based on session state. |
| B3.4 | **Operating hours warning banner** | `home_page.py` shows warning when hours ending | **TODO** | Yellow banner at top when operating hours are ending soon. |
| B3.5 | Welcome message with user name | `home_page.py` shows "שלום, {name}" | **TODO** | Personalized greeting. |

### B4. Packages Page

| # | Feature | Python Source | Status | Notes |
|---|---------|-------------|--------|-------|
| B4.1 | **Fix `PrintPages` → `Prints` binding** | N/A | **TODO** | XAML binds to `PrintPages` but model property is `Prints`. Binding silently fails. |
| B4.2 | Package cards with hover effects | `packages_page.py` with FrostCard styling | **TODO** | Cards should lift/shadow on hover. |
| B4.3 | Discount badge on discounted packages | `packages_page.py` shows discount percentage | **TODO** | Visual badge showing "20% הנחה" etc. |
| B4.4 | **Open PaymentDialog on package select** | `packages_page.py` opens `PaymentDialog` | **TODO** | Currently `PurchaseRequested` fires but nothing catches it. |
| B4.5 | Purchase confirmation dialog | `packages_page.py` confirms before payment | **TODO** | "Are you sure?" dialog before starting payment. |

### B5. History Page

| # | Feature | Python Source | Status | Notes |
|---|---------|-------------|--------|-------|
| B5.1 | Purchase history list with status badges | `history_page.py` with colored status badges | DONE | PurchaseCard and StatusBadge exist |
| B5.2 | **StatusBadge color mapping** | `history_page.py` maps status to color | **TODO** | StatusBadge control exists but has no logic to map status strings to colors (pending=yellow, completed=green, failed=red). |
| B5.3 | Summary statistics (total spent, total purchases) | `history_page.py` shows summary | DONE | HistoryViewModel has totals |
| B5.4 | Empty state when no purchases | `history_page.py` shows empty message | DONE | EmptyState control exists |

### B6. Help Page

| # | Feature | Python Source | Status | Notes |
|---|---------|-------------|--------|-------|
| B6.1 | FAQ accordion (expandable items) | `help_page.py` with collapsible cards | DONE | |
| B6.2 | Admin contact card | `help_page.py` loads from metadata | DONE | |

### B7. Floating Timer

| # | Feature | Python Source | Status | Notes |
|---|---------|-------------|--------|-------|
| B7.1 | Topmost draggable window | `floating_timer.py` with frameless, always-on-top | DONE | FloatingTimer control exists |
| B7.2 | **Show timer when session starts** | `main_window.py:_start_session()` creates FloatingTimer | **TODO** | Timer control exists but is never instantiated or shown when a session begins. |
| B7.3 | Time remaining display (MM:SS format) | `floating_timer.py` formats time | DONE | |
| B7.4 | Warning colors (normal→yellow→red) | `floating_timer.py` changes color at 5min/1min | DONE | |
| B7.5 | "Return to app" button on timer | `floating_timer.py` has button to bring main window to front | **TODO** | |
| B7.6 | Print balance display on timer | `floating_timer.py` shows print balance | **TODO** | Python timer shows time, usage duration, and print balance. |

### B8. Payment Dialog

| # | Feature | Python Source | Status | Notes |
|---|---------|-------------|--------|-------|
| B8.1 | **WebView2 loads payment page** | `payment_dialog.py` loads `localhost:{port}/payment.html` | **TODO** | WebView2 exists in XAML but no code loads a URL. |
| B8.2 | **Local server starts for payment HTML** | `payment_dialog.py` starts `LocalFileServer` | **TODO** | `LocalFileServer.cs` exists but is not registered in DI or used. |
| B8.3 | **JS↔C# bridge via WebView2** | `payment_bridge.py` uses QWebChannel | **TODO** | Need `CoreWebView2.WebMessageReceived` handler and `PostWebMessageAsString`. |
| B8.4 | Payment completion/cancellation handling | `payment_dialog.py` emits signals on completion | **TODO** | |
| B8.5 | Loading overlay during payment | `payment_dialog.py` shows loading state | **TODO** | |

### B9. Dialogs

| # | Feature | Python Source | Status | Notes |
|---|---------|-------------|--------|-------|
| B9.1 | Alert dialog (info/success/warning/error) | `alert_modal.py` | DONE | AlertDialog exists |
| B9.2 | Confirmation dialog | `modern_dialogs.py` | DONE | ModernDialog exists |
| B9.3 | Message dialog (read messages flow) | `message_modal.py` | DONE | MessageDialog exists |
| B9.4 | **Message accessibility (keyboard nav, screen reader)** | `message_accessibility.py` | **TODO** | Python has accessibility features for messages. |

---

## Part C: Build & Distribution

| # | Feature | Python Source | WPF File | Status | Notes |
|---|---------|-------------|----------|--------|-------|
| C1 | NSIS installer | `installer.nsi` | `installer.nsi` | DONE | Adapted for .NET output |
| C2 | Build script (version, compile, package) | `build.py` | `build.ps1` | DONE | PowerShell equivalent |
| C3 | **Firebase Storage upload** | `build.py:upload_to_firebase()` uploads installer to Firebase Storage and updates `public/latestRelease` | `build.ps1` does not upload | **TODO** | Python build script uploads the installer and updates the download URL. WPF build script only builds locally. |
| C4 | **payment.html template** | `templates/payment.html` | Not copied to WPF project | **TODO** | The payment HTML file that gets served by LocalFileServer must be included in the WPF project as an embedded resource or content file. |

---

## Part D: Testing

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| D1 | ViewModels unit tests | DONE | Auth, Main, Help, Message |
| D2 | Models unit tests | DONE | UserData, Package, Purchase |
| D3 | Infrastructure unit tests | DONE | AppConstants, DeviceInfo, ErrorTranslations |
| D4 | **Service integration tests** | **TODO** | Auth flow, session lifecycle, print monitor with mock Firebase |
| D5 | **Payment flow tests** | **TODO** | End-to-end payment with mock WebView |
| D6 | **UI automation tests** | **TODO** | FlaUI for kiosk scenario testing |

---

## Execution Plan

### Round 1: LOGIC Commits (Python → C#, no UI changes)

Order of commits (each = 1 Git commit):

1. **LOGIC: Fix token persistence** (A1.3, A1.4) — Store real refresh token, restore on startup
2. **LOGIC: Fix Auth→Main transition** (A12.2) — Debug and fix window transition crash
3. **LOGIC: Single-session enforcement** (A1.5) — Block login if session active elsewhere
4. **LOGIC: Orphaned session recovery** (A1.6) — Detect and recover crashed sessions
5. **LOGIC: Computer registration on login** (A9.4) — Register PC and associate user after login
6. **LOGIC: Wire ChatService startup** (A5.6, A5.7) — Start listening, update unread count
7. **LOGIC: Wire ForceLogout end-to-end** (A6.1, A6.2) — Fix path, wire event to logout
8. **LOGIC: Wire PrintMonitor to session** (A3.7, A3.5, A3.6) — Start on session, budget deduction, escaped jobs
9. **LOGIC: Wire OperatingHours to session** (A2.8, A8.4) — Hours ending → session end
10. **LOGIC: Payment bridge (WebView2↔C#)** (A4.6, A4.7, A4.8) — Full payment flow
11. **LOGIC: Wire PurchaseRequested to PaymentDialog** (A4.9) — Connect packages to payment
12. **LOGIC: Start system services properly** (A7.2, A7.5, A7.6, A12.4, A12.5) — All services started/stopped correctly
13. **LOGIC: Kiosk mode fullscreen** (A12.7) — Fullscreen, no chrome in kiosk mode
14. **LOGIC: Sync failure tracking** (A2.6) — Track consecutive failures, emit events
15. **LOGIC: Log directory & cleanup** (A11.4, A11.5, A11.6) — AppData in prod, 7-day rotation, crash log
16. **LOGIC: Forgot password flow** (A1.8) — Show admin contact

### Round 2: UI/UX Commits (Visual & Polish)

17. **UI/UX: Fix MainWindow `BgPrimaryBrush`** (B2.1) — Add missing resource
18. **UI/UX: Auth window animations & polish** (B1.1–B1.6) — Slide, loading, validation, forgot password
19. **UI/UX: Main window sidebar & navigation** (B2.2–B2.6) — Active indicator, transitions, user info, badge
20. **UI/UX: Home page live updates** (B3.1–B3.5) — Real-time stats, session buttons, welcome, warnings
21. **UI/UX: Packages page polish** (B4.1–B4.5) — Fix binding, hover effects, discount badge, purchase flow
22. **UI/UX: History page StatusBadge colors** (B5.2) — Color mapping
23. **UI/UX: Floating timer full integration** (B7.2–B7.6) — Show on session, return button, print balance
24. **UI/UX: Payment dialog full UI** (B8.1–B8.5) — WebView, loading, completion
25. **UI/UX: Modern design overhaul** — Final polish pass across all screens

---

## Progress Tracker

| Commit # | Type | Description | Status |
|----------|------|-------------|--------|
| 1 | LOGIC | Fix token persistence + auto-login | TODO |
| 2 | LOGIC | Fix Auth→Main window transition | TODO |
| 3 | LOGIC | Single-session enforcement | TODO |
| 4 | LOGIC | Orphaned session recovery | TODO |
| 5 | LOGIC | Computer registration on login | TODO |
| 6 | LOGIC | Wire ChatService startup + unread count | TODO |
| 7 | LOGIC | Wire ForceLogout end-to-end | TODO |
| 8 | LOGIC | Wire PrintMonitor to session lifecycle | TODO |
| 9 | LOGIC | Wire OperatingHours to session | TODO |
| 10 | LOGIC | Payment bridge (WebView2) | TODO |
| 11 | LOGIC | Wire PurchaseRequested → PaymentDialog | TODO |
| 12 | LOGIC | Start/stop all system services properly | TODO |
| 13 | LOGIC | Kiosk mode fullscreen | TODO |
| 14 | LOGIC | Sync failure tracking | TODO |
| 15 | LOGIC | Log directory + cleanup + crash log | TODO |
| 16 | LOGIC | Forgot password flow | TODO |
| 17 | UI/UX | Fix MainWindow BgPrimaryBrush | TODO |
| 18 | UI/UX | Auth window animations & polish | TODO |
| 19 | UI/UX | Main window sidebar & navigation | TODO |
| 20 | UI/UX | Home page live updates & session UI | TODO |
| 21 | UI/UX | Packages page polish + payment wiring | TODO |
| 22 | UI/UX | History page StatusBadge colors | TODO |
| 23 | UI/UX | Floating timer full integration | TODO |
| 24 | UI/UX | Payment dialog full UI | TODO |
| 25 | UI/UX | Modern design overhaul - final polish | TODO |

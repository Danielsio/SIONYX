# SIONYX - TODO & Roadmap

## 🎨 UI/UX Improvements

- [ ] **App Logo** - Add application logo/icon
  - Taskbar icon, window title bar
  - About page/splash screen
  - Desktop shortcut icon

- [ ] **UI Makeover** - Pages currently look awful, need full redesign
  - HomePage, PackagesPage, HistoryPage, HelpPage
  - Modern design, better layout, improved visuals

- [ ] **Notification UI** - Improve desktop notification appearance
  - Better styling, animations, positioning
  - Different styles for success/warning/error

- [ ] **Session Return Flow** - Improve handling when returning to app during session
  - Smoother transition from floating timer back to main window
  - Better state management

## 🚀 Features (Planned)

- [ ] **Single Session Enforcement** - Prevent user from logging in on multiple computers
  - If already logged in elsewhere, reject new login attempt
  - Show dedicated error message/notification to user
  - Track active sessions in Firebase

- [ ] **Kiosk Mode / Auto-Run** - App runs automatically on system startup
  - Add to Windows startup registry on install
  - Only admin can exit the application
  - Prevent regular users from closing/killing the app

- [ ] **Media Blocker** - Block video players and streaming sites during sessions
  - Monitor processes (VLC, Netflix, etc.)
  - Detect browser tabs with YouTube, Netflix via window titles
  - Configurable: warn vs block mode

- [ ] **Color Print Detection** - Detect if print job is color vs B&W
  - Currently assumes all prints are B&W
  - Would allow different pricing for color

## ⚡ Performance

- [ ] **Firebase Polling Optimization** - Improve message service listener
  - Better SSE connection handling
  - Reduce unnecessary polling/reconnects

## 🐛 Known Issues

- [ ] **Hebrew encoding in console** - Document names with Hebrew show as gibberish in PowerShell
  - Workaround: `chcp 65001` before running
  - Functionality works fine, just display issue

## ✅ Recently Completed

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
*Last updated: 2024-12-31*


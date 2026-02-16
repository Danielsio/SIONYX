# WIP — Migration Completion Progress

## Goal
Fix all remaining migration gaps, then remove the original `sionyx-kiosk/` Python app.

## Status: COMPLETE

### Completed (session 1)
- [x] Session minimize/restore when session starts/ends
- [x] Operating hours pre-session check in HomeViewModel
- [x] FloatingTimer: usage time, print balance, offline indicator
- [x] Print monitor → FloatingTimer print balance updates
- [x] Sync offline indicator on FloatingTimer
- [x] Force logout notification dialog before redirect
- [x] MessageDialog opened from HomePage via message card
- [x] FloatingTimer return button wired to end session
- [x] MainViewModel double-logout bug fixed (sync Logout, no auth call)
- [x] Frame journal memory leak fixed (Content= instead of Navigate)
- [x] HomeViewModel IDisposable + event unsubscription

### Completed (session 2)
- [x] History page: search box, status filter dropdown, sort toggle (ICollectionView)
- [x] Help page: click-to-copy for admin phone/email
- [x] Toast notification control: auto-dismiss overlay for print events, session warnings
- [x] Wired toasts in App.xaml.cs for: print allowed/blocked, 5min/1min warnings
- [x] FrostComboBox style added to Theme.xaml
- [x] Updated Makefile for WPF (dotnet build/test/run)
- [x] Updated scripts (release.py, merge_feature.py, merge_release.py)
- [x] Updated .cursor/rules/project-conventions.mdc
- [x] Removed `sionyx-kiosk/` directory entirely
- [x] Updated MIGRATION_AUDIT.md to mark everything complete
- [x] All 800 tests passing, 0 errors, 0 warnings

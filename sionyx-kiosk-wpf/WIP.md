# WIP — Migration Completion Progress

## Goal
Fix all remaining migration gaps, then remove the original `sionyx-kiosk/` Python app.

## Status

### Completed (previous session)
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

### In Progress (this session)
- [ ] History page: search box, status filter dropdown, sort toggle
- [ ] Help page: click-to-copy for admin phone/email
- [ ] Toast notification control: auto-dismiss overlay for print events, session warnings
- [ ] Wire toasts in App.xaml.cs for: print allowed/blocked, 5min/1min warnings, operating hours warning

### After all gaps fixed
- [ ] Commit: "fix: complete all WPF migration gaps"
- [ ] Remove `sionyx-kiosk/` directory entirely
- [ ] Commit: "chore: remove original Python kiosk (fully replaced by WPF)"
- [ ] Update MIGRATION_AUDIT.md to mark everything complete

## Files to modify

### History filters
- `ViewModels/HistoryViewModel.cs` — add SearchText, SelectedStatus, SortAscending, FilteredPurchases
- `Views/Pages/HistoryPage.xaml` — add search TextBox, status ComboBox, sort button
- `Views/Pages/HistoryPage.xaml.cs` — no changes needed (MVVM binding)

### Help click-to-copy
- `ViewModels/HelpViewModel.cs` — add CopyPhoneCommand, CopyEmailCommand
- `Views/Pages/HelpPage.xaml` — add copy buttons next to phone/email

### Toast notifications
- `Views/Controls/ToastNotification.xaml` + `.cs` — new control (auto-dismiss overlay)
- `App.xaml.cs` — wire print monitor events + session warnings to show toasts
- `Views/Windows/MainWindow.xaml` — add toast overlay container

## Recovery instructions
If the session crashes mid-work:
1. Read this file to see what's done vs pending
2. Run `dotnet build` in `sionyx-kiosk-wpf/src/SionyxKiosk` to check compile state
3. Run `dotnet test` in `sionyx-kiosk-wpf/` to check test state
4. Continue from the first unchecked item above

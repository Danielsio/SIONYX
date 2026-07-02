# IMP-006: Logout Button Missing Loading State and Double-Click Guard

## Problem
The "התנתק" (Logout) button in the sidebar had no protection against double-clicks.
Since the logout flow involves stopping services, Firebase cleanup, and window
transitions, clicking it multiple times could trigger parallel logout sequences.

## Root Cause
`MainViewModel.Logout()` directly invoked `LogoutRequested` without any guard.
The button in `MainWindow.xaml` had no `IsEnabled` binding.

## Fix
**ViewModel (`MainViewModel.cs`):**
- Added `IsLoggingOut` observable property
- `Logout()` checks `IsLoggingOut` before proceeding (double-click guard)
- Sets `IsLoggingOut = true` immediately on first click

**View (`MainWindow.xaml`):**
- Logout button `IsEnabled` bound to `!IsLoggingOut` via `InverseBool` converter
- Button becomes visually disabled after first click

**Code-behind (`MainWindow.xaml.cs`):**
- Registered `InverseBoolConverter` in window resources

## Impact
- Prevents duplicate logout sequences and race conditions
- User sees the button become disabled immediately after clicking

## Status: FIXED

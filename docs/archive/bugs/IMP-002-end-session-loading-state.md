# IMP-002: End Session Missing Loading State and Double-Click Protection

## Problem
The "סיים הפעלה" (End Session) button had no loading indicator and no protection
against double-clicks. Since `EndSessionAsync` involves Firebase sync + browser
cleanup (which can take several seconds), users could:

1. Click multiple times, triggering duplicate `EndSessionAsync` calls
2. See no visual feedback while the operation was in progress
3. Think the app was frozen

## Root Cause
`HomeViewModel.EndSessionAsync()` did not set any loading flag. The End button
in `HomePage.xaml` had no `IsEnabled` binding and no loading spinner.

## Fix
**ViewModel (`HomeViewModel.cs`):**
- Added `IsEndingSession` observable property
- `EndSessionAsync` now checks `IsEndingSession` to prevent re-entry (double-click guard)
- Sets `IsEndingSession = true` before the operation, `false` in `finally`
- Added try/catch with user-facing error message

**View (`HomePage.xaml`):**
- End button `IsEnabled` bound to `!IsEndingSession` via `InverseBool` converter
- Added `LoadingSpinner` below the End button, visible during the operation

## Impact
- Users see a spinner while session ends
- Button is disabled during the operation (no double-click)
- Errors are shown in the error banner instead of silently swallowed

## Status: FIXED

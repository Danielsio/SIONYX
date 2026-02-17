# IMP-007: Auth Window Loading Feedback Improvements

## Problem
1. Login/Register buttons were disabled during loading but showed no visual change
   in text -- users couldn't tell the operation was in progress
2. "Forgot Password" button had no loading state at all -- stayed clickable while
   fetching admin contact info from Firebase
3. No visual indication that the app was "working"

## Fix
**ViewModel (`AuthViewModel.cs`):**
- Added `LoginButtonText` computed property: "מתחבר..." during load, "התחבר" idle
- Added `RegisterButtonText` computed property: "נרשם..." during load, "הירשם" idle
- `ForgotPasswordAsync` now sets `IsLoading = true/false`, disabling all buttons

**View (`AuthWindow.xaml`):**
- Login button `Content` bound to `LoginButtonText` (shows "מתחבר..." while loading)
- Register button `Content` bound to `RegisterButtonText` (shows "נרשם..." while loading)
- Forgot password button `IsEnabled` bound to `!IsLoading` (disabled during any operation)

## Impact
- Clear visual feedback during login/register: button text changes to "connecting..."
- Forgot password is disabled while any auth operation is in progress
- Consistent loading behavior across all auth actions

## Status: FIXED

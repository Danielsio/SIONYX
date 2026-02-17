# BUG-005: "אין באפשרותנו להיכנס לחשבון שלך" on First KioskUser Logon

## Problem
After running the SIONYX installer, when logging into the `KioskUser` Windows
account for the first time, Windows shows a "temporary profile" error dialog:

> "אין באפשרותנו להיכנס לחשבון שלך"
> (We can't sign in to your account)

The user is logged in with a temporary profile, meaning settings, files, and
the kiosk app configuration are lost on logout.

## Root Cause
The installer creates `KioskUser` via `net user "KioskUser" "" /add`, then
**manually creates directories** at `C:\Users\KioskUser\AppData\...` before
the user has ever logged in.

Windows creates a proper user profile (with `ntuser.dat` and a registry entry
in `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList`) only on
**first interactive logon**. When the installer manually creates the folder
`C:\Users\KioskUser`, Windows finds the directory on first logon but has no
matching `ProfileList` registry entry. It falls back to a temporary profile.

**Flow before fix:**
1. `net user KioskUser "" /add` → user created, NO profile yet
2. `New-Item C:\Users\KioskUser\AppData\...` → directory created manually
3. User logs in → Windows sees `C:\Users\KioskUser` exists but has no
   ProfileList entry → **temporary profile** error

## Fix
Added a profile initialization step between user creation and directory setup:

1. After creating the user, check if `C:\Users\KioskUser\ntuser.dat` exists
   (indicates a properly initialized profile)
2. If not, run a PowerShell script that spawns a dummy process as KioskUser
   using `Start-Process -Credential ... -LoadUserProfile`
3. This forces Windows to create the proper profile (registry entry +
   ntuser.dat + default directories)
4. Wait 2 seconds for the profile to finalize
5. THEN create the app-specific directories inside the now-valid profile

**Flow after fix:**
1. `net user KioskUser "" /add` → user created, NO profile yet
2. `Start-Process cmd.exe /c exit -Credential KioskUser -LoadUserProfile`
   → Windows creates proper profile with ProfileList entry
3. `New-Item C:\Users\KioskUser\AppData\...` → custom dirs added to valid profile
4. User logs in → profile loads correctly, no error

## Impact
- First logon to KioskUser now works without the temporary profile error
- All app data, settings, and scheduled tasks work correctly
- Existing installations: user needs to either reinstall or manually delete
  `C:\Users\KioskUser` and re-run the installer

## Status: FIXED

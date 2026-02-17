# IMP-001: Single-Session Enforcement Missing in Auto-Login

## Problem
`AuthService.IsLoggedInAsync()` (auto-login via stored refresh token) did NOT check
whether the user was already logged in on another computer. Only `LoginAsync()` had
this guard.

**Scenario**: User logs in on PC-A, then PC-B auto-logs in from stored token. Both
PCs end up with active sessions for the same user -- budget gets double-charged,
session state is corrupted.

## Root Cause
`IsLoggedInAsync` (line 26) fetched user data from Firebase but skipped the
`isLoggedIn` + `currentComputerId` check that `LoginAsync` performs (lines 79-87).

## Fix
Added the same single-session guard to `IsLoggedInAsync`:
- Check `isLoggedIn == true` AND `currentComputerId != this PC's ID`
- If user is active on another PC: clear local tokens, return `false`
- User is shown the auth window and must log in manually

## Impact
- Prevents dual-session budget corruption
- User sees "please log in" instead of silently hijacking the session

## Status: FIXED

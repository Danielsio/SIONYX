# BUG-002: Users Not Shown as Active in Web Dashboard

**Status:** Fixed
**Severity:** Critical
**Component:** Kiosk (AuthService flow) + Firebase RTDB Rules
**Reported:** 2026-02-16
**Fixed:** 2026-02-17

---

## Summary

The web admin Users page shows 0 active users and 0 connected users, even when a user is logged into the kiosk with an active session (timer running).

## Symptoms

- Users page stats: "פעילים: 0" (Active: 0), "מושהים: 0" (Connected: 0)
- The Overview page partially works (uses different logic: `isSessionActive || currentComputerId`)
- User cards don't reflect logged-in/active status
- Floating timer shows an active session, but web doesn't reflect it

## Root Cause

**Cascading failure from BUG-001.** The login flow in `AuthService.HandleComputerRegistrationAsync`:

```csharp
var computerResult = await _computerService.RegisterComputerAsync();
if (!computerResult.IsSuccess) return; // ← EARLY RETURN
var assocResult = await _computerService.AssociateUserWithComputerAsync(userId, computerId, isLogin: true);
```

Because `RegisterComputerAsync()` fails (BUG-001: RTDB permission denied), the method returns early. `AssociateUserWithComputerAsync` is never called, which means:
- `isLoggedIn = true` is **never written** to the user record
- `currentComputerId` is **never written** to the user record

The web's `getUserStatus()` logic:
- **ACTIVE** = `isLoggedIn === true && isSessionActive === true`
- **CONNECTED** = `isLoggedIn === true && !isSessionActive`

Since `isLoggedIn` is never set to `true`, users always show as OFFLINE.

## Fix

### 1. Fix RTDB rules (see BUG-001)
Allows non-admin users to write to `computers/`, unblocking the registration flow.

### 2. Resilient login flow (AuthService.cs)
Made `HandleComputerRegistrationAsync` more resilient:
- Even if computer registration fails, still attempt user association
- Write `isLoggedIn = true` directly to the user if association also fails
- Ensures the user's login status is always reflected in Firebase

## Affected Files

- `database.rules.json` — RTDB rules (same fix as BUG-001)
- `sionyx-kiosk-wpf/src/SionyxKiosk/Services/AuthService.cs` — resilient login flow
- `sionyx-kiosk-wpf/src/SionyxKiosk/Services/ComputerService.cs` — writes missing fields

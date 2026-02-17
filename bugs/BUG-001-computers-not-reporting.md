# BUG-001: Computers Not Reported in Web Dashboard

**Status:** Fixed
**Severity:** Critical
**Component:** Kiosk (ComputerService) + Firebase RTDB Rules
**Reported:** 2026-02-16
**Fixed:** 2026-02-17

---

## Summary

The web admin dashboard shows 0 active computers and no computer status updates, even when kiosk users are actively logged in and using PCs.

## Symptoms

- Computers page shows "0 מחשבים פעילים" (0 active computers)
- Computer card shows "לא פעיל" (inactive) despite user being logged in
- `currentUserId` is never set on the computer record
- `isActive`, `lastSeen`, `lastUserLogin` fields are never written

## Root Cause

**Firebase RTDB rules** only allow admin users to write to the `computers/` path:

```json
"$computerId": {
  ".write": "auth != null && ...isAdmin.val() === true"
}
```

When a regular (non-admin) kiosk user logs in:
1. `RegisterComputerAsync()` attempts to write to `computers/{id}` → **PERMISSION_DENIED**
2. `HandleComputerRegistrationAsync` returns early on failure (line 234)
3. `AssociateUserWithComputerAsync` is **never called**
4. Computer `currentUserId` stays null
5. Computer `isActive` is never set

**Secondary issue:** Even if the write succeeded, the kiosk never wrote:
- `isActive` (boolean) — web stats use this field
- `lastSeen` (timestamp) — web uses for "last seen" display
- `lastUserLogin` (timestamp) — web uses for login time display

## Fix

### 1. RTDB Rules (database.rules.json)
Changed `computers/$computerId` write rule to allow any authenticated org member:
```json
".write": "auth != null && root.child('organizations').child($orgId).child('users').child(auth.uid).exists()"
```

### 2. ComputerService.cs
- `RegisterComputerAsync`: Now writes `isActive: false` and `lastSeen` on registration
- `AssociateUserWithComputerAsync`: Now writes `isActive: true`, `lastSeen`, `lastUserLogin`
- `DisassociateUserFromComputerAsync`: Now writes `isActive: false`, `lastSeen`

## Affected Files

- `database.rules.json` — RTDB rules
- `sionyx-kiosk-wpf/src/SionyxKiosk/Services/ComputerService.cs` — computer write logic

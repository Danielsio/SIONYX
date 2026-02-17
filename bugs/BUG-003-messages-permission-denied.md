# BUG-003: Messages PERMISSION_DENIED When Sending from Admin Dashboard

**Status:** Fixed
**Severity:** High
**Component:** Web (chatService.js) + Kiosk (ChatService.cs)
**Reported:** 2026-02-16
**Fixed:** 2026-02-17

---

## Summary

Admin cannot send messages to users from the web dashboard. The console shows:
```
PERMISSION_DENIED: Permission denied
```

## Symptoms

- Clicking send on a message in the admin dashboard throws a PERMISSION_DENIED error
- Error originates from Firebase RTDB `set()` call
- No messages are delivered to kiosk users
- Error trace: `index-CKih9ewY.js:26 [ERROR] Error sending message: Error: PERMISSION_DENIED`

## Root Cause

**Data type mismatch between code and RTDB validation rules.**

Firebase RTDB rules require:
```json
"timestamp": { ".validate": "newData.isNumber()" }
"readAt":    { ".validate": "newData.isNumber()" }
```

The web code sends **strings** instead of **numbers**:
```javascript
// chatService.js — sendMessage()
timestamp: new Date().toISOString(),  // ← STRING, rule expects NUMBER

// chatService.js — markMessageAsRead()
readAt: new Date().toISOString(),     // ← STRING, rule expects NUMBER
```

When a `.validate` rule fails, Firebase returns `PERMISSION_DENIED` (not a validation error), which is misleading.

The kiosk `ChatService.cs` has the same issue for `readAt`:
```csharp
await Firebase.DbSetAsync($"messages/{messageId}/readAt", DateTime.Now.ToString("o")); // STRING
```

## Fix

### 1. Web (chatService.js)
- `sendMessage()`: Changed `timestamp: new Date().toISOString()` → `timestamp: Date.now()`
- `markMessageAsRead()`: Changed `readAt: new Date().toISOString()` → `readAt: Date.now()`
- `updateUserLastSeen()`: Changed `lastSeen: new Date().toISOString()` → `lastSeen: Date.now()`
- Updated timestamp sorting to handle numeric timestamps

### 2. Kiosk (ChatService.cs)
- `MarkMessageAsReadAsync()`: Changed ISO string → `DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()`
- `UpdateLastSeenAsync()`: Changed ISO string → `DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()`

## Affected Files

- `sionyx-web/src/services/chatService.js` — timestamp format
- `sionyx-kiosk-wpf/src/SionyxKiosk/Services/ChatService.cs` — readAt/lastSeen format

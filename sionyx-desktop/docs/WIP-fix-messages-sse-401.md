# WIP: Fix Messages SSE 401 Unauthorized

## Bug Description
- **Log evidence**: Lines 52-53, 62-90, 145-147 in `sionyx_20260119.log`
- **Error**: `401 Client Error: Unauthorized` when reading `organizations/{orgId}/messages`
- **Impact**: Chat feature completely broken, SSE reconnects every 1-60 seconds

## Root Cause
Firebase security rules only allow per-message read access (`$messageId` level), but `ChatService` tries to read entire `messages` collection.

Current rule:
```json
"messages": {
  "$messageId": {
    ".read": "auth != null && (data.child('toUserId').val() == auth.uid || ...)"
  }
}
```

## Solution (Option A)
Add collection-level `.read` rule that allows authenticated users who exist in the organization to read messages.

## Steps

### Step 1: Update database.rules.json ✅
Add `.read` rule at `messages` level (not just `$messageId` level).

### Step 2: Deploy rules
```bash
make web-deploy-database
```

### Step 3: Test
- Login to desktop app
- Check logs for SSE connection success
- Verify chat messages load

## Changes Made
- `database.rules.json`: Added collection-level `.read` rule for messages

## Testing
- Manual testing: Login and verify no 401 errors in logs
- SSE should connect without constant reconnection

## Release
- Version bump: PATCH (bug fix)
- Tag: v1.10.1

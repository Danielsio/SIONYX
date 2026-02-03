# WIP: Fix Computer Registration 401 Unauthorized

## Bug Description
- **Log evidence**: Lines 38-40 in `sionyx_20260119.log`
- **Error**: `401 Client Error: Unauthorized` writing to `organizations/{orgId}/computers/{id}`
- **Impact**: Computer registration fails on login (warning only, login continues)

## Root Cause
Security rule checks `data.child('userId').val() == auth.uid` but if computer exists with different userId, the write fails.

Current rule:
```json
"$computerId": {
  ".write": "auth != null && (data.child('userId').val() == auth.uid || !data.exists() || isAdmin)"
}
```

This fails when:
1. Computer already exists (registered by another user)
2. Current user is not the owner
3. Current user is not admin

## Solution (Option A)
Allow any authenticated organization user to claim/update any computer. This is "last user wins" - whoever logs in last owns the computer.

## Steps

### Step 1: Update database.rules.json ✅
Simplify the `.write` rule to allow any authenticated org user to write.

### Step 2: Deploy rules
```bash
make web-deploy-database
```

### Step 3: Test
- Login to desktop app
- Check logs for successful computer registration
- Verify no 401 errors

## Changes Made
- `database.rules.json`: Simplified computers write rule

## Security Consideration
- Any user can now claim any computer
- This is acceptable for kiosk scenario (computers are shared)
- Admins can still see which user is on which computer

## Testing
- Manual testing: Login and verify no 401 errors in computer registration

## Release
- Version bump: PATCH (bug fix)
- Combined with other bug fixes

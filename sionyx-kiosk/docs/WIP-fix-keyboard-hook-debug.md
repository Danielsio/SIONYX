# WIP: Add Debug Logging to Keyboard Hook

## Bug Description
- **Log evidence**: Line 15 in `sionyx_20260119.log`
- **Error**: `"Failed to install keyboard hook: error 0"`
- **Impact**: Kiosk keyboard restrictions don't work (Alt+Tab, Win key still usable)

## Root Cause (Unknown)
"Error 0" means GetLastError() returned 0, which is unusual - it should return a specific error code.

Possible causes:
1. Another hook is already installed
2. Thread timing issue
3. Permission/elevation issue
4. Module handle issue

## Solution (Option D)
Add comprehensive debug logging to diagnose the root cause.

## Steps

### Step 1: Add debug logging to keyboard_restriction_service.py ✅
- Log GetModuleHandleW result
- Log thread state
- Clear last error before hook installation
- Log all hook callback activity

### Step 2: Add --debug flag to main.py ✅
- Make it easier to enable debug logging

### Step 3: User runs with --debug or -v flag
```bash
SIONYX.exe --debug
# or
SIONYX.exe -v
```

### Step 4: Analyze logs
- Look for patterns in hook failures
- Identify root cause

## Changes Made
- `keyboard_restriction_service.py`: Added extensive debug logging
- `main.py`: Added --debug alias for verbose logging

## Testing
- Unit tests for logging coverage
- Manual test: Run with --debug and check logs

## Release
- Version bump: PATCH
- Combined with other bug fixes

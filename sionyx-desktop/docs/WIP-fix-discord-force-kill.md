# WIP: Fix Discord Process Not Closable

## Bug Description
- **Log evidence**: Lines 95-96 in `sionyx_20260119.log`
- **Warning**: `"Failed to close 6 processes"` with `failed: ["Discord.exe"]`
- **Impact**: Discord stays open when new session starts (minor security issue)

## Root Cause
Discord has 6 processes (main + helper processes) and may resist termination:
1. Discord runs with elevated privileges
2. Multiple Discord processes (main + renderer + updater)
3. Discord may restart quickly after being killed

## Solution
1. Add retry logic with delays
2. Use `/T` flag to kill process tree (includes child processes)
3. Kill all instances in a single batch

## Steps

### Step 1: Update _kill_process with retry and tree kill ✅
- Add `/T` flag for tree kill
- Add retry logic with short delay
- Kill all PIDs of same process together

### Step 2: Test
- Start Discord with multiple windows
- Run process cleanup
- Verify all Discord processes closed

## Changes Made
- `process_cleanup_service.py`: Added retry logic and /T flag for stubborn processes

## Testing
- Unit tests for retry logic
- Manual test with Discord running

## Release
- Version bump: PATCH
- Combined with other bug fixes

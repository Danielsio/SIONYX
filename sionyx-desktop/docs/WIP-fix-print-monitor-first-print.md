# WIP: Fix Print Monitor - First Print No Reaction

## Bug Description
- **Log evidence**: User reports, documented in TODO.md
- **Issue 1**: First print has no reaction from the system
- **Issue 2**: Second print has reaction but no actual charge deducted
- **Impact**: Users can print without being charged

## Investigation

### Observed Behavior (from logs)
- Print monitor starts correctly with WMI events + polling fallback
- Found 2 printers: 'OneNote (Desktop)', 'Microsoft Print to PDF'
- WMI watcher initialized successfully
- No print job detection logs between start and session end

### Possible Causes

1. **Virtual Printers Complete Too Fast**
   - Virtual printers (PDF, OneNote) complete in milliseconds
   - WMI has `delay_secs=1` between checks
   - Polling is every 500ms
   - Job may complete BEFORE detection

2. **First Job Timing Gap**
   - When monitor starts, there's a gap between initialization and first poll
   - Jobs created in this window are ignored (added to known_jobs)

3. **Race Condition in `_initialize_known_jobs`**
   - Jobs created RIGHT after initialization but before first poll
   - Added to known_jobs and ignored

4. **Budget Deduction Path Issue**
   - `_deduct_budget` calls `db_update` on `users/{userId}`
   - But user data is at `organizations/{orgId}/users/{userId}`
   - Firebase client should handle org path, but verify

### Debug Changes

1. Add extensive DEBUG logging throughout print flow
2. Log every poll cycle with job IDs
3. Log WMI events immediately
4. Log budget get/update paths

## Steps

### Step 1: Add DEBUG logging ✅
- Log every poll with all job IDs
- Log WMI events immediately with timestamps
- Log budget operations with full paths

### Step 2: Reduce polling interval for testing
- Change from 500ms to 250ms for faster detection

### Step 3: Fix potential race condition
- Add small delay after initialization before first poll
- Or: Don't add jobs to known_jobs until after first successful poll

### Step 4: Test with real printer (not virtual)
- Virtual printers complete too fast for reliable testing

## Changes Made
- `print_monitor_service.py`: Added extensive debug logging

## Testing
- Manual test: Print to real printer with DEBUG logging
- Check logs for detection and budget deduction

## Release
- Version bump: PATCH (bug fix)
- Combined with other bug fixes

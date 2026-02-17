# IMP-003: EndSessionAsync Blocks UI During Browser Cleanup

## Problem
`SessionService.EndSessionAsync()` awaited browser cleanup (closing Chrome/Edge/Firefox
processes + deleting cookies). This took 2-5 seconds, during which the UI appeared frozen
and the "End Session" spinner kept spinning long after the session had already ended.

Additionally, fire-and-forget `EndSessionAsync` calls from countdown expiration and
operating hours enforcement silently swallowed exceptions.

## Root Cause
Browser cleanup (`CleanupWithBrowserClose`) was placed BEFORE `IsActive = false` and
`SessionEnded` event. The caller had to wait for the entire cleanup to complete.

Fire-and-forget calls used `_ = EndSessionAsync(reason)` without try/catch, so any
exception would be unobserved.

## Fix
**Non-blocking cleanup:**
- Moved `IsActive = false` and `SessionEnded` BEFORE browser cleanup
- Browser cleanup now runs as fire-and-forget with error logging
- The UI unblocks immediately after Firebase sync completes (~200ms vs ~3s)

**Safe fire-and-forget:**
- Added `SafeEndSessionAsync(reason)` wrapper with try/catch + logging
- Used in `OnCountdownTick` (time expired) and `OnHoursEnded` (operating hours)
- Exceptions are now logged instead of silently lost

## Impact
- "End Session" operation feels instant (UI returns in ~200ms)
- Browser cleanup still happens, just non-blocking
- Errors in automatic session termination are now logged for debugging

## Status: FIXED

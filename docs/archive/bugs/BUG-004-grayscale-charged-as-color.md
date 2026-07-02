# BUG-004: Grayscale Print Jobs Charged as Color

## Summary
Printing 5 pages in grayscale was charged 25 NIS (color rate) instead of the B&W rate.

## Root Cause
The `PrintMonitorService.ReadJobDetails()` method reads `DEVMODEW.dmColor` from the Windows print spooler to determine if a job is color or grayscale. However:

1. **Missing `dmFields` validation** -- The `dmFields` bitmask indicates which DEVMODE fields are actually populated by the printer driver. The code was reading `dmColor` without checking the `DM_COLOR` flag (0x800) in `dmFields`. When the flag isn't set, `dmColor` contains a garbage value or driver default.

2. **Driver default behavior** -- Many printer drivers for color-capable printers set `dmColor = 2` (DMCOLOR_COLOR) as a default regardless of the user's actual selection. When a user picks "Grayscale" in the print dialog, many drivers store that preference in the *private* DEVMODE data (driver-specific area after the standard struct), not in the standard `dmColor` field.

**Result**: The monitor read `dmColor == 2` (color) for a grayscale print job and applied the color price (5 NIS/page) instead of the B&W price.

## Fix
- Added `DM_COLOR` (0x800) and `DMCOLOR_MONOCHROME` (1) constants
- Now validates `dmFields & DM_COLOR` before reading `dmColor`
- If the `DM_COLOR` flag is NOT set in `dmFields`, defaults to B&W (the cheaper rate)
- Added comprehensive logging:
  - DEVMODE `dmColor` value and `dmFields` hex for debugging
  - Price per page used in cost calculation
  - Warning when pricing fails to load from DB

## Impact
- All print jobs on color-capable printers that use grayscale may have been overcharged
- Fix defaults to B&W when color detection is ambiguous (safer: undercharge vs overcharge)

## Status: FIXED

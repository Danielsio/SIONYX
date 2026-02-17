# IMP-004: Packages Page Shows Empty State During Loading

## Problem
The Packages page showed "אין חבילות זמינות" (No packages available) momentarily
during the loading phase, before packages were fetched from Firebase. The empty
state was bound to `Packages.Count == 0`, which is true when the page first loads.

Users could briefly see "no packages" flash before the actual list appeared.

## Root Cause
The `EmptyState` visibility was bound to `Packages.Count` via `ZeroToVis` converter,
which doesn't consider whether loading is still in progress.

## Fix
**ViewModel (`PackagesViewModel.cs`):**
- Added `ShowEmptyState` computed property: `!IsLoading && Packages.Count == 0`
- Raises `PropertyChanged` when either `IsLoading` or `Packages` changes

**View (`PackagesPage.xaml`):**
- Changed `EmptyState` binding from `Packages.Count, ZeroToVis` to `ShowEmptyState, BoolToVis`
- Empty state now only appears after loading completes with zero results

## Impact
- No more "no packages" flash during load
- Clean loading spinner → package list transition

## Status: FIXED

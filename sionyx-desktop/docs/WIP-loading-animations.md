# WIP: Loading Animations for API Operations

## Overview
Add loading spinner/animation when performing API operations (login, register, logout) to provide visual feedback to users.

## Current Version
- **v1.3.0** (before this feature)
- Target: **v1.4.0** (minor bump - new feature)

## Implementation Steps

### Step 1: Create Feature Branch ✅
```bash
git checkout -b feature/loading-animations
```

### Step 2: Create LoadingSpinner Component ✅
- File: `src/ui/components/loading_overlay.py`
- Features:
  - Animated spinning circle (SpinnerWidget with QPainter)
  - Semi-transparent overlay to block UI
  - Optional message text
  - Fade in/out animations

### Step 3: Integrate into AuthWindow ✅
- File: `src/ui/auth_window.py`
- Show spinner during:
  - `handle_sign_in()` - when calling `auth_service.login()`
  - `handle_sign_up()` - when calling `auth_service.register()`
- Block all inputs while loading

### Step 4: Test and Validate ✅
- 21 tests for loading overlay component
- Coverage improved from 89.09% to 89.2%

### Step 5: Merge Feature Branch ✅
```bash
make merge-feature
```

### Step 6: Release ⬜ (IN PROGRESS)
```bash
make release-minor
```
This will:
1. Create release/1.4.0 branch
2. Bump version to 1.4.0
3. Build installer
4. Merge to main
5. Create git tag v1.4.0
6. Push to remote

## Technical Details

### LoadingSpinner Component
```python
# Key PyQt6 features used:
- QPropertyAnimation for smooth rotation
- QGraphicsOpacityEffect for fade effects
- QPainter for custom drawing
- Overlay widget that covers parent
```

### Usage Pattern
```python
# Show loading
self.loading_spinner = LoadingOverlay(self.container)
self.loading_spinner.show_with_message("מתחבר...")

# After API call
self.loading_spinner.hide()
```

## Files Modified
1. `src/ui/components/loading_spinner.py` (NEW)
2. `src/ui/auth_window.py` (MODIFIED)
3. `TODO.md` (MODIFIED - added task)

## Rollback
If something goes wrong:
```bash
git checkout main
git branch -D feature/loading-animations
```

---
*Last updated: 2026-01-08*


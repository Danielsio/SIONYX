# WIP: Settings Page + Operating Hours Feature

## Overview
Add Settings page to sionyx-web with role-based access (admin/supervisor).
Add operating hours enforcement to sionyx-kiosk.

## Progress Tracker

### Phase 1: Web - Role Infrastructure
- [x] 1.1 Create RoleGuard component (`src/components/RoleGuard.jsx`)
- [x] 1.1b Create roles utility (`src/utils/roles.js`)
- [x] 1.2 Update authStore to handle role field
- [x] 1.3 Update authService to use role field (with isAdmin fallback)

### Phase 2: Web - Settings Page
- [x] 2.1 Create SettingsPage.jsx shell
- [x] 2.2 Create PricingSettings.jsx (move from PricingPage)
- [x] 2.3 Create OperatingHoursSettings.jsx (supervisor only)
- [x] 2.4 Create settingsService.js
- [x] 2.5 Update MainLayout.jsx sidebar (replace Pricing with Settings)
- [x] 2.6 Update App.jsx routes
- [x] 2.7 Delete PricingPage.jsx (after content moved)

### Phase 3: Web - Tests
- [x] 3.1 Create RoleGuard.test.jsx
- [x] 3.2 Create SettingsPage.test.jsx
- [x] 3.3 Create PricingSettings.test.jsx
- [x] 3.4 Create OperatingHoursSettings.test.jsx
- [x] 3.5 Create settingsService.test.js
- [x] 3.5b Create roles.test.js
- [x] 3.6 Update MainLayout.test.jsx
- [x] 3.7 Update App.test.jsx
- [x] 3.8 Refactor existing tests that use isAdmin

### Phase 4: Kiosk - Operating Hours Service
- [x] 4.1 Create operating_hours_service.py
- [x] 4.2 Create operating_hours_service_test.py
- [x] 4.3 Update organization_metadata_service.py to fetch settings

### Phase 5: Kiosk - UI Integration
- [x] 5.1 Update home_page.py - add start session check + popup
- [x] 5.2 Update session_service.py - periodic hours check
- [x] 5.3 Update home_page_test.py
- [x] 5.4 Update session_service_test.py

### Phase 6: Migration Script
- [x] 6.1 Create scripts/migrate_roles.py

### Phase 7: Documentation
- [x] 7.1 Update docs/app-design.md
- [x] 7.2 Update TODO.md

---

## Implementation Notes

### Role Field
- Old: `isAdmin: true/false`
- New: `role: "user" | "admin" | "supervisor"`
- Fallback: if `role` missing, check `isAdmin` for backwards compat

### Database Path
- Operating hours: `organizations/{orgId}/metadata/settings/operatingHours`
- Fields:
  - enabled: boolean
  - startTime: "HH:mm"
  - endTime: "HH:mm"
  - gracePeriodMinutes: number
  - graceBehavior: "graceful" | "force"

### Files Modified/Created
(Updated as work progresses)

---

## Current Status
**Started**: Yes
**Completed**: 2026-02-04
**Last Updated**: 2026-02-04
**Current Step**: ALL PHASES COMPLETE ✓

# WIP: Forgot Password - Admin Reset Flow

**Started**: 2026-01-16
**Completed**: 2026-01-16
**Status**: ✅ COMPLETE
**Released Version**: v1.7.0

## Overview

Implement a forgot password flow where users contact the organization admin to reset their password. This is needed because users have fake phone-to-email format (`0501234567@sionyx.app`) and can't use standard Firebase password reset.

## Problem

- Firebase Auth requires email for password reset
- Our users authenticate with phone numbers converted to fake emails
- Users don't have access to these fake email inboxes
- Standard "forgot password" email flow doesn't work

## Solution

Admin-assisted password reset:
1. User clicks "שכחת סיסמה?" → sees admin contact info
2. User contacts admin (phone/in-person)
3. Admin resets password via web dashboard
4. User logs in with new password

## Implementation Steps

### Phase 1: Desktop App Changes
- [x] Step 1.1: Update `forgot_password_clicked()` in `auth_window.py`
  - Show admin phone number fetched from organization metadata
  - Display message in Hebrew with contact instructions

- [ ] Step 1.2: Add method to fetch admin contact info
  - Use `OrganizationMetadataService` to get admin phone/email
  - Store admin contact in org metadata during registration

### Phase 2: Firebase Functions
- [ ] Step 2.1: Add `resetUserPassword` cloud function
  - Accepts: `orgId`, `userId`, `newPassword`
  - Validates caller is admin of the organization
  - Uses Firebase Admin SDK to update user password
  - Returns success/error

- [ ] Step 2.2: Update organization registration to store admin phone
  - Add `adminPhone` to metadata for display in desktop app

### Phase 3: Web Admin Dashboard
- [ ] Step 3.1: Add "איפוס סיסמה" button in UsersPage
  - Button in user details drawer under "פעולות מהירות"
  - Opens modal for entering new password

- [ ] Step 3.2: Create password reset modal
  - Input for new password (with confirmation)
  - Minimum 6 characters validation
  - Calls `resetUserPassword` function

### Phase 4: Testing
- [ ] Step 4.1: Add unit tests for desktop changes
- [ ] Step 4.2: Add tests for Firebase function
- [ ] Step 4.3: Add tests for web admin component

### Phase 5: Release
- [ ] Step 5.1: Run full test suite
- [ ] Step 5.2: Create release branch
- [ ] Step 5.3: Build and deploy
- [ ] Step 5.4: Tag and push v1.7.0

## Files Modified

### Desktop (sionyx-kiosk)
- `src/ui/auth_window.py` - Update forgot password click handler
- `src/services/organization_metadata_service.py` - Add admin contact method

### Firebase Functions
- `functions/index.js` - Add resetUserPassword function

### Web Admin (sionyx-web)
- `src/pages/UsersPage.jsx` - Add reset password button and modal
- `src/services/userService.js` - Add resetPassword service call

## Notes

- Admin phone stored in organization metadata during registration
- Desktop fetches admin contact on app startup or on-demand
- Password reset is a privileged operation - only org admins can do it
- New password must meet Firebase requirements (min 6 chars)

## Progress Log

### 2026-01-16
- Created WIP document
- Updated TODO.md with feature specification
- Created feature branch `feature/forgot-password-admin-reset`
- Added `resetUserPassword` Firebase Cloud Function
- Updated organization registration to store admin_phone and admin_email
- Added `resetUserPassword` service call in web admin
- Added "איפוס סיסמה" button in UsersPage (drawer and card dropdown)
- Added password reset modal in UsersPage
- Added `get_admin_contact()` method to OrganizationMetadataService
- Updated `forgot_password_clicked()` in auth_window.py to show admin contact
- Added tests for new functionality
- Ready for release!

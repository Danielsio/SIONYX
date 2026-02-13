# SIONYX Bug Report

> Generated: 2026-02-13 | Scanned: sionyx-web + sionyx-kiosk

---

## Critical

### BUG-001: ProtectedRoute redirects to non-existent `/login` -- FIXED
- **App:** Web
- **File:** `sionyx-web/src/components/ProtectedRoute.jsx:8`
- **Description:** When an unauthenticated user hits a protected route, they are redirected to `/login` which does not exist. The correct path is `/admin/login`.
- **Code:** `return <Navigate to='/login' replace />`
- **Fix:** Change to `<Navigate to='/admin/login' replace />`
- **Commit:** `9953a90`

### BUG-002: MessagesPage crashes if user is null -- FIXED
- **App:** Web
- **File:** `sionyx-web/src/pages/MessagesPage.jsx:76-77`
- **Description:** `loadData` accesses `user.orgId` without null-checking `user`. If auth state isn't ready when the page mounts, this throws.
- **Code:** `getAllUsers(user.orgId)`, `getAllMessages(user.orgId)`
- **Fix:** Add `if (!user?.orgId) return;` guard at top of `loadData`.
- **Commit:** `7182050`

---

## High

### BUG-003: useEffect missing `orgId` dependency on multiple pages -- FIXED
- **App:** Web
- **Files:**
  - `sionyx-web/src/pages/OverviewPage.jsx:60-62`
  - `sionyx-web/src/pages/UsersPage.jsx:117-119`
  - `sionyx-web/src/pages/PackagesPage.jsx:66-68`
  - `sionyx-web/src/components/settings/OperatingHoursSettings.jsx:42-44`
  - `sionyx-web/src/components/settings/PricingSettings.jsx:40-42`
- **Description:** These pages call data-loading functions that depend on `orgId`, but the `useEffect` has an empty `[]` dependency array. If `orgId` is null on first render (e.g. localStorage not yet read), data never loads.
- **Fix:** Added `orgId` to the dependency array. Existing guards prevent unnecessary calls.
- **Commit:** `d774ad4`
- **Note:** ComputersPage excluded -- it does not use orgId.

### BUG-004: UsersPage null user when sending message -- FIXED
- **App:** Web
- **File:** `sionyx-web/src/pages/UsersPage.jsx:356`
- **Description:** `sendMessage(orgId, selectedUser.uid, messageText, user.uid)` can crash if `user` is null.
- **Fix:** Added `if (!user?.uid)` guard before calling `sendMessage`.
- **Commit:** `35ebafd`

### BUG-005: LandingPage async state update after unmount -- FIXED
- **App:** Web
- **File:** `sionyx-web/src/pages/LandingPage.jsx:1339-1349`
- **Description:** `fetchReleaseInfo` is async with no cleanup. If the user navigates away before it resolves, `setReleaseInfo` fires on an unmounted component.
- **Fix:** Added `mounted` flag that is set to false in useEffect cleanup. Both success and error paths check the flag.
- **Commit:** `ed5872b`

### BUG-006: Inverted refresh logic in `refresh_all_pages`
- **App:** Kiosk
- **File:** `sionyx-kiosk/src/ui/main_window.py:363-369`
- **Description:** Pages are refreshed when `_should_skip_refresh` returns `True` (data is fresh) instead of `False` (data is stale). Logic is inverted.
- **Code:** `if force or self._should_skip_refresh(page_name):`
- **Fix:** Change to `if force or not self._should_skip_refresh(page_name):`

### BUG-007: Session sync failure silently ignored
- **App:** Kiosk
- **File:** `sionyx-kiosk/src/services/session_manager.py:76-106`
- **Description:** When `firebase.update_data()` returns `{"success": False}`, execution falls through without emitting `sync_failed` or raising an exception. The session appears synced but isn't.
- **Fix:** Add an `else` branch to handle the failure case (emit `sync_failed`, log error).

---

## Medium

### BUG-008: Double purchase completion handler
- **App:** Kiosk
- **File:** `sionyx-kiosk/src/ui/payment_dialog.py:360-372`
- **Description:** `on_purchase_completed` can be called twice (from both Firebase stream and polling) with no guard. Success UI can be shown more than once.
- **Fix:** Add a `self._purchase_handled = True` guard.

### BUG-009: SQLite connection leak on exception
- **App:** Kiosk
- **File:** `sionyx-kiosk/src/database/local_db.py:153-197`
- **Description:** DB connections opened with `sqlite3.connect()` are not closed if an exception occurs before `conn.close()`.
- **Fix:** Use `with sqlite3.connect(...) as conn:` or `try/finally`.

### BUG-010: GSAP animation scope mismatch -- FIXED
- **App:** Web
- **File:** `sionyx-web/src/pages/LandingPage.jsx:89-96`
- **Description:** `gsap.context` is scoped to `heroRef`, but `subtitleRef.current` may be outside that scope or null on first render.
- **Fix:** Added null check for `subtitleRef.current` before calling `gsap.fromTo`.
- **Commit:** `a6a8e97`

### BUG-011: Pricing validation allows undefined input -- FIXED
- **App:** Web
- **File:** `sionyx-web/src/services/pricingService.js:56`
- **Description:** `blackAndWhitePrice <= 0` evaluates to `false` when the value is `undefined`, bypassing validation.
- **Fix:** Added type checks for both prices before the numeric comparison.
- **Commit:** `a5542c0`

---

## Low

### BUG-012: Signal connection leak in AlertModal
- **App:** Kiosk
- **File:** `sionyx-kiosk/src/ui/components/alert_modal.py:296-301`
- **Description:** Each `close_modal()` call connects `finished` to `accept` without disconnecting previous connections. Rapid clicks accumulate connections.
- **Fix:** Disconnect before connecting, or use a flag.

### BUG-013: Silent exception in `_is_session_active`
- **App:** Kiosk
- **File:** `sionyx-kiosk/src/ui/pages/home_page.py:436-444`
- **Description:** Exceptions are swallowed with `pass` and no logging. Session state can be wrong without visibility.
- **Fix:** Add `logger.debug(f"Session check failed: {e}")` before `pass`.

### BUG-014: PricingSettings division by zero -- FIXED
- **App:** Web
- **File:** `sionyx-web/src/components/settings/PricingSettings.jsx:145`
- **Description:** If `blackAndWhitePrice` is 0, `colorPrice / blackAndWhitePrice` produces Infinity.
- **Fix:** Guard with `blackAndWhitePrice > 0` before dividing; shows 'N/A' when divisor is 0.
- **Commit:** `ec9db91`

---

## Summary

| Severity | Count | Fixed |
|----------|-------|-------|
| Critical | 2 | 2 |
| High | 5 | 4 |
| Medium | 4 | 2 |
| Low | 3 | 0 |
| **Total** | **14** | **8** |

### Fixed (Web) -- 8 commits
- BUG-001: ProtectedRoute wrong redirect path
- BUG-002: MessagesPage null user crash
- BUG-003: useEffect missing orgId dependency (5 pages)
- BUG-004: UsersPage null user on sendMessage
- BUG-005: LandingPage async unmount state update
- BUG-010: GSAP null ref in HeroSection
- BUG-011: pricingService undefined validation
- BUG-014: PricingSettings division by zero

### Remaining (Kiosk) -- 6 bugs
- BUG-006, BUG-007, BUG-008, BUG-009, BUG-012, BUG-013

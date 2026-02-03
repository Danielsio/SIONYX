# Integration Tests

## Overview

Integration tests to verify complete user flows through the application, testing multiple services working together.

## Current Status: ✅ Complete

### Test Files Created

| File | Status | Tests | Notes |
|------|--------|-------|-------|
| `src/tests/integration/__init__.py` | ✅ Done | - | Package init |
| `src/tests/integration/test_user_flows.py` | ✅ Done | 9 tests | Service integration tests |
| `src/tests/integration/test_ui_flows.py` | ✅ Done | 16 tests | UI integration tests |

### Test Results (Last Run: 2026-01-14)

```
============================= 25 passed in 0.99s ==============================

Service Integration Tests (test_user_flows.py): 9/9 PASSED
✅ test_complete_registration_flow
✅ test_complete_login_flow
✅ test_start_session_initializes_correctly
✅ test_session_countdown_decrements_time
✅ test_end_session_stops_timer_and_syncs
✅ test_cannot_start_session_with_zero_time
✅ test_cannot_start_duplicate_session
✅ test_logout_clears_session_and_computer
✅ test_complete_user_journey

UI Integration Tests (test_ui_flows.py): 16/16 PASSED
✅ test_auth_window_has_signin_panel
✅ test_login_form_has_required_fields
✅ test_can_fill_login_form
✅ test_has_signup_panel
✅ test_main_window_starts_on_home_page
✅ test_navigate_to_packages_page
✅ test_navigate_to_history_page
✅ test_navigate_to_help_page
✅ test_navigate_back_to_home
✅ test_start_session_creates_floating_timer
✅ test_return_from_session_closes_timer
✅ test_floating_timer_shows_time
✅ test_floating_timer_updates_usage_time
✅ test_floating_timer_updates_print_balance
✅ test_exit_button_emits_signal
✅ test_session_start_failure_shows_error
```

## Test Categories

### Service Integration Tests (`test_user_flows.py`)

Tests multiple services working together with mocked Firebase:

1. **Registration Flow** - User signup → Computer registration
2. **Login Flow** - Authentication → Computer association
3. **Session Flow** - Start session → Timer countdown → End session
4. **Logout Flow** - Disassociate user from computer
5. **Full User Journey** - Complete end-to-end flow

### UI Integration Tests (`test_ui_flows.py`)

Tests UI components with pytest-qt:

1. **AuthWindow Tests** - Login form, signup panel, input fields
2. **MainWindow Navigation** - Sidebar navigation between pages
3. **Session UI Flow** - Floating timer creation and closing
4. **FloatingTimer UI** - Time display, usage time, print balance, signals
5. **Error Handling** - Session start failure shows error dialog

## Key Fixes Applied

| Issue | Solution |
|-------|----------|
| Patch path for `get_app_icon_path` | Changed to `ui.base_window.get_app_icon_path` |
| Patch path for `ForceLogoutListener` | Changed to `ui.force_logout_listener.ForceLogoutListener` + patched `setup_force_logout_listener` method |
| AuthWindow attributes | Use `signin_panel`, `signin_email_input`, `signup_panel` |
| MainWindow navigation | Use `content_stack`, `nav_buttons[index]` |
| FloatingTimer attributes | Use `time_remaining_value`, `usage_time_value`, `exit_button` |
| Timing tests failing | Manually call `session_service._on_countdown_tick()` instead of waiting |

## Commands

```powershell
# Run only integration tests
pytest src/tests/integration/ -v

# Run with coverage
pytest src/tests/integration/ -v --cov=src --cov-report=term-missing

# Run specific test class
pytest src/tests/integration/test_user_flows.py::TestSessionFlow -v
```

## Future Enhancements

- [ ] Add package purchase flow tests
- [ ] Add print job tracking flow tests
- [ ] Add force logout scenario tests
- [ ] Add network error handling tests
- [ ] Add to CI pipeline

---
*Created: 2026-01-14*
*Completed: 2026-01-14*

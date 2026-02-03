"""
Integration Tests: UI Flows

Tests user interface interactions with pytest-qt:
1. Auth Window - Login/Registration forms
2. Main Window - Navigation and session management
3. Floating Timer - Session controls

These tests simulate real user interactions (clicks, typing) with mocked backend.
"""

from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLineEdit


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_auth_service():
    """Create mock AuthService for UI tests."""
    service = Mock()
    service.firebase = Mock()
    service.firebase.org_id = "test-org"
    service.is_logged_in.return_value = False
    service.get_current_user.return_value = {
        "uid": "ui-test-user",
        "email": "uitest@test.com",
        "firstName": "Test",
        "lastName": "User",
        "remainingTime": 3600,
        "printBalance": 50.0,
    }
    service.login.return_value = {"success": True, "user": service.get_current_user()}
    service.register.return_value = {"success": True}
    return service


@pytest.fixture
def mock_config():
    """Create mock Firebase config."""
    config = Mock()
    config.api_key = "test-api-key"
    config.database_url = "https://test.firebaseio.com"
    config.org_id = "test-org"
    return config


# =============================================================================
# Test: Auth Window UI Flows
# =============================================================================


class TestAuthWindowUIFlows:
    """
    UI integration tests for authentication window.
    
    Tests user interactions with login and registration forms.
    """

    @pytest.fixture
    def auth_window(self, qapp, mock_auth_service):
        """Create AuthWindow with mocked services."""
        # Patch get_app_icon_path in base_window where it's defined
        with patch("ui.base_window.get_app_icon_path", return_value=None):
            with patch.object(
                QApplication, "primaryScreen"
            ) as mock_screen:
                mock_geometry = Mock()
                mock_geometry.width.return_value = 1920
                mock_geometry.height.return_value = 1080
                mock_screen.return_value.geometry.return_value = mock_geometry

                from ui.auth_window import AuthWindow

                # Don't go fullscreen in tests
                with patch.object(AuthWindow, "setup_kiosk_window"):
                    window = AuthWindow(mock_auth_service)
                    yield window
                    window.close()

    def test_auth_window_has_signin_panel(self, auth_window):
        """Test auth window has login form panel."""
        # Verify signin_panel exists (visibility depends on show() being called)
        assert hasattr(auth_window, "signin_panel")
        assert auth_window.signin_panel is not None

    def test_login_form_has_required_fields(self, auth_window):
        """Test login form contains email and password fields."""
        # Check signin inputs exist
        assert hasattr(auth_window, "signin_email_input")
        assert hasattr(auth_window, "signin_password_input")
        
        # Find all line edits - should have at least phone and password
        email_inputs = auth_window.findChildren(QLineEdit)
        assert len(email_inputs) >= 2

    def test_can_fill_login_form(self, auth_window):
        """Test can enter text in login form fields."""
        # Fill in credentials
        auth_window.signin_email_input.setText("0501234567")
        auth_window.signin_password_input.setText("TestPassword123!")
        
        # Verify values were set
        assert auth_window.signin_email_input.text() == "0501234567"
        assert auth_window.signin_password_input.text() == "TestPassword123!"

    def test_has_signup_panel(self, auth_window):
        """Test auth window has signup panel for registration."""
        # Verify signup_panel exists and has required inputs
        assert hasattr(auth_window, "signup_panel")
        assert hasattr(auth_window, "signup_email_input")
        assert hasattr(auth_window, "signup_password_input")


# =============================================================================
# Test: Main Window Navigation
# =============================================================================


class TestMainWindowNavigation:
    """
    UI integration tests for main window navigation.
    
    Tests sidebar navigation between pages.
    """

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config):
        """Create MainWindow with mocked services."""
        mock_auth_service.is_logged_in.return_value = True
        
        with patch("ui.main_window.SessionService") as mock_session_cls:
            mock_session = Mock()
            mock_session.start_session.return_value = {"success": True}
            mock_session.end_session.return_value = {"success": True}
            mock_session.is_active = False
            # Create proper mock signals
            mock_session.time_updated = Mock()
            mock_session.time_updated.connect = Mock()
            mock_session.session_ended = Mock()
            mock_session.session_ended.connect = Mock()
            mock_session.warning_5min = Mock()
            mock_session.warning_5min.connect = Mock()
            mock_session.warning_1min = Mock()
            mock_session.warning_1min.connect = Mock()
            mock_session.sync_failed = Mock()
            mock_session.sync_failed.connect = Mock()
            mock_session.sync_restored = Mock()
            mock_session.sync_restored.connect = Mock()
            mock_session.print_monitor = Mock()
            mock_session.print_monitor.job_allowed = Mock()
            mock_session.print_monitor.job_allowed.connect = Mock()
            mock_session.print_monitor.job_blocked = Mock()
            mock_session.print_monitor.job_blocked.connect = Mock()
            mock_session.print_monitor.budget_updated = Mock()
            mock_session.print_monitor.budget_updated.connect = Mock()
            mock_session_cls.return_value = mock_session
            
            with patch("ui.force_logout_listener.ForceLogoutListener"):
                with patch("ui.base_window.get_app_icon_path", return_value=None):
                    with patch.object(
                        QApplication, "primaryScreen"
                    ) as mock_screen:
                        mock_geometry = Mock()
                        mock_geometry.width.return_value = 1920
                        mock_geometry.height.return_value = 1080
                        mock_screen.return_value.geometry.return_value = mock_geometry

                        from ui.main_window import MainWindow

                        with patch.object(MainWindow, "setup_kiosk_window"):
                            with patch.object(MainWindow, "setup_force_logout_listener"):
                                window = MainWindow(
                                    mock_auth_service, mock_config, kiosk_mode=False
                                )
                                yield window
                                window._allow_close = True
                                window.close()

    def test_main_window_starts_on_home_page(self, main_window):
        """Test main window shows home page initially."""
        # content_stack is the QStackedWidget containing pages
        assert main_window.content_stack.currentIndex() == 0

    def test_navigate_to_packages_page(self, main_window, qtbot):
        """Test clicking packages nav button shows packages page."""
        # nav_buttons[1] is packages (index 0=home, 1=packages, 2=history, 3=help)
        packages_btn = main_window.nav_buttons[1]
        
        qtbot.mouseClick(packages_btn, Qt.MouseButton.LeftButton)
        
        # Should show packages page (index 1)
        assert main_window.content_stack.currentIndex() == 1

    def test_navigate_to_history_page(self, main_window, qtbot):
        """Test clicking history nav button shows history page."""
        history_btn = main_window.nav_buttons[2]
        
        qtbot.mouseClick(history_btn, Qt.MouseButton.LeftButton)
        
        # Should show history page (index 2)
        assert main_window.content_stack.currentIndex() == 2

    def test_navigate_to_help_page(self, main_window, qtbot):
        """Test clicking help nav button shows help page."""
        help_btn = main_window.nav_buttons[3]
        
        qtbot.mouseClick(help_btn, Qt.MouseButton.LeftButton)
        
        # Should show help page (index 3)
        assert main_window.content_stack.currentIndex() == 3

    def test_navigate_back_to_home(self, main_window, qtbot):
        """Test can navigate back to home from other pages."""
        # First go to packages (index 1)
        qtbot.mouseClick(main_window.nav_buttons[1], Qt.MouseButton.LeftButton)
        assert main_window.content_stack.currentIndex() == 1
        
        # Then back to home (index 0)
        qtbot.mouseClick(main_window.nav_buttons[0], Qt.MouseButton.LeftButton)
        assert main_window.content_stack.currentIndex() == 0


# =============================================================================
# Test: Session Start/Return UI Flow
# =============================================================================


class TestSessionUIFlow:
    """
    UI integration tests for session management.
    
    Tests the flow of starting a session and returning from it.
    """

    @pytest.fixture
    def main_window_with_session(self, qapp, mock_auth_service, mock_config):
        """Create MainWindow configured for session testing."""
        mock_auth_service.is_logged_in.return_value = True
        mock_auth_service.get_current_user.return_value = {
            "uid": "session-test-user",
            "email": "session@test.com",
            "firstName": "Session",
            "lastName": "Tester",
            "remainingTime": 3600,
            "printBalance": 50.0,
        }
        
        with patch("ui.main_window.SessionService") as mock_session_cls:
            mock_session = Mock()
            mock_session.start_session.return_value = {"success": True}
            mock_session.end_session.return_value = {"success": True}
            mock_session.is_active = False
            # Create proper mock signals
            mock_session.time_updated = Mock()
            mock_session.time_updated.connect = Mock()
            mock_session.session_ended = Mock()
            mock_session.session_ended.connect = Mock()
            mock_session.warning_5min = Mock()
            mock_session.warning_5min.connect = Mock()
            mock_session.warning_1min = Mock()
            mock_session.warning_1min.connect = Mock()
            mock_session.sync_failed = Mock()
            mock_session.sync_failed.connect = Mock()
            mock_session.sync_restored = Mock()
            mock_session.sync_restored.connect = Mock()
            mock_session.print_monitor = Mock()
            mock_session.print_monitor.job_allowed = Mock()
            mock_session.print_monitor.job_allowed.connect = Mock()
            mock_session.print_monitor.job_blocked = Mock()
            mock_session.print_monitor.job_blocked.connect = Mock()
            mock_session.print_monitor.budget_updated = Mock()
            mock_session.print_monitor.budget_updated.connect = Mock()
            mock_session_cls.return_value = mock_session
            
            with patch("ui.force_logout_listener.ForceLogoutListener"):
                with patch("ui.base_window.get_app_icon_path", return_value=None):
                    with patch.object(
                        QApplication, "primaryScreen"
                    ) as mock_screen:
                        mock_geometry = Mock()
                        mock_geometry.width.return_value = 1920
                        mock_geometry.height.return_value = 1080
                        mock_screen.return_value.geometry.return_value = mock_geometry

                        from ui.main_window import MainWindow

                        with patch.object(MainWindow, "setup_kiosk_window"):
                            with patch.object(MainWindow, "setup_force_logout_listener"):
                                window = MainWindow(
                                    mock_auth_service, mock_config, kiosk_mode=False
                                )
                                yield window
                                window._allow_close = True
                                window.close()

    def test_start_session_creates_floating_timer(
        self, main_window_with_session, qtbot
    ):
        """Test starting session creates and shows floating timer."""
        with patch("ui.main_window.FloatingTimer") as mock_timer_cls:
            mock_timer = Mock()
            mock_timer_cls.return_value = mock_timer
            
            # Start session
            main_window_with_session.start_user_session(3600)
            
            # Verify floating timer was created and shown
            mock_timer_cls.assert_called_once()
            mock_timer.show.assert_called_once()
            assert main_window_with_session.floating_timer == mock_timer

    def test_return_from_session_closes_timer(
        self, main_window_with_session, qtbot
    ):
        """Test returning from session closes floating timer."""
        # Setup - create a mock timer
        mock_timer = Mock()
        main_window_with_session.floating_timer = mock_timer
        
        # Return from session
        main_window_with_session.return_from_session()
        
        # Timer should be closed
        mock_timer.close.assert_called_once()
        assert main_window_with_session.floating_timer is None


# =============================================================================
# Test: Floating Timer UI
# =============================================================================


class TestFloatingTimerUI:
    """
    UI integration tests for the floating timer.
    
    Tests timer display and controls during active session.
    """

    @pytest.fixture
    def floating_timer(self, qapp):
        """Create FloatingTimer instance."""
        # FloatingTimer doesn't use get_app_icon_path - it's a frameless widget
        from ui.floating_timer import FloatingTimer

        timer = FloatingTimer()
        yield timer
        timer.close()

    def test_floating_timer_shows_time(self, floating_timer):
        """Test floating timer displays time correctly."""
        # Update time
        floating_timer.update_time(3600)  # 1 hour
        
        # Check time is displayed (format: HH:MM:SS)
        time_text = floating_timer.time_remaining_value.text()
        # Should contain hour representation
        assert "01:00:00" in time_text

    def test_floating_timer_updates_usage_time(self, floating_timer):
        """Test floating timer shows usage time."""
        floating_timer.update_usage_time(300)  # 5 minutes
        
        # Usage time should be displayed
        usage_text = floating_timer.usage_time_value.text()
        assert "05:00" in usage_text or "00:05:00" in usage_text

    def test_floating_timer_updates_print_balance(self, floating_timer):
        """Test floating timer shows print balance."""
        floating_timer.update_print_balance(50.0)
        
        # Print balance should be displayed (format: "50.00₪")
        balance_text = floating_timer.print_balance_value.text()
        assert "50.00" in balance_text

    def test_exit_button_emits_signal(self, floating_timer):
        """Test clicking exit button emits return_clicked signal."""
        # Track if signal was emitted
        signal_received = []
        floating_timer.return_clicked.connect(lambda: signal_received.append(True))
        
        # Click exit button
        floating_timer.exit_button.click()
        
        # Verify signal was emitted
        assert len(signal_received) == 1


# =============================================================================
# Test: Error Handling UI
# =============================================================================


class TestErrorHandlingUI:
    """
    UI integration tests for error handling.
    
    Tests that errors are properly displayed to users.
    """

    @pytest.fixture
    def main_window_error(self, qapp, mock_auth_service, mock_config):
        """Create MainWindow configured for error testing."""
        mock_auth_service.is_logged_in.return_value = True
        
        with patch("ui.main_window.SessionService") as mock_session_cls:
            mock_session = Mock()
            # Session start will fail
            mock_session.start_session.return_value = {
                "success": False,
                "error": "Network error: Cannot connect to server"
            }
            mock_session.time_updated = Mock()
            mock_session.time_updated.connect = Mock()
            mock_session.session_ended = Mock()
            mock_session.session_ended.connect = Mock()
            mock_session.warning_5min = Mock()
            mock_session.warning_5min.connect = Mock()
            mock_session.warning_1min = Mock()
            mock_session.warning_1min.connect = Mock()
            mock_session.sync_failed = Mock()
            mock_session.sync_failed.connect = Mock()
            mock_session.sync_restored = Mock()
            mock_session.sync_restored.connect = Mock()
            mock_session.print_monitor = Mock()
            mock_session.print_monitor.job_allowed = Mock()
            mock_session.print_monitor.job_allowed.connect = Mock()
            mock_session.print_monitor.job_blocked = Mock()
            mock_session.print_monitor.job_blocked.connect = Mock()
            mock_session.print_monitor.budget_updated = Mock()
            mock_session.print_monitor.budget_updated.connect = Mock()
            mock_session_cls.return_value = mock_session
            
            with patch("ui.force_logout_listener.ForceLogoutListener"):
                with patch("ui.base_window.get_app_icon_path", return_value=None):
                    with patch.object(
                        QApplication, "primaryScreen"
                    ) as mock_screen:
                        mock_geometry = Mock()
                        mock_geometry.width.return_value = 1920
                        mock_geometry.height.return_value = 1080
                        mock_screen.return_value.geometry.return_value = mock_geometry

                        from ui.main_window import MainWindow

                        with patch.object(MainWindow, "setup_kiosk_window"):
                            with patch.object(MainWindow, "setup_force_logout_listener"):
                                window = MainWindow(
                                    mock_auth_service, mock_config, kiosk_mode=False
                                )
                                yield window
                                window._allow_close = True
                                window.close()

    def test_session_start_failure_shows_error(self, main_window_error, qtbot):
        """Test failed session start shows error message."""
        with patch("ui.main_window.QMessageBox") as mock_msgbox:
            main_window_error.start_user_session(3600)
            
            # Error dialog should be shown
            mock_msgbox.critical.assert_called_once()
            
            # Floating timer should not be created
            assert main_window_error.floating_timer is None

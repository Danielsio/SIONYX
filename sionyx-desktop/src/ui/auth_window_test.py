"""
Tests for auth_window.py - Authentication Window
Tests sign-in, sign-up forms, validation, and state transitions.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from PyQt6.QtCore import QRect, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def mock_auth_service():
    """Create mock auth service"""
    auth = Mock()
    auth.login.return_value = {"success": True}
    auth.register.return_value = {"success": True}
    return auth


@pytest.fixture
def auth_window(qapp, mock_auth_service):
    """Create AuthWindow instance for testing"""
    # Patch BaseKioskWindow to avoid fullscreen kiosk mode
    with patch(
        "ui.auth_window.BaseKioskWindow.__init__", lambda self: QWidget.__init__(self)
    ):
        with patch("ui.auth_window.BaseKioskWindow.create_main_layout") as mock_layout:
            mock_layout.return_value = QVBoxLayout()
            with patch(
                "ui.auth_window.BaseKioskWindow.apply_base_stylesheet", return_value=""
            ):
                from ui.auth_window import AuthWindow

                # Create window with minimal setup
                window = AuthWindow.__new__(AuthWindow)
                QWidget.__init__(window)
                window.auth_service = mock_auth_service
                window.is_sign_up_mode = False

                # Add mocked base class methods
                window.show_error = Mock()
                window.show_success = Mock()
                window.show_info = Mock()
                window.shake_widget = Mock()
                window.create_main_layout = Mock(return_value=QVBoxLayout())
                window.apply_base_stylesheet = Mock(return_value="")

                # Call init_ui to create the actual UI
                window.init_ui()

                yield window
                window.close()


# =============================================================================
# Initialization tests
# =============================================================================
class TestAuthWindowInit:
    """Tests for AuthWindow initialization"""

    def test_stores_auth_service(self, auth_window, mock_auth_service):
        """Test window stores auth service"""
        assert auth_window.auth_service == mock_auth_service

    def test_initial_mode_is_sign_in(self, auth_window):
        """Test initial mode is sign-in (not sign-up)"""
        assert auth_window.is_sign_up_mode is False

    def test_has_signin_panel(self, auth_window):
        """Test window has sign-in panel"""
        assert hasattr(auth_window, "signin_panel")
        assert isinstance(auth_window.signin_panel, QFrame)

    def test_has_signup_panel(self, auth_window):
        """Test window has sign-up panel"""
        assert hasattr(auth_window, "signup_panel")
        assert isinstance(auth_window.signup_panel, QFrame)

    def test_has_overlay_container(self, auth_window):
        """Test window has overlay container"""
        assert hasattr(auth_window, "overlay_container")

    def test_has_container(self, auth_window):
        """Test window has main container"""
        assert hasattr(auth_window, "container")
        assert auth_window.container.width() == 900
        assert auth_window.container.height() == 600

    def test_rtl_layout_direction(self, auth_window):
        """Test window uses RTL layout for Hebrew"""
        assert auth_window.layoutDirection() == Qt.LayoutDirection.RightToLeft


# =============================================================================
# Sign-in form tests
# =============================================================================
class TestSignInForm:
    """Tests for sign-in form elements"""

    def test_has_email_input(self, auth_window):
        """Test sign-in has email/phone input"""
        assert hasattr(auth_window, "signin_email_input")
        assert isinstance(auth_window.signin_email_input, QLineEdit)

    def test_has_password_input(self, auth_window):
        """Test sign-in has password input"""
        assert hasattr(auth_window, "signin_password_input")
        assert isinstance(auth_window.signin_password_input, QLineEdit)

    def test_password_input_is_password_mode(self, auth_window):
        """Test password input uses password echo mode"""
        assert (
            auth_window.signin_password_input.echoMode() == QLineEdit.EchoMode.Password
        )

    def test_has_signin_button(self, auth_window):
        """Test sign-in has submit button"""
        assert hasattr(auth_window, "signin_button")
        assert isinstance(auth_window.signin_button, QPushButton)

    def test_signin_panel_size(self, auth_window):
        """Test sign-in panel has correct size"""
        assert auth_window.signin_panel.width() == 450
        assert auth_window.signin_panel.height() == 600


# =============================================================================
# Sign-up form tests
# =============================================================================
class TestSignUpForm:
    """Tests for sign-up form elements"""

    def test_has_firstname_input(self, auth_window):
        """Test sign-up has first name input"""
        assert hasattr(auth_window, "signup_firstname_input")
        assert isinstance(auth_window.signup_firstname_input, QLineEdit)

    def test_has_lastname_input(self, auth_window):
        """Test sign-up has last name input"""
        assert hasattr(auth_window, "signup_lastname_input")
        assert isinstance(auth_window.signup_lastname_input, QLineEdit)

    def test_has_phone_input(self, auth_window):
        """Test sign-up has phone input"""
        assert hasattr(auth_window, "signup_phone_input")
        assert isinstance(auth_window.signup_phone_input, QLineEdit)

    def test_has_email_input(self, auth_window):
        """Test sign-up has email input"""
        assert hasattr(auth_window, "signup_email_input")
        assert isinstance(auth_window.signup_email_input, QLineEdit)

    def test_has_password_input(self, auth_window):
        """Test sign-up has password input"""
        assert hasattr(auth_window, "signup_password_input")
        assert isinstance(auth_window.signup_password_input, QLineEdit)

    def test_has_confirm_input(self, auth_window):
        """Test sign-up has confirm password input"""
        assert hasattr(auth_window, "signup_confirm_input")
        assert isinstance(auth_window.signup_confirm_input, QLineEdit)

    def test_has_signup_button(self, auth_window):
        """Test sign-up has submit button"""
        assert hasattr(auth_window, "signup_button")
        assert isinstance(auth_window.signup_button, QPushButton)

    def test_password_inputs_use_password_mode(self, auth_window):
        """Test password inputs use password echo mode"""
        assert (
            auth_window.signup_password_input.echoMode() == QLineEdit.EchoMode.Password
        )
        assert (
            auth_window.signup_confirm_input.echoMode() == QLineEdit.EchoMode.Password
        )


# =============================================================================
# Overlay panel tests
# =============================================================================
class TestOverlayPanel:
    """Tests for overlay panel elements"""

    def test_has_overlay(self, auth_window):
        """Test window has overlay widget"""
        assert hasattr(auth_window, "overlay")

    def test_has_overlay_left(self, auth_window):
        """Test window has left overlay panel"""
        assert hasattr(auth_window, "overlay_left")

    def test_has_overlay_right(self, auth_window):
        """Test window has right overlay panel"""
        assert hasattr(auth_window, "overlay_right")

    def test_has_left_button(self, auth_window):
        """Test window has left toggle button"""
        assert hasattr(auth_window, "left_button")
        assert isinstance(auth_window.left_button, QPushButton)

    def test_has_right_button(self, auth_window):
        """Test window has right toggle button"""
        assert hasattr(auth_window, "right_button")
        assert isinstance(auth_window.right_button, QPushButton)

    def test_overlay_size(self, auth_window):
        """Test overlay has correct size"""
        assert auth_window.overlay.width() == 900
        assert auth_window.overlay.height() == 600


# =============================================================================
# handle_sign_in tests
# =============================================================================
class TestHandleSignIn:
    """Tests for handle_sign_in method"""

    def test_empty_phone_shows_error(self, auth_window):
        """Test empty phone shows error"""
        auth_window.signin_email_input.setText("")
        auth_window.signin_password_input.setText("password123")

        auth_window.handle_sign_in()

        auth_window.show_error.assert_called()
        auth_window.shake_widget.assert_called()

    def test_empty_password_shows_error(self, auth_window):
        """Test empty password shows error"""
        auth_window.signin_email_input.setText("0501234567")
        auth_window.signin_password_input.setText("")

        auth_window.handle_sign_in()

        auth_window.show_error.assert_called()
        auth_window.shake_widget.assert_called()

    def test_valid_credentials_starts_login_thread(self, auth_window, mock_auth_service):
        """Test valid credentials starts login thread"""
        auth_window.signin_email_input.setText("0501234567")
        auth_window.signin_password_input.setText("password123")

        auth_window.handle_sign_in()

        # Thread should be created
        assert hasattr(auth_window, "_login_thread")
        assert hasattr(auth_window, "_login_worker")

    def test_successful_login_shows_success(self, auth_window, mock_auth_service):
        """Test successful login shows success message (via callback)"""
        # Directly test the callback
        auth_window._on_login_complete({"success": True})

        auth_window.show_success.assert_called()

    def test_failed_login_shows_error(self, auth_window, mock_auth_service):
        """Test failed login shows error message (via callback)"""
        # Directly test the callback
        auth_window._on_login_complete(
            {"success": False, "error": "Invalid credentials"}
        )

        auth_window.show_error.assert_called()
        auth_window.shake_widget.assert_called()

    def test_failed_login_clears_password(self, auth_window, mock_auth_service):
        """Test failed login clears password field (via callback)"""
        auth_window.signin_password_input.setText("wrongpassword")

        # Directly test the callback
        auth_window._on_login_complete({"success": False, "error": "Invalid"})

        assert auth_window.signin_password_input.text() == ""

    def test_button_disabled_during_login(self, auth_window, mock_auth_service):
        """Test button is disabled during login"""
        auth_window.signin_email_input.setText("0501234567")
        auth_window.signin_password_input.setText("password123")

        auth_window.handle_sign_in()

        # Button should be disabled when thread starts
        assert auth_window.signin_button.isEnabled() is False

        # After callback, button should be re-enabled
        auth_window._on_login_complete({"success": True})
        assert auth_window.signin_button.isEnabled() is True


# =============================================================================
# handle_sign_up tests
# =============================================================================
class TestHandleSignUp:
    """Tests for handle_sign_up method"""

    def test_empty_firstname_shows_error(self, auth_window):
        """Test empty first name shows error"""
        auth_window.signup_firstname_input.setText("")
        auth_window.signup_lastname_input.setText("Doe")
        auth_window.signup_phone_input.setText("0501234567")
        auth_window.signup_password_input.setText("password123")
        auth_window.signup_confirm_input.setText("password123")

        auth_window.handle_sign_up()

        auth_window.show_error.assert_called()

    def test_empty_lastname_shows_error(self, auth_window):
        """Test empty last name shows error"""
        auth_window.signup_firstname_input.setText("John")
        auth_window.signup_lastname_input.setText("")
        auth_window.signup_phone_input.setText("0501234567")
        auth_window.signup_password_input.setText("password123")
        auth_window.signup_confirm_input.setText("password123")

        auth_window.handle_sign_up()

        auth_window.show_error.assert_called()

    def test_empty_phone_shows_error(self, auth_window):
        """Test empty phone shows error"""
        auth_window.signup_firstname_input.setText("John")
        auth_window.signup_lastname_input.setText("Doe")
        auth_window.signup_phone_input.setText("")
        auth_window.signup_password_input.setText("password123")
        auth_window.signup_confirm_input.setText("password123")

        auth_window.handle_sign_up()

        auth_window.show_error.assert_called()

    def test_empty_password_shows_error(self, auth_window):
        """Test empty password shows error"""
        auth_window.signup_firstname_input.setText("John")
        auth_window.signup_lastname_input.setText("Doe")
        auth_window.signup_phone_input.setText("0501234567")
        auth_window.signup_password_input.setText("")
        auth_window.signup_confirm_input.setText("")

        auth_window.handle_sign_up()

        auth_window.show_error.assert_called()

    def test_short_password_shows_error(self, auth_window):
        """Test password < 6 chars shows error"""
        auth_window.signup_firstname_input.setText("John")
        auth_window.signup_lastname_input.setText("Doe")
        auth_window.signup_phone_input.setText("0501234567")
        auth_window.signup_password_input.setText("12345")  # Only 5 chars
        auth_window.signup_confirm_input.setText("12345")

        auth_window.handle_sign_up()

        auth_window.show_error.assert_called()

    def test_mismatched_passwords_shows_error(self, auth_window):
        """Test mismatched passwords shows error"""
        auth_window.signup_firstname_input.setText("John")
        auth_window.signup_lastname_input.setText("Doe")
        auth_window.signup_phone_input.setText("0501234567")
        auth_window.signup_password_input.setText("password123")
        auth_window.signup_confirm_input.setText("different456")

        auth_window.handle_sign_up()

        auth_window.show_error.assert_called()

    def test_mismatched_passwords_clears_confirm(self, auth_window):
        """Test mismatched passwords clears confirm field"""
        auth_window.signup_firstname_input.setText("John")
        auth_window.signup_lastname_input.setText("Doe")
        auth_window.signup_phone_input.setText("0501234567")
        auth_window.signup_password_input.setText("password123")
        auth_window.signup_confirm_input.setText("different456")

        auth_window.handle_sign_up()

        assert auth_window.signup_confirm_input.text() == ""

    def test_valid_data_starts_register_thread(self, auth_window, mock_auth_service):
        """Test valid data starts register thread"""
        auth_window.signup_firstname_input.setText("John")
        auth_window.signup_lastname_input.setText("Doe")
        auth_window.signup_phone_input.setText("0501234567")
        auth_window.signup_email_input.setText("john@example.com")
        auth_window.signup_password_input.setText("password123")
        auth_window.signup_confirm_input.setText("password123")

        auth_window.handle_sign_up()

        # Thread should be created
        assert hasattr(auth_window, "_register_thread")
        assert hasattr(auth_window, "_register_worker")

    def test_successful_register_shows_success(self, auth_window, mock_auth_service):
        """Test successful registration shows success message (via callback)"""
        # Directly test the callback
        auth_window._on_register_complete({"success": True})

        auth_window.show_success.assert_called()

    def test_failed_register_shows_error(self, auth_window, mock_auth_service):
        """Test failed registration shows error message (via callback)"""
        # Directly test the callback
        auth_window._on_register_complete({"success": False, "error": "Phone exists"})

        auth_window.show_error.assert_called()


# =============================================================================
# Mode toggle tests
# =============================================================================
class TestModeToggle:
    """Tests for mode toggling"""

    def test_toggle_to_sign_up_changes_mode(self, auth_window):
        """Test toggle_to_sign_up changes is_sign_up_mode"""
        assert auth_window.is_sign_up_mode is False

        auth_window.toggle_to_sign_up()

        assert auth_window.is_sign_up_mode is True

    def test_toggle_to_sign_up_shows_signup_panel(self, auth_window):
        """Test toggle_to_sign_up shows signup panel"""
        auth_window.toggle_to_sign_up()

        assert not auth_window.signup_panel.isHidden()

    def test_toggle_to_sign_up_when_already_signup_does_nothing(self, auth_window):
        """Test toggle_to_sign_up does nothing if already in sign-up mode"""
        auth_window.is_sign_up_mode = True
        initial_geometry = auth_window.signin_panel.geometry()

        auth_window.toggle_to_sign_up()

        # Geometry should not have changed
        assert auth_window.signin_panel.geometry() == initial_geometry

    def test_toggle_to_sign_in_changes_mode(self, auth_window):
        """Test toggle_to_sign_in changes is_sign_up_mode"""
        auth_window.is_sign_up_mode = True

        auth_window.toggle_to_sign_in()

        assert auth_window.is_sign_up_mode is False

    def test_toggle_to_sign_in_shows_signin_panel(self, auth_window):
        """Test toggle_to_sign_in shows signin panel"""
        auth_window.is_sign_up_mode = True

        auth_window.toggle_to_sign_in()

        assert not auth_window.signin_panel.isHidden()

    def test_toggle_to_sign_in_when_already_signin_does_nothing(self, auth_window):
        """Test toggle_to_sign_in does nothing if already in sign-in mode"""
        auth_window.is_sign_up_mode = False
        initial_geometry = auth_window.signup_panel.geometry()

        auth_window.toggle_to_sign_in()

        # Geometry should not have changed
        assert auth_window.signup_panel.geometry() == initial_geometry


# =============================================================================
# reset_positions tests
# =============================================================================
class TestResetPositions:
    """Tests for reset_positions method"""

    def test_signin_panel_at_origin(self, auth_window):
        """Test sign-in panel is at origin after reset"""
        auth_window.reset_positions()

        assert auth_window.signin_panel.x() == 0
        assert auth_window.signin_panel.y() == 0

    def test_signup_panel_hidden(self, auth_window):
        """Test sign-up panel is hidden after reset"""
        auth_window.reset_positions()

        assert auth_window.signup_panel.isHidden()

    def test_overlay_container_at_right(self, auth_window):
        """Test overlay container is at right side"""
        auth_window.reset_positions()

        assert auth_window.overlay_container.x() == 450


# =============================================================================
# forgot_password_clicked tests
# =============================================================================
class TestForgotPassword:
    """Tests for forgot password functionality"""

    def test_forgot_password_shows_info(self, auth_window):
        """Test forgot password shows info dialog"""
        auth_window.forgot_password_clicked()

        auth_window.show_info.assert_called_once()

    def test_forgot_password_shows_admin_contact_when_available(
        self, auth_window, mock_auth_service
    ):
        """Test forgot password shows admin contact info when available"""
        mock_auth_service.firebase = Mock()
        mock_auth_service.firebase.org_id = "test-org"

        with patch(
            "ui.auth_window.OrganizationMetadataService"
        ) as mock_metadata_service:
            mock_service_instance = Mock()
            mock_metadata_service.return_value = mock_service_instance
            mock_service_instance.get_admin_contact.return_value = {
                "success": True,
                "contact": {
                    "phone": "0501234567",
                    "email": "admin@test.com",
                    "org_name": "Test Organization",
                },
            }

            auth_window.forgot_password_clicked()

            auth_window.show_info.assert_called()
            call_args = auth_window.show_info.call_args
            # Check that admin contact is displayed
            assert "0501234567" in str(call_args) or "admin@test.com" in str(call_args)

    def test_forgot_password_fallback_when_no_admin_contact(
        self, auth_window, mock_auth_service
    ):
        """Test forgot password shows fallback when admin contact not found"""
        mock_auth_service.firebase = Mock()
        mock_auth_service.firebase.org_id = "test-org"

        with patch(
            "ui.auth_window.OrganizationMetadataService"
        ) as mock_metadata_service:
            mock_service_instance = Mock()
            mock_metadata_service.return_value = mock_service_instance
            mock_service_instance.get_admin_contact.return_value = {
                "success": False,
                "error": "Admin contact not found",
            }

            auth_window.forgot_password_clicked()

            auth_window.show_info.assert_called_once()

    def test_forgot_password_fallback_on_exception(
        self, auth_window, mock_auth_service
    ):
        """Test forgot password shows fallback on exception"""
        mock_auth_service.firebase = Mock()
        mock_auth_service.firebase.org_id = "test-org"

        with patch(
            "ui.auth_window.OrganizationMetadataService"
        ) as mock_metadata_service:
            mock_metadata_service.side_effect = Exception("Service error")

            auth_window.forgot_password_clicked()

            auth_window.show_info.assert_called_once()


# =============================================================================
# login_success signal tests
# =============================================================================
class TestLoginSuccessSignal:
    """Tests for login_success signal"""

    def test_successful_login_emits_signal(self, auth_window, mock_auth_service):
        """Test successful login emits login_success signal (via callback)"""
        # Track signal emission
        signal_received = []
        auth_window.login_success.connect(lambda: signal_received.append(True))

        # Directly test the callback
        auth_window._on_login_complete({"success": True})

        assert len(signal_received) == 1

    def test_successful_register_emits_signal(self, auth_window, mock_auth_service):
        """Test successful registration emits login_success signal (via callback)"""
        # Track signal emission
        signal_received = []
        auth_window.login_success.connect(lambda: signal_received.append(True))

        # Directly test the callback
        auth_window._on_register_complete({"success": True})

        assert len(signal_received) == 1


# =============================================================================
# Input field interaction tests
# =============================================================================
class TestInputFieldInteraction:
    """Tests for input field interactions"""

    def test_signin_password_enter_triggers_sign_in(
        self, auth_window, mock_auth_service
    ):
        """Test Enter key on password field triggers sign-in"""
        auth_window.signin_email_input.setText("0501234567")
        auth_window.signin_password_input.setText("password123")

        # Simulate return pressed
        auth_window.signin_password_input.returnPressed.emit()

        # Thread should be created
        assert hasattr(auth_window, "_login_thread")

    def test_signup_confirm_enter_triggers_sign_up(
        self, auth_window, mock_auth_service
    ):
        """Test Enter key on confirm field triggers sign-up"""
        auth_window.signup_firstname_input.setText("John")
        auth_window.signup_lastname_input.setText("Doe")
        auth_window.signup_phone_input.setText("0501234567")
        auth_window.signup_password_input.setText("password123")
        auth_window.signup_confirm_input.setText("password123")

        # Simulate return pressed
        auth_window.signup_confirm_input.returnPressed.emit()

        # Thread should be created
        assert hasattr(auth_window, "_register_thread")


# =============================================================================
# Edge case tests
# =============================================================================
class TestEdgeCases:
    """Tests for edge cases"""

    def test_whitespace_only_phone_is_invalid(self, auth_window):
        """Test whitespace-only phone is treated as empty"""
        auth_window.signin_email_input.setText("   ")
        auth_window.signin_password_input.setText("password123")

        auth_window.handle_sign_in()

        auth_window.show_error.assert_called()

    def test_whitespace_only_password_starts_thread(self, auth_window):
        """Test whitespace-only password passes validation (server validates)"""
        auth_window.signin_email_input.setText("0501234567")
        auth_window.signin_password_input.setText("   ")

        auth_window.handle_sign_in()

        # Thread should be created (password not stripped, so "   " is not empty)
        assert hasattr(auth_window, "_login_thread")

    def test_phone_is_stripped(self, auth_window, mock_auth_service):
        """Test phone whitespace is stripped"""
        auth_window.signin_email_input.setText("  0501234567  ")
        auth_window.signin_password_input.setText("password123")

        auth_window.handle_sign_in()

        # Thread should be created (phone gets stripped)
        assert hasattr(auth_window, "_login_thread")

    def test_email_is_optional_for_signup(self, auth_window, mock_auth_service):
        """Test email is optional for signup"""
        auth_window.signup_firstname_input.setText("John")
        auth_window.signup_lastname_input.setText("Doe")
        auth_window.signup_phone_input.setText("0501234567")
        auth_window.signup_email_input.setText("")  # Empty email
        auth_window.signup_password_input.setText("password123")
        auth_window.signup_confirm_input.setText("password123")

        auth_window.handle_sign_up()

        # Thread should be created (email is optional)
        assert hasattr(auth_window, "_register_thread")


# =============================================================================
# Widget attribute tests
# =============================================================================
class TestWidgetAttributes:
    """Tests for widget attributes"""

    def test_signin_button_has_cursor(self, auth_window):
        """Test sign-in button has pointing hand cursor"""
        assert (
            auth_window.signin_button.cursor().shape()
            == Qt.CursorShape.PointingHandCursor
        )

    def test_signup_button_has_cursor(self, auth_window):
        """Test sign-up button has pointing hand cursor"""
        assert (
            auth_window.signup_button.cursor().shape()
            == Qt.CursorShape.PointingHandCursor
        )

    def test_overlay_buttons_have_cursor(self, auth_window):
        """Test overlay buttons have pointing hand cursor"""
        assert (
            auth_window.left_button.cursor().shape()
            == Qt.CursorShape.PointingHandCursor
        )
        assert (
            auth_window.right_button.cursor().shape()
            == Qt.CursorShape.PointingHandCursor
        )

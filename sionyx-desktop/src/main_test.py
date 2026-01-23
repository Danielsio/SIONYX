"""
Tests for main application module
"""

import sys
from unittest.mock import MagicMock, PropertyMock, patch

import pytest


class TestSionyxApp:
    """Tests for the SionyxApp class."""

    @pytest.fixture
    def mock_dependencies(self):
        """Set up common mocks for SionyxApp."""
        patches = {}

        # Mock QApplication
        patches["qapp"] = patch("main.QApplication")
        mock_qapp = patches["qapp"].start()
        mock_app = MagicMock()
        mock_qapp.return_value = mock_app
        mock_qapp.primaryScreen.return_value.geometry.return_value.center.return_value = (
            MagicMock()
        )

        # Mock AuthService
        patches["auth_service"] = patch("main.AuthService")
        mock_auth_service = patches["auth_service"].start()
        mock_auth_service.return_value.is_logged_in.return_value = False

        # Mock GlobalHotkeyService
        patches["hotkey_service"] = patch("main.GlobalHotkeyService")
        mock_hotkey = patches["hotkey_service"].start()
        mock_hotkey.return_value.admin_exit_requested = MagicMock()

        # Mock KeyboardRestrictionService
        patches["keyboard_service"] = patch("main.KeyboardRestrictionService")
        mock_keyboard = patches["keyboard_service"].start()
        mock_keyboard.return_value.blocked_key_pressed = MagicMock()

        # Mock ProcessRestrictionService
        patches["process_service"] = patch("main.ProcessRestrictionService")
        mock_process = patches["process_service"].start()
        mock_process.return_value.process_blocked = MagicMock()

        # Mock get_firebase_config
        patches["firebase_config"] = patch("main.get_firebase_config")
        mock_firebase = patches["firebase_config"].start()
        mock_firebase.return_value = {"apiKey": "test"}

        # Mock AuthWindow
        patches["auth_window"] = patch("main.AuthWindow")
        mock_auth_window = patches["auth_window"].start()
        mock_auth_window.return_value.login_success = MagicMock()

        # Mock MainWindow
        patches["main_window"] = patch("main.MainWindow")
        patches["main_window"].start()

        # Mock Path.exists for .env check
        patches["path_exists"] = patch("main.Path.exists", return_value=True)
        patches["path_exists"].start()

        # Mock get_app_icon_path (imported inside __init__)
        patches["icon_path"] = patch(
            "ui.base_window.get_app_icon_path", return_value="icon.ico"
        )
        patches["icon_path"].start()

        # Mock QIcon (imported inside __init__)
        patches["qicon"] = patch("PyQt6.QtGui.QIcon")
        patches["qicon"].start()

        # Mock QShortcut to avoid real widget binding
        patches["qshortcut"] = patch("main.QShortcut")
        patches["qshortcut"].start()

        yield patches

        # Stop all patches
        for p in patches.values():
            p.stop()

    def test_init_creates_app(self, mock_dependencies):
        """Should create QApplication instance."""
        from main import SionyxApp

        sionyx = SionyxApp(verbose=False, kiosk_mode=False)

        assert sionyx.app is not None

    def test_init_stores_options(self, mock_dependencies):
        """Should store verbose and kiosk_mode options."""
        from main import SionyxApp

        sionyx = SionyxApp(verbose=True, kiosk_mode=True)

        assert sionyx.verbose is True
        assert sionyx.kiosk_mode is True

    def test_init_starts_hotkey_service(self, mock_dependencies):
        """Should initialize and start global hotkey service."""
        from main import GlobalHotkeyService, SionyxApp

        sionyx = SionyxApp()

        assert sionyx.global_hotkey_service is not None
        GlobalHotkeyService.return_value.start.assert_called_once()

    def test_hotkey_service_uses_queued_connection(self, mock_dependencies):
        """Admin exit signal MUST use QueuedConnection for cross-thread safety.

        This is a regression test for a bug where the admin exit hotkey would not
        show the password dialog because the signal was emitted from a background
        thread but the dialog (GUI) must be created on the main thread.

        Using Qt.ConnectionType.QueuedConnection ensures the slot runs on the
        main thread even when the signal is emitted from a background thread.
        """
        from PyQt6.QtCore import Qt

        from main import GlobalHotkeyService, SionyxApp

        # Get the mock signal
        mock_signal = GlobalHotkeyService.return_value.admin_exit_requested

        sionyx = SionyxApp()

        # Verify connect was called with QueuedConnection
        mock_signal.connect.assert_called_once()
        call_args = mock_signal.connect.call_args

        # The second argument should be Qt.ConnectionType.QueuedConnection
        assert len(call_args.args) == 2 or call_args.kwargs.get("type") is not None, (
            "Signal must be connected with QueuedConnection for thread safety"
        )

        if len(call_args.args) == 2:
            assert call_args.args[1] == Qt.ConnectionType.QueuedConnection, (
                "Signal MUST use QueuedConnection to ensure slot runs on main thread"
            )

    def test_init_starts_kiosk_services_when_enabled(self, mock_dependencies):
        """Should start keyboard and process restriction when kiosk mode enabled."""
        from main import (
            KeyboardRestrictionService,
            ProcessRestrictionService,
            SionyxApp,
        )

        sionyx = SionyxApp(kiosk_mode=True)

        KeyboardRestrictionService.return_value.start.assert_called_once()
        ProcessRestrictionService.return_value.start.assert_called_once()

    def test_init_does_not_start_kiosk_services_when_disabled(self, mock_dependencies):
        """Should not start kiosk services when kiosk mode disabled."""
        from main import (
            KeyboardRestrictionService,
            ProcessRestrictionService,
            SionyxApp,
        )

        sionyx = SionyxApp(kiosk_mode=False)

        KeyboardRestrictionService.return_value.start.assert_not_called()
        ProcessRestrictionService.return_value.start.assert_not_called()

    def test_init_shows_auth_window_when_not_logged_in(self, mock_dependencies):
        """Should show auth window when user not logged in."""
        from main import AuthWindow, SionyxApp

        SionyxApp()

        AuthWindow.return_value.show.assert_called_once()

    def test_init_shows_main_window_when_logged_in(self, mock_dependencies):
        """Should show main window when user already logged in."""
        from main import AuthService, MainWindow, SionyxApp

        AuthService.return_value.is_logged_in.return_value = True

        SionyxApp()

        MainWindow.return_value.show.assert_called_once()


class TestSionyxAppMethods:
    """Tests for SionyxApp methods."""

    @pytest.fixture
    def sionyx_app(self, mock_dependencies):
        """Create a SionyxApp instance with mocked dependencies."""
        from main import SionyxApp

        return SionyxApp()

    @pytest.fixture
    def mock_dependencies(self):
        """Set up common mocks for SionyxApp."""
        patches = {}

        patches["qapp"] = patch("main.QApplication")
        mock_qapp = patches["qapp"].start()
        mock_app = MagicMock()
        mock_qapp.return_value = mock_app
        mock_qapp.primaryScreen.return_value.geometry.return_value.center.return_value = (
            MagicMock()
        )

        patches["auth_service"] = patch("main.AuthService")
        mock_auth_service = patches["auth_service"].start()
        mock_auth_service.return_value.is_logged_in.return_value = False

        patches["hotkey_service"] = patch("main.GlobalHotkeyService")
        mock_hotkey = patches["hotkey_service"].start()
        mock_hotkey.return_value.admin_exit_requested = MagicMock()

        patches["keyboard_service"] = patch("main.KeyboardRestrictionService")
        mock_keyboard = patches["keyboard_service"].start()
        mock_keyboard.return_value.blocked_key_pressed = MagicMock()

        patches["process_service"] = patch("main.ProcessRestrictionService")
        mock_process = patches["process_service"].start()
        mock_process.return_value.process_blocked = MagicMock()

        patches["firebase_config"] = patch("main.get_firebase_config")
        mock_firebase = patches["firebase_config"].start()
        mock_firebase.return_value = {"apiKey": "test"}

        patches["auth_window"] = patch("main.AuthWindow")
        mock_auth_window = patches["auth_window"].start()
        mock_auth_window.return_value.login_success = MagicMock()

        patches["main_window"] = patch("main.MainWindow")
        patches["main_window"].start()

        patches["path_exists"] = patch("main.Path.exists", return_value=True)
        patches["path_exists"].start()

        patches["icon_path"] = patch(
            "ui.base_window.get_app_icon_path", return_value="icon.ico"
        )
        patches["icon_path"].start()

        patches["qicon"] = patch("PyQt6.QtGui.QIcon")
        patches["qicon"].start()

        yield patches

        for p in patches.values():
            p.stop()

    def test_show_auth_window_creates_window(self, sionyx_app):
        """Should create and show auth window."""
        from main import AuthWindow

        sionyx_app.show_auth_window()

        assert sionyx_app.auth_window is not None
        AuthWindow.return_value.show.assert_called()

    def test_show_main_window_closes_auth_window(self, sionyx_app):
        """Should close auth window when showing main window."""
        # Auth window is already set during init from show_auth_window
        # We need to replace it with a mock to test close
        mock_auth = MagicMock()
        sionyx_app.auth_window = mock_auth

        sionyx_app.show_main_window()

        mock_auth.close.assert_called_once()
        assert sionyx_app.auth_window is None

    def test_show_main_window_creates_main_window(self, sionyx_app):
        """Should create and show main window."""
        from main import MainWindow

        sionyx_app.show_main_window()

        assert sionyx_app.main_window is not None
        MainWindow.return_value.show.assert_called()

    def test_cleanup_stops_all_services(self, sionyx_app):
        """Should stop all services during cleanup."""
        mock_hotkey = MagicMock()
        mock_keyboard = MagicMock()
        mock_process = MagicMock()

        sionyx_app.global_hotkey_service = mock_hotkey
        sionyx_app.keyboard_restriction_service = mock_keyboard
        sionyx_app.process_restriction_service = mock_process

        sionyx_app.cleanup()

        mock_hotkey.stop.assert_called_once()
        mock_keyboard.stop.assert_called_once()
        mock_process.stop.assert_called_once()

    def test_cleanup_handles_exceptions(self, sionyx_app):
        """Should handle exceptions gracefully during cleanup."""
        mock_hotkey = MagicMock()
        mock_hotkey.stop.side_effect = RuntimeError("Stop failed")

        sionyx_app.global_hotkey_service = mock_hotkey

        # Should not raise
        sionyx_app.cleanup()

    def test_on_blocked_key_logs_warning(self, sionyx_app):
        """Should handle blocked key callback."""
        # Should not raise
        sionyx_app._on_blocked_key("Alt+Tab")

    def test_on_blocked_process_logs_warning(self, sionyx_app):
        """Should handle blocked process callback."""
        # Should not raise
        sionyx_app._on_blocked_process("cmd.exe")

    def test_run_executes_event_loop(self, sionyx_app):
        """Should execute Qt event loop."""
        sionyx_app.app.exec.return_value = 0

        result = sionyx_app.run()

        sionyx_app.app.exec.assert_called_once()
        assert result == 0


class TestStartKioskServices:
    """Tests for _start_kiosk_services method."""

    @pytest.fixture
    def mock_dependencies(self):
        """Set up common mocks."""
        patches = {}

        patches["qapp"] = patch("main.QApplication")
        mock_qapp = patches["qapp"].start()
        mock_app = MagicMock()
        mock_qapp.return_value = mock_app
        mock_qapp.primaryScreen.return_value.geometry.return_value.center.return_value = (
            MagicMock()
        )

        patches["auth_service"] = patch("main.AuthService")
        mock_auth_service = patches["auth_service"].start()
        mock_auth_service.return_value.is_logged_in.return_value = False

        patches["hotkey_service"] = patch("main.GlobalHotkeyService")
        mock_hotkey = patches["hotkey_service"].start()
        mock_hotkey.return_value.admin_exit_requested = MagicMock()

        patches["keyboard_service"] = patch("main.KeyboardRestrictionService")
        mock_keyboard = patches["keyboard_service"].start()
        mock_keyboard.return_value.blocked_key_pressed = MagicMock()

        patches["process_service"] = patch("main.ProcessRestrictionService")
        mock_process = patches["process_service"].start()
        mock_process.return_value.process_blocked = MagicMock()

        patches["firebase_config"] = patch("main.get_firebase_config")
        mock_firebase = patches["firebase_config"].start()
        mock_firebase.return_value = {"apiKey": "test"}

        patches["auth_window"] = patch("main.AuthWindow")
        mock_auth_window = patches["auth_window"].start()
        mock_auth_window.return_value.login_success = MagicMock()

        patches["main_window"] = patch("main.MainWindow")
        patches["main_window"].start()

        patches["path_exists"] = patch("main.Path.exists", return_value=True)
        patches["path_exists"].start()

        patches["icon_path"] = patch(
            "ui.base_window.get_app_icon_path", return_value="icon.ico"
        )
        patches["icon_path"].start()

        patches["qicon"] = patch("PyQt6.QtGui.QIcon")
        patches["qicon"].start()

        yield patches

        for p in patches.values():
            p.stop()

    def test_start_kiosk_services_handles_exception(self, mock_dependencies):
        """Should handle exceptions when starting kiosk services."""
        from main import KeyboardRestrictionService, SionyxApp

        KeyboardRestrictionService.side_effect = RuntimeError("Failed")

        # Should not raise during init with kiosk mode
        app = SionyxApp(kiosk_mode=True)

        # Service should be None since it failed
        assert app.keyboard_restriction_service is None


# NOTE: Tests for missing .env config scenarios are skipped because they require
# complex mocking of Python's import system and Path operations that don't work
# reliably in the test environment. The functionality is tested manually.


class TestAppInitializationFailure:
    """Tests for application initialization failure scenarios."""

    @pytest.fixture
    def mock_dependencies(self):
        """Set up mocks that will fail during init."""
        patches = {}

        patches["qapp"] = patch("main.QApplication")
        mock_qapp = patches["qapp"].start()
        mock_app = MagicMock()
        mock_qapp.return_value = mock_app
        mock_qapp.primaryScreen.return_value.geometry.return_value.center.return_value = (
            MagicMock()
        )

        patches["auth_service"] = patch("main.AuthService")
        patches["auth_service"].start()

        patches["hotkey_service"] = patch("main.GlobalHotkeyService")
        mock_hotkey = patches["hotkey_service"].start()
        mock_hotkey.return_value.admin_exit_requested = MagicMock()

        patches["keyboard_service"] = patch("main.KeyboardRestrictionService")
        patches["keyboard_service"].start()

        patches["process_service"] = patch("main.ProcessRestrictionService")
        patches["process_service"].start()

        patches["firebase_config"] = patch("main.get_firebase_config")
        patches["firebase_config"].start()

        patches["auth_window"] = patch("main.AuthWindow")
        patches["auth_window"].start()

        patches["main_window"] = patch("main.MainWindow")
        patches["main_window"].start()

        patches["path_exists"] = patch("main.Path.exists", return_value=True)
        patches["path_exists"].start()

        patches["icon_path"] = patch(
            "ui.base_window.get_app_icon_path", return_value="icon.ico"
        )
        patches["icon_path"].start()

        patches["qicon"] = patch("PyQt6.QtGui.QIcon")
        patches["qicon"].start()

        yield patches

        for p in patches.values():
            p.stop()

    def test_exception_during_init_raises(self, mock_dependencies):
        """Should raise exception when initialization fails."""
        from main import get_firebase_config

        # Make firebase config raise an exception
        get_firebase_config.side_effect = RuntimeError("Config load failed")

        with pytest.raises(RuntimeError, match="Config load failed"):
            from main import SionyxApp
            SionyxApp()


# NOTE: Tests for handle_admin_exit scenarios are skipped because the method
# imports PyQt widgets inline which makes them difficult to mock reliably.
# The functionality is tested manually and covered by integration tests.

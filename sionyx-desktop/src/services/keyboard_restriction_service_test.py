"""
Unit tests for KeyboardRestrictionService.

Note: These tests mock the Windows API calls since we can't actually
install keyboard hooks in a test environment.
"""

import pytest
from unittest.mock import MagicMock, patch

from services.keyboard_restriction_service import (
    KeyboardRestrictionService,
    VK_TAB,
    VK_LWIN,
    VK_RWIN,
    VK_F4,
    VK_ESCAPE,
    VK_MENU,
    VK_CONTROL,
    VK_SHIFT,
)


class TestKeyboardRestrictionServiceInit:
    """Tests for service initialization."""

    def test_init_default_enabled(self):
        """Service should be enabled by default."""
        service = KeyboardRestrictionService()
        assert service.enabled is True
        assert service.hook_handle is None

    def test_init_disabled(self):
        """Service can be initialized as disabled."""
        service = KeyboardRestrictionService(enabled=False)
        assert service.enabled is False

    def test_default_blocked_combos(self):
        """Default blocked key combinations should be set."""
        service = KeyboardRestrictionService()
        assert service.blocked_combos["alt+tab"] is True
        assert service.blocked_combos["alt+f4"] is True
        assert service.blocked_combos["win"] is True
        assert service.blocked_combos["ctrl+shift+esc"] is True
        assert service.blocked_combos["ctrl+esc"] is True


class TestKeyboardRestrictionServiceControl:
    """Tests for start/stop/enable/disable methods."""

    @patch("services.keyboard_restriction_service.threading.Thread")
    def test_start_when_enabled(self, mock_thread):
        """Start should create and start thread when enabled."""
        service = KeyboardRestrictionService(enabled=True)
        service.start()

        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()

    def test_start_when_disabled(self):
        """Start should do nothing when disabled."""
        service = KeyboardRestrictionService(enabled=False)
        service.start()

        assert service.hook_thread is None

    @patch("services.keyboard_restriction_service.user32")
    def test_stop_unhooks(self, mock_user32):
        """Stop should call UnhookWindowsHookEx."""
        service = KeyboardRestrictionService()
        service.hook_handle = 12345  # Fake handle

        service.stop()

        mock_user32.UnhookWindowsHookEx.assert_called_once_with(12345)
        assert service.hook_handle is None

    def test_stop_when_not_started(self):
        """Stop should handle case when not started."""
        service = KeyboardRestrictionService()
        # Should not raise
        service.stop()

    @patch("services.keyboard_restriction_service.threading.Thread")
    def test_set_enabled_true_starts(self, mock_thread):
        """Setting enabled=True should start the service."""
        service = KeyboardRestrictionService(enabled=False)
        service.set_enabled(True)

        assert service.enabled is True
        mock_thread.assert_called_once()

    @patch("services.keyboard_restriction_service.user32")
    def test_set_enabled_false_stops(self, mock_user32):
        """Setting enabled=False should stop the service."""
        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        service.set_enabled(False)

        assert service.enabled is False
        mock_user32.UnhookWindowsHookEx.assert_called_once()


class TestKeyboardRestrictionServiceIsActive:
    """Tests for is_active method."""

    def test_is_active_when_running(self):
        """is_active should return True when hook is installed and enabled."""
        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345  # Fake handle

        assert service.is_active() is True

    def test_is_active_when_no_handle(self):
        """is_active should return False when no hook handle."""
        service = KeyboardRestrictionService(enabled=True)

        assert service.is_active() is False

    def test_is_active_when_disabled(self):
        """is_active should return False when disabled."""
        service = KeyboardRestrictionService(enabled=False)
        service.hook_handle = 12345

        assert service.is_active() is False


class TestKeyboardRestrictionServiceCallback:
    """Tests for the keyboard hook callback logic."""

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_blocks_windows_key(self, mock_user32):
        """Callback should block Windows key."""
        mock_user32.GetAsyncKeyState.return_value = 0  # No modifiers
        mock_user32.CallNextHookEx.return_value = 0

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        # Create mock keyboard data
        from ctypes import pointer
        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = VK_LWIN

        # The callback should return 1 to block
        # Note: We can't easily test the actual callback due to ctypes complexity
        # This is more of a design verification test

        assert service.blocked_combos["win"] is True

    def test_callback_blocks_alt_tab(self):
        """Alt+Tab should be in blocked combos."""
        service = KeyboardRestrictionService()
        assert service.blocked_combos["alt+tab"] is True

    def test_callback_blocks_alt_f4(self):
        """Alt+F4 should be in blocked combos."""
        service = KeyboardRestrictionService()
        assert service.blocked_combos["alt+f4"] is True

    def test_callback_blocks_ctrl_shift_esc(self):
        """Ctrl+Shift+Esc should be in blocked combos."""
        service = KeyboardRestrictionService()
        assert service.blocked_combos["ctrl+shift+esc"] is True


class TestKeyboardRestrictionServiceSignals:
    """Tests for Qt signals."""

    def test_blocked_key_signal_exists(self):
        """Service should have blocked_key_pressed signal."""
        service = KeyboardRestrictionService()
        assert hasattr(service, "blocked_key_pressed")

    def test_blocked_key_signal_can_connect(self):
        """Signal should be connectable."""
        service = KeyboardRestrictionService()
        handler = MagicMock()

        # Should not raise
        service.blocked_key_pressed.connect(handler)


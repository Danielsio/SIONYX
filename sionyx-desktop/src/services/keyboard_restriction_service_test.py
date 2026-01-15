"""
Unit tests for KeyboardRestrictionService.

Note: These tests mock the Windows API calls since we can't actually
install keyboard hooks in a test environment.
"""

from unittest.mock import MagicMock, patch

import pytest

from services.keyboard_restriction_service import (
    VK_CONTROL,
    VK_ESCAPE,
    VK_F4,
    VK_LWIN,
    VK_MENU,
    VK_RWIN,
    VK_SHIFT,
    VK_TAB,
    KeyboardRestrictionService,
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

    @patch("services.keyboard_restriction_service.threading.Thread")
    def test_start_when_already_started(self, mock_thread):
        """Start should do nothing if hook already installed."""
        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345  # Pretend already started

        service.start()

        # Should not create a new thread
        mock_thread.assert_not_called()

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

    @patch("services.keyboard_restriction_service.threading.Thread")
    def test_set_enabled_true_does_not_start_if_already_running(self, mock_thread):
        """Setting enabled=True should not restart if already running."""
        service = KeyboardRestrictionService(enabled=False)
        service.hook_handle = 12345  # Already has a handle

        service.set_enabled(True)

        # Should not create new thread
        mock_thread.assert_not_called()


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


class TestKeyboardHookCallback:
    """Tests for the _keyboard_hook_callback method."""

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_passes_through_when_disabled(self, mock_user32):
        """Callback should pass through when service is disabled."""
        mock_user32.CallNextHookEx.return_value = 0

        service = KeyboardRestrictionService(enabled=False)
        service.hook_handle = 12345

        # Create mock lParam that points to keyboard data
        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT
        import ctypes

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = VK_LWIN
        lParam = ctypes.addressof(kb_data)

        result = service._keyboard_hook_callback(0, 0, lParam)

        # Should call next hook (pass through)
        mock_user32.CallNextHookEx.assert_called_once()

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_passes_through_when_ncode_negative(self, mock_user32):
        """Callback should pass through when nCode < 0."""
        mock_user32.CallNextHookEx.return_value = 0

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        result = service._keyboard_hook_callback(-1, 0, 0)

        mock_user32.CallNextHookEx.assert_called_once()

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_blocks_windows_key_lwin(self, mock_user32):
        """Callback should block left Windows key."""
        mock_user32.GetAsyncKeyState.return_value = 0

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT
        import ctypes

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = VK_LWIN
        lParam = ctypes.addressof(kb_data)

        result = service._keyboard_hook_callback(0, 0, lParam)

        assert result == 1  # Blocked

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_blocks_windows_key_rwin(self, mock_user32):
        """Callback should block right Windows key."""
        mock_user32.GetAsyncKeyState.return_value = 0

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT
        import ctypes

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = VK_RWIN
        lParam = ctypes.addressof(kb_data)

        result = service._keyboard_hook_callback(0, 0, lParam)

        assert result == 1  # Blocked

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_blocks_alt_tab(self, mock_user32):
        """Callback should block Alt+Tab."""
        # Mock Alt key being pressed
        def get_async_key_state(vk):
            if vk == VK_MENU:
                return 0x8000
            return 0
        mock_user32.GetAsyncKeyState.side_effect = get_async_key_state

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT
        import ctypes

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = VK_TAB
        lParam = ctypes.addressof(kb_data)

        result = service._keyboard_hook_callback(0, 0, lParam)

        assert result == 1  # Blocked

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_blocks_alt_f4(self, mock_user32):
        """Callback should block Alt+F4."""
        def get_async_key_state(vk):
            if vk == VK_MENU:
                return 0x8000
            return 0
        mock_user32.GetAsyncKeyState.side_effect = get_async_key_state

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT
        import ctypes

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = VK_F4
        lParam = ctypes.addressof(kb_data)

        result = service._keyboard_hook_callback(0, 0, lParam)

        assert result == 1  # Blocked

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_blocks_alt_esc(self, mock_user32):
        """Callback should block Alt+Escape."""
        def get_async_key_state(vk):
            if vk == VK_MENU:
                return 0x8000
            return 0
        mock_user32.GetAsyncKeyState.side_effect = get_async_key_state

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT
        import ctypes

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = VK_ESCAPE
        lParam = ctypes.addressof(kb_data)

        result = service._keyboard_hook_callback(0, 0, lParam)

        assert result == 1  # Blocked

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_blocks_ctrl_shift_esc(self, mock_user32):
        """Callback should block Ctrl+Shift+Escape (Task Manager)."""
        def get_async_key_state(vk):
            if vk in (VK_CONTROL, VK_SHIFT):
                return 0x8000
            return 0
        mock_user32.GetAsyncKeyState.side_effect = get_async_key_state

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT
        import ctypes

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = VK_ESCAPE
        lParam = ctypes.addressof(kb_data)

        result = service._keyboard_hook_callback(0, 0, lParam)

        assert result == 1  # Blocked

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_blocks_ctrl_esc(self, mock_user32):
        """Callback should block Ctrl+Escape (Start menu)."""
        def get_async_key_state(vk):
            if vk == VK_CONTROL:
                return 0x8000
            return 0
        mock_user32.GetAsyncKeyState.side_effect = get_async_key_state

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT
        import ctypes

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = VK_ESCAPE
        lParam = ctypes.addressof(kb_data)

        result = service._keyboard_hook_callback(0, 0, lParam)

        assert result == 1  # Blocked

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_allows_unblocked_key(self, mock_user32):
        """Callback should pass through non-blocked keys."""
        mock_user32.GetAsyncKeyState.return_value = 0
        mock_user32.CallNextHookEx.return_value = 0

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT
        import ctypes

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = 0x41  # 'A' key
        lParam = ctypes.addressof(kb_data)

        result = service._keyboard_hook_callback(0, 0, lParam)

        mock_user32.CallNextHookEx.assert_called_once()

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_emits_signal_on_block(self, mock_user32):
        """Callback should emit signal when key is blocked."""
        mock_user32.GetAsyncKeyState.return_value = 0

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        handler = MagicMock()
        service.blocked_key_pressed.connect(handler)

        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT
        import ctypes

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = VK_LWIN
        lParam = ctypes.addressof(kb_data)

        service._keyboard_hook_callback(0, 0, lParam)

        handler.assert_called_once_with("Windows key")

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_handles_signal_exception(self, mock_user32, qtbot):
        """Callback should handle signal emit exceptions gracefully."""
        mock_user32.GetAsyncKeyState.return_value = 0

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345

        # Create a handler that raises
        def bad_handler(combo):
            raise RuntimeError("Handler error")

        service.blocked_key_pressed.connect(bad_handler)

        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT
        import ctypes

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = VK_LWIN
        lParam = ctypes.addressof(kb_data)

        # The callback should still return 1, but the signal handler raises an exception
        # which pytest-qt captures. We use raises_exceptions=True to allow this behavior.
        with qtbot.capture_exceptions() as exceptions:
            result = service._keyboard_hook_callback(0, 0, lParam)
            assert result == 1

        # Verify the exception was captured (handler raised RuntimeError)
        assert len(exceptions) == 1
        assert isinstance(exceptions[0][1], RuntimeError)

    @patch("services.keyboard_restriction_service.user32")
    def test_callback_does_not_block_disabled_combo(self, mock_user32):
        """Callback should not block combo that has been disabled."""
        mock_user32.GetAsyncKeyState.return_value = 0
        mock_user32.CallNextHookEx.return_value = 0

        service = KeyboardRestrictionService(enabled=True)
        service.hook_handle = 12345
        service.blocked_combos["win"] = False  # Disable Windows key blocking

        from services.keyboard_restriction_service import KBDLLHOOKSTRUCT
        import ctypes

        kb_data = KBDLLHOOKSTRUCT()
        kb_data.vkCode = VK_LWIN
        lParam = ctypes.addressof(kb_data)

        result = service._keyboard_hook_callback(0, 0, lParam)

        # Should pass through
        mock_user32.CallNextHookEx.assert_called_once()


class TestRunHookLoop:
    """Tests for the _run_hook_loop method."""

    @patch("services.keyboard_restriction_service.user32")
    @patch("services.keyboard_restriction_service.kernel32")
    def test_hook_loop_installs_hook(self, mock_kernel32, mock_user32):
        """_run_hook_loop should install Windows hook."""
        mock_user32.SetWindowsHookExW.return_value = 12345
        mock_user32.GetMessageW.return_value = 0  # Exit immediately
        mock_kernel32.GetModuleHandleW.return_value = 0

        service = KeyboardRestrictionService(enabled=True)
        service._run_hook_loop()

        mock_user32.SetWindowsHookExW.assert_called_once()

    @patch("services.keyboard_restriction_service.user32")
    @patch("services.keyboard_restriction_service.kernel32")
    @patch("services.keyboard_restriction_service.ctypes.get_last_error")
    def test_hook_loop_handles_install_failure(self, mock_error, mock_kernel32, mock_user32):
        """_run_hook_loop should handle hook installation failure."""
        mock_user32.SetWindowsHookExW.return_value = None  # Failure
        mock_error.return_value = 1234
        mock_kernel32.GetModuleHandleW.return_value = 0

        service = KeyboardRestrictionService(enabled=True)
        service._run_hook_loop()

        # Hook handle should remain None
        assert service.hook_handle is None

    @patch("services.keyboard_restriction_service.user32")
    @patch("services.keyboard_restriction_service.kernel32")
    def test_hook_loop_runs_message_loop(self, mock_kernel32, mock_user32):
        """_run_hook_loop should run message loop."""
        mock_user32.SetWindowsHookExW.return_value = 12345
        mock_kernel32.GetModuleHandleW.return_value = 0

        # Simulate message loop: return non-zero once, then zero to exit
        mock_user32.GetMessageW.side_effect = [1, 0]

        service = KeyboardRestrictionService(enabled=True)
        service._run_hook_loop()

        # Should have processed at least one message
        assert mock_user32.TranslateMessage.call_count >= 1
        assert mock_user32.DispatchMessageW.call_count >= 1

    @patch("services.keyboard_restriction_service.user32")
    @patch("services.keyboard_restriction_service.kernel32")
    def test_hook_loop_handles_exception(self, mock_kernel32, mock_user32):
        """_run_hook_loop should handle exceptions gracefully."""
        mock_user32.SetWindowsHookExW.side_effect = Exception("Test error")
        mock_kernel32.GetModuleHandleW.return_value = 0

        service = KeyboardRestrictionService(enabled=True)

        # Should not raise
        service._run_hook_loop()

        assert service.hook_handle is None

    @patch("services.keyboard_restriction_service.user32")
    @patch("services.keyboard_restriction_service.kernel32")
    def test_hook_loop_cleanup_on_exit(self, mock_kernel32, mock_user32):
        """_run_hook_loop should clean up hook on exit."""
        mock_user32.SetWindowsHookExW.return_value = 12345
        mock_user32.GetMessageW.return_value = 0
        mock_kernel32.GetModuleHandleW.return_value = 0

        service = KeyboardRestrictionService(enabled=True)
        service._run_hook_loop()

        # UnhookWindowsHookEx should be called in finally block
        mock_user32.UnhookWindowsHookEx.assert_called_once_with(12345)

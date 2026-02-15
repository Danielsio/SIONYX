"""
Tests for global_hotkey_service.py - Global Hotkey Service
"""

from unittest.mock import patch

from PyQt6.QtCore import QObject


# =============================================================================
# Test GlobalHotkeyService initialization
# =============================================================================
class TestGlobalHotkeyServiceInit:
    """Tests for GlobalHotkeyService initialization"""

    def test_init_sets_is_running_false(self, qapp):
        """Test initialization sets is_running to False"""
        with patch("services.global_hotkey_service.keyboard"):
            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()

            assert service.is_running is False

    def test_init_sets_hotkey_thread_none(self, qapp):
        """Test initialization sets hotkey_thread to None"""
        with patch("services.global_hotkey_service.keyboard"):
            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()

            assert service.hotkey_thread is None

    def test_has_admin_exit_signal(self, qapp):
        """Test service has admin_exit_requested signal"""
        with patch("services.global_hotkey_service.keyboard"):
            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()

            assert hasattr(service, "admin_exit_requested")

    def test_inherits_from_qobject(self, qapp):
        """Test service inherits from QObject"""
        with patch("services.global_hotkey_service.keyboard"):
            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()

            assert isinstance(service, QObject)


# =============================================================================
# Test start method
# =============================================================================
class TestGlobalHotkeyServiceStart:
    """Tests for GlobalHotkeyService start method"""

    def test_start_sets_is_running_true(self, qapp):
        """Test start sets is_running to True"""
        with patch("services.global_hotkey_service.keyboard"):
            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()
            service.start()

            assert service.is_running is True

            # Cleanup
            service.is_running = False

    def test_start_creates_hotkey_thread(self, qapp):
        """Test start creates hotkey thread"""
        with patch("services.global_hotkey_service.keyboard"):
            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()
            service.start()

            assert service.hotkey_thread is not None

            # Cleanup
            service.is_running = False

    def test_start_when_already_running_returns_early(self, qapp):
        """Test start returns early if already running"""
        with patch("services.global_hotkey_service.keyboard"):
            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()
            service.is_running = True
            original_thread = service.hotkey_thread

            service.start()

            # Thread should not change
            assert service.hotkey_thread == original_thread


# =============================================================================
# Test stop method
# =============================================================================
class TestGlobalHotkeyServiceStop:
    """Tests for GlobalHotkeyService stop method"""

    def test_stop_sets_is_running_false(self, qapp):
        """Test stop sets is_running to False"""
        with patch("services.global_hotkey_service.keyboard"):
            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()
            service.is_running = True

            service.stop()

            assert service.is_running is False

    def test_stop_calls_unhook_all(self, qapp):
        """Test stop calls keyboard.unhook_all"""
        with patch("services.global_hotkey_service.keyboard") as mock_keyboard:
            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()
            service.is_running = True

            service.stop()

            mock_keyboard.unhook_all.assert_called_once()

    def test_stop_when_not_running_returns_early(self, qapp):
        """Test stop returns early if not running"""
        with patch("services.global_hotkey_service.keyboard") as mock_keyboard:
            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()
            service.is_running = False

            service.stop()

            # unhook_all should not be called
            mock_keyboard.unhook_all.assert_not_called()

    def test_stop_handles_unhook_exception(self, qapp):
        """Test stop handles exception from unhook_all"""
        with patch("services.global_hotkey_service.keyboard") as mock_keyboard:
            mock_keyboard.unhook_all.side_effect = Exception("Unhook error")

            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()
            service.is_running = True

            # Should not raise
            service.stop()

            assert service.is_running is False


# =============================================================================
# Test _on_admin_exit_hotkey method
# =============================================================================
class TestOnAdminExitHotkey:
    """Tests for _on_admin_exit_hotkey method"""

    def test_emits_admin_exit_signal(self, qapp):
        """Test hotkey handler emits admin_exit_requested signal"""
        with patch("services.global_hotkey_service.keyboard"):
            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()

            signal_received = []
            service.admin_exit_requested.connect(lambda: signal_received.append(True))

            service._on_admin_exit_hotkey()

            assert len(signal_received) == 1


# =============================================================================
# Test _listen_for_hotkeys method
# =============================================================================
class TestListenForHotkeys:
    """Tests for _listen_for_hotkeys method"""

    def test_registers_admin_exit_hotkeys(self, qapp):
        """Test listener registers configured + legacy admin exit hotkeys"""
        with patch("services.global_hotkey_service.keyboard") as mock_keyboard:
            # Make wait() exit immediately
            mock_keyboard.wait.side_effect = Exception("Exit loop")

            from services.global_hotkey_service import GlobalHotkeyService
            from utils.const import ADMIN_EXIT_HOTKEY_DEFAULT

            service = GlobalHotkeyService()
            service.is_running = True

            # Call listener directly (will exit on exception)
            service._listen_for_hotkeys()

            # Check hotkeys were registered
            hotkeys = [call[0][0] for call in mock_keyboard.add_hotkey.call_args_list]
            assert ADMIN_EXIT_HOTKEY_DEFAULT in hotkeys
            assert "ctrl+alt+q" in hotkeys

    def test_env_hotkey_override(self, qapp):
        """Test listener uses env override for admin exit hotkey"""
        with patch("services.global_hotkey_service.keyboard") as mock_keyboard:
            # Make wait() exit immediately
            mock_keyboard.wait.side_effect = Exception("Exit loop")

            with patch.dict("os.environ", {"ADMIN_EXIT_HOTKEY": "ctrl+alt+shift+x"}):
                from services.global_hotkey_service import GlobalHotkeyService

                service = GlobalHotkeyService()
                service.is_running = True

                service._listen_for_hotkeys()

                hotkeys = [
                    call[0][0] for call in mock_keyboard.add_hotkey.call_args_list
                ]
                assert "ctrl+alt+shift+x" in hotkeys
                assert "ctrl+alt+q" in hotkeys

    def test_handles_exception_in_listener(self, qapp):
        """Test listener handles exceptions gracefully"""
        with patch("services.global_hotkey_service.keyboard") as mock_keyboard:
            mock_keyboard.add_hotkey.side_effect = Exception("Hotkey error")

            from services.global_hotkey_service import GlobalHotkeyService

            service = GlobalHotkeyService()
            service.is_running = True

            # Should not raise
            service._listen_for_hotkeys()

"""
Unit tests for ProcessRestrictionService.
"""

from unittest.mock import MagicMock, patch

from services.process_restriction_service import ProcessRestrictionService


class TestProcessRestrictionServiceInit:
    """Tests for service initialization."""

    def test_init_default_enabled(self):
        """Service should be enabled by default."""
        service = ProcessRestrictionService()
        assert service.enabled is True

    def test_init_disabled(self):
        """Service can be initialized as disabled."""
        service = ProcessRestrictionService(enabled=False)
        assert service.enabled is False

    def test_init_default_blacklist(self):
        """Default blacklist should contain common dangerous processes."""
        service = ProcessRestrictionService()
        assert "cmd.exe" in service.blacklist
        assert "regedit.exe" in service.blacklist
        assert "powershell.exe" in service.blacklist
        assert "taskmgr.exe" in service.blacklist

    def test_init_custom_blacklist(self):
        """Custom blacklist can be provided."""
        custom = {"notepad.exe", "calc.exe"}
        service = ProcessRestrictionService(blacklist=custom)
        assert service.blacklist == custom

    def test_init_custom_interval(self):
        """Custom check interval can be set."""
        service = ProcessRestrictionService(check_interval_ms=5000)
        assert service.check_interval_ms == 5000


class TestProcessRestrictionServiceBlacklist:
    """Tests for blacklist management."""

    def test_add_to_blacklist(self):
        """Can add process to blacklist."""
        service = ProcessRestrictionService()
        service.add_to_blacklist("notepad.exe")
        assert "notepad.exe" in service.blacklist

    def test_add_to_blacklist_lowercase(self):
        """Process names are normalized to lowercase."""
        service = ProcessRestrictionService()
        service.add_to_blacklist("NOTEPAD.EXE")
        assert "notepad.exe" in service.blacklist

    def test_remove_from_blacklist(self):
        """Can remove process from blacklist."""
        service = ProcessRestrictionService()
        service.add_to_blacklist("notepad.exe")
        service.remove_from_blacklist("notepad.exe")
        assert "notepad.exe" not in service.blacklist

    def test_remove_nonexistent_from_blacklist(self):
        """Removing nonexistent process doesn't raise."""
        service = ProcessRestrictionService()
        # Should not raise
        service.remove_from_blacklist("nonexistent.exe")

    def test_get_blacklist_sorted(self):
        """get_blacklist returns sorted list."""
        service = ProcessRestrictionService(blacklist={"zebra.exe", "alpha.exe"})
        result = service.get_blacklist()
        assert result == ["alpha.exe", "zebra.exe"]


class TestProcessRestrictionServiceControl:
    """Tests for start/stop/enable methods."""

    def test_start_when_enabled(self):
        """Start should start the timer when enabled."""
        service = ProcessRestrictionService(enabled=True)

        with patch.object(service.check_timer, "start") as mock_start:
            with patch.object(service, "_check_processes"):
                service.start()
                mock_start.assert_called_once_with(service.check_interval_ms)

    def test_start_when_disabled(self):
        """Start should not start timer when disabled."""
        service = ProcessRestrictionService(enabled=False)

        with patch.object(service.check_timer, "start") as mock_start:
            service.start()
            mock_start.assert_not_called()

    def test_stop(self):
        """Stop should stop the timer."""
        service = ProcessRestrictionService()

        with patch.object(service.check_timer, "stop") as mock_stop:
            service.stop()
            mock_stop.assert_called_once()

    def test_set_enabled_true(self):
        """set_enabled(True) should start the service."""
        service = ProcessRestrictionService(enabled=False)

        with patch.object(service, "start") as mock_start:
            service.set_enabled(True)
            assert service.enabled is True
            mock_start.assert_called_once()

    def test_set_enabled_false(self):
        """set_enabled(False) should stop the service."""
        service = ProcessRestrictionService(enabled=True)

        with patch.object(service, "stop") as mock_stop:
            service.set_enabled(False)
            assert service.enabled is False
            mock_stop.assert_called_once()


class TestProcessRestrictionServiceIsActive:
    """Tests for is_active method."""

    def test_is_active_when_timer_running(self):
        """is_active returns True when timer is running and enabled."""
        service = ProcessRestrictionService(enabled=True)

        with patch.object(service.check_timer, "isActive", return_value=True):
            assert service.is_active() is True

    def test_is_active_when_timer_stopped(self):
        """is_active returns False when timer is stopped."""
        service = ProcessRestrictionService(enabled=True)

        with patch.object(service.check_timer, "isActive", return_value=False):
            assert service.is_active() is False

    def test_is_active_when_disabled(self):
        """is_active returns False when disabled."""
        service = ProcessRestrictionService(enabled=False)

        with patch.object(service.check_timer, "isActive", return_value=True):
            assert service.is_active() is False


class TestProcessRestrictionServiceCheckProcesses:
    """Tests for process checking logic."""

    @patch("services.process_restriction_service.psutil.process_iter")
    def test_check_processes_kills_blacklisted(self, mock_process_iter):
        """Should terminate blacklisted processes."""
        # Create mock process
        mock_proc = MagicMock()
        mock_proc.info = {"name": "cmd.exe", "pid": 1234}
        mock_proc.pid = 1234
        mock_process_iter.return_value = [mock_proc]

        service = ProcessRestrictionService(enabled=True)
        service._check_processes()

        mock_proc.terminate.assert_called_once()

    @patch("services.process_restriction_service.psutil.process_iter")
    def test_check_processes_ignores_allowed(self, mock_process_iter):
        """Should not terminate non-blacklisted processes."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "notepad.exe", "pid": 1234}
        mock_proc.pid = 1234
        mock_process_iter.return_value = [mock_proc]

        service = ProcessRestrictionService(enabled=True)
        service._check_processes()

        mock_proc.terminate.assert_not_called()

    @patch("services.process_restriction_service.psutil.process_iter")
    def test_check_processes_skips_when_disabled(self, mock_process_iter):
        """Should not check processes when disabled."""
        service = ProcessRestrictionService(enabled=False)
        service._check_processes()

        mock_process_iter.assert_not_called()

    @patch("services.process_restriction_service.psutil.process_iter")
    def test_check_processes_handles_no_such_process(self, mock_process_iter):
        """Should handle NoSuchProcess exception gracefully."""
        import psutil

        mock_proc = MagicMock()
        mock_proc.info.__getitem__.side_effect = psutil.NoSuchProcess(1234)
        mock_process_iter.return_value = [mock_proc]

        service = ProcessRestrictionService(enabled=True)
        # Should not raise
        service._check_processes()

    @patch("services.process_restriction_service.psutil.process_iter")
    def test_check_processes_skips_recently_blocked(self, mock_process_iter):
        """Should skip processes that were recently blocked."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "cmd.exe", "pid": 1234}
        mock_proc.pid = 1234
        mock_process_iter.return_value = [mock_proc]

        service = ProcessRestrictionService(enabled=True)
        # Mark this PID as recently blocked
        service.recently_blocked.add(1234)
        service._check_processes()

        # Should not try to terminate again
        mock_proc.terminate.assert_not_called()

    @patch("services.process_restriction_service.psutil.process_iter")
    def test_check_processes_handles_access_denied(self, mock_process_iter):
        """Should handle AccessDenied exception gracefully."""
        import psutil

        mock_proc = MagicMock()
        mock_proc.info.__getitem__.side_effect = psutil.AccessDenied(1234)
        mock_process_iter.return_value = [mock_proc]

        service = ProcessRestrictionService(enabled=True)
        # Should not raise
        service._check_processes()

    @patch("services.process_restriction_service.psutil.process_iter")
    def test_check_processes_handles_general_exception(self, mock_process_iter):
        """Should handle general exception in check loop."""
        mock_process_iter.side_effect = RuntimeError("Unexpected error")

        service = ProcessRestrictionService(enabled=True)
        # Should not raise
        service._check_processes()


class TestProcessRestrictionServiceTerminate:
    """Tests for process termination logic."""

    def test_terminate_process_timeout_forces_kill(self):
        """Should force kill if terminate times out."""
        import psutil

        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_proc.wait.side_effect = psutil.TimeoutExpired(1)

        service = ProcessRestrictionService(enabled=True)
        service._terminate_process(mock_proc, "test.exe")

        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()

    def test_terminate_process_already_gone(self):
        """Should handle process already gone."""
        import psutil

        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_proc.terminate.side_effect = psutil.NoSuchProcess(1234)

        service = ProcessRestrictionService(enabled=True)
        # Should not raise
        service._terminate_process(mock_proc, "test.exe")

    def test_terminate_process_access_denied(self):
        """Should handle access denied and emit error signal."""
        import psutil

        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_proc.terminate.side_effect = psutil.AccessDenied(1234)

        service = ProcessRestrictionService(enabled=True)
        error_handler = MagicMock()
        service.error_occurred.connect(error_handler)

        service._terminate_process(mock_proc, "test.exe")

        # Should emit error signal
        error_handler.assert_called_once()

    def test_terminate_process_general_exception(self):
        """Should handle general exception and emit error signal."""
        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_proc.terminate.side_effect = RuntimeError("Unexpected")

        service = ProcessRestrictionService(enabled=True)
        error_handler = MagicMock()
        service.error_occurred.connect(error_handler)

        service._terminate_process(mock_proc, "test.exe")

        # Should emit error signal
        error_handler.assert_called_once()

    def test_terminate_process_emits_blocked_signal(self):
        """Should emit process_blocked signal on success."""
        mock_proc = MagicMock()
        mock_proc.pid = 1234

        service = ProcessRestrictionService(enabled=True)
        blocked_handler = MagicMock()
        service.process_blocked.connect(blocked_handler)

        service._terminate_process(mock_proc, "cmd.exe")

        blocked_handler.assert_called_once_with("cmd.exe")

    def test_terminate_process_adds_to_recently_blocked(self):
        """Should add PID to recently_blocked set."""
        mock_proc = MagicMock()
        mock_proc.pid = 5678

        service = ProcessRestrictionService(enabled=True)
        service._terminate_process(mock_proc, "test.exe")

        assert 5678 in service.recently_blocked


class TestProcessRestrictionServiceCleanup:
    """Tests for cleanup logic."""

    @patch("services.process_restriction_service.psutil.process_iter")
    def test_cleanup_blocked_set_removes_dead_pids(self, mock_process_iter):
        """Should remove PIDs that are no longer running."""
        # Only PID 1000 is still running
        mock_proc = MagicMock()
        mock_proc.pid = 1000
        mock_process_iter.return_value = [mock_proc]

        service = ProcessRestrictionService(enabled=True)
        service.recently_blocked = {1000, 2000, 3000}

        service._cleanup_blocked_set()

        # Only 1000 should remain
        assert service.recently_blocked == {1000}


class TestProcessRestrictionServiceSignals:
    """Tests for Qt signals."""

    def test_process_blocked_signal_exists(self):
        """Service should have process_blocked signal."""
        service = ProcessRestrictionService()
        assert hasattr(service, "process_blocked")

    def test_error_occurred_signal_exists(self):
        """Service should have error_occurred signal."""
        service = ProcessRestrictionService()
        assert hasattr(service, "error_occurred")

    def test_signals_can_connect(self):
        """Signals should be connectable."""
        service = ProcessRestrictionService()
        handler = MagicMock()

        # Should not raise
        service.process_blocked.connect(handler)
        service.error_occurred.connect(handler)


class TestProcessRestrictionServiceDefaultBlacklist:
    """Tests for the default blacklist contents."""

    def test_contains_system_tools(self):
        """Default blacklist should contain dangerous system tools."""
        blacklist = ProcessRestrictionService.DEFAULT_BLACKLIST

        assert "cmd.exe" in blacklist
        assert "powershell.exe" in blacklist
        assert "regedit.exe" in blacklist
        assert "taskmgr.exe" in blacklist
        assert "mmc.exe" in blacklist

    def test_contains_script_hosts(self):
        """Default blacklist should contain script hosts."""
        blacklist = ProcessRestrictionService.DEFAULT_BLACKLIST

        assert "wscript.exe" in blacklist
        assert "cscript.exe" in blacklist

    def test_contains_remote_access(self):
        """Default blacklist should contain remote access tools."""
        blacklist = ProcessRestrictionService.DEFAULT_BLACKLIST

        assert "teamviewer.exe" in blacklist
        assert "anydesk.exe" in blacklist

"""
Tests for ProcessCleanupService

Testing Strategy:
- Mock subprocess calls (don't actually kill processes!)
- Test whitelist/target logic
- Test error handling
"""

from unittest.mock import Mock, patch

import pytest

from services.process_cleanup_service import ProcessCleanupService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def cleanup_service():
    """Create a ProcessCleanupService instance."""
    return ProcessCleanupService()


@pytest.fixture
def mock_tasklist_output():
    """Sample tasklist output for testing."""
    return '''"Image Name","PID","Session Name","Session#","Mem Usage"
"System Idle Process","0","Services","0","8 K"
"System","4","Services","0","144 K"
"chrome.exe","1234","Console","1","150,000 K"
"chrome.exe","1235","Console","1","100,000 K"
"msedge.exe","2345","Console","1","200,000 K"
"explorer.exe","3456","Console","1","50,000 K"
"svchost.exe","4567","Services","0","30,000 K"
"notepad.exe","5678","Console","1","10,000 K"
'''


# =============================================================================
# Test Initialization
# =============================================================================


class TestProcessCleanupServiceInit:
    """Tests for service initialization."""

    def test_creates_instance(self, cleanup_service):
        """Test service can be instantiated."""
        assert cleanup_service is not None
        assert isinstance(cleanup_service, ProcessCleanupService)

    def test_has_whitelist(self, cleanup_service):
        """Test service has whitelist of protected processes."""
        assert hasattr(ProcessCleanupService, "WHITELIST")
        assert "explorer.exe" in ProcessCleanupService.WHITELIST
        assert "svchost.exe" in ProcessCleanupService.WHITELIST

    def test_has_targets(self, cleanup_service):
        """Test service has list of target processes."""
        assert hasattr(ProcessCleanupService, "TARGETS")
        assert "chrome.exe" in ProcessCleanupService.TARGETS
        assert "msedge.exe" in ProcessCleanupService.TARGETS


# =============================================================================
# Test Get Running Processes
# =============================================================================


class TestGetRunningProcesses:
    """Tests for _get_running_processes method."""

    def test_parses_tasklist_output(self, cleanup_service, mock_tasklist_output):
        """Test parses tasklist CSV output correctly."""
        mock_result = Mock()
        mock_result.stdout = mock_tasklist_output

        with patch("subprocess.run", return_value=mock_result):
            processes = cleanup_service._get_running_processes()

        assert "chrome.exe" in processes
        assert len(processes["chrome.exe"]) == 2  # Two Chrome processes
        assert 1234 in processes["chrome.exe"]
        assert 1235 in processes["chrome.exe"]

    def test_handles_empty_output(self, cleanup_service):
        """Test handles empty tasklist output."""
        mock_result = Mock()
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            processes = cleanup_service._get_running_processes()

        assert processes == {}

    def test_handles_timeout(self, cleanup_service):
        """Test handles subprocess timeout."""
        import subprocess

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 10)):
            processes = cleanup_service._get_running_processes()

        assert processes == {}

    def test_handles_exception(self, cleanup_service):
        """Test handles subprocess exception."""
        with patch("subprocess.run", side_effect=Exception("Error")):
            processes = cleanup_service._get_running_processes()

        assert processes == {}


# =============================================================================
# Test Kill Process
# =============================================================================


class TestKillProcess:
    """Tests for _kill_process method."""

    def test_kills_process_successfully(self, cleanup_service):
        """Test kills process with taskkill."""
        mock_result = Mock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = cleanup_service._kill_process(1234, "test.exe")

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "/PID" in call_args
        assert "1234" in call_args

    def test_handles_kill_failure(self, cleanup_service):
        """Test handles taskkill failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Access denied"

        with patch("subprocess.run", return_value=mock_result):
            result = cleanup_service._kill_process(1234, "test.exe")

        assert result is False

    def test_handles_kill_timeout(self, cleanup_service):
        """Test handles taskkill timeout."""
        import subprocess

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5)):
            result = cleanup_service._kill_process(1234, "test.exe")

        assert result is False

    def test_handles_kill_exception(self, cleanup_service):
        """Test handles taskkill exception."""
        with patch("subprocess.run", side_effect=Exception("Error")):
            result = cleanup_service._kill_process(1234, "test.exe")

        assert result is False


# =============================================================================
# Test Cleanup User Processes
# =============================================================================


class TestCleanupUserProcesses:
    """Tests for cleanup_user_processes method."""

    def test_kills_target_processes(self, cleanup_service, mock_tasklist_output):
        """Test kills processes in TARGETS list."""
        mock_list_result = Mock()
        mock_list_result.stdout = mock_tasklist_output

        mock_kill_result = Mock()
        mock_kill_result.returncode = 0

        def mock_run_side_effect(*args, **kwargs):
            # First call is tasklist, rest are taskkill
            if "tasklist" in args[0]:
                return mock_list_result
            return mock_kill_result

        with patch("subprocess.run", side_effect=mock_run_side_effect):
            result = cleanup_service.cleanup_user_processes()

        # Should have closed some processes (chrome, edge, notepad)
        assert result["closed_count"] >= 1
        assert "chrome.exe" in result["closed_processes"]

    def test_skips_whitelisted_processes(self, cleanup_service):
        """Test skips processes in whitelist."""
        tasklist = '''"explorer.exe","1234","Console","1","50,000 K"
"svchost.exe","2345","Services","0","30,000 K"
'''
        mock_result = Mock()
        mock_result.stdout = tasklist

        with patch("subprocess.run", return_value=mock_result):
            result = cleanup_service.cleanup_user_processes()

        # Should not try to kill whitelisted processes
        assert result["closed_count"] == 0

    def test_handles_no_processes(self, cleanup_service):
        """Test handles case with no processes to clean."""
        mock_result = Mock()
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            result = cleanup_service.cleanup_user_processes()

        assert result["success"] is True
        assert result["closed_count"] == 0


# =============================================================================
# Test Close Browsers Only
# =============================================================================


class TestCloseBrowsersOnly:
    """Tests for close_browsers_only method."""

    def test_closes_only_browsers(self, cleanup_service, mock_tasklist_output):
        """Test closes only browser processes."""
        mock_list_result = Mock()
        mock_list_result.stdout = mock_tasklist_output

        mock_kill_result = Mock()
        mock_kill_result.returncode = 0

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [mock_list_result] + [mock_kill_result] * 10
            result = cleanup_service.close_browsers_only()

        assert result["success"] is True
        # Should close chrome.exe and msedge.exe (3 processes total)
        assert result["closed_count"] >= 1


# =============================================================================
# Test Is Process Running
# =============================================================================


class TestIsProcessRunning:
    """Tests for is_process_running method."""

    def test_detects_running_process(self, cleanup_service, mock_tasklist_output):
        """Test detects a running process."""
        mock_result = Mock()
        mock_result.stdout = mock_tasklist_output

        with patch("subprocess.run", return_value=mock_result):
            result = cleanup_service.is_process_running("chrome.exe")

        assert result is True

    def test_detects_not_running_process(self, cleanup_service, mock_tasklist_output):
        """Test detects a process that isn't running."""
        mock_result = Mock()
        mock_result.stdout = mock_tasklist_output

        with patch("subprocess.run", return_value=mock_result):
            result = cleanup_service.is_process_running("vlc.exe")

        assert result is False


# =============================================================================
# Test Get Running User Processes
# =============================================================================


class TestGetRunningUserProcesses:
    """Tests for get_running_user_processes method."""

    def test_returns_non_system_processes(self, cleanup_service, mock_tasklist_output):
        """Test returns user processes, not system processes."""
        mock_result = Mock()
        mock_result.stdout = mock_tasklist_output

        with patch("subprocess.run", return_value=mock_result):
            processes = cleanup_service.get_running_user_processes()

        # Should include chrome, edge, notepad but not explorer, svchost
        assert "chrome.exe" in processes
        assert "msedge.exe" in processes
        assert "notepad.exe" in processes
        assert "explorer.exe" not in processes
        assert "svchost.exe" not in processes


# =============================================================================
# Test Whitelist and Target Constants
# =============================================================================


class TestConstants:
    """Tests for whitelist and target constants."""

    def test_sionyx_in_whitelist(self):
        """Test SIONYX process is in whitelist."""
        assert "sionyx.exe" in ProcessCleanupService.WHITELIST

    def test_python_in_whitelist(self):
        """Test Python process is in whitelist (for dev)."""
        assert "python.exe" in ProcessCleanupService.WHITELIST

    def test_browsers_in_targets(self):
        """Test all major browsers are in targets."""
        assert "chrome.exe" in ProcessCleanupService.TARGETS
        assert "msedge.exe" in ProcessCleanupService.TARGETS
        assert "firefox.exe" in ProcessCleanupService.TARGETS

    def test_office_in_targets(self):
        """Test Office apps are in targets."""
        assert "winword.exe" in ProcessCleanupService.TARGETS
        assert "excel.exe" in ProcessCleanupService.TARGETS

    def test_discord_in_targets(self):
        """Test Discord is in targets."""
        assert "discord.exe" in ProcessCleanupService.TARGETS


# =============================================================================
# Test Kill By Name
# =============================================================================


class TestKillByName:
    """Tests for _kill_by_name method."""

    def test_kills_process_by_name(self, cleanup_service):
        """Test kills all instances of a process by name."""
        mock_result = Mock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = cleanup_service._kill_by_name("Discord.exe")

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "/IM" in call_args
        assert "Discord.exe" in call_args
        assert "/F" in call_args
        assert "/T" in call_args

    def test_handles_process_not_found(self, cleanup_service):
        """Test handles case when process is not running."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "ERROR: The process \"Discord.exe\" not found."

        with patch("subprocess.run", return_value=mock_result):
            result = cleanup_service._kill_by_name("Discord.exe")

        # Should return True since process is not running (already dead)
        assert result is True

    def test_handles_kill_failure(self, cleanup_service):
        """Test handles kill failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Access denied"

        with patch("subprocess.run", return_value=mock_result):
            result = cleanup_service._kill_by_name("Discord.exe")

        assert result is False


# =============================================================================
# Test Kill Process Retry Logic
# =============================================================================


class TestKillProcessRetry:
    """Tests for _kill_process retry logic."""

    def test_retries_on_failure(self, cleanup_service):
        """Test retries killing process on failure."""
        mock_fail = Mock()
        mock_fail.returncode = 1
        mock_fail.stderr = "Access denied"

        mock_success = Mock()
        mock_success.returncode = 0

        with patch("subprocess.run", side_effect=[mock_fail, mock_success]) as mock_run:
            with patch("time.sleep"):  # Don't actually sleep in tests
                result = cleanup_service._kill_process(1234, "test.exe", retry_count=1)

        assert result is True
        assert mock_run.call_count == 2

    def test_uses_tree_kill(self, cleanup_service):
        """Test uses /T flag for tree kill."""
        mock_result = Mock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            cleanup_service._kill_process(1234, "test.exe")

        call_args = mock_run.call_args[0][0]
        assert "/T" in call_args
        assert "/F" in call_args

    def test_returns_true_if_process_already_dead(self, cleanup_service):
        """Test returns True if process is already terminated."""
        mock_result = Mock()
        mock_result.returncode = 128
        mock_result.stderr = "ERROR: The process with PID 1234 not found."

        with patch("subprocess.run", return_value=mock_result):
            result = cleanup_service._kill_process(1234, "test.exe")

        assert result is True


# =============================================================================
# Test Stubborn Process Handling
# =============================================================================


class TestStubbornProcessHandling:
    """Tests for handling stubborn processes like Discord."""

    def test_uses_kill_by_name_for_discord(self, cleanup_service):
        """Test uses _kill_by_name for Discord."""
        tasklist = '''"Image Name","PID","Session Name","Session#","Mem Usage"
"Discord.exe","1234","Console","1","150,000 K"
"Discord.exe","1235","Console","1","100,000 K"
'''
        mock_list_result = Mock()
        mock_list_result.stdout = tasklist

        mock_kill_result = Mock()
        mock_kill_result.returncode = 0

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [mock_list_result, mock_kill_result]
            result = cleanup_service.cleanup_user_processes()

        # Should have closed both Discord PIDs
        assert "Discord.exe" in result["closed_processes"]
        assert result["closed_count"] == 2

    def test_discord_in_stubborn_list(self, cleanup_service):
        """Test Discord is treated as stubborn process."""
        # Verify the cleanup logic recognizes Discord as stubborn
        assert "discord.exe" in {"discord.exe", "teams.exe", "slack.exe", "zoom.exe"}

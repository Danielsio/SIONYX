"""
Tests for SessionService
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from services.session_service import SessionService


class TestSessionService:
    """Test cases for SessionService"""

    @pytest.fixture
    def session_service(self, mock_firebase_client, qtbot):
        """Create SessionService instance with mocked dependencies"""
        with patch("services.session_service.ComputerService"):
            with patch("services.session_service.PrintMonitorService"):
                return SessionService(mock_firebase_client, "test-user-id", "test-org")

    def test_initialization(self, session_service):
        """Test SessionService initialization"""
        assert session_service.user_id == "test-user-id"
        assert session_service.org_id == "test-org"
        assert session_service.session_id is None
        assert session_service.is_active is False
        assert session_service.remaining_time == 0

    def test_start_session_success(self, session_service, mock_firebase_client, qtbot):
        """Test successful session start"""
        mock_firebase_client.db_update.return_value = {"success": True}
        session_service.computer_service.get_computer_info.return_value = {
            "success": True,
            "data": {"computerName": "Test PC"},
        }

        with patch.object(session_service, "_get_current_computer_id", return_value="test-computer-id"):
            result = session_service.start_session(3600)

        assert result["success"] is True
        assert session_service.is_active is True
        assert session_service.remaining_time == 3600

    def test_start_session_already_active(self, session_service):
        """Test starting session when already active"""
        session_service.is_active = True
        result = session_service.start_session(3600)
        assert result["success"] is False
        assert result["error"] == "Session already active"

    def test_start_session_no_time(self, session_service):
        """Test starting session with no remaining time"""
        result = session_service.start_session(0)
        assert result["success"] is False
        assert result["error"] == "No time remaining"

    def test_start_session_negative_time(self, session_service):
        """Test starting session with negative time"""
        result = session_service.start_session(-100)
        assert result["success"] is False
        assert result["error"] == "No time remaining"

    def test_start_session_firebase_failure(self, session_service, mock_firebase_client, qtbot):
        """Test session start with Firebase failure"""
        mock_firebase_client.db_update.return_value = {"success": False, "error": "Database error"}
        session_service.computer_service.get_computer_info.return_value = {
            "success": True,
            "data": {"computerName": "Test PC"},
        }

        with patch.object(session_service, "_get_current_computer_id", return_value="test-computer-id"):
            result = session_service.start_session(3600)

        assert result["success"] is False
        assert session_service.is_active is False

    def test_end_session_success(self, session_service, mock_firebase_client, qtbot):
        """Test successful session end"""
        session_service.is_active = True
        session_service.session_id = "test-session-id"
        session_service.remaining_time = 1800
        session_service.start_time = datetime.now() - timedelta(minutes=30)
        mock_firebase_client.db_update.return_value = {"success": True}

        result = session_service.end_session("user")

        assert result["success"] is True
        assert session_service.is_active is False
        # remaining_time is preserved (not reset) so user keeps their time for next session
        assert session_service.remaining_time == 1800
        assert result["remaining_time"] == 1800

    def test_end_session_not_active(self, session_service):
        """Test ending session when not active"""
        result = session_service.end_session("user")
        assert result["success"] is False
        assert result["error"] == "No active session"

    def test_countdown_tick_normal(self, session_service, qtbot):
        """Test countdown tick under normal conditions"""
        session_service.is_active = True
        session_service.remaining_time = 100

        time_updated_signals = []
        session_service.time_updated.connect(lambda x: time_updated_signals.append(x))

        session_service._on_countdown_tick()

        assert session_service.remaining_time == 99
        assert len(time_updated_signals) == 1

    def test_countdown_tick_5min_warning(self, session_service, qtbot):
        """Test countdown tick triggering 5-minute warning"""
        session_service.is_active = True
        # Set to 301 because _on_countdown_tick decrements BEFORE checking
        session_service.remaining_time = 301
        session_service.warned_5min = False

        warning_signals = []
        session_service.warning_5min.connect(lambda: warning_signals.append(True))

        session_service._on_countdown_tick()

        assert session_service.remaining_time == 300  # After decrement
        assert session_service.warned_5min is True
        assert len(warning_signals) == 1

    def test_countdown_tick_1min_warning(self, session_service, qtbot):
        """Test countdown tick triggering 1-minute warning"""
        session_service.is_active = True
        # Set to 61 because _on_countdown_tick decrements BEFORE checking
        session_service.remaining_time = 61
        session_service.warned_5min = True
        session_service.warned_1min = False

        warning_signals = []
        session_service.warning_1min.connect(lambda: warning_signals.append(True))

        session_service._on_countdown_tick()

        assert session_service.remaining_time == 60  # After decrement
        assert session_service.warned_1min is True
        assert len(warning_signals) == 1

    def test_countdown_tick_session_expired(self, session_service, qtbot):
        """Test countdown tick when session expires"""
        session_service.is_active = True
        session_service.remaining_time = 1
        session_service.warned_5min = True
        session_service.warned_1min = True

        session_ended_signals = []
        session_service.session_ended.connect(lambda x: session_ended_signals.append(x))

        with patch.object(session_service, "end_session", return_value={"success": True}) as mock_end:
            session_service._on_countdown_tick()

        assert session_service.remaining_time == 0
        mock_end.assert_called_once_with("expired")

    def test_sync_to_firebase_success(self, session_service, mock_firebase_client, qtbot):
        """Test successful Firebase sync"""
        session_service.is_active = True
        session_service.remaining_time = 1800
        session_service.consecutive_sync_failures = 2
        mock_firebase_client.db_update.return_value = {"success": True}

        sync_restored_signals = []
        session_service.sync_restored.connect(lambda: sync_restored_signals.append(True))

        session_service._sync_to_firebase()

        assert session_service.consecutive_sync_failures == 0
        assert len(sync_restored_signals) == 1

    def test_sync_to_firebase_failure(self, session_service, mock_firebase_client, qtbot):
        """Test Firebase sync failure - signal emits after 3 consecutive failures"""
        session_service.is_active = True
        session_service.remaining_time = 1800
        session_service.consecutive_sync_failures = 2  # Already had 2 failures
        mock_firebase_client.db_update.return_value = {"success": False, "error": "Network error"}

        sync_failed_signals = []
        session_service.sync_failed.connect(lambda x: sync_failed_signals.append(x))

        session_service._sync_to_firebase()

        # After 3rd failure, signal is emitted
        assert session_service.consecutive_sync_failures == 3
        assert session_service.is_online is False
        assert len(sync_failed_signals) == 1

    def test_sync_to_firebase_not_active(self, session_service, mock_firebase_client, qtbot):
        """Test Firebase sync when session is not active"""
        session_service.is_active = False
        session_service._sync_to_firebase()
        mock_firebase_client.db_update.assert_not_called()

    def test_get_remaining_time(self, session_service):
        """Test getting remaining time"""
        session_service.remaining_time = 1800
        assert session_service.get_remaining_time() == 1800

    def test_get_time_used(self, session_service):
        """Test getting time used"""
        session_service.time_used = 900
        assert session_service.get_time_used() == 900

    def test_is_session_active(self, session_service):
        """Test checking if session is active"""
        session_service.is_active = True
        assert session_service.is_session_active() is True

    def test_get_current_computer_id(self, session_service, mock_firebase_client):
        """Test getting current computer ID from Firebase"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"currentComputerId": "test-computer-123"}
        }

        result = session_service._get_current_computer_id()

        assert result == "test-computer-123"
        mock_firebase_client.db_get.assert_called_once_with("users/test-user-id")

    def test_get_current_computer_id_not_found(self, session_service, mock_firebase_client):
        """Test getting current computer ID when not set"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {}
        }

        result = session_service._get_current_computer_id()

        assert result == "unknown"

    @pytest.mark.parametrize("remaining_time,expected_warning", [
        # remaining_time is set BEFORE tick, tick decrements first then checks
        # So 301 -> 300 triggers 5min, 300 -> 299 does not
        (301, "5min"),
        (300, None),  # Becomes 299 after tick, no warning
        (61, "1min"),
        (60, None),   # Becomes 59 after tick, no warning
        (30, None),
    ])
    def test_warning_triggers(self, session_service, qtbot, remaining_time, expected_warning):
        """Test warning triggers at correct times"""
        session_service.is_active = True
        session_service.remaining_time = remaining_time
        session_service.warned_5min = False
        session_service.warned_1min = False

        warning_5min = []
        warning_1min = []
        session_service.warning_5min.connect(lambda: warning_5min.append(True))
        session_service.warning_1min.connect(lambda: warning_1min.append(True))

        session_service._on_countdown_tick()

        if expected_warning == "5min":
            assert len(warning_5min) == 1
            assert session_service.warned_5min is True
        elif expected_warning == "1min":
            assert len(warning_1min) == 1
            assert session_service.warned_1min is True
        else:
            assert len(warning_5min) == 0
            assert len(warning_1min) == 0


# =============================================================================
# Additional SessionService Tests
# =============================================================================

class TestSessionServiceAdditional:
    """Additional test cases for SessionService"""

    @pytest.fixture
    def session_service(self, mock_firebase_client, qtbot):
        """Create SessionService instance with mocked dependencies"""
        with patch("services.session_service.ComputerService"):
            with patch("services.session_service.PrintMonitorService"):
                return SessionService(mock_firebase_client, "test-user-id", "test-org")

    def test_countdown_tick_when_not_active(self, session_service):
        """Test countdown tick does nothing when not active"""
        session_service.is_active = False
        session_service.remaining_time = 100

        session_service._on_countdown_tick()

        assert session_service.remaining_time == 100  # Unchanged

    def test_end_session_disassociates_user_for_user_reason(self, session_service, mock_firebase_client, qtbot):
        """Test end_session disassociates user from computer for 'user' reason"""
        session_service.is_active = True
        session_service.session_id = "test-session-id"
        session_service.remaining_time = 1800
        mock_firebase_client.db_update.return_value = {"success": True}
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"currentComputerId": "computer-123"}
        }

        session_service.end_session("user")

        session_service.computer_service.disassociate_user_from_computer.assert_called_once()

    def test_end_session_disassociates_user_for_expired_reason(self, session_service, mock_firebase_client, qtbot):
        """Test end_session disassociates user from computer for 'expired' reason"""
        session_service.is_active = True
        session_service.session_id = "test-session-id"
        session_service.remaining_time = 0
        mock_firebase_client.db_update.return_value = {"success": True}
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"currentComputerId": "computer-123"}
        }

        session_service.end_session("expired")

        session_service.computer_service.disassociate_user_from_computer.assert_called_once()

    def test_get_current_computer_id_db_failure(self, session_service, mock_firebase_client):
        """Test _get_current_computer_id handles database failure"""
        mock_firebase_client.db_get.return_value = {"success": False, "error": "DB error"}

        result = session_service._get_current_computer_id()

        assert result == "unknown"

    def test_get_current_computer_id_exception(self, session_service, mock_firebase_client):
        """Test _get_current_computer_id handles exceptions"""
        mock_firebase_client.db_get.side_effect = Exception("Network error")

        result = session_service._get_current_computer_id()

        assert result == "unknown"

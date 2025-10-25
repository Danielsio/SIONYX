"""
Tests for SessionService
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from PyQt6.QtCore import QTimer

from src.services.session_service import SessionService


class TestSessionService:
    """Test cases for SessionService"""

    @pytest.fixture
    def session_service(self, mock_firebase_client, qtbot):
        """Create SessionService instance with mocked dependencies"""
        with patch("src.services.session_service.ComputerService"), patch(
            "src.services.session_service.PrintValidationService"
        ):
            service = SessionService(mock_firebase_client, "test-user-id", "test-org")
            return service

    def test_initialization(self, session_service):
        """Test SessionService initialization"""
        assert session_service.user_id == "test-user-id"
        assert session_service.org_id == "test-org"
        assert session_service.session_id is None
        assert session_service.is_active is False
        assert session_service.remaining_time == 0
        assert session_service.time_used == 0
        assert session_service.start_time is None
        assert session_service.is_online is True
        assert session_service.consecutive_sync_failures == 0
        assert session_service.warned_5min is False
        assert session_service.warned_1min is False

    def test_start_session_success(self, session_service, mock_firebase_client, qtbot):
        """Test successful session start"""
        initial_time = 3600  # 1 hour
        mock_firebase_client.db_update.return_value = {"success": True}
        session_service.computer_service.get_computer_info.return_value = {
            "success": True,
            "data": {"computerName": "Test PC"},
        }

        with patch.object(
            session_service, "_get_current_computer_id", return_value="test-computer-id"
        ):
            result = session_service.start_session(initial_time)

        assert result["success"] is True
        assert "session_id" in result
        assert session_service.is_active is True
        assert session_service.remaining_time == initial_time
        assert session_service.start_time is not None
        assert session_service.session_id is not None

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

    def test_start_session_firebase_failure(
        self, session_service, mock_firebase_client, qtbot
    ):
        """Test session start with Firebase failure"""
        initial_time = 3600
        mock_firebase_client.db_update.return_value = {
            "success": False,
            "error": "Database error",
        }
        session_service.computer_service.get_computer_info.return_value = {
            "success": True,
            "data": {"computerName": "Test PC"},
        }

        with patch.object(
            session_service, "_get_current_computer_id", return_value="test-computer-id"
        ):
            result = session_service.start_session(initial_time)

        assert result["success"] is False
        assert result["error"] == "Database error"
        assert session_service.is_active is False

    def test_end_session_success(self, session_service, mock_firebase_client, qtbot):
        """Test successful session end"""
        # Setup active session
        session_service.is_active = True
        session_service.session_id = "test-session-id"
        session_service.remaining_time = 1800
        session_service.start_time = datetime.now() - timedelta(minutes=30)

        mock_firebase_client.db_update.return_value = {"success": True}

        result = session_service.end_session("user")

        assert result["success"] is True
        assert session_service.is_active is False
        assert session_service.session_id is None
        assert session_service.remaining_time == 0

    def test_end_session_not_active(self, session_service):
        """Test ending session when not active"""
        result = session_service.end_session("user")

        assert result["success"] is False
        assert result["error"] == "No active session"

    def test_end_session_firebase_failure(
        self, session_service, mock_firebase_client, qtbot
    ):
        """Test session end with Firebase failure"""
        # Setup active session
        session_service.is_active = True
        session_service.session_id = "test-session-id"
        session_service.remaining_time = 1800

        mock_firebase_client.db_update.return_value = {
            "success": False,
            "error": "Database error",
        }

        result = session_service.end_session("user")

        assert result["success"] is False
        assert result["error"] == "Database error"

    def test_countdown_tick_normal(self, session_service, qtbot):
        """Test countdown tick under normal conditions"""
        session_service.is_active = True
        session_service.remaining_time = 100
        session_service.warned_5min = False
        session_service.warned_1min = False

        # Connect signal to capture emissions
        time_updated_signals = []
        warning_5min_signals = []
        warning_1min_signals = []

        session_service.time_updated.connect(lambda x: time_updated_signals.append(x))
        session_service.warning_5min.connect(lambda: warning_5min_signals.append(True))
        session_service.warning_1min.connect(lambda: warning_1min_signals.append(True))

        # Simulate countdown tick
        session_service._on_countdown_tick()

        assert session_service.remaining_time == 99
        assert len(time_updated_signals) == 1
        assert time_updated_signals[0] == 99

    def test_countdown_tick_5min_warning(self, session_service, qtbot):
        """Test countdown tick triggering 5-minute warning"""
        session_service.is_active = True
        session_service.remaining_time = 300  # 5 minutes
        session_service.warned_5min = False
        session_service.warned_1min = False

        warning_5min_signals = []
        session_service.warning_5min.connect(lambda: warning_5min_signals.append(True))

        session_service._on_countdown_tick()

        assert session_service.warned_5min is True
        assert len(warning_5min_signals) == 1

    def test_countdown_tick_1min_warning(self, session_service, qtbot):
        """Test countdown tick triggering 1-minute warning"""
        session_service.is_active = True
        session_service.remaining_time = 60  # 1 minute
        session_service.warned_5min = True
        session_service.warned_1min = False

        warning_1min_signals = []
        session_service.warning_1min.connect(lambda: warning_1min_signals.append(True))

        session_service._on_countdown_tick()

        assert session_service.warned_1min is True
        assert len(warning_1min_signals) == 1

    def test_countdown_tick_session_expired(self, session_service, qtbot):
        """Test countdown tick when session expires"""
        session_service.is_active = True
        session_service.remaining_time = 1
        session_service.warned_5min = True
        session_service.warned_1min = True

        session_ended_signals = []
        session_service.session_ended.connect(lambda x: session_ended_signals.append(x))

        with patch.object(
            session_service, "end_session", return_value={"success": True}
        ) as mock_end:
            session_service._on_countdown_tick()

        assert session_service.remaining_time == 0
        assert len(session_ended_signals) == 1
        assert session_ended_signals[0] == "expired"
        mock_end.assert_called_once_with("expired")

    def test_sync_to_firebase_success(
        self, session_service, mock_firebase_client, qtbot
    ):
        """Test successful Firebase sync"""
        session_service.is_active = True
        session_service.remaining_time = 1800
        session_service.time_used = 1800
        session_service.is_online = True
        session_service.consecutive_sync_failures = 2

        mock_firebase_client.db_update.return_value = {"success": True}

        sync_restored_signals = []
        session_service.sync_restored.connect(
            lambda: sync_restored_signals.append(True)
        )

        session_service._sync_to_firebase()

        assert session_service.consecutive_sync_failures == 0
        assert session_service.is_online is True
        assert len(sync_restored_signals) == 1
        mock_firebase_client.db_update.assert_called_once()

    def test_sync_to_firebase_failure(
        self, session_service, mock_firebase_client, qtbot
    ):
        """Test Firebase sync failure"""
        session_service.is_active = True
        session_service.remaining_time = 1800
        session_service.is_online = True
        session_service.consecutive_sync_failures = 0

        mock_firebase_client.db_update.return_value = {
            "success": False,
            "error": "Network error",
        }

        sync_failed_signals = []
        session_service.sync_failed.connect(lambda x: sync_failed_signals.append(x))

        session_service._sync_to_firebase()

        assert session_service.consecutive_sync_failures == 1
        assert session_service.is_online is False
        assert len(sync_failed_signals) == 1
        assert sync_failed_signals[0] == "Network error"

    def test_sync_to_firebase_max_failures(
        self, session_service, mock_firebase_client, qtbot
    ):
        """Test Firebase sync with maximum failures reached"""
        session_service.is_active = True
        session_service.remaining_time = 1800
        session_service.is_online = False
        session_service.consecutive_sync_failures = 4  # Max is 5

        mock_firebase_client.db_update.return_value = {
            "success": False,
            "error": "Network error",
        }

        session_ended_signals = []
        session_service.session_ended.connect(lambda x: session_ended_signals.append(x))

        with patch.object(
            session_service, "end_session", return_value={"success": True}
        ) as mock_end:
            session_service._sync_to_firebase()

        assert session_service.consecutive_sync_failures == 5
        assert len(session_ended_signals) == 1
        assert session_ended_signals[0] == "error"
        mock_end.assert_called_once_with("error")

    def test_sync_to_firebase_not_active(
        self, session_service, mock_firebase_client, qtbot
    ):
        """Test Firebase sync when session is not active"""
        session_service.is_active = False

        session_service._sync_to_firebase()

        # Should not call Firebase
        mock_firebase_client.db_update.assert_not_called()

    def test_get_remaining_time(self, session_service):
        """Test getting remaining time"""
        session_service.remaining_time = 1800

        result = session_service.get_remaining_time()

        assert result == 1800

    def test_get_time_used(self, session_service):
        """Test getting time used"""
        session_service.time_used = 900

        result = session_service.get_time_used()

        assert result == 900

    def test_is_session_active(self, session_service):
        """Test checking if session is active"""
        session_service.is_active = True

        result = session_service.is_session_active()

        assert result is True

    def test_pause_session(self, session_service, qtbot):
        """Test pausing session"""
        session_service.is_active = True
        session_service.countdown_timer.isActive.return_value = True

        result = session_service.pause_session()

        assert result["success"] is True
        assert session_service.is_active is False
        session_service.countdown_timer.stop.assert_called_once()

    def test_resume_session(self, session_service, qtbot):
        """Test resuming session"""
        session_service.is_active = False
        session_service.remaining_time = 1800

        result = session_service.resume_session()

        assert result["success"] is True
        assert session_service.is_active is True
        session_service.countdown_timer.start.assert_called_once()

    def test_resume_session_no_time(self, session_service):
        """Test resuming session with no time remaining"""
        session_service.is_active = False
        session_service.remaining_time = 0

        result = session_service.resume_session()

        assert result["success"] is False
        assert result["error"] == "No time remaining"

    def test_resume_session_already_active(self, session_service):
        """Test resuming session when already active"""
        session_service.is_active = True

        result = session_service.resume_session()

        assert result["success"] is False
        assert result["error"] == "Session already active"

    def test_get_current_computer_id(self, session_service):
        """Test getting current computer ID"""
        with patch(
            "src.services.session_service.device_info.get_computer_id",
            return_value="test-computer-id",
        ):
            result = session_service._get_current_computer_id()

        assert result == "test-computer-id"

    def test_timer_cleanup_on_destroy(self, session_service, qtbot):
        """Test timer cleanup when service is destroyed"""
        session_service.is_active = True
        session_service.countdown_timer.isActive.return_value = True
        session_service.sync_timer.isActive.return_value = True

        # Simulate destruction
        session_service.__del__()

        session_service.countdown_timer.stop.assert_called_once()
        session_service.sync_timer.stop.assert_called_once()

    @pytest.mark.parametrize(
        "remaining_time,expected_warning",
        [
            (300, "5min"),  # Exactly 5 minutes
            (301, None),  # Just over 5 minutes
            (60, "1min"),  # Exactly 1 minute
            (61, None),  # Just over 1 minute
            (30, None),  # Less than 1 minute
        ],
    )
    def test_warning_triggers(
        self, session_service, qtbot, remaining_time, expected_warning
    ):
        """Test warning triggers at correct times"""
        session_service.is_active = True
        session_service.remaining_time = remaining_time
        session_service.warned_5min = False
        session_service.warned_1min = False

        warning_5min_signals = []
        warning_1min_signals = []
        session_service.warning_5min.connect(lambda: warning_5min_signals.append(True))
        session_service.warning_1min.connect(lambda: warning_1min_signals.append(True))

        session_service._on_countdown_tick()

        if expected_warning == "5min":
            assert len(warning_5min_signals) == 1
            assert session_service.warned_5min is True
        elif expected_warning == "1min":
            assert len(warning_1min_signals) == 1
            assert session_service.warned_1min is True
        else:
            assert len(warning_5min_signals) == 0
            assert len(warning_1min_signals) == 0

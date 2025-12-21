"""
Tests for session_manager.py - Session Manager
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtCore import QObject


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def mock_firebase():
    """Create mock Firebase client"""
    firebase = Mock()
    firebase.set_data.return_value = {"success": True}
    firebase.get_data.return_value = {"success": True, "data": {"remainingTime": 3600}}
    firebase.update_data.return_value = {"success": True}
    return firebase


@pytest.fixture
def session_manager(qapp, mock_firebase):
    """Create SessionManager instance"""
    from services.session_manager import SessionManager
    
    manager = SessionManager(mock_firebase, "test-user-123")
    yield manager
    
    # Cleanup
    manager.sync_timer.stop()


# =============================================================================
# Test SessionManager initialization
# =============================================================================
class TestSessionManagerInit:
    """Tests for SessionManager initialization"""

    def test_stores_firebase_client(self, session_manager, mock_firebase):
        """Test manager stores firebase client"""
        assert session_manager.firebase == mock_firebase

    def test_stores_user_id(self, session_manager):
        """Test manager stores user ID"""
        assert session_manager.user_id == "test-user-123"

    def test_session_id_is_none_initially(self, session_manager):
        """Test session_id is None initially"""
        assert session_manager.session_id is None

    def test_is_active_is_false_initially(self, session_manager):
        """Test is_active is False initially"""
        assert session_manager.is_active is False

    def test_cached_remaining_time_is_zero_initially(self, session_manager):
        """Test cached_remaining_time is 0 initially"""
        assert session_manager.cached_remaining_time == 0

    def test_has_sync_timer(self, session_manager):
        """Test manager has sync timer"""
        assert session_manager.sync_timer is not None

    def test_sync_timer_interval_is_10_seconds(self, session_manager):
        """Test sync timer interval is 10 seconds"""
        assert session_manager.sync_timer.interval() == 10000

    def test_inherits_from_qobject(self, session_manager):
        """Test manager inherits from QObject"""
        assert isinstance(session_manager, QObject)


# =============================================================================
# Test signals
# =============================================================================
class TestSessionManagerSignals:
    """Tests for SessionManager signals"""

    def test_has_time_updated_signal(self, session_manager):
        """Test manager has time_updated signal"""
        assert hasattr(session_manager, "time_updated")

    def test_has_time_expired_signal(self, session_manager):
        """Test manager has time_expired signal"""
        assert hasattr(session_manager, "time_expired")

    def test_has_sync_failed_signal(self, session_manager):
        """Test manager has sync_failed signal"""
        assert hasattr(session_manager, "sync_failed")


# =============================================================================
# Test start_session
# =============================================================================
class TestStartSession:
    """Tests for start_session method"""

    def test_start_session_creates_session_id(self, session_manager):
        """Test start_session creates a session ID"""
        result = session_manager.start_session()
        
        assert session_manager.session_id is not None
        assert len(session_manager.session_id) > 0

    def test_start_session_sets_start_time(self, session_manager):
        """Test start_session sets start time"""
        session_manager.start_session()
        
        assert session_manager.start_time is not None
        assert session_manager.start_time > 0

    def test_start_session_sets_is_active_true(self, session_manager):
        """Test start_session sets is_active to True"""
        session_manager.start_session()
        
        assert session_manager.is_active is True

    def test_start_session_starts_sync_timer(self, session_manager):
        """Test start_session starts the sync timer"""
        session_manager.start_session()
        
        assert session_manager.sync_timer.isActive()

    def test_start_session_calls_firebase_set_data(self, session_manager, mock_firebase):
        """Test start_session calls Firebase set_data"""
        session_manager.start_session()
        
        mock_firebase.set_data.assert_called_once()
        call_args = mock_firebase.set_data.call_args
        
        # First arg should be session path
        assert "sessions/" in call_args[0][0]

    def test_start_session_returns_true_on_success(self, session_manager):
        """Test start_session returns True on success"""
        result = session_manager.start_session()
        
        assert result is True

    def test_start_session_returns_false_on_firebase_failure(self, session_manager, mock_firebase):
        """Test start_session returns False when Firebase fails"""
        mock_firebase.set_data.return_value = {"success": False}
        
        result = session_manager.start_session()
        
        assert result is False

    def test_start_session_emits_sync_failed_on_error(self, session_manager, mock_firebase):
        """Test start_session emits sync_failed signal on error"""
        mock_firebase.set_data.side_effect = Exception("Connection error")
        
        signal_received = []
        session_manager.sync_failed.connect(lambda msg: signal_received.append(msg))
        
        session_manager.start_session()
        
        assert len(signal_received) == 1
        assert "Connection error" in signal_received[0]


# =============================================================================
# Test sync_session_time
# =============================================================================
class TestSyncSessionTime:
    """Tests for sync_session_time method"""

    def test_sync_does_nothing_when_not_active(self, session_manager, mock_firebase):
        """Test sync returns early when not active"""
        session_manager.is_active = False
        
        session_manager.sync_session_time()
        
        # update_data should not be called
        mock_firebase.update_data.assert_not_called()

    def test_sync_updates_session_data(self, session_manager, mock_firebase):
        """Test sync updates session data in Firebase"""
        session_manager.start_session()
        mock_firebase.reset_mock()
        
        session_manager.sync_session_time()
        
        # Should call update_data for session
        assert mock_firebase.update_data.called

    def test_sync_emits_time_updated_signal(self, session_manager, mock_firebase):
        """Test sync emits time_updated signal"""
        session_manager.start_session()
        
        signal_received = []
        session_manager.time_updated.connect(lambda t: signal_received.append(t))
        
        session_manager.sync_session_time()
        
        assert len(signal_received) == 1

    def test_sync_handles_time_expired(self, session_manager, mock_firebase):
        """Test sync handles when time expires"""
        mock_firebase.get_data.return_value = {"success": True, "data": {"remainingTime": 0}}
        
        session_manager.start_session()
        
        signal_received = []
        session_manager.time_expired.connect(lambda: signal_received.append(True))
        
        session_manager.sync_session_time()
        
        # Should emit time_expired
        assert len(signal_received) == 1

    def test_sync_emits_sync_failed_on_error(self, session_manager, mock_firebase):
        """Test sync emits sync_failed on error"""
        session_manager.start_session()
        mock_firebase.update_data.return_value = {"success": False}
        
        signal_received = []
        session_manager.sync_failed.connect(lambda msg: signal_received.append(msg))
        
        session_manager.sync_session_time()
        
        assert len(signal_received) == 1


# =============================================================================
# Test handle_time_expired
# =============================================================================
class TestHandleTimeExpired:
    """Tests for handle_time_expired method"""

    def test_stops_session(self, session_manager):
        """Test handle_time_expired stops the session"""
        session_manager.start_session()
        
        session_manager.handle_time_expired()
        
        assert session_manager.is_active is False

    def test_emits_time_expired_signal(self, session_manager):
        """Test handle_time_expired emits time_expired signal"""
        session_manager.start_session()
        
        signal_received = []
        session_manager.time_expired.connect(lambda: signal_received.append(True))
        
        session_manager.handle_time_expired()
        
        assert len(signal_received) == 1


# =============================================================================
# Test stop_session
# =============================================================================
class TestStopSession:
    """Tests for stop_session method"""

    def test_stop_does_nothing_when_not_active(self, session_manager, mock_firebase):
        """Test stop returns early when not active"""
        session_manager.is_active = False
        
        session_manager.stop_session()
        
        # update_data should not be called
        mock_firebase.update_data.assert_not_called()

    def test_stop_sets_is_active_false(self, session_manager):
        """Test stop sets is_active to False"""
        session_manager.start_session()
        
        session_manager.stop_session()
        
        assert session_manager.is_active is False

    def test_stop_stops_sync_timer(self, session_manager):
        """Test stop stops the sync timer"""
        session_manager.start_session()
        
        session_manager.stop_session()
        
        assert not session_manager.sync_timer.isActive()

    def test_stop_updates_session_as_inactive(self, session_manager, mock_firebase):
        """Test stop marks session as inactive in Firebase"""
        session_manager.start_session()
        mock_firebase.reset_mock()
        
        session_manager.stop_session()
        
        # Check update_data was called with isActive: False
        assert mock_firebase.update_data.called
        call_args_list = mock_firebase.update_data.call_args_list
        
        # Find the session update call
        session_update_found = False
        for call in call_args_list:
            if "sessions/" in call[0][0]:
                data = call[0][1]
                if data.get("isActive") is False:
                    session_update_found = True
                    break
        
        assert session_update_found

    def test_stop_handles_exception_gracefully(self, session_manager, mock_firebase):
        """Test stop handles exceptions gracefully"""
        session_manager.start_session()
        mock_firebase.update_data.side_effect = Exception("Network error")
        
        # Should not raise
        session_manager.stop_session()
        
        assert session_manager.is_active is False


# =============================================================================
# Test get_remaining_time
# =============================================================================
class TestGetRemainingTime:
    """Tests for get_remaining_time method"""

    def test_returns_cached_value_on_error(self, session_manager, mock_firebase):
        """Test returns cached value when Firebase fails"""
        session_manager.cached_remaining_time = 1800
        mock_firebase.get_data.side_effect = Exception("Network error")
        
        result = session_manager.get_remaining_time()
        
        assert result == 1800

    def test_returns_fresh_data_on_success(self, session_manager, mock_firebase):
        """Test returns fresh data from Firebase"""
        mock_firebase.get_data.return_value = {"success": True, "data": {"remainingTime": 2400}}
        
        result = session_manager.get_remaining_time()
        
        assert result == 2400

    def test_updates_cache_on_success(self, session_manager, mock_firebase):
        """Test updates cached value on success"""
        mock_firebase.get_data.return_value = {"success": True, "data": {"remainingTime": 2400}}
        
        session_manager.get_remaining_time()
        
        assert session_manager.cached_remaining_time == 2400

    def test_returns_zero_when_no_remaining_time(self, session_manager, mock_firebase):
        """Test returns 0 when remainingTime not in data"""
        mock_firebase.get_data.return_value = {"success": True, "data": {}}
        
        result = session_manager.get_remaining_time()
        
        assert result == 0


# =============================================================================
# Test session data structure
# =============================================================================
class TestSessionDataStructure:
    """Tests for session data structure sent to Firebase"""

    def test_session_data_includes_user_id(self, session_manager, mock_firebase):
        """Test session data includes userId"""
        session_manager.start_session()
        
        call_args = mock_firebase.set_data.call_args
        session_data = call_args[0][1]
        
        assert session_data["userId"] == "test-user-123"

    def test_session_data_includes_device_id(self, session_manager, mock_firebase):
        """Test session data includes deviceId"""
        with patch("services.session_manager.get_device_id", return_value="device-123"):
            from services.session_manager import SessionManager
            
            manager = SessionManager(mock_firebase, "test-user")
            manager.start_session()
            
            call_args = mock_firebase.set_data.call_args
            session_data = call_args[0][1]
            
            assert "deviceId" in session_data

    def test_session_data_includes_start_time(self, session_manager, mock_firebase):
        """Test session data includes startTime"""
        session_manager.start_session()
        
        call_args = mock_firebase.set_data.call_args
        session_data = call_args[0][1]
        
        assert "startTime" in session_data
        assert session_data["startTime"] > 0

    def test_session_data_includes_is_active(self, session_manager, mock_firebase):
        """Test session data includes isActive"""
        session_manager.start_session()
        
        call_args = mock_firebase.set_data.call_args
        session_data = call_args[0][1]
        
        assert session_data["isActive"] is True




"""
Tests for chat_service.py - Client-side message handling
Tests message fetching, marking as read, caching, and listening functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time
import threading

from services.chat_service import ChatService


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def mock_firebase():
    """Create a mock FirebaseClient"""
    firebase = Mock()
    return firebase


@pytest.fixture
def chat_service(mock_firebase, qapp):
    """Create a ChatService instance with mocked dependencies"""
    with patch("services.chat_service.get_logger") as mock_logger:
        mock_logger.return_value = Mock()
        service = ChatService(
            firebase_client=mock_firebase,
            user_id="user123",
            org_id="org456"
        )
        return service


@pytest.fixture
def sample_messages():
    """Sample message data for testing"""
    return {
        "msg1": {
            "toUserId": "user123",
            "fromAdmin": "admin1",
            "content": "Hello user!",
            "timestamp": "2024-01-15T10:00:00",
            "read": False
        },
        "msg2": {
            "toUserId": "user123",
            "fromAdmin": "admin2",
            "content": "Second message",
            "timestamp": "2024-01-15T11:00:00",
            "read": False
        },
        "msg3": {
            "toUserId": "other_user",
            "fromAdmin": "admin1",
            "content": "Not for this user",
            "timestamp": "2024-01-15T12:00:00",
            "read": False
        },
        "msg4": {
            "toUserId": "user123",
            "fromAdmin": "admin1",
            "content": "Already read",
            "timestamp": "2024-01-15T09:00:00",
            "read": True
        }
    }


# =============================================================================
# Initialization tests
# =============================================================================
class TestChatServiceInit:
    """Tests for ChatService initialization"""

    def test_initialization_with_user_id(self, mock_firebase, qapp):
        """Test service stores user ID"""
        with patch("services.chat_service.get_logger"):
            service = ChatService(mock_firebase, "user123", "org456")
            assert service.user_id == "user123"

    def test_initialization_with_org_id(self, mock_firebase, qapp):
        """Test service stores org ID"""
        with patch("services.chat_service.get_logger"):
            service = ChatService(mock_firebase, "user123", "org456")
            assert service.org_id == "org456"

    def test_initialization_with_firebase_client(self, mock_firebase, qapp):
        """Test service stores firebase client"""
        with patch("services.chat_service.get_logger"):
            service = ChatService(mock_firebase, "user123", "org456")
            assert service.firebase == mock_firebase

    def test_initial_listening_state(self, chat_service):
        """Test initial listening state is False"""
        assert chat_service.is_listening is False

    def test_initial_poll_interval(self, chat_service):
        """Test initial poll interval is base interval"""
        assert chat_service.current_poll_interval == chat_service.base_poll_interval

    def test_initial_cache_state(self, chat_service):
        """Test initial cache is empty"""
        assert chat_service.cached_messages == []
        assert chat_service.cache_timestamp is None


# =============================================================================
# get_unread_messages tests
# =============================================================================
class TestGetUnreadMessages:
    """Tests for get_unread_messages method"""

    def test_get_unread_messages_success(self, chat_service, mock_firebase, sample_messages):
        """Test successful retrieval of unread messages"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": sample_messages
        }

        result = chat_service.get_unread_messages(use_cache=False)

        assert result["success"] is True
        # Should only include user123's unread messages (msg1, msg2)
        assert len(result["messages"]) == 2

    def test_get_unread_messages_filters_by_user(self, chat_service, mock_firebase, sample_messages):
        """Test messages are filtered by user ID"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": sample_messages
        }

        result = chat_service.get_unread_messages(use_cache=False)

        for message in result["messages"]:
            assert message["toUserId"] == "user123"

    def test_get_unread_messages_excludes_read(self, chat_service, mock_firebase, sample_messages):
        """Test read messages are excluded"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": sample_messages
        }

        result = chat_service.get_unread_messages(use_cache=False)

        for message in result["messages"]:
            assert message.get("read", False) is False

    def test_get_unread_messages_sorted_by_timestamp(self, chat_service, mock_firebase, sample_messages):
        """Test messages are sorted by timestamp"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": sample_messages
        }

        result = chat_service.get_unread_messages(use_cache=False)

        # msg1 (10:00) should come before msg2 (11:00)
        timestamps = [m["timestamp"] for m in result["messages"]]
        assert timestamps == sorted(timestamps)

    def test_get_unread_messages_includes_id(self, chat_service, mock_firebase, sample_messages):
        """Test each message has ID added"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": sample_messages
        }

        result = chat_service.get_unread_messages(use_cache=False)

        for message in result["messages"]:
            assert "id" in message

    def test_get_unread_messages_empty_data(self, chat_service, mock_firebase):
        """Test with no messages"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": None
        }

        result = chat_service.get_unread_messages(use_cache=False)

        assert result["success"] is True
        assert result["messages"] == []

    def test_get_unread_messages_failure(self, chat_service, mock_firebase):
        """Test handling of fetch failure"""
        mock_firebase.db_get.return_value = {
            "success": False,
            "error": "Network error"
        }

        result = chat_service.get_unread_messages(use_cache=False)

        assert result["success"] is False
        assert result["error"] == "Network error"
        assert result["messages"] == []

    def test_get_unread_messages_uses_cache(self, chat_service, mock_firebase, sample_messages):
        """Test cache is used when valid"""
        # Prime the cache
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": sample_messages
        }
        chat_service.get_unread_messages(use_cache=False)
        mock_firebase.db_get.reset_mock()

        # Should use cache, not call Firebase
        result = chat_service.get_unread_messages(use_cache=True)

        mock_firebase.db_get.assert_not_called()
        assert result["success"] is True

    def test_get_unread_messages_bypasses_cache(self, chat_service, mock_firebase, sample_messages):
        """Test cache can be bypassed"""
        # Prime the cache
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": sample_messages
        }
        chat_service.get_unread_messages(use_cache=False)
        mock_firebase.db_get.reset_mock()

        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {}
        }

        # Should bypass cache
        result = chat_service.get_unread_messages(use_cache=False)

        mock_firebase.db_get.assert_called_once()


# =============================================================================
# mark_message_as_read tests
# =============================================================================
class TestMarkMessageAsRead:
    """Tests for mark_message_as_read method"""

    def test_mark_message_as_read_success(self, chat_service, mock_firebase):
        """Test successfully marking a message as read"""
        mock_firebase.db_set.return_value = {"success": True}

        result = chat_service.mark_message_as_read("msg123")

        assert result["success"] is True

    def test_mark_message_as_read_sets_read_flag(self, chat_service, mock_firebase):
        """Test read flag is set to True"""
        mock_firebase.db_set.return_value = {"success": True}

        chat_service.mark_message_as_read("msg123")

        # First call should set read to True
        mock_firebase.db_set.assert_any_call("messages/msg123/read", True)

    def test_mark_message_as_read_sets_timestamp(self, chat_service, mock_firebase):
        """Test readAt timestamp is set"""
        mock_firebase.db_set.return_value = {"success": True}

        chat_service.mark_message_as_read("msg123")

        # Second call should set readAt timestamp
        calls = mock_firebase.db_set.call_args_list
        assert len(calls) >= 2
        assert "readAt" in calls[1][0][0]

    def test_mark_message_as_read_failure(self, chat_service, mock_firebase):
        """Test handling of mark failure"""
        mock_firebase.db_set.return_value = {
            "success": False,
            "error": "Permission denied"
        }

        result = chat_service.mark_message_as_read("msg123")

        assert result["success"] is False
        assert result["error"] == "Permission denied"


# =============================================================================
# mark_all_messages_as_read tests
# =============================================================================
class TestMarkAllMessagesAsRead:
    """Tests for mark_all_messages_as_read method"""

    def test_mark_all_as_read_success(self, chat_service, mock_firebase, sample_messages):
        """Test marking all messages as read"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": sample_messages
        }
        mock_firebase.db_set.return_value = {"success": True}

        result = chat_service.mark_all_messages_as_read()

        assert result["success"] is True

    def test_mark_all_as_read_marks_each_message(self, chat_service, mock_firebase, sample_messages):
        """Test each unread message is marked"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": sample_messages
        }
        mock_firebase.db_set.return_value = {"success": True}

        chat_service.mark_all_messages_as_read()

        # Should have called db_set for each unread message (2 messages x 2 calls each)
        assert mock_firebase.db_set.call_count >= 2

    def test_mark_all_as_read_no_messages(self, chat_service, mock_firebase):
        """Test with no unread messages"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": None
        }

        result = chat_service.mark_all_messages_as_read()

        assert result["success"] is True

    def test_mark_all_as_read_failure_on_get(self, chat_service, mock_firebase):
        """Test handling of get failure"""
        mock_firebase.db_get.return_value = {
            "success": False,
            "error": "Database error"
        }

        result = chat_service.mark_all_messages_as_read()

        assert result["success"] is False


# =============================================================================
# update_last_seen tests
# =============================================================================
class TestUpdateLastSeen:
    """Tests for update_last_seen method"""

    def test_update_last_seen_success(self, chat_service, mock_firebase):
        """Test successful last seen update"""
        mock_firebase.db_set.return_value = {"success": True}

        result = chat_service.update_last_seen()

        assert result["success"] is True

    def test_update_last_seen_sets_timestamp(self, chat_service, mock_firebase):
        """Test last seen timestamp is set in database"""
        mock_firebase.db_set.return_value = {"success": True}

        chat_service.update_last_seen()

        mock_firebase.db_set.assert_called_once()
        call_args = mock_firebase.db_set.call_args
        assert "lastSeen" in call_args[0][0]

    def test_update_last_seen_debouncing(self, chat_service, mock_firebase):
        """Test debouncing prevents frequent updates"""
        mock_firebase.db_set.return_value = {"success": True}

        # First call should succeed
        result1 = chat_service.update_last_seen()
        assert result1["success"] is True

        # Second immediate call should be debounced
        result2 = chat_service.update_last_seen()
        assert result2.get("skipped") is True

        # Only one actual Firebase call
        assert mock_firebase.db_set.call_count == 1

    def test_update_last_seen_force_bypasses_debounce(self, chat_service, mock_firebase):
        """Test force=True bypasses debouncing"""
        mock_firebase.db_set.return_value = {"success": True}

        chat_service.update_last_seen()
        result = chat_service.update_last_seen(force=True)

        assert result["success"] is True
        assert mock_firebase.db_set.call_count == 2

    def test_update_last_seen_failure(self, chat_service, mock_firebase):
        """Test handling of update failure"""
        mock_firebase.db_set.return_value = {
            "success": False,
            "error": "Network error"
        }

        result = chat_service.update_last_seen(force=True)

        assert result["success"] is False
        assert result["error"] == "Network error"


# =============================================================================
# start_listening / stop_listening tests
# =============================================================================
class TestListening:
    """Tests for start_listening and stop_listening methods"""

    def test_start_listening_sets_flag(self, chat_service, mock_firebase):
        """Test start_listening sets is_listening flag"""
        mock_firebase.db_get.return_value = {"success": True, "data": None}
        mock_firebase.db_set.return_value = {"success": True}

        result = chat_service.start_listening()

        assert result is True
        assert chat_service.is_listening is True
        
        # Cleanup
        chat_service.stop_listening()

    def test_start_listening_already_listening(self, chat_service, mock_firebase):
        """Test start_listening when already listening returns False"""
        mock_firebase.db_get.return_value = {"success": True, "data": None}
        mock_firebase.db_set.return_value = {"success": True}

        chat_service.start_listening()
        result = chat_service.start_listening()

        assert result is False
        
        # Cleanup
        chat_service.stop_listening()

    def test_start_listening_creates_thread(self, chat_service, mock_firebase):
        """Test start_listening creates a listening thread"""
        mock_firebase.db_get.return_value = {"success": True, "data": None}
        mock_firebase.db_set.return_value = {"success": True}

        chat_service.start_listening()

        assert chat_service.listen_thread is not None
        assert chat_service.listen_thread.is_alive()
        
        # Cleanup
        chat_service.stop_listening()

    def test_stop_listening_sets_flag(self, chat_service, mock_firebase):
        """Test stop_listening clears is_listening flag"""
        mock_firebase.db_get.return_value = {"success": True, "data": None}
        mock_firebase.db_set.return_value = {"success": True}

        chat_service.start_listening()
        chat_service.stop_listening()

        assert chat_service.is_listening is False

    def test_stop_listening_when_not_listening(self, chat_service):
        """Test stop_listening when not listening does nothing"""
        chat_service.stop_listening()  # Should not raise


# =============================================================================
# is_user_active tests
# =============================================================================
class TestIsUserActive:
    """Tests for is_user_active method"""

    def test_is_user_active_recent(self, chat_service):
        """Test user is active if last seen within 5 minutes"""
        recent = datetime.now().isoformat()
        assert chat_service.is_user_active(recent) is True

    def test_is_user_active_old(self, chat_service):
        """Test user is inactive if last seen over 5 minutes ago"""
        old_time = (datetime.now() - timedelta(minutes=10)).isoformat()
        assert chat_service.is_user_active(old_time) is False

    def test_is_user_active_just_under_5_minutes(self, chat_service):
        """Test edge case just under 5 minutes"""
        # Use 4:59 to avoid timing precision issues
        four_min_59_sec = (datetime.now() - timedelta(minutes=4, seconds=59)).isoformat()
        assert chat_service.is_user_active(four_min_59_sec) is True

    def test_is_user_active_empty_string(self, chat_service):
        """Test empty last_seen returns False"""
        assert chat_service.is_user_active("") is False

    def test_is_user_active_none(self, chat_service):
        """Test None last_seen returns False"""
        assert chat_service.is_user_active(None) is False

    def test_is_user_active_invalid_format(self, chat_service):
        """Test invalid timestamp returns False"""
        assert chat_service.is_user_active("not-a-timestamp") is False

    def test_is_user_active_with_timezone(self, chat_service):
        """Test timestamp with UTC timezone marker"""
        recent = datetime.now().isoformat() + "Z"
        result = chat_service.is_user_active(recent)
        # Should handle Z suffix
        assert isinstance(result, bool)


# =============================================================================
# Cache tests
# =============================================================================
class TestCaching:
    """Tests for caching functionality"""

    def test_is_cache_valid_empty(self, chat_service):
        """Test empty cache is invalid"""
        assert chat_service._is_cache_valid() is False

    def test_is_cache_valid_fresh(self, chat_service):
        """Test fresh cache is valid"""
        chat_service.cached_messages = [{"id": "msg1"}]
        chat_service.cache_timestamp = datetime.now()

        assert chat_service._is_cache_valid() is True

    def test_is_cache_valid_stale(self, chat_service):
        """Test stale cache is invalid"""
        chat_service.cached_messages = [{"id": "msg1"}]
        chat_service.cache_timestamp = datetime.now() - timedelta(seconds=15)

        assert chat_service._is_cache_valid() is False

    def test_update_cache(self, chat_service):
        """Test cache update"""
        messages = [{"id": "msg1"}, {"id": "msg2"}]
        chat_service._update_cache(messages)

        assert chat_service.cached_messages == messages
        assert chat_service.cache_timestamp is not None

    def test_invalidate_cache(self, chat_service):
        """Test cache invalidation"""
        chat_service.cached_messages = [{"id": "msg1"}]
        chat_service.cache_timestamp = datetime.now()

        chat_service.invalidate_cache()

        assert chat_service.cached_messages == []
        assert chat_service.cache_timestamp is None


# =============================================================================
# cleanup tests
# =============================================================================
class TestCleanup:
    """Tests for cleanup method"""

    def test_cleanup_stops_listening(self, chat_service, mock_firebase):
        """Test cleanup stops listening"""
        mock_firebase.db_get.return_value = {"success": True, "data": None}
        mock_firebase.db_set.return_value = {"success": True}

        chat_service.start_listening()
        chat_service.cleanup()

        assert chat_service.is_listening is False

    def test_cleanup_when_not_listening(self, chat_service):
        """Test cleanup when not listening doesn't raise"""
        chat_service.cleanup()  # Should not raise


# =============================================================================
# Signal emission tests
# =============================================================================
class TestSignals:
    """Tests for signal emission"""

    def test_messages_received_signal_exists(self, chat_service):
        """Test messages_received signal exists"""
        assert hasattr(chat_service, "messages_received")

    def test_messages_received_signal_can_connect(self, chat_service):
        """Test signal can be connected to a slot"""
        callback = Mock()
        chat_service.messages_received.connect(callback)
        # Should not raise


# =============================================================================
# Polling configuration tests
# =============================================================================
class TestPollingConfiguration:
    """Tests for smart polling configuration"""

    def test_base_poll_interval_default(self, chat_service):
        """Test default base poll interval"""
        assert chat_service.base_poll_interval == 5

    def test_max_poll_interval_default(self, chat_service):
        """Test default max poll interval"""
        assert chat_service.max_poll_interval == 60

    def test_initial_consecutive_empty_polls(self, chat_service):
        """Test initial empty poll counter is 0"""
        assert chat_service.consecutive_empty_polls == 0

    def test_max_empty_polls_threshold(self, chat_service):
        """Test max empty polls before interval increase"""
        assert chat_service.max_empty_polls == 3


# =============================================================================
# Additional Edge Case Tests
# =============================================================================
class TestEdgeCases:
    """Tests for edge cases and error paths"""

    def test_mark_message_read_timestamp_failure(self, chat_service, mock_firebase):
        """Test mark_message_as_read when setting timestamp fails but read flag succeeds"""
        # First call sets read flag (succeeds), second call sets readAt (fails)
        call_count = [0]
        def db_set_side_effect(path, value=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return {"success": True}  # read flag
            return {"success": False, "error": "Timestamp update failed"}  # readAt
        
        mock_firebase.db_set.side_effect = db_set_side_effect
        
        result = chat_service.mark_message_as_read("msg-123")
        
        # Should still return success because read flag was set
        assert result["success"] is True

    def test_smart_polling_initial_interval(self, chat_service):
        """Test initial polling interval matches base"""
        assert chat_service.current_poll_interval == chat_service.base_poll_interval

    def test_smart_polling_consecutive_empty_initial(self, chat_service):
        """Test consecutive empty polls starts at 0"""
        assert chat_service.consecutive_empty_polls == 0

    def test_is_user_active_with_recent_timestamp(self, chat_service):
        """Test is_user_active returns True for recent activity"""
        recent_time = datetime.now().isoformat()
        
        result = chat_service.is_user_active(recent_time)
        
        assert result is True

    def test_is_user_active_with_old_timestamp(self, chat_service):
        """Test is_user_active returns False for old activity"""
        old_time = (datetime.now() - timedelta(minutes=10)).isoformat()
        
        result = chat_service.is_user_active(old_time)
        
        assert result is False

    def test_is_user_active_with_empty_timestamp(self, chat_service):
        """Test is_user_active returns False for empty timestamp"""
        result = chat_service.is_user_active("")
        
        assert result is False

    def test_is_user_active_with_none_timestamp(self, chat_service):
        """Test is_user_active returns False for None timestamp"""
        result = chat_service.is_user_active(None)
        
        assert result is False


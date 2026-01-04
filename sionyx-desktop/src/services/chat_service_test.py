"""
Tests for chat_service.py - Client-side message handling
Tests message fetching, marking as read, caching, and SSE listening functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

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

    def test_initial_stream_listener_is_none(self, chat_service):
        """Test initial SSE stream listener is None"""
        assert chat_service._stream_listener is None

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

    def test_start_listening_creates_stream_listener(self, chat_service, mock_firebase):
        """Test start_listening creates an SSE stream listener"""
        # Mock db_listen to return a mock StreamListener
        mock_listener = Mock()
        mock_firebase.db_listen.return_value = mock_listener

        chat_service.start_listening()

        assert chat_service._stream_listener is not None
        mock_firebase.db_listen.assert_called_once_with(
            path="messages",
            callback=chat_service._on_stream_event,
            error_callback=chat_service._on_stream_error,
        )
        
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

    def test_cache_used_when_sse_listening(self, chat_service, mock_firebase):
        """Test cache is used when SSE is actively listening"""
        # Simulate SSE is active
        chat_service.is_listening = True
        chat_service.cached_messages = [{"id": "msg1", "toUserId": "user123"}]
        chat_service.cache_timestamp = datetime.now()

        result = chat_service.get_unread_messages(use_cache=True)

        # Should return cached messages without calling Firebase
        mock_firebase.db_get.assert_not_called()
        assert result["success"] is True
        assert result["messages"] == chat_service.cached_messages

    def test_cache_used_when_fresh(self, chat_service, mock_firebase):
        """Test recent cache is used even when not listening"""
        chat_service.is_listening = False
        chat_service.cached_messages = [{"id": "msg1"}]
        chat_service.cache_timestamp = datetime.now()  # Fresh cache

        result = chat_service.get_unread_messages(use_cache=True)

        mock_firebase.db_get.assert_not_called()
        assert result["success"] is True


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
# SSE configuration tests
# =============================================================================
class TestSSEConfiguration:
    """Tests for SSE streaming configuration"""

    def test_last_seen_debounce_seconds_default(self, chat_service):
        """Test default last seen debounce interval"""
        assert chat_service.last_seen_debounce_seconds == 60

    def test_initial_message_callback_is_none(self, chat_service):
        """Test initial message callback is None"""
        assert chat_service._message_callback is None

    def test_initial_last_seen_update_time_is_none(self, chat_service):
        """Test initial last seen update time is None"""
        assert chat_service.last_seen_update_time is None


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


# =============================================================================
# SSE Event Handling Tests
# =============================================================================
class TestSSEEventHandling:
    """Tests for SSE stream event handling"""

    def test_on_stream_event_put_with_data(self, chat_service):
        """Test handling of 'put' event with message data"""
        messages_data = {
            "msg1": {
                "toUserId": "user123",
                "content": "Hello",
                "timestamp": "2024-01-15T10:00:00",
                "read": False
            }
        }
        data = {"path": "/", "data": messages_data}
        
        # Connect a signal receiver
        received = []
        chat_service.messages_received.connect(lambda r: received.append(r))
        
        chat_service._on_stream_event("put", data)
        
        assert len(received) == 1
        assert received[0]["success"] is True
        assert len(received[0]["messages"]) == 1

    def test_on_stream_event_put_with_empty_data(self, chat_service):
        """Test handling of 'put' event with no data"""
        received = []
        chat_service.messages_received.connect(lambda r: received.append(r))
        
        chat_service._on_stream_event("put", None)
        
        assert len(received) == 1
        assert received[0]["messages"] == []

    def test_on_stream_event_keep_alive(self, chat_service, mock_firebase):
        """Test keep-alive event triggers last seen update"""
        mock_firebase.db_set.return_value = {"success": True}
        
        chat_service._on_stream_event("keep-alive", None)
        
        # Should have called update_last_seen
        mock_firebase.db_set.assert_called()

    def test_on_stream_error_logs_error(self, chat_service):
        """Test stream error is handled gracefully"""
        # Should not raise
        chat_service._on_stream_error("Connection lost")

    def test_extract_user_messages_filters_correctly(self, chat_service, sample_messages):
        """Test _extract_user_messages filters for current user's unread messages"""
        result = chat_service._extract_user_messages(sample_messages)
        
        # Should only have msg1 and msg2 (user123's unread messages)
        assert len(result) == 2
        for msg in result:
            assert msg["toUserId"] == "user123"
            assert msg.get("read", False) is False

    def test_extract_user_messages_with_none(self, chat_service):
        """Test _extract_user_messages handles None"""
        result = chat_service._extract_user_messages(None)
        assert result == []

    def test_extract_user_messages_with_empty_dict(self, chat_service):
        """Test _extract_user_messages handles empty dict"""
        result = chat_service._extract_user_messages({})
        assert result == []

    def test_emit_messages_calls_callback(self, chat_service):
        """Test _emit_messages calls legacy callback"""
        callback = Mock()
        chat_service._message_callback = callback
        
        chat_service._emit_messages([{"id": "msg1"}])
        
        callback.assert_called_once()
        assert callback.call_args[0][0]["success"] is True

    def test_on_stream_event_cancel_event(self, chat_service):
        """Test cancel event is logged and returns"""
        # Should not raise and should not emit messages
        received = []
        chat_service.messages_received.connect(lambda result: received.append(result))

        chat_service._on_stream_event("cancel", None)

        # No messages should be emitted for cancel
        assert len(received) == 0

    def test_on_stream_event_auth_revoked_event(self, chat_service):
        """Test auth_revoked event is handled"""
        received = []
        chat_service.messages_received.connect(lambda result: received.append(result))

        chat_service._on_stream_event("auth_revoked", None)

        # No messages should be emitted for auth_revoked
        assert len(received) == 0

    def test_on_stream_event_unknown_event_type(self, chat_service):
        """Test unknown event types are ignored"""
        received = []
        chat_service.messages_received.connect(lambda result: received.append(result))

        chat_service._on_stream_event("unknown_event", {"some": "data"})

        # No messages should be emitted for unknown events
        assert len(received) == 0

    def test_on_stream_event_patch_event(self, chat_service, mock_firebase, sample_messages):
        """Test patch event triggers full refresh"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": sample_messages
        }
        mock_firebase.db_set.return_value = {"success": True}

        received = []
        chat_service.messages_received.connect(lambda result: received.append(result))

        # Patch events trigger a full refresh
        chat_service._on_stream_event("patch", {"path": "/msg1/read", "data": True})

        # Should have fetched full messages
        mock_firebase.db_get.assert_called()
        assert len(received) == 1

    def test_on_stream_event_put_non_root_path(self, chat_service, mock_firebase, sample_messages):
        """Test put event with non-root path triggers refresh"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": sample_messages
        }
        mock_firebase.db_set.return_value = {"success": True}

        received = []
        chat_service.messages_received.connect(lambda result: received.append(result))

        # Put on specific path (not "/") also triggers refresh
        chat_service._on_stream_event("put", {"path": "/msg1", "data": {"content": "updated"}})

        # Should have fetched full messages
        mock_firebase.db_get.assert_called()

    def test_on_stream_event_exception_handling(self, chat_service):
        """Test exception in event processing is caught"""
        # Force an exception by passing bad data type
        with patch.object(chat_service, '_update_cache', side_effect=Exception("Cache error")):
            # Should not raise
            chat_service._on_stream_event("put", {"path": "/", "data": {"msg1": {"toUserId": "user123"}}})

    def test_emit_messages_callback_exception(self, chat_service):
        """Test exception in callback doesn't crash emit"""
        callback = Mock(side_effect=Exception("Callback error"))
        chat_service._message_callback = callback

        # Should not raise
        chat_service._emit_messages([{"id": "msg1"}])

        # Callback was called even though it raised
        callback.assert_called_once()

    def test_extract_user_messages_skips_non_dict_items(self, chat_service):
        """Test _extract_user_messages skips non-dict message items"""
        messages = {
            "msg1": {"toUserId": "user123", "content": "valid"},  # Valid
            "msg2": "not a dict",  # Invalid - should skip
            "msg3": None,  # Invalid - should skip
            "msg4": ["list", "not", "dict"],  # Invalid - should skip
            "msg5": {"toUserId": "user123", "content": "also valid"},  # Valid
        }

        result = chat_service._extract_user_messages(messages)

        # Only valid dict items should be included
        assert len(result) == 2
        assert all(isinstance(m, dict) for m in result)

    def test_on_stream_event_patch_when_get_fails(self, chat_service, mock_firebase):
        """Test patch event when get_unread_messages fails"""
        mock_firebase.db_get.return_value = {"success": False, "error": "Network error"}
        mock_firebase.db_set.return_value = {"success": True}

        received = []
        chat_service.messages_received.connect(lambda result: received.append(result))

        chat_service._on_stream_event("patch", {"path": "/msg1", "data": True})

        # Should have tried to get but not emitted due to failure
        mock_firebase.db_get.assert_called()
        # No successful emit on failed fetch
        assert len(received) == 0


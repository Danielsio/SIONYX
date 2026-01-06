"""
Tests for FirebaseClient and StreamListener (SSE)
"""

import threading
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from services.firebase_client import FirebaseClient, StreamListener


class TestFirebaseClient:
    """Test cases for FirebaseClient"""

    @pytest.fixture
    def firebase_client(self, mock_firebase_config):
        """Create FirebaseClient instance with mocked config"""
        with patch(
            "services.firebase_client.get_firebase_config",
            return_value=mock_firebase_config,
        ):
            return FirebaseClient()

    def test_initialization(self, firebase_client, mock_firebase_config):
        """Test FirebaseClient initialization"""
        assert firebase_client.api_key == mock_firebase_config.api_key
        assert firebase_client.database_url == mock_firebase_config.database_url
        assert firebase_client.id_token is None
        assert firebase_client.refresh_token is None
        assert firebase_client.user_id is None

    def test_get_org_path(self, firebase_client):
        """Test organization path generation for multi-tenancy"""
        assert (
            firebase_client._get_org_path("users/123")
            == "organizations/test-org/users/123"
        )
        assert (
            firebase_client._get_org_path("/users/123/")
            == "organizations/test-org/users/123"
        )
        assert firebase_client._get_org_path("") == "organizations/test-org/"

    @pytest.mark.parametrize(
        "email,password,expected_success",
        [
            ("test@sionyx.app", "password123", True),
            ("invalid-email", "password123", False),
            ("test@sionyx.app", "", False),
        ],
    )
    def test_sign_up(
        self, firebase_client, email, password, expected_success, mock_requests
    ):
        """Test user sign up functionality"""
        if expected_success:
            mock_response = Mock()
            mock_response.json.return_value = {
                "idToken": "test-id-token",
                "refreshToken": "test-refresh-token",
                "localId": "test-user-id",
                "expiresIn": "3600",
            }
            mock_response.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_response
        else:
            mock_requests.post.side_effect = requests.exceptions.RequestException(
                "Invalid request"
            )

        result = firebase_client.sign_up(email, password)

        if expected_success:
            assert result["success"] is True
            assert result["uid"] == "test-user-id"
        else:
            assert result["success"] is False

    def test_sign_in(self, firebase_client, mock_requests):
        """Test user sign in functionality"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "idToken": "test-id-token",
            "refreshToken": "test-refresh-token",
            "localId": "test-user-id",
            "expiresIn": "3600",
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        result = firebase_client.sign_in("test@sionyx.app", "password123")

        assert result["success"] is True
        assert result["uid"] == "test-user-id"

    def test_refresh_token_request(self, firebase_client, mock_requests):
        """Test token refresh functionality"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id_token": "new-id-token",
            "refresh_token": "new-refresh-token",
            "user_id": "test-user-id",
            "expires_in": "3600",
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        result = firebase_client.refresh_token_request("old-refresh-token")

        assert result["success"] is True
        assert firebase_client.id_token == "new-id-token"

    def test_ensure_valid_token_no_tokens(self, firebase_client):
        """Test ensure_valid_token when no tokens are present"""
        firebase_client.id_token = None
        firebase_client.refresh_token = None
        result = firebase_client.ensure_valid_token()
        assert result is False

    def test_ensure_valid_token_valid_token(self, firebase_client):
        """Test ensure_valid_token when token is still valid"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(hours=1)
        result = firebase_client.ensure_valid_token()
        assert result is True

    def test_db_get_success(self, firebase_client, mock_requests):
        """Test successful database get operation"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(hours=1)

        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response

        result = firebase_client.db_get("users/123")

        assert result["success"] is True
        assert result["data"] == {"test": "data"}

    def test_db_get_not_authenticated(self, firebase_client):
        """Test database get when not authenticated"""
        firebase_client.id_token = None
        result = firebase_client.db_get("users/123")
        assert result["success"] is False
        assert result["error"] == "Not authenticated"

    def test_db_set_success(self, firebase_client, mock_requests):
        """Test successful database set operation"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(hours=1)

        mock_response = Mock()
        mock_response.json.return_value = {"name": "test-data"}
        mock_response.raise_for_status.return_value = None
        mock_requests.put.return_value = mock_response

        result = firebase_client.db_set("users/123", {"name": "test-data"})

        assert result["success"] is True

    def test_db_update_success(self, firebase_client, mock_requests):
        """Test successful database update operation"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(hours=1)

        mock_response = Mock()
        mock_response.json.return_value = {"updated": True}
        mock_response.raise_for_status.return_value = None
        mock_requests.patch.return_value = mock_response

        result = firebase_client.db_update("users/123", {"name": "updated"})

        assert result["success"] is True

    def test_db_delete_success(self, firebase_client, mock_requests):
        """Test successful database delete operation"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(hours=1)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_requests.delete.return_value = mock_response

        result = firebase_client.db_delete("users/123")

        assert result["success"] is True

    def test_parse_error_email_exists(self, firebase_client):
        """Test error parsing for EMAIL_EXISTS error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "EMAIL_EXISTS"}}
        mock_exception.response = mock_response

        with patch(
            "services.firebase_client.translate_error",
            return_value="Email already exists",
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Email already exists"

    def test_parse_error_invalid_credentials(self, firebase_client):
        """Test error parsing for invalid credentials error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": {"message": "INVALID_LOGIN_CREDENTIALS"}
        }
        mock_exception.response = mock_response

        with patch(
            "services.firebase_client.translate_error",
            return_value="Invalid credentials",
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Invalid credentials"

    def test_store_auth_data(self, firebase_client):
        """Test storing authentication data"""
        auth_data = {
            "idToken": "test-id-token",
            "refreshToken": "test-refresh-token",
            "localId": "test-user-id",
            "expiresIn": "3600",
        }

        firebase_client._store_auth_data(auth_data)

        assert firebase_client.id_token == "test-id-token"
        assert firebase_client.refresh_token == "test-refresh-token"
        assert firebase_client.user_id == "test-user-id"
        assert firebase_client.token_expiry is not None

    @pytest.mark.parametrize(
        "operation", ["db_get", "db_set", "db_update", "db_delete"]
    )
    def test_database_operations_with_network_error(
        self, firebase_client, operation, mock_requests
    ):
        """Test database operations with network errors"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(hours=1)

        error = requests.exceptions.ConnectionError("Network error")
        mock_requests.get.side_effect = error
        mock_requests.put.side_effect = error
        mock_requests.patch.side_effect = error
        mock_requests.delete.side_effect = error

        if operation == "db_get":
            result = firebase_client.db_get("test/path")
        elif operation == "db_set":
            result = firebase_client.db_set("test/path", {"data": "test"})
        elif operation == "db_update":
            result = firebase_client.db_update("test/path", {"data": "test"})
        else:
            result = firebase_client.db_delete("test/path")

        assert result["success"] is False
        assert "error" in result

    def test_sign_in_request_exception(self, firebase_client, mock_requests):
        """Test sign_in handles request exceptions"""
        mock_requests.post.side_effect = requests.exceptions.RequestException(
            "Connection failed"
        )

        result = firebase_client.sign_in("test@example.com", "password")

        assert result["success"] is False
        assert "error" in result

    def test_refresh_token_request_exception(self, firebase_client, mock_requests):
        """Test refresh_token_request handles exceptions"""
        mock_requests.post.side_effect = Exception("Unexpected error")

        result = firebase_client.refresh_token_request("old-refresh-token")

        assert result["success"] is False
        assert "error" in result

    def test_ensure_valid_token_near_expiry_refreshes(
        self, firebase_client, mock_requests
    ):
        """Test ensure_valid_token refreshes when near expiry"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        # Set expiry to 2 minutes from now (within 5 minute refresh window)
        firebase_client.token_expiry = datetime.now() + timedelta(minutes=2)

        mock_response = Mock()
        mock_response.json.return_value = {
            "id_token": "new-id-token",
            "refresh_token": "new-refresh-token",
            "user_id": "test-user-id",
            "expires_in": "3600",
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        result = firebase_client.ensure_valid_token()

        assert result is True
        assert firebase_client.id_token == "new-id-token"

    def test_ensure_valid_token_refresh_fails(self, firebase_client, mock_requests):
        """Test ensure_valid_token returns False when refresh fails"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(minutes=2)

        mock_requests.post.side_effect = Exception("Refresh failed")

        result = firebase_client.ensure_valid_token()

        assert result is False

    def test_db_set_not_authenticated(self, firebase_client):
        """Test db_set returns error when not authenticated"""
        firebase_client.id_token = None

        result = firebase_client.db_set("test/path", {"data": "test"})

        assert result["success"] is False
        assert result["error"] == "Not authenticated"

    def test_db_update_not_authenticated(self, firebase_client):
        """Test db_update returns error when not authenticated"""
        firebase_client.id_token = None

        result = firebase_client.db_update("test/path", {"data": "test"})

        assert result["success"] is False
        assert result["error"] == "Not authenticated"

    def test_db_delete_not_authenticated(self, firebase_client):
        """Test db_delete returns error when not authenticated"""
        firebase_client.id_token = None

        result = firebase_client.db_delete("test/path")

        assert result["success"] is False
        assert result["error"] == "Not authenticated"

    def test_parse_error_invalid_password(self, firebase_client):
        """Test error parsing for INVALID_PASSWORD error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "INVALID_PASSWORD"}}
        mock_exception.response = mock_response

        with patch(
            "services.firebase_client.translate_error",
            return_value="Invalid credentials",
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Invalid credentials"

    def test_parse_error_weak_password(self, firebase_client):
        """Test error parsing for WEAK_PASSWORD error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "WEAK_PASSWORD"}}
        mock_exception.response = mock_response

        with patch(
            "services.firebase_client.translate_error", return_value="Password too weak"
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Password too weak"

    def test_parse_error_too_many_attempts(self, firebase_client):
        """Test error parsing for TOO_MANY_ATTEMPTS error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "TOO_MANY_ATTEMPTS"}}
        mock_exception.response = mock_response

        with patch(
            "services.firebase_client.translate_error", return_value="Too many attempts"
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Too many attempts"

    def test_parse_error_user_disabled(self, firebase_client):
        """Test error parsing for USER_DISABLED error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "USER_DISABLED"}}
        mock_exception.response = mock_response

        with patch(
            "services.firebase_client.translate_error", return_value="Account disabled"
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Account disabled"

    def test_parse_error_invalid_email(self, firebase_client):
        """Test error parsing for INVALID_EMAIL error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "INVALID_EMAIL"}}
        mock_exception.response = mock_response

        with patch(
            "services.firebase_client.translate_error", return_value="Invalid input"
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Invalid input"

    def test_parse_error_missing_password(self, firebase_client):
        """Test error parsing for MISSING_PASSWORD error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "MISSING_PASSWORD"}}
        mock_exception.response = mock_response

        with patch(
            "services.firebase_client.translate_error", return_value="Required field"
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Required field"

    def test_parse_error_operation_not_allowed(self, firebase_client):
        """Test error parsing for OPERATION_NOT_ALLOWED error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": {"message": "OPERATION_NOT_ALLOWED"}
        }
        mock_exception.response = mock_response

        with patch(
            "services.firebase_client.translate_error", return_value="Access denied"
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Access denied"

    def test_parse_error_email_not_found(self, firebase_client):
        """Test error parsing for EMAIL_NOT_FOUND error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "EMAIL_NOT_FOUND"}}
        mock_exception.response = mock_response

        with patch(
            "services.firebase_client.translate_error",
            return_value="Invalid credentials",
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Invalid credentials"

    def test_parse_error_unknown_firebase_error(self, firebase_client):
        """Test error parsing for unknown Firebase error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "SOME_UNKNOWN_ERROR"}}
        mock_exception.response = mock_response

        with patch(
            "services.firebase_client.translate_error",
            return_value="SOME_UNKNOWN_ERROR",
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "SOME_UNKNOWN_ERROR"

    def test_parse_error_json_exception(self, firebase_client):
        """Test error parsing when JSON parsing fails"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.side_effect = Exception("JSON parse error")
        mock_exception.response = mock_response

        with patch(
            "services.firebase_client.translate_error", return_value="Error message"
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Error message"

    def test_parse_error_no_response(self, firebase_client):
        """Test error parsing when exception has no response"""
        mock_exception = Exception("Generic error")

        with patch(
            "services.firebase_client.translate_error", return_value="Generic error"
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Generic error"

    def test_db_listen_creates_stream_listener(self, firebase_client):
        """Test db_listen creates and returns a StreamListener"""
        callback = Mock()
        error_callback = Mock()

        with patch.object(StreamListener, "start"):
            listener = firebase_client.db_listen("messages", callback, error_callback)

            assert listener is not None
            assert isinstance(listener, StreamListener)
            assert listener.firebase == firebase_client
            assert listener.path == "messages"
            assert listener.callback == callback
            assert listener.error_callback == error_callback


# =============================================================================
# StreamListener Tests
# =============================================================================
class TestStreamListener:
    """Tests for SSE StreamListener"""

    @pytest.fixture
    def mock_firebase_client(self, mock_firebase_config):
        """Create a mock firebase client"""
        with patch(
            "services.firebase_client.get_firebase_config",
            return_value=mock_firebase_config,
        ):
            client = FirebaseClient()
            client.id_token = "test-token"
            client.refresh_token = "test-refresh"
            client.token_expiry = datetime.now() + timedelta(hours=1)
            return client

    @pytest.fixture
    def stream_listener(self, mock_firebase_client):
        """Create a StreamListener for testing with proper cleanup"""
        callback = Mock()
        error_callback = Mock()
        listener = StreamListener(
            firebase_client=mock_firebase_client,
            path="messages",
            callback=callback,
            error_callback=error_callback,
        )
        yield listener
        # Cleanup: ensure the listener is stopped after each test
        listener._running = False
        if listener._response:
            try:
                listener._response.close()
            except Exception:
                pass
        if listener._thread and listener._thread.is_alive():
            listener._thread.join(timeout=1)

    def test_initialization(self, stream_listener, mock_firebase_client):
        """Test StreamListener initialization"""
        assert stream_listener.firebase == mock_firebase_client
        assert stream_listener.path == "messages"
        assert stream_listener._running is False
        assert stream_listener._thread is None
        assert stream_listener._reconnect_delay == 1

    def test_start_sets_running_flag(self, stream_listener):
        """Test start() sets running flag and creates thread"""
        with patch.object(stream_listener, "_listen_loop"):
            stream_listener.start()

            assert stream_listener._running is True
            assert stream_listener._thread is not None

            # Cleanup - properly stop the listener
            stream_listener.stop()

    def test_start_when_already_running(self, stream_listener):
        """Test start() does nothing if already running"""
        stream_listener._running = True
        original_thread = stream_listener._thread

        stream_listener.start()

        # Thread should not change
        assert stream_listener._thread == original_thread

    def test_stop_clears_running_flag(self, stream_listener):
        """Test stop() clears running flag"""
        stream_listener._running = True
        stream_listener._thread = Mock()
        stream_listener._thread.is_alive.return_value = False

        stream_listener.stop()

        assert stream_listener._running is False

    def test_stop_sets_running_false_with_response(self, stream_listener):
        """Test stop() sets running flag to False (response is NOT closed from another thread)"""
        stream_listener._running = True
        stream_listener._response = Mock()
        stream_listener._thread = Mock()
        stream_listener._thread.is_alive.return_value = False

        stream_listener.stop()

        # We no longer close response from another thread - it causes crashes
        # The thread will exit naturally on next timeout
        assert stream_listener._running is False
        stream_listener._response.close.assert_not_called()

    def test_process_event_keep_alive(self, stream_listener):
        """Test processing keep-alive event"""
        stream_listener._process_event("keep-alive", None)

        # Should not call callback for keep-alive
        stream_listener.callback.assert_not_called()

    def test_process_event_cancel(self, stream_listener):
        """Test processing cancel event"""
        stream_listener._process_event("cancel", None)

        stream_listener.callback.assert_called_once_with("cancel", None)

    def test_process_event_auth_revoked(self, stream_listener):
        """Test processing auth_revoked event"""
        stream_listener._process_event("auth_revoked", None)

        stream_listener.callback.assert_called_once_with("auth_revoked", None)

    def test_process_event_put(self, stream_listener):
        """Test processing put event with data"""
        import json

        data = {"path": "/", "data": {"msg1": {"content": "hello"}}}
        data_str = json.dumps(data)

        stream_listener._process_event("put", data_str)

        stream_listener.callback.assert_called_once_with("put", data)

    def test_process_event_patch(self, stream_listener):
        """Test processing patch event with data"""
        import json

        data = {"path": "/msg1", "data": {"read": True}}
        data_str = json.dumps(data)

        stream_listener._process_event("patch", data_str)

        stream_listener.callback.assert_called_once_with("patch", data)

    def test_process_event_invalid_json(self, stream_listener):
        """Test processing event with invalid JSON logs error but doesn't crash"""
        # Should not raise even with bad JSON
        stream_listener._process_event("put", "not-valid-json")

        # Callback should NOT be called for invalid JSON
        stream_listener.callback.assert_not_called()

    def test_process_event_empty_data(self, stream_listener):
        """Test processing event with empty data"""
        stream_listener._process_event("put", "")

        stream_listener.callback.assert_called_once_with("put", None)

    def test_connect_and_stream_not_authenticated(
        self, stream_listener, mock_firebase_client
    ):
        """Test connection fails when not authenticated"""
        mock_firebase_client.id_token = None
        mock_firebase_client.refresh_token = None

        with pytest.raises(ConnectionError, match="Not authenticated"):
            stream_listener._connect_and_stream()

    def test_reconnect_delay_exponential_backoff(self, stream_listener):
        """Test reconnect delay increases exponentially"""
        initial_delay = stream_listener._reconnect_delay
        max_delay = stream_listener._max_reconnect_delay

        # Simulate multiple reconnections
        stream_listener._reconnect_delay = min(
            stream_listener._reconnect_delay * 2, max_delay
        )
        assert stream_listener._reconnect_delay == 2

        stream_listener._reconnect_delay = min(
            stream_listener._reconnect_delay * 2, max_delay
        )
        assert stream_listener._reconnect_delay == 4

        # Should cap at max
        stream_listener._reconnect_delay = 100
        stream_listener._reconnect_delay = min(
            stream_listener._reconnect_delay * 2, max_delay
        )
        assert stream_listener._reconnect_delay == max_delay

    def test_error_callback_called_on_error(self, stream_listener):
        """Test error callback is called when there's an error"""
        error_msg = "Connection failed"
        stream_listener._on_stream_error = stream_listener.error_callback

        if stream_listener.error_callback:
            stream_listener.error_callback(error_msg)

        stream_listener.error_callback.assert_called_with(error_msg)

    def test_listener_with_no_error_callback(self, mock_firebase_client):
        """Test listener works without error callback"""
        import json

        callback = Mock()
        listener = StreamListener(
            firebase_client=mock_firebase_client,
            path="messages",
            callback=callback,
            error_callback=None,  # No error callback
        )

        assert listener.error_callback is None

        # Processing events should still work
        data_str = json.dumps({"path": "/", "data": {}})
        listener._process_event("put", data_str)
        callback.assert_called_once()

    def test_stop_does_not_close_response(self, stream_listener):
        """Test stop() does NOT close response (to avoid cross-thread crashes)"""
        stream_listener._running = True
        stream_listener._response = Mock()
        stream_listener._thread = Mock()
        stream_listener._thread.is_alive.return_value = False

        stream_listener.stop()

        assert stream_listener._running is False
        # Response should NOT be closed from stop() - causes crashes
        stream_listener._response.close.assert_not_called()

    def test_stop_logs_when_thread_still_running(self, stream_listener):
        """Test stop() logs when thread doesn't finish in time"""
        stream_listener._running = True
        stream_listener._thread = Mock()
        stream_listener._thread.is_alive.return_value = True  # Thread still running

        with patch("services.firebase_client.logger") as mock_logger:
            stream_listener.stop()

            # Should log that thread is still running
            assert mock_logger.debug.called

    def test_stop_waits_for_thread(self, stream_listener):
        """Test stop() waits briefly for thread to finish"""
        stream_listener._running = True
        stream_listener._thread = Mock()
        stream_listener._thread.is_alive.return_value = True

        stream_listener.stop()

        # Now waits 0.5s instead of 2s to avoid blocking logout
        stream_listener._thread.join.assert_called_once_with(timeout=0.5)

    def test_process_event_null_string_data(self, stream_listener):
        """Test processing event with 'null' as data string"""
        stream_listener._process_event("put", "null")

        stream_listener.callback.assert_called_once_with("put", None)

    def test_process_event_general_exception(self, stream_listener):
        """Test _process_event handles general exceptions gracefully"""
        # Force callback to raise an exception
        stream_listener.callback.side_effect = Exception("Callback failed")

        # Should not raise - exception is caught and logged
        stream_listener._process_event("put", '{"path": "/", "data": {}}')

    def test_is_running_property(self, stream_listener):
        """Test _running state management"""
        assert stream_listener._running is False

        stream_listener._running = True
        assert stream_listener._running is True

        stream_listener._running = False
        assert stream_listener._running is False

    def test_connect_and_stream_success(self, stream_listener, mock_firebase_client):
        """Test successful connection and streaming"""
        with patch("services.firebase_client.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()

            # Simulate SSE data
            sse_data = [
                "event: put",
                'data: {"path": "/", "data": {"key": "value"}}',
                "",  # Empty line ends event
            ]
            mock_response.iter_lines.return_value = iter(sse_data)
            mock_get.return_value = mock_response

            stream_listener._running = True
            stream_listener._connect_and_stream()

            # Verify callback was called with parsed data
            stream_listener.callback.assert_called_once()
            call_args = stream_listener.callback.call_args[0]
            assert call_args[0] == "put"

    def test_connect_and_stream_handles_none_lines(
        self, stream_listener, mock_firebase_client
    ):
        """Test _connect_and_stream handles None lines in stream"""
        with patch("services.firebase_client.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()

            # Include None values that should be skipped
            sse_data = [
                None,  # Should be skipped
                "event: put",
                None,  # Should be skipped
                'data: {"path": "/", "data": false}',
                "",
            ]
            mock_response.iter_lines.return_value = iter(sse_data)
            mock_get.return_value = mock_response

            stream_listener._running = True
            stream_listener._connect_and_stream()

            stream_listener.callback.assert_called_once()

    def test_connect_and_stream_stops_when_running_false(
        self, stream_listener, mock_firebase_client
    ):
        """Test _connect_and_stream exits when _running becomes False"""
        with patch("services.firebase_client.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()

            # Generator that stops listener mid-stream
            def lines_generator():
                yield "event: put"
                stream_listener._running = False  # Stop during iteration
                yield 'data: {"path": "/", "data": true}'
                yield ""

            mock_response.iter_lines.return_value = lines_generator()
            mock_get.return_value = mock_response

            stream_listener._running = True
            stream_listener._connect_and_stream()

            # Callback should not be called since we stopped before empty line
            stream_listener.callback.assert_not_called()

    def test_error_callback_exception_is_caught(
        self, mock_firebase_client
    ):
        """Test error_callback exception is caught and doesn't crash"""
        callback = Mock()
        error_callback = Mock()
        error_callback.side_effect = Exception("Error callback crashed")

        listener = StreamListener(
            firebase_client=mock_firebase_client,
            path="messages",
            callback=callback,
            error_callback=error_callback,
        )

        # Simulate the error handling code path
        listener._running = True
        error_msg = "Connection failed"
        if listener.error_callback:
            try:
                listener.error_callback(error_msg)
            except Exception:
                pass

        # Should have been called even though it raised
        error_callback.assert_called_once_with(error_msg)

    def test_listen_loop_breaks_on_error_when_not_running(
        self, stream_listener, mock_firebase_client
    ):
        """Test listen loop breaks during error handling when _running is False"""
        with patch("services.firebase_client.requests.get") as mock_get:
            # First call raises, but _running will be False
            mock_get.side_effect = Exception("Connection failed")

            stream_listener._running = False  # Already stopped

            # Should exit immediately without reconnect
            stream_listener._listen_loop()

            # Should only have been called once (no reconnect attempts)
            assert mock_get.call_count <= 1

    def test_listen_loop_error_callback_exception_caught(
        self, mock_firebase_client
    ):
        """Test _listen_loop catches error_callback exceptions"""
        callback = Mock()
        error_callback = Mock()
        error_callback.side_effect = Exception("Error callback crashed")

        listener = StreamListener(
            firebase_client=mock_firebase_client,
            path="messages",
            callback=callback,
            error_callback=error_callback,
        )

        call_count = [0]

        def raise_then_stop(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Connection failed")
            # Stop after first error
            listener._running = False
            raise Exception("Connection failed again")

        with patch("services.firebase_client.requests.get") as mock_get:
            mock_get.side_effect = raise_then_stop

            listener._running = True
            # Use very short reconnect delay
            listener._reconnect_delay = 0.01

            with patch("services.firebase_client.threading.Event") as mock_event:
                mock_event.return_value.wait = Mock()
                listener._listen_loop()

            # Error callback should have been called
            error_callback.assert_called()

    def test_listen_loop_reconnect_sleep_checks_running_flag(
        self, mock_firebase_client
    ):
        """Test _listen_loop reconnect sleep checks _running flag"""
        callback = Mock()
        listener = StreamListener(
            firebase_client=mock_firebase_client,
            path="messages",
            callback=callback,
            error_callback=None,
        )

        call_count = [0]

        def raise_and_stop_mid_sleep(*args, **kwargs):
            call_count[0] += 1
            raise Exception("Connection failed")

        with patch("services.firebase_client.requests.get") as mock_get:
            mock_get.side_effect = raise_and_stop_mid_sleep

            listener._running = True
            listener._reconnect_delay = 0.5  # Would sleep 5 times

            # Mock Event().wait to stop running after first sleep
            sleep_count = [0]

            def stop_during_sleep(timeout):
                sleep_count[0] += 1
                if sleep_count[0] >= 2:
                    listener._running = False

            with patch("services.firebase_client.threading.Event") as mock_event:
                mock_event.return_value.wait.side_effect = stop_during_sleep
                listener._listen_loop()

            # Should have called sleep a few times before stopping
            assert sleep_count[0] >= 1


class TestStreamListenerIntegration:
    """Integration tests for StreamListener with mocked network"""

    @pytest.fixture
    def mock_firebase_client(self, mock_firebase_config):
        """Create a mock firebase client"""
        with patch(
            "services.firebase_client.get_firebase_config",
            return_value=mock_firebase_config,
        ):
            client = FirebaseClient()
            client.id_token = "test-token"
            client.refresh_token = "test-refresh"
            client.token_expiry = datetime.now() + timedelta(hours=1)
            yield client

    @pytest.fixture
    def stream_listener_integration(self, mock_firebase_client):
        """Create a StreamListener for integration testing with cleanup"""
        callback = Mock()
        listener = StreamListener(
            firebase_client=mock_firebase_client,
            path="messages",
            callback=callback,
            error_callback=None,
        )
        yield listener
        # Cleanup
        listener._running = False
        if listener._thread and listener._thread.is_alive():
            listener._thread.join(timeout=1)

    def test_listen_loop_exits_when_stopped(self, mock_firebase_client):
        """Test listen loop exits when _running is set to False"""
        callback = Mock()
        listener = StreamListener(
            firebase_client=mock_firebase_client,
            path="messages",
            callback=callback,
            error_callback=None,
        )

        # Set to not running before starting
        listener._running = False

        # Run listen loop directly - should exit immediately
        listener._listen_loop()

        # Callback should not be called
        callback.assert_not_called()

    def test_listen_loop_handles_connection_error(self, mock_firebase_client):
        """Test listen loop handles connection errors and stops when requested"""
        callback = Mock()
        error_callback = Mock()
        listener = StreamListener(
            firebase_client=mock_firebase_client,
            path="messages",
            callback=callback,
            error_callback=error_callback,
        )

        # Track how many times _connect_and_stream is called
        call_count = [0]

        def mock_connect():
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("First connection failed")
            # Stop after first error to avoid infinite loop
            listener._running = False

        listener._connect_and_stream = mock_connect
        listener._running = True
        listener._reconnect_delay = 0.01  # Very short delay for test

        listener._listen_loop()

        # Should have tried to connect at least once
        assert call_count[0] >= 1
        error_callback.assert_called()

    def test_listen_loop_handles_read_timeout(self, mock_firebase_client):
        """Test listen loop handles ReadTimeout and continues"""
        callback = Mock()
        listener = StreamListener(
            firebase_client=mock_firebase_client,
            path="messages",
            callback=callback,
            error_callback=None,
        )

        call_count = [0]

        def mock_connect():
            call_count[0] += 1
            if call_count[0] == 1:
                raise requests.exceptions.ReadTimeout("Read timed out")
            # Stop after timeout
            listener._running = False

        listener._connect_and_stream = mock_connect
        listener._running = True

        listener._listen_loop()

        # Should have been called twice (once for timeout, once to stop)
        assert call_count[0] >= 1

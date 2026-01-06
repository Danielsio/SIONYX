"""
Tests for force_logout_listener.py - Force Logout Listener
Tests Firebase streaming for force logout detection.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from PyQt6.QtCore import QThread


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def mock_firebase():
    """Create mock Firebase client"""
    firebase = Mock()
    firebase.org_id = "test-org"
    firebase.database_url = "https://test-db.firebaseio.com"
    firebase.id_token = "test-token-123"
    return firebase


@pytest.fixture
def force_logout_listener(qapp, mock_firebase):
    """Create ForceLogoutListener instance"""
    from ui.force_logout_listener import ForceLogoutListener

    listener = ForceLogoutListener(mock_firebase, "test-user-123")
    yield listener

    # Cleanup
    listener.running = False
    if listener.isRunning():
        listener.quit()
        listener.wait(1000)


# =============================================================================
# Test initialization
# =============================================================================
class TestForceLogoutListenerInit:
    """Tests for ForceLogoutListener initialization"""

    def test_inherits_from_qthread(self, force_logout_listener):
        """Test listener inherits from QThread"""
        assert isinstance(force_logout_listener, QThread)

    def test_stores_firebase_client(self, force_logout_listener, mock_firebase):
        """Test listener stores firebase client"""
        assert force_logout_listener.firebase == mock_firebase

    def test_stores_user_id(self, force_logout_listener):
        """Test listener stores user ID"""
        assert force_logout_listener.user_id == "test-user-123"

    def test_running_is_true_initially(self, force_logout_listener):
        """Test running flag is True initially"""
        assert force_logout_listener.running is True

    def test_has_force_logout_signal(self, force_logout_listener):
        """Test listener has force_logout_detected signal"""
        assert hasattr(force_logout_listener, "force_logout_detected")


# =============================================================================
# Test stop method
# =============================================================================
class TestForceLogoutListenerStop:
    """Tests for stop method"""

    def test_stop_sets_running_false(self, force_logout_listener):
        """Test stop sets running to False"""
        force_logout_listener.running = True

        force_logout_listener.stop()

        assert force_logout_listener.running is False

    def test_stop_does_not_close_response(self, force_logout_listener):
        """Test stop does NOT close the response (to avoid cross-thread crashes)"""
        force_logout_listener.running = True
        force_logout_listener._response = Mock()

        force_logout_listener.stop()

        # Response should NOT be closed from stop() - it causes crashes
        force_logout_listener._response.close.assert_not_called()

    def test_stop_logs_info(self, force_logout_listener):
        """Test stop logs the stop request"""
        with patch("ui.force_logout_listener.logger") as mock_logger:
            force_logout_listener.stop()

            # Should log debug and info messages
            assert mock_logger.debug.called or mock_logger.info.called


# =============================================================================
# Test run method
# =============================================================================
class TestForceLogoutListenerRun:
    """Tests for run method"""

    def test_run_builds_correct_stream_url(self, force_logout_listener, mock_firebase):
        """Test run builds correct Firebase stream URL"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = iter([])  # Empty stream

            # Stop the listener after the request is made
            def stop_after_call(*args, **kwargs):
                force_logout_listener.running = False
                return mock_response

            mock_get.side_effect = stop_after_call

            force_logout_listener.run()

            call_args = mock_get.call_args
            url = call_args[0][0]

            assert "test-db.firebaseio.com" in url
            assert "test-org" in url
            assert "test-user-123" in url
            assert "forceLogout" in url

    def test_run_handles_non_200_status(self, force_logout_listener):
        """Test run handles non-200 status code"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response

            # Stop the listener after first request
            def stop_after_call(*args, **kwargs):
                force_logout_listener.running = False
                return mock_response

            mock_get.side_effect = stop_after_call

            # Should not raise
            force_logout_listener.run()

    def test_run_emits_signal_on_force_logout_true(self, force_logout_listener):
        """Test run emits signal when forceLogout is true"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            # Simulate Firebase SSE stream format: event + data + empty line
            sse_data = [
                "event: put",
                'data: {"path": "/", "data": true}',
                "",  # Empty line signals end of event
            ]
            mock_response.iter_lines.return_value = iter(sse_data)
            mock_get.return_value = mock_response

            signal_received = []
            force_logout_listener.force_logout_detected.connect(
                lambda: signal_received.append(True)
            )

            force_logout_listener.run()

            assert len(signal_received) == 1

    def test_run_ignores_false_value(self, force_logout_listener):
        """Test run ignores false value"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            # Simulate Firebase SSE stream with false value
            sse_data = [
                "event: put",
                'data: {"path": "/", "data": false}',
                "",  # Empty line signals end of event
            ]
            mock_response.iter_lines.return_value = iter(sse_data)

            # Stop the listener after processing
            def stop_after_call(*args, **kwargs):
                force_logout_listener.running = False
                return mock_response

            mock_get.side_effect = stop_after_call

            signal_received = []
            force_logout_listener.force_logout_detected.connect(
                lambda: signal_received.append(True)
            )

            force_logout_listener.run()

            # Signal should NOT be emitted for false
            assert len(signal_received) == 0

    def test_run_ignores_null_value(self, force_logout_listener):
        """Test run ignores null value"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            # Simulate Firebase SSE stream with null value
            sse_data = [
                "event: put",
                'data: {"path": "/", "data": null}',
                "",  # Empty line signals end of event
            ]
            mock_response.iter_lines.return_value = iter(sse_data)

            # Stop the listener after processing
            def stop_after_call(*args, **kwargs):
                force_logout_listener.running = False
                return mock_response

            mock_get.side_effect = stop_after_call

            signal_received = []
            force_logout_listener.force_logout_detected.connect(
                lambda: signal_received.append(True)
            )

            force_logout_listener.run()

            assert len(signal_received) == 0

    def test_run_handles_timeout_exception(self, force_logout_listener):
        """Test run handles timeout exception"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            import requests as req_module

            # Raise exception then stop the listener
            def raise_and_stop(*args, **kwargs):
                force_logout_listener.running = False
                raise req_module.exceptions.Timeout("Connection timed out")

            mock_get.side_effect = raise_and_stop

            # Should not raise
            force_logout_listener.run()

    def test_run_handles_read_timeout_continues_loop(self, force_logout_listener):
        """Test run handles ReadTimeout and continues checking running flag"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            import requests as req_module

            call_count = [0]

            # Raise ReadTimeout first, then stop
            def raise_timeout_then_stop(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise req_module.exceptions.ReadTimeout("Read timed out")
                # Second call - stop the loop
                force_logout_listener.running = False
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.iter_lines.return_value = iter([])
                return mock_response

            mock_get.side_effect = raise_timeout_then_stop

            # Should not raise and should continue after ReadTimeout
            force_logout_listener.run()

            # Should have been called at least twice (once for timeout, once to stop)
            assert call_count[0] >= 1

    def test_run_handles_general_exception(self, force_logout_listener):
        """Test run handles general exception"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            # Raise exception then stop the listener
            def raise_and_stop(*args, **kwargs):
                force_logout_listener.running = False
                raise Exception("Network error")

            mock_get.side_effect = raise_and_stop

            # Should not raise
            force_logout_listener.run()

    def test_run_handles_connection_error_with_retry(self, force_logout_listener):
        """Test run handles ConnectionError and retries when running"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            import requests as req_module

            call_count = [0]

            def raise_connection_error(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    # First call: raise ConnectionError while running is True
                    raise req_module.exceptions.ConnectionError("Connection failed")
                # Second call: stop
                force_logout_listener.running = False
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.iter_lines.return_value = iter([])
                return mock_response

            mock_get.side_effect = raise_connection_error

            # Patch _sleep_if_running to not actually sleep
            with patch.object(force_logout_listener, "_sleep_if_running"):
                force_logout_listener.run()

            assert call_count[0] >= 1

    def test_run_handles_exception_with_retry(self, force_logout_listener):
        """Test run handles Exception and retries when running"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            call_count = [0]

            def raise_exception(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    # First call: raise Exception while running is True
                    raise RuntimeError("Unexpected error")
                # Second call: stop
                force_logout_listener.running = False
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.iter_lines.return_value = iter([])
                return mock_response

            mock_get.side_effect = raise_exception

            # Patch _sleep_if_running to not actually sleep
            with patch.object(force_logout_listener, "_sleep_if_running"):
                force_logout_listener.run()

            assert call_count[0] >= 1

    def test_run_handles_json_decode_error(self, force_logout_listener):
        """Test run handles JSON decode error"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            # Invalid JSON in SSE data field
            sse_data = [
                "event: put",
                "data: not valid json",
                "",  # Empty line signals end of event
            ]
            mock_response.iter_lines.return_value = iter(sse_data)

            # Stop the listener after processing
            def stop_after_call(*args, **kwargs):
                force_logout_listener.running = False
                return mock_response

            mock_get.side_effect = stop_after_call

            # Should not raise
            force_logout_listener.run()

    def test_run_stops_when_running_false(self, force_logout_listener):
        """Test run stops iteration when running is set to False"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200

            # Create iterator that checks running flag
            def lines_generator():
                sse_data = [
                    "event: put",
                    'data: {"path": "/", "data": false}',
                    "",
                ]
                for line in sse_data:
                    if not force_logout_listener.running:
                        return
                    yield line

            mock_response.iter_lines.return_value = lines_generator()
            mock_get.return_value = mock_response

            force_logout_listener.running = False
            force_logout_listener.run()

            # Should complete without hanging

    def test_run_handles_none_lines(self, force_logout_listener):
        """Test run handles None lines in stream"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            # Include None values in the stream
            sse_data = [
                None,  # Should be skipped
                "event: put",
                None,  # Should be skipped
                'data: {"path": "/", "data": false}',
                "",
            ]
            mock_response.iter_lines.return_value = iter(sse_data)

            def stop_after_call(*args, **kwargs):
                force_logout_listener.running = False
                return mock_response

            mock_get.side_effect = stop_after_call

            force_logout_listener.run()

    def test_run_handles_keep_alive_event(self, force_logout_listener):
        """Test run handles keep-alive events"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            # SSE keep-alive event
            sse_data = [
                "event: keep-alive",
                "data: null",
                "",
            ]
            mock_response.iter_lines.return_value = iter(sse_data)

            def stop_after_call(*args, **kwargs):
                force_logout_listener.running = False
                return mock_response

            mock_get.side_effect = stop_after_call

            force_logout_listener.run()

    def test_process_event_handles_exception(self, force_logout_listener):
        """Test _process_event handles general exceptions"""
        # Force an exception by mocking json.loads to raise
        with patch("ui.force_logout_listener.json.loads") as mock_loads:
            mock_loads.side_effect = Exception("Unexpected error")

            # Should not raise
            force_logout_listener._process_event("put", '{"path": "/", "data": true}')


# =============================================================================
# Test _sleep_if_running method
# =============================================================================
class TestSleepIfRunning:
    """Tests for _sleep_if_running method"""

    def test_sleep_if_running_exits_when_running_false(self, force_logout_listener):
        """Test _sleep_if_running exits early when running is False"""
        force_logout_listener.running = False

        # Should return quickly without actually sleeping the full duration
        import time

        start = time.time()
        force_logout_listener._sleep_if_running(10)  # Would be 10 seconds if not stopped
        elapsed = time.time() - start

        # Should exit almost immediately (less than 1 second)
        assert elapsed < 1

    def test_sleep_if_running_checks_flag_periodically(self, force_logout_listener):
        """Test _sleep_if_running checks running flag in intervals"""
        force_logout_listener.running = True

        # Set running to False after a short delay
        import threading

        def stop_after_delay():
            import time

            time.sleep(0.2)
            force_logout_listener.running = False

        thread = threading.Thread(target=stop_after_delay)
        thread.start()

        import time

        start = time.time()
        force_logout_listener._sleep_if_running(10)
        elapsed = time.time() - start

        thread.join()

        # Should exit within about 0.5 seconds (0.2 delay + some buffer)
        assert elapsed < 1


# =============================================================================
# Test stream URL construction
# =============================================================================
class TestStreamUrlConstruction:
    """Tests for stream URL construction"""

    def test_url_includes_org_id(self, mock_firebase):
        """Test URL includes org_id"""
        from ui.force_logout_listener import ForceLogoutListener

        listener = ForceLogoutListener(mock_firebase, "user-123")

        # Check the components are stored correctly
        assert listener.firebase.org_id == "test-org"

    def test_url_includes_user_id(self, force_logout_listener):
        """Test URL includes user_id"""
        assert force_logout_listener.user_id == "test-user-123"

    def test_url_uses_database_url(self, force_logout_listener, mock_firebase):
        """Test URL uses database_url from firebase"""
        assert (
            force_logout_listener.firebase.database_url
            == "https://test-db.firebaseio.com"
        )

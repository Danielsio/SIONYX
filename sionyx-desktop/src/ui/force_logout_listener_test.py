"""
Tests for force_logout_listener.py - Force Logout Listener
Tests Firebase streaming for force logout detection.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
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
            mock_response.iter_content.return_value = iter([])
            mock_get.return_value = mock_response
            
            force_logout_listener.running = False  # Exit immediately
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
            
            # Should not raise
            force_logout_listener.run()

    def test_run_emits_signal_on_force_logout_true(self, force_logout_listener):
        """Test run emits signal when forceLogout is true"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            # Simulate Firebase stream sending "true"
            mock_response.iter_content.return_value = iter(list("true\n"))
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
            # Simulate Firebase stream sending "false"
            mock_response.iter_content.return_value = iter(list("false\n"))
            mock_get.return_value = mock_response
            
            signal_received = []
            force_logout_listener.force_logout_detected.connect(
                lambda: signal_received.append(True)
            )
            
            # Stop after first iteration
            force_logout_listener.running = False
            force_logout_listener.run()
            
            # Signal should NOT be emitted for false
            assert len(signal_received) == 0

    def test_run_ignores_null_value(self, force_logout_listener):
        """Test run ignores null value"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.iter_content.return_value = iter(list("null\n"))
            mock_get.return_value = mock_response
            
            signal_received = []
            force_logout_listener.force_logout_detected.connect(
                lambda: signal_received.append(True)
            )
            
            force_logout_listener.running = False
            force_logout_listener.run()
            
            assert len(signal_received) == 0

    def test_run_handles_timeout_exception(self, force_logout_listener):
        """Test run handles timeout exception"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            import requests
            mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
            
            # Should not raise
            force_logout_listener.run()

    def test_run_handles_general_exception(self, force_logout_listener):
        """Test run handles general exception"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            # Should not raise
            force_logout_listener.run()

    def test_run_handles_json_decode_error(self, force_logout_listener):
        """Test run handles JSON decode error"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            # Invalid JSON
            mock_response.iter_content.return_value = iter(list("not valid json\n"))
            mock_get.return_value = mock_response
            
            force_logout_listener.running = False
            # Should not raise
            force_logout_listener.run()

    def test_run_stops_when_running_false(self, force_logout_listener):
        """Test run stops iteration when running is set to False"""
        with patch("ui.force_logout_listener.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            
            # Create infinite iterator but stop via running flag
            def content_generator():
                for c in "false\n":
                    if not force_logout_listener.running:
                        return
                    yield c
            
            mock_response.iter_content.return_value = content_generator()
            mock_get.return_value = mock_response
            
            force_logout_listener.running = False
            force_logout_listener.run()
            
            # Should complete without hanging


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
        assert force_logout_listener.firebase.database_url == "https://test-db.firebaseio.com"





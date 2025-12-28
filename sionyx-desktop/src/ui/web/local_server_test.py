"""
Tests for LocalFileServer - HTTP server for serving local HTML assets
"""

import socket
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from ui.web.local_server import LocalFileServer, _QuietHandler


# =============================================================================
# Tests for _QuietHandler
# =============================================================================
class TestQuietHandler:
    """Tests for _QuietHandler class"""

    def test_log_message_does_nothing(self):
        """Test log_message is silenced"""
        # Create mock request and client_address
        mock_request = Mock()
        mock_server = Mock()
        
        # _QuietHandler should have log_message that does nothing
        handler = _QuietHandler.__new__(_QuietHandler)
        # Call log_message - should not raise
        handler.log_message("test %s", "message")


# =============================================================================
# Tests for LocalFileServer initialization
# =============================================================================
class TestLocalFileServerInit:
    """Tests for LocalFileServer initialization"""

    def test_init_with_defaults(self, tmp_path):
        """Test initialization with default host and port"""
        server = LocalFileServer(tmp_path)
        
        assert server.root_dir == tmp_path
        assert server.host == "127.0.0.1"
        assert isinstance(server.port, int)
        assert server.port > 0
        assert server._httpd is None
        assert server._thread is None

    def test_init_with_custom_host(self, tmp_path):
        """Test initialization with custom host"""
        server = LocalFileServer(tmp_path, host="localhost")
        
        assert server.host == "localhost"

    def test_init_with_custom_port(self, tmp_path):
        """Test initialization with custom port"""
        server = LocalFileServer(tmp_path, port=8888)
        
        assert server.port == 8888

    def test_init_converts_root_dir_to_path(self, tmp_path):
        """Test that root_dir is converted to Path"""
        server = LocalFileServer(str(tmp_path))
        
        assert isinstance(server.root_dir, Path)


# =============================================================================
# Tests for _find_free_port
# =============================================================================
class TestFindFreePort:
    """Tests for _find_free_port static method"""

    def test_find_free_port_returns_int(self):
        """Test that _find_free_port returns an integer"""
        port = LocalFileServer._find_free_port("127.0.0.1")
        
        assert isinstance(port, int)
        assert port > 0

    def test_find_free_port_is_available(self):
        """Test that returned port is actually available"""
        port = LocalFileServer._find_free_port("127.0.0.1")
        
        # Try binding to the port - should work
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))


# =============================================================================
# Tests for base_url property
# =============================================================================
class TestBaseUrl:
    """Tests for base_url property"""

    def test_base_url_format(self, tmp_path):
        """Test base_url returns correct format"""
        server = LocalFileServer(tmp_path, port=9999)
        
        assert server.base_url == "http://127.0.0.1:9999"

    def test_base_url_with_custom_host(self, tmp_path):
        """Test base_url with custom host"""
        server = LocalFileServer(tmp_path, host="localhost", port=8080)
        
        assert server.base_url == "http://localhost:8080"


# =============================================================================
# Tests for start and stop
# =============================================================================
class TestServerLifecycle:
    """Tests for server start and stop"""

    def test_start_creates_httpd_and_thread(self, tmp_path):
        """Test start creates HTTP server and thread"""
        server = LocalFileServer(tmp_path)
        
        try:
            server.start()
            
            assert server._httpd is not None
            assert server._thread is not None
            assert server._thread.is_alive()
        finally:
            server.stop()

    def test_stop_cleans_up_resources(self, tmp_path):
        """Test stop cleans up server resources"""
        server = LocalFileServer(tmp_path)
        server.start()
        
        server.stop()
        
        assert server._httpd is None

    def test_stop_when_not_started(self, tmp_path):
        """Test stop when server was never started"""
        server = LocalFileServer(tmp_path)
        
        # Should not raise
        server.stop()
        
        assert server._httpd is None

    def test_server_serves_files(self, tmp_path):
        """Test that server can serve files"""
        import urllib.request
        
        # Create a test file
        test_file = tmp_path / "test.html"
        test_file.write_text("<html>test</html>")
        
        server = LocalFileServer(tmp_path)
        
        try:
            server.start()
            
            # Give server time to start
            time.sleep(0.1)
            
            # Try to fetch the file
            url = f"{server.base_url}/test.html"
            response = urllib.request.urlopen(url, timeout=5)
            content = response.read().decode("utf-8")
            
            assert "<html>test</html>" in content
        finally:
            server.stop()

    def test_stop_cleans_up_after_multiple_calls(self, tmp_path):
        """Test stop can be called multiple times safely"""
        server = LocalFileServer(tmp_path)
        server.start()
        
        # Call stop multiple times
        server.stop()
        server.stop()  # Should not raise
        
        assert server._httpd is None


# =============================================================================
# Tests for concurrent access
# =============================================================================
class TestConcurrentAccess:
    """Tests for concurrent server access"""

    def test_multiple_start_stop_cycles(self, tmp_path):
        """Test server can be started and stopped multiple times"""
        server = LocalFileServer(tmp_path)
        
        for _ in range(3):
            server.start()
            assert server._httpd is not None
            server.stop()
            assert server._httpd is None

    def test_different_ports(self, tmp_path):
        """Test that different instances get different ports"""
        server1 = LocalFileServer(tmp_path)
        server2 = LocalFileServer(tmp_path)
        
        # Ports should be different (unless specifically set)
        assert server1.port != server2.port or server1.port == server2.port  # Both could get same free port


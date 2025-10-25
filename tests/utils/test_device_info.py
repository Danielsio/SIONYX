"""
Tests for device_info utility
"""

import socket
from unittest.mock import patch

from src.utils.device_info import (
    get_computer_id,
    get_computer_name,
    get_device_id,
    get_mac_address,
)


class TestDeviceInfo:
    """Test cases for device information utilities"""

    def test_get_computer_name_success(self):
        """Test successful computer name retrieval"""
        with patch("socket.gethostname", return_value="TEST-PC"):
            result = get_computer_name()
            assert result == "TEST-PC"

    def test_get_computer_name_failure(self):
        """Test computer name retrieval failure"""
        with patch("socket.gethostname", side_effect=socket.error("Hostname error")):
            result = get_computer_name()
            assert result == "Unknown-PC"

    def test_get_mac_address_success(self):
        """Test successful MAC address retrieval"""
        with patch("uuid.getnode", return_value=0x123456789ABC):
            result = get_mac_address()
            assert result == "00:00:00:12:34:56"

    def test_get_mac_address_failure(self):
        """Test MAC address retrieval failure"""
        with patch("uuid.getnode", side_effect=Exception("MAC error")):
            result = get_mac_address()
            assert result is None

    def test_get_mac_address_invalid_node(self):
        """Test MAC address with invalid node ID"""
        with patch("uuid.getnode", return_value=0):
            result = get_mac_address()
            assert result is None

    def test_get_computer_id_success(self):
        """Test successful computer ID generation"""
        with patch(
            "src.utils.device_info.get_device_id", return_value="test-device-id"
        ):
            result = get_computer_id()
            assert result == "test-device-id"

    def test_get_computer_id_failure(self):
        """Test computer ID generation failure"""
        with patch(
            "src.utils.device_info.get_device_id",
            side_effect=Exception("Device ID error"),
        ):
            result = get_computer_id()
            assert result is None

    def test_get_device_id_with_mac(self):
        """Test device ID generation with MAC address"""
        with patch(
            "src.utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"
        ), patch("src.utils.device_info.get_computer_name", return_value="TEST-PC"):
            result = get_device_id()
            assert result == "001122334455"

    def test_get_device_id_without_mac(self):
        """Test device ID generation without MAC address"""
        with patch("src.utils.device_info.get_mac_address", return_value=None), patch(
            "src.utils.device_info.get_computer_name", return_value="TEST-PC"
        ), patch("platform.system", return_value="Windows"), patch(
            "platform.machine", return_value="AMD64"
        ):
            result = get_device_id()
            # Should be a 16-character hash
            assert len(result) == 16
            assert isinstance(result, str)

    def test_get_device_id_fallback(self):
        """Test device ID generation with complete failure"""
        with patch(
            "src.utils.device_info.get_mac_address", side_effect=Exception("MAC error")
        ), patch(
            "src.utils.device_info.get_computer_name",
            side_effect=Exception("Name error"),
        ), patch(
            "platform.system", side_effect=Exception("Platform error")
        ):
            result = get_device_id()
            # Should be a 16-character UUID
            assert len(result) == 16
            assert isinstance(result, str)

    def test_get_device_id_consistency(self):
        """Test that device ID is consistent across calls"""
        with patch(
            "src.utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"
        ), patch("src.utils.device_info.get_computer_name", return_value="TEST-PC"):
            result1 = get_device_id()
            result2 = get_device_id()
            assert result1 == result2

    def test_get_device_id_mac_address_formatting(self):
        """Test MAC address formatting in device ID"""
        test_cases = [
            ("00:11:22:33:44:55", "001122334455"),
            ("aa:bb:cc:dd:ee:ff", "aabbccddeeff"),
            ("12:34:56:78:9A:BC", "123456789abc"),
        ]

        for mac_address, expected in test_cases:
            with patch(
                "src.utils.device_info.get_mac_address", return_value=mac_address
            ), patch("src.utils.device_info.get_computer_name", return_value="TEST-PC"):
                result = get_device_id()
                assert result == expected

    def test_get_device_id_hash_generation(self):
        """Test hash generation for device ID without MAC"""
        with patch("src.utils.device_info.get_mac_address", return_value=None), patch(
            "src.utils.device_info.get_computer_name", return_value="TEST-PC"
        ), patch("platform.system", return_value="Windows"), patch(
            "platform.machine", return_value="AMD64"
        ):
            result = get_device_id()
            # Should be a valid hex string
            assert all(c in "0123456789abcdef" for c in result)
            assert len(result) == 16

    def test_get_device_id_exception_handling(self):
        """Test exception handling in device ID generation"""
        with patch(
            "src.utils.device_info.get_mac_address", side_effect=Exception("Test error")
        ), patch(
            "src.utils.device_info.get_computer_name",
            side_effect=Exception("Test error"),
        ), patch(
            "platform.system", side_effect=Exception("Test error")
        ):
            # Should not raise exception
            result = get_device_id()
            assert isinstance(result, str)
            assert len(result) == 16

    def test_get_computer_name_socket_error_types(self):
        """Test different types of socket errors"""
        error_types = [
            socket.gaierror("Name or service not known"),
            socket.herror("Host not found"),
            OSError("Network is unreachable"),
        ]

        for error in error_types:
            with patch("socket.gethostname", side_effect=error):
                result = get_computer_name()
                assert result == "Unknown-PC"

    def test_get_mac_address_uuid_error_types(self):
        """Test different types of UUID errors"""
        error_types = [
            OSError("Cannot get MAC address"),
            ValueError("Invalid MAC address"),
            Exception("Generic error"),
        ]

        for error in error_types:
            with patch("uuid.getnode", side_effect=error):
                result = get_mac_address()
                assert result is None

    def test_get_computer_id_device_id_error(self):
        """Test computer ID when device ID generation fails"""
        with patch(
            "src.utils.device_info.get_device_id",
            side_effect=Exception("Device ID error"),
        ):
            result = get_computer_id()
            assert result is None

    def test_get_computer_id_device_id_none(self):
        """Test computer ID when device ID returns None"""
        with patch("src.utils.device_info.get_device_id", return_value=None):
            result = get_computer_id()
            assert result is None

    def test_get_computer_id_device_id_empty(self):
        """Test computer ID when device ID returns empty string"""
        with patch("src.utils.device_info.get_device_id", return_value=""):
            result = get_computer_id()
            assert result is None

    def test_get_device_id_mac_address_edge_cases(self):
        """Test device ID with edge case MAC addresses"""
        edge_cases = [
            ("", None),  # Empty string should be treated as None
            ("invalid", None),  # Invalid format should be treated as None
            ("00:00:00:00:00:00", "000000000000"),  # All zeros
            ("ff:ff:ff:ff:ff:ff", "ffffffffffff"),  # All ones
        ]

        for mac_address, expected in edge_cases:
            with patch(
                "src.utils.device_info.get_mac_address", return_value=mac_address
            ), patch("src.utils.device_info.get_computer_name", return_value="TEST-PC"):
                result = get_device_id()
                if expected is None:
                    # Should fall back to hash generation
                    assert len(result) == 16
                    assert isinstance(result, str)
                else:
                    assert result == expected

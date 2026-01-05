"""
Tests for device_info utility
"""

import socket
from unittest.mock import patch

from utils.device_info import (
    get_computer_info,
    get_computer_name,
    get_device_id,
)


class TestGetComputerName:
    """Tests for get_computer_name function"""

    def test_success_windows(self):
        """Test successful computer name retrieval on Windows"""
        with patch("utils.device_info.platform.node", return_value="TEST-PC"):
            with patch("utils.device_info.platform.system", return_value="Windows"):
                result = get_computer_name()
                assert result == "TEST-PC"

    def test_success_linux(self):
        """Test successful computer name retrieval on Linux/Mac"""
        with patch("utils.device_info.socket.gethostname", return_value="LINUX-PC"):
            with patch("utils.device_info.platform.system", return_value="Linux"):
                result = get_computer_name()
                assert result == "LINUX-PC"

    def test_failure_returns_unknown(self):
        """Test computer name retrieval failure returns Unknown-PC"""
        with patch("utils.device_info.platform.system", side_effect=Exception("Error")):
            result = get_computer_name()
            assert result == "Unknown-PC"

    def test_error_types(self):
        """Test different types of errors during computer name retrieval"""
        error_types = [
            socket.gaierror("Name or service not known"),
            socket.herror("Host not found"),
            OSError("Network is unreachable"),
        ]
        for error in error_types:
            with patch("utils.device_info.platform.system", side_effect=error):
                result = get_computer_name()
                assert result == "Unknown-PC"


class TestGetDeviceId:
    """Tests for get_device_id function"""

    def test_with_mac_address(self):
        """Test device ID generation with MAC address"""
        with patch(
            "utils.device_info._get_mac_address", return_value="00:11:22:33:44:55"
        ):
            result = get_device_id()
            assert result == "001122334455"

    def test_without_mac_address(self):
        """Test device ID generation without MAC address"""
        with patch("utils.device_info._get_mac_address", return_value=None):
            with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
                with patch("utils.device_info.platform.system", return_value="Windows"):
                    with patch(
                        "utils.device_info.platform.machine", return_value="AMD64"
                    ):
                        result = get_device_id()
                        assert len(result) == 16
                        assert all(c in "0123456789abcdef" for c in result)

    def test_consistency(self):
        """Test that device ID is consistent across calls"""
        with patch(
            "utils.device_info._get_mac_address", return_value="00:11:22:33:44:55"
        ):
            result1 = get_device_id()
            result2 = get_device_id()
            assert result1 == result2

    def test_mac_address_formatting(self):
        """Test MAC address formatting in device ID"""
        test_cases = [
            ("00:11:22:33:44:55", "001122334455"),
            ("aa:bb:cc:dd:ee:ff", "aabbccddeeff"),
            ("12:34:56:78:9A:BC", "123456789abc"),
        ]
        for mac_address, expected in test_cases:
            with patch("utils.device_info._get_mac_address", return_value=mac_address):
                result = get_device_id()
                assert result == expected

    def test_fallback_on_exception(self):
        """Test device ID generation with complete failure"""
        with patch(
            "utils.device_info._get_mac_address", side_effect=Exception("Error")
        ):
            with patch(
                "utils.device_info.get_computer_name", side_effect=Exception("Error")
            ):
                with patch(
                    "utils.device_info.platform.system", side_effect=Exception("Error")
                ):
                    result = get_device_id()
                    assert len(result) == 16
                    assert isinstance(result, str)


class TestGetComputerInfo:
    """Tests for get_computer_info function"""

    def test_returns_dict(self):
        """Test computer_info returns dictionary"""
        with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
            with patch("utils.device_info.get_device_id", return_value="abc123"):
                result = get_computer_info()
                assert isinstance(result, dict)

    def test_contains_computer_name(self):
        """Test computer_info contains computerName"""
        with patch("utils.device_info.get_computer_name", return_value="MY-PC"):
            with patch("utils.device_info.get_device_id", return_value="abc123"):
                result = get_computer_info()
                assert result["computerName"] == "MY-PC"

    def test_contains_device_id(self):
        """Test computer_info contains deviceId"""
        with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
            with patch("utils.device_info.get_device_id", return_value="device123"):
                result = get_computer_info()
                assert result["deviceId"] == "device123"

    def test_minimal_fields_only(self):
        """Test computer_info only contains minimal required fields"""
        with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
            with patch("utils.device_info.get_device_id", return_value="abc123"):
                result = get_computer_info()
                # isActive is derived from currentUserId, not stored in initial info
                assert set(result.keys()) == {"computerName", "deviceId"}

    def test_failure_returns_fallback(self):
        """Test computer_info returns fallback on failure"""
        with patch(
            "utils.device_info.get_computer_name", side_effect=Exception("Error")
        ):
            result = get_computer_info()
            assert result["computerName"] == "Unknown-PC"
            assert "deviceId" in result

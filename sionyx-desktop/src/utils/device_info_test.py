"""
Tests for device_info utility
"""

import socket
from unittest.mock import patch

from utils.device_info import (
    get_computer_name,
    get_device_id,
    get_mac_address,
    get_hardware_fingerprint,
    get_os_info,
    get_network_info,
    get_computer_info,
)


class TestDeviceInfo:
    """Test cases for device information utilities"""

    def test_get_computer_name_success(self):
        """Test successful computer name retrieval"""
        # On Windows, platform.node() is used first; on Linux/Mac, socket.gethostname()
        with patch("utils.device_info.platform.node", return_value="TEST-PC"):
            with patch("utils.device_info.platform.system", return_value="Windows"):
                result = get_computer_name()
                assert result == "TEST-PC"

    def test_get_computer_name_success_linux(self):
        """Test successful computer name retrieval on Linux/Mac"""
        with patch("utils.device_info.socket.gethostname", return_value="LINUX-PC"):
            with patch("utils.device_info.platform.system", return_value="Linux"):
                result = get_computer_name()
                assert result == "LINUX-PC"

    def test_get_computer_name_failure(self):
        """Test computer name retrieval failure"""
        with patch("utils.device_info.platform.system", side_effect=Exception("Error")):
            result = get_computer_name()
            assert result == "unknown-pc"  # Note: lowercase in implementation

    def test_get_mac_address_success(self):
        """Test successful MAC address retrieval"""
        with patch("utils.device_info.uuid.getnode", return_value=0x123456789ABC):
            result = get_mac_address()
            # MAC is formatted from the node value
            assert result is not None
            assert ":" in result

    def test_get_mac_address_failure(self):
        """Test MAC address retrieval failure"""
        with patch("utils.device_info.uuid.getnode", side_effect=Exception("MAC error")):
            result = get_mac_address()
            assert result is None

    def test_get_device_id_with_mac(self):
        """Test device ID generation with MAC address"""
        with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
            with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
                result = get_device_id()
                assert result == "001122334455"

    def test_get_device_id_without_mac(self):
        """Test device ID generation without MAC address"""
        with patch("utils.device_info.get_mac_address", return_value=None):
            with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
                with patch("utils.device_info.platform.system", return_value="Windows"):
                    with patch("utils.device_info.platform.machine", return_value="AMD64"):
                        result = get_device_id()
                        assert len(result) == 16
                        assert isinstance(result, str)

    def test_get_device_id_fallback(self):
        """Test device ID generation with complete failure"""
        with patch("utils.device_info.get_mac_address", side_effect=Exception("MAC error")):
            with patch("utils.device_info.get_computer_name", side_effect=Exception("Name error")):
                with patch("utils.device_info.platform.system", side_effect=Exception("Platform error")):
                    result = get_device_id()
                    assert len(result) == 16
                    assert isinstance(result, str)

    def test_get_device_id_consistency(self):
        """Test that device ID is consistent across calls"""
        with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
            with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
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
            with patch("utils.device_info.get_mac_address", return_value=mac_address):
                with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
                    result = get_device_id()
                    assert result == expected

    def test_get_device_id_hash_generation(self):
        """Test hash generation for device ID without MAC"""
        with patch("utils.device_info.get_mac_address", return_value=None):
            with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
                with patch("utils.device_info.platform.system", return_value="Windows"):
                    with patch("utils.device_info.platform.machine", return_value="AMD64"):
                        result = get_device_id()
                        assert all(c in "0123456789abcdef" for c in result)
                        assert len(result) == 16

    def test_get_device_id_exception_handling(self):
        """Test exception handling in device ID generation"""
        with patch("utils.device_info.get_mac_address", side_effect=Exception("Test error")):
            with patch("utils.device_info.get_computer_name", side_effect=Exception("Test error")):
                with patch("utils.device_info.platform.system", side_effect=Exception("Test error")):
                    result = get_device_id()
                    assert isinstance(result, str)
                    assert len(result) == 16

    def test_get_computer_name_error_types(self):
        """Test different types of errors during computer name retrieval"""
        error_types = [
            socket.gaierror("Name or service not known"),
            socket.herror("Host not found"),
            OSError("Network is unreachable"),
        ]

        for error in error_types:
            with patch("utils.device_info.platform.system", side_effect=error):
                result = get_computer_name()
                assert result == "unknown-pc"

    def test_get_mac_address_uuid_error_types(self):
        """Test different types of UUID errors"""
        error_types = [
            OSError("Cannot get MAC address"),
            ValueError("Invalid MAC address"),
            Exception("Generic error"),
        ]

        for error in error_types:
            with patch("utils.device_info.uuid.getnode", side_effect=error):
                result = get_mac_address()
                assert result is None

    def test_get_device_id_mac_address_edge_cases(self):
        """Test device ID with edge case MAC addresses"""
        edge_cases = [
            ("00:00:00:00:00:00", "000000000000"),
            ("ff:ff:ff:ff:ff:ff", "ffffffffffff"),
        ]

        for mac_address, expected in edge_cases:
            with patch("utils.device_info.get_mac_address", return_value=mac_address):
                with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
                    result = get_device_id()
                    assert result == expected


# =============================================================================
# get_hardware_fingerprint tests
# =============================================================================
class TestGetHardwareFingerprint:
    """Tests for get_hardware_fingerprint function"""

    def test_returns_string(self):
        """Test fingerprint returns string"""
        with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
            with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
                with patch("utils.device_info.platform.system", return_value="Windows"):
                    with patch("utils.device_info.platform.machine", return_value="AMD64"):
                        with patch("utils.device_info.platform.processor", return_value="Intel"):
                            result = get_hardware_fingerprint()
                            assert isinstance(result, str)

    def test_fingerprint_length(self):
        """Test fingerprint is 32 characters"""
        with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
            with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
                with patch("utils.device_info.platform.system", return_value="Windows"):
                    with patch("utils.device_info.platform.machine", return_value="AMD64"):
                        with patch("utils.device_info.platform.processor", return_value="Intel"):
                            result = get_hardware_fingerprint()
                            assert len(result) == 32

    def test_fingerprint_is_hex(self):
        """Test fingerprint is hex string"""
        with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
            with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
                with patch("utils.device_info.platform.system", return_value="Windows"):
                    with patch("utils.device_info.platform.machine", return_value="AMD64"):
                        with patch("utils.device_info.platform.processor", return_value="Intel"):
                            result = get_hardware_fingerprint()
                            assert all(c in "0123456789abcdef" for c in result)

    def test_fingerprint_without_mac(self):
        """Test fingerprint works without MAC"""
        with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
            with patch("utils.device_info.get_mac_address", return_value=None):
                with patch("utils.device_info.platform.system", return_value="Windows"):
                    with patch("utils.device_info.platform.machine", return_value="AMD64"):
                        with patch("utils.device_info.platform.processor", return_value="Intel"):
                            result = get_hardware_fingerprint()
                            assert len(result) == 32

    def test_fingerprint_failure_fallback(self):
        """Test fingerprint fallback on complete failure"""
        with patch("utils.device_info.get_computer_name", side_effect=Exception("Error")):
            result = get_hardware_fingerprint()
            # Falls back to UUID
            assert isinstance(result, str)
            assert len(result) > 0


# =============================================================================
# get_os_info tests
# =============================================================================
class TestGetOsInfo:
    """Tests for get_os_info function"""

    def test_returns_dict(self):
        """Test os_info returns dictionary"""
        result = get_os_info()
        assert isinstance(result, dict)

    def test_contains_system(self):
        """Test os_info contains system key"""
        result = get_os_info()
        assert "system" in result

    def test_contains_release(self):
        """Test os_info contains release key"""
        result = get_os_info()
        assert "release" in result

    def test_contains_version(self):
        """Test os_info contains version key"""
        result = get_os_info()
        assert "version" in result

    def test_contains_machine(self):
        """Test os_info contains machine key"""
        result = get_os_info()
        assert "machine" in result

    def test_contains_processor(self):
        """Test os_info contains processor key"""
        result = get_os_info()
        assert "processor" in result

    def test_contains_architecture(self):
        """Test os_info contains architecture key"""
        result = get_os_info()
        assert "architecture" in result

    def test_failure_returns_unknown(self):
        """Test os_info returns Unknown on failure"""
        with patch("utils.device_info.platform.system", side_effect=Exception("Error")):
            result = get_os_info()
            assert result["system"] == "Unknown"


# =============================================================================
# get_network_info tests
# =============================================================================
class TestGetNetworkInfo:
    """Tests for get_network_info function"""

    def test_returns_dict(self):
        """Test network_info returns dictionary"""
        with patch("utils.device_info.socket.gethostname", return_value="TEST-PC"):
            with patch("utils.device_info.socket.gethostbyname", return_value="192.168.1.1"):
                with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
                    result = get_network_info()
                    assert isinstance(result, dict)

    def test_contains_hostname(self):
        """Test network_info contains hostname"""
        with patch("utils.device_info.socket.gethostname", return_value="TEST-PC"):
            with patch("utils.device_info.socket.gethostbyname", return_value="192.168.1.1"):
                with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
                    result = get_network_info()
                    assert "hostname" in result
                    assert result["hostname"] == "TEST-PC"

    def test_contains_local_ip(self):
        """Test network_info contains local_ip"""
        with patch("utils.device_info.socket.gethostname", return_value="TEST-PC"):
            with patch("utils.device_info.socket.gethostbyname", return_value="192.168.1.100"):
                with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
                    result = get_network_info()
                    assert "local_ip" in result
                    assert result["local_ip"] == "192.168.1.100"

    def test_contains_mac_address(self):
        """Test network_info contains mac_address"""
        with patch("utils.device_info.socket.gethostname", return_value="TEST-PC"):
            with patch("utils.device_info.socket.gethostbyname", return_value="192.168.1.1"):
                with patch("utils.device_info.get_mac_address", return_value="AA:BB:CC:DD:EE:FF"):
                    result = get_network_info()
                    assert "mac_address" in result
                    assert result["mac_address"] == "AA:BB:CC:DD:EE:FF"

    def test_failure_returns_unknown(self):
        """Test network_info returns Unknown on failure"""
        with patch("utils.device_info.socket.gethostname", side_effect=Exception("Error")):
            result = get_network_info()
            assert result["hostname"] == "Unknown"
            assert result["local_ip"] == "Unknown"


# =============================================================================
# get_computer_info tests
# =============================================================================
class TestGetComputerInfo:
    """Tests for get_computer_info function"""

    def test_returns_dict(self):
        """Test computer_info returns dictionary"""
        with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
            with patch("utils.device_info.get_device_id", return_value="abc123"):
                with patch("utils.device_info.get_hardware_fingerprint", return_value="xyz789"):
                    with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
                        with patch("utils.device_info.get_os_info", return_value={"system": "Windows"}):
                            with patch("utils.device_info.get_network_info", return_value={"hostname": "TEST-PC"}):
                                result = get_computer_info()
                                assert isinstance(result, dict)

    def test_contains_computer_name(self):
        """Test computer_info contains computerName"""
        with patch("utils.device_info.get_computer_name", return_value="MY-PC"):
            with patch("utils.device_info.get_device_id", return_value="abc123"):
                with patch("utils.device_info.get_hardware_fingerprint", return_value="xyz789"):
                    with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
                        with patch("utils.device_info.get_os_info", return_value={"system": "Windows"}):
                            with patch("utils.device_info.get_network_info", return_value={"hostname": "MY-PC"}):
                                result = get_computer_info()
                                assert result["computerName"] == "MY-PC"

    def test_contains_device_id(self):
        """Test computer_info contains deviceId"""
        with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
            with patch("utils.device_info.get_device_id", return_value="device123"):
                with patch("utils.device_info.get_hardware_fingerprint", return_value="xyz789"):
                    with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
                        with patch("utils.device_info.get_os_info", return_value={"system": "Windows"}):
                            with patch("utils.device_info.get_network_info", return_value={"hostname": "TEST-PC"}):
                                result = get_computer_info()
                                assert result["deviceId"] == "device123"

    def test_contains_hardware_id(self):
        """Test computer_info contains hardwareId"""
        with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
            with patch("utils.device_info.get_device_id", return_value="abc123"):
                with patch("utils.device_info.get_hardware_fingerprint", return_value="hardware456"):
                    with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
                        with patch("utils.device_info.get_os_info", return_value={"system": "Windows"}):
                            with patch("utils.device_info.get_network_info", return_value={"hostname": "TEST-PC"}):
                                result = get_computer_info()
                                assert result["hardwareId"] == "hardware456"

    def test_contains_is_active(self):
        """Test computer_info contains isActive"""
        with patch("utils.device_info.get_computer_name", return_value="TEST-PC"):
            with patch("utils.device_info.get_device_id", return_value="abc123"):
                with patch("utils.device_info.get_hardware_fingerprint", return_value="xyz789"):
                    with patch("utils.device_info.get_mac_address", return_value="00:11:22:33:44:55"):
                        with patch("utils.device_info.get_os_info", return_value={"system": "Windows"}):
                            with patch("utils.device_info.get_network_info", return_value={"hostname": "TEST-PC"}):
                                result = get_computer_info()
                                assert result["isActive"] is True

    def test_failure_returns_fallback(self):
        """Test computer_info returns fallback on failure"""
        with patch("utils.device_info.get_computer_name", side_effect=Exception("Error")):
            result = get_computer_info()
            assert result["computerName"] == "Unknown-PC"
            assert result["isActive"] is True


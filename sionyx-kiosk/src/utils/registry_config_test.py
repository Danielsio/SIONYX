"""
Tests for Windows Registry Configuration Reader
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestIsProduction:
    """Tests for is_production function"""

    def test_returns_false_when_not_frozen(self):
        """Test returns False when running as script"""
        from utils.registry_config import is_production

        # Ensure frozen attribute is not set
        if hasattr(sys, "frozen"):
            delattr(sys, "frozen")

        assert is_production() is False

    def test_returns_true_when_frozen(self):
        """Test returns True when running as PyInstaller executable"""
        from utils.registry_config import is_production

        with patch.object(sys, "frozen", True, create=True):
            assert is_production() is True


class TestReadRegistryValue:
    """Tests for read_registry_value function"""

    def test_returns_value_when_exists(self):
        """Test returns registry value when it exists"""
        from utils.registry_config import read_registry_value

        mock_key = MagicMock()

        with patch("utils.registry_config.winreg") as mock_winreg:
            mock_winreg.OpenKey.return_value = mock_key
            mock_winreg.QueryValueEx.return_value = ("test-value", 1)
            mock_winreg.HKEY_LOCAL_MACHINE = 0x80000002

            result = read_registry_value("TestKey")

            assert result == "test-value"
            mock_winreg.CloseKey.assert_called_once_with(mock_key)

    def test_returns_default_when_not_found(self):
        """Test returns default value when registry key not found"""
        from utils.registry_config import read_registry_value

        with patch("utils.registry_config.winreg") as mock_winreg:
            mock_winreg.OpenKey.side_effect = OSError("Not found")
            mock_winreg.HKEY_LOCAL_MACHINE = 0x80000002

            result = read_registry_value("MissingKey", default="fallback")

            assert result == "fallback"

    def test_returns_none_when_no_default(self):
        """Test returns None when key not found and no default"""
        from utils.registry_config import read_registry_value

        with patch("utils.registry_config.winreg") as mock_winreg:
            mock_winreg.OpenKey.side_effect = OSError("Not found")
            mock_winreg.HKEY_LOCAL_MACHINE = 0x80000002

            result = read_registry_value("MissingKey")

            assert result is None

    def test_returns_default_when_winreg_not_available(self):
        """Test returns default when winreg module not available (non-Windows)"""
        from utils import registry_config

        # Temporarily set winreg to None
        original_winreg = registry_config.winreg
        registry_config.winreg = None

        try:
            result = registry_config.read_registry_value("AnyKey", default="default")
            assert result == "default"
        finally:
            registry_config.winreg = original_winreg


class TestGetAllConfig:
    """Tests for get_all_config function"""

    def test_returns_all_config_values(self):
        """Test returns dictionary with all config values"""
        from utils.registry_config import get_all_config

        config_values = {
            "OrgId": "test-org",
            "FirebaseApiKey": "test-api-key",
            "FirebaseAuthDomain": "test.firebaseapp.com",
            "FirebaseProjectId": "test-project",
            "FirebaseDatabaseUrl": "https://test.firebaseio.com",
            "FirebaseStorageBucket": "test.appspot.com",
            "FirebaseMessagingSenderId": "123456",
            "FirebaseAppId": "1:123:web:abc",
            "FirebaseMeasurementId": "G-TEST",
        }

        mock_key = MagicMock()

        with patch("utils.registry_config.winreg") as mock_winreg:
            mock_winreg.OpenKey.return_value = mock_key
            mock_winreg.QueryValueEx.side_effect = lambda k, name: (
                config_values.get(name),
                1,
            )
            mock_winreg.HKEY_LOCAL_MACHINE = 0x80000002

            result = get_all_config()

            assert result["org_id"] == "test-org"
            assert result["api_key"] == "test-api-key"
            assert result["auth_domain"] == "test.firebaseapp.com"
            assert result["project_id"] == "test-project"
            assert result["database_url"] == "https://test.firebaseio.com"

    def test_returns_none_for_missing_values(self):
        """Test returns None for values not in registry"""
        from utils.registry_config import get_all_config

        with patch("utils.registry_config.winreg") as mock_winreg:
            mock_winreg.OpenKey.side_effect = OSError("Not found")
            mock_winreg.HKEY_LOCAL_MACHINE = 0x80000002

            result = get_all_config()

            assert result["org_id"] is None
            assert result["api_key"] is None


class TestRegistryConfigExists:
    """Tests for registry_config_exists function"""

    def test_returns_true_when_config_exists(self):
        """Test returns True when registry key and OrgId exist"""
        from utils.registry_config import registry_config_exists

        mock_key = MagicMock()

        with patch("utils.registry_config.winreg") as mock_winreg:
            mock_winreg.OpenKey.return_value = mock_key
            mock_winreg.QueryValueEx.return_value = ("test-org", 1)
            mock_winreg.HKEY_LOCAL_MACHINE = 0x80000002

            assert registry_config_exists() is True

    def test_returns_false_when_key_missing(self):
        """Test returns False when registry key doesn't exist"""
        from utils.registry_config import registry_config_exists

        with patch("utils.registry_config.winreg") as mock_winreg:
            mock_winreg.OpenKey.side_effect = OSError("Not found")
            mock_winreg.HKEY_LOCAL_MACHINE = 0x80000002

            assert registry_config_exists() is False

    def test_returns_false_when_winreg_not_available(self):
        """Test returns False when winreg module not available"""
        from utils import registry_config

        original_winreg = registry_config.winreg
        registry_config.winreg = None

        try:
            assert registry_config.registry_config_exists() is False
        finally:
            registry_config.winreg = original_winreg

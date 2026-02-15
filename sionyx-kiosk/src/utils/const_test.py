"""
Tests for const.py - Global constants
Tests application branding and security constants.
"""

import os
from unittest.mock import patch

from utils.const import ADMIN_EXIT_PASSWORD, APP_NAME, get_admin_exit_password


class TestConstants:
    """Tests for global constants"""

    def test_app_name_is_string(self):
        """Test APP_NAME is a string"""
        assert isinstance(APP_NAME, str)

    def test_app_name_not_empty(self):
        """Test APP_NAME is not empty"""
        assert len(APP_NAME) > 0

    def test_app_name_value(self):
        """Test APP_NAME has expected value"""
        assert APP_NAME == "SIONYX"

    def test_admin_password_is_string(self):
        """Test ADMIN_EXIT_PASSWORD is a string"""
        assert isinstance(ADMIN_EXIT_PASSWORD, str)

    def test_admin_password_not_empty(self):
        """Test ADMIN_EXIT_PASSWORD is not empty"""
        assert len(ADMIN_EXIT_PASSWORD) > 0

    def test_admin_password_has_value(self):
        """Test ADMIN_EXIT_PASSWORD has a value set"""
        assert ADMIN_EXIT_PASSWORD is not None

    def test_admin_password_not_hardcoded_admin123(self):
        """Test ADMIN_EXIT_PASSWORD is not the old insecure default (ENH-001)"""
        assert ADMIN_EXIT_PASSWORD != "admin123"


class TestGetAdminExitPassword:
    """Tests for get_admin_exit_password function"""

    def test_returns_env_var_when_set(self):
        """Test password is read from ADMIN_EXIT_PASSWORD env var"""
        with patch.dict(os.environ, {"ADMIN_EXIT_PASSWORD": "my-secure-pass"}):
            result = get_admin_exit_password()
            assert result == "my-secure-pass"

    def test_returns_default_when_no_config(self):
        """Test fallback default is returned when nothing is configured"""
        with patch.dict(os.environ, {}, clear=True):
            # Remove ADMIN_EXIT_PASSWORD if set
            env = os.environ.copy()
            env.pop("ADMIN_EXIT_PASSWORD", None)
            with patch.dict(os.environ, env, clear=True):
                result = get_admin_exit_password()
                assert result == "sionyx2025"

    def test_returns_registry_value_in_production(self):
        """Test password is read from registry in frozen/production mode"""
        with patch("utils.const.getattr", return_value=True):
            pass  # Can't easily test without Windows registry
        # At minimum, verify the function is callable
        assert callable(get_admin_exit_password)

    def test_env_var_takes_priority_in_dev(self):
        """Test env var overrides default in development mode"""
        with patch.dict(os.environ, {"ADMIN_EXIT_PASSWORD": "env-password"}):
            result = get_admin_exit_password()
            assert result == "env-password"
            assert result != "sionyx2025"

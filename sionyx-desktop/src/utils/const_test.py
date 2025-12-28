"""
Tests for const.py - Global constants
Tests application branding and security constants.
"""

import pytest

from utils.const import APP_NAME, ADMIN_EXIT_PASSWORD


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





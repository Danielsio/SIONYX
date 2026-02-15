"""
Tests for Operating Hours Service
"""

from datetime import datetime, time
from unittest.mock import MagicMock, patch

import pytest

from services.operating_hours_service import (
    DEFAULT_OPERATING_HOURS,
    OperatingHoursService,
)


@pytest.fixture
def mock_firebase():
    """Create mock Firebase client"""
    firebase = MagicMock()
    firebase.org_id = "test-org"
    return firebase


@pytest.fixture
def service(mock_firebase):
    """Create service instance"""
    return OperatingHoursService(mock_firebase)


class TestOperatingHoursService:
    """Tests for OperatingHoursService"""

    def test_init_with_defaults(self, service):
        """Test service initializes with default settings"""
        assert service.settings["enabled"] is False
        assert service.settings["startTime"] == "06:00"
        assert service.settings["endTime"] == "00:00"
        assert service.settings["gracePeriodMinutes"] == 5
        assert service.settings["graceBehavior"] == "graceful"

    def test_load_settings_success(self, service, mock_firebase):
        """Test loading settings from Firebase"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {
                "enabled": True,
                "startTime": "08:00",
                "endTime": "22:00",
                "gracePeriodMinutes": 10,
                "graceBehavior": "force",
            },
        }

        result = service.load_settings()

        assert result["success"] is True
        assert service.settings["enabled"] is True
        assert service.settings["startTime"] == "08:00"
        assert service.settings["endTime"] == "22:00"
        assert service.settings["gracePeriodMinutes"] == 10
        assert service.settings["graceBehavior"] == "force"

    def test_load_settings_uses_defaults_on_failure(self, service, mock_firebase):
        """Test that defaults are used when loading fails"""
        mock_firebase.db_get.return_value = {"success": False, "error": "Network error"}

        result = service.load_settings()

        assert result["success"] is True
        assert result.get("is_default") is True
        assert service.settings == DEFAULT_OPERATING_HOURS

    def test_load_settings_uses_defaults_on_no_data(self, service, mock_firebase):
        """Test that defaults are used when no data exists"""
        mock_firebase.db_get.return_value = {"success": True, "data": None}

        result = service.load_settings()

        assert result["success"] is True
        assert result.get("is_default") is True

    def test_is_within_operating_hours_disabled(self, service):
        """Test that disabled hours always allow access"""
        service.settings["enabled"] = False

        is_within, reason = service.is_within_operating_hours()

        assert is_within is True
        assert reason is None

    @patch("services.operating_hours_service.datetime")
    def test_is_within_operating_hours_normal_hours(self, mock_datetime, service):
        """Test normal operating hours (e.g., 06:00 - 22:00)"""
        service.settings = {
            "enabled": True,
            "startTime": "06:00",
            "endTime": "22:00",
            "gracePeriodMinutes": 5,
            "graceBehavior": "graceful",
        }

        # Test within hours (10:00)
        mock_now = MagicMock()
        mock_now.time.return_value = time(10, 0)
        mock_datetime.now.return_value = mock_now

        is_within, reason = service.is_within_operating_hours()
        assert is_within is True

        # Test outside hours (04:00)
        mock_now.time.return_value = time(4, 0)
        is_within, reason = service.is_within_operating_hours()
        assert is_within is False
        assert "06:00" in reason

        # Test outside hours (23:00)
        mock_now.time.return_value = time(23, 0)
        is_within, reason = service.is_within_operating_hours()
        assert is_within is False

    @patch("services.operating_hours_service.datetime")
    def test_is_within_operating_hours_overnight(self, mock_datetime, service):
        """Test overnight operating hours (e.g., 22:00 - 06:00)"""
        service.settings = {
            "enabled": True,
            "startTime": "22:00",
            "endTime": "06:00",
            "gracePeriodMinutes": 5,
            "graceBehavior": "graceful",
        }

        # Test within hours (23:00)
        mock_now = MagicMock()
        mock_now.time.return_value = time(23, 0)
        mock_datetime.now.return_value = mock_now

        is_within, reason = service.is_within_operating_hours()
        assert is_within is True

        # Test within hours (03:00)
        mock_now.time.return_value = time(3, 0)
        is_within, reason = service.is_within_operating_hours()
        assert is_within is True

        # Test outside hours (12:00)
        mock_now.time.return_value = time(12, 0)
        is_within, reason = service.is_within_operating_hours()
        assert is_within is False

    def test_get_minutes_until_closing_disabled(self, service):
        """Test minutes calculation when hours disabled"""
        service.settings["enabled"] = False

        minutes = service.get_minutes_until_closing()

        assert minutes == -1

    @patch("services.operating_hours_service.datetime")
    def test_get_minutes_until_closing(self, mock_datetime, service):
        """Test minutes until closing calculation"""
        service.settings = {
            "enabled": True,
            "startTime": "06:00",
            "endTime": "22:00",
            "gracePeriodMinutes": 5,
            "graceBehavior": "graceful",
        }

        # Current time is 21:30, should be 30 minutes left
        mock_now = datetime(2024, 1, 15, 21, 30, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.combine = datetime.combine

        minutes = service.get_minutes_until_closing()

        assert minutes == 30

    def test_should_warn_grace_period_disabled(self, service):
        """Test grace period warning when hours disabled"""
        service.settings["enabled"] = False

        should_warn = service.should_warn_grace_period()

        assert should_warn is False

    def test_should_warn_grace_period_already_warned(self, service):
        """Test grace period warning when already warned"""
        service.settings["enabled"] = True
        service.warned_grace = True

        should_warn = service.should_warn_grace_period()

        assert should_warn is False

    @patch("services.operating_hours_service.datetime")
    def test_should_warn_grace_period(self, mock_datetime, service):
        """Test grace period warning triggers correctly"""
        service.settings = {
            "enabled": True,
            "startTime": "06:00",
            "endTime": "22:00",
            "gracePeriodMinutes": 5,
            "graceBehavior": "graceful",
        }
        service.warned_grace = False

        # 3 minutes until closing
        mock_now = datetime(2024, 1, 15, 21, 57, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.combine = datetime.combine

        should_warn = service.should_warn_grace_period()

        assert should_warn is True

    def test_parse_time_valid(self, service):
        """Test parsing valid time strings"""
        assert service._parse_time("06:00") == time(6, 0)
        assert service._parse_time("22:30") == time(22, 30)
        assert service._parse_time("00:00") == time(0, 0)
        assert service._parse_time("23:59") == time(23, 59)

    def test_parse_time_invalid(self, service):
        """Test parsing invalid time strings"""
        assert service._parse_time("invalid") is None
        assert service._parse_time("25:00") is None
        assert service._parse_time("12:60") is None
        assert service._parse_time("") is None

    def test_start_monitoring(self, service, mock_firebase):
        """Test starting monitoring"""
        mock_firebase.db_get.return_value = {"success": True, "data": None}

        service.start_monitoring()

        assert service.is_monitoring is True
        assert service.check_timer.isActive()

    def test_stop_monitoring(self, service):
        """Test stopping monitoring"""
        service.is_monitoring = True
        service.check_timer.start(30000)

        service.stop_monitoring()

        assert service.is_monitoring is False
        assert not service.check_timer.isActive()

    def test_get_settings(self, service):
        """Test getting current settings"""
        service.settings["enabled"] = True
        service.settings["startTime"] = "09:00"

        settings = service.get_settings()

        assert settings["enabled"] is True
        assert settings["startTime"] == "09:00"
        # Ensure it's a copy
        settings["enabled"] = False
        assert service.settings["enabled"] is True

    def test_is_enabled(self, service):
        """Test checking if hours are enabled"""
        service.settings["enabled"] = False
        assert service.is_enabled() is False

        service.settings["enabled"] = True
        assert service.is_enabled() is True

    def test_cleanup(self, service):
        """Test cleanup"""
        service.is_monitoring = True
        service.check_timer.start(30000)

        service.cleanup()

        assert service.is_monitoring is False
        assert not service.check_timer.isActive()

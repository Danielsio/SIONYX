"""
Operating Hours Service
Checks and enforces organization operating hours restrictions.
"""

from datetime import datetime, time
from typing import Any, Dict, Optional, Tuple

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from services.firebase_client import FirebaseClient
from utils.logger import get_logger


logger = get_logger(__name__)


# Default operating hours settings
DEFAULT_OPERATING_HOURS = {
    "enabled": False,
    "startTime": "06:00",
    "endTime": "00:00",  # Midnight
    "gracePeriodMinutes": 5,
    "graceBehavior": "graceful",  # 'graceful' or 'force'
}


class OperatingHoursService(QObject):
    """
    Service for checking and enforcing operating hours.
    
    Emits signals when:
    - Operating hours start/end
    - Grace period begins
    - Session should end due to hours
    """
    
    # Signals
    hours_started = pyqtSignal()  # Operating hours have started
    hours_ending_soon = pyqtSignal(int)  # Emits minutes until closing
    hours_ended = pyqtSignal(str)  # Emits grace behavior ('graceful' or 'force')
    settings_updated = pyqtSignal(dict)  # Emits new settings
    
    def __init__(self, firebase_client: FirebaseClient):
        super().__init__()
        self.firebase = firebase_client
        self.settings: Dict[str, Any] = {**DEFAULT_OPERATING_HOURS}
        self.is_monitoring = False
        
        # Timer for periodic checks (every 30 seconds)
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_operating_hours)
        
        # State tracking
        self.warned_grace = False
        self.grace_warned_at: Optional[datetime] = None
        
        logger.info("Operating hours service initialized")
    
    def load_settings(self) -> Dict[str, Any]:
        """
        Load operating hours settings from Firebase.
        
        Returns:
            Dict with success status and settings
        """
        try:
            result = self.firebase.db_get("metadata/settings/operatingHours")
            
            if not result.get("success"):
                logger.warning("Failed to load operating hours, using defaults")
                return {
                    "success": True,
                    "settings": {**DEFAULT_OPERATING_HOURS},
                    "is_default": True,
                }
            
            data = result.get("data")
            if not data:
                logger.info("No operating hours configured, using defaults")
                return {
                    "success": True,
                    "settings": {**DEFAULT_OPERATING_HOURS},
                    "is_default": True,
                }
            
            # Merge with defaults for any missing fields
            self.settings = {
                "enabled": data.get("enabled", DEFAULT_OPERATING_HOURS["enabled"]),
                "startTime": data.get("startTime", DEFAULT_OPERATING_HOURS["startTime"]),
                "endTime": data.get("endTime", DEFAULT_OPERATING_HOURS["endTime"]),
                "gracePeriodMinutes": data.get(
                    "gracePeriodMinutes", DEFAULT_OPERATING_HOURS["gracePeriodMinutes"]
                ),
                "graceBehavior": data.get(
                    "graceBehavior", DEFAULT_OPERATING_HOURS["graceBehavior"]
                ),
            }
            
            logger.info(f"Operating hours loaded: enabled={self.settings['enabled']}")
            self.settings_updated.emit(self.settings)
            
            return {"success": True, "settings": self.settings}
            
        except Exception as e:
            logger.error(f"Error loading operating hours: {e}")
            return {"success": False, "error": str(e)}
    
    def is_within_operating_hours(self) -> Tuple[bool, Optional[str]]:
        """
        Check if current time is within operating hours.
        
        Returns:
            Tuple of (is_allowed, reason_if_not)
        """
        if not self.settings.get("enabled", False):
            return True, None
        
        now = datetime.now()
        current_time = now.time()
        
        start_time = self._parse_time(self.settings["startTime"])
        end_time = self._parse_time(self.settings["endTime"])
        
        if start_time is None or end_time is None:
            logger.warning("Invalid time format in settings, allowing access")
            return True, None
        
        # Handle overnight hours (e.g., 22:00 - 06:00)
        if start_time <= end_time:
            # Normal hours (e.g., 06:00 - 22:00)
            is_within = start_time <= current_time <= end_time
        else:
            # Overnight hours (e.g., 22:00 - 06:00)
            is_within = current_time >= start_time or current_time <= end_time
        
        if not is_within:
            reason = (
                f"שעות הפעילות הן בין {self.settings['startTime']} "
                f"ל-{self.settings['endTime']}"
            )
            return False, reason
        
        return True, None
    
    def get_minutes_until_closing(self) -> int:
        """
        Get minutes remaining until operating hours end.
        
        Returns:
            Minutes until closing, or -1 if hours not enabled
        """
        if not self.settings.get("enabled", False):
            return -1
        
        now = datetime.now()
        end_time = self._parse_time(self.settings["endTime"])
        
        if end_time is None:
            return -1
        
        # Create datetime for end time today
        end_datetime = datetime.combine(now.date(), end_time)
        
        # If end time is before current time, it's tomorrow
        if end_datetime <= now:
            from datetime import timedelta
            end_datetime += timedelta(days=1)
        
        delta = end_datetime - now
        return int(delta.total_seconds() / 60)
    
    def should_warn_grace_period(self) -> bool:
        """
        Check if we should warn about grace period.
        
        Returns:
            True if warning should be shown
        """
        if not self.settings.get("enabled", False):
            return False
        
        if self.warned_grace:
            return False
        
        minutes_left = self.get_minutes_until_closing()
        grace_minutes = self.settings.get("gracePeriodMinutes", 5)
        
        return 0 < minutes_left <= grace_minutes
    
    def start_monitoring(self):
        """Start monitoring operating hours"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.warned_grace = False
        self.grace_warned_at = None
        
        # Load initial settings
        self.load_settings()
        
        # Start check timer (every 30 seconds)
        self.check_timer.start(30000)
        
        logger.info("Operating hours monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring operating hours"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.check_timer.stop()
        
        logger.info("Operating hours monitoring stopped")
    
    def _check_operating_hours(self):
        """Periodic check of operating hours"""
        if not self.settings.get("enabled", False):
            return
        
        is_within, reason = self.is_within_operating_hours()
        
        if not is_within:
            # Hours have ended
            logger.warning("Operating hours ended")
            self.hours_ended.emit(self.settings.get("graceBehavior", "graceful"))
            return
        
        # Check for grace period warning
        if self.should_warn_grace_period():
            minutes_left = self.get_minutes_until_closing()
            logger.warning(f"Operating hours ending in {minutes_left} minutes")
            self.warned_grace = True
            self.grace_warned_at = datetime.now()
            self.hours_ending_soon.emit(minutes_left)
    
    def _parse_time(self, time_str: str) -> Optional[time]:
        """
        Parse time string in HH:mm format.
        
        Args:
            time_str: Time string like "06:00" or "23:30"
            
        Returns:
            time object or None if invalid
        """
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                return None
            
            hour = int(parts[0])
            minute = int(parts[1])
            
            return time(hour=hour, minute=minute)
        except (ValueError, TypeError):
            logger.error(f"Invalid time format: {time_str}")
            return None
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current operating hours settings"""
        return {**self.settings}
    
    def is_enabled(self) -> bool:
        """Check if operating hours are enabled"""
        return self.settings.get("enabled", False)
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_monitoring()
        logger.debug("Operating hours service cleaned up")

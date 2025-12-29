"""
Session Management Service
Handles PC usage sessions with real-time tracking and sync
"""

import time
from datetime import datetime
from typing import Dict, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from services.computer_service import ComputerService
from services.firebase_client import FirebaseClient
from services.print_monitor_service import PrintMonitorService
from utils.logger import get_logger


logger = get_logger(__name__)


class SessionService(QObject):
    """Manages user sessions with Firebase sync"""

    # Signals
    time_updated = pyqtSignal(int)  # Emits remaining seconds
    session_ended = pyqtSignal(str)  # Emits reason: 'expired', 'user', 'error'
    warning_5min = pyqtSignal()
    warning_1min = pyqtSignal()
    sync_failed = pyqtSignal(str)  # Emits error message
    sync_restored = pyqtSignal()

    def __init__(self, firebase_client: FirebaseClient, user_id: str, org_id: str):
        super().__init__()
        self.firebase = firebase_client
        self.computer_service = ComputerService(firebase_client)
        self.user_id = user_id
        self.org_id = org_id

        # Print monitoring
        self.print_monitor = PrintMonitorService(firebase_client, user_id, org_id)

        # Session state
        self.session_id: Optional[str] = None
        self.is_active = False
        self.remaining_time = 0  # seconds
        self.time_used = 0  # seconds
        self.start_time: Optional[datetime] = None

        # Sync state
        self.last_sync_time = 0
        self.sync_queue = []  # Queue updates when offline
        self.is_online = True
        self.consecutive_sync_failures = 0

        # Timers
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._on_countdown_tick)

        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._sync_to_firebase)

        # Warning flags
        self.warned_5min = False
        self.warned_1min = False

        logger.info(f"Session service initialized for user: {user_id}")

    def start_session(self, initial_remaining_time: int) -> Dict:
        """
        Start a new session

        Args:
            initial_remaining_time: User's remaining time in seconds

        Returns:
            {'success': bool, 'session_id': str, 'error': str}
        """
        logger.debug("Starting new session", action="session_start")

        if self.is_active:
            logger.warning("Session already active")
            return {"success": False, "error": "Session already active"}

        if initial_remaining_time <= 0:
            logger.error("Cannot start session with 0 time")
            return {"success": False, "error": "No time remaining"}

        # OPTIMIZATION: No separate session table!
        # Store everything on user record to save 50% more writes
        now = datetime.now().isoformat()

        # Get current computer info for session tracking
        computer_info = self.computer_service.get_computer_info(
            self._get_current_computer_id()
        )
        computer_name = "Unknown PC"
        if computer_info.get("success") and computer_info.get("data"):
            computer_name = computer_info["data"].get("computerName", "Unknown PC")

        result = self.firebase.db_update(
            f"users/{self.user_id}",
            {
                "isSessionActive": True,
                "sessionStartTime": now,
                "lastActivity": now,
                "sessionComputerName": computer_name,
                "updatedAt": now,
            },
        )

        if not result.get("success"):
            logger.error("Failed to start session")
            return {"success": False, "error": "Failed to start session"}

        # Generate local session ID for tracking
        import uuid

        self.session_id = str(uuid.uuid4())
        logger.debug(
            "Session started", session_id=self.session_id, action="session_start"
        )

        # Initialize local state
        self.remaining_time = initial_remaining_time
        self.time_used = 0
        self.start_time = datetime.now()
        self.is_active = True
        self.warned_5min = False
        self.warned_1min = False

        # Start timers
        self.countdown_timer.start(1000)  # Every second (local countdown, free)
        self.sync_timer.start(60000)  # Every 60 seconds (83% cost reduction!)

        # Start print monitoring
        self.print_monitor.start_monitoring()

        logger.info(
            "Session started successfully",
            remaining_time=initial_remaining_time,
            action="session_start",
        )
        return {"success": True, "session_id": self.session_id}

    def end_session(self, reason: str = "user") -> Dict:
        """
        End the current session

        Args:
            reason: 'user', 'expired', 'error'
        """
        if not self.is_active:
            return {"success": False, "error": "No active session"}

        logger.info(
            "Ending session",
            session_id=self.session_id,
            reason=reason,
            action="session_end",
        )

        # Stop timers
        self.countdown_timer.stop()
        self.sync_timer.stop()

        # Stop print monitoring
        self.print_monitor.stop_monitoring()

        # Disassociate user from computer if logging out
        if reason in ["user", "expired", "admin_kick"]:
            computer_id = self._get_current_computer_id()
            if computer_id != "unknown":
                self.computer_service.disassociate_user_from_computer(
                    self.user_id, computer_id
                )

        # Final sync
        self._final_sync(reason)

        # Update state
        self.is_active = False

        # Emit signal
        self.session_ended.emit(reason)

        logger.info("Session ended", time_used=self.time_used, action="session_end")
        return {
            "success": True,
            "time_used": self.time_used,
            "remaining_time": self.remaining_time,
        }

    def _on_countdown_tick(self):
        """Called every second to update countdown"""
        if not self.is_active:
            return

        # Decrement time
        self.remaining_time -= 1
        self.time_used += 1

        # Emit update
        self.time_updated.emit(self.remaining_time)

        # Check warnings
        if self.remaining_time == 300 and not self.warned_5min:
            logger.warning("5 minutes remaining")
            self.warned_5min = True
            self.warning_5min.emit()

        if self.remaining_time == 60 and not self.warned_1min:
            logger.warning("1 minute remaining")
            self.warned_1min = True
            self.warning_1min.emit()

        # Check expiration
        if self.remaining_time <= 0:
            logger.warning("Time expired")
            self.end_session("expired")

    def _sync_to_firebase(self):
        """Sync session state to Firebase every 60 seconds"""
        if not self.is_active:
            return

        logger.debug("Syncing user state", action="session_sync")

        # OPTIMIZATION: Only update user record!
        # No separate session table = 50% fewer writes
        now = datetime.now().isoformat()

        user_result = self.firebase.db_update(
            f"users/{self.user_id}",
            {
                "remainingTime": self.remaining_time,
                "lastActivity": now,
                "updatedAt": now,
            },
        )

        if user_result.get("success"):
            logger.debug("Sync successful", action="session_sync")

            # Reset failure counter
            if self.consecutive_sync_failures > 0:
                self.consecutive_sync_failures = 0
                self.is_online = True
                self.sync_restored.emit()
                logger.info("Connection restored")
        else:
            # Handle sync failure
            self.consecutive_sync_failures += 1
            logger.error(
                "Sync failed",
                failures=self.consecutive_sync_failures,
                action="session_sync",
            )

            if self.consecutive_sync_failures >= 3:
                self.is_online = False
                self.sync_failed.emit("Connection lost")

            # Queue update for retry (simplified)
            self.sync_queue.append(
                {"timestamp": time.time(), "remainingTime": self.remaining_time}
            )

    def _final_sync(self, reason: str):
        """Final sync when ending session"""
        logger.debug("Final session sync", action="session_end")

        # OPTIMIZATION: Only update user record, no separate session
        now = datetime.now().isoformat()

        self.firebase.db_update(
            f"users/{self.user_id}",
            {
                "remainingTime": max(0, self.remaining_time),
                "isSessionActive": False,
                "sessionStartTime": None,
                "lastActivity": now,
                "updatedAt": now,
            },
        )

        logger.debug(
            "Session final sync completed",
            reason=reason,
            time_used=self.time_used,
            action="session_end",
        )

    def _get_current_computer_id(self) -> str:
        """Get the current computer ID from user data"""
        try:
            user_result = self.firebase.db_get(f"users/{self.user_id}")
            if user_result.get("success") and user_result.get("data"):
                return user_result["data"].get("currentComputerId", "unknown")
            return "unknown"
        except Exception as e:
            logger.warning(f"Failed to get current computer ID: {e}")
            return "unknown"

    def get_remaining_time(self) -> int:
        """Get current remaining time in seconds"""
        return self.remaining_time

    def get_time_used(self) -> int:
        """Get time used in current session"""
        return self.time_used

    def is_session_active(self) -> bool:
        """Check if session is active"""
        return self.is_active

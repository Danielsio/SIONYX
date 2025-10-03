"""
Session Management Service
Handles PC usage sessions with real-time tracking and sync
"""

from typing import Dict, Optional
from datetime import datetime
import time
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

from services.firebase_client import FirebaseClient
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

    def __init__(self, firebase_client: FirebaseClient, user_id: str):
        super().__init__()
        self.firebase = firebase_client
        self.user_id = user_id

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
        logger.info("Starting new session")

        if self.is_active:
            logger.warning("Session already active")
            return {
                'success': False,
                'error': 'Session already active'
            }

        if initial_remaining_time <= 0:
            logger.error("Cannot start session with 0 time")
            return {
                'success': False,
                'error': 'No time remaining'
            }

        # Create session in Firebase
        session_data = {
            'userId': self.user_id,
            'startTime': datetime.now().isoformat(),
            'lastHeartbeat': datetime.now().isoformat(),
            'isActive': True,
            'timeUsed': 0,
            'status': 'active'
        }

        # Generate session ID using Firebase push
        import requests
        response = requests.post(
            f"{self.firebase.database_url}/sessions.json",
            params={'auth': self.firebase.id_token},
            json=session_data
        )

        if response.status_code != 200:
            logger.error(f"Failed to create session: {response.text}")
            return {
                'success': False,
                'error': 'Failed to create session in database'
            }

        self.session_id = response.json()['name']
        logger.info(f"Session created: {self.session_id}")

        # Update user's active session
        self.firebase.db_update(f'users/{self.user_id}', {
            'activeSessionId': self.session_id
        })

        # Initialize local state
        self.remaining_time = initial_remaining_time
        self.time_used = 0
        self.start_time = datetime.now()
        self.is_active = True
        self.warned_5min = False
        self.warned_1min = False

        # Start timers
        self.countdown_timer.start(1000)  # Every second
        self.sync_timer.start(10000)  # Every 10 seconds

        logger.info(f"Session started with {initial_remaining_time}s")
        return {
            'success': True,
            'session_id': self.session_id
        }

    def end_session(self, reason: str = 'user') -> Dict:
        """
        End the current session

        Args:
            reason: 'user', 'expired', 'error'
        """
        if not self.is_active:
            return {'success': False, 'error': 'No active session'}

        logger.info(f"Ending session: {self.session_id} (reason: {reason})")

        # Stop timers
        self.countdown_timer.stop()
        self.sync_timer.stop()

        # Final sync
        self._final_sync(reason)

        # Update state
        self.is_active = False

        # Emit signal
        self.session_ended.emit(reason)

        logger.info(f"Session ended. Time used: {self.time_used}s")
        return {
            'success': True,
            'time_used': self.time_used,
            'remaining_time': self.remaining_time
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
            self.end_session('expired')

    def _sync_to_firebase(self):
        """Sync session state to Firebase every 10 seconds"""
        if not self.is_active:
            return

        logger.debug("Syncing session to Firebase")

        sync_data = {
            'lastHeartbeat': datetime.now().isoformat(),
            'timeUsed': self.time_used
        }

        # Update session
        session_result = self.firebase.db_update(
            f'sessions/{self.session_id}',
            sync_data
        )

        # Update user's remaining time
        user_result = self.firebase.db_update(
            f'users/{self.user_id}',
            {'remainingTime': self.remaining_time}
        )

        if session_result.get('success') and user_result.get('success'):
            logger.debug("Sync successful")

            # Reset failure counter
            if self.consecutive_sync_failures > 0:
                self.consecutive_sync_failures = 0
                self.is_online = True
                self.sync_restored.emit()
                logger.info("Connection restored")
        else:
            # Handle sync failure
            self.consecutive_sync_failures += 1
            logger.error(f"Sync failed ({self.consecutive_sync_failures} times)")

            if self.consecutive_sync_failures >= 3:
                self.is_online = False
                self.sync_failed.emit("Connection lost")

            # Queue update for retry
            self.sync_queue.append({
                'timestamp': time.time(),
                'data': sync_data
            })

    def _final_sync(self, reason: str):
        """Final sync when ending session"""
        logger.info("Final session sync")

        # Update session
        session_data = {
            'endTime': datetime.now().isoformat(),
            'isActive': False,
            'status': 'completed' if reason == 'user' else reason,
            'timeUsed': self.time_used,
            'lastHeartbeat': datetime.now().isoformat()
        }

        self.firebase.db_update(f'sessions/{self.session_id}', session_data)

        # Update user
        self.firebase.db_update(f'users/{self.user_id}', {
            'remainingTime': max(0, self.remaining_time),
            'activeSessionId': None
        })

    def get_remaining_time(self) -> int:
        """Get current remaining time in seconds"""
        return self.remaining_time

    def get_time_used(self) -> int:
        """Get time used in current session"""
        return self.time_used

    def is_session_active(self) -> bool:
        """Check if session is active"""
        return self.is_active
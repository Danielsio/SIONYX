import time
import uuid
from typing import Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from services.firebase_client import FirebaseClient
from utils.device_info import get_device_id
from database.local_db import LocalDatabase


class SessionManager(QObject):
    time_updated = pyqtSignal(int)  # Emit remaining seconds
    time_expired = pyqtSignal()
    sync_failed = pyqtSignal(str)  # Error message

    def __init__(self, firebase_client: FirebaseClient, user_id: str):
        super().__init__()
        self.firebase = firebase_client
        self.user_id = user_id
        self.session_id = None
        self.local_db = LocalDatabase()

        self.start_time = None
        self.last_sync_time = None
        self.is_active = False

        # Timer for 10-second sync
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.sync_session_time)
        self.sync_timer.setInterval(10000)  # 10 seconds

    def start_session(self) -> bool:
        """Initialize a new session"""
        try:
            self.session_id = str(uuid.uuid4())
            self.start_time = time.time()
            self.last_sync_time = self.start_time

            # Call Cloud Function to start session
            result = self.firebase.call_function('startSession', {
                'sessionId': self.session_id,
                'deviceId': get_device_id(),
                'timestamp': int(self.start_time * 1000)
            })

            if not result.get('success'):
                raise Exception(result.get('message', 'Failed to start session'))

            # Cache session locally
            self.local_db.create_session(
                session_id=self.session_id,
                user_id=self.user_id,
                start_time=self.start_time
            )

            self.is_active = True
            self.sync_timer.start()

            return True

        except Exception as e:
            self.sync_failed.emit(str(e))
            return False

    def sync_session_time(self):
        """Sync elapsed time with server (called every 10 seconds)"""
        if not self.is_active:
            return

        try:
            current_time = time.time()
            elapsed_seconds = int(current_time - self.last_sync_time)

            # Call Cloud Function
            result = self.firebase.call_function('syncSessionTime', {
                'sessionId': self.session_id,
                'elapsedTime': elapsed_seconds,
                'timestamp': int(current_time * 1000)
            })

            if result.get('success'):
                remaining_time = result['remainingTime']
                self.time_updated.emit(remaining_time)

                # Update local cache
                self.local_db.update_session_sync(
                    session_id=self.session_id,
                    elapsed_time=elapsed_seconds
                )

                self.last_sync_time = current_time

                # Check if time expired
                if result.get('shouldLogout'):
                    self.handle_time_expired()
            else:
                raise Exception(result.get('message', 'Sync failed'))

        except Exception as e:
            # Queue for offline sync
            self.local_db.queue_sync_request(
                session_id=self.session_id,
                elapsed_time=elapsed_seconds,
                timestamp=current_time
            )
            self.sync_failed.emit(str(e))

    def handle_time_expired(self):
        """Handle when user's time runs out"""
        self.stop_session()
        self.time_expired.emit()

    def stop_session(self):
        """Stop the current session"""
        if not self.is_active:
            return

        self.sync_timer.stop()
        self.is_active = False

        # Final sync
        try:
            current_time = time.time()
            elapsed_seconds = int(current_time - self.last_sync_time)

            self.firebase.call_function('syncSessionTime', {
                'sessionId': self.session_id,
                'elapsedTime': elapsed_seconds,
                'timestamp': int(current_time * 1000)
            })
        except:
            pass  # Best effort

        # Mark session as ended locally
        self.local_db.end_session(self.session_id)

    def get_remaining_time(self) -> int:
        """Get remaining time from local cache"""
        return self.local_db.get_cached_remaining_time(self.user_id)
import time
import uuid

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from services.firebase_client import FirebaseClient
from utils.device_info import get_device_id


class SessionManager(QObject):
    time_updated = pyqtSignal(int)  # Emit remaining seconds
    time_expired = pyqtSignal()
    sync_failed = pyqtSignal(str)  # Error message

    def __init__(self, firebase_client: FirebaseClient, user_id: str):
        super().__init__()
        self.firebase = firebase_client
        self.user_id = user_id
        self.session_id = None

        self.start_time = None
        self.last_sync_time = None
        self.is_active = False
        self.cached_remaining_time = 0

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

            # Create session in Realtime Database
            session_data = {
                "userId": self.user_id,
                "deviceId": get_device_id(),
                "startTime": int(self.start_time * 1000),
                "lastSync": int(self.start_time * 1000),
                "isActive": True,
            }

            result = self.firebase.set_data(f"sessions/{self.session_id}", session_data)

            if not result.get("success"):
                raise Exception("Failed to start session")

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

            # Update session in Realtime Database
            sync_data = {
                "lastSync": int(current_time * 1000),
                "elapsedTime": elapsed_seconds,
            }

            result = self.firebase.update_data(f"sessions/{self.session_id}", sync_data)

            if result.get("success"):
                # Get updated user data to check remaining time
                user_result = self.firebase.get_data(f"users/{self.user_id}")

                if user_result.get("success"):
                    user_data = user_result["data"]
                    remaining_time = user_data.get("remainingTime", 0)

                    # Deduct elapsed time from user's remaining time
                    new_remaining_time = max(0, remaining_time - elapsed_seconds)

                    # Update user's remaining time
                    self.firebase.update_data(
                        f"users/{self.user_id}",
                        {
                            "remainingTime": new_remaining_time,
                            "updatedAt": int(current_time * 1000),
                        },
                    )

                    self.cached_remaining_time = new_remaining_time
                    self.time_updated.emit(new_remaining_time)
                    self.last_sync_time = current_time

                    # Check if time expired
                    if new_remaining_time <= 0:
                        self.handle_time_expired()
                else:
                    raise Exception("Failed to fetch user data during sync")
            else:
                raise Exception("Sync failed")

        except Exception as e:
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

        # Final sync and mark session as ended
        try:
            current_time = time.time()
            elapsed_seconds = int(current_time - self.last_sync_time)

            # Update session to inactive
            self.firebase.update_data(
                f"sessions/{self.session_id}",
                {
                    "isActive": False,
                    "endTime": int(current_time * 1000),
                    "elapsedTime": elapsed_seconds,
                },
            )

            # Update user's remaining time one last time
            user_result = self.firebase.get_data(f"users/{self.user_id}")
            if user_result.get("success"):
                remaining_time = user_result["data"].get("remainingTime", 0)
                new_remaining_time = max(0, remaining_time - elapsed_seconds)

                self.firebase.update_data(
                    f"users/{self.user_id}",
                    {
                        "remainingTime": new_remaining_time,
                        "updatedAt": int(current_time * 1000),
                    },
                )

                self.cached_remaining_time = new_remaining_time
        except Exception:
            pass  # Best effort

    def get_remaining_time(self) -> int:
        """Get remaining time from cache or server"""
        try:
            # Try to get fresh data from server
            result = self.firebase.get_data(f"users/{self.user_id}")
            if result.get("success"):
                self.cached_remaining_time = result["data"].get("remainingTime", 0)
                return self.cached_remaining_time
        except Exception:
            pass

        # Return cached value
        return self.cached_remaining_time

"""
Force Logout Listener
Listens for forceLogout changes in Firebase and emits signals when user is kicked
"""

import json

import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.logger import get_logger


logger = get_logger(__name__)


class ForceLogoutListener(QThread):
    """Thread to listen for forceLogout changes via Firebase SSE streaming"""

    force_logout_detected = pyqtSignal()  # Emits when forceLogout becomes true

    def __init__(self, firebase_client, user_id: str):
        super().__init__()
        self.firebase = firebase_client
        self.user_id = user_id
        self.running = True
        self._response = None  # Store response to allow closing from stop()

    def run(self):
        """Listen for changes to forceLogout field using Firebase REST SSE streaming"""
        logger.info(f"Starting force logout listener for user: {self.user_id}")

        while self.running:
            try:
                self._connect_and_stream()
            except requests.exceptions.ConnectionError as e:
                if self.running:
                    logger.warning(
                        f"Force logout stream connection error, retrying: {e}"
                    )
                    self._sleep_if_running(5)
            except Exception as e:
                if self.running:
                    logger.error(f"Force logout stream error: {e}")
                    self._sleep_if_running(5)

        logger.info("Force logout listener stopped")

    def _sleep_if_running(self, seconds: int):
        """Sleep in small intervals to allow stopping"""
        for _ in range(seconds * 10):
            if not self.running:
                break
            self.msleep(100)

    def _connect_and_stream(self):
        """Connect to Firebase SSE stream and process events"""
        # Firebase streaming endpoint for user's forceLogout field
        user_path = (
            f"organizations/{self.firebase.org_id}/users/{self.user_id}/forceLogout"
        )
        stream_url = f"{self.firebase.database_url}/{user_path}.json"
        params = {"auth": self.firebase.id_token}

        # CRITICAL: Must use Accept: text/event-stream for SSE
        headers = {"Accept": "text/event-stream"}

        # Open SSE streaming connection (no timeout for long-lived connection)
        self._response = requests.get(
            stream_url,
            params=params,
            headers=headers,
            stream=True,
            timeout=None,  # No timeout - Firebase sends keep-alive
        )

        if self._response.status_code != 200:
            logger.error(
                f"Firebase stream failed with status: {self._response.status_code}"
            )
            return

        logger.debug("Force logout SSE stream connected")

        # Parse SSE events
        event_type = None
        data_lines = []

        for line in self._response.iter_lines(decode_unicode=True):
            if not self.running:
                break

            if line is None:
                continue

            line = line.strip()

            if not line:
                # Empty line = end of event, process it
                if event_type and data_lines:
                    data_str = "\n".join(data_lines)
                    self._process_event(event_type, data_str)
                event_type = None
                data_lines = []
                continue

            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())

    def _process_event(self, event_type: str, data_str: str):
        """Process a single SSE event"""
        try:
            if event_type == "keep-alive":
                logger.debug("Force logout SSE keep-alive received")
                return

            if event_type in ("put", "patch"):
                # Parse the SSE data - format: {"path": "/", "data": <value>}
                if data_str and data_str != "null":
                    try:
                        event_data = json.loads(data_str)
                        force_logout_value = event_data.get("data")

                        logger.debug(f"Force logout value: {force_logout_value}")

                        # Check if forceLogout is true
                        if force_logout_value is True:
                            logger.warning("Force logout detected!")
                            self.force_logout_detected.emit()
                            self.running = False
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse force logout data: {e}")

        except Exception as e:
            logger.error(f"Error processing force logout event: {e}")

    def stop(self):
        """Stop the listener"""
        self.running = False

        # Close the response to unblock iter_lines
        if self._response:
            try:
                self._response.close()
            except Exception:
                pass

        logger.info("Force logout listener stop requested")

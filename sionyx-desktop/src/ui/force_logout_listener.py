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
    """Thread to listen for forceLogout changes via Firebase streaming"""

    force_logout_detected = pyqtSignal()  # Emits when forceLogout becomes true

    def __init__(self, firebase_client, user_id: str):
        super().__init__()
        self.firebase = firebase_client
        self.user_id = user_id
        self.running = True

    def run(self):
        """Listen for changes to forceLogout field using Firebase REST streaming"""
        logger.info(f"Starting force logout listener for user: {self.user_id}")

        try:
            # Firebase streaming endpoint for user's forceLogout field
            user_path = (
                f"organizations/{self.firebase.org_id}/users/{self.user_id}/forceLogout"
            )
            stream_url = f"{self.firebase.database_url}/{user_path}.json"
            params = {"auth": self.firebase.id_token}

            # Open streaming connection
            response = requests.get(stream_url, params=params, stream=True, timeout=300)

            if response.status_code != 200:
                logger.error(
                    f"Firebase stream failed with status: {response.status_code}"
                )
                return

            # Firebase streaming sends data in chunks
            buffer = ""
            for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                if not self.running:
                    break

                if chunk:
                    buffer += chunk

                    # Look for complete JSON objects (Firebase sends them line by line)
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()

                        if line and line != "null":
                            try:
                                force_logout_value = json.loads(line)
                                logger.debug(
                                    f"Force logout value: {force_logout_value}"
                                )

                                # Check if forceLogout is true
                                if force_logout_value:
                                    logger.warning("Force logout detected!")
                                    self.force_logout_detected.emit()
                                    self.running = False
                                    return

                            except json.JSONDecodeError as e:
                                logger.warning(
                                    f"Failed to parse Firebase stream data: {line}, error: {e}"
                                )

        except requests.exceptions.Timeout:
            logger.warning("Firebase stream timed out (5 minutes)")
        except Exception as e:
            logger.error(f"Firebase stream error: {e}")

        logger.info("Force logout listener stopped")

    def stop(self):
        """Stop the listener"""
        self.running = False
        logger.info("Force logout listener stop requested")

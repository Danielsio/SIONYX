"""
Local Token Storage
Only stores encrypted refresh token for auto-login
All other data is in Firebase Realtime Database
"""

import base64
import hashlib
import sqlite3
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

from utils.logger import get_logger


logger = get_logger(__name__)


class LocalDatabase:
    """Minimal local storage for refresh token only"""

    def __init__(self):
        # Store in user's app data folder
        app_data = Path.home() / ".sionyx"
        app_data.mkdir(exist_ok=True)

        self.db_path = app_data / "auth.db"
        self.key = self._get_encryption_key()
        self.cipher = Fernet(self.key)

        self._init_db()

    def _init_db(self):
        """Create database if doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
                       CREATE TABLE IF NOT EXISTS auth
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           CHECK
                       (
                           id =
                           1
                       ),
                           encrypted_token TEXT
                           )
                       """
        )

        conn.commit()
        conn.close()

    def _get_encryption_key(self) -> bytes:
        """Generate encryption key from machine-specific data"""
        # Use a consistent key based on machine
        # In production, use hardware ID or similar
        machine_id = "sionyx-desktop-app"  # Simple for now

        # Derive key
        key_material = hashlib.sha256(machine_id.encode()).digest()
        key = base64.urlsafe_b64encode(key_material)

        return key

    def store_credentials(
        self, uid: str, phone: str, refresh_token: str, user_data: dict
    ):
        """Store only the refresh token (encrypted)"""
        encrypted = self.cipher.encrypt(refresh_token.encode())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO auth (id, encrypted_token)
            VALUES (1, ?)
        """,
            (encrypted.decode(),),
        )

        conn.commit()
        conn.close()

        logger.info("Refresh token stored")

    def get_stored_token(self) -> Optional[str]:
        """Get stored refresh token (decrypted)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT encrypted_token FROM auth WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            return None

        try:
            decrypted = self.cipher.decrypt(row[0].encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}")
            return None

    def clear_tokens(self):
        """Clear stored token (logout)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM auth")

        conn.commit()
        conn.close()

        logger.info("Tokens cleared")

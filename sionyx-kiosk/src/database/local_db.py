"""
Local Token Storage
Only stores encrypted refresh token for auto-login
All other data is in Firebase Realtime Database

Singleton Pattern:
    LocalDatabase uses the Singleton pattern to ensure only one instance exists.
    This prevents multiple SQLite connections to the same file and ensures
    consistent encryption state.

    Usage:
        db1 = LocalDatabase()
        db2 = LocalDatabase()
        assert db1 is db2  # Same instance

    For testing:
        LocalDatabase.reset_instance()  # Creates fresh instance for next test
"""

import base64
import hashlib
import sqlite3
import threading
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

from utils.logger import get_logger


logger = get_logger(__name__)


class LocalDatabase:
    """
    Minimal local storage for refresh token only.

    Singleton Pattern: Only one instance exists throughout the application.
    Use LocalDatabase() or LocalDatabase.get_instance() to get it.
    """

    _instance: Optional["LocalDatabase"] = None
    _lock = threading.Lock()
    _initialized = False  # Flag to ensure __init__ runs only once

    def __new__(cls, *args, **kwargs):
        """
        Singleton implementation using __new__.
        Returns the same instance for all calls to LocalDatabase().
        Thread-safe using a lock.
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the LocalDatabase.

        NOTE: __init__ is called every time LocalDatabase() is used,
        but we only want to initialize once. The _initialized flag
        ensures setup code runs only on first instantiation.
        """
        if self._initialized:
            return

        # Store in user's app data folder
        app_data = Path.home() / ".sionyx"
        app_data.mkdir(exist_ok=True)

        self.db_path = app_data / "auth.db"
        self.key = self._get_encryption_key()
        self.cipher = Fernet(self.key)

        self._init_db()

        logger.info("LocalDatabase initialized (singleton)", component="local_db")
        LocalDatabase._initialized = True

    @classmethod
    def get_instance(cls) -> "LocalDatabase":
        """
        Returns the singleton instance of LocalDatabase.

        This is more explicit than LocalDatabase() and makes
        the singleton pattern more visible in code.
        """
        if cls._instance is None:
            cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """
        Resets the singleton instance for testing purposes.

        This allows tests to start with a fresh LocalDatabase instance.
        Should NOT be used in production code.
        """
        with cls._lock:
            cls._instance = None
            cls._initialized = False
            logger.debug("LocalDatabase singleton instance reset.")

    def _init_db(self):
        """Create database if doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        try:
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
        finally:
            conn.close()

    def _get_encryption_key(self) -> bytes:
        """Generate encryption key from machine-specific hardware data"""
        from utils.device_info import get_device_id

        # Use hardware-derived device ID (MAC address or machine hash)
        # Salted with app name to prevent reuse across applications
        machine_id = f"sionyx-kiosk-{get_device_id()}"

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
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO auth (id, encrypted_token)
                VALUES (1, ?)
            """,
                (encrypted.decode(),),
            )

            conn.commit()
        finally:
            conn.close()

        logger.info("Refresh token stored")

    def get_stored_token(self) -> Optional[str]:
        """Get stored refresh token (decrypted)"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT encrypted_token FROM auth WHERE id = 1")
            row = cursor.fetchone()
        finally:
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
        try:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM auth")

            conn.commit()
        finally:
            conn.close()

        logger.info("Tokens cleared")

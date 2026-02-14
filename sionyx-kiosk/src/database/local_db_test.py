"""
Tests for LocalDatabase
"""

import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from database.local_db import LocalDatabase


class TestSingletonPattern:
    """Test cases for LocalDatabase Singleton pattern"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before and after each test"""
        LocalDatabase.reset_instance()
        yield
        LocalDatabase.reset_instance()

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary directory for database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_same_instance_returned(self, temp_db_path):
        """Multiple calls to LocalDatabase() return the SAME instance"""
        with patch.object(Path, "home", return_value=temp_db_path):
            db1 = LocalDatabase()
            db2 = LocalDatabase()

            assert db1 is db2
            assert id(db1) == id(db2)

    def test_get_instance_returns_same_object(self, temp_db_path):
        """get_instance() returns the same object as LocalDatabase()"""
        with patch.object(Path, "home", return_value=temp_db_path):
            db1 = LocalDatabase()
            db2 = LocalDatabase.get_instance()

            assert db1 is db2

    def test_get_instance_creates_if_needed(self, temp_db_path):
        """get_instance() creates instance if none exists"""
        with patch.object(Path, "home", return_value=temp_db_path):
            db = LocalDatabase.get_instance()

            assert db is not None
            assert isinstance(db, LocalDatabase)

    def test_reset_instance_allows_new_creation(self, temp_db_path):
        """reset_instance() allows a new instance to be created"""
        with patch.object(Path, "home", return_value=temp_db_path):
            db1 = LocalDatabase()
            first_id = id(db1)

            LocalDatabase.reset_instance()

            db2 = LocalDatabase()
            second_id = id(db2)

            assert first_id != second_id

    def test_init_runs_only_once(self, temp_db_path):
        """__init__ should only run once, not on every LocalDatabase() call"""
        init_count = 0
        original_init_db = LocalDatabase._init_db

        def counting_init_db(self):
            nonlocal init_count
            init_count += 1
            return original_init_db(self)

        with patch.object(Path, "home", return_value=temp_db_path):
            with patch.object(LocalDatabase, "_init_db", counting_init_db):
                LocalDatabase()
                LocalDatabase()
                LocalDatabase()

                # _init_db should only be called once
                assert init_count == 1

    def test_thread_safety(self, temp_db_path):
        """Singleton should be thread-safe"""
        instances = []
        errors = []

        def create_instance():
            try:
                with patch.object(Path, "home", return_value=temp_db_path):
                    instance = LocalDatabase()
                    instances.append(instance)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # All instances should be the same object
        assert len(set(id(i) for i in instances)) == 1


class TestLocalDatabase:
    """Test cases for LocalDatabase"""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary directory for database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def local_db(self, temp_db_path):
        """Create LocalDatabase instance with temp path"""
        with patch.object(Path, "home", return_value=temp_db_path):
            db = LocalDatabase()
            yield db

    def test_initialization(self, local_db, temp_db_path):
        """Test LocalDatabase initialization creates db file"""
        expected_path = temp_db_path / ".sionyx" / "auth.db"
        assert local_db.db_path == expected_path
        assert local_db.key is not None
        assert local_db.cipher is not None

    def test_encryption_key_generation(self, local_db):
        """Test encryption key is generated consistently"""
        key1 = local_db._get_encryption_key()
        key2 = local_db._get_encryption_key()
        assert key1 == key2
        assert len(key1) == 44  # Base64-encoded 32-byte key

    def test_store_and_retrieve_credentials(self, local_db):
        """Test storing and retrieving refresh token"""
        refresh_token = "test-refresh-token-12345"

        local_db.store_credentials(
            uid="test-user-id",
            phone="1234567890",
            refresh_token=refresh_token,
            user_data={"name": "Test User"},
        )

        retrieved_token = local_db.get_stored_token()
        assert retrieved_token == refresh_token

    def test_get_stored_token_when_empty(self, local_db):
        """Test getting token when database is empty"""
        result = local_db.get_stored_token()
        assert result is None

    def test_clear_tokens(self, local_db):
        """Test clearing stored tokens"""
        # First store a token
        local_db.store_credentials(
            uid="test-user-id",
            phone="1234567890",
            refresh_token="test-token",
            user_data={},
        )

        # Verify it's stored
        assert local_db.get_stored_token() == "test-token"

        # Clear tokens
        local_db.clear_tokens()

        # Verify it's cleared
        assert local_db.get_stored_token() is None

    def test_store_credentials_overwrites_existing(self, local_db):
        """Test that storing new credentials overwrites existing ones"""
        local_db.store_credentials("uid1", "phone1", "token1", {})
        local_db.store_credentials("uid2", "phone2", "token2", {})

        assert local_db.get_stored_token() == "token2"

    def test_encryption_decryption(self, local_db):
        """Test that tokens are properly encrypted and decrypted"""
        original_token = "very-secret-refresh-token"

        # Store the token
        local_db.store_credentials("uid", "phone", original_token, {})

        # Retrieve and verify
        retrieved = local_db.get_stored_token()
        assert retrieved == original_token

    def test_get_stored_token_with_invalid_encrypted_data(self, local_db):
        """Test handling of corrupted encrypted data"""
        import sqlite3

        # Manually insert invalid encrypted data
        conn = sqlite3.connect(local_db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO auth (id, encrypted_token) VALUES (1, ?)",
            ("invalid-not-encrypted-data",),
        )
        conn.commit()
        conn.close()

        # Should return None when decryption fails
        result = local_db.get_stored_token()
        assert result is None

    def test_database_persistence(self, temp_db_path):
        """Test that database persists across instances"""
        refresh_token = "persistent-token"

        with patch.object(Path, "home", return_value=temp_db_path):
            # Create first instance and store token
            db1 = LocalDatabase()
            db1.store_credentials("uid", "phone", refresh_token, {})

            # Create second instance and retrieve token
            db2 = LocalDatabase()
            retrieved = db2.get_stored_token()

            assert retrieved == refresh_token

    def test_store_credentials_closes_connection_on_exception(self, local_db):
        """Test that store_credentials closes DB connection on error (BUG-009)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("disk I/O error")
        mock_conn.cursor.return_value = mock_cursor

        with patch("database.local_db.sqlite3.connect", return_value=mock_conn):
            try:
                local_db.store_credentials("uid", "phone", "token", {})
            except Exception:
                pass

        mock_conn.close.assert_called()

    def test_init_db_creates_table(self, temp_db_path):
        """Test that _init_db creates the auth table"""
        import sqlite3

        with patch.object(Path, "home", return_value=temp_db_path):
            db = LocalDatabase()

            # Check table exists
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='auth'"
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            assert result[0] == "auth"

"""
Pytest configuration and shared fixtures
"""

from unittest.mock import Mock

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from database.local_db import LocalDatabase
from services.firebase_client import FirebaseClient
from utils.firebase_config import FirebaseConfig


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for PyQt6 tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_firebase_config():
    """Mock Firebase configuration"""
    config = Mock(spec=FirebaseConfig)
    config.api_key = "test-api-key"
    config.database_url = "https://test-project.firebaseio.com"
    config.auth_url = "https://identitytoolkit.googleapis.com/v1/accounts"
    config.org_id = "test-org"
    return config


@pytest.fixture(autouse=True)
def reset_singletons(qapp):
    """
    Reset all singleton instances before each test.

    This ensures each test starts with fresh instances.
    autouse=True means this runs automatically for every test.

    Singletons reset:
    - FirebaseClient
    - LocalDatabase

    Also processes pending Qt events to prevent timer leaks between tests.
    """
    # Process any pending Qt events from previous tests
    qapp.processEvents()

    # Reset singletons before test
    FirebaseClient.reset_instance()
    LocalDatabase.reset_instance()

    yield

    # Reset singletons after test (cleanup)
    FirebaseClient.reset_instance()
    LocalDatabase.reset_instance()

    # Process any pending Qt events to flush timers
    qapp.processEvents()


@pytest.fixture
def mock_firebase_client(mock_firebase_config):
    """Mock Firebase client with common methods"""
    client = Mock(spec=FirebaseClient)
    client.api_key = mock_firebase_config.api_key
    client.database_url = mock_firebase_config.database_url
    client.auth_url = mock_firebase_config.auth_url
    client.org_id = mock_firebase_config.org_id
    client.id_token = "test-id-token"
    client.refresh_token = "test-refresh-token"
    client.user_id = "test-user-id"

    client.sign_up.return_value = {"success": True, "uid": "test-user-id"}
    client.sign_in.return_value = {"success": True, "uid": "test-user-id"}
    client.db_get.return_value = {"success": True, "data": {}}
    client.db_set.return_value = {"success": True}
    client.db_update.return_value = {"success": True}
    client.db_delete.return_value = {"success": True}
    client.ensure_valid_token.return_value = True

    return client


@pytest.fixture
def mock_requests():
    """Mock requests library for HTTP calls - patches requests in firebase_client"""
    from unittest.mock import patch

    import requests as real_requests

    mock = Mock()
    mock.get.return_value.status_code = 200
    mock.post.return_value.status_code = 200
    mock.put.return_value.status_code = 200
    mock.patch.return_value.status_code = 200
    mock.delete.return_value.status_code = 200

    # Preserve the real exceptions module so except clauses work
    mock.exceptions = real_requests.exceptions

    # Actually patch requests in the firebase_client module
    with patch("services.firebase_client.requests", mock):
        yield mock


@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "uid": "test-user-123",
        "email": "test@sionyx.app",
        "org_id": "test-org",
        "remaining_time": 3600,
        "is_active": True,
    }


@pytest.fixture
def sample_session_data():
    """Sample session data for testing"""
    return {
        "session_id": "test-session-123",
        "user_id": "test-user-123",
        "org_id": "test-org",
        "start_time": "2024-01-01T10:00:00Z",
        "remaining_time": 3600,
        "is_active": True,
    }


@pytest.fixture
def sample_package_data():
    """Sample package data for testing"""
    return {
        "id": "test-package-123",
        "name": "Test Package",
        "price": 9.99,
        "duration": 3600,
        "description": "Test package description",
    }


@pytest.fixture
def qtbot(qapp):
    """QtBot instance for PyQt6 testing"""
    from pytestqt.qtbot import QtBot

    return QtBot(qapp)


@pytest.fixture
def timer():
    """QTimer for testing time-based functionality"""
    return QTimer()

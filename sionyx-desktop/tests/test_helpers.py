"""
Test helper utilities and fixtures
"""

from datetime import datetime
from unittest.mock import Mock

import pytest
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QApplication


class MockSignal:
    """Mock PyQt6 signal for testing"""

    def __init__(self):
        self.connected_functions = []

    def connect(self, func):
        """Connect a function to this signal"""
        self.connected_functions.append(func)

    def emit(self, *args):
        """Emit the signal with given arguments"""
        for func in self.connected_functions:
            func(*args)

    def disconnect(self, func=None):
        """Disconnect a function or all functions"""
        if func is None:
            self.connected_functions.clear()
        elif func in self.connected_functions:
            self.connected_functions.remove(func)


class MockQObject(QObject):
    """Mock QObject with signals for testing"""

    def __init__(self):
        super().__init__()
        self.signals = {}

    def add_signal(self, name, signal_type):
        """Add a signal to this mock object"""
        self.signals[name] = MockSignal()
        setattr(self, name, self.signals[name])

    def emit_signal(self, name, *args):
        """Emit a signal by name"""
        if name in self.signals:
            self.signals[name].emit(*args)


class FirebaseResponseBuilder:
    """Builder for creating Firebase API responses"""

    def __init__(self):
        self.response = {"success": True}

    def success(self, success=True):
        """Set success status"""
        self.response["success"] = success
        return self

    def data(self, data):
        """Set response data"""
        self.response["data"] = data
        return self

    def error(self, error):
        """Set error message"""
        self.response["error"] = error
        return self

    def uid(self, uid):
        """Set user ID"""
        self.response["uid"] = uid
        return self

    def id_token(self, token):
        """Set ID token"""
        self.response["id_token"] = token
        return self

    def refresh_token(self, token):
        """Set refresh token"""
        self.response["refresh_token"] = token
        return self

    def build(self):
        """Build the response"""
        return self.response.copy()


class UserDataBuilder:
    """Builder for creating user data objects"""

    def __init__(self):
        self.user_data = {
            "uid": "test-user-123",
            "firstName": "Test",
            "lastName": "User",
            "phoneNumber": "1234567890",
            "email": "test@example.com",
            "remainingTime": 3600,
            "remainingPrints": 100.0,
            "isActive": True,
            "isAdmin": False,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }

    def uid(self, uid):
        """Set user ID"""
        self.user_data["uid"] = uid
        return self

    def name(self, first_name, last_name):
        """Set user name"""
        self.user_data["firstName"] = first_name
        self.user_data["lastName"] = last_name
        return self

    def phone(self, phone):
        """Set phone number"""
        self.user_data["phoneNumber"] = phone
        return self

    def email(self, email):
        """Set email"""
        self.user_data["email"] = email
        return self

    def remaining_time(self, time):
        """Set remaining time in seconds"""
        self.user_data["remainingTime"] = time
        return self

    def remaining_prints(self, prints):
        """Set remaining print budget"""
        self.user_data["remainingPrints"] = prints
        return self

    def active(self, is_active):
        """Set active status"""
        self.user_data["isActive"] = is_active
        return self

    def admin(self, is_admin):
        """Set admin status"""
        self.user_data["isAdmin"] = is_admin
        return self

    def build(self):
        """Build the user data"""
        return self.user_data.copy()


class SessionDataBuilder:
    """Builder for creating session data objects"""

    def __init__(self):
        self.session_data = {
            "session_id": "test-session-123",
            "user_id": "test-user-123",
            "org_id": "test-org",
            "start_time": datetime.now().isoformat(),
            "remaining_time": 3600,
            "time_used": 0,
            "is_active": True,
            "computer_id": "test-computer-123",
            "computer_name": "Test PC",
        }

    def session_id(self, session_id):
        """Set session ID"""
        self.session_data["session_id"] = session_id
        return self

    def user_id(self, user_id):
        """Set user ID"""
        self.session_data["user_id"] = user_id
        return self

    def org_id(self, org_id):
        """Set organization ID"""
        self.session_data["org_id"] = org_id
        return self

    def remaining_time(self, time):
        """Set remaining time in seconds"""
        self.session_data["remaining_time"] = time
        return self

    def time_used(self, time):
        """Set time used in seconds"""
        self.session_data["time_used"] = time
        return self

    def active(self, is_active):
        """Set active status"""
        self.session_data["is_active"] = is_active
        return self

    def computer(self, computer_id, computer_name):
        """Set computer information"""
        self.session_data["computer_id"] = computer_id
        self.session_data["computer_name"] = computer_name
        return self

    def build(self):
        """Build the session data"""
        return self.session_data.copy()


class MockFirebaseClient:
    """Mock Firebase client for testing"""

    def __init__(self):
        self.api_key = "test-api-key"
        self.database_url = "https://test-project.firebaseio.com"
        self.auth_url = "https://identitytoolkit.googleapis.com/v1/accounts"
        self.org_id = "test-org"
        self.id_token = None
        self.refresh_token = None
        self.user_id = None
        self.token_expiry = None

        # Mock responses
        self.mock_responses = {}
        self.call_history = []

    def set_mock_response(self, method, response):
        """Set mock response for a method"""
        self.mock_responses[method] = response

    def get_call_history(self, method=None):
        """Get call history for a method or all methods"""
        if method:
            return [call for call in self.call_history if call[0] == method]
        return self.call_history

    def _record_call(self, method, *args, **kwargs):
        """Record a method call"""
        self.call_history.append((method, args, kwargs))

    def sign_up(self, email, password):
        """Mock sign up"""
        self._record_call("sign_up", email, password)
        return self.mock_responses.get(
            "sign_up", {"success": True, "uid": "test-user-id"}
        )

    def sign_in(self, email, password):
        """Mock sign in"""
        self._record_call("sign_in", email, password)
        return self.mock_responses.get(
            "sign_in", {"success": True, "uid": "test-user-id"}
        )

    def refresh_token_request(self, refresh_token):
        """Mock token refresh"""
        self._record_call("refresh_token_request", refresh_token)
        return self.mock_responses.get("refresh_token_request", {"success": True})

    def db_get(self, path):
        """Mock database get"""
        self._record_call("db_get", path)
        return self.mock_responses.get("db_get", {"success": True, "data": {}})

    def db_set(self, path, data):
        """Mock database set"""
        self._record_call("db_set", path, data)
        return self.mock_responses.get("db_set", {"success": True})

    def db_update(self, path, data):
        """Mock database update"""
        self._record_call("db_update", path, data)
        return self.mock_responses.get("db_update", {"success": True})

    def db_delete(self, path):
        """Mock database delete"""
        self._record_call("db_delete", path)
        return self.mock_responses.get("db_delete", {"success": True})

    def ensure_valid_token(self):
        """Mock token validation"""
        self._record_call("ensure_valid_token")
        return self.mock_responses.get("ensure_valid_token", True)


class MockLocalDatabase:
    """Mock local database for testing"""

    def __init__(self):
        self.stored_data = {}
        self.call_history = []

    def _record_call(self, method, *args, **kwargs):
        """Record a method call"""
        self.call_history.append((method, args, kwargs))

    def get_stored_token(self):
        """Mock get stored token"""
        self._record_call("get_stored_token")
        return self.stored_data.get("refresh_token")

    def store_credentials(self, uid, phone, refresh_token, user_data):
        """Mock store credentials"""
        self._record_call("store_credentials", uid, phone, refresh_token, user_data)
        self.stored_data.update(
            {
                "uid": uid,
                "phone": phone,
                "refresh_token": refresh_token,
                "user_data": user_data,
            }
        )

    def clear_tokens(self):
        """Mock clear tokens"""
        self._record_call("clear_tokens")
        self.stored_data.clear()


class MockComputerService:
    """Mock computer service for testing"""

    def __init__(self):
        self.call_history = []
        self.mock_responses = {}

    def _record_call(self, method, *args, **kwargs):
        """Record a method call"""
        self.call_history.append((method, args, kwargs))

    def set_mock_response(self, method, response):
        """Set mock response for a method"""
        self.mock_responses[method] = response

    def register_computer(self):
        """Mock register computer"""
        self._record_call("register_computer")
        return self.mock_responses.get(
            "register_computer", {"success": True, "computer_id": "test-computer-id"}
        )

    def get_computer_info(self, computer_id):
        """Mock get computer info"""
        self._record_call("get_computer_info", computer_id)
        return self.mock_responses.get(
            "get_computer_info", {"success": True, "data": {"computerName": "Test PC"}}
        )

    def associate_user_with_computer(self, user_id, computer_id):
        """Mock associate user with computer"""
        self._record_call("associate_user_with_computer", user_id, computer_id)
        return self.mock_responses.get(
            "associate_user_with_computer", {"success": True}
        )


# Pytest fixtures using the mock classes
@pytest.fixture
def mock_firebase_response_builder():
    """Fixture for Firebase response builder"""
    return FirebaseResponseBuilder()


@pytest.fixture
def mock_user_data_builder():
    """Fixture for user data builder"""
    return UserDataBuilder()


@pytest.fixture
def mock_session_data_builder():
    """Fixture for session data builder"""
    return SessionDataBuilder()


@pytest.fixture
def mock_firebase_client_advanced():
    """Fixture for advanced mock Firebase client"""
    return MockFirebaseClient()


@pytest.fixture
def mock_local_database_advanced():
    """Fixture for advanced mock local database"""
    return MockLocalDatabase()


@pytest.fixture
def mock_computer_service_advanced():
    """Fixture for advanced mock computer service"""
    return MockComputerService()


@pytest.fixture
def mock_qobject():
    """Fixture for mock QObject with signals"""
    return MockQObject()


# Utility functions for testing
def assert_signal_emitted(signal_mock, expected_args=None, expected_count=1):
    """Assert that a signal was emitted with expected arguments"""
    if expected_args is None:
        expected_args = ()

    assert signal_mock.emit.call_count == expected_count
    if expected_count > 0:
        signal_mock.emit.assert_called_with(*expected_args)


def create_mock_timer():
    """Create a mock QTimer for testing"""
    timer = Mock()
    timer.isActive.return_value = False
    timer.start = Mock()
    timer.stop = Mock()
    timer.timeout = MockSignal()
    return timer


def create_mock_qtbot(qapp):
    """Create a mock QtBot for testing"""
    from pytestqt.qtbot import QtBot

    return QtBot(qapp)


def wait_for_signal(signal, timeout=1000):
    """Wait for a signal to be emitted"""
    from pytestqt.qtbot import QtBot

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    qtbot = QtBot(app)
    qtbot.waitSignal(signal, timeout=timeout)


def create_test_user_data(**kwargs):
    """Create test user data with optional overrides"""
    default_data = {
        "uid": "test-user-123",
        "firstName": "Test",
        "lastName": "User",
        "phoneNumber": "1234567890",
        "email": "test@example.com",
        "remainingTime": 3600,
        "remainingPrints": 100.0,
        "isActive": True,
        "isAdmin": False,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
    }
    default_data.update(kwargs)
    return default_data


def create_test_session_data(**kwargs):
    """Create test session data with optional overrides"""
    default_data = {
        "session_id": "test-session-123",
        "user_id": "test-user-123",
        "org_id": "test-org",
        "start_time": datetime.now().isoformat(),
        "remaining_time": 3600,
        "time_used": 0,
        "is_active": True,
        "computer_id": "test-computer-123",
        "computer_name": "Test PC",
    }
    default_data.update(kwargs)
    return default_data

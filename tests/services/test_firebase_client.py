"""
Tests for FirebaseClient
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
import requests

from src.services.firebase_client import FirebaseClient


class TestFirebaseClient:
    """Test cases for FirebaseClient"""

    @pytest.fixture
    def firebase_client(self, mock_firebase_config):
        """Create FirebaseClient instance with mocked config"""
        with patch(
            "src.services.firebase_client.get_firebase_config",
            return_value=mock_firebase_config,
        ):
            return FirebaseClient()

    def test_initialization(self, firebase_client, mock_firebase_config):
        """Test FirebaseClient initialization"""
        assert firebase_client.api_key == mock_firebase_config.api_key
        assert firebase_client.database_url == mock_firebase_config.database_url
        assert firebase_client.auth_url == mock_firebase_config.auth_url
        assert firebase_client.org_id == mock_firebase_config.org_id
        assert firebase_client.id_token is None
        assert firebase_client.refresh_token is None
        assert firebase_client.token_expiry is None
        assert firebase_client.user_id is None

    def test_get_org_path(self, firebase_client):
        """Test organization path generation for multi-tenancy"""
        # Test basic path
        assert (
            firebase_client._get_org_path("users/123")
            == "organizations/test-org/users/123"
        )

        # Test path with leading/trailing slashes
        assert (
            firebase_client._get_org_path("/users/123/")
            == "organizations/test-org/users/123"
        )

        # Test root path
        assert firebase_client._get_org_path("") == "organizations/test-org"
        assert firebase_client._get_org_path("/") == "organizations/test-org"

    @pytest.mark.parametrize(
        "email,password,expected_success",
        [
            ("test@sionyx.app", "password123", True),
            ("invalid-email", "password123", False),
            ("test@sionyx.app", "", False),
        ],
    )
    def test_sign_up(
        self, firebase_client, email, password, expected_success, mock_requests
    ):
        """Test user sign up functionality"""
        if expected_success:
            mock_response = Mock()
            mock_response.json.return_value = {
                "idToken": "test-id-token",
                "refreshToken": "test-refresh-token",
                "localId": "test-user-id",
                "expiresIn": "3600",
            }
            mock_response.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_response
        else:
            mock_requests.post.side_effect = requests.exceptions.RequestException(
                "Invalid request"
            )

        result = firebase_client.sign_up(email, password)

        if expected_success:
            assert result["success"] is True
            assert result["uid"] == "test-user-id"
            assert firebase_client.id_token == "test-id-token"
            assert firebase_client.refresh_token == "test-refresh-token"
            assert firebase_client.user_id == "test-user-id"
        else:
            assert result["success"] is False
            assert "error" in result

    def test_sign_in(self, firebase_client, mock_requests):
        """Test user sign in functionality"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "idToken": "test-id-token",
            "refreshToken": "test-refresh-token",
            "localId": "test-user-id",
            "expiresIn": "3600",
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        result = firebase_client.sign_in("test@sionyx.app", "password123")

        assert result["success"] is True
        assert result["uid"] == "test-user-id"
        assert firebase_client.id_token == "test-id-token"

    def test_refresh_token_request(self, firebase_client, mock_requests):
        """Test token refresh functionality"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id_token": "new-id-token",
            "refresh_token": "new-refresh-token",
            "user_id": "test-user-id",
            "expires_in": "3600",
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        result = firebase_client.refresh_token_request("old-refresh-token")

        assert result["success"] is True
        assert firebase_client.id_token == "new-id-token"
        assert firebase_client.refresh_token == "new-refresh-token"
        assert firebase_client.user_id == "test-user-id"

    def test_ensure_valid_token_no_tokens(self, firebase_client):
        """Test ensure_valid_token when no tokens are present"""
        firebase_client.id_token = None
        firebase_client.refresh_token = None

        result = firebase_client.ensure_valid_token()
        assert result is False

    def test_ensure_valid_token_valid_token(self, firebase_client):
        """Test ensure_valid_token when token is still valid"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(hours=1)

        result = firebase_client.ensure_valid_token()
        assert result is True

    def test_ensure_valid_token_expiring_soon(self, firebase_client, mock_requests):
        """Test ensure_valid_token when token is expiring soon"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(
            minutes=3
        )  # Less than 5 minutes

        mock_response = Mock()
        mock_response.json.return_value = {
            "id_token": "new-token",
            "refresh_token": "new-refresh",
            "user_id": "test-user-id",
            "expires_in": "3600",
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        result = firebase_client.ensure_valid_token()
        assert result is True

    def test_db_get_success(self, firebase_client, mock_requests):
        """Test successful database get operation"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(hours=1)

        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response

        result = firebase_client.db_get("users/123")

        assert result["success"] is True
        assert result["data"] == {"test": "data"}
        mock_requests.get.assert_called_once()

    def test_db_get_not_authenticated(self, firebase_client):
        """Test database get when not authenticated"""
        firebase_client.id_token = None

        result = firebase_client.db_get("users/123")

        assert result["success"] is False
        assert result["error"] == "Not authenticated"

    def test_db_set_success(self, firebase_client, mock_requests):
        """Test successful database set operation"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(hours=1)

        mock_response = Mock()
        mock_response.json.return_value = {"name": "test-data"}
        mock_response.raise_for_status.return_value = None
        mock_requests.put.return_value = mock_response

        test_data = {"name": "test-data"}
        result = firebase_client.db_set("users/123", test_data)

        assert result["success"] is True
        assert result["data"] == {"name": "test-data"}
        mock_requests.put.assert_called_once()

    def test_db_update_success(self, firebase_client, mock_requests):
        """Test successful database update operation"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(hours=1)

        mock_response = Mock()
        mock_response.json.return_value = {"updated": True}
        mock_response.raise_for_status.return_value = None
        mock_requests.patch.return_value = mock_response

        test_data = {"name": "updated-data"}
        result = firebase_client.db_update("users/123", test_data)

        assert result["success"] is True
        assert result["data"] == {"updated": True}
        mock_requests.patch.assert_called_once()

    def test_db_delete_success(self, firebase_client, mock_requests):
        """Test successful database delete operation"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(hours=1)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_requests.delete.return_value = mock_response

        result = firebase_client.db_delete("users/123")

        assert result["success"] is True
        mock_requests.delete.assert_called_once()

    def test_parse_error_email_exists(self, firebase_client):
        """Test error parsing for EMAIL_EXISTS error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "EMAIL_EXISTS"}}
        mock_exception.response = mock_response

        with patch(
            "src.services.firebase_client.translate_error",
            return_value="Email already exists",
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Email already exists"

    def test_parse_error_invalid_credentials(self, firebase_client):
        """Test error parsing for invalid credentials error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": {"message": "INVALID_LOGIN_CREDENTIALS"}
        }
        mock_exception.response = mock_response

        with patch(
            "src.services.firebase_client.translate_error",
            return_value="Invalid credentials",
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Invalid credentials"

    def test_parse_error_weak_password(self, firebase_client):
        """Test error parsing for weak password error"""
        mock_exception = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "WEAK_PASSWORD"}}
        mock_exception.response = mock_response

        with patch(
            "src.services.firebase_client.translate_error",
            return_value="Password too weak",
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Password too weak"

    def test_parse_error_generic_exception(self, firebase_client):
        """Test error parsing for generic exception"""
        mock_exception = Exception("Generic error")

        with patch(
            "src.services.firebase_client.translate_error", return_value="Generic error"
        ):
            result = firebase_client._parse_error(mock_exception)
            assert result == "Generic error"

    def test_store_auth_data(self, firebase_client):
        """Test storing authentication data"""
        auth_data = {
            "idToken": "test-id-token",
            "refreshToken": "test-refresh-token",
            "localId": "test-user-id",
            "expiresIn": "3600",
        }

        firebase_client._store_auth_data(auth_data)

        assert firebase_client.id_token == "test-id-token"
        assert firebase_client.refresh_token == "test-refresh-token"
        assert firebase_client.user_id == "test-user-id"
        assert firebase_client.token_expiry is not None

    @pytest.mark.parametrize(
        "operation,method_name",
        [
            ("db_get", "get"),
            ("db_set", "put"),
            ("db_update", "patch"),
            ("db_delete", "delete"),
        ],
    )
    def test_database_operations_with_network_error(
        self, firebase_client, operation, method_name, mock_requests
    ):
        """Test database operations with network errors"""
        firebase_client.id_token = "test-token"
        firebase_client.refresh_token = "test-refresh"
        firebase_client.token_expiry = datetime.now() + timedelta(hours=1)

        mock_requests.get.side_effect = requests.exceptions.ConnectionError(
            "Network error"
        )
        mock_requests.put.side_effect = requests.exceptions.ConnectionError(
            "Network error"
        )
        mock_requests.patch.side_effect = requests.exceptions.ConnectionError(
            "Network error"
        )
        mock_requests.delete.side_effect = requests.exceptions.ConnectionError(
            "Network error"
        )

        if operation == "db_get":
            result = firebase_client.db_get("test/path")
        elif operation == "db_set":
            result = firebase_client.db_set("test/path", {"data": "test"})
        elif operation == "db_update":
            result = firebase_client.db_update("test/path", {"data": "test"})
        elif operation == "db_delete":
            result = firebase_client.db_delete("test/path")

        assert result["success"] is False
        assert "error" in result

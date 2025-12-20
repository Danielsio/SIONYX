"""
Tests for AuthService
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from src.services.auth_service import AuthService


class TestAuthService:
    """Test cases for AuthService"""

    @pytest.fixture
    def auth_service(self, mock_firebase_client):
        """Create AuthService instance with mocked dependencies"""
        with patch(
            "src.services.auth_service.FirebaseClient",
            return_value=mock_firebase_client,
        ), patch("src.services.auth_service.LocalDatabase"), patch(
            "src.services.auth_service.ComputerService"
        ):
            return AuthService()

    def test_initialization(self, auth_service):
        """Test AuthService initialization"""
        assert auth_service.current_user is None
        assert auth_service.config is None

    def test_phone_to_email_conversion(self):
        """Test phone number to email conversion"""
        # Test with clean phone number
        assert AuthService._phone_to_email("1234567890") == "1234567890@sionyx.app"

        # Test with phone number containing special characters
        assert AuthService._phone_to_email("+1-234-567-890") == "1234567890@sionyx.app"

        # Test with phone number containing spaces
        assert AuthService._phone_to_email("123 456 7890") == "1234567890@sionyx.app"

        # Test with empty string
        assert AuthService._phone_to_email("") == "@sionyx.app"

    def test_is_logged_in_no_stored_token(self, auth_service):
        """Test is_logged_in when no stored token exists"""
        auth_service.local_db.get_stored_token.return_value = None

        result = auth_service.is_logged_in()

        assert result is False

    def test_is_logged_in_valid_token(
        self, auth_service, mock_firebase_client, sample_user_data
    ):
        """Test is_logged_in with valid stored token"""
        auth_service.local_db.get_stored_token.return_value = "test-refresh-token"
        mock_firebase_client.refresh_token_request.return_value = {"success": True}
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": sample_user_data,
        }

        with patch.object(auth_service, "_recover_orphaned_session"), patch.object(
            auth_service, "_handle_computer_registration"
        ):
            result = auth_service.is_logged_in()

        assert result is True
        assert auth_service.current_user == sample_user_data
        assert auth_service.current_user["uid"] == mock_firebase_client.user_id

    def test_is_logged_in_invalid_token(self, auth_service):
        """Test is_logged_in with invalid stored token"""
        auth_service.local_db.get_stored_token.return_value = "invalid-token"
        auth_service.firebase.refresh_token_request.return_value = {"success": False}

        result = auth_service.is_logged_in()

        assert result is False

    def test_login_success(self, auth_service, mock_firebase_client, sample_user_data):
        """Test successful login"""
        phone = "1234567890"
        password = "password123"

        mock_firebase_client.sign_in.return_value = {
            "success": True,
            "uid": "test-user-id",
            "refresh_token": "test-refresh-token",
        }
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": sample_user_data,
        }

        with patch.object(auth_service, "_recover_orphaned_session"), patch.object(
            auth_service, "_handle_computer_registration"
        ), patch(
            "src.services.auth_service.translate_error", return_value="Error message"
        ):
            result = auth_service.login(phone, password)

        assert result["success"] is True
        assert result["user"] == sample_user_data
        assert auth_service.current_user == sample_user_data
        auth_service.local_db.store_credentials.assert_called_once()

    def test_login_firebase_failure(self, auth_service, mock_firebase_client):
        """Test login with Firebase authentication failure"""
        phone = "1234567890"
        password = "wrongpassword"

        mock_firebase_client.sign_in.return_value = {
            "success": False,
            "error": "INVALID_LOGIN_CREDENTIALS",
        }

        with patch(
            "src.services.auth_service.translate_error",
            return_value="Invalid credentials",
        ):
            result = auth_service.login(phone, password)

        assert result["success"] is False
        assert result["error"] == "Invalid credentials"

    def test_login_user_data_not_found(self, auth_service, mock_firebase_client):
        """Test login when user data is not found in database"""
        phone = "1234567890"
        password = "password123"

        mock_firebase_client.sign_in.return_value = {
            "success": True,
            "uid": "test-user-id",
            "refresh_token": "test-refresh-token",
        }
        mock_firebase_client.db_get.return_value = {"success": False}

        with patch(
            "src.services.auth_service.translate_error",
            return_value="User data not found",
        ):
            result = auth_service.login(phone, password)

        assert result["success"] is False
        assert result["error"] == "User data not found"

    def test_register_success(self, auth_service, mock_firebase_client):
        """Test successful user registration"""
        phone = "1234567890"
        password = "password123"
        first_name = "John"
        last_name = "Doe"
        email = "john@example.com"

        mock_firebase_client.sign_up.return_value = {
            "success": True,
            "uid": "test-user-id",
            "refresh_token": "test-refresh-token",
        }
        mock_firebase_client.db_set.return_value = {"success": True}

        result = auth_service.register(phone, password, first_name, last_name, email)

        assert result["success"] is True
        assert result["user"]["firstName"] == first_name
        assert result["user"]["lastName"] == last_name
        assert result["user"]["phoneNumber"] == phone
        assert result["user"]["email"] == email
        assert result["user"]["remainingTime"] == 0
        assert result["user"]["remainingPrints"] == 0.0
        assert result["user"]["isActive"] is True
        assert result["user"]["isAdmin"] is False
        auth_service.local_db.store_credentials.assert_called_once()

    def test_register_weak_password(self, auth_service):
        """Test registration with weak password"""
        phone = "1234567890"
        password = "123"  # Too short
        first_name = "John"
        last_name = "Doe"

        with patch(
            "src.services.auth_service.translate_error",
            return_value="Password too short",
        ):
            result = auth_service.register(phone, password, first_name, last_name)

        assert result["success"] is False
        assert result["error"] == "Password too short"

    def test_register_firebase_failure(self, auth_service, mock_firebase_client):
        """Test registration with Firebase signup failure"""
        phone = "1234567890"
        password = "password123"
        first_name = "John"
        last_name = "Doe"

        mock_firebase_client.sign_up.return_value = {
            "success": False,
            "error": "EMAIL_EXISTS",
        }

        with patch(
            "src.services.auth_service.translate_error",
            return_value="Email already exists",
        ):
            result = auth_service.register(phone, password, first_name, last_name)

        assert result["success"] is False
        assert result["error"] == "Email already exists"

    def test_register_database_failure(self, auth_service, mock_firebase_client):
        """Test registration with database save failure"""
        phone = "1234567890"
        password = "password123"
        first_name = "John"
        last_name = "Doe"

        mock_firebase_client.sign_up.return_value = {
            "success": True,
            "uid": "test-user-id",
            "refresh_token": "test-refresh-token",
        }
        mock_firebase_client.db_set.return_value = {"success": False}

        result = auth_service.register(phone, password, first_name, last_name)

        assert result["success"] is False
        assert result["error"] == "Failed to create user profile"

    def test_logout(self, auth_service, sample_user_data):
        """Test user logout"""
        auth_service.current_user = sample_user_data
        auth_service.firebase.id_token = "test-token"
        auth_service.firebase.refresh_token = "test-refresh"
        auth_service.firebase.user_id = "test-user-id"

        auth_service.logout()

        assert auth_service.current_user is None
        assert auth_service.firebase.id_token is None
        assert auth_service.firebase.refresh_token is None
        assert auth_service.firebase.user_id is None
        auth_service.local_db.clear_tokens.assert_called_once()

    def test_get_current_user(self, auth_service, sample_user_data):
        """Test getting current user data"""
        auth_service.current_user = sample_user_data

        result = auth_service.get_current_user()

        assert result == sample_user_data

    def test_get_current_user_not_logged_in(self, auth_service):
        """Test getting current user when not logged in"""
        result = auth_service.get_current_user()

        assert result is None

    def test_update_user_data_success(
        self, auth_service, mock_firebase_client, sample_user_data
    ):
        """Test successful user data update"""
        auth_service.current_user = sample_user_data
        updates = {"remainingTime": 3600, "remainingPrints": 50.0}
        mock_firebase_client.db_update.return_value = {"success": True}

        result = auth_service.update_user_data(updates)

        assert result["success"] is True
        assert auth_service.current_user["remainingTime"] == 3600
        assert auth_service.current_user["remainingPrints"] == 50.0
        assert "updatedAt" in auth_service.current_user

    def test_update_user_data_not_logged_in(self, auth_service):
        """Test updating user data when not logged in"""
        updates = {"remainingTime": 3600}

        result = auth_service.update_user_data(updates)

        assert result["success"] is False
        assert result["error"] == "No user logged in"

    def test_update_user_data_database_failure(
        self, auth_service, mock_firebase_client, sample_user_data
    ):
        """Test user data update with database failure"""
        auth_service.current_user = sample_user_data
        updates = {"remainingTime": 3600}
        mock_firebase_client.db_update.return_value = {
            "success": False,
            "error": "Database error",
        }

        result = auth_service.update_user_data(updates)

        assert result["success"] is False
        assert result["error"] == "Database error"
        # Local cache should not be updated on database failure
        assert auth_service.current_user["remainingTime"] != 3600

    def test_recover_orphaned_session_no_active_session(
        self, auth_service, mock_firebase_client
    ):
        """Test orphaned session recovery when no active session"""
        user_id = "test-user-id"
        user_data = {"isSessionActive": False}
        mock_firebase_client.db_get.return_value = {"success": True, "data": user_data}

        auth_service._recover_orphaned_session(user_id)

        # Should not call db_update
        mock_firebase_client.db_update.assert_not_called()

    def test_recover_orphaned_session_old_session(
        self, auth_service, mock_firebase_client
    ):
        """Test orphaned session recovery with old session"""
        user_id = "test-user-id"
        old_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        user_data = {"isSessionActive": True, "lastActivity": old_time.isoformat()}
        mock_firebase_client.db_get.return_value = {"success": True, "data": user_data}

        auth_service._recover_orphaned_session(user_id)

        # Should clean up the session
        mock_firebase_client.db_update.assert_called_once()
        call_args = mock_firebase_client.db_update.call_args
        assert call_args[0][0] == f"users/{user_id}"
        assert call_args[0][1]["isSessionActive"] is False

    def test_recover_orphaned_session_recent_session(
        self, auth_service, mock_firebase_client
    ):
        """Test orphaned session recovery with recent session"""
        user_id = "test-user-id"
        recent_time = datetime.now()
        user_data = {"isSessionActive": True, "lastActivity": recent_time.isoformat()}
        mock_firebase_client.db_get.return_value = {"success": True, "data": user_data}

        auth_service._recover_orphaned_session(user_id)

        # Should not clean up recent session
        mock_firebase_client.db_update.assert_not_called()

    def test_handle_computer_registration_success(self, auth_service):
        """Test successful computer registration"""
        user_id = "test-user-id"
        computer_id = "test-computer-id"

        auth_service.computer_service.register_computer.return_value = {
            "success": True,
            "computer_id": computer_id,
        }
        auth_service.computer_service.associate_user_with_computer.return_value = {
            "success": True
        }

        auth_service._handle_computer_registration(user_id)

        auth_service.computer_service.register_computer.assert_called_once()
        auth_service.computer_service.associate_user_with_computer.assert_called_once_with(
            user_id, computer_id
        )

    def test_handle_computer_registration_failure(self, auth_service):
        """Test computer registration failure"""
        user_id = "test-user-id"

        auth_service.computer_service.register_computer.return_value = {
            "success": False,
            "error": "Registration failed",
        }

        # Should not raise exception
        auth_service._handle_computer_registration(user_id)

        auth_service.computer_service.register_computer.assert_called_once()
        auth_service.computer_service.associate_user_with_computer.assert_not_called()

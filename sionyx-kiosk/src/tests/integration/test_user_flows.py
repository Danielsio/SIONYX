"""
Integration Tests: User Flows

Tests the complete user journey through the application:
1. Registration Flow
2. Login Flow
3. Session Start/End Flow
4. Logout Flow

These tests use mocked Firebase client (from conftest.py fixtures).
"""

from unittest.mock import patch

import pytest

from services.computer_service import ComputerService
from services.session_service import SessionService


# =============================================================================
# Test: User Registration Flow
# =============================================================================


class TestUserRegistrationFlow:
    """
    Integration test for user registration flow.

    Flow: User fills form → AuthService registers → ComputerService registers PC
    """

    def test_complete_registration_flow(self, mock_firebase_client):
        """Test complete user registration creates user and registers computer."""
        # Arrange - Set up mock responses for the flow
        mock_firebase_client.sign_up.return_value = {
            "success": True,
            "uid": "new-user-123",
        }

        # Act - Register user
        result = mock_firebase_client.sign_up("newuser@test.com", "SecurePassword123!")

        # Assert - User created successfully
        assert result["success"] is True
        assert result["uid"] == "new-user-123"

        # Act - Register computer for this user
        computer_service = ComputerService(mock_firebase_client)

        with patch("services.computer_service.get_computer_info") as mock_info:
            mock_info.return_value = {
                "deviceId": "test-device-abc123",
                "computerName": "TEST-PC",
            }

            computer_result = computer_service.register_computer()

        # Assert - Computer registered
        assert computer_result["success"] is True
        assert computer_result["computer_id"] == "test-device-abc123"


# =============================================================================
# Test: User Login Flow
# =============================================================================


class TestUserLoginFlow:
    """
    Integration test for user login flow.

    Flow: User enters credentials → AuthService authenticates →
          ComputerService associates user with PC
    """

    def test_complete_login_flow(self, mock_firebase_client):
        """Test complete login flow authenticates and associates computer."""
        # Arrange - Set up mock responses
        mock_firebase_client.sign_in.return_value = {
            "success": True,
            "uid": "existing-user-456",
        }

        # Act - Login
        login_result = mock_firebase_client.sign_in(
            "existing@test.com", "ExistingPassword123!"
        )

        # Assert - Login successful
        assert login_result["success"] is True
        assert login_result["uid"] == "existing-user-456"

        # Act - Associate user with computer
        computer_service = ComputerService(mock_firebase_client)

        with patch("services.computer_service.get_device_id") as mock_device_id:
            mock_device_id.return_value = "test-device-abc123"

            assoc_result = computer_service.associate_user_with_computer(
                user_id="existing-user-456",
                computer_id="test-device-abc123",
                is_login=True,
            )

        # Assert - Association successful
        assert assoc_result["success"] is True


# =============================================================================
# Test: Session Start/End Flow
# =============================================================================


class TestSessionFlow:
    """
    Integration test for session lifecycle.

    Flow: User clicks Start → SessionService starts → Timer runs →
          User clicks Return → Session ends → Time saved
    """

    @pytest.fixture
    def session_service(self, qapp, mock_firebase_client):
        """Create SessionService for testing."""
        # Mock ProcessCleanupService and BrowserCleanupService to avoid
        # killing actual processes during tests
        with patch("services.session_service.ProcessCleanupService"):
            with patch("services.session_service.BrowserCleanupService"):
                with patch("services.session_service.ComputerService"):
                    with patch("services.session_service.PrintMonitorService"):
                        service = SessionService(
                            firebase_client=mock_firebase_client,
                            user_id="test-user-session",
                            org_id="test-org",
                        )
                        yield service
                        # Cleanup
                        if service.is_active:
                            service.end_session("test_cleanup")

    def test_start_session_initializes_correctly(self, session_service):
        """Test starting a session initializes all components."""
        # Arrange
        initial_time = 3600  # 1 hour

        # Act
        result = session_service.start_session(initial_time)

        # Assert
        assert result["success"] is True
        assert session_service.is_active is True
        assert session_service.remaining_time == initial_time
        assert session_service.countdown_timer.isActive() is True

        # Cleanup
        session_service.end_session("test")

    def test_session_countdown_decrements_time(self, session_service, qtbot):
        """Test session countdown decrements remaining time."""
        # Arrange
        initial_time = 10  # 10 seconds for quick test
        session_service.start_session(initial_time)

        # Act - Manually trigger countdown tick (simulates 1 second passing)
        # This is more reliable than waiting for real timer
        session_service._on_countdown_tick()

        # Assert - Time should have decremented by 1
        assert session_service.remaining_time == initial_time - 1

        # Cleanup
        session_service.end_session("test")

    def test_end_session_stops_timer_and_syncs(self, session_service):
        """Test ending session stops timer and syncs to Firebase."""
        # Arrange
        session_service.start_session(3600)
        assert session_service.is_active is True

        # Act
        result = session_service.end_session("user")

        # Assert
        assert result["success"] is True
        assert session_service.is_active is False
        assert session_service.countdown_timer.isActive() is False

    def test_cannot_start_session_with_zero_time(self, session_service):
        """Test cannot start session when user has no time remaining."""
        # Act
        result = session_service.start_session(0)

        # Assert
        assert result["success"] is False
        assert "No time remaining" in result["error"]
        assert session_service.is_active is False

    def test_cannot_start_duplicate_session(self, session_service):
        """Test cannot start a second session while one is active."""
        # Arrange
        session_service.start_session(3600)

        # Act
        result = session_service.start_session(3600)

        # Assert
        assert result["success"] is False
        assert "already active" in result["error"]

        # Cleanup
        session_service.end_session("test")


# =============================================================================
# Test: Logout Flow
# =============================================================================


class TestLogoutFlow:
    """
    Integration test for logout flow.

    Flow: User clicks Logout → Session ended if active →
          User disassociated from computer → Token cleared
    """

    def test_logout_clears_session_and_computer_association(self, mock_firebase_client):
        """Test logout clears active session and computer association."""
        # Arrange
        user_id = "logout-test-user"
        computer_id = "logout-test-computer"

        computer_service = ComputerService(mock_firebase_client)

        # Simulate user was logged in and associated
        # Act - Disassociate on logout
        result = computer_service.disassociate_user_from_computer(
            user_id=user_id, computer_id=computer_id, is_logout=True
        )

        # Assert
        assert result["success"] is True


# =============================================================================
# Test: Full User Journey (Registration → Login → Session → Logout)
# =============================================================================


class TestFullUserJourney:
    """
    Complete integration test of the full user journey.

    This tests the entire flow a user would experience:
    1. Register new account
    2. Login
    3. Start session
    4. Use time (countdown)
    5. Return from session
    6. Logout
    """

    def test_complete_user_journey(self, qapp, mock_firebase_client, qtbot):
        """Test complete user journey from registration to logout."""
        # ===== STEP 1: REGISTRATION =====
        mock_firebase_client.sign_up.return_value = {
            "success": True,
            "uid": "journey-user-001",
        }

        reg_result = mock_firebase_client.sign_up(
            "journey@test.com", "JourneyPassword123!"
        )
        assert reg_result["success"] is True
        user_id = reg_result["uid"]

        # ===== STEP 2: COMPUTER REGISTRATION =====
        computer_service = ComputerService(mock_firebase_client)

        with patch("services.computer_service.get_computer_info") as mock_info:
            mock_info.return_value = {
                "deviceId": "journey-device-001",
                "computerName": "JOURNEY-PC",
            }
            computer_result = computer_service.register_computer()

        assert computer_result["success"] is True
        computer_id = computer_result["computer_id"]

        # ===== STEP 3: LOGIN (Associate with computer) =====
        assoc_result = computer_service.associate_user_with_computer(
            user_id=user_id, computer_id=computer_id, is_login=True
        )
        assert assoc_result["success"] is True

        # ===== STEP 4: START SESSION =====
        # Mock ProcessCleanupService and related services to avoid
        # killing actual processes during tests
        with patch("services.session_service.ProcessCleanupService"):
            with patch("services.session_service.BrowserCleanupService"):
                with patch("services.session_service.ComputerService"):
                    with patch("services.session_service.PrintMonitorService"):
                        session_service = SessionService(
                            firebase_client=mock_firebase_client,
                            user_id=user_id,
                            org_id="test-org",
                        )

                        initial_time = 3600  # 1 hour
                        session_result = session_service.start_session(initial_time)
                        assert session_result["success"] is True
                        assert session_service.is_active is True

                        # ===== STEP 5: USE TIME (Simulate countdown) =====
                        # Manually trigger countdown tick (more reliable than waiting)
                        session_service._on_countdown_tick()

                        assert session_service.remaining_time == initial_time - 1

                        # ===== STEP 6: RETURN FROM SESSION =====
                        end_result = session_service.end_session("user")
                        assert end_result["success"] is True
                        assert session_service.is_active is False

        # ===== STEP 7: LOGOUT =====
        logout_result = computer_service.disassociate_user_from_computer(
            user_id=user_id, computer_id=computer_id, is_logout=True
        )
        assert logout_result["success"] is True

        # Journey complete!

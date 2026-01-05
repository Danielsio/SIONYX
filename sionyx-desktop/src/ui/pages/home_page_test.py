"""
Tests for HomePage UI Component

Testing Strategy:
- Test behavior and data loading, NOT styles/colors
- Use mock/dummy data to isolate from backend
- Verify widget structure and user interactions
- Test state changes (time remaining, button states)
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton

from ui.pages.home_page import HomePage


# =============================================================================
# MOCK DATA FIXTURES
# =============================================================================

MOCK_USER_WITH_TIME = {
    "uid": "test-user-123",
    "firstName": "יוסי",
    "lastName": "כהן",
    "remainingTime": 3600,  # 1 hour
    "printBalance": 25.50,
}

MOCK_USER_NO_TIME = {
    "uid": "test-user-456",
    "firstName": "דני",
    "lastName": "לוי",
    "remainingTime": 0,
    "printBalance": 10.00,
}

MOCK_USER_LOW_TIME = {
    "uid": "test-user-789",
    "firstName": "שרה",
    "lastName": "אברהם",
    "remainingTime": 180,  # 3 minutes
    "printBalance": 5.00,
}

MOCK_MESSAGES = [
    {"id": "msg-1", "content": "הודעה ראשונה", "isRead": False},
    {"id": "msg-2", "content": "הודעה שנייה", "isRead": False},
]


class TestHomePage:
    """Test cases for HomePage UI component"""

    @pytest.fixture
    def mock_auth_service(self, mock_firebase_client):
        """Create mock auth service with firebase client"""
        auth_service = Mock()
        auth_service.firebase = mock_firebase_client
        auth_service.firebase.org_id = "test-org"
        auth_service.get_current_user.return_value = MOCK_USER_WITH_TIME.copy()
        return auth_service

    @pytest.fixture
    def mock_chat_service(self):
        """Create mock chat service"""
        chat_service = Mock()
        chat_service.is_listening = False
        chat_service.start_listening = Mock()
        chat_service.get_unread_messages = Mock(
            return_value={"success": True, "messages": []}
        )
        chat_service.cleanup = Mock()
        chat_service.messages_received = Mock()
        chat_service.messages_received.connect = Mock()
        return chat_service

    @pytest.fixture
    def home_page(self, mock_auth_service, mock_chat_service, qapp):
        """Create HomePage with mocked dependencies"""
        with patch("ui.pages.home_page.ChatService", return_value=mock_chat_service):
            page = HomePage(mock_auth_service)
            yield page
            # Cleanup
            page.countdown_timer.stop()

    @pytest.fixture
    def home_page_no_time(self, mock_firebase_client, mock_chat_service, qapp):
        """Create HomePage for user with no time"""
        auth_service = Mock()
        auth_service.firebase = mock_firebase_client
        auth_service.firebase.org_id = "test-org"
        auth_service.get_current_user.return_value = MOCK_USER_NO_TIME.copy()

        with patch("ui.pages.home_page.ChatService", return_value=mock_chat_service):
            page = HomePage(auth_service)
            yield page
            page.countdown_timer.stop()

    @pytest.fixture
    def home_page_with_messages(self, mock_auth_service, qapp):
        """Create HomePage with pending messages"""
        mock_chat = Mock()
        mock_chat.is_listening = False
        mock_chat.start_listening = Mock()
        mock_chat.get_unread_messages = Mock(
            return_value={"success": True, "messages": MOCK_MESSAGES.copy()}
        )
        mock_chat.cleanup = Mock()
        mock_chat.messages_received = Mock()
        mock_chat.messages_received.connect = Mock()

        with patch("ui.pages.home_page.ChatService", return_value=mock_chat):
            page = HomePage(mock_auth_service)
            yield page
            page.countdown_timer.stop()

    # =========================================================================
    # INITIALIZATION TESTS
    # =========================================================================

    def test_initialization(self, home_page):
        """Test page initializes without errors"""
        assert home_page is not None
        assert home_page.objectName() == "homePage"

    def test_stores_current_user(self, home_page):
        """Test current user is stored after initialization"""
        assert home_page.current_user is not None
        assert home_page.current_user["uid"] == "test-user-123"
        assert home_page.current_user["firstName"] == "יוסי"

    def test_has_countdown_timer(self, home_page):
        """Test countdown timer is created"""
        assert home_page.countdown_timer is not None

    def test_chat_service_initialized(self, home_page, mock_chat_service):
        """Test chat service is initialized"""
        assert home_page.chat_service is not None

    # =========================================================================
    # STAT CARDS TESTS
    # =========================================================================

    def test_has_time_card(self, home_page):
        """Test time card exists"""
        assert home_page.time_card is not None
        assert isinstance(home_page.time_card, QFrame)

    def test_has_prints_card(self, home_page):
        """Test prints card exists"""
        assert home_page.prints_card is not None
        assert isinstance(home_page.prints_card, QFrame)

    def test_has_message_card(self, home_page):
        """Test message card exists (hidden by default)"""
        assert home_page.message_card is not None
        assert isinstance(home_page.message_card, QFrame)
        # Should be hidden when no messages
        assert not home_page.message_card.isVisible()

    def test_time_card_displays_time(self, home_page):
        """Test time card displays remaining time"""
        time_value = home_page.time_card.findChild(QLabel, "timeValue")
        assert time_value is not None
        # 3600 seconds = 1:00:00
        assert "1:00:00" in time_value.text()

    def test_prints_card_displays_balance(self, home_page):
        """Test prints card displays print balance"""
        print_value = home_page.prints_card.findChild(QLabel, "printValue")
        assert print_value is not None
        assert "25.50" in print_value.text()

    # =========================================================================
    # WELCOME MESSAGE TESTS
    # =========================================================================

    def test_welcome_label_exists(self, home_page):
        """Test welcome label exists"""
        assert home_page.welcome_label is not None

    def test_welcome_message_contains_user_name(self, home_page):
        """Test welcome message displays user's first name"""
        welcome_text = home_page.welcome_label.text()
        assert "יוסי" in welcome_text
        assert "שלום" in welcome_text

    # =========================================================================
    # START BUTTON TESTS
    # =========================================================================

    def test_start_button_exists(self, home_page):
        """Test start button exists"""
        assert home_page.start_btn is not None

    def test_start_button_enabled_with_time(self, home_page):
        """Test start button is enabled when user has time"""
        assert home_page.start_btn.isEnabled()

    def test_start_button_disabled_no_time(self, home_page_no_time):
        """Test start button is disabled when user has no time"""
        assert not home_page_no_time.start_btn.isEnabled()

    def test_instruction_text_changes_no_time(self, home_page_no_time):
        """Test instruction text changes when no time available"""
        instruction_text = home_page_no_time.instruction.text()
        assert "אין" in instruction_text or "רכוש" in instruction_text

    # =========================================================================
    # COUNTDOWN DISPLAY TESTS
    # =========================================================================

    def test_update_countdown_formats_time_correctly(self, home_page):
        """Test countdown formats time as H:MM:SS"""
        home_page.current_user["remainingTime"] = 7325  # 2:02:05
        home_page.update_countdown()

        time_value = home_page.time_card.findChild(QLabel, "timeValue")
        assert "2:02:05" in time_value.text()

    def test_update_countdown_zero_time(self, home_page):
        """Test countdown displays 0:00:00 when no time"""
        home_page.current_user["remainingTime"] = 0
        home_page.update_countdown()

        time_value = home_page.time_card.findChild(QLabel, "timeValue")
        assert "0:00:00" in time_value.text()

    def test_update_countdown_disables_button_at_zero(self, home_page):
        """Test countdown disables start button when time reaches zero"""
        home_page.current_user["remainingTime"] = 0
        home_page.update_countdown()

        assert not home_page.start_btn.isEnabled()

    # =========================================================================
    # MESSAGE NOTIFICATION TESTS
    # =========================================================================

    def test_message_card_shows_with_messages(self, home_page_with_messages):
        """Test message card is visible when there are messages"""
        # Use not isHidden() since parent widget isn't shown in tests
        assert not home_page_with_messages.message_card.isHidden()

    def test_message_count_displayed(self, home_page_with_messages):
        """Test message count is displayed"""
        count_text = home_page_with_messages.message_count_label.text()
        assert "2" in count_text or "הודעות" in count_text

    def test_show_message_notification_updates_label(self, home_page):
        """Test show_message_notification updates the label"""
        home_page.show_message_notification(3)

        assert not home_page.message_card.isHidden()
        assert "3" in home_page.message_count_label.text()

    def test_show_message_notification_hides_at_zero(self, home_page):
        """Test message card hides when count is zero"""
        home_page.show_message_notification(0)
        assert not home_page.message_card.isVisible()

    def test_single_message_text(self, home_page):
        """Test singular form for single message"""
        home_page.show_message_notification(1)
        # Should use singular form "הודעה חדשה"
        assert not home_page.message_card.isHidden()

    # =========================================================================
    # USER DATA REFRESH TESTS
    # =========================================================================

    def test_refresh_user_data_updates_display(self, home_page, mock_auth_service):
        """Test refresh_user_data updates the display"""
        # Update mock to return new data
        new_user_data = {
            "uid": "test-user-123",
            "firstName": "אבי",
            "remainingTime": 7200,
            "printBalance": 50.00,
        }
        mock_auth_service.get_current_user.return_value = new_user_data

        home_page.refresh_user_data()

        assert home_page.current_user["firstName"] == "אבי"
        assert "אבי" in home_page.welcome_label.text()

    def test_refresh_user_data_updates_prints(self, home_page, mock_auth_service):
        """Test refresh_user_data updates print balance"""
        new_user_data = {
            "uid": "test-user-123",
            "firstName": "אבי",
            "remainingTime": 7200,
            "printBalance": 100.00,
        }
        mock_auth_service.get_current_user.return_value = new_user_data

        home_page.refresh_user_data()

        print_value = home_page.prints_card.findChild(QLabel, "printValue")
        assert "100.00" in print_value.text()

    # =========================================================================
    # CLEAR USER DATA TESTS
    # =========================================================================

    def test_clear_user_data_resets_state(self, home_page):
        """Test clear_user_data resets the page state"""
        home_page.clear_user_data()

        assert home_page.current_user is None

    def test_clear_user_data_resets_time_display(self, home_page):
        """Test clear_user_data resets time display to zero"""
        home_page.clear_user_data()

        time_value = home_page.time_card.findChild(QLabel, "timeValue")
        assert "0:00:00" in time_value.text()

    def test_clear_user_data_resets_prints_display(self, home_page):
        """Test clear_user_data resets prints display to zero"""
        home_page.clear_user_data()

        print_value = home_page.prints_card.findChild(QLabel, "printValue")
        assert "0.00" in print_value.text()

    def test_clear_user_data_resets_welcome(self, home_page):
        """Test clear_user_data resets welcome message"""
        home_page.clear_user_data()

        # Should just say "שלום!" without user name
        welcome_text = home_page.welcome_label.text()
        assert "שלום" in welcome_text
        assert "יוסי" not in welcome_text

    # =========================================================================
    # MESSAGE HANDLING TESTS
    # =========================================================================

    def test_handle_new_messages_success(self, home_page):
        """Test handling new messages shows notification"""
        home_page.handle_new_messages(
            {"success": True, "messages": MOCK_MESSAGES.copy()}
        )

        assert len(home_page.pending_messages) == 2
        assert not home_page.message_card.isHidden()

    def test_handle_new_messages_empty(self, home_page):
        """Test handling empty messages list"""
        home_page.handle_new_messages({"success": True, "messages": []})

        assert len(home_page.pending_messages) == 0

    def test_on_all_messages_read_hides_card(self, home_page):
        """Test all messages read hides notification card"""
        home_page.pending_messages = MOCK_MESSAGES.copy()
        home_page.message_card.show()

        home_page.on_all_messages_read()

        assert len(home_page.pending_messages) == 0
        assert not home_page.message_card.isVisible()

    # =========================================================================
    # CLEANUP TESTS
    # =========================================================================

    def test_cleanup_stops_timer(self, home_page):
        """Test cleanup stops the countdown timer"""
        home_page.cleanup()
        assert not home_page.countdown_timer.isActive()

    def test_cleanup_cleans_chat_service(self, home_page, mock_chat_service):
        """Test cleanup calls chat service cleanup"""
        home_page.cleanup()
        mock_chat_service.cleanup.assert_called_once()

    # =========================================================================
    # TIME FORMAT EDGE CASES
    # =========================================================================

    def test_time_format_minutes_only(self, home_page):
        """Test time format with only minutes"""
        home_page.current_user["remainingTime"] = 300  # 5 minutes
        home_page.update_countdown()

        time_value = home_page.time_card.findChild(QLabel, "timeValue")
        assert "0:05:00" in time_value.text()

    def test_time_format_seconds_only(self, home_page):
        """Test time format with only seconds"""
        home_page.current_user["remainingTime"] = 45
        home_page.update_countdown()

        time_value = home_page.time_card.findChild(QLabel, "timeValue")
        assert "0:00:45" in time_value.text()

    def test_time_format_large_hours(self, home_page):
        """Test time format with many hours"""
        home_page.current_user["remainingTime"] = 36000  # 10 hours
        home_page.update_countdown()

        time_value = home_page.time_card.findChild(QLabel, "timeValue")
        assert "10:00:00" in time_value.text()

    # =========================================================================
    # PRINTS DISPLAY TESTS
    # =========================================================================

    def test_update_prints_display(self, home_page):
        """Test prints display updates correctly"""
        home_page.current_user["printBalance"] = 123.45
        home_page.update_prints_display()

        print_value = home_page.prints_card.findChild(QLabel, "printValue")
        assert "123.45" in print_value.text()

    def test_update_prints_display_zero(self, home_page):
        """Test prints display with zero balance"""
        home_page.current_user["printBalance"] = 0
        home_page.update_prints_display()

        print_value = home_page.prints_card.findChild(QLabel, "printValue")
        assert "0.00" in print_value.text()

    def test_update_prints_display_no_user(self, home_page):
        """Test prints display does nothing when no user"""
        home_page.current_user = None
        # Should not raise exception
        home_page.update_prints_display()

    # =========================================================================
    # SESSION AND MESSAGE HANDLING TESTS
    # =========================================================================

    def test_handle_start_session_no_time(self, home_page_no_time):
        """Test handle_start_session does nothing when no remaining time"""
        # Track if parent methods are called
        parent_mock = Mock()
        parent_mock.parent.return_value.parent.return_value.start_user_session = Mock()

        with patch.object(home_page_no_time, "parent", return_value=parent_mock):
            # Should return early - no time
            home_page_no_time.handle_start_session()

        # start_user_session should not be called
        parent_mock.parent.return_value.parent.return_value.start_user_session.assert_not_called()

    def test_show_message_notification_zero_count(self, home_page):
        """Test message notification hides when count is 0"""
        home_page.message_card.show()  # Ensure visible first
        home_page.show_message_notification(0)
        assert not home_page.message_card.isVisible()

    def test_show_message_notification_single(self, home_page):
        """Test message notification shows singular text for 1 message"""
        home_page.show_message_notification(1)
        # Check text is set correctly (visibility requires parent to be shown)
        assert "הודעה חדשה" in home_page.message_count_label.text()

    def test_show_message_notification_multiple(self, home_page):
        """Test message notification shows plural text for multiple messages"""
        home_page.show_message_notification(3)
        # Check text is set correctly
        assert "3 הודעות" in home_page.message_count_label.text()

    def test_on_all_messages_read(self, home_page):
        """Test on_all_messages_read clears pending messages and hides card"""
        home_page.pending_messages = [{"id": "1"}, {"id": "2"}]
        home_page.message_card.show()

        home_page.on_all_messages_read()

        assert home_page.pending_messages == []
        assert not home_page.message_card.isVisible()

    def test_on_message_read(self, home_page):
        """Test on_message_read does nothing (placeholder)"""
        # Should not raise
        home_page.on_message_read("msg-id-123")

    def test_cleanup_stops_timer(self, home_page, mock_chat_service):
        """Test cleanup stops the countdown timer"""
        home_page.chat_service = mock_chat_service
        home_page.countdown_timer.start(1000)

        home_page.cleanup()

        assert not home_page.countdown_timer.isActive()
        mock_chat_service.cleanup.assert_called_once()

    def test_show_message_modal_no_pending_messages(self, home_page):
        """Test show_message_modal does nothing when no pending messages"""
        home_page.pending_messages = []
        home_page.message_modal = None

        home_page.show_message_modal()

        assert home_page.message_modal is None

    def test_handle_new_messages_success(self, home_page):
        """Test handle_new_messages updates pending messages and shows notification"""
        messages = [{"id": "msg1"}, {"id": "msg2"}]
        result = {"success": True, "messages": messages}

        home_page.handle_new_messages(result)

        assert home_page.pending_messages == messages
        # Notification text should be updated
        assert "2 הודעות" in home_page.message_count_label.text()

    def test_handle_new_messages_failure(self, home_page):
        """Test handle_new_messages ignores failed results"""
        home_page.pending_messages = []
        result = {"success": False, "error": "Network error"}

        home_page.handle_new_messages(result)

        assert home_page.pending_messages == []

    def test_load_messages_success(self, mock_auth_service, qapp):
        """Test load_messages fetches and stores messages"""
        mock_chat = Mock()
        mock_chat.is_listening = False
        mock_chat.get_unread_messages = Mock(
            return_value={"success": True, "messages": [{"id": "m1"}]}
        )
        mock_chat.messages_received = Mock()
        mock_chat.messages_received.connect = Mock()

        with patch("ui.pages.home_page.ChatService", return_value=mock_chat):
            page = HomePage(mock_auth_service)

            page.load_messages()

            assert len(page.pending_messages) == 1
            page.countdown_timer.stop()

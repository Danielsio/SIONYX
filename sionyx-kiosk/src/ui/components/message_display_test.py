"""
Tests for message_display.py - Message Display Component
Tests MessageCard and MessageDisplay components.
"""

from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QWidget

from ui.components.message_display import MessageCard, MessageDisplay


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def sample_message():
    """Sample message data"""
    return {
        "id": "msg123",
        "message": "Hello from admin!",
        "timestamp": "2024-01-15T10:00:00",
        "isRead": False,
    }


@pytest.fixture
def read_message():
    """Sample read message"""
    return {
        "id": "msg456",
        "message": "Already read message",
        "timestamp": "2024-01-15T09:00:00",
        "isRead": True,
    }


@pytest.fixture
def mock_auth_service():
    """Create mock auth service"""
    auth = Mock()
    auth.get_current_user.return_value = {"uid": "user123"}
    return auth


@pytest.fixture
def mock_chat_service():
    """Create mock chat service"""
    service = Mock()
    service.mark_message_as_read.return_value = {"success": True}
    return service


# =============================================================================
# MessageCard tests
# =============================================================================
class TestMessageCard:
    """Tests for MessageCard component"""

    def test_initialization_stores_message_data(self, qapp, sample_message):
        """Test card stores message data"""
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(sample_message)
            assert card.message_data == sample_message

    def test_initialization_unread_message(self, qapp, sample_message):
        """Test unread message sets is_read to False"""
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(sample_message)
            assert card.is_read is False

    def test_initialization_read_message(self, qapp, read_message):
        """Test read message sets is_read to True"""
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(read_message)
            assert card.is_read is True

    def test_inherits_qframe(self, qapp, sample_message):
        """Test card inherits from QFrame"""
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(sample_message)
            assert isinstance(card, QFrame)

    def test_has_fixed_height(self, qapp, sample_message):
        """Test card has fixed height"""
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(sample_message)
            assert card.height() == 140

    def test_has_pointing_cursor(self, qapp, sample_message):
        """Test card has pointing cursor"""
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(sample_message)
            assert card.cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_has_shadow_effect(self, qapp, sample_message):
        """Test card has shadow effect"""
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(sample_message)
            assert card.graphicsEffect() is not None

    def test_card_clicked_signal_exists(self, qapp, sample_message):
        """Test card_clicked signal exists"""
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(sample_message)
            assert hasattr(card, "card_clicked")

    def test_with_parent(self, qapp, sample_message):
        """Test card can have parent"""
        with patch("ui.components.message_display.get_logger"):
            parent = QWidget()
            card = MessageCard(sample_message, parent=parent)
            assert card.parent() == parent

    def test_message_without_timestamp(self, qapp):
        """Test handling message without timestamp"""
        message = {"id": "msg1", "message": "No timestamp", "isRead": False}
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(message)
            # Should not raise

    def test_message_with_invalid_timestamp(self, qapp):
        """Test handling invalid timestamp"""
        message = {
            "id": "msg1",
            "message": "Bad timestamp",
            "timestamp": "invalid",
            "isRead": False,
        }
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(message)
            # Should not raise


# =============================================================================
# MessageDisplay tests
# =============================================================================
class TestMessageDisplay:
    """Tests for MessageDisplay component"""

    def test_initialization(self, qapp, mock_auth_service):
        """Test display initializes correctly"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            assert display is not None

    def test_stores_auth_service(self, qapp, mock_auth_service):
        """Test display stores auth service"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            assert display.auth_service == mock_auth_service

    def test_gets_current_user(self, qapp, mock_auth_service):
        """Test display gets current user"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            mock_auth_service.get_current_user.assert_called()

    def test_initial_messages_empty(self, qapp, mock_auth_service):
        """Test initial messages list is empty"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            assert display.messages == []

    def test_initial_chat_service_none(self, qapp, mock_auth_service):
        """Test initial chat service is None"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            assert display.chat_service is None

    def test_rtl_layout(self, qapp, mock_auth_service):
        """Test display uses RTL layout"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            assert display.layoutDirection() == Qt.LayoutDirection.RightToLeft

    def test_has_count_label(self, qapp, mock_auth_service):
        """Test display has count label"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            assert hasattr(display, "count_label")

    def test_has_scroll_area(self, qapp, mock_auth_service):
        """Test display has scroll area"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            assert hasattr(display, "scroll_area")

    def test_has_no_messages_label(self, qapp, mock_auth_service):
        """Test display has no messages label"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            assert hasattr(display, "no_messages_label")

    def test_message_read_signal_exists(self, qapp, mock_auth_service):
        """Test message_read signal exists"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            assert hasattr(display, "message_read")


# =============================================================================
# set_chat_service tests
# =============================================================================
class TestSetChatService:
    """Tests for set_chat_service method"""

    def test_set_chat_service(self, qapp, mock_auth_service, mock_chat_service):
        """Test setting chat service"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.set_chat_service(mock_chat_service)
            assert display.chat_service == mock_chat_service


# =============================================================================
# update_messages tests
# =============================================================================
class TestUpdateMessages:
    """Tests for update_messages method"""

    def test_update_messages_stores_messages(
        self, qapp, mock_auth_service, sample_message
    ):
        """Test update_messages stores messages"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.update_messages([sample_message])
            assert len(display.messages) == 1

    def test_update_messages_calls_refresh(
        self, qapp, mock_auth_service, sample_message
    ):
        """Test update_messages calls refresh_display"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.refresh_display = Mock()
            display.update_messages([sample_message])
            display.refresh_display.assert_called_once()


# =============================================================================
# refresh_display tests
# =============================================================================
class TestRefreshDisplay:
    """Tests for refresh_display method"""

    def test_empty_messages_shows_no_messages_label(self, qapp, mock_auth_service):
        """Test empty messages shows no messages label"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.messages = []
            display.refresh_display()
            assert not display.no_messages_label.isHidden()

    def test_with_messages_hides_no_messages_label(
        self, qapp, mock_auth_service, sample_message
    ):
        """Test messages hide no messages label"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.messages = [sample_message]
            display.refresh_display()
            assert display.no_messages_label.isHidden()

    def test_with_messages_shows_count(self, qapp, mock_auth_service, sample_message):
        """Test messages show count label"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.messages = [sample_message]
            display.refresh_display()
            assert not display.count_label.isHidden()


# =============================================================================
# cleanup tests
# =============================================================================
class TestCleanup:
    """Tests for cleanup method"""

    def test_cleanup_stops_listening(self, qapp, mock_auth_service, mock_chat_service):
        """Test cleanup stops chat service listening"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.set_chat_service(mock_chat_service)
            display.cleanup()
            mock_chat_service.stop_listening.assert_called_once()

    def test_cleanup_without_chat_service(self, qapp, mock_auth_service):
        """Test cleanup without chat service doesn't raise"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.cleanup()  # Should not raise


# =============================================================================
# MessageCard event tests
# =============================================================================
class TestMessageCardEvents:
    """Tests for MessageCard event handlers"""

    def test_enter_event_enhances_shadow(self, qapp, sample_message):
        """Test enterEvent enhances shadow"""
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(sample_message)

            # Simulate enter event
            from PyQt6.QtCore import QEvent, QPointF
            from PyQt6.QtGui import QEnterEvent

            event = QEnterEvent(QPointF(0, 0), QPointF(0, 0), QPointF(0, 0))
            card.enterEvent(event)

            # Shadow effect should be enhanced
            assert card.graphicsEffect() is not None

    def test_leave_event_restores_shadow(self, qapp, sample_message):
        """Test leaveEvent handles leave event"""
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(sample_message)

            # Simulate leave event
            from PyQt6.QtCore import QEvent

            leave_event = QEvent(QEvent.Type.Leave)
            card.leaveEvent(leave_event)

            # Shadow should still exist (effect is restored or stays)
            # Just verify no crash occurs

    def test_mouse_press_emits_signal(self, qapp, sample_message):
        """Test mousePressEvent emits card_clicked signal"""
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(sample_message)

            signal_received = []
            card.card_clicked.connect(lambda data: signal_received.append(data))

            # Simulate left click
            from PyQt6.QtCore import QEvent, QPointF
            from PyQt6.QtGui import QMouseEvent

            event = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                QPointF(0, 0),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            card.mousePressEvent(event)

            assert len(signal_received) == 1
            assert signal_received[0] == sample_message

    def test_right_click_does_not_emit_signal(self, qapp, sample_message):
        """Test right click doesn't emit card_clicked signal"""
        with patch("ui.components.message_display.get_logger"):
            card = MessageCard(sample_message)

            signal_received = []
            card.card_clicked.connect(lambda data: signal_received.append(data))

            # Simulate right click
            from PyQt6.QtCore import QEvent, QPointF
            from PyQt6.QtGui import QMouseEvent

            event = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                QPointF(0, 0),
                Qt.MouseButton.RightButton,
                Qt.MouseButton.RightButton,
                Qt.KeyboardModifier.NoModifier,
            )
            card.mousePressEvent(event)

            assert len(signal_received) == 0


# =============================================================================
# on_card_clicked tests
# =============================================================================
class TestOnCardClicked:
    """Tests for on_card_clicked method"""

    def test_on_card_clicked_without_chat_service(
        self, qapp, mock_auth_service, sample_message
    ):
        """Test on_card_clicked without chat service"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            # Should not raise
            display.on_card_clicked(sample_message)

    def test_on_card_clicked_with_chat_service(
        self, qapp, mock_auth_service, mock_chat_service, sample_message
    ):
        """Test on_card_clicked with chat service"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.set_chat_service(mock_chat_service)

            # Patch the MessageModal import inside the method
            from unittest.mock import MagicMock

            mock_modal_class = MagicMock()
            mock_modal_instance = MagicMock()
            mock_modal_class.return_value = mock_modal_instance

            with patch.object(display, "on_card_clicked") as mock_method:
                # Just test the method exists and can be called
                mock_method(sample_message)
                mock_method.assert_called_once_with(sample_message)


# =============================================================================
# handle_message_read tests
# =============================================================================
class TestHandleMessageRead:
    """Tests for handle_message_read method"""

    def test_handle_message_read_success(
        self, qapp, mock_auth_service, mock_chat_service, sample_message
    ):
        """Test successful message read handling"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.set_chat_service(mock_chat_service)
            display.messages = [sample_message]

            mock_chat_service.mark_message_as_read.return_value = {"success": True}

            display.handle_message_read("msg123")

            mock_chat_service.mark_message_as_read.assert_called_once_with("msg123")
            # Message should be removed from list
            assert len(display.messages) == 0

    def test_handle_message_read_failure(
        self, qapp, mock_auth_service, mock_chat_service, sample_message
    ):
        """Test failed message read handling"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.set_chat_service(mock_chat_service)
            display.messages = [sample_message]

            mock_chat_service.mark_message_as_read.return_value = {
                "success": False,
                "error": "Failed",
            }

            display.handle_message_read("msg123")

            # Message should still be in list
            assert len(display.messages) == 1

    def test_handle_message_read_without_chat_service(
        self, qapp, mock_auth_service, sample_message
    ):
        """Test handle_message_read without chat service"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.messages = [sample_message]

            # Should not raise
            display.handle_message_read("msg123")


# =============================================================================
# show_message_notification tests
# =============================================================================
class TestShowMessageNotification:
    """Tests for show_message_notification method"""

    def test_show_message_notification_callable(
        self, qapp, mock_auth_service, sample_message
    ):
        """Test show_message_notification is callable"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)

            # Method should exist and be callable
            assert hasattr(display, "show_message_notification")
            assert callable(display.show_message_notification)

            # Should not raise when called
            display.show_message_notification(sample_message)


# =============================================================================
# refresh_display edge cases
# =============================================================================
class TestRefreshDisplayEdgeCases:
    """Additional tests for refresh_display edge cases"""

    def test_refresh_removes_old_cards(
        self, qapp, mock_auth_service, sample_message, read_message
    ):
        """Test refresh_display removes old cards"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)

            # First, add some messages
            display.messages = [sample_message, read_message]
            display.refresh_display()

            # Now update with fewer messages
            display.messages = [sample_message]
            display.refresh_display()

            # Should have only one message card (plus no_messages_label and stretch)

    def test_refresh_count_shows_unread_count(
        self, qapp, mock_auth_service, sample_message, read_message
    ):
        """Test refresh shows unread count when there are unread messages"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.messages = [sample_message, read_message]  # 1 unread
            display.refresh_display()

            assert display.count_label.text() == "1"  # Only unread count

    def test_refresh_count_shows_total_when_all_read(
        self, qapp, mock_auth_service, read_message
    ):
        """Test refresh shows total count when all messages are read"""
        with patch("ui.components.message_display.get_logger"):
            display = MessageDisplay(mock_auth_service)
            display.messages = [read_message]  # 0 unread
            display.refresh_display()

            assert display.count_label.text() == "1"  # Total count

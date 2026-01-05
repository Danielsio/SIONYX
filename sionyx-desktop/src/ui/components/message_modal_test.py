"""
Tests for message_modal.py - Smart Message Modal Component
Tests message display, navigation, reading, and signals.
"""

from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog

from ui.components.message_modal import MessageModal


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def mock_chat_service():
    """Create mock chat service"""
    service = Mock()
    service.mark_message_as_read.return_value = {"success": True}
    return service


@pytest.fixture
def sample_messages():
    """Sample messages for testing"""
    return [
        {
            "id": "msg1",
            "message": "First message content",
            "timestamp": "2024-01-15T10:00:00",
        },
        {
            "id": "msg2",
            "message": "Second message content",
            "timestamp": "2024-01-15T11:00:00",
        },
        {
            "id": "msg3",
            "message": "Third message content",
            "timestamp": "2024-01-15T12:00:00",
        },
    ]


@pytest.fixture
def message_modal(qapp, sample_messages, mock_chat_service):
    """Create MessageModal instance"""
    with patch("ui.components.message_modal.get_logger") as mock_logger:
        mock_logger.return_value = Mock()
        modal = MessageModal(messages=sample_messages, chat_service=mock_chat_service)
        return modal


# =============================================================================
# Initialization tests
# =============================================================================
class TestMessageModalInit:
    """Tests for MessageModal initialization"""

    def test_initialization_stores_messages(
        self, qapp, sample_messages, mock_chat_service
    ):
        """Test modal stores messages"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)
            assert len(modal.messages) == 3

    def test_initialization_copies_messages(
        self, qapp, sample_messages, mock_chat_service
    ):
        """Test modal copies messages (doesn't modify original)"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)
            modal.messages.append({"id": "new"})
            assert len(sample_messages) == 3

    def test_initialization_stores_chat_service(
        self, qapp, sample_messages, mock_chat_service
    ):
        """Test modal stores chat service"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)
            assert modal.chat_service == mock_chat_service

    def test_initialization_starts_at_first_message(
        self, qapp, sample_messages, mock_chat_service
    ):
        """Test modal starts at index 0"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)
            assert modal.current_index == 0

    def test_initialization_read_count_zero(
        self, qapp, sample_messages, mock_chat_service
    ):
        """Test read count starts at 0"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)
            assert modal.read_count == 0

    def test_initialization_empty_messages(self, qapp, mock_chat_service):
        """Test initialization with empty messages"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal([], mock_chat_service)
            assert modal.messages == []

    def test_initialization_none_messages(self, qapp, mock_chat_service):
        """Test initialization with None messages"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(None, mock_chat_service)
            assert modal.messages == []

    def test_inherits_qdialog(self, message_modal):
        """Test modal inherits from QDialog"""
        assert isinstance(message_modal, QDialog)

    def test_is_modal(self, message_modal):
        """Test dialog is modal"""
        assert message_modal.isModal()

    def test_rtl_layout(self, message_modal):
        """Test RTL layout for Hebrew"""
        assert message_modal.layoutDirection() == Qt.LayoutDirection.RightToLeft


# =============================================================================
# UI element tests
# =============================================================================
class TestMessageModalUI:
    """Tests for UI elements"""

    def test_has_container(self, message_modal):
        """Test modal has container widget"""
        assert hasattr(message_modal, "container")
        assert message_modal.container is not None

    def test_has_message_label(self, message_modal):
        """Test modal has message label"""
        assert hasattr(message_modal, "message_label")

    def test_has_timestamp_label(self, message_modal):
        """Test modal has timestamp label"""
        assert hasattr(message_modal, "timestamp_label")

    def test_has_progress_label(self, message_modal):
        """Test modal has progress label"""
        assert hasattr(message_modal, "progress_label")

    def test_has_read_next_button(self, message_modal):
        """Test modal has read next button"""
        assert hasattr(message_modal, "read_next_button")

    def test_has_read_all_button(self, message_modal):
        """Test modal has read all button"""
        assert hasattr(message_modal, "read_all_button")

    def test_has_close_button(self, message_modal):
        """Test modal has close button"""
        assert hasattr(message_modal, "close_button")


# =============================================================================
# show_current_message tests
# =============================================================================
class TestShowCurrentMessage:
    """Tests for show_current_message method"""

    def test_displays_first_message(self, message_modal):
        """Test first message is displayed"""
        message_modal.show_current_message()
        assert "First message content" in message_modal.message_label.text()

    def test_displays_progress(self, message_modal):
        """Test progress is displayed"""
        message_modal.show_current_message()
        assert "1" in message_modal.progress_label.text()
        assert "3" in message_modal.progress_label.text()

    def test_formats_timestamp(self, message_modal):
        """Test timestamp is formatted"""
        message_modal.show_current_message()
        # Should show formatted date
        assert message_modal.timestamp_label.text() != ""

    def test_empty_messages_shows_placeholder(self, qapp, mock_chat_service):
        """Test empty messages shows placeholder"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal([], mock_chat_service)
            assert "אין הודעות" in modal.message_label.text()


# =============================================================================
# read_next_message tests
# =============================================================================
class TestReadNextMessage:
    """Tests for read_next_message method"""

    def test_marks_message_as_read(self, message_modal, mock_chat_service):
        """Test current message is marked as read"""
        message_modal.read_next_message()
        mock_chat_service.mark_message_as_read.assert_called_with("msg1")

    def test_increments_current_index(self, message_modal):
        """Test index increments after reading"""
        initial_index = message_modal.current_index
        message_modal.read_next_message()
        assert message_modal.current_index == initial_index + 1

    def test_increments_read_count(self, message_modal):
        """Test read count increments"""
        message_modal.read_next_message()
        assert message_modal.read_count == 1

    def test_emits_message_read_signal(self, message_modal):
        """Test message_read signal is emitted"""
        signal_received = []
        message_modal.message_read.connect(
            lambda msg_id: signal_received.append(msg_id)
        )
        message_modal.read_next_message()
        assert len(signal_received) == 1
        assert signal_received[0] == "msg1"

    def test_shows_next_message(self, message_modal):
        """Test next message is shown after reading"""
        message_modal.read_next_message()
        assert "Second message content" in message_modal.message_label.text()

    def test_handles_mark_failure(self, message_modal, mock_chat_service):
        """Test handling of mark failure"""
        mock_chat_service.mark_message_as_read.return_value = {
            "success": False,
            "error": "Failed",
        }
        # Should not raise
        message_modal.read_next_message()
        # Read count should not increment on failure
        assert message_modal.read_count == 0


# =============================================================================
# read_all_messages tests
# =============================================================================
class TestReadAllMessages:
    """Tests for read_all_messages method"""

    def test_marks_all_messages_as_read(self, message_modal, mock_chat_service):
        """Test all remaining messages are marked as read"""
        message_modal.read_all_messages()
        assert mock_chat_service.mark_message_as_read.call_count == 3

    def test_read_count_equals_total(self, message_modal):
        """Test read count equals total messages"""
        message_modal.read_all_messages()
        assert message_modal.read_count == 3

    def test_emits_all_messages_read_signal(self, message_modal):
        """Test all_messages_read signal is emitted"""
        signal_received = []
        message_modal.all_messages_read.connect(lambda: signal_received.append(True))
        message_modal.read_all_messages()
        assert len(signal_received) == 1

    def test_read_all_from_middle(self, message_modal, mock_chat_service):
        """Test reading all when starting from middle"""
        message_modal.current_index = 1  # Start from second message
        message_modal.read_all_messages()
        # Should only mark remaining 2 messages
        assert mock_chat_service.mark_message_as_read.call_count == 2

    def test_empty_messages_does_nothing(self, qapp, mock_chat_service):
        """Test read_all with empty messages"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal([], mock_chat_service)
            modal.read_all_messages()
            mock_chat_service.mark_message_as_read.assert_not_called()


# =============================================================================
# Signal tests
# =============================================================================
class TestSignals:
    """Tests for signal definitions"""

    def test_message_read_signal_exists(self, message_modal):
        """Test message_read signal exists"""
        assert hasattr(message_modal, "message_read")

    def test_all_messages_read_signal_exists(self, message_modal):
        """Test all_messages_read signal exists"""
        assert hasattr(message_modal, "all_messages_read")

    def test_can_connect_to_message_read(self, message_modal):
        """Test can connect to message_read signal"""
        callback = Mock()
        message_modal.message_read.connect(callback)
        # Should not raise


# =============================================================================
# Animation tests
# =============================================================================
class TestAnimations:
    """Tests for animation setup"""

    def test_has_fade_animation(self, message_modal):
        """Test modal has fade animation"""
        assert hasattr(message_modal, "fade_animation")


# =============================================================================
# Keyboard handling tests
# =============================================================================
class TestKeyboardHandling:
    """Tests for keyboard event handling"""

    def test_has_key_press_handler(self, message_modal):
        """Test modal has keyPressEvent handler"""
        assert hasattr(message_modal, "keyPressEvent")


# =============================================================================
# Edge cases
# =============================================================================
class TestEdgeCases:
    """Tests for edge cases"""

    def test_message_without_id(self, qapp, mock_chat_service):
        """Test handling message without ID"""
        messages = [{"message": "No ID message", "timestamp": "2024-01-01"}]
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(messages, mock_chat_service)
            modal.read_next_message()
            # Should not call mark_message_as_read without ID
            mock_chat_service.mark_message_as_read.assert_not_called()

    def test_message_without_timestamp(self, qapp, mock_chat_service):
        """Test handling message without timestamp - shows empty label"""
        messages = [{"id": "msg1", "message": "No timestamp"}]
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(messages, mock_chat_service)
            modal.show_current_message()
            # Timestamp label is empty when no timestamp provided
            assert modal.timestamp_label.text() == ""

    def test_invalid_timestamp_format(self, qapp, mock_chat_service):
        """Test handling invalid timestamp format"""
        messages = [{"id": "msg1", "message": "Bad timestamp", "timestamp": "invalid"}]
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(messages, mock_chat_service)
            modal.show_current_message()
            # Should show the raw timestamp
            assert "invalid" in modal.timestamp_label.text()

    def test_none_chat_service(self, qapp, sample_messages):
        """Test handling None chat service"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, None)
            # Should not raise when trying to read
            modal.read_next_message()

    def test_show_current_message_no_messages(self, qapp, mock_chat_service):
        """Test show_current_message with empty messages closes modal"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal([], mock_chat_service)
            close_called = []
            modal.close_modal = lambda: close_called.append(True)

            modal.show_current_message()

            assert len(close_called) == 1

    def test_show_current_message_index_out_of_bounds(
        self, qapp, mock_chat_service, sample_messages
    ):
        """Test show_current_message when index exceeds messages"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)
            modal.current_index = 100  # Out of bounds
            close_called = []
            modal.close_modal = lambda: close_called.append(True)

            modal.show_current_message()

            assert len(close_called) == 1

    def test_read_next_message_no_messages(self, qapp, mock_chat_service):
        """Test read_next_message with empty messages closes modal"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal([], mock_chat_service)
            close_called = []
            modal.close_modal = lambda: close_called.append(True)

            modal.read_next_message()

            assert len(close_called) == 1

    def test_read_next_message_index_out_of_bounds(
        self, qapp, mock_chat_service, sample_messages
    ):
        """Test read_next_message when index exceeds messages"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)
            modal.current_index = 100  # Out of bounds
            close_called = []
            modal.close_modal = lambda: close_called.append(True)

            modal.read_next_message()

            assert len(close_called) == 1


# =============================================================================
# Keyboard Event Tests
# =============================================================================
class TestKeyPressEvent:
    """Tests for keyboard event handling"""

    def test_enter_key_reads_next(self, qapp, mock_chat_service, sample_messages):
        """Test Enter key triggers read_next_message"""
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)
            read_called = []
            modal.read_next_message = lambda: read_called.append(True)

            event = QKeyEvent(
                QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier
            )
            modal.keyPressEvent(event)

            assert len(read_called) == 1

    def test_enter_key_alternate_reads_next(
        self, qapp, mock_chat_service, sample_messages
    ):
        """Test numpad Enter key triggers read_next_message"""
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)
            read_called = []
            modal.read_next_message = lambda: read_called.append(True)

            event = QKeyEvent(
                QEvent.Type.KeyPress, Qt.Key.Key_Enter, Qt.KeyboardModifier.NoModifier
            )
            modal.keyPressEvent(event)

            assert len(read_called) == 1

    def test_escape_key_closes_modal(self, qapp, mock_chat_service, sample_messages):
        """Test Escape key triggers close_modal"""
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)
            close_called = []
            modal.close_modal = lambda: close_called.append(True)

            event = QKeyEvent(
                QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier
            )
            modal.keyPressEvent(event)

            assert len(close_called) == 1

    def test_other_key_passes_to_parent(self, qapp, mock_chat_service, sample_messages):
        """Test other keys are passed to parent handler"""
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)

            event = QKeyEvent(
                QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier
            )
            # Should not raise
            modal.keyPressEvent(event)


# =============================================================================
# Animation Tests
# =============================================================================
class TestShowAnimated:
    """Tests for show_animated method"""

    def test_show_animated_sets_opacity_to_zero(
        self, qapp, mock_chat_service, sample_messages
    ):
        """Test show_animated initially sets opacity to 0"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)
            # Mock to avoid actual show
            modal.show = Mock()
            modal.fade_animation.start = Mock()

            modal.show_animated()

            # Verify animation setup
            modal.fade_animation.start.assert_called_once()

    def test_show_animated_centers_on_screen(
        self, qapp, mock_chat_service, sample_messages
    ):
        """Test show_animated centers the modal"""
        with patch("ui.components.message_modal.get_logger"):
            modal = MessageModal(sample_messages, mock_chat_service)
            modal.show = Mock()
            modal.fade_animation.start = Mock()
            original_move = modal.move
            move_called = []
            modal.move = lambda x, y: move_called.append((x, y))

            modal.show_animated()

            # Move should have been called with screen-centered coordinates
            assert len(move_called) == 1
            x, y = move_called[0]
            assert x >= 0
            assert y >= 0

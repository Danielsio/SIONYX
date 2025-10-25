"""
Message Display Component
Shows admin messages to users on the home page
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from utils.logger import get_logger


logger = get_logger(__name__)


class MessageCard(QFrame):
    """Individual message card component with modern design"""

    # Signal emitted when card is clicked
    card_clicked = pyqtSignal(dict)

    def __init__(self, message_data, parent=None):
        super().__init__(parent)
        self.message_data = message_data
        self.is_read = message_data.get("isRead", False)
        self.init_ui()
        self.setup_animations()

    def init_ui(self):
        """Initialize modern message card UI"""
        self.setObjectName("messageCard")
        self.setFixedHeight(140)  # Increased height for better content display
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Enhanced modern card styling with better shadows and hover effects
        self.setStyleSheet(
            f"""
            QFrame#messageCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFFFF, stop:1 #F8FAFC);
                border: 2px solid {'#10B981' if self.is_read else '#E2E8F0'};
                border-radius: 20px;
                margin: 12px 8px;
            }}
            QFrame#messageCard:hover {{
                border: 2px solid #3B82F6;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F0F9FF, stop:1 #E0F2FE);
                transform: translateY(-2px);
            }}
            QFrame#messageCard:pressed {{
                transform: translateY(0px);
                border: 2px solid #1E40AF;
            }}
        """
        )

        # Add professional shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Header with status indicator and timestamp
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # Status indicator (read/unread)
        status_indicator = QLabel("✓" if self.is_read else "●")
        status_indicator.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        status_indicator.setStyleSheet(
            f"""
            color: {'#10B981' if self.is_read else '#3B82F6'};
            background: transparent;
        """
        )

        # Message icon with better styling
        icon_label = QLabel("💬")
        icon_label.setFont(QFont("Segoe UI", 18))
        icon_label.setStyleSheet("color: #3B82F6;")

        # Timestamp with improved formatting
        timestamp = self.message_data.get("timestamp", "")
        if timestamp:
            from datetime import datetime

            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                time_str = timestamp
        else:
            time_str = "Unknown time"

        timestamp_label = QLabel(time_str)
        timestamp_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        timestamp_label.setStyleSheet(
            """
            color: #64748B;
            background: transparent;
            border: none;
        """
        )

        header_layout.addWidget(status_indicator)
        header_layout.addWidget(icon_label)
        header_layout.addStretch()
        header_layout.addWidget(timestamp_label)

        # Message content with improved typography and better spacing
        message_text = self.message_data.get("message", "No message")
        message_label = QLabel(message_text)
        message_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        message_label.setStyleSheet(
            """
            color: #1E293B;
            background: transparent;
            border: none;
            line-height: 1.6;
            font-weight: 500;
        """
        )
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        message_label.setMaximumHeight(60)  # Limit height for consistent card sizing

        # Read status label with modern styling
        read_status = QLabel("נקרא" if self.is_read else "לא נקרא")
        read_status.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        read_status.setStyleSheet(
            f"""
            color: {'#10B981' if self.is_read else '#F59E0B'};
            background: {'#F0FDF4' if self.is_read else '#FFFBEB'};
            border: 1px solid {'#BBF7D0' if self.is_read else '#FDE68A'};
            border-radius: 12px;
            padding: 4px 12px;
            font-weight: 600;
        """
        )
        read_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        read_status.setFixedHeight(24)

        # Add to main layout
        layout.addLayout(header_layout)
        layout.addWidget(message_label)
        layout.addWidget(read_status)

    def setup_animations(self):
        """Setup hover animations for better UX"""
        # Enhanced shadow on hover
        self.original_shadow = self.graphicsEffect()

    def enterEvent(self, event):
        """Enhanced hover effect"""
        super().enterEvent(event)
        if self.original_shadow:
            # Increase shadow on hover
            enhanced_shadow = QGraphicsDropShadowEffect()
            enhanced_shadow.setBlurRadius(35)
            enhanced_shadow.setXOffset(0)
            enhanced_shadow.setYOffset(12)
            enhanced_shadow.setColor(QColor(0, 0, 0, 60))
            self.setGraphicsEffect(enhanced_shadow)

    def leaveEvent(self, event):
        """Restore original shadow"""
        super().leaveEvent(event)
        if self.original_shadow:
            self.setGraphicsEffect(self.original_shadow)

    def mousePressEvent(self, event):
        """Handle card click to open modal"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.card_clicked.emit(self.message_data)
        super().mousePressEvent(event)


class MessageDisplay(QWidget):
    """Main message display component"""

    message_read = pyqtSignal(str)  # Signal emitted when message is marked as read

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_user = auth_service.get_current_user()
        self.messages = []
        self.chat_service = None

        self.init_ui()

    def init_ui(self):
        """Initialize message display UI"""
        self.setObjectName("messageDisplay")

        # Set RTL layout direction for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Modern container styling
        self.setStyleSheet(
            """
            QWidget#messageDisplay {
                background: transparent;
                border: none;
            }
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Modern header with enhanced styling
        header_frame = QFrame()
        header_frame.setObjectName("messageHeader")
        header_frame.setFixedHeight(70)
        header_frame.setStyleSheet(
            """
            QFrame#messageHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3B82F6, stop:1 #1E40AF);
                border-radius: 16px 16px 0 0;
                border: none;
            }
        """
        )

        # Add subtle shadow to header
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(15)
        header_shadow.setXOffset(0)
        header_shadow.setYOffset(4)
        header_shadow.setColor(QColor(0, 0, 0, 30))
        header_frame.setGraphicsEffect(header_shadow)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(25, 15, 25, 15)
        header_layout.setSpacing(15)

        # Title with enhanced styling
        title_label = QLabel("💬 הודעות מהמנהל")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet(
            """
            QLabel {
                color: white;
                background: transparent;
                border: none;
                font-weight: 800;
            }
        """
        )

        # Modern message count badge
        self.count_label = QLabel("0")
        self.count_label.setObjectName("messageCount")
        self.count_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.count_label.setStyleSheet(
            """
            QLabel#messageCount {
                color: #1E40AF;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFFFF, stop:1 #F8FAFC);
                border-radius: 16px;
                padding: 6px 16px;
                font-weight: 800;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """
        )
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setFixedSize(50, 32)
        self.count_label.hide()  # Hide initially

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.count_label)

        # Modern messages container
        self.messages_container = QFrame()
        self.messages_container.setObjectName("messagesContainer")
        self.messages_container.setStyleSheet(
            """
            QFrame#messagesContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFFFF, stop:1 #F8FAFC);
                border: 2px solid #E2E8F0;
                border-top: none;
                border-radius: 0 0 16px 16px;
            }
        """
        )

        # Add subtle shadow to container
        container_shadow = QGraphicsDropShadowEffect()
        container_shadow.setBlurRadius(20)
        container_shadow.setXOffset(0)
        container_shadow.setYOffset(8)
        container_shadow.setColor(QColor(0, 0, 0, 25))
        self.messages_container.setGraphicsEffect(container_shadow)

        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                border-radius: 5px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #CBD5E1, stop:1 #94A3B8);
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #94A3B8, stop:1 #64748B);
            }
            QScrollBar::handle:vertical:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #64748B, stop:1 #475569);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """
        )

        # Messages widget
        self.messages_widget = QWidget()
        self.messages_widget.setObjectName("messagesWidget")
        self.messages_widget.setStyleSheet(
            """
            QWidget#messagesWidget {
                background: transparent;
                border: none;
            }
        """
        )

        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(8, 8, 8, 8)
        self.messages_layout.setSpacing(0)

        # Modern no messages label
        self.no_messages_label = QLabel("📭 אין הודעות חדשות")
        self.no_messages_label.setObjectName("noMessages")
        self.no_messages_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        self.no_messages_label.setStyleSheet(
            """
            QLabel#noMessages {
                color: #94A3B8;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F8FAFC, stop:1 #F1F5F9);
                border: 2px dashed #E2E8F0;
                border-radius: 16px;
                padding: 40px 20px;
                font-weight: 500;
            }
        """
        )
        self.no_messages_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_messages_label.hide()

        self.messages_layout.addWidget(self.no_messages_label)
        self.messages_layout.addStretch()

        self.scroll_area.setWidget(self.messages_widget)

        # Add to main layout
        layout.addWidget(header_frame)
        layout.addWidget(self.messages_container)

        messages_layout = QVBoxLayout(self.messages_container)
        messages_layout.setContentsMargins(0, 0, 0, 0)
        messages_layout.addWidget(self.scroll_area)

        # Connect signals
        self.message_read.connect(self.handle_message_read)

    def set_chat_service(self, chat_service):
        """Set the chat service for message handling"""
        self.chat_service = chat_service

    def update_messages(self, messages):
        """Update the displayed messages"""
        self.messages = messages
        self.refresh_display()

    def refresh_display(self):
        """Refresh the message display with modern styling"""
        # Clear existing message cards
        for i in reversed(range(self.messages_layout.count())):
            child = self.messages_layout.itemAt(i).widget()
            if child and child.objectName() != "noMessages":
                child.setParent(None)

        if not self.messages:
            self.no_messages_label.show()
            self.count_label.hide()
        else:
            self.no_messages_label.hide()

            # Show message count with modern badge styling
            unread_count = sum(
                1 for msg in self.messages if not msg.get("isRead", False)
            )
            self.count_label.setText(
                str(unread_count) if unread_count > 0 else str(len(self.messages))
            )
            self.count_label.show()

            # Add message cards with click handling
            for message in self.messages:
                card = MessageCard(message, self)
                card.card_clicked.connect(self.on_card_clicked)
                self.messages_layout.insertWidget(0, card)  # Insert at top

    def on_card_clicked(self, message_data):
        """Handle message card click - open modal for reading"""
        # Import here to avoid circular imports
        try:
            from ui.components.message_modal import MessageModal

            if self.chat_service:
                modal = MessageModal([message_data], self.chat_service, self)
                modal.message_read.connect(self.message_read.emit)
                modal.show_animated()
        except ImportError:
            logger.warning("MessageModal not available, falling back to simple read")
            # Fallback: just mark as read
            message_id = message_data.get("id")
            if message_id and self.chat_service:
                result = self.chat_service.mark_message_as_read(message_id)
                if result.get("success"):
                    self.message_read.emit(message_id)

    def handle_message_read(self, message_id):
        """Handle message read signal"""
        if self.chat_service:
            result = self.chat_service.mark_message_as_read(message_id)
            if result.get("success"):
                logger.info(f"Message {message_id} marked as read")
                # Remove the message from display
                self.messages = [
                    msg for msg in self.messages if msg.get("id") != message_id
                ]
                self.refresh_display()
            else:
                logger.error(f"Failed to mark message as read: {result.get('error')}")

    def show_message_notification(self, message):
        """Show a notification for a new message"""
        # This could be enhanced with a toast notification
        logger.info(f"New message received: {message.get('message', '')}")

    def cleanup(self):
        """Cleanup resources"""
        if self.chat_service:
            self.chat_service.stop_listening()

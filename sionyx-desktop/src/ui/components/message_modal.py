"""
Smart Message Modal Component
Beautiful, modern message display with elegant animations
"""

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from utils.logger import get_logger


logger = get_logger(__name__)


class MessageModal(QDialog):
    """
    Beautiful modal for displaying admin messages
    Modern design with smooth animations and excellent UX
    """

    # Signals
    message_read = pyqtSignal(str)
    all_messages_read = pyqtSignal()

    def __init__(self, messages, chat_service, parent=None):
        super().__init__(parent)
        self.messages = messages.copy() if messages else []
        self.chat_service = chat_service
        self.current_index = 0
        self.read_count = 0

        self.setup_ui()
        self.setup_animations()

    def setup_ui(self):
        """Setup beautiful modal UI"""
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Main container - spacious for content
        self.container = QFrame()
        self.container.setObjectName("messageModalContainer")
        self.container.setFixedSize(580, 480)

        # Soft shadow for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setXOffset(0)
        shadow.setYOffset(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)

        # Container layout
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Build sections
        self.setup_header(container_layout)
        self.setup_content(container_layout)
        self.setup_footer(container_layout)
        self.apply_styles()

        # Show first message
        if self.messages:
            self.show_current_message()
        else:
            self.message_label.setText("אין הודעות להצגה")
            self.timestamp_label.setText("")
            self.progress_label.setText("0 מתוך 0")

    def setup_header(self, layout):
        """Setup compact elegant header"""
        header = QFrame()
        header.setObjectName("messageHeader")
        header.setFixedHeight(64)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 0, 28, 0)
        header_layout.setSpacing(12)

        # Title with icon
        title = QLabel("✉️  הודעות מהמנהל")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")

        # Progress badge
        self.progress_label = QLabel("")
        self.progress_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.progress_label.setStyleSheet(
            """
            color: white;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            padding: 5px 12px;
        """
        )

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.progress_label)
        layout.addWidget(header)

    def setup_content(self, layout):
        """Setup clean, spacious content area with proper scrolling"""
        self.content_frame = QFrame()
        self.content_frame.setObjectName("messageContent")

        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(32, 24, 32, 16)
        content_layout.setSpacing(12)

        # Scrollable message area - THIS IS THE KEY
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet(
            """
            QScrollArea { 
                background: #F8FAFC; 
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
            QScrollArea > QWidget > QWidget {
                background: #F8FAFC;
            }
            QScrollBar:vertical {
                background: #F1F5F9;
                width: 10px;
                margin: 4px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #94A3B8;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #64748B; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """
        )

        # Message container - needs proper size policy
        msg_widget = QWidget()
        msg_widget.setObjectName("msgWidget")
        msg_layout = QVBoxLayout(msg_widget)
        msg_layout.setContentsMargins(20, 16, 20, 16)
        msg_layout.setSpacing(0)

        # Message text - CRITICAL: use QLabel with proper settings
        self.message_label = QLabel()
        self.message_label.setObjectName("messageText")
        self.message_label.setFont(QFont("Segoe UI", 15))
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        # IMPORTANT: Let label grow vertically as needed
        self.message_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        )
        self.message_label.setMinimumHeight(50)
        self.message_label.setStyleSheet(
            """
            QLabel {
                color: #1E293B;
                background: transparent;
                padding: 0;
            }
        """
        )

        msg_layout.addWidget(self.message_label)
        msg_layout.addStretch()
        
        self.scroll_area.setWidget(msg_widget)

        # Timestamp - subtle pill at bottom
        timestamp_row = QHBoxLayout()
        timestamp_row.setContentsMargins(0, 0, 0, 0)
        
        self.timestamp_label = QLabel()
        self.timestamp_label.setFont(QFont("Segoe UI", 11))
        self.timestamp_label.setStyleSheet(
            """
            color: #64748B;
            background: #F1F5F9;
            border-radius: 8px;
            padding: 6px 14px;
        """
        )
        timestamp_row.addWidget(self.timestamp_label)
        timestamp_row.addStretch()

        content_layout.addWidget(self.scroll_area, 1)
        content_layout.addLayout(timestamp_row)
        layout.addWidget(self.content_frame, 1)

    def setup_footer(self, layout):
        """Setup compact footer with clean buttons"""
        footer = QFrame()
        footer.setObjectName("messageFooter")
        footer.setFixedHeight(72)

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(28, 14, 28, 14)
        footer_layout.setSpacing(10)

        # Read All button (success) - on the right for RTL
        self.read_all_button = QPushButton("✓ קרא הכל")
        self.read_all_button.setObjectName("readAllButton")
        self.read_all_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.read_all_button.setFixedHeight(44)
        self.read_all_button.setMinimumWidth(110)
        self.read_all_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.read_all_button.clicked.connect(self.read_all_messages)

        # Read Next / Finish button (primary)
        self.read_next_button = QPushButton("הבא →")
        self.read_next_button.setObjectName("readNextButton")
        self.read_next_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.read_next_button.setFixedHeight(44)
        self.read_next_button.setMinimumWidth(100)
        self.read_next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.read_next_button.clicked.connect(self.read_next_message)

        # Close button (secondary) - on the left for RTL
        self.close_button = QPushButton("סגור")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.close_button.setFixedHeight(44)
        self.close_button.setMinimumWidth(90)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.clicked.connect(self.close_modal)

        footer_layout.addWidget(self.read_all_button)
        footer_layout.addWidget(self.read_next_button)
        footer_layout.addStretch()
        footer_layout.addWidget(self.close_button)
        layout.addWidget(footer)

    def apply_styles(self):
        """Apply clean, modern styling"""
        self.container.setStyleSheet(
            """
            QFrame#messageModalContainer {
                background: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #E2E8F0;
            }

            QFrame#messageHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3B82F6, stop:1 #1D4ED8);
                border-radius: 20px 20px 0 0;
                border-bottom: none;
            }

            QFrame#messageContent {
                background: #FFFFFF;
                border: none;
            }

            QFrame#messageFooter {
                background: #F9FAFB;
                border-top: 1px solid #E5E7EB;
                border-radius: 0 0 20px 20px;
            }

            QPushButton#readAllButton {
                background: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
            }
            QPushButton#readAllButton:hover {
                background: #059669;
            }
            QPushButton#readAllButton:pressed {
                background: #047857;
            }

            QPushButton#readNextButton {
                background: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
            }
            QPushButton#readNextButton:hover {
                background: #2563EB;
            }
            QPushButton#readNextButton:pressed {
                background: #1D4ED8;
            }

            QPushButton#closeButton {
                background: #F3F4F6;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                padding: 0 16px;
            }
            QPushButton#closeButton:hover {
                background: #E5E7EB;
                border-color: #9CA3AF;
            }
            QPushButton#closeButton:pressed {
                background: #D1D5DB;
            }
        """
        )

    def setup_animations(self):
        """Setup smooth fade animation"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(250)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def show_current_message(self):
        """Display the current message"""
        if not self.messages or self.current_index >= len(self.messages):
            self.close_modal()
            return

        message = self.messages[self.current_index]

        # Update content
        self.message_label.setText(message.get("message", ""))

        # Format timestamp
        timestamp = message.get("timestamp", "")
        if timestamp:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%d/%m/%Y  •  %H:%M")
            except Exception:
                time_str = timestamp
        else:
            time_str = ""

        self.timestamp_label.setText(time_str)

        # Update progress
        total = len(self.messages)
        current = self.current_index + 1
        self.progress_label.setText(f"{current} מתוך {total}")

        # Update button text based on position
        is_last = self.current_index >= len(self.messages) - 1
        self.read_next_button.setText("סיום ✓" if is_last else "הבא →")

        # Hide "Read All" if only one message or on last message
        self.read_all_button.setVisible(total > 1 and not is_last)

    def read_next_message(self):
        """Mark current message as read and show next"""
        if not self.messages or self.current_index >= len(self.messages):
            self.close_modal()
            return

        # Mark current message as read
        current_message = self.messages[self.current_index]
        message_id = current_message.get("id")

        if message_id and self.chat_service:
            result = self.chat_service.mark_message_as_read(message_id)
            if result.get("success"):
                self.message_read.emit(message_id)
                self.read_count += 1
                logger.info(f"Message {message_id} marked as read")
            else:
                logger.error(f"Failed to mark message as read: {result.get('error')}")

        # Move to next message
        self.current_index += 1

        if self.current_index >= len(self.messages):
            # All messages read
            self.all_messages_read.emit()
            self.close_modal()
        else:
            # Show next message
            self.show_current_message()

    def read_all_messages(self):
        """Mark all remaining messages as read"""
        if not self.messages:
            return

        # Mark all remaining messages as read
        for i in range(self.current_index, len(self.messages)):
            message = self.messages[i]
            message_id = message.get("id")

            if message_id and self.chat_service:
                result = self.chat_service.mark_message_as_read(message_id)
                if result.get("success"):
                    self.message_read.emit(message_id)
                    self.read_count += 1
                    logger.info(f"Message {message_id} marked as read")

        # Emit signal and close
        self.all_messages_read.emit()
        self.close_modal()

    def close_modal(self):
        """Close the modal with animation"""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()

    def show_animated(self):
        """Show the modal with enhanced entrance animation"""
        # Center the modal on screen - use screen geometry instead of parent
        from PyQt6.QtWidgets import QApplication

        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

        self.setWindowOpacity(0.0)
        self.show()

        # Simple fade in animation without scale
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.read_next_message()
        elif event.key() == Qt.Key.Key_Escape:
            self.close_modal()
        else:
            super().keyPressEvent(event)

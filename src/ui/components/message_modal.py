"""
Smart Message Modal Component
Professional UX-focused message display with one-by-one reading
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
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from utils.logger import get_logger


logger = get_logger(__name__)


class MessageModal(QDialog):
    """
    Smart modal for displaying messages one by one
    Professional UX with user control and flexibility
    """

    # Signals
    message_read = pyqtSignal(str)  # Emitted when a message is marked as read
    all_messages_read = pyqtSignal()  # Emitted when all messages are read

    def __init__(self, messages, chat_service, parent=None):
        super().__init__(parent)
        self.messages = messages.copy() if messages else []
        self.chat_service = chat_service
        self.current_index = 0
        self.read_count = 0

        self.setup_ui()
        self.setup_animations()

    def setup_ui(self):
        """Setup the modal UI with enhanced professional styling"""
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        # Set RTL for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Enhanced main container with better proportions
        self.container = QFrame()
        self.container.setObjectName("messageModalContainer")
        self.container.setFixedSize(700, 550)  # Much larger for better content display

        # Enhanced professional shadow with better depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.container.setGraphicsEffect(shadow)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)

        # Container layout
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header
        self.setup_header(container_layout)

        # Content area
        self.setup_content(container_layout)

        # Footer with controls
        self.setup_footer(container_layout)

        # Apply styling
        self.apply_styles()

        # Show first message
        if self.messages:
            self.show_current_message()
        else:
            # If no messages, show a placeholder
            self.message_label.setText("אין הודעות להצגה")
            self.timestamp_label.setText("")
            self.progress_label.setText("0 מתוך 0")

    def setup_header(self, layout):
        """Setup the enhanced modal header"""
        header_frame = QFrame()
        header_frame.setObjectName("messageHeader")
        header_frame.setFixedHeight(110)  # Increased height for better proportions

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(40, 30, 40, 30)  # More generous margins
        header_layout.setSpacing(25)

        # Enhanced message icon
        icon_label = QLabel("💬")
        icon_label.setFont(QFont("Segoe UI", 28))
        icon_label.setStyleSheet(
            """
            color: white;
            background: rgba(255, 255, 255, 0.15);
            border-radius: 25px;
            padding: 12px;
        """
        )
        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Enhanced title
        self.title_label = QLabel("הודעות מהמנהל")
        self.title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.title_label.setStyleSheet(
            """
            color: white;
            background: transparent;
            font-weight: 800;
        """
        )

        # Enhanced progress indicator with better styling
        self.progress_label = QLabel("")
        self.progress_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        self.progress_label.setStyleSheet(
            """
            color: rgba(255, 255, 255, 0.9);
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 8px 16px;
            font-weight: 600;
        """
        )

        header_layout.addWidget(icon_label)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.progress_label)
        layout.addWidget(header_frame)

    def setup_content(self, layout):
        """Setup the enhanced message content area"""
        self.content_frame = QFrame()
        self.content_frame.setObjectName("messageContent")

        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(60, 50, 60, 50)  # Much more generous margins
        content_layout.setSpacing(35)

        # Enhanced message content with better typography
        self.message_label = QLabel()
        self.message_label.setObjectName("messageText")
        self.message_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Medium))
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.message_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.message_label.setStyleSheet(
            """
            QLabel#messageText {
                color: #1E293B;
                background: transparent;
                border: none;
                line-height: 1.8;
                font-weight: 500;
                padding: 25px;
            }
        """
        )

        # Enhanced timestamp with better styling
        self.timestamp_label = QLabel()
        self.timestamp_label.setObjectName("messageTimestamp")
        self.timestamp_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        self.timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.timestamp_label.setStyleSheet(
            """
            QLabel#messageTimestamp {
                color: #64748B;
                background: #F1F5F9;
                border: 2px solid #E2E8F0;
                border-radius: 18px;
                padding: 15px 25px;
                font-weight: 600;
            }
        """
        )

        content_layout.addWidget(self.message_label)
        content_layout.addWidget(self.timestamp_label)
        content_layout.addStretch()

        layout.addWidget(self.content_frame)

    def setup_footer(self, layout):
        """Setup the enhanced footer with modern action buttons"""
        footer_frame = QFrame()
        footer_frame.setObjectName("messageFooter")
        footer_frame.setFixedHeight(120)  # Increased height for better proportions

        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(50, 30, 50, 30)  # More generous margins
        footer_layout.setSpacing(30)

        # Enhanced Read All button with modern styling
        self.read_all_button = QPushButton("📖 קרא הכל")
        self.read_all_button.setObjectName("readAllButton")
        self.read_all_button.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.read_all_button.setFixedSize(180, 60)  # Larger button with more space
        self.read_all_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.read_all_button.clicked.connect(self.read_all_messages)

        # Spacer
        spacer = QSpacerItem(
            50, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        # Enhanced Read Next button
        self.read_next_button = QPushButton("➡️ קרא הבא")
        self.read_next_button.setObjectName("readNextButton")
        self.read_next_button.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.read_next_button.setFixedSize(180, 60)  # Larger button with more space
        self.read_next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.read_next_button.clicked.connect(self.read_next_message)

        # Enhanced Close button
        self.close_button = QPushButton("❌ סגור")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.close_button.setFixedSize(150, 60)  # Larger button with more space
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.clicked.connect(self.close_modal)

        footer_layout.addWidget(self.read_all_button)
        footer_layout.addItem(spacer)
        footer_layout.addWidget(self.read_next_button)
        footer_layout.addWidget(self.close_button)

        layout.addWidget(footer_frame)

    def apply_styles(self):
        """Apply professional styling"""
        self.container.setStyleSheet(
            """
            QFrame#messageModalContainer {
                background: #FFFFFF;
                border-radius: 28px;
                border: 2px solid #E2E8F0;
            }
            
            QFrame#messageHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3B82F6, stop:1 #2563EB);
                border-radius: 28px 28px 0 0;
            }
            
            QFrame#messageContent {
                background: #FFFFFF;
                border: none;
            }
            
            QFrame#messageFooter {
                background: #F8FAFC;
                border-top: 2px solid #E2E8F0;
                border-radius: 0 0 28px 28px;
            }
            
            QLabel#messageText {
                color: #1E293B;
                background: transparent;
                border: none;
                line-height: 1.6;
            }
            
            QLabel#messageTimestamp {
                color: #64748B;
                background: transparent;
                border: none;
            }
            
            QPushButton#readAllButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #10B981, stop:1 #059669);
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: 800;
                font-size: 15px;
                padding: 12px 24px;
            }
            QPushButton#readAllButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #059669, stop:1 #047857);
            }
            QPushButton#readAllButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #047857, stop:1 #065F46);
            }
            
            QPushButton#readNextButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3B82F6, stop:1 #2563EB);
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: 800;
                font-size: 15px;
                padding: 12px 24px;
            }
            QPushButton#readNextButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2563EB, stop:1 #1E40AF);
            }
            QPushButton#readNextButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1E40AF, stop:1 #1E3A8A);
            }
            
            QPushButton#closeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6B7280, stop:1 #4B5563);
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: 800;
                font-size: 15px;
                padding: 12px 24px;
            }
            QPushButton#closeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4B5563, stop:1 #374151);
            }
            QPushButton#closeButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #374151, stop:1 #1F2937);
            }
        """
        )

    def setup_animations(self):
        """Setup enhanced smooth animations"""
        # Enhanced fade in animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(400)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Content slide animation with better easing
        self.slide_animation = QPropertyAnimation(self.content_frame, b"geometry")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutBack)

        # Scale animation for modal entrance
        self.scale_animation = QPropertyAnimation(self.container, b"geometry")
        self.scale_animation.setDuration(350)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutBack)

    def show_current_message(self):
        """Display the current message"""
        if not self.messages or self.current_index >= len(self.messages):
            self.close_modal()
            return

        message = self.messages[self.current_index]

        # Update content
        self.message_label.setText(message.get("message", "No message"))

        # Format timestamp
        timestamp = message.get("timestamp", "")
        if timestamp:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%d/%m/%Y %H:%M")
            except:
                time_str = timestamp
        else:
            time_str = "Unknown time"

        self.timestamp_label.setText(time_str)

        # Update progress
        total = len(self.messages)
        current = self.current_index + 1
        self.progress_label.setText(f"{current} מתוך {total}")

        # Update button states
        self.read_next_button.setText(
            "קרא הבא" if self.current_index < len(self.messages) - 1 else "סיום"
        )

        # Animate content change
        self.animate_content_change()

    def animate_content_change(self):
        """Animate the content change with slide effect"""
        # Simple fade effect for now
        self.content_frame.setStyleSheet(
            self.content_frame.styleSheet()
            + """
            QFrame#messageContent {
                background: #FFFFFF;
                border: none;
            }
        """
        )

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

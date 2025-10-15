"""
Message Display Component
Shows admin messages to users on the home page
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap, QPainter, QBrush
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect

from utils.logger import get_logger

logger = get_logger(__name__)


class MessageCard(QFrame):
    """Individual message card component"""
    
    def __init__(self, message_data, parent=None):
        super().__init__(parent)
        self.message_data = message_data
        self.init_ui()
        
    def init_ui(self):
        """Initialize message card UI"""
        self.setObjectName("messageCard")
        self.setFixedHeight(120)
        
        # Modern card styling
        self.setStyleSheet("""
            QFrame#messageCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFFFF, stop:1 #F8FAFC);
                border: 2px solid #E2E8F0;
                border-radius: 16px;
                margin: 8px;
            }
            QFrame#messageCard:hover {
                border: 2px solid #3B82F6;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F0F9FF, stop:1 #E0F2FE);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Header with icon and timestamp
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Message icon
        icon_label = QLabel("💬")
        icon_label.setFont(QFont("Segoe UI", 16))
        icon_label.setStyleSheet("color: #3B82F6;")
        
        # Timestamp
        timestamp = self.message_data.get('timestamp', '')
        if timestamp:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%d/%m/%Y %H:%M')
            except:
                time_str = timestamp
        else:
            time_str = "Unknown time"
            
        timestamp_label = QLabel(time_str)
        timestamp_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        timestamp_label.setStyleSheet("color: #64748B;")
        
        header_layout.addWidget(icon_label)
        header_layout.addStretch()
        header_layout.addWidget(timestamp_label)
        
        # Message content
        message_text = self.message_data.get('message', 'No message')
        message_label = QLabel(message_text)
        message_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        message_label.setStyleSheet("""
            QLabel {
                color: #1E293B;
                background: transparent;
                border: none;
            }
        """)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Mark as read button
        read_button = QPushButton("✓ קרא")
        read_button.setObjectName("readButton")
        read_button.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        read_button.setFixedSize(80, 32)
        read_button.setStyleSheet("""
            QPushButton#readButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #10B981, stop:1 #059669);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 700;
            }
            QPushButton#readButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #059669, stop:1 #047857);
            }
            QPushButton#readButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #047857, stop:1 #065F46);
            }
        """)
        read_button.clicked.connect(self.mark_as_read)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()
        button_layout.addWidget(read_button)
        
        layout.addLayout(header_layout)
        layout.addWidget(message_label)
        layout.addLayout(button_layout)
        
    def mark_as_read(self):
        """Emit signal to mark message as read"""
        # Find the MessageDisplay parent and emit the signal
        parent = self.parent()
        while parent and not hasattr(parent, 'message_read'):
            parent = parent.parent()
        
        if parent and hasattr(parent, 'message_read'):
            parent.message_read.emit(self.message_data.get('id'))
        else:
            # Fallback: try to find the message display in the widget hierarchy
            message_display = self.find_message_display()
            if message_display:
                message_display.message_read.emit(self.message_data.get('id'))
    
    def find_message_display(self):
        """Find the MessageDisplay widget in the hierarchy"""
        widget = self.parent()
        while widget:
            if hasattr(widget, 'message_read'):
                return widget
            widget = widget.parent()
        return None


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
        self.setStyleSheet("""
            QWidget#messageDisplay {
                background: transparent;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header_frame = QFrame()
        header_frame.setObjectName("messageHeader")
        header_frame.setFixedHeight(60)
        header_frame.setStyleSheet("""
            QFrame#messageHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3B82F6, stop:1 #1E40AF);
                border-radius: 12px 12px 0 0;
                border: none;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 12, 20, 12)
        
        # Title
        title_label = QLabel("💬 הודעות מהמנהל")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
        """)
        
        # Message count badge
        self.count_label = QLabel("0")
        self.count_label.setObjectName("messageCount")
        self.count_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.count_label.setFixedSize(24, 24)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet("""
            QLabel#messageCount {
                background: #EF4444;
                color: white;
                border-radius: 12px;
                border: 2px solid white;
            }
        """)
        self.count_label.hide()  # Hide initially
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.count_label)
        
        # Messages container
        self.messages_container = QFrame()
        self.messages_container.setObjectName("messagesContainer")
        self.messages_container.setStyleSheet("""
            QFrame#messagesContainer {
                background: #FFFFFF;
                border: 2px solid #E2E8F0;
                border-top: none;
                border-radius: 0 0 12px 12px;
            }
        """)
        
        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #F1F5F9;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
        """)
        
        # Messages widget
        self.messages_widget = QWidget()
        self.messages_widget.setObjectName("messagesWidget")
        self.messages_widget.setStyleSheet("""
            QWidget#messagesWidget {
                background: transparent;
                border: none;
            }
        """)
        
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(8, 8, 8, 8)
        self.messages_layout.setSpacing(0)
        
        # No messages label
        self.no_messages_label = QLabel("אין הודעות חדשות")
        self.no_messages_label.setObjectName("noMessages")
        self.no_messages_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        self.no_messages_label.setStyleSheet("""
            QLabel#noMessages {
                color: #64748B;
                background: transparent;
                border: none;
                padding: 20px;
            }
        """)
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
        """Refresh the message display"""
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
            
            # Show message count
            self.count_label.setText(str(len(self.messages)))
            self.count_label.show()
            
            # Add message cards
            for message in self.messages:
                card = MessageCard(message, self)
                self.messages_layout.insertWidget(0, card)  # Insert at top
                
    def handle_message_read(self, message_id):
        """Handle message read signal"""
        if self.chat_service:
            result = self.chat_service.mark_message_as_read(message_id)
            if result.get('success'):
                logger.info(f"Message {message_id} marked as read")
                # Remove the message from display
                self.messages = [msg for msg in self.messages if msg.get('id') != message_id]
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

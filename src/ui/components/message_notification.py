"""
Message Notification Toast
Non-intrusive notification for new messages
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from utils.logger import get_logger

logger = get_logger(__name__)


class MessageNotification(QDialog):
    """
    Toast notification for new messages
    Appears in top-right corner with smooth animations
    """
    
    # Signals
    notification_clicked = pyqtSignal()  # Emitted when user clicks the notification
    
    def __init__(self, message_count, parent=None):
        super().__init__(parent)
        self.message_count = message_count
        self.duration = 5000  # 5 seconds
        
        self.setup_ui()
        self.setup_animations()
        self.setup_timer()
        
    def setup_ui(self):
        """Setup the notification UI"""
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(False)
        
        # Set RTL for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Main container
        self.container = QFrame()
        self.container.setObjectName("notificationContainer")
        self.container.setFixedSize(350, 80)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.container.setGraphicsEffect(shadow)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)
        
        # Container layout
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(20, 15, 20, 15)
        container_layout.setSpacing(15)
        
        # Icon
        icon_label = QLabel("💬")
        icon_label.setFont(QFont("Segoe UI", 20))
        icon_label.setStyleSheet("color: #3B82F6;")
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)
        
        # Title
        title_label = QLabel("הודעות חדשות")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1E293B;")
        
        # Message count
        count_text = f"{self.message_count} הודעות חדשות מהמנהל" if self.message_count > 1 else "הודעה חדשה מהמנהל"
        count_label = QLabel(count_text)
        count_label.setFont(QFont("Segoe UI", 12))
        count_label.setStyleSheet("color: #64748B;")
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(count_label)
        
        # Click to view button
        self.view_button = QPushButton("צפה")
        self.view_button.setObjectName("viewButton")
        self.view_button.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.view_button.setFixedSize(60, 35)
        self.view_button.clicked.connect(self.on_notification_clicked)
        
        # Close button
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.close_notification)
        
        # Add to layout
        container_layout.addWidget(icon_label)
        container_layout.addLayout(content_layout)
        container_layout.addWidget(self.view_button)
        container_layout.addWidget(self.close_button)
        
        # Apply styling
        self.apply_styles()
    
    def apply_styles(self):
        """Apply professional styling"""
        self.container.setStyleSheet("""
            QFrame#notificationContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFFFF, stop:1 #F8FAFC);
                border: 2px solid #E2E8F0;
                border-radius: 16px;
            }
            
            QPushButton#viewButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3B82F6, stop:1 #1E40AF);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 700;
            }
            QPushButton#viewButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1E40AF, stop:1 #1E3A8A);
            }
            QPushButton#viewButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1E3A8A, stop:1 #1E293B);
            }
            
            QPushButton#closeButton {
                background: #F1F5F9;
                color: #64748B;
                border: none;
                border-radius: 15px;
                font-weight: 700;
            }
            QPushButton#closeButton:hover {
                background: #E2E8F0;
                color: #374151;
            }
            QPushButton#closeButton:pressed {
                background: #CBD5E1;
            }
        """)
    
    def setup_animations(self):
        """Setup smooth animations"""
        # Slide in from right
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Fade animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def setup_timer(self):
        """Setup auto-dismiss timer"""
        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.close_notification)
    
    def on_notification_clicked(self):
        """Handle notification click"""
        self.notification_clicked.emit()
        self.close_notification()
    
    def close_notification(self):
        """Close the notification with animation"""
        self.auto_close_timer.stop()
        
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()
    
    def show_animated(self, parent_geometry):
        """Show the notification with slide-in animation"""
        # Position in top-right corner
        x = parent_geometry.x() + parent_geometry.width() - self.width() - 20
        y = parent_geometry.y() + 20
        
        # Start off-screen
        start_rect = QRect(x + self.width(), y, self.width(), self.height())
        end_rect = QRect(x, y, self.width(), self.height())
        
        self.setGeometry(start_rect)
        self.setWindowOpacity(0.0)
        self.show()
        
        # Animate slide in
        self.slide_animation.setStartValue(start_rect)
        self.slide_animation.setEndValue(end_rect)
        self.slide_animation.start()
        
        # Fade in
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        # Start auto-close timer
        self.auto_close_timer.start(self.duration)
    
    def mousePressEvent(self, event):
        """Handle mouse click on notification"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_notification_clicked()
        super().mousePressEvent(event)

"""
Floating Timer Overlay
Always-on-top timer displayed during sessions
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                             QPushButton, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from utils.logger import get_logger
from ui.styles import (
    FLOATING_TIMER_BASE_QSS,
    FLOATING_TIMER_WARNING_QSS,
    FLOATING_TIMER_CRITICAL_QSS,
)

logger = get_logger(__name__)


class FloatingTimer(QWidget):
    """Always-on-top floating timer widget"""

    return_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.is_hovered = False
        self.is_warning = False
        self.is_critical = False

        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        # Window flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(180, 80)

        # Position at top-right corner
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 200, 20)

        # Main container
        self.container = QWidget()
        self.container.setObjectName("timerContainer")

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        # Time display
        self.time_label = QLabel("0h 00m 00s")
        self.time_label.setObjectName("timeDisplay")
        self.time_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Status label
        self.status_label = QLabel("Session Active")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Return button (hidden by default)
        self.return_button = QPushButton("Return to App")
        self.return_button.setObjectName("returnButton")
        self.return_button.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.return_button.setMinimumHeight(32)
        self.return_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.return_button.clicked.connect(self.return_clicked.emit)
        self.return_button.hide()

        layout.addWidget(self.time_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.return_button)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.container.setGraphicsEffect(shadow)

        self.apply_styles()

        # Enable mouse tracking for hover
        self.setMouseTracking(True)
        self.container.setMouseTracking(True)

    def update_time(self, seconds: int):
        """Update time display"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        time_str = f"{hours}h {minutes:02d}m {secs:02d}s"
        self.time_label.setText(time_str)

        # Update warning states
        if seconds <= 60:
            if not self.is_critical:
                self.set_critical_mode()
        elif seconds <= 300:
            if not self.is_warning:
                self.set_warning_mode()

    def set_warning_mode(self):
        """Set warning appearance (5 min remaining)"""
        self.is_warning = True
        self.status_label.setText("⚠ Low Time")
        self.container.setStyleSheet(FLOATING_TIMER_WARNING_QSS)
        logger.warning("Timer in warning mode")

    def set_critical_mode(self):
        """Set critical appearance (1 min remaining)"""
        self.is_critical = True
        self.status_label.setText("🔥 CRITICAL")
        self.container.setStyleSheet(FLOATING_TIMER_CRITICAL_QSS)

        # Start pulse animation
        self.pulse_animation()
        logger.error("Timer in critical mode")

    def pulse_animation(self):
        """Pulse animation for critical state"""
        # Simple scale animation
        # Could be enhanced with QPropertyAnimation
        pass

    def set_offline_mode(self, offline: bool):
        """Show offline indicator"""
        if offline:
            self.status_label.setText("⚠ Offline")
        else:
            self.status_label.setText("Session Active")

    def enterEvent(self, event):
        """Mouse entered widget"""
        self.is_hovered = True
        self.return_button.show()
        self.setFixedHeight(120)
        logger.debug("Timer hovered")

    def leaveEvent(self, event):
        """Mouse left widget"""
        self.is_hovered = False
        self.return_button.hide()
        self.setFixedHeight(80)

    def apply_styles(self):
        """Apply styles"""
        self.container.setStyleSheet(FLOATING_TIMER_BASE_QSS)
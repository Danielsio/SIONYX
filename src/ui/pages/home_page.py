"""
Home Dashboard Page
Shows user stats and session controls
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QMessageBox,
                              QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from utils.logger import get_logger
from ui.styles import HOME_PAGE_QSS

logger = get_logger(__name__)


class HomePage(QWidget):
    """Home dashboard with stats and session controls"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_user = auth_service.get_current_user()

        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)

        self.init_ui()
        self.countdown_timer.start(1000)

    def init_ui(self):
        """Initialize UI"""
        self.setObjectName("homePage")
        
        # Set RTL layout direction for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(45, 35, 45, 35)
        layout.setSpacing(25)

        # Header
        header = QLabel("לוח בקרה")
        header.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        header.setStyleSheet("color: #111827;")

        # Stats grid - ONLY 2 CARDS NOW
        stats_container = QWidget()
        stats_container.setStyleSheet("background-color: transparent;")
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setSpacing(20)

        # Time card
        self.time_card = self.create_stat_card(
            "זמן נותר",
            "0ש 0ד 0שנ",
            "#10B981",
            "timeValue"
        )

        # Prints card
        prints = str(self.current_user.get('remainingPrints', 0))
        self.prints_card = self.create_stat_card(
            "הדפסות זמינות",
            prints,
            "#3B82F6",
            "printsValue"
        )

        stats_layout.addWidget(self.time_card)
        stats_layout.addWidget(self.prints_card)
        stats_layout.addStretch()

        # Main action card
        action_card = self.create_action_card()

        layout.addWidget(header)
        layout.addWidget(stats_container)
        layout.addWidget(action_card)
        layout.addStretch()

        self.update_countdown()
        # Apply page styles (in addition to base styles from parent window)
        self.setStyleSheet(HOME_PAGE_QSS)

    def create_stat_card(self, title: str, value: str, color: str, value_name: str) -> QFrame:
        """Create stat card"""
        card = QFrame()
        card.setObjectName("statCard")
        card.setFixedSize(320, 120)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 20))
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        title_label.setStyleSheet("color: #6B7280;")

        value_label = QLabel(value)
        value_label.setObjectName(value_name)
        value_label.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return card

    def create_action_card(self) -> QFrame:
        """Create action card"""
        card = QFrame()
        card.setObjectName("mainActionCard")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 50))
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(18)

        welcome = QLabel(f"ברוך הבא, {self.current_user.get('firstName')}!")
        welcome.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        welcome.setStyleSheet("color: #111827;")

        # Instruction text (will update based on time)
        self.instruction = QLabel("מוכן להתחיל את הפעלתך? לחץ למטה כדי להתחיל.")
        self.instruction.setFont(QFont("Segoe UI", 14))
        self.instruction.setStyleSheet("color: #6B7280;")

        # Start button
        self.start_btn = QPushButton("🚀  התחל להשתמש במחשב")
        self.start_btn.setObjectName("startButton")
        self.start_btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.start_btn.setMinimumHeight(70)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.handle_start_session)

        layout.addWidget(welcome)
        layout.addWidget(self.instruction)
        layout.addSpacing(12)
        layout.addWidget(self.start_btn)

        return card

    def update_countdown(self):
        """Update time display and button state"""
        remaining = self.current_user.get('remainingTime', 0)

        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60

        time_str = f"{hours}ש {minutes}ד {seconds}שנ"

        time_value = self.time_card.findChild(QLabel, "timeValue")
        if time_value:
            time_value.setText(time_str)

            # Color based on time
            if remaining <= 0:
                time_value.setStyleSheet("color: #EF4444;")
            elif remaining < 300:
                time_value.setStyleSheet("color: #EF4444;")
            elif remaining < 1800:
                time_value.setStyleSheet("color: #F59E0B;")
            else:
                time_value.setStyleSheet("color: #10B981;")

        # Update button state
        if remaining <= 0:
            self.start_btn.setEnabled(False)
            self.start_btn.setText("⏸  אין זמן זמין")
            self.instruction.setText("אין לך זמן נותר. רכוש חבילה כדי להמשיך.")
            self.instruction.setStyleSheet("color: #DC2626; font-weight: 600;")

            # Update button style for disabled state
            self.start_btn.setStyleSheet("""
                #startButton:disabled {
                    background-color: #D1D5DB;
                    color: #6B7280;
                    cursor: not-allowed;
                }
            """)
        else:
            self.start_btn.setEnabled(True)
            self.start_btn.setText("🚀  התחל להשתמש במחשב")
            self.instruction.setText("מוכן להתחיל את הפעלתך? לחץ למטה כדי להתחיל.")
            self.instruction.setStyleSheet("color: #6B7280;")

    def handle_start_session(self):
        """Start session immediately without confirmation"""
        logger.info("Start session button clicked")

        remaining = self.current_user.get('remainingTime', 0)

        # Double-check (shouldn't happen if button is disabled)
        if remaining <= 0:
            logger.warning("Attempted to start session with 0 time")
            return

        # Start session immediately - no confirmation needed
        logger.info(f"Starting session with {remaining} seconds available")
        self.parent().parent().parent().start_user_session(remaining)

    def cleanup(self):
        """Cleanup"""
        self.countdown_timer.stop()
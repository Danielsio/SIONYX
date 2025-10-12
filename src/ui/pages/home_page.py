"""
Home Dashboard Page
Shows user stats and session controls
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QMessageBox,
                              QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon

from utils.logger import get_logger

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
        """Initialize modern UI with professional styling"""
        self.setObjectName("homePage")
        
        # Set RTL layout direction for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Set main background
        self.setStyleSheet("""
            QWidget {
                background: #F8FAFC;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(30)

        # Modern header with gradient background
        header_container = QWidget()
        header_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3B82F6, stop:1 #1E40AF);
                border-radius: 20px;
                padding: 20px;
            }
        """)
        
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(30, 25, 30, 25)
        header_layout.setSpacing(8)
        
        # Top row with title and refresh button
        top_row = QWidget()
        top_row_layout = QHBoxLayout(top_row)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.setSpacing(20)
        
        # Main title with stunning typography
        header = QLabel("לוח בקרה")
        header.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        header.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: 800;
                margin-bottom: 8px;
            }
        """)
        
        # Modern refresh button
        self.refresh_btn = QPushButton("🔄 רענן")
        self.refresh_btn.setObjectName("refreshButton")
        self.refresh_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        self.refresh_btn.setFixedSize(140, 45)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                font-weight: 600;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.4);
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_user_data)
        
        top_row_layout.addWidget(header)
        top_row_layout.addStretch()
        top_row_layout.addWidget(self.refresh_btn)
        
        # Subtitle with elegant styling
        subtitle = QLabel("סקירה כללית של החשבון שלך וזמן הפעלה זמין")
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                font-weight: 400;
                margin-top: 8px;
            }
        """)
        
        header_layout.addWidget(top_row)
        header_layout.addWidget(subtitle)

        # Modern stats grid container with responsive design
        stats_container = QWidget()
        stats_container.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setSpacing(25)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the cards

        # Time card with modern styling
        self.time_card = self.create_modern_stat_card(
            "זמן נותר",
            "0:00:00",
            "#10B981",
            "timeValue",
            "⏰"
        )

        # Prints card with modern styling
        prints = str(self.current_user.get('remainingPrints', 0))
        self.prints_card = self.create_modern_stat_card(
            "הדפסות זמינות",
            prints,
            "#3B82F6",
            "printsValue",
            "🖨️"
        )

        # Add cards with proper alignment
        stats_layout.addStretch()
        stats_layout.addWidget(self.time_card)
        stats_layout.addWidget(self.prints_card)
        stats_layout.addStretch()

        # Main action card
        action_card = self.create_action_card()

        # Add some spacing and visual separation
        layout.addWidget(header_container)
        layout.addSpacing(10)  # Add breathing room
        layout.addWidget(stats_container)
        layout.addSpacing(20)  # Add breathing room
        layout.addWidget(action_card)
        layout.addStretch()

        # Add subtle animation effects
        self.setup_animations()

        self.update_countdown()

    def setup_animations(self):
        """Setup subtle animations and effects for better UX"""
        # Add hover effects to stat cards
        for card in [self.time_card, self.prints_card]:
            if card:
                # Add subtle hover animation
                card.enterEvent = lambda event, c=card: self.card_hover_enter(c)
                card.leaveEvent = lambda event, c=card: self.card_hover_leave(c)

    def card_hover_enter(self, card):
        """Handle card hover enter with enhanced shadow"""
        if card:
            # Significantly increase shadow on hover for dramatic effect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(50)
            shadow.setXOffset(0)
            shadow.setYOffset(16)
            shadow.setColor(QColor(0, 0, 0, 45))
            card.setGraphicsEffect(shadow)

    def card_hover_leave(self, card):
        """Handle card hover leave with enhanced base shadow"""
        if card:
            # Enhanced base shadow
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(40)
            shadow.setXOffset(0)
            shadow.setYOffset(12)
            shadow.setColor(QColor(0, 0, 0, 35))
            card.setGraphicsEffect(shadow)

    def create_modern_stat_card(self, title: str, value: str, color: str, value_name: str, icon: str) -> QFrame:
        """Create modern stat card with professional styling"""
        card = QFrame()
        card.setObjectName("modernStatCard")
        card.setFixedSize(400, 160)  # Perfect dimensions for modern look

        # Enhanced drop shadow for better elevation effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(12)
        shadow.setColor(QColor(0, 0, 0, 35))
        card.setGraphicsEffect(shadow)

        # Modern card styling with enhanced shadows
        card.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border-radius: 20px;
                border: 2px solid #E2E8F0;
            }}
            QFrame:hover {{
                border: 2px solid {color};
                background: #F8FAFC;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
            QLabel:hover {{
                border: none;
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        # Icon and title row
        icon_title_row = QWidget()
        icon_title_layout = QHBoxLayout(icon_title_row)
        icon_title_layout.setContentsMargins(0, 0, 0, 0)
        icon_title_layout.setSpacing(12)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 24))
        icon_label.setStyleSheet(f"color: {color};")

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        title_label.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-weight: 600;
            }
        """)

        icon_title_layout.addWidget(icon_label)
        icon_title_layout.addWidget(title_label)
        icon_title_layout.addStretch()

        # Value with modern typography and clean borders
        value_label = QLabel(value)
        value_label.setObjectName(value_name)
        value_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-weight: 800;
                font-size: 28px;
                border: none;
                background: transparent;
            }}
            QLabel:hover {{
                border: none;
                background: transparent;
            }}
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setWordWrap(False)

        layout.addWidget(icon_title_row)
        layout.addWidget(value_label)

        return card

    def create_action_card(self) -> QFrame:
        """Create modern action card with professional styling"""
        card = QFrame()
        card.setObjectName("modernActionCard")

        # Enhanced shadow for dramatic depth effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setXOffset(0)
        shadow.setYOffset(16)
        shadow.setColor(QColor(0, 0, 0, 40))
        card.setGraphicsEffect(shadow)

        # Modern card styling with gradient background
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFFFF, stop:1 #F8FAFC);
                border-radius: 24px;
                border: 2px solid #E2E8F0;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(60, 50, 60, 50)
        layout.setSpacing(25)

        # Welcome section with modern typography
        welcome_container = QWidget()
        welcome_layout = QVBoxLayout(welcome_container)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        welcome_layout.setSpacing(8)

        welcome = QLabel(f"ברוך הבא, {self.current_user.get('firstName')}! 👋")
        welcome.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        welcome.setStyleSheet("""
            QLabel {
                color: #1E293B;
                font-weight: 800;
                text-align: center;
            }
        """)
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Subtitle
        subtitle = QLabel("התחל את הפעלתך במחשב עכשיו")
        subtitle.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
        subtitle.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-weight: 500;
                text-align: center;
            }
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome_layout.addWidget(welcome)
        welcome_layout.addWidget(subtitle)

        # Instruction text with modern styling
        self.instruction = QLabel("מוכן להתחיל את הפעלתך? לחץ למטה כדי להתחיל.")
        self.instruction.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
        self.instruction.setStyleSheet("""
            QLabel {
                color: #475569;
                font-weight: 500;
                text-align: center;
                background: #F1F5F9;
                padding: 16px 24px;
                border-radius: 12px;
                border-left: 4px solid #3B82F6;
            }
        """)
        self.instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Modern start button with gradient
        self.start_btn = QPushButton("🚀  התחל להשתמש במחשב")
        self.start_btn.setObjectName("modernStartButton")
        self.start_btn.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.start_btn.setMinimumHeight(80)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3B82F6, stop:1 #1E40AF);
                color: white;
                border: none;
                border-radius: 16px;
                font-weight: 700;
                font-size: 18px;
                padding: 20px 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2563EB, stop:1 #1D4ED8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1D4ED8, stop:1 #1E3A8A);
            }
        """)
        self.start_btn.clicked.connect(self.handle_start_session)

        layout.addWidget(welcome_container)
        layout.addWidget(self.instruction)
        layout.addSpacing(20)
        layout.addWidget(self.start_btn)

        return card

    def update_countdown(self):
        """Update time display and button state with modern styling"""
        remaining = self.current_user.get('remainingTime', 0)

        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60

        time_str = f"{hours}:{minutes:02d}:{seconds:02d}"

        time_value = self.time_card.findChild(QLabel, "timeValue")
        if time_value:
            time_value.setText(time_str)

            # Dynamic color based on time remaining
            if remaining <= 0:
                color = "#EF4444"
            elif remaining < 300:  # Less than 5 minutes
                color = "#EF4444"
            elif remaining < 1800:  # Less than 30 minutes
                color = "#F59E0B"
            else:
                color = "#10B981"

            # Update value color
            time_value.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-weight: 800;
                    font-size: 28px;
                }}
            """)

        # Update button state with modern styling
        if remaining <= 0:
            self.start_btn.setEnabled(False)
            self.start_btn.setText("⏸  אין זמן זמין")
            self.instruction.setText("אין לך זמן נותר. רכוש חבילה כדי להמשיך.")
            self.instruction.setStyleSheet("""
                QLabel {
                    color: #DC2626;
                    font-weight: 600;
                    text-align: center;
                    background: #FEF2F2;
                    padding: 16px 24px;
                    border-radius: 12px;
                    border-left: 4px solid #EF4444;
                }
            """)

            # Modern disabled button style
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: #E2E8F0;
                    color: #94A3B8;
                    border: none;
                    border-radius: 16px;
                    font-weight: 700;
                    font-size: 18px;
                    padding: 20px 40px;
                }
                QPushButton:disabled {
                    background: #E2E8F0;
                    color: #94A3B8;
                    cursor: not-allowed;
                }
            """)
        else:
            self.start_btn.setEnabled(True)
            self.start_btn.setText("🚀  התחל להשתמש במחשב")
            self.instruction.setText("מוכן להתחיל את הפעלתך? לחץ למטה כדי להתחיל.")
            self.instruction.setStyleSheet("""
                QLabel {
                    color: #475569;
                    font-weight: 500;
                    text-align: center;
                    background: #F1F5F9;
                    padding: 16px 24px;
                    border-radius: 12px;
                    border-left: 4px solid #3B82F6;
                }
            """)

            # Modern enabled button style
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #3B82F6, stop:1 #1E40AF);
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-weight: 700;
                    font-size: 18px;
                    padding: 20px 40px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #2563EB, stop:1 #1D4ED8);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #1D4ED8, stop:1 #1E3A8A);
                }
            """)

    def refresh_user_data(self):
        """Refresh user data from Firebase with modern feedback"""
        logger.info("Refreshing user data...")
        
        try:
            # Show loading state with modern styling
            self.refresh_btn.setText("🔄 מרענן...")
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.3);
                    color: white;
                    border: 2px solid rgba(255, 255, 255, 0.4);
                    border-radius: 12px;
                    font-weight: 600;
                    padding: 8px 16px;
                }
                QPushButton:disabled {
                    background: rgba(255, 255, 255, 0.3);
                    color: rgba(255, 255, 255, 0.8);
                }
            """)
            
            # Refresh user data from Firebase
            self.current_user = self.auth_service.get_current_user()
            
            # Update the prints card immediately
            prints = str(self.current_user.get('remainingPrints', 0))
            prints_value = self.prints_card.findChild(QLabel, "printsValue")
            if prints_value:
                prints_value.setText(prints)
            
            # Update countdown will handle time display
            self.update_countdown()
            
            logger.info("User data refreshed successfully")
            
            # Show success message with modern styling
            self.refresh_btn.setText("✅ עודכן!")
            self.refresh_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(16, 185, 129, 0.3);
                    color: white;
                    border: 2px solid rgba(16, 185, 129, 0.5);
                    border-radius: 12px;
                    font-weight: 600;
                    padding: 8px 16px;
                }
            """)
            QTimer.singleShot(2000, self.reset_refresh_button)
            
        except Exception as e:
            logger.error(f"Failed to refresh user data: {e}")
            self.refresh_btn.setText("❌ שגיאה")
            self.refresh_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(239, 68, 68, 0.3);
                    color: white;
                    border: 2px solid rgba(239, 68, 68, 0.5);
                    border-radius: 12px;
                    font-weight: 600;
                    padding: 8px 16px;
                }
            """)
            QTimer.singleShot(2000, self.reset_refresh_button)
    
    def reset_refresh_button(self):
        """Reset refresh button to normal state with modern styling"""
        self.refresh_btn.setText("🔄 רענן")
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                font-weight: 600;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.4);
            }
        """)

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

    def resizeEvent(self, event):
        """Handle window resize for responsive design"""
        super().resizeEvent(event)
        # Ensure cards remain properly sized and centered
        if hasattr(self, 'time_card') and hasattr(self, 'prints_card'):
            # Cards will maintain their fixed size but layout will adjust
            pass

    def cleanup(self):
        """Cleanup"""
        self.countdown_timer.stop()
"""
Home Dashboard Page
Shows user stats and session controls
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame,
                              QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from utils.logger import get_logger
from services.chat_service import ChatService

logger = get_logger(__name__)

# Optional modal system imports
try:
    from ui.components.message_modal import MessageModal
    MODAL_SYSTEM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Modal system not available: {e}")
    MessageModal = None
    MessageNotification = None
    MODAL_SYSTEM_AVAILABLE = False


class HomePage(QWidget):
    """Home dashboard with stats and session controls"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_user = auth_service.get_current_user()

        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)

        # Initialize chat service
        self.chat_service = ChatService(
            auth_service.firebase,
            self.current_user['uid'],
            auth_service.firebase.org_id
        )
        

        self.message_modal = None
        self.pending_messages = []

        self.init_ui()
        self.countdown_timer.start(1000)
        
        # Start listening for messages
        self.start_message_listening()

        # Connect to chat service signals for thread-safe updates
        if self.chat_service:
            self.chat_service.messages_received.connect(self.handle_new_messages)

    def init_ui(self):
        """Initialize modern UI with professional styling"""
        self.setObjectName("homePage")
        
        # Set RTL layout direction for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Set sophisticated grayish background
        self.setStyleSheet("""
            QWidget {
                background: #F1F5F9;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(30)

        # Clean header section matching packages page style
        header_container = QWidget()
        header_container.setStyleSheet("""
            QWidget {
                background: #3B82F6;
                border-radius: 20px;
                padding: 20px;
            }
        """)
        
        # Add shadow to header
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(40)
        header_shadow.setXOffset(0)
        header_shadow.setYOffset(12)
        header_shadow.setColor(QColor(0, 0, 0, 55))
        header_container.setGraphicsEffect(header_shadow)
        
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(30, 25, 30, 25)
        header_layout.setSpacing(8)
        
        # Main title with stunning typography
        header = QLabel("לוח בקרה")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: 800;
                margin-bottom: 8px;
            }
        """)
        
        # Subtitle with elegant styling
        subtitle = QLabel("ניהול זמן והדפסות")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                font-weight: 400;
            }
        """)
        
        
        header_layout.addWidget(header)
        header_layout.addWidget(subtitle)

        # Add header to main layout
        layout.addWidget(header_container)


        # Load initial messages
        self.load_messages()

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

        self.message_card = self.create_message_notification_card()
        self.message_card.hide()  # Start hidden until messages arrive

        # Add cards with proper alignment
        stats_layout.addStretch()
        stats_layout.addWidget(self.time_card)
        stats_layout.addWidget(self.prints_card)
        stats_layout.addWidget(self.message_card)
        stats_layout.addStretch()

        # Main action card
        action_card = self.create_action_card()

        # Add some spacing and visual separation
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
            shadow.setBlurRadius(70)
            shadow.setXOffset(0)
            shadow.setYOffset(20)
            shadow.setColor(QColor(0, 0, 0, 80))
            card.setGraphicsEffect(shadow)

    def card_hover_leave(self, card):
        """Handle card hover leave with enhanced base shadow"""
        if card:
            # Enhanced base shadow
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(50)
            shadow.setXOffset(0)
            shadow.setYOffset(15)
            shadow.setColor(QColor(0, 0, 0, 60))
            card.setGraphicsEffect(shadow)

    def create_modern_stat_card(self, title: str, value: str, color: str, value_name: str, icon: str) -> QFrame:
        """Create modern stat card with professional styling"""
        card = QFrame()
        card.setObjectName("modernStatCard")
        card.setFixedSize(400, 160)  # Perfect dimensions for modern look

        # Enhanced drop shadow for better elevation effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setXOffset(0)
        shadow.setYOffset(15)
        shadow.setColor(QColor(0, 0, 0, 60))
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

    def create_message_notification_card(self) -> QFrame:
        """Create message notification card integrated into the dashboard"""
        card = QFrame()
        card.setObjectName("messageNotificationCard")
        card.setFixedSize(400, 160)  # Same size as other cards

        # Enhanced drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setXOffset(0)
        shadow.setYOffset(15)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)

        # Message card styling
        card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 20px;
                border: 2px solid #E2E8F0;
            }
            QLabel {
                border: none;
                background: transparent;
            }
            QPushButton {
                border: none;
                background: transparent;
                border-radius: 12px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(245, 158, 11, 0.1);
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 18, 25, 18)  # Reduced margins for better text fit
        layout.setSpacing(10)

        # Icon and title row
        icon_title_row = QWidget()
        icon_title_layout = QHBoxLayout(icon_title_row)
        icon_title_layout.setContentsMargins(0, 0, 0, 0)
        icon_title_layout.setSpacing(12)

        # Message icon
        icon_label = QLabel("💬")
        icon_label.setFont(QFont("Segoe UI", 24))
        icon_label.setStyleSheet("color: #F59E0B;")

        # Title
        title_label = QLabel("הודעות חדשות")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1E293B;")

        icon_title_layout.addWidget(icon_label)
        icon_title_layout.addWidget(title_label)
        icon_title_layout.addStretch()

        # Message count and action
        self.message_count_label = QLabel("0 הודעות")
        self.message_count_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        self.message_count_label.setStyleSheet("color: #64748B;")
        self.message_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # View messages button
        self.view_messages_button = QPushButton("👁️ צפה בהודעות")
        self.view_messages_button.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.view_messages_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_messages_button.clicked.connect(self.show_message_modal)
        self.view_messages_button.setFixedHeight(45)  # Fixed height to ensure text fits
        self.view_messages_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F59E0B, stop:1 #D97706);
                color: white;
                border: none;
                border-radius: 15px;
                padding: 12px 25px;
                font-weight: 700;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #D97706, stop:1 #B45309);
            }
        """)

        layout.addWidget(icon_title_row)
        layout.addWidget(self.message_count_label)
        layout.addWidget(self.view_messages_button)

        return card

    def create_action_card(self) -> QFrame:
        """Create modern action card with professional styling"""
        card = QFrame()
        card.setObjectName("modernActionCard")

        # Enhanced shadow for dramatic depth effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setXOffset(0)
        shadow.setYOffset(20)
        shadow.setColor(QColor(0, 0, 0, 70))
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
        """Refresh user data (called by main window)"""
        logger.info("Refreshing user data in HomePage")

        # Get current user from auth service
        self.current_user = self.auth_service.get_current_user()

        if not self.current_user:
            logger.warning("No current user found in HomePage refresh")
            return

        # Update UI with current user data
        self.update_countdown()  # This will update the display

        # Don't reload messages here - they're already loaded during initialization
        # This prevents duplicate message loading

    def clear_user_data(self):
        """Clear all user data (called on logout)"""
        logger.info("Clearing user data in HomePage")
        
        self.current_user = None
        
        # Reset UI to default state
        if hasattr(self, 'time_value'):
            self.time_value.setText("00:00")
        if hasattr(self, 'prints_value'):
            self.prints_value.setText("0")
        
        # Disable session button
        if hasattr(self, 'start_btn'):
            self.start_btn.setEnabled(False)

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

    def start_message_listening(self):
        """Start listening for new messages"""
        if self.chat_service and not self.chat_service.is_listening:
            self.chat_service.start_listening()  # No callback needed, using signals
            logger.info("Started listening for messages")
        elif self.chat_service and self.chat_service.is_listening:
            logger.debug("Chat service already listening, skipping")

    def load_messages(self):
        """Load initial unread messages"""
        if self.chat_service:
            result = self.chat_service.get_unread_messages()
            if result.get('success'):
                messages = result.get('messages', [])
                self.pending_messages = messages

                if messages:
                    self.show_message_notification(len(messages))
                    logger.info(f"Loaded {len(messages)} unread messages")
                else:
                    logger.info("No unread messages")
            else:
                logger.error(f"Failed to load messages: {result.get('error')}")
    
    def handle_new_messages(self, result):
        """Handle new messages from chat service"""
        if result.get('success'):
            messages = result.get('messages', [])
            self.pending_messages = messages

            if messages:
                self.show_message_notification(len(messages))
                logger.info(f"Received {len(messages)} new messages")
        else:
            logger.error(f"Error receiving messages: {result.get('error')}")
    
    def on_message_read(self, message_id):
        """Handle message read signal from MessageDisplay"""
        logger.info(f"Message {message_id} marked as read")
        # The MessageDisplay component handles the actual marking as read
        # This is just for logging and any additional cleanup if needed

    def show_message_notification(self, message_count):
        """Update message notification card with new message count"""
        logger.info(f"show_message_notification called with {message_count} messages")
        
        if message_count <= 0:
            # Hide the message card if no messages
            if hasattr(self, 'message_card'):
                self.message_card.hide()
            return
        
        # Show the message card and update count
        if hasattr(self, 'message_card'):
            self.message_card.show()
            if message_count == 1:
                self.message_count_label.setText("הודעה חדשה")
            else:
                self.message_count_label.setText(f"{message_count} הודעות")
            
            # Update button text
            if message_count == 1:
                self.view_messages_button.setText("👁️ צפה בהודעה")
            else:
                self.view_messages_button.setText("👁️ צפה בהודעות")
        
        logger.info(f"Message card updated with {message_count} messages")

    def show_message_modal(self):
        """Show the message modal with pending messages"""
        logger.info(f"show_message_modal called with {len(self.pending_messages)} messages")
        
        if not self.pending_messages:
            logger.warning("No pending messages to show")
            return
            
        # Close existing modal if any
        if self.message_modal:
            self.message_modal.close()
        
        # Create new modal with pending messages
        logger.info("Creating MessageModal...")
        self.message_modal = MessageModal(self.pending_messages, self.chat_service, self)
        self.message_modal.message_read.connect(self.on_message_read)
        self.message_modal.all_messages_read.connect(self.on_all_messages_read)
        
        # Show the modal with animation (centered)
        logger.info("Showing modal with animation...")
        self.message_modal.show_animated()
        
        # Ensure the modal gets focus and appears on top after animation
        QTimer.singleShot(500, lambda: self._focus_modal())

    def _focus_modal(self):
        """Focus the message modal after animation"""
        if self.message_modal:
            self.message_modal.raise_()
            self.message_modal.activateWindow()
            self.message_modal.setFocus()

    def on_all_messages_read(self):
        """Handle when all messages are read"""
        self.pending_messages = []
        # Hide the message card since no messages are pending
        if hasattr(self, 'message_card'):
            self.message_card.hide()
        logger.info("All messages have been read")

    def cleanup(self):
        """Cleanup"""
        self.countdown_timer.stop()
        if self.chat_service:
            self.chat_service.cleanup()
        if self.message_modal:
            self.message_modal.close()
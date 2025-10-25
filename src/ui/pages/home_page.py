"""
Home Dashboard Page
Shows user stats and session controls
Refactored to use centralized constants and base components
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.chat_service import ChatService
from ui.components.base_components import (
    ActionButton,
    StatCard,
)
from ui.constants.ui_constants import (
    BorderRadius,
    Colors,
    Gradients,
    Shadows,
    Spacing,
    Typography,
    UIStrings,
    get_shadow_effect,
)
from utils.logger import get_logger


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
            self.current_user["uid"],
            auth_service.firebase.org_id,
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
        """Initialize modern UI using base components and constants"""
        self.setObjectName("homePage")

        # Set RTL layout direction for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Set background using constants
        self.setStyleSheet(
            f"""
            QWidget {{
                background: {Colors.BG_PRIMARY};
            }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Spacing.PAGE_MARGIN,
            Spacing.SECTION_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.SECTION_MARGIN,
        )
        layout.setSpacing(Spacing.SECTION_SPACING)

        # Create header matching history page style
        self.create_header(layout)

        # Modern stats grid container using constants
        stats_container = QWidget()
        stats_container.setStyleSheet("background: transparent;")
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setSpacing(5)  # Very minimal spacing between cards
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Time card using base component
        self.time_card = StatCard(
            UIStrings.TIME_REMAINING, "0:00:00", "", Colors.SUCCESS, "⏰"
        )
        self.time_card.setObjectName("timeCard")

        # Prints card using base component - now shows budget instead of count
        print_budget = self.current_user.get("remainingPrints", 0.0)
        budget_text = f"{print_budget:.2f}₪"
        self.prints_card = StatCard("יתרת הדפסות", budget_text, "", Colors.PRIMARY, "🖨️")
        self.prints_card.setObjectName("printsCard")

        # Message notification card
        self.message_card = self.create_message_notification_card()
        logger.info(f"Message card created: {self.message_card is not None}")
        logger.info(f"Message card object name: {self.message_card.objectName()}")
        self.message_card.hide()  # Start hidden until messages arrive

        # Add cards with proper alignment
        stats_layout.addStretch()
        stats_layout.addWidget(self.time_card)
        stats_layout.addWidget(self.prints_card)
        stats_layout.addWidget(self.message_card)
        stats_layout.addStretch()

        # Load initial messages after message card is created
        self.load_messages()

        # Main action card
        action_card = self.create_action_card()

        # Add minimal spacing between components - closer together
        layout.addSpacing(8)  # Small spacing after header
        layout.addWidget(stats_container)
        layout.addSpacing(8)  # Small spacing between cards and action
        layout.addWidget(action_card)
        layout.addStretch()

        # Add subtle animation effects
        self.setup_animations()

        self.update_countdown()

    def create_header(self, parent_layout):
        """Create page header matching history page style"""
        # Clean header section matching history page style
        header_container = QWidget()
        header_container.setStyleSheet(
            """
            QWidget {
                background: #3B82F6;
                border-radius: 20px;
                padding: 20px;
            }
        """
        )

        # Add shadow to header - Enhanced shadow effect
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(50)
        header_shadow.setXOffset(0)
        header_shadow.setYOffset(15)
        header_shadow.setColor(QColor(0, 0, 0, 65))
        header_container.setGraphicsEffect(header_shadow)
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(30, 25, 30, 25)
        header_layout.setSpacing(8)

        # Main title with stunning typography
        title = QLabel("ניהול זמן והדפסות")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: 800;
                margin-bottom: 8px;
            }
        """
        )

        # Subtitle with elegant styling
        subtitle = QLabel("לוח בקרה")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                font-weight: 400;
            }
        """
        )

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        parent_layout.addWidget(header_container)

    def setup_animations(self):
        """Setup subtle animations and effects for better UX"""
        # Cards use static styling - no hover effects needed

    def create_modern_stat_card(
        self, title: str, value: str, color: str, value_name: str, icon: str
    ) -> QFrame:
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
        card.setStyleSheet(
            """
            QFrame {
                background: #FFFFFF;
                border-radius: 20px;
                border: 2px solid #E2E8F0;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """
        )

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
        title_label.setStyleSheet(
            """
            QLabel {
                color: #64748B;
                font-weight: 600;
            }
        """
        )

        icon_title_layout.addWidget(icon_label)
        icon_title_layout.addWidget(title_label)
        icon_title_layout.addStretch()

        # Value with modern typography and clean borders
        value_label = QLabel(value)
        value_label.setObjectName(value_name)
        value_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-weight: 800;
                font-size: 28px;
                border: none;
                background: transparent;
            }}
        """
        )
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setWordWrap(False)

        layout.addWidget(icon_title_row)
        layout.addWidget(value_label)

        return card

    def create_message_notification_card(self) -> QFrame:
        """Create message notification card integrated into the dashboard"""
        card = QFrame()
        card.setObjectName("messageNotificationCard")
        card.setFixedSize(400, 200)  # Increased height for better content visibility

        # Apply same shadow as stat cards for consistency
        from ui.constants.ui_constants import Shadows, get_shadow_effect

        shadow_config = get_shadow_effect(
            Shadows.LARGE_BLUR, Shadows.Y_OFFSET_LARGE, Shadows.DARK
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(shadow_config["blur_radius"])
        shadow.setXOffset(shadow_config["x_offset"])
        shadow.setYOffset(shadow_config["y_offset"])
        shadow.setColor(QColor(shadow_config["color"]))
        card.setGraphicsEffect(shadow)

        # Message card styling
        card.setStyleSheet(
            """
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
        """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            25, 30, 25, 20
        )  # Extra top margin to match stat cards
        layout.setSpacing(12)  # Increased spacing for better layout

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
        self.view_messages_button.setFixedHeight(
            40
        )  # Comfortable height for increased card size
        self.view_messages_button.setStyleSheet(
            """
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
        """
        )

        layout.addWidget(icon_title_row)
        layout.addWidget(self.message_count_label)
        layout.addWidget(self.view_messages_button)

        return card

    def create_action_card(self) -> QFrame:
        """Create modern action card using base components and constants"""
        card = QFrame()
        card.setObjectName("modernActionCard")

        # Apply shadow using constants
        shadow_config = get_shadow_effect(
            Shadows.EXTRA_LARGE_BLUR, Shadows.Y_OFFSET_EXTRA_LARGE
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(shadow_config["blur_radius"])
        shadow.setXOffset(shadow_config["x_offset"])
        shadow.setYOffset(shadow_config["y_offset"])
        shadow.setColor(QColor(shadow_config["color"]))
        card.setGraphicsEffect(shadow)

        # Apply card styling using constants
        card.setStyleSheet(
            f"""
            QFrame {{
                background: {Gradients.CARD_GRADIENT};
                border-radius: {BorderRadius.EXTRA_LARGE}px;
                border: 2px solid {Colors.BORDER_LIGHT};
            }}
        """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            Spacing.SECTION_MARGIN * 2,
            Spacing.SECTION_MARGIN * 2,
            Spacing.SECTION_MARGIN * 2,
            Spacing.SECTION_MARGIN * 2,
        )
        layout.setSpacing(Spacing.CARD_SPACING)

        # Welcome section
        welcome_container = self.create_welcome_section()

        # Instruction text
        self.instruction = self.create_instruction_text()

        # Start button using base component
        self.start_btn = ActionButton("🚀  התחל להשתמש במחשב", "primary", "large")
        self.start_btn.setObjectName("modernStartButton")
        self.start_btn.clicked.connect(self.handle_start_session)

        layout.addWidget(welcome_container)
        layout.addWidget(self.instruction)
        layout.addSpacing(Spacing.CARD_MARGIN)
        layout.addWidget(self.start_btn)

        return card

    def create_welcome_section(self) -> QWidget:
        """Create welcome section with user greeting"""
        welcome_container = QWidget()
        welcome_layout = QVBoxLayout(welcome_container)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        welcome_layout.setSpacing(Spacing.TIGHT_SPACING)

        # Welcome message
        welcome = QLabel(f"ברוך הבא, {self.current_user.get('firstName')}! 👋")
        welcome.setFont(
            QFont(
                Typography.FONT_FAMILY, Typography.SIZE_3XL, Typography.WEIGHT_EXTRABOLD
            )
        )
        welcome.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome_layout.addWidget(welcome)

        return welcome_container

    def create_instruction_text(self) -> QLabel:
        """Create instruction text with styling"""
        instruction = QLabel("מוכן להתחיל את הפעלתך? לחץ למטה כדי להתחיל.")
        instruction.setFont(
            QFont(Typography.FONT_FAMILY, Typography.SIZE_LG, Typography.WEIGHT_MEDIUM)
        )
        instruction.setStyleSheet(
            f"""
            QLabel {{
                color: {Colors.GRAY_600};
                text-align: center;
                background: {Colors.BG_PRIMARY};
                padding: {Spacing.COMPONENT_MARGIN}px {Spacing.CARD_MARGIN}px;
                border-radius: {BorderRadius.MEDIUM}px;
                border-left: 4px solid {Colors.PRIMARY};
            }}
        """
        )
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return instruction

    def update_countdown(self):
        """Update time display and button state using constants"""
        remaining = self.current_user.get("remainingTime", 0)

        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60

        time_str = f"{hours}:{minutes:02d}:{seconds:02d}"

        # Update time card value
        time_value = self.time_card.findChild(QLabel, "timeValue")
        if time_value:
            time_value.setText(time_str)

            # Dynamic color based on time remaining using constants
            if remaining <= 0:
                color = Colors.ERROR
            elif remaining < 300:  # Less than 5 minutes
                color = Colors.ERROR
            elif remaining < 1800:  # Less than 30 minutes
                color = Colors.WARNING
            else:
                color = Colors.SUCCESS

            # Update value color using constants
            time_value.setStyleSheet(
                f"""
                QLabel {{
                    color: {color};
                    font-weight: {Typography.WEIGHT_EXTRABOLD};
                    font-size: {Typography.SIZE_3XL}px;
                }}
            """
            )

        # Update button state using constants
        if remaining <= 0:
            self.start_btn.setEnabled(False)
            self.start_btn.setText("⏸  אין זמן זמין")
            self.instruction.setText("אין לך זמן נותר. רכוש חבילה כדי להמשיך.")
            self.instruction.setStyleSheet(
                f"""
                QLabel {{
                    color: {Colors.ERROR_HOVER};
                    font-weight: {Typography.WEIGHT_SEMIBOLD};
                    text-align: center;
                    background: {Colors.ERROR_LIGHT};
                    padding: {Spacing.COMPONENT_MARGIN}px {Spacing.CARD_MARGIN}px;
                    border-radius: {BorderRadius.MEDIUM}px;
                    border-left: 4px solid {Colors.ERROR};
                }}
            """
            )

            # Disabled button style using constants
            self.start_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {Colors.GRAY_200};
                    color: {Colors.TEXT_MUTED};
                    border: none;
                    border-radius: {BorderRadius.LARGE}px;
                    font-weight: {Typography.WEIGHT_BOLD};
                    font-size: {Typography.SIZE_XL}px;
                    padding: {Spacing.CARD_MARGIN}px {Spacing.SECTION_MARGIN}px;
                }}
                QPushButton:disabled {{
                    background: {Colors.GRAY_200};
                    color: {Colors.TEXT_MUTED};
                    cursor: not-allowed;
                }}
            """
            )
        else:
            self.start_btn.setEnabled(True)
            self.start_btn.setText("🚀  התחל להשתמש במחשב")
            self.instruction.setText("מוכן להתחיל את הפעלתך? לחץ למטה כדי להתחיל.")
            self.instruction.setStyleSheet(
                f"""
                QLabel {{
                    color: {Colors.GRAY_600};
                    font-weight: {Typography.WEIGHT_MEDIUM};
                    text-align: center;
                    background: {Colors.BG_PRIMARY};
                    padding: {Spacing.COMPONENT_MARGIN}px {Spacing.CARD_MARGIN}px;
                    border-radius: {BorderRadius.MEDIUM}px;
                    border-left: 4px solid {Colors.PRIMARY};
                }}
            """
            )

            # Enabled button style using constants
            self.start_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {Gradients.PRIMARY_GRADIENT};
                    color: {Colors.WHITE};
                    border: none;
                    border-radius: {BorderRadius.LARGE}px;
                    font-weight: {Typography.WEIGHT_BOLD};
                    font-size: {Typography.SIZE_XL}px;
                    padding: {Spacing.CARD_MARGIN}px {Spacing.SECTION_MARGIN}px;
                }}
                QPushButton:hover {{
                    background: {Gradients.PRIMARY_GRADIENT.replace('#3B82F6', '#2563EB')};
                }}
                QPushButton:pressed {{
                    background: {Gradients.PRIMARY_GRADIENT.replace('#3B82F6', '#1D4ED8')};
                }}
            """
            )

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
        if hasattr(self, "time_value"):
            self.time_value.setText("00:00")
        if hasattr(self, "prints_value"):
            self.prints_value.setText("0")

        # Disable session button
        if hasattr(self, "start_btn"):
            self.start_btn.setEnabled(False)

    def handle_start_session(self):
        """Start session immediately without confirmation"""
        logger.info("Start session button clicked")

        remaining = self.current_user.get("remainingTime", 0)

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
        if hasattr(self, "time_card") and hasattr(self, "prints_card"):
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
            result = self.chat_service.get_unread_messages(
                use_cache=False
            )  # Force fresh data
            logger.info(f"load_messages result: {result}")
            if result.get("success"):
                messages = result.get("messages", [])
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
        if result.get("success"):
            messages = result.get("messages", [])
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
        logger.info(f"hasattr(self, 'message_card'): {hasattr(self, 'message_card')}")

        if message_count <= 0:
            # Hide the message card if no messages
            if hasattr(self, "message_card"):
                logger.info("Hiding message card - no messages")
                self.message_card.hide()
            return

        # Show the message card and update count
        if hasattr(self, "message_card"):
            logger.info(f"Showing message card with {message_count} messages")
            logger.info(
                f"Message card visible before show(): {self.message_card.isVisible()}"
            )
            self.message_card.show()
            logger.info(
                f"Message card visible after show(): {self.message_card.isVisible()}"
            )
            if message_count == 1:
                self.message_count_label.setText("הודעה חדשה")
            else:
                self.message_count_label.setText(f"{message_count} הודעות")

            # Update button text
            if message_count == 1:
                self.view_messages_button.setText("👁️ צפה בהודעה")
            else:
                self.view_messages_button.setText("👁️ צפה בהודעות")
        else:
            logger.error("Message card not found!")

        logger.info(f"Message card updated with {message_count} messages")

    def show_message_modal(self):
        """Show the message modal with pending messages"""
        logger.info(
            f"show_message_modal called with {len(self.pending_messages)} messages"
        )

        if not self.pending_messages:
            logger.warning("No pending messages to show")
            return

        # Close existing modal if any
        if self.message_modal:
            self.message_modal.close()

        # Create new modal with pending messages
        logger.info("Creating MessageModal...")
        self.message_modal = MessageModal(
            self.pending_messages, self.chat_service, self
        )
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
        if hasattr(self, "message_card"):
            self.message_card.hide()
        logger.info("All messages have been read")

    def cleanup(self):
        """Cleanup"""
        self.countdown_timer.stop()
        if self.chat_service:
            self.chat_service.cleanup()
        if self.message_modal:
            self.message_modal.close()

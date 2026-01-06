"""
Home Page - FROST Design System
Clean dashboard with stats and session controls.
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
    FrostCard,
    PageHeader,
    apply_shadow,
)
from ui.constants.ui_constants import (
    BorderRadius,
    Colors,
    Dimensions,
    Gradients,
    Spacing,
    Typography,
    UIStrings,
)
from utils.logger import get_logger


logger = get_logger(__name__)

# Optional modal imports
try:
    from ui.components.message_modal import MessageModal

    MODAL_AVAILABLE = True
except ImportError:
    MessageModal = None
    MODAL_AVAILABLE = False


class HomePage(QWidget):
    """Modern home dashboard with stats and session controls"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_user = auth_service.get_current_user()

        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)

        self.chat_service = ChatService(
            auth_service.firebase,
            self.current_user["uid"],
            auth_service.firebase.org_id,
        )

        self.message_modal = None
        self.pending_messages = []

        self.init_ui()
        self.countdown_timer.start(1000)
        self.start_message_listening()

        if self.chat_service:
            self.chat_service.messages_received.connect(self.handle_new_messages)

    def init_ui(self):
        """Build the UI"""
        self.setObjectName("homePage")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Page background
        self.setStyleSheet(f"background: {Colors.BG_PAGE};")

        # Center content
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        content.setMaximumWidth(1100)  # Wider to accommodate shadows
        content.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        layout.setSpacing(Spacing.LG)

        # Header
        header = PageHeader(UIStrings.HOME_TITLE, UIStrings.HOME_SUBTITLE)
        layout.addWidget(header)

        # Stats row
        stats = self._build_stats_row()
        layout.addWidget(stats)

        # Action card
        action = self._build_action_card()
        layout.addWidget(action)

        layout.addStretch()

        outer.addStretch()
        outer.addWidget(content)
        outer.addStretch()

        self.update_countdown()
        self.load_messages()

    def _build_stats_row(self) -> QWidget:
        """Build the statistics cards row"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container)
        # Add padding for shadows to render properly
        layout.setContentsMargins(Spacing.BASE, Spacing.BASE, Spacing.BASE, Spacing.LG)
        layout.setSpacing(Spacing.BASE)

        # Time card
        self.time_card = self._create_stat_card(
            "⏱️", UIStrings.TIME_REMAINING, "0:00:00", Colors.PRIMARY
        )
        layout.addWidget(self.time_card)

        # Print balance card
        balance = self.current_user.get("printBalance", 0.0)
        self.prints_card = self._create_stat_card(
            "🖨️", UIStrings.PRINT_BALANCE, f"{balance:.2f}₪", Colors.ACCENT
        )
        layout.addWidget(self.prints_card)

        # Messages card (hidden initially)
        self.message_card = self._create_message_card()
        self.message_card.hide()
        layout.addWidget(self.message_card)

        layout.addStretch()

        return container

    def _create_stat_card(
        self, icon: str, title: str, value: str, color: str
    ) -> QFrame:
        """Create a statistics card"""
        card = QFrame()
        card.setFixedSize(260, 120)
        card.setStyleSheet(
            f"""
            QFrame {{
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.XL}px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """
        )
        apply_shadow(card, "md")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.LG, Spacing.BASE, Spacing.LG, Spacing.BASE)
        layout.setSpacing(Spacing.XS)

        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(Spacing.SM)

        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont(Typography.FONT_FAMILY, 18))
        header_layout.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setFont(
            QFont(Typography.FONT_FAMILY, Typography.SIZE_SM, Typography.WEIGHT_MEDIUM)
        )
        title_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; border: none;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        layout.addWidget(header)

        # Value
        value_lbl = QLabel(value)
        value_lbl.setObjectName("timeValue" if "זמן" in title else "printValue")
        value_lbl.setFont(
            QFont(Typography.FONT_FAMILY, Typography.SIZE_2XL, Typography.WEIGHT_BOLD)
        )
        value_lbl.setStyleSheet(f"color: {color}; border: none;")
        layout.addWidget(value_lbl)

        layout.addStretch()
        return card

    def _create_message_card(self) -> QFrame:
        """Create the messages notification card"""
        card = QFrame()
        card.setObjectName("messageNotificationCard")
        card.setFixedSize(280, 160)  # Increased size for better visibility
        card.setStyleSheet(
            f"""
            QFrame {{
                background: {Colors.WHITE};
                border: 2px solid {Colors.WARNING};
                border-radius: {BorderRadius.XL}px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """
        )
        apply_shadow(card, "md")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.BASE)

        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(Spacing.SM)

        icon_lbl = QLabel("💬")
        icon_lbl.setFont(QFont(Typography.FONT_FAMILY, 22))
        header_layout.addWidget(icon_lbl)

        title_lbl = QLabel(UIStrings.NEW_MESSAGES)
        title_lbl.setFont(
            QFont(
                Typography.FONT_FAMILY, Typography.SIZE_BASE, Typography.WEIGHT_SEMIBOLD
            )
        )
        title_lbl.setStyleSheet(f"color: {Colors.WARNING_DARK};")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        layout.addWidget(header)

        # Count
        self.message_count_label = QLabel("0 הודעות")
        self.message_count_label.setFont(
            QFont(
                Typography.FONT_FAMILY, Typography.SIZE_LG, Typography.WEIGHT_SEMIBOLD
            )
        )
        self.message_count_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(self.message_count_label)

        # View button - more prominent
        self.view_messages_button = QPushButton("📬 צפה בהודעות")
        self.view_messages_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_messages_button.clicked.connect(self.show_message_modal)
        self.view_messages_button.setFixedHeight(40)
        self.view_messages_button.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.WARNING}, stop:1 {Colors.WARNING_DARK});
                color: {Colors.WHITE};
                border: none;
                border-radius: {BorderRadius.LG}px;
                padding: 10px 16px;
                font-size: {Typography.SIZE_BASE}px;
                font-weight: {Typography.WEIGHT_BOLD};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.WARNING_HOVER}, stop:1 {Colors.WARNING});
            }}
        """
        )
        layout.addWidget(self.view_messages_button)

        return card

    def _build_action_card(self) -> QFrame:
        """Build the main action card"""
        card = QFrame()
        card.setStyleSheet(
            f"""
            QFrame {{
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.XXL}px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """
        )
        apply_shadow(card, "lg")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.XXL, Spacing.XL, Spacing.XXL, Spacing.XL)
        layout.setSpacing(Spacing.LG)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Welcome text
        name = self.current_user.get("firstName", "משתמש")
        self.welcome_label = QLabel(f"👋 שלום, {name}!")
        self.welcome_label.setFont(
            QFont(Typography.FONT_FAMILY, Typography.SIZE_2XL, Typography.WEIGHT_BOLD)
        )
        self.welcome_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.welcome_label)

        # Instructions
        self.instruction = QLabel("מוכן להתחיל? לחץ על הכפתור למטה")
        self.instruction.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_BASE))
        self.instruction.setStyleSheet(
            f"""
            color: {Colors.TEXT_SECONDARY};
            background: {Colors.GRAY_50};
            padding: {Spacing.MD}px {Spacing.LG}px;
            border-radius: {BorderRadius.MD}px;
        """
        )
        self.instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.instruction)

        layout.addSpacing(Spacing.SM)

        # Start button
        self.start_btn = ActionButton(f"🚀  {UIStrings.START_SESSION}", "primary", "xl")
        self.start_btn.setMinimumWidth(280)
        self.start_btn.clicked.connect(self.handle_start_session)
        layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return card

    def _is_session_active(self) -> bool:
        """Check if a session is currently active"""
        try:
            main_window = self.parent().parent().parent()
            if hasattr(main_window, "session_service"):
                return main_window.session_service.is_session_active()
        except Exception:
            pass
        return False

    def update_countdown(self):
        """Update time display"""
        remaining = self.current_user.get("remainingTime", 0)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        time_str = f"{hours}:{minutes:02d}:{seconds:02d}"

        # Update time card
        time_value = self.time_card.findChild(QLabel, "timeValue")
        if time_value:
            time_value.setText(time_str)

            # Color based on time
            if remaining <= 0:
                color = Colors.ERROR
            elif remaining < 300:
                color = Colors.ERROR
            elif remaining < 1800:
                color = Colors.WARNING
            else:
                color = Colors.PRIMARY

            time_value.setStyleSheet(
                f"""
                color: {color};
                font-size: {Typography.SIZE_2XL}px;
                font-weight: {Typography.WEIGHT_BOLD};
            """
            )

        # Check if session is active
        session_active = self._is_session_active()

        # Update button state based on session and remaining time
        if session_active:
            # Session is active - show "Return to session" button
            self.start_btn.setEnabled(True)
            self.start_btn.setText("🔙  חזור להפעלה")
            self.instruction.setText("יש לך הפעלה פעילה. לחץ לחזור לטיימר.")
            self.instruction.setStyleSheet(
                f"""
                color: {Colors.PRIMARY_DARK};
                background: {Colors.PRIMARY_LIGHT};
                padding: {Spacing.MD}px {Spacing.LG}px;
                border-radius: {BorderRadius.MD}px;
            """
            )
        elif remaining <= 0:
            self.start_btn.setEnabled(False)
            self.start_btn.setText("⏸  אין זמן זמין")
            self.instruction.setText("אין לך זמן נותר. רכוש חבילה כדי להמשיך.")
            self.instruction.setStyleSheet(
                f"""
                color: {Colors.ERROR_DARK};
                background: {Colors.ERROR_LIGHT};
                padding: {Spacing.MD}px {Spacing.LG}px;
                border-radius: {BorderRadius.MD}px;
            """
            )
        else:
            self.start_btn.setEnabled(True)
            self.start_btn.setText(f"🚀  {UIStrings.START_SESSION}")
            self.instruction.setText("מוכן להתחיל? לחץ על הכפתור למטה")
            self.instruction.setStyleSheet(
                f"""
                color: {Colors.TEXT_SECONDARY};
                background: {Colors.GRAY_50};
                padding: {Spacing.MD}px {Spacing.LG}px;
                border-radius: {BorderRadius.MD}px;
            """
            )

    def refresh_user_data(self):
        """Refresh user data"""
        self.current_user = self.auth_service.get_current_user()
        if self.current_user:
            self.update_countdown()
            self.update_prints_display()
            # Update welcome message with new user's name
            name = self.current_user.get("firstName", "משתמש")
            self.welcome_label.setText(f"👋 שלום, {name}!")

    def update_prints_display(self):
        """Update prints balance display"""
        if not self.current_user:
            return

        balance = self.current_user.get("printBalance", 0.0)
        print_value = self.prints_card.findChild(QLabel, "printValue")
        if print_value:
            print_value.setText(f"{balance:.2f}₪")

    def clear_user_data(self):
        """Clear user data on logout"""
        self.current_user = None
        # Reset displays to default values
        time_value = self.time_card.findChild(QLabel, "timeValue")
        if time_value:
            time_value.setText("0:00:00")
        print_value = self.prints_card.findChild(QLabel, "printValue")
        if print_value:
            print_value.setText("0.00₪")
        # Reset welcome message
        if hasattr(self, "welcome_label"):
            self.welcome_label.setText("👋 שלום!")

    def handle_start_session(self):
        """Start session or return to active session"""
        main_window = self.parent().parent().parent()

        # If session is already active, just minimize back to the floating timer
        if self._is_session_active():
            logger.info("Session already active, returning to floating timer")
            main_window.showMinimized()
            return

        # Otherwise, start a new session
        remaining = self.current_user.get("remainingTime", 0)
        if remaining <= 0:
            return
        main_window.start_user_session(remaining)

    def start_message_listening(self):
        """Start listening for messages"""
        if self.chat_service and not self.chat_service.is_listening:
            self.chat_service.start_listening()

    def load_messages(self):
        """Load initial messages"""
        if self.chat_service:
            result = self.chat_service.get_unread_messages(use_cache=False)
            if result.get("success"):
                messages = result.get("messages", [])
                self.pending_messages = messages
                if messages:
                    self.show_message_notification(len(messages))

    def handle_new_messages(self, result):
        """Handle new messages"""
        if result.get("success"):
            messages = result.get("messages", [])
            self.pending_messages = messages
            if messages:
                self.show_message_notification(len(messages))

    def show_message_notification(self, count):
        """Show message notification"""
        if count <= 0:
            self.message_card.hide()
            return

        self.message_card.show()
        text = "הודעה חדשה" if count == 1 else f"{count} הודעות"
        self.message_count_label.setText(text)

    def show_message_modal(self):
        """Show message modal"""
        if not self.pending_messages or not MODAL_AVAILABLE:
            return

        if self.message_modal:
            self.message_modal.close()

        self.message_modal = MessageModal(
            self.pending_messages, self.chat_service, self
        )
        self.message_modal.message_read.connect(self.on_message_read)
        self.message_modal.all_messages_read.connect(self.on_all_messages_read)
        self.message_modal.show_animated()

        QTimer.singleShot(500, lambda: self._focus_modal())

    def _focus_modal(self):
        if self.message_modal:
            self.message_modal.raise_()
            self.message_modal.activateWindow()

    def on_message_read(self, message_id):
        """Handle message read"""
        pass

    def on_all_messages_read(self):
        """Handle all messages read"""
        self.pending_messages = []
        self.message_card.hide()

    def cleanup(self):
        """Cleanup"""
        from utils.logger import get_logger

        logger = get_logger(__name__)
        logger.debug("HomePage.cleanup() called")

        logger.debug("HomePage: stopping countdown timer...")
        self.countdown_timer.stop()
        logger.debug("HomePage: countdown timer stopped")

        if self.chat_service:
            logger.debug("HomePage: cleaning up chat service...")
            self.chat_service.cleanup()
            logger.debug("HomePage: chat service cleaned up")
        else:
            logger.debug("HomePage: no chat service to cleanup")

        if self.message_modal:
            logger.debug("HomePage: closing message modal...")
            self.message_modal.close()
            logger.debug("HomePage: message modal closed")
        else:
            logger.debug("HomePage: no message modal to close")

        logger.debug("HomePage.cleanup() completed")

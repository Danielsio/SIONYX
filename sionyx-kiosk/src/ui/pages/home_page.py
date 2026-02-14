"""
Home Page - FROST Design System
Clean dashboard with stats and session controls.
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from services.chat_service import ChatService
from services.operating_hours_service import OperatingHoursService
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

        # Operating hours service
        self.operating_hours_service = OperatingHoursService(auth_service.firebase)
        self.operating_hours_service.load_settings()

        self.message_modal = None
        self.pending_messages = []
        self.stat_cards = []
        self._stats_reflow_timer = QTimer(self)
        self._stats_reflow_timer.setSingleShot(True)
        self._stats_reflow_timer.timeout.connect(self._layout_stats_grid)

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
        self.setStyleSheet(
            f"""
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.BG_PAGE},
                stop:1 {Colors.GRAY_100}
            );
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.LG)
        layout.setSpacing(Spacing.LG)

        # Header
        header = PageHeader(UIStrings.HOME_TITLE, UIStrings.HOME_SUBTITLE)
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(header)

        # Stats grid
        self.stats_container = QWidget()
        self.stats_container.setStyleSheet("background: transparent;")
        self.stats_layout = QGridLayout(self.stats_container)
        self.stats_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        self.stats_layout.setHorizontalSpacing(Spacing.LG)
        self.stats_layout.setVerticalSpacing(Spacing.LG)
        layout.addWidget(self.stats_container)
        self._build_stats_row()

        # Action card
        action = self._build_action_card()
        layout.addWidget(action)

        layout.addStretch()

        self.update_countdown()
        self.load_messages()

    def _build_stats_row(self) -> QWidget:
        """Build the statistics cards list"""
        self.stat_cards = []

        # Time card
        self.time_card = self._create_stat_card(
            "◉", UIStrings.TIME_REMAINING, "0:00:00", Colors.PRIMARY
        )
        self.stat_cards.append(self.time_card)

        # Print balance card
        balance = self.current_user.get("printBalance", 0.0)
        self.prints_card = self._create_stat_card(
            "◉", UIStrings.PRINT_BALANCE, f"{balance:.2f}₪", Colors.ACCENT
        )
        self.stat_cards.append(self.prints_card)

        # Messages card (hidden initially)
        self.message_card = self._create_message_card()
        self.message_card.hide()
        self.stat_cards.append(self.message_card)

        self._layout_stats_grid()
        return self.stats_container

    def _create_stat_card(
        self, icon: str, title: str, value: str, color: str
    ) -> QFrame:
        """Create a statistics card"""
        card = QFrame()
        card.setMaximumWidth(920)
        card.setMinimumWidth(240)
        card.setMinimumHeight(110)
        card.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        card.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.WHITE},
                    stop:1 {Colors.GRAY_50}
                );
                border: 1px solid {Colors.BORDER_LIGHT};
                border-top: 3px solid {color};
                border-radius: {BorderRadius.XL}px;
            }}
            QFrame:hover {{
                border-color: {color};
                background: {Colors.WHITE};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """
        )
        apply_shadow(card, "md")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.LG, Spacing.SM, Spacing.LG, Spacing.SM)
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
        card.setMinimumWidth(260)
        card.setMinimumHeight(160)
        card.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        )
        card.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.WHITE},
                    stop:1 {Colors.WARNING_LIGHT}
                );
                border: 2px solid {Colors.WARNING};
                border-radius: {BorderRadius.XL}px;
            }}
            QFrame:hover {{
                border-color: {Colors.WARNING_DARK};
                background: {Colors.WHITE};
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

        icon_lbl = QLabel("◉")
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
        self.view_messages_button = QPushButton("צפה בהודעות")
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
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        card.setMinimumHeight(180)
        card.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.WHITE},
                    stop:1 {Colors.PRIMARY_GHOST}
                );
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.XXL}px;
            }}
            QFrame:hover {{
                border-color: {Colors.PRIMARY};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """
        )
        apply_shadow(card, "lg")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        layout.setSpacing(Spacing.SM)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Welcome text
        name = self.current_user.get("firstName", "משתמש")
        self.welcome_label = QLabel(f"שלום, {name}")
        self.welcome_label.setFont(
            QFont(Typography.FONT_FAMILY, Typography.SIZE_3XL, Typography.WEIGHT_BOLD)
        )
        self.welcome_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.welcome_label)

        # Instructions
        self.instruction = QLabel("מוכן להתחיל? לחץ על הכפתור כדי להפעיל את הזמן שלך")
        self.instruction.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_BASE))
        self.instruction.setStyleSheet(
            f"""
            color: {Colors.TEXT_SECONDARY};
            background: rgba(99, 102, 241, 0.08);
            border: 1px solid rgba(99, 102, 241, 0.18);
            padding: {Spacing.MD}px {Spacing.LG}px;
            border-radius: {BorderRadius.MD}px;
        """
        )
        self.instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction.setWordWrap(True)
        self.instruction.setMinimumHeight(64)
        self.instruction.setMinimumWidth(420)
        self.instruction.setMaximumWidth(520)
        layout.addWidget(self.instruction)

        # Start button
        self.start_btn = ActionButton(UIStrings.START_SESSION, "primary", "xl")
        self.start_btn.setMinimumWidth(280)
        self.start_btn.clicked.connect(self.handle_start_session)
        self.start_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )

        layout.addWidget(
            self.start_btn,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )

        return card

    def resizeEvent(self, event):
        """Reflow stats on resize"""
        super().resizeEvent(event)
        if self.stat_cards:
            self._stats_reflow_timer.start(120)

    def _layout_stats_grid(self):
        """Lay out stats based on available width"""
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if not self.stat_cards:
            return

        columns = self._calculate_stats_columns()
        row = 0
        col = 0
        for card in self.stat_cards:
            self.stats_layout.addWidget(card, row, col)
            col += 1
            if col >= columns:
                col = 0
                row += 1

        for i in range(columns):
            self.stats_layout.setColumnStretch(i, 1)

    def _calculate_stats_columns(self) -> int:
        """Determine number of stat columns based on available width"""
        available_width = max(1, self.stats_container.width() - Spacing.LG)
        card_min_width = 240
        max_columns = max(1, available_width // (card_min_width + Spacing.LG))
        return min(max_columns, max(1, len(self.stat_cards)))

    def _is_session_active(self) -> bool:
        """Check if a session is currently active"""
        try:
            main_window = self.parent().parent().parent()
            if hasattr(main_window, "session_service"):
                return main_window.session_service.is_session_active()
        except Exception as e:
            logger.debug(f"Session check failed: {e}")
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
            self.start_btn.setText("חזור להפעלה")
            self.instruction.setText("יש לך הפעלה פעילה. לחץ לחזור לטיימר.")
            self.instruction.setStyleSheet(
                f"""
                color: {Colors.PRIMARY_DARK};
                background: {Colors.PRIMARY_LIGHT};
                border: 1px solid rgba(99, 102, 241, 0.25);
                padding: {Spacing.MD}px {Spacing.LG}px;
                border-radius: {BorderRadius.MD}px;
            """
            )
        elif remaining <= 0:
            self.start_btn.setEnabled(False)
            self.start_btn.setText("אין זמן זמין")
            self.instruction.setText("אין לך זמן נותר. רכוש חבילה כדי להמשיך.")
            self.instruction.setStyleSheet(
                f"""
                color: {Colors.ERROR_DARK};
                background: {Colors.ERROR_LIGHT};
                border: 1px solid rgba(239, 68, 68, 0.25);
                padding: {Spacing.MD}px {Spacing.LG}px;
                border-radius: {BorderRadius.MD}px;
            """
            )
        else:
            self.start_btn.setEnabled(True)
            self.start_btn.setText(UIStrings.START_SESSION)
            self.instruction.setText("מוכן להתחיל? לחץ על הכפתור למטה")
            self.instruction.setStyleSheet(
                f"""
                color: {Colors.TEXT_SECONDARY};
                background: rgba(99, 102, 241, 0.08);
                border: 1px solid rgba(99, 102, 241, 0.18);
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
            self.welcome_label.setText(f"שלום, {name}")

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
            self.welcome_label.setText("שלום")

    def handle_start_session(self):
        """Start session or return to active session"""
        main_window = self.parent().parent().parent()

        # If session is already active, just minimize back to the floating timer
        if self._is_session_active():
            logger.info("Session already active, returning to floating timer")
            main_window.showMinimized()
            return

        # Check operating hours before starting new session
        is_within, reason = self.operating_hours_service.is_within_operating_hours()
        if not is_within:
            logger.warning(f"Cannot start session: outside operating hours - {reason}")
            self._show_operating_hours_error(reason)
            return

        # Otherwise, start a new session
        remaining = self.current_user.get("remainingTime", 0)
        if remaining <= 0:
            return
        main_window.start_user_session(remaining)

    def _show_operating_hours_error(self, reason: str):
        """Show error dialog for operating hours restriction"""
        from ui.components.alert_modal import AlertModal

        modal = AlertModal(
            title="שעות פעילות",
            message="לא ניתן להתחיל הפעלה כרגע",
            detail=reason,
            alert_type="warning",
            button_text="הבנתי",
            parent=self,
        )
        modal.show_animated()
        modal.exec()

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
            self._layout_stats_grid()
            return

        self.message_card.show()
        text = "הודעה חדשה" if count == 1 else f"{count} הודעות"
        self.message_count_label.setText(text)
        self._layout_stats_grid()

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

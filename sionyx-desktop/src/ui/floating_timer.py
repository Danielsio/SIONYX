"""
Floating Timer Overlay
Always-on-top timer displayed during sessions
"""

from PyQt6.QtCore import Qt, pyqtSignal
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

from src.utils.logger import get_logger


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
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(280, 140)  # Further increased height for perfect text display

        # Position at top-center of screen - stick to ceiling
        from PyQt6.QtWidgets import QApplication

        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - 280) // 2  # Center horizontally with new width
        y = 0  # Stick to the ceiling (top of screen)
        self.move(x, y)

        # Debug positioning
        logger.info(f"Screen size: {screen.width()}x{screen.height()}")
        logger.info(f"Timer positioned at: {x}, {y}")
        logger.info("Timer size: 280x140")

        # Main container
        self.container = QWidget()
        self.container.setObjectName("timerContainer")

        # Main horizontal layout
        main_layout = QHBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setStretch(0, 0)  # Left section fixed width
        main_layout.setStretch(1, 1)  # Right section takes remaining space

        # Left section - Exit button and printer icon
        left_section = QFrame()
        left_section.setObjectName("leftSection")
        left_section.setFixedWidth(90)  # Increased width to prevent יציאה button cutoff

        left_layout = QVBoxLayout(left_section)
        left_layout.setContentsMargins(14, 14, 14, 14)  # Increased padding
        left_layout.setSpacing(10)  # Increased spacing
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Exit button
        self.exit_button = QPushButton("יציאה")
        self.exit_button.setObjectName("exitButton")
        self.exit_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.exit_button.setFixedHeight(32)
        self.exit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_button.clicked.connect(self.return_clicked.emit)

        # Printer icon area
        self.printer_icon = QLabel("🖨️")
        self.printer_icon.setObjectName("printerIcon")
        self.printer_icon.setFont(QFont("Segoe UI", 16))
        self.printer_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.printer_icon.setFixedHeight(40)

        left_layout.addWidget(self.exit_button)
        left_layout.addWidget(self.printer_icon)

        # Right section - Time information
        right_section = QFrame()
        right_section.setObjectName("rightSection")
        right_section.setMinimumWidth(
            180
        )  # Further reduced minimum width for more compact design

        right_layout = QVBoxLayout(right_section)
        right_layout.setContentsMargins(
            12, 20, 12, 20
        )  # Further increased vertical padding for perfect text fit
        right_layout.setSpacing(
            10
        )  # Increased spacing between elements for better text fit
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Time remaining row
        time_remaining_row = QHBoxLayout()
        time_remaining_row.setSpacing(8)
        time_remaining_row.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.time_remaining_value = QLabel("00:00:00")
        self.time_remaining_value.setObjectName("timeRemainingValue")
        self.time_remaining_value.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.time_remaining_value.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.time_remaining_label = QLabel("זמן שנותר")
        self.time_remaining_label.setObjectName("timeRemainingLabel")
        self.time_remaining_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.time_remaining_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        time_remaining_row.addWidget(self.time_remaining_value)
        time_remaining_row.addWidget(self.time_remaining_label)

        # Usage time row
        usage_time_row = QHBoxLayout()
        usage_time_row.setSpacing(8)
        usage_time_row.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.usage_time_value = QLabel("00:00:00")
        self.usage_time_value.setObjectName("usageTimeValue")
        self.usage_time_value.setFont(QFont("Segoe UI", 14))
        self.usage_time_value.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.usage_time_label = QLabel("זמן שימוש")
        self.usage_time_label.setObjectName("usageTimeLabel")
        self.usage_time_label.setFont(QFont("Segoe UI", 14))
        self.usage_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        usage_time_row.addWidget(self.usage_time_value)
        usage_time_row.addWidget(self.usage_time_label)

        # Print balance row
        print_balance_row = QHBoxLayout()
        print_balance_row.setSpacing(8)
        print_balance_row.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.print_balance_value = QLabel("0₪")
        self.print_balance_value.setObjectName("printBalanceValue")
        self.print_balance_value.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.print_balance_value.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.print_balance_label = QLabel("יתרת הדפסות")
        self.print_balance_label.setObjectName("printBalanceLabel")
        self.print_balance_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.print_balance_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        print_balance_row.addWidget(self.print_balance_value)
        print_balance_row.addWidget(self.print_balance_label)

        # My Account button
        self.account_button = QPushButton("החשבון שלי")
        self.account_button.setObjectName("accountButton")
        self.account_button.setFont(QFont("Segoe UI", 12))
        self.account_button.setFixedHeight(30)
        self.account_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.account_button.clicked.connect(self.return_clicked.emit)

        right_layout.addLayout(time_remaining_row)
        right_layout.addLayout(usage_time_row)
        right_layout.addLayout(print_balance_row)
        right_layout.addStretch()
        right_layout.addWidget(self.account_button)

        # Add sections to main layout
        main_layout.addWidget(left_section)
        main_layout.addWidget(right_section)

        # Main layout
        main_widget_layout = QVBoxLayout(self)
        main_widget_layout.setContentsMargins(0, 0, 0, 0)
        main_widget_layout.addWidget(self.container)

        # Apply professional styling
        self.apply_professional_styles()

        # Enable mouse tracking for hover
        self.setMouseTracking(True)
        self.container.setMouseTracking(True)

    def update_time(self, seconds: int):
        """Update time display"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        # Update time remaining display
        time_str = f"{hours:02d}:{minutes:02d}:{secs:02d}"
        self.time_remaining_value.setText(time_str)

        # Update warning states
        if seconds <= 60:
            if not self.is_critical:
                self.set_critical_mode()
        elif seconds <= 300:
            if not self.is_warning:
                self.set_warning_mode()

    def update_usage_time(self, seconds: int):
        """Update usage time display"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        usage_str = f"{hours:02d}:{minutes:02d}:{secs:02d}"
        self.usage_time_value.setText(usage_str)

    def update_print_balance(self, balance: float):
        """Update print balance display"""
        self.print_balance_value.setText(f"{balance:.2f}₪")

    def set_warning_mode(self):
        """Set warning appearance (5 min remaining)"""
        self.is_warning = True
        self.apply_warning_styles()
        logger.warning("Timer in warning mode")

    def set_critical_mode(self):
        """Set critical appearance (1 min remaining)"""
        self.is_critical = True
        self.apply_critical_styles()

        # Start pulse animation
        self.pulse_animation()
        logger.error("Timer in critical mode")

    def pulse_animation(self):
        """Pulse animation for critical state"""
        # Simple scale animation
        # Could be enhanced with QPropertyAnimation

    def set_offline_mode(self, offline: bool):
        """Show offline indicator"""
        if offline:
            self.time_remaining_value.setText("⚠ Offline")
        else:
            # Reset to normal state
            self.is_warning = False
            self.is_critical = False
            self.apply_professional_styles()

    def apply_professional_styles(self):
        """Apply professional dark theme styling to match the design"""
        self.container.setStyleSheet(
            """
            #timerContainer {
                background-color: #363636;
                border: 1px solid #555555;
                border-radius: 8px;
            }

            #leftSection {
                background-color: #363636;
                border-right: 1px solid #555555;
            }

            #rightSection {
                background-color: #363636;
            }

            #exitButton {
                background-color: #FF0000;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 12px;
            }

            #exitButton:hover {
                background-color: #FF3333;
            }

            #exitButton:pressed {
                background-color: #CC0000;
            }

            #printerIcon {
                color: #FFFFFF;
                background-color: #363636;
                border: 1px solid #AAAAAA;
                border-radius: 4px;
                padding: 8px;
            }

            #timeRemainingLabel {
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
            }

            #timeRemainingValue {
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
            }

            #usageTimeLabel {
                color: #CCCCCC;
                font-size: 14px;
            }

            #usageTimeValue {
                color: #CCCCCC;
                font-size: 14px;
            }

            #printBalanceLabel {
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
            }

            #printBalanceValue {
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
            }

            #accountButton {
                background-color: #363636;
                color: #FFFFFF;
                border: 1px solid #AAAAAA;
                border-radius: 4px;
                font-size: 12px;
                padding: 6px 12px;
            }

            #accountButton:hover {
                background-color: #4A4A4A;
            }

            #accountButton:pressed {
                background-color: #2A2A2A;
            }
        """
        )

        # Add professional shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)

    def apply_warning_styles(self):
        """Apply warning styles (5 min remaining) - orange accent"""
        self.container.setStyleSheet(
            """
            #timerContainer {
                background-color: #4A3A00;
                border: 1px solid #FFA500;
                border-radius: 8px;
            }

            #leftSection {
                background-color: #4A3A00;
                border-right: 1px solid #FFA500;
            }

            #rightSection {
                background-color: #4A3A00;
            }

            #exitButton {
                background-color: #FF0000;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 12px;
            }

            #exitButton:hover {
                background-color: #FF3333;
            }

            #exitButton:pressed {
                background-color: #CC0000;
            }

            #printerIcon {
                color: #FFFFFF;
                background-color: #4A3A00;
                border: 1px solid #FFA500;
                border-radius: 4px;
                padding: 8px;
            }

            #timeRemainingLabel {
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
            }

            #timeRemainingValue {
                color: #FFA500;
                font-weight: bold;
                font-size: 16px;
            }

            #usageTimeLabel {
                color: #CCCCCC;
                font-size: 14px;
            }

            #usageTimeValue {
                color: #CCCCCC;
                font-size: 14px;
            }

            #printBalanceLabel {
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
            }

            #printBalanceValue {
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
            }

            #accountButton {
                background-color: #4A3A00;
                color: #FFFFFF;
                border: 1px solid #FFA500;
                border-radius: 4px;
                font-size: 9px;
                padding: 6px 12px;
            }

            #accountButton:hover {
                background-color: #5A4A00;
            }

            #accountButton:pressed {
                background-color: #3A2A00;
            }
        """
        )

    def apply_critical_styles(self):
        """Apply critical styles (1 min remaining) - red accent"""
        self.container.setStyleSheet(
            """
            #timerContainer {
                background-color: #4A0000;
                border: 1px solid #FF0000;
                border-radius: 8px;
            }

            #leftSection {
                background-color: #4A0000;
                border-right: 1px solid #FF0000;
            }

            #rightSection {
                background-color: #4A0000;
            }

            #exitButton {
                background-color: #FF0000;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 12px;
            }

            #exitButton:hover {
                background-color: #FF3333;
            }

            #exitButton:pressed {
                background-color: #CC0000;
            }

            #printerIcon {
                color: #FFFFFF;
                background-color: #4A0000;
                border: 1px solid #FF0000;
                border-radius: 4px;
                padding: 8px;
            }

            #timeRemainingLabel {
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
            }

            #timeRemainingValue {
                color: #FF0000;
                font-weight: bold;
                font-size: 16px;
            }

            #usageTimeLabel {
                color: #CCCCCC;
                font-size: 14px;
            }

            #usageTimeValue {
                color: #CCCCCC;
                font-size: 14px;
            }

            #printBalanceLabel {
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
            }

            #printBalanceValue {
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
            }

            #accountButton {
                background-color: #4A0000;
                color: #FFFFFF;
                border: 1px solid #FF0000;
                border-radius: 4px;
                font-size: 9px;
                padding: 6px 12px;
            }

            #accountButton:hover {
                background-color: #5A0000;
            }

            #accountButton:pressed {
                background-color: #3A0000;
            }
        """
        )

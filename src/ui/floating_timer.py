"""
Floating Timer Overlay
Always-on-top timer displayed during sessions
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGraphicsDropShadowEffect, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from utils.logger import get_logger

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
        self.setFixedSize(320, 120)  # Wider to accommodate two-column layout

        # Position at top-right corner
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 340, 20)

        # Main container
        self.container = QWidget()
        self.container.setObjectName("timerContainer")

        # Main horizontal layout
        main_layout = QHBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left section - Exit button and printer icon
        left_section = QFrame()
        left_section.setObjectName("leftSection")
        left_section.setFixedWidth(80)
        
        left_layout = QVBoxLayout(left_section)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Exit button
        self.exit_button = QPushButton("יציאה")
        self.exit_button.setObjectName("exitButton")
        self.exit_button.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
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
        
        right_layout = QVBoxLayout(right_section)
        right_layout.setContentsMargins(16, 12, 16, 12)
        right_layout.setSpacing(4)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Time remaining
        self.time_remaining_label = QLabel("זמן שנותר")
        self.time_remaining_label.setObjectName("timeRemainingLabel")
        self.time_remaining_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.time_remaining_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.time_remaining_value = QLabel("07:33:37")
        self.time_remaining_value.setObjectName("timeRemainingValue")
        self.time_remaining_value.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.time_remaining_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Usage time
        self.usage_time_label = QLabel("זמן שימוש")
        self.usage_time_label.setObjectName("usageTimeLabel")
        self.usage_time_label.setFont(QFont("Segoe UI", 9))
        self.usage_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.usage_time_value = QLabel("00:00:03")
        self.usage_time_value.setObjectName("usageTimeValue")
        self.usage_time_value.setFont(QFont("Segoe UI", 11))
        self.usage_time_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Print balance
        self.print_balance_label = QLabel("יתרת הדפסות")
        self.print_balance_label.setObjectName("printBalanceLabel")
        self.print_balance_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.print_balance_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.print_balance_value = QLabel("0₪")
        self.print_balance_value.setObjectName("printBalanceValue")
        self.print_balance_value.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.print_balance_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        # My Account button
        self.account_button = QPushButton("החשבון שלי")
        self.account_button.setObjectName("accountButton")
        self.account_button.setFont(QFont("Segoe UI", 9))
        self.account_button.setFixedHeight(28)
        self.account_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.account_button.clicked.connect(self.return_clicked.emit)

        right_layout.addWidget(self.time_remaining_label)
        right_layout.addWidget(self.time_remaining_value)
        right_layout.addWidget(self.usage_time_label)
        right_layout.addWidget(self.usage_time_value)
        right_layout.addWidget(self.print_balance_label)
        right_layout.addWidget(self.print_balance_value)
        right_layout.addStretch()
        right_layout.addWidget(self.account_button)

        # Add sections to main layout
        main_layout.addWidget(left_section)
        main_layout.addWidget(right_section)

        # Main layout
        main_widget_layout = QVBoxLayout(self)
        main_widget_layout.setContentsMargins(0, 0, 0, 0)
        main_widget_layout.addWidget(self.container)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
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

    def update_print_balance(self, balance: int):
        """Update print balance display"""
        self.print_balance_value.setText(f"{balance}₪")

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
        pass

    def set_offline_mode(self, offline: bool):
        """Show offline indicator"""
        if offline:
            self.time_remaining_value.setText("⚠ Offline")
            self.time_remaining_value.setStyleSheet("color: #FFA500;")
        else:
            # Reset to normal state
            self.is_warning = False
            self.is_critical = False
            self.apply_styles()

    def apply_styles(self):
        """Apply base styles"""
        self.container.setStyleSheet("""
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
            }
            
            #timeRemainingLabel { 
                color: #FFFFFF; 
                font-weight: bold; 
            }
            
            #timeRemainingValue { 
                color: #FFFFFF; 
                font-weight: bold; 
            }
            
            #usageTimeLabel { 
                color: #CCCCCC; 
            }
            
            #usageTimeValue { 
                color: #CCCCCC; 
            }
            
            #printBalanceLabel { 
                color: #FFFFFF; 
                font-weight: bold; 
            }
            
            #printBalanceValue { 
                color: #FFFFFF; 
                font-weight: bold; 
            }
            
            #accountButton { 
                background-color: #363636; 
                color: #FFFFFF; 
                border: 1px solid #AAAAAA; 
                border-radius: 4px; 
            }
            
            #accountButton:hover { 
                background-color: #4A4A4A; 
            }
            
            #accountButton:pressed { 
                background-color: #2A2A2A; 
            }
        """)

    def apply_warning_styles(self):
        """Apply warning styles (5 min remaining)"""
        self.container.setStyleSheet("""
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
            }
            
            #timeRemainingLabel { 
                color: #FFFFFF; 
                font-weight: bold; 
            }
            
            #timeRemainingValue { 
                color: #FFA500; 
                font-weight: bold; 
            }
            
            #usageTimeLabel { 
                color: #CCCCCC; 
            }
            
            #usageTimeValue { 
                color: #CCCCCC; 
            }
            
            #printBalanceLabel { 
                color: #FFFFFF; 
                font-weight: bold; 
            }
            
            #printBalanceValue { 
                color: #FFFFFF; 
                font-weight: bold; 
            }
            
            #accountButton { 
                background-color: #4A3A00; 
                color: #FFFFFF; 
                border: 1px solid #FFA500; 
                border-radius: 4px; 
            }
            
            #accountButton:hover { 
                background-color: #5A4A00; 
            }
            
            #accountButton:pressed { 
                background-color: #3A2A00; 
            }
        """)

    def apply_critical_styles(self):
        """Apply critical styles (1 min remaining)"""
        self.container.setStyleSheet("""
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
            }
            
            #timeRemainingLabel { 
                color: #FFFFFF; 
                font-weight: bold; 
            }
            
            #timeRemainingValue { 
                color: #FF0000; 
                font-weight: bold; 
            }
            
            #usageTimeLabel { 
                color: #CCCCCC; 
            }
            
            #usageTimeValue { 
                color: #CCCCCC; 
            }
            
            #printBalanceLabel { 
                color: #FFFFFF; 
                font-weight: bold; 
            }
            
            #printBalanceValue { 
                color: #FFFFFF; 
                font-weight: bold; 
            }
            
            #accountButton { 
                background-color: #4A0000; 
                color: #FFFFFF; 
                border: 1px solid #FF0000; 
                border-radius: 4px; 
            }
            
            #accountButton:hover { 
                background-color: #5A0000; 
            }
            
            #accountButton:pressed { 
                background-color: #3A0000; 
            }
        """)
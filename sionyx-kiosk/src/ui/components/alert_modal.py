"""
Alert Modal Component
Beautiful, modern alert dialog with elegant animations
Premium floating card design
"""

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


# Alert types with colors and icons
ALERT_TYPES = {
    "warning": {
        "icon": "⚠️",
        "header_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F59E0B, stop:1 #D97706)",
        "icon_bg": "#FEF3C7",
        "icon_color": "#D97706",
        "button_bg": "#F59E0B",
        "button_hover": "#D97706",
        "glow_color": QColor(245, 158, 11, 100),
        "border_color": "#F59E0B",
    },
    "error": {
        "icon": "❌",
        "header_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF4444, stop:1 #DC2626)",
        "icon_bg": "#FEE2E2",
        "icon_color": "#DC2626",
        "button_bg": "#EF4444",
        "button_hover": "#DC2626",
        "glow_color": QColor(239, 68, 68, 100),
        "border_color": "#EF4444",
    },
    "info": {
        "icon": "ℹ️",
        "header_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #1D4ED8)",
        "icon_bg": "#DBEAFE",
        "icon_color": "#1D4ED8",
        "button_bg": "#3B82F6",
        "button_hover": "#2563EB",
        "glow_color": QColor(59, 130, 246, 100),
        "border_color": "#3B82F6",
    },
    "success": {
        "icon": "✅",
        "header_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #059669)",
        "icon_bg": "#D1FAE5",
        "icon_color": "#059669",
        "button_bg": "#10B981",
        "button_hover": "#059669",
        "glow_color": QColor(16, 185, 129, 100),
        "border_color": "#10B981",
    },
}


class AlertModal(QDialog):
    """
    Premium floating card modal for alerts
    Clean design with colored glow effect
    """

    def __init__(
        self,
        title: str,
        message: str,
        detail: str = "",
        alert_type: str = "info",
        button_text: str = "הבנתי",
        parent=None,
    ):
        super().__init__(parent)
        self.title_text = title
        self.message_text = message
        self.detail_text = detail
        self.alert_type = alert_type if alert_type in ALERT_TYPES else "info"
        self.button_text = button_text
        self.colors = ALERT_TYPES[self.alert_type]

        self.setup_ui()
        self.setup_animations()

    def setup_ui(self):
        """Setup premium floating card UI"""
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Fixed size with padding for shadow
        self.setFixedSize(520, 440)

        # Main container card
        self.container = QFrame(self)
        self.container.setObjectName("alertModalContainer")
        self.container.setGeometry(40, 30, 440, 380)

        # Premium colored glow shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(self.colors["glow_color"])
        self.container.setGraphicsEffect(shadow)

        # Container layout
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Build sections
        self.setup_header(container_layout)
        self.setup_content(container_layout)
        self.setup_footer(container_layout)
        self.apply_styles()

    def setup_header(self, layout):
        """Setup elegant header"""
        header = QFrame()
        header.setObjectName("alertHeader")
        header.setFixedHeight(70)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 0, 28, 0)
        header_layout.setSpacing(14)

        # Icon
        icon_label = QLabel(self.colors["icon"])
        icon_label.setFont(QFont("Segoe UI Emoji", 22))
        icon_label.setStyleSheet("background: transparent;")

        # Title
        title = QLabel(self.title_text)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addWidget(header)

    def setup_content(self, layout):
        """Setup content area"""
        content_frame = QFrame()
        content_frame.setObjectName("alertContent")

        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(32, 28, 32, 20)
        content_layout.setSpacing(18)

        # Centered icon
        icon_container = QFrame()
        icon_container.setFixedSize(80, 80)
        icon_container.setStyleSheet(
            f"""
            QFrame {{
                background: {self.colors['icon_bg']};
                border-radius: 40px;
                border: 3px solid white;
            }}
        """
        )

        icon_shadow = QGraphicsDropShadowEffect()
        icon_shadow.setBlurRadius(25)
        icon_shadow.setXOffset(0)
        icon_shadow.setYOffset(5)
        icon_shadow.setColor(self.colors["glow_color"])
        icon_container.setGraphicsEffect(icon_shadow)

        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        center_icon = QLabel(self.colors["icon"])
        center_icon.setFont(QFont("Segoe UI Emoji", 36))
        center_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_icon.setStyleSheet("background: transparent;")
        icon_layout.addWidget(center_icon)

        icon_row = QHBoxLayout()
        icon_row.addStretch()
        icon_row.addWidget(icon_container)
        icon_row.addStretch()
        content_layout.addLayout(icon_row)

        # Main message
        message_label = QLabel(self.message_text)
        message_label.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("color: #1E293B; background: transparent;")
        content_layout.addWidget(message_label)

        # Detail text
        if self.detail_text:
            detail_label = QLabel(self.detail_text)
            detail_label.setFont(QFont("Segoe UI", 15))
            detail_label.setWordWrap(True)
            detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            detail_label.setStyleSheet(
                f"""
                color: #475569;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FAFAFA, stop:1 #F1F5F9);
                border: 2px solid {self.colors['border_color']}40;
                border-radius: 14px;
                padding: 16px 20px;
            """
            )
            content_layout.addWidget(detail_label)

        content_layout.addStretch()
        layout.addWidget(content_frame, 1)

    def setup_footer(self, layout):
        """Setup footer with button"""
        footer = QFrame()
        footer.setObjectName("alertFooter")
        footer.setFixedHeight(85)

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(32, 16, 32, 22)

        footer_layout.addStretch()

        # Action button
        self.ok_button = QPushButton(self.button_text)
        self.ok_button.setObjectName("okButton")
        self.ok_button.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.ok_button.setFixedSize(160, 52)
        self.ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ok_button.clicked.connect(self.close_modal)

        footer_layout.addWidget(self.ok_button)
        footer_layout.addStretch()

        layout.addWidget(footer)

    def apply_styles(self):
        """Apply premium styling"""
        self.container.setStyleSheet(
            f"""
            QFrame#alertModalContainer {{
                background: white;
                border-radius: 28px;
                border: 2px solid {self.colors['border_color']};
            }}

            QFrame#alertHeader {{
                background: {self.colors['header_gradient']};
                border-radius: 26px 26px 0 0;
            }}

            QFrame#alertContent {{
                background: white;
            }}

            QFrame#alertFooter {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FAFAFA, stop:1 #F5F5F5);
                border-top: 1px solid #E5E7EB;
                border-radius: 0 0 26px 26px;
            }}

            QPushButton#okButton {{
                background: {self.colors['button_bg']};
                color: white;
                border: none;
                border-radius: 14px;
                font-weight: bold;
            }}
            QPushButton#okButton:hover {{
                background: {self.colors['button_hover']};
            }}
        """
        )

    def setup_animations(self):
        """Setup animations"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def close_modal(self):
        """Close with animation"""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        try:
            self.fade_animation.finished.disconnect(self.accept)
        except TypeError:
            pass  # Not connected yet
        self.fade_animation.finished.connect(self.accept)
        self.fade_animation.start()

    def show_animated(self):
        """Show centered with animation"""
        from PyQt6.QtWidgets import QApplication

        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

        self.setWindowOpacity(0.0)
        self.show()

        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

    def keyPressEvent(self, event):
        """Handle keyboard"""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape):
            self.close_modal()
        else:
            super().keyPressEvent(event)


def show_warning(title: str, message: str, detail: str = "", parent=None) -> None:
    """Show a warning alert"""
    modal = AlertModal(title, message, detail, "warning", parent=parent)
    modal.show_animated()
    modal.exec()


def show_error(title: str, message: str, detail: str = "", parent=None) -> None:
    """Show an error alert"""
    modal = AlertModal(title, message, detail, "error", parent=parent)
    modal.show_animated()
    modal.exec()


def show_info(title: str, message: str, detail: str = "", parent=None) -> None:
    """Show an info alert"""
    modal = AlertModal(title, message, detail, "info", parent=parent)
    modal.show_animated()
    modal.exec()


def show_success(title: str, message: str, detail: str = "", parent=None) -> None:
    """Show a success alert"""
    modal = AlertModal(title, message, detail, "success", parent=parent)
    modal.show_animated()
    modal.exec()

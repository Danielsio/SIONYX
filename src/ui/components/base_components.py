"""
Base UI Components - FROST Design System
Clean, modern, reusable components with consistent styling.
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

from ui.constants.ui_constants import (
    BorderRadius,
    Colors,
    Dimensions,
    Gradients,
    Shadows,
    Spacing,
    Typography,
    get_button_style,
    get_shadow,
)


def apply_shadow(widget: QWidget, level: str = "md"):
    """Apply consistent shadow to a widget for floating effect"""
    # Enhanced shadow configs for better floating appearance
    configs = {
        "sm": {"blur": 12, "y": 3, "color": "rgba(15, 23, 42, 0.08)"},
        "md": {"blur": 20, "y": 6, "color": "rgba(15, 23, 42, 0.10)"},
        "lg": {"blur": 28, "y": 10, "color": "rgba(15, 23, 42, 0.12)"},
        "xl": {"blur": 40, "y": 16, "color": "rgba(15, 23, 42, 0.15)"},
        "primary": {"blur": 24, "y": 8, "color": "rgba(99, 102, 241, 0.20)"},
    }
    config = configs.get(level, configs["md"])
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(config["blur"])
    shadow.setXOffset(0)
    shadow.setYOffset(config["y"])
    shadow.setColor(QColor(config["color"]))
    widget.setGraphicsEffect(shadow)


class FrostCard(QFrame):
    """
    Modern card component with subtle shadow and clean styling.
    The foundation for all card-based layouts.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.XL}px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QWidget {{
                background: transparent;
                border: none;
            }}
        """)
        apply_shadow(self, "md")


class StatCard(FrostCard):
    """
    Statistics display card with icon, label, and value.
    Used for showing time remaining, print balance, etc.
    """

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        color: str = Colors.PRIMARY,
        icon: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.color = color
        self.icon = icon
        self._build()

    def _build(self):
        self.setFixedSize(Dimensions.STAT_CARD_WIDTH, Dimensions.STAT_CARD_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.SM)

        # Header row with icon and title
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(Spacing.SM)

        if self.icon:
            icon_label = QLabel(self.icon)
            icon_label.setFont(QFont(Typography.FONT_FAMILY, 20))
            icon_label.setStyleSheet(f"color: {self.color};")
            header_layout.addWidget(icon_label)

        title_label = QLabel(self.title)
        title_label.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_SM, Typography.WEIGHT_MEDIUM))
        title_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)

        # Value
        self.value_label = QLabel(self.value)
        self.value_label.setObjectName("timeValue")
        self.value_label.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_3XL, Typography.WEIGHT_BOLD))
        self.value_label.setStyleSheet(f"color: {self.color};")
        layout.addWidget(self.value_label)

        layout.addStretch()


class ActionButton(QPushButton):
    """
    Styled button with multiple variants: primary, secondary, danger, ghost.
    """

    def __init__(
        self,
        text: str,
        variant: str = "primary",
        size: str = "md",
        parent=None,
    ):
        super().__init__(text, parent)
        self.variant = variant
        self.size = size
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(get_button_style(self.variant, self.size))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_BASE, Typography.WEIGHT_SEMIBOLD))


class PageHeader(QFrame):
    """
    Beautiful gradient page header with title and subtitle.
    """

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.title_text = title
        self.subtitle_text = subtitle
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {Gradients.HERO};
                border-radius: {BorderRadius.XL}px;
                border: none;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        apply_shadow(self, "primary")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        layout.setSpacing(Spacing.XS)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel(self.title_text)
        title.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_3XL, Typography.WEIGHT_BOLD))
        title.setStyleSheet(f"color: {Colors.WHITE}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        if self.subtitle_text:
            subtitle = QLabel(self.subtitle_text)
            subtitle.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_BASE, Typography.WEIGHT_NORMAL))
            subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.85); background: transparent;")
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(subtitle)


class LoadingSpinner(QWidget):
    """Simple loading indicator"""

    def __init__(self, message: str = "טוען...", parent=None):
        super().__init__(parent)
        self.message = message
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(Spacing.MD)

        spinner = QLabel("⏳")
        spinner.setFont(QFont(Typography.FONT_FAMILY, 32))
        spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinner.setStyleSheet(f"color: {Colors.PRIMARY};")
        layout.addWidget(spinner)

        text = QLabel(self.message)
        text.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_BASE))
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(text)


class EmptyState(QWidget):
    """Empty state placeholder with icon and message"""

    def __init__(
        self,
        icon: str = "📭",
        title: str = "אין נתונים",
        subtitle: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.icon = icon
        self.title_text = title
        self.subtitle_text = subtitle
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(Spacing.MD)
        layout.setContentsMargins(Spacing.XL, Spacing.XXL, Spacing.XL, Spacing.XXL)

        icon = QLabel(self.icon)
        icon.setFont(QFont(Typography.FONT_FAMILY, 48))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"color: {Colors.GRAY_300};")
        layout.addWidget(icon)

        title = QLabel(self.title_text)
        title.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_LG, Typography.WEIGHT_SEMIBOLD))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(title)

        if self.subtitle_text:
            subtitle = QLabel(self.subtitle_text)
            subtitle.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_BASE))
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
            subtitle.setWordWrap(True)
            layout.addWidget(subtitle)


class StatusBadge(QLabel):
    """Status indicator badge with color variants"""

    VARIANTS = {
        "completed": (Colors.SUCCESS_DARK, Colors.SUCCESS_LIGHT),
        "success": (Colors.SUCCESS_DARK, Colors.SUCCESS_LIGHT),
        "pending": (Colors.WARNING_DARK, Colors.WARNING_LIGHT),
        "warning": (Colors.WARNING_DARK, Colors.WARNING_LIGHT),
        "failed": (Colors.ERROR_DARK, Colors.ERROR_LIGHT),
        "error": (Colors.ERROR_DARK, Colors.ERROR_LIGHT),
        "active": (Colors.PRIMARY, Colors.PRIMARY_LIGHT),
        "info": (Colors.PRIMARY, Colors.PRIMARY_LIGHT),
    }

    def __init__(self, text: str, variant: str = "info", parent=None):
        super().__init__(text, parent)
        self.variant = variant
        self._setup_style()

    def _setup_style(self):
        text_color, bg_color = self.VARIANTS.get(
            self.variant, (Colors.TEXT_SECONDARY, Colors.GRAY_100)
        )
        self.setStyleSheet(f"""
            QLabel {{
                background: {bg_color};
                color: {text_color};
                border-radius: {BorderRadius.SM}px;
                padding: {Spacing.XS}px {Spacing.SM}px;
                font-size: {Typography.SIZE_SM}px;
                font-weight: {Typography.WEIGHT_SEMIBOLD};
            }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class Divider(QFrame):
    """Simple horizontal divider"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {Colors.BORDER_LIGHT};")


class IconButton(QPushButton):
    """Circular icon button"""

    def __init__(self, icon: str, size: int = 40, parent=None):
        super().__init__(icon, parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.GRAY_100};
                border: none;
                border-radius: {size // 2}px;
                font-size: {size // 2}px;
            }}
            QPushButton:hover {{
                background: {Colors.GRAY_200};
            }}
        """)


# Legacy compatibility aliases
BaseCard = FrostCard
HeaderSection = PageHeader


def get_shadow_effect(blur_radius: int = 16, y_offset: int = 4, color: str = "rgba(15, 23, 42, 0.12)"):
    """Legacy shadow function"""
    return {
        "blur_radius": blur_radius,
        "x_offset": 0,
        "y_offset": y_offset,
        "color": color,
    }

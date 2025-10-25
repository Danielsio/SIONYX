"""
Base UI Components - Reusable components to eliminate code duplication.

This module provides standardized, reusable UI components that follow
consistent styling and behavior patterns across the application.
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
    Shadows,
    Spacing,
    Typography,
    get_button_style,
    get_shadow_effect,
)


class BaseCard(QFrame):
    """Base card component with consistent styling and behavior"""

    def __init__(self, card_type: str = "default", parent=None):
        super().__init__(parent)
        self.card_type = card_type
        self.setup_base_style()
        self.setup_shadow()

    def setup_base_style(self):
        """Apply base card styling - use message card style for consistency"""
        self.setStyleSheet(
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

    def setup_shadow(self):
        """Apply standard shadow effect"""
        shadow_config = get_shadow_effect()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(shadow_config["blur_radius"])
        shadow.setXOffset(shadow_config["x_offset"])
        shadow.setYOffset(shadow_config["y_offset"])
        shadow.setColor(QColor(shadow_config["color"]))
        self.setGraphicsEffect(shadow)

    def setup_strong_shadow(self):
        """Apply stronger shadow effect for stat cards"""
        shadow_config = get_shadow_effect(
            Shadows.LARGE_BLUR, Shadows.Y_OFFSET_LARGE, Shadows.DARK
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(shadow_config["blur_radius"])
        shadow.setXOffset(shadow_config["x_offset"])
        shadow.setYOffset(shadow_config["y_offset"])
        shadow.setColor(QColor(shadow_config["color"]))
        self.setGraphicsEffect(shadow)


class StatCard(BaseCard):
    """Standardized statistics card component"""

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        color: str = Colors.PRIMARY,
        icon: str = "",
        parent=None,
    ):
        super().__init__("stat", parent)
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.color = color
        self.icon = icon

        self.setup_layout()
        self.setup_content()

    def setup_layout(self):
        """Setup card layout"""
        # Increased height to accommodate content properly
        self.setFixedSize(400, 200)  # Increased height for better content visibility

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 30, 25, 20)  # Match message card margins
        layout.setSpacing(12)  # Match message card spacing

        self.layout = layout

        # Apply same shadow as message card for consistency
        from ui.constants.ui_constants import Shadows, get_shadow_effect

        shadow_config = get_shadow_effect(
            Shadows.LARGE_BLUR, Shadows.Y_OFFSET_LARGE, Shadows.DARK
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(shadow_config["blur_radius"])
        shadow.setXOffset(shadow_config["x_offset"])
        shadow.setYOffset(shadow_config["y_offset"])
        shadow.setColor(QColor(shadow_config["color"]))
        self.setGraphicsEffect(shadow)

    def setup_content(self):
        """Setup card content"""
        # Icon and title row
        if self.icon:
            icon_title_row = self.create_icon_title_row()
            self.layout.addWidget(icon_title_row)

        # Value display
        value_label = self.create_value_label()
        self.layout.addWidget(value_label)

    def create_icon_title_row(self) -> QWidget:
        """Create icon and title row"""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)  # Match message card spacing

        # Icon - match message card styling
        icon_label = QLabel(self.icon)
        icon_label.setFont(QFont("Segoe UI", 24))  # Match message card icon size
        icon_label.setStyleSheet(f"color: {self.color};")

        # Title - match message card styling
        title_label = QLabel(self.title)
        title_label.setFont(
            QFont("Segoe UI", 16, QFont.Weight.Bold)
        )  # Match message card title
        title_label.setStyleSheet("color: #1E293B;")  # Match message card title color

        row_layout.addWidget(icon_label)
        row_layout.addWidget(title_label)
        row_layout.addStretch()

        return row

    def create_value_label(self) -> QLabel:
        """Create value label - match message card styling"""
        value_label = QLabel(self.value)
        value_label.setObjectName("timeValue")  # Set objectName for time updates
        value_label.setFont(
            QFont("Segoe UI", 14, QFont.Weight.Medium)
        )  # Match message card font
        value_label.setStyleSheet("color: #64748B;")  # Match message card color
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return value_label


class ActionButton(QPushButton):
    """Standardized action button component"""

    def __init__(
        self, text: str, button_type: str = "primary", size: str = "medium", parent=None
    ):
        super().__init__(text, parent)
        self.button_type = button_type
        self.size = size

        self.setup_style()
        self.setup_behavior()

    def setup_style(self):
        """Apply button styling"""
        self.setStyleSheet(get_button_style(self.button_type, self.size))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def setup_behavior(self):
        """Setup button behavior"""
        height = getattr(Dimensions, f"BUTTON_HEIGHT_{self.size.upper()}")
        self.setMinimumHeight(height)


class HeaderSection(QFrame):
    """Standardized page header section"""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle

        self.setup_layout()
        self.setup_content()
        self.setup_shadow()

    def setup_layout(self):
        """Setup header layout"""
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {Colors.PRIMARY};
                border-radius: {BorderRadius.EXTRA_LARGE}px;
                padding: {Spacing.CARD_MARGIN}px;
            }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Spacing.SECTION_MARGIN,
            Spacing.SECTION_MARGIN,
            Spacing.SECTION_MARGIN,
            Spacing.SECTION_MARGIN,
        )
        layout.setSpacing(Spacing.TIGHT_SPACING)

        self.layout = layout

    def setup_content(self):
        """Setup header content"""
        # Title
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {Colors.WHITE};
                font-size: {Typography.SIZE_4XL}px;
                font-weight: {Typography.WEIGHT_EXTRABOLD};
                margin-bottom: {Spacing.TIGHT_SPACING}px;
            }}
        """
        )

        # Subtitle
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle_label.setStyleSheet(
                f"""
                QLabel {{
                    color: rgba(255, 255, 255, 0.9);
                    font-size: {Typography.SIZE_LG}px;
                    font-weight: {Typography.WEIGHT_NORMAL};
                }}
            """
            )
            self.layout.addWidget(subtitle_label)

        self.layout.addWidget(title_label)

    def setup_shadow(self):
        """Apply header shadow"""
        shadow_config = get_shadow_effect(Shadows.MEDIUM_BLUR, Shadows.Y_OFFSET_MEDIUM)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(shadow_config["blur_radius"])
        shadow.setXOffset(shadow_config["x_offset"])
        shadow.setYOffset(shadow_config["y_offset"])
        shadow.setColor(QColor(shadow_config["color"]))
        self.setGraphicsEffect(shadow)


class LoadingSpinner(QWidget):
    """Standardized loading spinner component"""

    def __init__(self, message: str = "טוען...", parent=None):
        super().__init__(parent)
        self.message = message

        self.setup_layout()
        self.setup_content()

    def setup_layout(self):
        """Setup spinner layout"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(Spacing.COMPONENT_SPACING)

        self.layout = layout

    def setup_content(self):
        """Setup spinner content"""
        # Spinner icon
        spinner_label = QLabel("⏳")
        spinner_label.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_4XL))
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinner_label.setStyleSheet(f"color: {Colors.PRIMARY};")

        # Loading text
        text_label = QLabel(self.message)
        text_label.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_LG))
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")

        self.layout.addWidget(spinner_label)
        self.layout.addWidget(text_label)


class EmptyState(QWidget):
    """Standardized empty state component"""

    def __init__(
        self,
        icon: str = "📋",
        title: str = "אין נתונים",
        subtitle: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.subtitle = subtitle

        self.setup_layout()
        self.setup_content()

    def setup_layout(self):
        """Setup empty state layout"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(Spacing.COMPONENT_SPACING)

        self.layout = layout

    def setup_content(self):
        """Setup empty state content"""
        # Icon
        icon_label = QLabel(self.icon)
        icon_label.setFont(QFont(Typography.FONT_FAMILY, 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")

        # Title
        title_label = QLabel(self.title)
        title_label.setFont(
            QFont(Typography.FONT_FAMILY, Typography.SIZE_XL, Typography.WEIGHT_BOLD)
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")

        # Subtitle
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_MD))
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
            subtitle_label.setWordWrap(True)
            self.layout.addWidget(subtitle_label)

        self.layout.addWidget(icon_label)
        self.layout.addWidget(title_label)


class StatusBadge(QLabel):
    """Standardized status badge component"""

    STATUS_COLORS = {
        "completed": (Colors.SUCCESS, Colors.SUCCESS_LIGHT),
        "pending": (Colors.WARNING, Colors.WARNING_LIGHT),
        "failed": (Colors.ERROR, Colors.ERROR_LIGHT),
        "active": (Colors.PRIMARY, Colors.PRIMARY_LIGHT),
    }

    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        self.status = status

        self.setup_style()

    def setup_style(self):
        """Setup badge styling based on status"""
        text_color, bg_color = self.STATUS_COLORS.get(
            self.status, (Colors.TEXT_SECONDARY, Colors.GRAY_100)
        )

        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: {BorderRadius.MEDIUM}px;
                padding: {Spacing.TIGHT_SPACING}px {Spacing.ELEMENT_SPACING}px;
                font-weight: {Typography.WEIGHT_BOLD};
                font-size: {Typography.SIZE_SM}px;
            }}
        """
        )
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(24)


class BaseModal(QFrame):
    """Base modal component with consistent behavior"""

    # Signals
    closed = pyqtSignal()

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title

        self.setup_window_properties()
        self.setup_layout()
        self.setup_shadow()

    def setup_window_properties(self):
        """Setup modal window properties"""
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(Dimensions.MODAL_WIDTH, Dimensions.MODAL_HEIGHT)

    def setup_layout(self):
        """Setup modal layout"""
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {Colors.WHITE};
                border-radius: {BorderRadius.EXTRA_LARGE}px;
                border: 2px solid {Colors.BORDER_LIGHT};
            }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.layout = layout

    def setup_shadow(self):
        """Apply modal shadow"""
        shadow_config = get_shadow_effect(
            Shadows.MEDIUM_BLUR, Shadows.Y_OFFSET_MEDIUM, Shadows.EXTRA_DARK
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(shadow_config["blur_radius"])
        shadow.setXOffset(shadow_config["x_offset"])
        shadow.setYOffset(shadow_config["y_offset"])
        shadow.setColor(QColor(shadow_config["color"]))
        self.setGraphicsEffect(shadow)

    def center_on_screen(self):
        """Center modal on screen"""
        from PyQt6.QtWidgets import QApplication

        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def close_modal(self):
        """Close the modal and emit signal"""
        self.closed.emit()
        self.close()

"""
UI Constants - Centralized configuration for all UI dimensions, colors, and styling.

This file eliminates magic numbers and provides a single source of truth for:
- Widget dimensions and spacing
- Color schemes and gradients
- Typography settings
- Animation durations
- Layout margins and padding
"""

from typing import Any, Dict


# ============================================================================
# DIMENSIONS & SPACING
# ============================================================================


class Dimensions:
    """Standard dimensions for UI components"""

    # Window dimensions
    MAIN_WINDOW_WIDTH = 1200
    MAIN_WINDOW_HEIGHT = 800
    AUTH_WINDOW_WIDTH = 400
    AUTH_WINDOW_HEIGHT = 500

    # Sidebar dimensions
    SIDEBAR_WIDTH = 240
    SIDEBAR_HEADER_HEIGHT = 80

    # Card dimensions
    STAT_CARD_WIDTH = 400
    STAT_CARD_HEIGHT = 160
    PACKAGE_CARD_WIDTH = 320
    PACKAGE_CARD_HEIGHT = 480
    PURCHASE_CARD_HEIGHT = 120
    MESSAGE_CARD_WIDTH = 400
    MESSAGE_CARD_HEIGHT = 160

    # Button dimensions
    BUTTON_HEIGHT_SMALL = 40
    BUTTON_HEIGHT_MEDIUM = 52
    BUTTON_HEIGHT_LARGE = 80
    BUTTON_MIN_WIDTH = 120

    # Input dimensions
    INPUT_HEIGHT = 40
    INPUT_PADDING = 14

    # Modal dimensions
    MODAL_WIDTH = 700
    MODAL_HEIGHT = 550
    MODAL_HEADER_HEIGHT = 110
    MODAL_FOOTER_HEIGHT = 120

    # Content area settings
    CONTENT_MIN_HEIGHT = 500
    CONTENT_MAX_HEIGHT = 800

    # Scroll area settings
    SCROLL_BAR_WIDTH = 12
    SCROLL_BAR_RADIUS = 6


class Spacing:
    """Standard spacing values for consistent layouts"""

    # Layout margins
    PAGE_MARGIN = 40
    CARD_MARGIN = 20
    SECTION_MARGIN = 30
    COMPONENT_MARGIN = 16

    # Layout spacing
    SECTION_SPACING = 30
    CARD_SPACING = 25
    COMPONENT_SPACING = 16
    ELEMENT_SPACING = 12
    TIGHT_SPACING = 8

    # Padding values
    CARD_PADDING = 24
    BUTTON_PADDING = 12
    INPUT_PADDING = 14
    MODAL_PADDING = 30


class BorderRadius:
    """Standard border radius values"""

    SMALL = 8
    MEDIUM = 12
    LARGE = 16
    EXTRA_LARGE = 20
    ROUND = 50


# ============================================================================
# COLORS & THEMES
# ============================================================================


class Colors:
    """Centralized color palette"""

    # Primary colors
    PRIMARY = "#3B82F6"
    PRIMARY_HOVER = "#2563EB"
    PRIMARY_PRESSED = "#1D4ED8"
    PRIMARY_LIGHT = "#DBEAFE"

    # Success colors
    SUCCESS = "#10B981"
    SUCCESS_HOVER = "#059669"
    SUCCESS_LIGHT = "#D1FAE5"

    # Warning colors
    WARNING = "#F59E0B"
    WARNING_HOVER = "#D97706"
    WARNING_LIGHT = "#FEF3C7"

    # Error colors
    ERROR = "#EF4444"
    ERROR_HOVER = "#DC2626"
    ERROR_LIGHT = "#FEE2E2"

    # Neutral colors
    WHITE = "#FFFFFF"
    GRAY_50 = "#F8FAFC"
    GRAY_100 = "#F1F5F9"
    GRAY_200 = "#E2E8F0"
    GRAY_300 = "#CBD5E1"
    GRAY_400 = "#94A3B8"
    GRAY_500 = "#64748B"
    GRAY_600 = "#475569"
    GRAY_700 = "#334155"
    GRAY_800 = "#1E293B"
    GRAY_900 = "#0F172A"

    # Text colors
    TEXT_PRIMARY = "#1E293B"
    TEXT_SECONDARY = "#64748B"
    TEXT_MUTED = "#94A3B8"
    TEXT_INVERSE = "#FFFFFF"

    # Background colors
    BG_PRIMARY = "#F1F5F9"
    BG_SECONDARY = "#FFFFFF"
    BG_SIDEBAR = "#1E293B"
    BG_SIDEBAR_DARK = "#0F172A"

    # Border colors
    BORDER_LIGHT = "#E2E8F0"
    BORDER_MEDIUM = "#CBD5E1"
    BORDER_DARK = "#94A3B8"


class Gradients:
    """Predefined gradient combinations"""

    PRIMARY_GRADIENT = (
        "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3B82F6, stop:1 #1E40AF)"
    )
    SUCCESS_GRADIENT = (
        "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10B981, stop:1 #059669)"
    )
    WARNING_GRADIENT = (
        "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F59E0B, stop:1 #D97706)"
    )
    ERROR_GRADIENT = (
        "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #EF4444, stop:1 #DC2626)"
    )
    CARD_GRADIENT = (
        "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8FAFC)"
    )
    SIDEBAR_GRADIENT = (
        "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E293B, stop:1 #0F172A)"
    )


# ============================================================================
# TYPOGRAPHY
# ============================================================================


class Typography:
    """Typography settings and font configurations"""

    FONT_FAMILY = "Segoe UI"

    # Font sizes
    SIZE_XS = 11
    SIZE_SM = 12
    SIZE_BASE = 13
    SIZE_MD = 14
    SIZE_LG = 16
    SIZE_XL = 18
    SIZE_2XL = 24
    SIZE_3XL = 28
    SIZE_4XL = 32

    # Font weights
    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700
    WEIGHT_EXTRABOLD = 800

    # Line heights
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_NORMAL = 1.4
    LINE_HEIGHT_RELAXED = 1.6
    LINE_HEIGHT_LOOSE = 1.8


# ============================================================================
# ANIMATIONS & TIMING
# ============================================================================


class Animation:
    """Animation durations and easing settings"""

    # Durations (in milliseconds)
    FAST = 200
    NORMAL = 300
    SLOW = 500
    VERY_SLOW = 800

    # Easing curves
    EASE_OUT_CUBIC = "OutCubic"
    EASE_OUT_BACK = "OutBack"
    EASE_IN_OUT = "InOutCubic"


class Timing:
    """Timing constants for various operations"""

    # Timer intervals
    COUNTDOWN_INTERVAL = 1000  # 1 second
    MESSAGE_CHECK_INTERVAL = 5000  # 5 seconds
    SESSION_SYNC_INTERVAL = 60000  # 1 minute

    # Timeouts
    API_TIMEOUT = 30000  # 30 seconds
    MODAL_TIMEOUT = 5000  # 5 seconds
    LOADING_TIMEOUT = 10000  # 10 seconds


# ============================================================================
# SHADOWS & EFFECTS
# ============================================================================


class Shadows:
    """Standard shadow configurations"""

    # Shadow blur radius
    SMALL_BLUR = 15
    MEDIUM_BLUR = 40
    LARGE_BLUR = 50
    EXTRA_LARGE_BLUR = 70

    # Shadow offsets
    X_OFFSET = 0
    Y_OFFSET_SMALL = 4
    Y_OFFSET_MEDIUM = 12
    Y_OFFSET_LARGE = 15
    Y_OFFSET_EXTRA_LARGE = 20

    # Shadow colors
    LIGHT = "rgba(0, 0, 0, 25)"
    MEDIUM = "rgba(0, 0, 0, 50)"
    DARK = "rgba(0, 0, 0, 70)"
    EXTRA_DARK = "rgba(0, 0, 0, 100)"


# ============================================================================
# UI STRINGS (Hebrew)
# ============================================================================


class UIStrings:
    """Centralized UI text strings in Hebrew"""

    # Page titles
    HOME_TITLE = "לוח בקרה"
    PACKAGES_TITLE = "חבילות זמינות"
    HISTORY_TITLE = "היסטוריית רכישות"
    HELP_TITLE = "עזרה"

    # Common actions
    LOGIN = "התחבר"
    LOGOUT = "התנתק"
    CANCEL = "ביטול"
    CONFIRM = "אישור"
    CLOSE = "סגור"
    SAVE = "שמור"
    DELETE = "מחק"
    EDIT = "ערוך"
    REFRESH = "רענן"

    # Status messages
    LOADING = "טוען..."
    SUCCESS = "הצלחה"
    ERROR = "שגיאה"
    WARNING = "אזהרה"
    INFO = "מידע"

    # Time-related
    TIME_REMAINING = "זמן נותר"
    PRINTS_AVAILABLE = "הדפסות זמינות"
    NEW_MESSAGES = "הודעות חדשות"

    # Package-related
    BUY_NOW = "קנה עכשיו"
    PACKAGE_DETAILS = "פרטי החבילה"
    PRICE = "מחיר"

    # Session-related
    START_SESSION = "התחל להשתמש במחשב"
    SESSION_ACTIVE = "הפעלה פעילה"
    SESSION_ENDED = "הפעלה הסתיימה"


# ============================================================================
# LAYOUT CONFIGURATIONS
# ============================================================================


class LayoutConfig:
    """Layout-specific configurations"""

    # Grid configurations
    PACKAGES_MAX_COLUMNS = 3
    PACKAGES_MIN_COLUMNS = 1

    # Scroll area settings
    SCROLL_BAR_WIDTH = 12
    SCROLL_BAR_RADIUS = 6

    # Content area settings
    CONTENT_MIN_HEIGHT = 500
    CONTENT_MAX_HEIGHT = 800


# ============================================================================
# VALIDATION RULES
# ============================================================================


class Validation:
    """Input validation rules and limits"""

    # Password requirements
    MIN_PASSWORD_LENGTH = 6
    MAX_PASSWORD_LENGTH = 128

    # Phone number requirements
    MIN_PHONE_LENGTH = 10
    MAX_PHONE_LENGTH = 15

    # Name requirements
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 50

    # Session limits
    MAX_SESSION_DURATION = 86400  # 24 hours in seconds
    MIN_SESSION_DURATION = 60  # 1 minute in seconds


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def get_shadow_effect(
    blur_radius: int = Shadows.MEDIUM_BLUR,
    y_offset: int = Shadows.Y_OFFSET_MEDIUM,
    color: str = Shadows.MEDIUM,
) -> Dict[str, Any]:
    """Get shadow effect configuration"""
    return {
        "blur_radius": blur_radius,
        "x_offset": Shadows.X_OFFSET,
        "y_offset": y_offset,
        "color": color,
    }


def get_button_style(button_type: str = "primary", size: str = "medium") -> str:
    """Get standardized button style"""
    height = getattr(Dimensions, f"BUTTON_HEIGHT_{size.upper()}")

    if button_type == "primary":
        return f"""
            QPushButton {{
                background: {Gradients.PRIMARY_GRADIENT};
                color: {Colors.WHITE};
                border: none;
                border-radius: {BorderRadius.LARGE}px;
                font-weight: {Typography.WEIGHT_BOLD};
                font-size: {Typography.SIZE_LG}px;
                padding: {Spacing.BUTTON_PADDING}px {Spacing.COMPONENT_MARGIN}px;
                min-height: {height}px;
            }}
            QPushButton:hover {{
                background: {Gradients.PRIMARY_GRADIENT.replace('#3B82F6', '#2563EB')};
            }}
        """

    return ""


def get_card_style(card_type: str = "default") -> str:
    """Get standardized card style - static, no hover effects"""
    return f"""
        QFrame {{
            background: {Colors.WHITE};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: {BorderRadius.EXTRA_LARGE}px;
            margin: {Spacing.TIGHT_SPACING}px;
        }}
    """

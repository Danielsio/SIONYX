"""
UI Constants - FROST Design System
A modern, clean design language inspired by Material Design and glassmorphism.

Design Philosophy:
- Clean whites with violet-blue accents
- Soft, layered shadows for depth
- Generous whitespace and breathing room
- Elegant typography with clear hierarchy
"""

from typing import Any, Dict


# ============================================================================
# FROST COLOR PALETTE
# ============================================================================


class Colors:
    """
    Frost Design System Colors
    A sophisticated palette with violet-indigo primary and teal accents
    """

    # Primary - Violet Indigo
    PRIMARY = "#6366F1"
    PRIMARY_HOVER = "#4F46E5"
    PRIMARY_DARK = "#4338CA"
    PRIMARY_LIGHT = "#E0E7FF"
    PRIMARY_GHOST = "#EEF2FF"

    # Accent - Teal
    ACCENT = "#14B8A6"
    ACCENT_HOVER = "#0D9488"
    ACCENT_LIGHT = "#CCFBF1"

    # Success - Emerald
    SUCCESS = "#10B981"
    SUCCESS_HOVER = "#059669"
    SUCCESS_LIGHT = "#D1FAE5"
    SUCCESS_DARK = "#065F46"

    # Warning - Amber
    WARNING = "#F59E0B"
    WARNING_HOVER = "#D97706"
    WARNING_LIGHT = "#FEF3C7"
    WARNING_DARK = "#92400E"

    # Error - Rose
    ERROR = "#EF4444"
    ERROR_HOVER = "#DC2626"
    ERROR_LIGHT = "#FEE2E2"
    ERROR_DARK = "#991B1B"

    # Neutral Grays - Slate
    WHITE = "#FFFFFF"
    SNOW = "#FAFBFC"
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

    # Text Colors
    TEXT_PRIMARY = "#0F172A"
    TEXT_SECONDARY = "#475569"
    TEXT_MUTED = "#94A3B8"
    TEXT_INVERSE = "#FFFFFF"

    # Background Colors
    BG_PAGE = "#F8FAFC"
    BG_CARD = "#FFFFFF"
    BG_SIDEBAR = "#0F172A"
    BG_SIDEBAR_HOVER = "#1E293B"

    # Additional Background Colors (for dialogs)
    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F1F5F9"  # GRAY_100
    BG_HOVER = "#E2E8F0"  # GRAY_200
    BG_DISABLED = "#CBD5E1"  # GRAY_300

    # Additional Text Colors (for dialogs)
    TEXT_DISABLED = "#94A3B8"  # GRAY_400

    # Border Colors
    BORDER = "#CBD5E1"  # GRAY_300
    BORDER_LIGHT = "#E2E8F0"
    BORDER_DEFAULT = "#CBD5E1"
    BORDER_FOCUS = "#6366F1"


class Gradients:
    """Beautiful gradient combinations for the Frost theme"""

    # Primary button gradient
    PRIMARY = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:1 #4F46E5)"
    PRIMARY_HOVER = (
        "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4F46E5, stop:1 #4338CA)"
    )

    # Success gradient
    SUCCESS = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10B981, stop:1 #059669)"

    # Accent gradient
    ACCENT = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #14B8A6, stop:1 #0D9488)"

    # Error/Danger gradient
    DANGER = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #EF4444, stop:1 #DC2626)"

    # Hero gradient for headers
    HERO = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:0.5 #8B5CF6, stop:1 #A855F7)"

    # Subtle card gradient
    CARD = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #FAFBFC)"

    # Sidebar gradient
    SIDEBAR = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E293B, stop:1 #0F172A)"

    # Frost glass effect
    GLASS = "rgba(255, 255, 255, 0.85)"


# ============================================================================
# TYPOGRAPHY
# ============================================================================


class Typography:
    """Clean, modern typography settings"""

    FONT_FAMILY = "Segoe UI"
    FONT_FAMILY_MONO = "Consolas"

    # Font sizes (using a modular scale)
    SIZE_XS = 11
    SIZE_SM = 12
    SIZE_BASE = 14
    SIZE_MD = 15
    SIZE_LG = 17
    SIZE_XL = 20
    SIZE_2XL = 24
    SIZE_3XL = 30
    SIZE_4XL = 36
    SIZE_DISPLAY = 48

    # Font weights
    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700
    WEIGHT_EXTRABOLD = 800

    # Line heights
    LINE_HEIGHT_TIGHT = 1.25
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_RELAXED = 1.75


# ============================================================================
# DIMENSIONS & SPACING
# ============================================================================


class Dimensions:
    """Standard dimensions for UI components"""

    # Window
    MAIN_WINDOW_WIDTH = 1280
    MAIN_WINDOW_HEIGHT = 800
    AUTH_WINDOW_WIDTH = 420
    AUTH_WINDOW_HEIGHT = 520

    # Sidebar
    SIDEBAR_WIDTH = 260
    SIDEBAR_COLLAPSED = 72

    # Cards
    STAT_CARD_WIDTH = 280
    STAT_CARD_HEIGHT = 140
    PACKAGE_CARD_WIDTH = 300
    PACKAGE_CARD_HEIGHT = 460
    HISTORY_CARD_HEIGHT = 100

    # Buttons
    BUTTON_HEIGHT_SM = 36
    BUTTON_HEIGHT_MD = 44
    BUTTON_HEIGHT_LG = 52
    BUTTON_HEIGHT_XL = 60

    # Inputs
    INPUT_HEIGHT = 44

    # Modals
    MODAL_WIDTH = 480
    MODAL_HEIGHT = 400

    # Content
    CONTENT_MAX_WIDTH = 960
    CONTENT_MIN_HEIGHT = 400


class Spacing:
    """Consistent spacing scale (based on 4px grid)"""

    XS = 4
    SM = 8
    MD = 12
    BASE = 16
    LG = 24
    XL = 32
    XXL = 48
    XXXL = 64

    # Semantic spacing
    PAGE_PADDING = 32
    CARD_PADDING = 24
    SECTION_GAP = 32
    ELEMENT_GAP = 16

    # Additional semantic spacing (for dialogs)
    PAGE_MARGIN = 24
    SECTION_MARGIN = 16
    SECTION_SPACING = 16
    BUTTON_SPACING = 12


class BorderRadius:
    """Border radius scale"""

    NONE = 0
    SM = 6
    MD = 10
    LG = 14
    XL = 20
    XXL = 28
    FULL = 9999


# ============================================================================
# SHADOWS & EFFECTS
# ============================================================================


class Shadows:
    """Layered shadow system for depth"""

    # Shadow levels
    BLUR_SM = 8
    BLUR_MD = 16
    BLUR_LG = 24
    BLUR_XL = 40

    Y_SM = 2
    Y_MD = 4
    Y_LG = 8
    Y_XL = 16

    # Shadow colors
    COLOR_SUBTLE = "rgba(15, 23, 42, 0.04)"
    COLOR_LIGHT = "rgba(15, 23, 42, 0.08)"
    COLOR_MEDIUM = "rgba(15, 23, 42, 0.12)"
    COLOR_HEAVY = "rgba(15, 23, 42, 0.20)"
    COLOR_PRIMARY = "rgba(99, 102, 241, 0.25)"


# ============================================================================
# ANIMATIONS
# ============================================================================


class Animation:
    """Animation timing constants"""

    INSTANT = 100
    FAST = 150
    NORMAL = 250
    SLOW = 400
    VERY_SLOW = 600


class Timing:
    """Timer intervals"""

    COUNTDOWN = 1000
    MESSAGE_CHECK = 5000
    SYNC_INTERVAL = 60000
    DEBOUNCE = 300


# ============================================================================
# UI STRINGS (Hebrew)
# ============================================================================


class UIStrings:
    """Centralized Hebrew text strings"""

    # Navigation
    NAV_HOME = "דף הבית"
    NAV_PACKAGES = "חבילות"
    NAV_HISTORY = "היסטוריה"
    NAV_HELP = "עזרה"

    # Pages
    HOME_TITLE = "ניהול זמן והדפסות"
    HOME_SUBTITLE = "ברוך הבא ללוח הבקרה שלך"
    PACKAGES_TITLE = "חבילות זמינות"
    PACKAGES_SUBTITLE = "בחר חבילה שמתאימה לך"
    HISTORY_TITLE = "היסטוריית רכישות"
    HISTORY_SUBTITLE = "צפה בכל הרכישות שביצעת"
    HELP_TITLE = "עזרה ותמיכה"
    HELP_SUBTITLE = "יש לך שאלות? אנחנו כאן בשבילך"

    # Stats
    TIME_REMAINING = "זמן נותר"
    PRINT_BALANCE = "יתרת הדפסות"
    NEW_MESSAGES = "הודעות חדשות"

    # Actions
    START_SESSION = "התחל הפעלה"
    BUY_NOW = "רכוש עכשיו"
    VIEW_ALL = "צפה בהכל"
    LOGOUT = "התנתק"
    CLOSE = "סגור"
    CONFIRM = "אישור"
    CANCEL = "ביטול"

    # States
    LOADING = "טוען..."
    NO_DATA = "אין נתונים"
    ERROR = "שגיאה"


# ============================================================================
# STYLE PRESETS
# ============================================================================


def get_shadow(level: str = "md") -> Dict[str, Any]:
    """Get shadow configuration by level"""
    configs = {
        "sm": {
            "blur": Shadows.BLUR_SM,
            "y": Shadows.Y_SM,
            "color": Shadows.COLOR_LIGHT,
        },
        "md": {
            "blur": Shadows.BLUR_MD,
            "y": Shadows.Y_MD,
            "color": Shadows.COLOR_MEDIUM,
        },
        "lg": {
            "blur": Shadows.BLUR_LG,
            "y": Shadows.Y_LG,
            "color": Shadows.COLOR_MEDIUM,
        },
        "xl": {
            "blur": Shadows.BLUR_XL,
            "y": Shadows.Y_XL,
            "color": Shadows.COLOR_HEAVY,
        },
        "primary": {
            "blur": Shadows.BLUR_LG,
            "y": Shadows.Y_LG,
            "color": Shadows.COLOR_PRIMARY,
        },
    }
    return configs.get(level, configs["md"])


def get_card_style() -> str:
    """Get standard card styling"""
    return f"""
        QFrame {{
            background: {Colors.WHITE};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: {BorderRadius.XL}px;
        }}
    """


def get_button_style(variant: str = "primary", size: str = "md") -> str:
    """Get button styling by variant and size"""
    heights = {
        "sm": Dimensions.BUTTON_HEIGHT_SM,
        "md": Dimensions.BUTTON_HEIGHT_MD,
        "lg": Dimensions.BUTTON_HEIGHT_LG,
        "xl": Dimensions.BUTTON_HEIGHT_XL,
    }
    height = heights.get(size, Dimensions.BUTTON_HEIGHT_MD)

    if variant == "primary":
        return f"""
            QPushButton {{
                background: {Gradients.PRIMARY};
                color: {Colors.WHITE};
                border: none;
                border-radius: {BorderRadius.MD}px;
                font-size: {Typography.SIZE_BASE}px;
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                padding: 0 {Spacing.LG}px;
                min-height: {height}px;
            }}
            QPushButton:hover {{
                background: {Gradients.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background: {Colors.PRIMARY_DARK};
            }}
            QPushButton:disabled {{
                background: {Colors.GRAY_300};
                color: {Colors.GRAY_500};
            }}
        """
    elif variant == "secondary":
        return f"""
            QPushButton {{
                background: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {BorderRadius.MD}px;
                font-size: {Typography.SIZE_BASE}px;
                font-weight: {Typography.WEIGHT_MEDIUM};
                padding: 0 {Spacing.LG}px;
                min-height: {height}px;
            }}
            QPushButton:hover {{
                background: {Colors.GRAY_50};
                border-color: {Colors.GRAY_400};
            }}
        """
    elif variant == "danger":
        return f"""
            QPushButton {{
                background: transparent;
                color: {Colors.ERROR};
                border: 1px solid {Colors.ERROR};
                border-radius: {BorderRadius.MD}px;
                font-size: {Typography.SIZE_BASE}px;
                font-weight: {Typography.WEIGHT_MEDIUM};
                padding: 0 {Spacing.LG}px;
                min-height: {height}px;
            }}
            QPushButton:hover {{
                background: {Colors.ERROR_LIGHT};
            }}
        """
    elif variant == "ghost":
        return f"""
            QPushButton {{
                background: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-radius: {BorderRadius.MD}px;
                font-size: {Typography.SIZE_BASE}px;
                font-weight: {Typography.WEIGHT_MEDIUM};
                padding: 0 {Spacing.BASE}px;
                min-height: {height}px;
            }}
            QPushButton:hover {{
                background: {Colors.GRAY_100};
                color: {Colors.TEXT_PRIMARY};
            }}
        """

    return ""


# Legacy compatibility
def get_shadow_effect(
    blur_radius: int = 16, y_offset: int = 4, color: str = "rgba(15, 23, 42, 0.12)"
) -> Dict[str, Any]:
    """Legacy shadow function for compatibility"""
    return {
        "blur_radius": blur_radius,
        "x_offset": 0,
        "y_offset": y_offset,
        "color": color,
    }


# ============================================================================
# LAYOUT CONFIGURATIONS
# ============================================================================


class LayoutConfig:
    """Layout settings"""

    PACKAGES_COLUMNS = 3
    HISTORY_ITEMS_PER_PAGE = 10
    SCROLL_BAR_WIDTH = 8


class Validation:
    """Input validation rules"""

    MIN_PASSWORD_LENGTH = 6
    MAX_PASSWORD_LENGTH = 128
    MIN_PHONE_LENGTH = 10
    MAX_PHONE_LENGTH = 15
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 50

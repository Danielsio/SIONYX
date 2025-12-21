"""
Help Page - FROST Design System
Modern help center with FAQ cards and contact info.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from utils.logger import get_logger
from ui.components.base_components import PageHeader, apply_shadow
from ui.constants.ui_constants import (
    BorderRadius,
    Colors,
    Dimensions,
    Spacing,
    Typography,
    UIStrings,
)


logger = get_logger(__name__)


class FAQCard(QFrame):
    """Expandable FAQ card"""

    def __init__(self, icon: str, question: str, answer: str, parent=None):
        super().__init__(parent)
        self.question = question
        self.answer = answer
        self.icon = icon
        self._build()

    def _build(self):
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG}px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """
        )
        apply_shadow(self, "sm")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.BASE, Spacing.LG, Spacing.BASE)
        layout.setSpacing(Spacing.SM)

        # Question row
        q_row = QWidget()
        q_layout = QHBoxLayout(q_row)
        q_layout.setContentsMargins(0, 0, 0, 0)
        q_layout.setSpacing(Spacing.SM)

        icon = QLabel(self.icon)
        icon.setFont(QFont(Typography.FONT_FAMILY, 18))
        q_layout.addWidget(icon)

        question = QLabel(self.question)
        question.setFont(
            QFont(
                Typography.FONT_FAMILY, Typography.SIZE_BASE, Typography.WEIGHT_SEMIBOLD
            )
        )
        question.setStyleSheet(
            f"color: {Colors.TEXT_PRIMARY}; background: transparent;"
        )
        question.setWordWrap(True)
        q_layout.addWidget(question, 1)

        layout.addWidget(q_row)

        # Answer
        answer = QLabel(self.answer)
        answer.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_SM))
        answer.setStyleSheet(
            f"""
            color: {Colors.TEXT_SECONDARY};
            background: {Colors.GRAY_50};
            padding: {Spacing.MD}px;
            border-radius: {BorderRadius.SM}px;
        """
        )
        answer.setWordWrap(True)
        layout.addWidget(answer)


class ContactCard(QFrame):
    """Contact information card"""

    def __init__(self, icon: str, title: str, value: str, parent=None):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.value = value
        self._build()

    def _build(self):
        self.setFixedHeight(100)
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG}px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """
        )
        apply_shadow(self, "sm")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.BASE, Spacing.LG, Spacing.BASE)
        layout.setSpacing(Spacing.XS)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon = QLabel(self.icon)
        icon.setFont(QFont(Typography.FONT_FAMILY, 24))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        # Title
        title = QLabel(self.title)
        title.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_SM))
        title.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Value
        value = QLabel(self.value)
        value.setFont(
            QFont(
                Typography.FONT_FAMILY, Typography.SIZE_BASE, Typography.WEIGHT_SEMIBOLD
            )
        )
        value.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value)


class HelpPage(QWidget):
    """Modern help and support page"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_user = auth_service.get_current_user()
        self.init_ui()

    def init_ui(self):
        """Build the UI"""
        self.setObjectName("helpPage")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
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
        header = PageHeader(UIStrings.HELP_TITLE, UIStrings.HELP_SUBTITLE)
        layout.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(
            Spacing.BASE, Spacing.BASE, Spacing.BASE, Spacing.BASE
        )
        scroll_layout.setSpacing(Spacing.LG)

        # Contact section
        contact_title = QLabel("📞 יצירת קשר")
        contact_title.setFont(
            QFont(
                Typography.FONT_FAMILY, Typography.SIZE_LG, Typography.WEIGHT_SEMIBOLD
            )
        )
        contact_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        scroll_layout.addWidget(contact_title)

        contact_row = QWidget()
        contact_layout = QHBoxLayout(contact_row)
        contact_layout.setContentsMargins(0, 0, 0, 0)
        contact_layout.setSpacing(Spacing.BASE)

        contact_layout.addWidget(ContactCard("📧", "אימייל", "support@sionyx.co.il"))
        contact_layout.addWidget(ContactCard("📱", "טלפון", "03-1234567"))
        contact_layout.addWidget(ContactCard("💬", "וואטסאפ", "050-1234567"))
        contact_layout.addStretch()

        scroll_layout.addWidget(contact_row)

        # FAQ section
        faq_title = QLabel("❓ שאלות נפוצות")
        faq_title.setFont(
            QFont(
                Typography.FONT_FAMILY, Typography.SIZE_LG, Typography.WEIGHT_SEMIBOLD
            )
        )
        faq_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        scroll_layout.addWidget(faq_title)

        # FAQ items
        faqs = [
            (
                "⏱️",
                "איך אני רוכש זמן?",
                "לחץ על 'חבילות' בתפריט הצד, בחר חבילה ובצע תשלום מאובטח.",
            ),
            (
                "🖨️",
                "איך עובדות ההדפסות?",
                "יתרת ההדפסות שלך מוצגת בשקלים. כל הדפסה מחויבת לפי מחיר העמוד.",
            ),
            (
                "💳",
                "האם התשלום מאובטח?",
                "כן! אנו משתמשים בטכנולוגיית הצפנה מתקדמת להגנה על פרטי התשלום שלך.",
            ),
            (
                "🔄",
                "מה קורה אם נגמר לי הזמן?",
                "תקבל התראה לפני סיום הזמן. תוכל לרכוש זמן נוסף בכל עת.",
            ),
            (
                "📞",
                "למי לפנות אם יש בעיה?",
                "צור קשר עם התמיכה שלנו באמצעות הטלפון, אימייל או וואטסאפ.",
            ),
        ]

        for icon, question, answer in faqs:
            faq = FAQCard(icon, question, answer)
            scroll_layout.addWidget(faq)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        outer.addStretch()
        outer.addWidget(content)
        outer.addStretch()

        logger.debug("Help page initialized")

    def refresh_user_data(self):
        """Refresh user data (not needed for help page)"""
        pass

"""
Help Page - FROST Design System
Modern help center with FAQ cards and contact info.
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from services.organization_metadata_service import OrganizationMetadataService
from ui.components.base_components import PageHeader, apply_shadow
from ui.constants.ui_constants import (
    BorderRadius,
    Colors,
    Dimensions,
    Spacing,
    Typography,
    UIStrings,
)
from utils.logger import get_logger


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
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.WHITE},
                    stop:1 {Colors.GRAY_50}
                );
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

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: {Colors.BORDER_LIGHT};")
        layout.addWidget(divider)

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

    def __init__(
        self, icon: str, title: str, value: str, copy_text: str = "", parent=None
    ):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.value = value
        self.copy_text = copy_text
        self._build()

    def _build(self):
        self.setMinimumHeight(120)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        )
        self.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.WHITE},
                    stop:1 {Colors.GRAY_50}
                );
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG}px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
            QFrame:hover {{
                border: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """
        )
        apply_shadow(self, "lg")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        layout.setSpacing(Spacing.SM)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon = QLabel(self.icon)
        icon.setFont(QFont(Typography.FONT_FAMILY, 22))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            f"""
            color: {Colors.TEXT_PRIMARY};
            background: {Colors.GRAY_50};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: {BorderRadius.SM}px;
            padding: 4px 10px;
        """
        )
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
                Typography.FONT_FAMILY, Typography.SIZE_MD, Typography.WEIGHT_SEMIBOLD
            )
        )
        value.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value)

        if self.copy_text:
            self.setToolTip("לחץ להעתקה")
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if self.copy_text:
            clipboard = QApplication.instance().clipboard()
            clipboard.setText(self.copy_text)
        super().mousePressEvent(event)


class HelpPage(QWidget):
    """Modern help and support page"""

    def __init__(self, auth_service, firebase_client=None, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.firebase_client = firebase_client
        self.current_user = auth_service.get_current_user()
        self.contact_cards = []
        self._contact_reflow_timer = QTimer(self)
        self._contact_reflow_timer.setSingleShot(True)
        self._contact_reflow_timer.timeout.connect(self._layout_contact_cards)

        # Fetch admin contact from organization metadata
        self.admin_phone = ""
        self.admin_email = ""
        self.org_name = ""
        self._fetch_admin_contact()

        self.init_ui()

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        clipboard = QApplication.instance().clipboard()
        clipboard.setText(text or "")

    def _clear_layout(self, layout, delete_widgets: bool = True):
        """Remove all widgets/items from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget and delete_widgets:
                widget.deleteLater()

    def _fetch_admin_contact(self):
        """Fetch admin contact info from organization metadata"""
        if not self.firebase_client:
            logger.warning("No firebase_client provided, using default contact info")
            return

        try:
            # firebase_client handles org_id automatically (multi-tenancy)
            metadata_service = OrganizationMetadataService(self.firebase_client)
            result = metadata_service.get_admin_contact()

            if result.get("success"):
                contact = result["contact"]
                self.admin_phone = contact.get("phone", "")
                self.admin_email = contact.get("email", "")
                self.org_name = contact.get("org_name", "")
                logger.debug(
                    "Admin contact fetched",
                    has_phone=bool(self.admin_phone),
                    has_email=bool(self.admin_email),
                )
            else:
                logger.warning(f"Failed to fetch admin contact: {result.get('error')}")
        except Exception as e:
            logger.error(f"Error fetching admin contact: {e}")

    def init_ui(self):
        """Build the UI"""
        self.setObjectName("helpPage")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
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
            Spacing.XXL, Spacing.LG, Spacing.XXL, Spacing.XL
        )
        scroll_layout.setSpacing(Spacing.LG)

        # Contact section
        self.contact_title = QLabel("יצירת קשר")
        self.contact_title.setFont(
            QFont(
                Typography.FONT_FAMILY, Typography.SIZE_LG, Typography.WEIGHT_SEMIBOLD
            )
        )
        self.contact_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        scroll_layout.addWidget(self.contact_title)

        contact_row = QWidget()
        contact_row.setStyleSheet("background: transparent;")
        self.contact_layout = QGridLayout(contact_row)
        self.contact_layout.setContentsMargins(
            Spacing.LG, Spacing.SM, Spacing.LG, Spacing.LG
        )
        self.contact_layout.setHorizontalSpacing(Spacing.XL)
        self.contact_layout.setVerticalSpacing(Spacing.LG)
        self.contact_container = contact_row

        scroll_layout.addWidget(contact_row)

        # Help text for users
        self.help_text = QLabel(
            "אם משהו לא עובד או אם תשלום לא עבר - ניתן ליצור קשר עם מנהל המערכת "
            "באימייל או בטלפון."
        )
        self.help_text.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_SM))
        self.help_text.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        self.help_text.setWordWrap(True)
        scroll_layout.addWidget(self.help_text)

        support_note = QLabel("זמני תמיכה: א׳‑ה׳ 09:00‑18:00")
        support_note.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_SM))
        support_note.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        support_note.setWordWrap(True)
        scroll_layout.addWidget(support_note)

        # Render contact widgets
        self._render_contact_section()

        # FAQ section
        faq_title = QLabel("שאלות נפוצות")
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
                "■",
                "איך אני רוכש זמן?",
                "לחץ על 'חבילות' בתפריט הצד, בחר חבילה ובצע תשלום מאובטח.",
            ),
            (
                "■",
                "איך עובדות ההדפסות?",
                "יתרת ההדפסות שלך מוצגת בשקלים. כל הדפסה מחויבת לפי מחיר העמוד.",
            ),
            (
                "■",
                "האם התשלום מאובטח?",
                "כן! אנו משתמשים בטכנולוגיית הצפנה מתקדמת להגנה על פרטי התשלום שלך.",
            ),
            (
                "■",
                "מה קורה אם נגמר לי הזמן?",
                "תקבל התראה לפני סיום הזמן. תוכל לרכוש זמן נוסף בכל עת.",
            ),
            (
                "■",
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

        logger.debug("Help page initialized")

    def refresh_user_data(self):
        """Refresh admin contact info for help page."""
        self._fetch_admin_contact()
        self._render_contact_section()

    def _render_contact_section(self):
        """Render contact cards and action buttons."""
        # Title with org name
        contact_title_text = "יצירת קשר"
        if self.org_name:
            contact_title_text += f" - {self.org_name}"
        self.contact_title.setText(contact_title_text)

        # Clear layout
        self._clear_layout(self.contact_layout)
        self.contact_cards = []

        # Show admin contact info from organization metadata
        if self.admin_email:
            self.contact_cards.append(
                ContactCard(
                    "📧",
                    "אימייל מנהל",
                    self.admin_email,
                    copy_text=self.admin_email,
                )
            )

        if self.admin_phone:
            phone_text = str(self.admin_phone)
            self.contact_cards.append(
                ContactCard(
                    "📱",
                    "טלפון מנהל",
                    phone_text,
                    copy_text=phone_text,
                )
            )
            # Also show WhatsApp with the same phone number
            self.contact_cards.append(
                ContactCard(
                    "💬",
                    "וואטסאפ",
                    phone_text,
                    copy_text=phone_text,
                )
            )

        # If no admin contact info available, show placeholder
        if not self.admin_email and not self.admin_phone:
            self.contact_cards.append(ContactCard("ℹ️", "מידע", "פנה למנהל המערכת"))

        self._layout_contact_cards()

        # No action buttons; contact cards are clickable via link

    def resizeEvent(self, event):
        """Reflow contact cards on resize"""
        super().resizeEvent(event)
        if self.contact_cards:
            self._contact_reflow_timer.start(120)

    def _layout_contact_cards(self):
        """Lay out contact cards responsively"""
        self._clear_layout(self.contact_layout, delete_widgets=False)
        if not self.contact_cards:
            return

        columns = self._calculate_contact_columns()
        row = 0
        col = 0
        for card in self.contact_cards:
            self.contact_layout.addWidget(card, row, col)
            col += 1
            if col >= columns:
                col = 0
                row += 1

        for i in range(columns):
            self.contact_layout.setColumnStretch(i, 1)

    def _calculate_contact_columns(self) -> int:
        """Determine number of contact columns based on available width"""
        available_width = max(1, self.contact_container.width() - Spacing.BASE)
        card_min_width = 240
        max_columns = max(1, available_width // (card_min_width + Spacing.BASE))
        return min(max_columns, max(1, len(self.contact_cards)))

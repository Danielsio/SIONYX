"""
History Page - FROST Design System
Clean purchase history with modern list design.
"""

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from services.purchase_service import PurchaseService
from ui.components.base_components import (
    EmptyState,
    LoadingSpinner,
    PageHeader,
    StatusBadge,
    apply_shadow,
)
from ui.constants.ui_constants import (
    BorderRadius,
    Colors,
    Dimensions,
    Spacing,
    Typography,
    UIStrings,
)
from utils.logger import get_logger
from utils.purchase_constants import get_status_label


logger = get_logger(__name__)


class PurchaseCard(QFrame):
    """Modern purchase history card"""

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self._build()

    def _build(self):
        self.setMinimumHeight(96)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
        )
        accent = self._get_accent_color(self.data.get("status", "pending"))
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-right: 3px solid {accent};
                border-radius: {BorderRadius.LG}px;
            }}
            QFrame:hover {{
                border-color: {Colors.BORDER_DEFAULT};
                background: {Colors.GRAY_50};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """
        )
        apply_shadow(self, "sm")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.BASE, Spacing.LG, Spacing.BASE)
        layout.setSpacing(Spacing.BASE)

        # Status icon
        status = self.data.get("status", "pending")
        icon_frame = QFrame()
        icon_frame.setFixedSize(44, 44)
        icon_frame.setStyleSheet(self._get_icon_style(status))

        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel(self._get_icon(status))
        icon.setFont(QFont(Typography.FONT_FAMILY, 16))
        icon.setStyleSheet("color: white;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon)

        layout.addWidget(icon_frame)

        # Content
        content = QVBoxLayout()
        content.setSpacing(2)

        # Package name
        name = QLabel(self.data.get("packageName", "חבילה"))
        name.setFont(
            QFont(
                Typography.FONT_FAMILY, Typography.SIZE_BASE, Typography.WEIGHT_SEMIBOLD
            )
        )
        name.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        content.addWidget(name)

        # Details
        minutes = self.data.get("minutes", 0)
        prints = self.data.get("prints", 0)
        details = QLabel(f"{minutes} דקות • {prints}₪ הדפסות")
        details.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_SM))
        details.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; background: transparent;"
        )
        content.addWidget(details)

        # Date
        date_str = self._format_date(self.data.get("createdAt", ""))
        date_lbl = QLabel(date_str)
        date_lbl.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_XS))
        date_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
        content.addWidget(date_lbl)

        layout.addLayout(content, 1)

        # Right side - price and status
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        right.setSpacing(Spacing.XS)

        # Price
        amount = self._safe_int(self.data.get("amount", 0))
        price = QLabel(f"₪{amount}")
        price.setFont(
            QFont(Typography.FONT_FAMILY, Typography.SIZE_LG, Typography.WEIGHT_BOLD)
        )
        price.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent;")
        right.addWidget(price, alignment=Qt.AlignmentFlag.AlignRight)

        # Status badge
        badge = StatusBadge(get_status_label(status), status)
        right.addWidget(badge, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addLayout(right)

    def _get_icon_style(self, status: str) -> str:
        colors = {
            "completed": Colors.SUCCESS,
            "pending": Colors.WARNING,
            "failed": Colors.ERROR,
        }
        color = colors.get(status, Colors.GRAY_400)
        return f"""
            background: {color};
            border-radius: 22px;
        """

    def _get_accent_color(self, status: str) -> str:
        colors = {
            "completed": Colors.SUCCESS,
            "pending": Colors.WARNING,
            "failed": Colors.ERROR,
        }
        return colors.get(status, Colors.GRAY_300)

    def _get_icon(self, status: str) -> str:
        icons = {"completed": "✓", "pending": "⏳", "failed": "✕"}
        return icons.get(status, "?")

    def _format_date(self, date_str: str) -> str:
        try:
            if date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            pass
        return "תאריך לא זמין"

    def _safe_int(self, value, default=0) -> int:
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return default


class HistoryPage(QWidget):
    """Modern purchase history page"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_user = None
        self.purchases = []
        self.filtered_purchases = []

        self.firebase_client = auth_service.firebase
        self.purchase_service = PurchaseService(self.firebase_client)

        self.cached_purchases = []
        self.cache_timestamp = None
        self.cache_duration = 60
        self.last_user_id = None

        self.init_ui()

    def init_ui(self):
        """Build the UI"""
        self.setObjectName("historyPage")
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
        layout.setSpacing(Spacing.BASE)

        # Header
        header = PageHeader(UIStrings.HISTORY_TITLE, UIStrings.HISTORY_SUBTITLE)
        layout.addWidget(header)

        # Filters
        filters = self._build_filters()
        layout.addWidget(filters)

        # Purchases list - reduced spacing
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"""
            QScrollArea {{ 
                border: none; 
                background: transparent; 
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.GRAY_300};
                border-radius: 4px;
                min-height: 40px;
            }}
        """
        )

        self.list_container = QWidget()
        self.list_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
        )
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, Spacing.SM, 0, 0)
        self.list_layout.setSpacing(Spacing.SM)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll, 1)

    def _build_filters(self) -> QWidget:
        """Build filters section"""
        container = QFrame()
        container.setStyleSheet(
            f"""
            QFrame {{
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG}px;
            }}
        """
        )
        apply_shadow(container, "sm")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Search
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("חיפוש...")
        self.search_box.setMinimumHeight(40)
        self.search_box.setStyleSheet(
            f"""
            QLineEdit {{
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD}px;
                padding: 0 {Spacing.MD}px;
                font-size: {Typography.SIZE_SM}px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
            QLineEdit::placeholder {{
                color: {Colors.TEXT_MUTED};
            }}
        """
        )
        self.search_box.textChanged.connect(self._filter)
        layout.addWidget(self.search_box, 1)

        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems(["כל הסטטוסים", "הושלם", "ממתין", "נכשל"])
        self.status_filter.setMinimumHeight(40)
        self.status_filter.setStyleSheet(
            f"""
            QComboBox {{
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD}px;
                padding: 0 {Spacing.MD}px;
                font-size: {Typography.SIZE_SM}px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QComboBox:focus {{
                border-color: {Colors.PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
                subcontrol-origin: padding;
                subcontrol-position: center left;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 0px;
                outline: none;
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.PRIMARY_LIGHT};
                selection-color: {Colors.PRIMARY};
                padding: 4px;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 32px;
                padding: 8px 12px;
                background: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: {Colors.GRAY_100};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
            }}
        """
        )
        self.status_filter.currentTextChanged.connect(self._filter)
        layout.addWidget(self.status_filter)

        # Sort button
        self.sort_btn = QPushButton("מיון")
        self.sort_btn.setMinimumHeight(40)
        self.sort_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sort_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {Colors.GRAY_100};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD}px;
                padding: 0 {Spacing.MD}px;
                font-size: {Typography.SIZE_SM}px;
                color: {Colors.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                background: {Colors.GRAY_200};
            }}
        """
        )
        self.sort_btn.clicked.connect(self._toggle_sort)
        layout.addWidget(self.sort_btn)

        return container

    def _clear_list(self):
        """Clear the purchases list"""
        for i in reversed(range(self.list_layout.count())):
            child = self.list_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

    def _show_loading(self):
        """Show loading state"""
        self._clear_list()
        spinner = LoadingSpinner("טוען היסטוריה...")
        self.list_layout.addWidget(spinner)

    def _show_empty(self):
        """Show empty state"""
        self._clear_list()
        empty = EmptyState("■", "אין רכישות", "הרכישות שלך יופיעו כאן")
        self.list_layout.addWidget(empty)

    def _show_error(self, message: str):
        """Show error state"""
        self._clear_list()
        error = EmptyState("■", "שגיאה", message)
        self.list_layout.addWidget(error)

    def _display_purchases(self):
        """Display purchases"""
        self._clear_list()

        if not self.filtered_purchases:
            self._show_empty()
            return

        for purchase in self.filtered_purchases:
            card = PurchaseCard(purchase)
            self.list_layout.addWidget(card)

        self.list_layout.addStretch()

    def _filter(self):
        """Filter purchases"""
        search = self.search_box.text().lower()
        status = self.status_filter.currentText()

        status_map = {"הושלם": "completed", "ממתין": "pending", "נכשל": "failed"}

        self.filtered_purchases = []
        for p in self.purchases:
            # Search filter
            if search:
                name = p.get("packageName", "").lower()
                if search not in name:
                    continue

            # Status filter
            if status != "כל הסטטוסים":
                if p.get("status") != status_map.get(status):
                    continue

            self.filtered_purchases.append(p)

        self._display_purchases()

    def _toggle_sort(self):
        """Toggle sort order"""
        if not self.filtered_purchases:
            return

        # Check current order
        if len(self.filtered_purchases) > 1:
            first = self.filtered_purchases[0].get("createdAt", "")
            second = self.filtered_purchases[1].get("createdAt", "")
            newest_first = first > second
        else:
            newest_first = True

        self.filtered_purchases.sort(
            key=lambda x: x.get("createdAt", ""), reverse=not newest_first
        )
        self._display_purchases()

    def refresh_user_data(self, force: bool = False):
        """Refresh user data"""
        self.current_user = self.auth_service.get_current_user()
        if not self.current_user:
            return

        self._load_data(use_cache=not force)

    def _load_data(self, use_cache: bool = True):
        """Load purchase data"""
        if not self.current_user:
            self._show_error("לא מחובר")
            return

        user_id = self.current_user.get("uid")
        if not user_id:
            return

        # Check cache
        if use_cache and self._is_cache_valid(user_id):
            self.purchases = self.cached_purchases.copy()
            self.filtered_purchases = self.purchases.copy()
            self._display_purchases()
            return

        self._show_loading()

        try:
            result = self.purchase_service.get_user_purchase_history(user_id)

            if result.get("success"):
                self.purchases = result.get("data", [])
                self.filtered_purchases = self.purchases.copy()
                self._update_cache(self.purchases, user_id)
                self._display_purchases()
            else:
                self._show_error(result.get("error", "שגיאה"))

        except Exception as e:
            logger.exception("Error loading purchases")
            self._show_error(str(e))

    def _is_cache_valid(self, user_id: str) -> bool:
        if not self.cached_purchases or not self.cache_timestamp:
            return False
        if self.last_user_id != user_id:
            return False
        age = (datetime.now() - self.cache_timestamp).total_seconds()
        return age < self.cache_duration

    def _update_cache(self, data: list, user_id: str):
        self.cached_purchases = data.copy()
        self.cache_timestamp = datetime.now()
        self.last_user_id = user_id

    def clear_user_data(self):
        """Clear user data"""
        self.current_user = None
        self.purchases = []
        self.filtered_purchases = []
        self.cached_purchases = []
        self.cache_timestamp = None
        self._show_empty()

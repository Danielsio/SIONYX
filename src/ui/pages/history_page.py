"""
History Page
View session history and transactions with modern UI/UX
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
    QFrame, QPushButton, QComboBox, QLineEdit, QSpacerItem,
    QSizePolicy, QGraphicsDropShadowEffect, QGridLayout
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient, QBrush, QPen

from utils.logger import get_logger
from utils.purchase_constants import get_status_label, get_status_color
from services.purchase_service import PurchaseService
from services.firebase_client import FirebaseClient
from datetime import datetime, timedelta
import random

logger = get_logger(__name__)


class PurchaseCard(QFrame):
    """Individual purchase card with modern styling"""
    
    def __init__(self, purchase_data, parent=None):
        super().__init__(parent)
        self.purchase_data = purchase_data
        self.init_ui()
        self.setup_animations()
    
    def init_ui(self):
        """Initialize card UI"""
        self.setObjectName("purchaseCard")
        self.setFixedHeight(120)
        self.setStyleSheet("""
            QFrame#purchaseCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFFFF, stop:1 #F8FAFC);
                border: 1px solid #E2E8F0;
                border-radius: 16px;
                margin: 8px;
            }
            QFrame#purchaseCard:hover {
                border: 1px solid #3B82F6;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFFFF, stop:1 #F0F9FF);
            }
        """)
        
        # Add subtle shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 15))
        self.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        # Package icon/status indicator
        self.status_frame = QFrame()
        self.status_frame.setFixedSize(48, 48)
        self.status_frame.setStyleSheet(self.get_status_style())
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        status_icon = QLabel(self.get_status_icon())
        status_icon.setFont(QFont("Segoe UI", 20))
        status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(status_icon)
        
        # Main content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # Package name
        package_name = QLabel(self.purchase_data.get('packageName', 'חבילת זמן'))
        package_name.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        package_name.setStyleSheet("color: #1E293B;")
        
        # Purchase details
        details_text = f"{self.purchase_data.get('minutes', 0)} דקות • {self.purchase_data.get('prints', 0)} הדפסות"
        details = QLabel(details_text)
        details.setFont(QFont("Segoe UI", 12))
        details.setStyleSheet("color: #64748B;")
        
        # Date
        date_text = self.format_date(self.purchase_data.get('createdAt', ''))
        date_label = QLabel(date_text)
        date_label.setFont(QFont("Segoe UI", 11))
        date_label.setStyleSheet("color: #94A3B8;")
        
        content_layout.addWidget(package_name)
        content_layout.addWidget(details)
        content_layout.addWidget(date_label)
        content_layout.addStretch()
        
        # Price and status
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        # Price
        amount = self._safe_int(self.purchase_data.get('amount', 0))
        price = QLabel(f"₪{amount}")
        price.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        price.setStyleSheet("color: #059669;")
        
        # Status badge
        status_badge = QLabel(get_status_label(self.purchase_data.get('status', 'pending')))
        status_badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        status_badge.setStyleSheet(self.get_status_badge_style())
        status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_badge.setFixedHeight(24)
        status_badge.setContentsMargins(12, 4, 12, 4)
        
        right_layout.addWidget(price)
        right_layout.addWidget(status_badge)
        right_layout.addStretch()
        
        layout.addWidget(self.status_frame)
        layout.addLayout(content_layout)
        layout.addStretch()
        layout.addLayout(right_layout)
    
    def get_status_style(self):
        """Get status indicator style"""
        status = self.purchase_data.get('status', 'pending')
        if status == 'completed':
            return """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #10B981, stop:1 #059669);
                border-radius: 24px;
            """
        elif status == 'failed':
            return """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #EF4444, stop:1 #DC2626);
                border-radius: 24px;
            """
        else:  # pending
            return """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F59E0B, stop:1 #D97706);
                border-radius: 24px;
            """
    
    def get_status_icon(self):
        """Get status icon"""
        status = self.purchase_data.get('status', 'pending')
        if status == 'completed':
            return "✓"
        elif status == 'failed':
            return "✕"
        else:  # pending
            return "⏳"
    
    def get_status_badge_style(self):
        """Get status badge style"""
        status = self.purchase_data.get('status', 'pending')
        if status == 'completed':
            return """
                background-color: #D1FAE5;
                color: #065F46;
                border-radius: 12px;
                border: 1px solid #A7F3D0;
            """
        elif status == 'failed':
            return """
                background-color: #FEE2E2;
                color: #991B1B;
                border-radius: 12px;
                border: 1px solid #FECACA;
            """
        else:  # pending
            return """
                background-color: #FEF3C7;
                color: #92400E;
                border-radius: 12px;
                border: 1px solid #FDE68A;
            """
    
    def format_date(self, date_str):
        """Format date string"""
        try:
            if date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime("%d/%m/%Y %H:%M")
        except:
            pass
        return "תאריך לא זמין"
    
    def setup_animations(self):
        """Setup hover animations"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _safe_int(self, value, default=0):
        """Safely convert value to integer, handling strings and None"""
        if value is None:
            return default
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return default


class StatsCard(QFrame):
    """Statistics summary card"""
    
    def __init__(self, title, value, subtitle, color="#3B82F6", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.color = color
        self.init_ui()
    
    def init_ui(self):
        """Initialize stats card UI"""
        self.setObjectName("statsCard")
        self.setFixedHeight(180)  # Even more height for better visibility
        self.setMinimumWidth(250)  # Much wider minimum width
        self.setMaximumWidth(300)  # Set maximum width to prevent over-stretching
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"""
            QFrame#statsCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.color}08, stop:1 {self.color}04);
                border: 1px solid {self.color}20;
                border-radius: 16px;
                margin: 4px;
            }}
        """)
        
        # Add subtle shadow to stats cards
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 10))
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)  # Even more padding for better spacing
        layout.setSpacing(14)  # Even more spacing between elements
        
        # Value
        value_label = QLabel(self.value)
        value_label.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))  # Much larger font
        value_label.setStyleSheet(f"color: {self.color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))  # Much larger font
        title_label.setStyleSheet("color: #1E293B;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Subtitle
        subtitle_label = QLabel(self.subtitle)
        subtitle_label.setFont(QFont("Segoe UI", 12))  # Much larger font
        subtitle_label.setStyleSheet("color: #64748B;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(value_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addStretch()


class HistoryPage(QWidget):
    """Session history and transactions page with modern UI/UX"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_user = auth_service.get_current_user()
        self.purchases = []
        self.filtered_purchases = []
        
        # Use the authenticated Firebase client from auth_service
        self.firebase_client = auth_service.firebase
        self.purchase_service = PurchaseService(self.firebase_client)
        
        self.init_ui()
        self.load_purchase_data()
        self.setup_animations()

    def init_ui(self):
        """Initialize UI"""
        self.setObjectName("contentPage")
        
        # Set RTL layout direction for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(30)  # Even more spacing between sections

        # Header section
        self.create_header(main_layout)
        
        # Statistics section
        self.create_stats_section(main_layout)
        
        # Filters section
        self.create_filters_section(main_layout)
        
        # Purchases list
        self.create_purchases_section(main_layout)
        
        # Add stretch to push content to top
        main_layout.addStretch()

        logger.debug("History page initialized")

    def create_header(self, parent_layout):
        """Create page header"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # Title
        title = QLabel("היסטוריית רכישות")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #0F172A; margin-bottom: 8px;")
        
        # Subtitle
        subtitle = QLabel("צפה בכל הרכישות והעסקאות שביצעת")
        subtitle.setFont(QFont("Segoe UI", 16))
        subtitle.setStyleSheet("color: #64748B;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        parent_layout.addLayout(header_layout)

    def create_stats_section(self, parent_layout):
        """Create statistics cards section"""
        # Create a container widget for the stats section
        stats_container = QWidget()
        stats_container.setMinimumHeight(200)  # Even more height for container
        stats_container.setMaximumHeight(220)  # Allow even more space
        stats_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.stats_layout = QHBoxLayout(stats_container)
        self.stats_layout.setSpacing(30)  # Much more spacing between cards
        self.stats_layout.setContentsMargins(20, 20, 20, 20)  # Much more margins
        self.stats_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the cards
        
        # Initialize with loading state
        self.update_stats_cards()
        
        parent_layout.addWidget(stats_container)

    def create_filters_section(self, parent_layout):
        """Create filters and search section"""
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(12)
        
        # Search box
        search_box = QLineEdit()
        search_box.setObjectName("searchBox")
        search_box.setPlaceholderText("חיפוש ברכישות...")
        search_box.setFixedHeight(40)
        search_box.setStyleSheet("""
            QLineEdit#searchBox {
                padding: 10px 16px;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                background-color: #FFFFFF;
                font-size: 14px;
                color: #1E293B;
            }
            QLineEdit#searchBox:focus {
                border: 2px solid #3B82F6;
                background-color: #F8FAFC;
            }
            QLineEdit#searchBox::placeholder {
                color: #94A3B8;
            }
        """)
        search_box.textChanged.connect(self.filter_purchases)
        
        # Status filter
        status_filter = QComboBox()
        status_filter.setObjectName("statusFilter")
        status_filter.addItems(["כל הסטטוסים", "הושלם", "ממתין", "נכשל"])
        status_filter.setFixedHeight(40)
        status_filter.setStyleSheet("""
            QComboBox#statusFilter {
                padding: 8px 12px;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                background-color: #FFFFFF;
                font-size: 14px;
                color: #1E293B;
                min-width: 120px;
            }
            QComboBox#statusFilter:focus {
                border: 2px solid #3B82F6;
            }
            QComboBox#statusFilter::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox#statusFilter::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #64748B;
                margin-right: 8px;
            }
        """)
        status_filter.currentTextChanged.connect(self.filter_purchases)
        
        # Sort button
        sort_button = QPushButton("מיון לפי תאריך")
        sort_button.setObjectName("sortButton")
        sort_button.setFixedHeight(40)
        sort_button.setStyleSheet("""
            QPushButton#sortButton {
                background-color: #F1F5F9;
                color: #475569;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton#sortButton:hover {
                background-color: #E2E8F0;
                border-color: #CBD5E1;
            }
            QPushButton#sortButton:pressed {
                background-color: #CBD5E1;
            }
        """)
        sort_button.clicked.connect(self.toggle_sort)
        
        # Refresh button
        refresh_button = QPushButton("רענן")
        refresh_button.setObjectName("refreshButton")
        refresh_button.setFixedHeight(40)
        refresh_button.setStyleSheet("""
            QPushButton#refreshButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton#refreshButton:hover {
                background-color: #2563EB;
            }
            QPushButton#refreshButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        refresh_button.clicked.connect(self.refresh_data)
        
        filters_layout.addWidget(search_box)
        filters_layout.addWidget(status_filter)
        filters_layout.addWidget(sort_button)
        filters_layout.addWidget(refresh_button)
        filters_layout.addStretch()
        
        parent_layout.addLayout(filters_layout)

    def create_purchases_section(self, parent_layout):
        """Create purchases list section"""
        # Scroll area for purchases
        scroll_area = QScrollArea()
        scroll_area.setObjectName("purchasesScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea#purchasesScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Content widget for scroll area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        
        scroll_area.setWidget(self.content_widget)
        parent_layout.addWidget(scroll_area)

    def load_purchase_data(self):
        """Load purchase data from Firebase database"""
        if not self.current_user:
            logger.warning("No current user, cannot load purchase data")
            self.show_error_state("לא מחובר למשתמש")
            return
        
        user_id = self.current_user.get('uid')
        if not user_id:
            logger.warning("No user ID found")
            self.show_error_state("מזהה משתמש לא נמצא")
            return
        
        logger.info(f"Loading purchase data for user: {user_id}")
        
        # Check if Firebase client is authenticated
        if not self.firebase_client.id_token:
            logger.warning("Firebase client not authenticated")
            self.show_error_state("לא מחובר לשרת")
            return
        
        # Show loading state
        self.show_loading_state()
        
        try:
            # Fetch purchase history from database
            result = self.purchase_service.get_user_purchase_history(user_id)
            
            if result.get('success'):
                self.purchases = result.get('purchases', [])
                self.filtered_purchases = self.purchases.copy()
                
                logger.info(f"Loaded {len(self.purchases)} purchases from database")
                
                # Update stats and display
                self.update_stats_cards()
                self.update_purchases_display()
                
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Failed to load purchase data: {error_msg}")
                self.show_error_state(f"שגיאה בטעינת הנתונים: {error_msg}")
                
        except Exception as e:
            logger.exception("Exception while loading purchase data")
            self.show_error_state(f"שגיאה בטעינת הנתונים: {str(e)}")

    def show_loading_state(self):
        """Show loading state while fetching data"""
        # Clear existing content
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Create loading frame
        loading_frame = QFrame()
        loading_frame.setObjectName("loadingState")
        loading_frame.setFixedHeight(200)
        loading_frame.setStyleSheet("""
            QFrame#loadingState {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F8FAFC, stop:1 #F1F5F9);
                border: 1px solid #E2E8F0;
                border-radius: 20px;
                margin: 20px;
            }
        """)
        
        layout = QVBoxLayout(loading_frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        # Loading spinner (animated dots)
        spinner_label = QLabel("⏳")
        spinner_label.setFont(QFont("Segoe UI", 32))
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinner_label.setStyleSheet("color: #3B82F6;")
        
        # Loading text
        loading_text = QLabel("טוען נתונים...")
        loading_text.setFont(QFont("Segoe UI", 16))
        loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_text.setStyleSheet("color: #64748B;")
        
        layout.addWidget(spinner_label)
        layout.addWidget(loading_text)
        
        self.content_layout.addWidget(loading_frame)

    def show_error_state(self, error_message):
        """Show error state when data loading fails"""
        # Clear existing content
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Create error frame
        error_frame = QFrame()
        error_frame.setObjectName("errorState")
        error_frame.setFixedHeight(200)
        error_frame.setStyleSheet("""
            QFrame#errorState {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FEF2F2, stop:1 #FEE2E2);
                border: 1px solid #FECACA;
                border-radius: 20px;
                margin: 20px;
            }
        """)
        
        layout = QVBoxLayout(error_frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        # Error icon
        error_icon = QLabel("⚠️")
        error_icon.setFont(QFont("Segoe UI", 32))
        error_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_icon.setStyleSheet("color: #EF4444;")
        
        # Error message
        error_text = QLabel(error_message)
        error_text.setFont(QFont("Segoe UI", 14))
        error_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_text.setStyleSheet("color: #991B1B;")
        error_text.setWordWrap(True)
        
        # Retry button
        retry_button = QPushButton("נסה שוב")
        retry_button.setObjectName("retryButton")
        retry_button.setFixedHeight(40)
        retry_button.setStyleSheet("""
            QPushButton#retryButton {
                background-color: #EF4444;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton#retryButton:hover {
                background-color: #DC2626;
            }
            QPushButton#retryButton:pressed {
                background-color: #B91C1C;
            }
        """)
        retry_button.clicked.connect(self.load_purchase_data)
        
        layout.addWidget(error_icon)
        layout.addWidget(error_text)
        layout.addWidget(retry_button)
        
        self.content_layout.addWidget(error_frame)

    def update_purchases_display(self):
        """Update the purchases display"""
        # Clear existing cards
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Check if there are purchases to display
        if not self.filtered_purchases:
            self.show_empty_state()
        else:
            # Add purchase cards
            for purchase in self.filtered_purchases:
                card = PurchaseCard(purchase)
                self.content_layout.addWidget(card)
        
        # Add stretch to push cards to top
        self.content_layout.addStretch()

    def show_empty_state(self):
        """Show empty state when no purchases are found"""
        empty_frame = QFrame()
        empty_frame.setObjectName("emptyState")
        empty_frame.setFixedHeight(300)
        empty_frame.setStyleSheet("""
            QFrame#emptyState {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F8FAFC, stop:1 #F1F5F9);
                border: 2px dashed #CBD5E1;
                border-radius: 20px;
                margin: 20px;
            }
        """)
        
        layout = QVBoxLayout(empty_frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        # Empty state icon
        icon_label = QLabel("📋")
        icon_label.setFont(QFont("Segoe UI", 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #94A3B8;")
        
        # Empty state title
        title_label = QLabel("אין רכישות להצגה")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #64748B;")
        
        # Empty state subtitle
        subtitle_label = QLabel("הרכישות שלך יופיעו כאן לאחר שתרכוש חבילות זמן")
        subtitle_label.setFont(QFont("Segoe UI", 14))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #94A3B8;")
        subtitle_label.setWordWrap(True)
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        
        self.content_layout.addWidget(empty_frame)

    def filter_purchases(self):
        """Filter purchases based on search and status"""
        search_text = self.sender().text().lower() if hasattr(self.sender(), 'text') else ""
        status_filter = "כל הסטטוסים"  # Default
        
        # Get current filter values
        for widget in self.findChildren(QComboBox):
            if widget.objectName() == "statusFilter":
                status_filter = widget.currentText()
                break
        
        self.filtered_purchases = []
        
        for purchase in self.purchases:
            # Search filter - search in package name, amount, and date
            if search_text:
                package_name = purchase.get('packageName', '').lower()
                amount_str = str(purchase.get('amount', '')).lower()
                date_str = purchase.get('createdAt', '').lower()
                
                if (search_text not in package_name and 
                    search_text not in amount_str and 
                    search_text not in date_str):
                    continue
            
            # Status filter
            if status_filter != "כל הסטטוסים":
                status_map = {
                    "הושלם": "completed",
                    "ממתין": "pending", 
                    "נכשל": "failed"
                }
                if purchase.get('status') != status_map.get(status_filter):
                    continue
            
            self.filtered_purchases.append(purchase)
        
        self.update_purchases_display()

    def toggle_sort(self):
        """Toggle sort order"""
        self.filtered_purchases.reverse()
        self.update_purchases_display()

    def refresh_data(self):
        """Refresh purchase data from database"""
        logger.info("Refreshing purchase data from database")
        self.load_purchase_data()
        self.animate_refresh()

    def update_stats_cards(self):
        """Update statistics cards with current data"""
        # Clear existing stats cards
        for i in reversed(range(self.stats_layout.count())):
            child = self.stats_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Calculate stats from current purchases
        total_spent = sum(self._safe_int(p.get('amount', 0)) for p in self.purchases if p.get('status') == 'completed')
        total_purchases = len([p for p in self.purchases if p.get('status') == 'completed'])
        pending_purchases = len([p for p in self.purchases if p.get('status') == 'pending'])
        
        # Total spent card
        spent_card = StatsCard(
            "סכום כולל",
            f"₪{total_spent}",
            f"מ-{total_purchases} רכישות",
            "#059669"
        )
        
        # Total purchases card
        purchases_card = StatsCard(
            "רכישות הושלמו",
            str(total_purchases),
            "עסקאות מוצלחות",
            "#059669"  # Green to match completed status
        )
        
        # Pending card
        pending_card = StatsCard(
            "ממתינות",
            str(pending_purchases),
            "עסקאות בהמתנה",
            "#6B7280"  # Much more subtle gray color instead of orange
        )
        
        self.stats_layout.addWidget(spent_card)
        self.stats_layout.addWidget(purchases_card)
        self.stats_layout.addWidget(pending_card)
        self.stats_layout.addStretch()

    def animate_refresh(self):
        """Animate refresh action"""
        # Create a subtle animation for the refresh
        for card in self.findChildren(PurchaseCard):
            card.setStyleSheet(card.styleSheet() + """
                QFrame#purchaseCard {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #F0F9FF, stop:1 #E0F2FE);
                    border: 1px solid #0EA5E9;
                }
            """)
        
        # Reset after animation
        QTimer.singleShot(500, self.reset_card_styles)

    def reset_card_styles(self):
        """Reset card styles after refresh animation"""
        for card in self.findChildren(PurchaseCard):
            card.setStyleSheet("""
                QFrame#purchaseCard {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #FFFFFF, stop:1 #F8FAFC);
                    border: 1px solid #E2E8F0;
                    border-radius: 16px;
                    margin: 8px;
                }
                QFrame#purchaseCard:hover {
                    border: 1px solid #3B82F6;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #FFFFFF, stop:1 #F0F9FF);
                }
            """)

    def setup_animations(self):
        """Setup page animations"""
        # Fade in animation for the page
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Start animation
        QTimer.singleShot(100, self.fade_animation.start)

    def _safe_int(self, value, default=0):
        """Safely convert value to integer, handling strings and None"""
        if value is None:
            return default
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return default
"""
Payment Dialog with Firebase Real-Time Listener
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import Qt, QUrl, QTimer
from pathlib import Path
import os
import json
import requests

from services.payment_bridge import PaymentBridge
from services.purchase_service import PurchaseService
from utils.logger import get_logger

logger = get_logger(__name__)


class PaymentDialog(QDialog):
    """Payment dialog with server-side verification.

    Refactored to derive dependencies (user, auth_service) from the given parent
    widget to reduce parameter coupling.
    """

    def __init__(self, package: dict, parent=None):
        super().__init__(parent)

        self.package = package

        # Derive dependencies from parent (e.g., PackagesPage)
        self.auth_service = getattr(parent, 'auth_service', None)
        derived_user = getattr(parent, 'current_user', None)

        if self.auth_service is None:
            logger.error("PaymentDialog could not find 'auth_service' on parent")
            raise ValueError("Parent must expose 'auth_service'")

        # Fallback to fetching from auth if not provided by parent
        if derived_user is None and hasattr(self.auth_service, 'get_current_user'):
            derived_user = self.auth_service.get_current_user()

        self.user = derived_user or {}
        self.payment_response = None
        self.purchase_id = None

        # Create pending purchase FIRST
        purchase_service = PurchaseService(self.auth_service.firebase)
        result = purchase_service.create_pending_purchase(
            self.user['uid'],
            self.package
        )

        if not result.get('success'):
            logger.error("Failed to create pending purchase")
            return

        self.purchase_id = result['purchase_id']
        logger.info(f"Pending purchase created: {self.purchase_id}")

        # Setup Firebase listener for purchase status
        self.setup_purchase_listener()

        self.init_ui()

    def setup_purchase_listener(self):
        """Setup Firebase real-time listener for purchase status"""
        # Poll Firebase every 2 seconds for status change
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_purchase_status)
        self.status_timer.start(2000)  # Check every 2 seconds

        self.check_count = 0
        self.max_checks = 150  # 5 minutes max (150 * 2s)

    def check_purchase_status(self):
        """Check if purchase was completed via callback"""
        self.check_count += 1

        if self.check_count > self.max_checks:
            logger.warning("Purchase verification timeout")
            self.status_timer.stop()
            return

        # Get purchase status from Firebase
        try:
            response = requests.get(
                f"{self.auth_service.firebase.database_url}/pendingPurchases/{self.purchase_id}.json",
                params={'auth': self.auth_service.firebase.id_token}
            )

            if response.status_code == 200:
                purchase = response.json()

                if purchase and purchase.get('status') == 'completed':
                    logger.info("Purchase completed via callback!")
                    self.status_timer.stop()

                    # Store payment response
                    self.payment_response = purchase.get('rawResponse', {})

                    # Close dialog with success
                    self.accept()

                elif purchase and purchase.get('status') == 'failed':
                    logger.error("Purchase failed via callback")
                    self.status_timer.stop()
                    # Dialog stays open to show error

        except Exception as e:
            logger.error(f"Failed to check purchase status: {e}")

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("תשלום מאובטח - Secure Payment")

        # Allow resize and maximize
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        # Set size - INCREASED HEIGHT
        self.setMinimumSize(800, 900)
        self.resize(900, 1050)

        # Center on screen
        self.center_on_screen()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Web view
        self.web_view = QWebEngineView()

        # Setup web channel
        self.channel = QWebChannel()
        self.bridge = PaymentBridge()
        self.channel.registerObject('payment_bridge', self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # Connect signals
        self.bridge.payment_success.connect(self.on_payment_success)
        self.bridge.payment_cancelled.connect(self.on_payment_cancelled)

        # Load HTML
        html_path = Path(__file__).parent.parent / 'templates' / 'payment.html'

        if not html_path.exists():
            logger.error(f"Payment HTML not found: {html_path}")
            return

        self.web_view.setUrl(QUrl.fromLocalFile(str(html_path.absolute())))
        self.web_view.loadFinished.connect(self.on_page_loaded)

        layout.addWidget(self.web_view)

        logger.info("Payment dialog initialized")

    def center_on_screen(self):
        """Center dialog on screen"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def on_page_loaded(self, success: bool):
        """Page loaded, inject configuration"""
        if not success:
            logger.error("Failed to load payment page")
            return

        # Get credentials
        mosad_id = os.getenv('NEDARIM_MOSAD_ID', '')
        api_valid = os.getenv('NEDARIM_API_VALID', '')
        callback_url = os.getenv('NEDARIM_CALLBACK_URL', '')

        if not mosad_id or not api_valid:
            logger.error("Missing Nedarim Plus credentials")
            return

        # Calculate price
        from services.package_service import PackageService
        pricing = PackageService.calculate_final_price(self.package)

        # Configuration with CALLBACK URL and PURCHASE ID
        config = {
            'mosadId': mosad_id,
            'apiValid': api_valid,
            'amount': str(int(pricing['final_price'])),
            'packageName': self.package.get('name', ''),
            'packageMinutes': str(self.package.get('minutes', 0)),
            'packagePrints': str(self.package.get('prints', 0)),
            'userName': f"{self.user.get('firstName', '')} {self.user.get('lastName', '')}",
            'callbackUrl': callback_url,
            'purchaseId': self.purchase_id
        }

        js_code = f"setConfig({json.dumps(config)});"
        self.web_view.page().runJavaScript(js_code)

        logger.debug("Configuration injected")

    def on_payment_success(self, response: dict):
        """Handle payment success from JavaScript (immediate feedback)"""
        logger.info("Payment initiated successfully (waiting for callback)")

    def on_payment_cancelled(self):
        """Handle cancellation"""
        logger.info("Payment cancelled")
        self.status_timer.stop()
        self.reject()

    def get_payment_response(self):
        """Get payment response after dialog closes"""
        return self.payment_response

    def closeEvent(self, event):
        """Cleanup when dialog closes"""
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        super().closeEvent(event)
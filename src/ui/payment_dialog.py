"""
Payment Dialog
Full-screen payment interface with Nedarim Plus integration
"""
import json

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import Qt, QUrl
from pathlib import Path
import os

from services.payment_bridge import PaymentBridge
from utils.logger import get_logger

logger = get_logger(__name__)


class PaymentDialog(QDialog):
    """Full-screen payment dialog with embedded web view"""

    def __init__(self, package: dict, user: dict, parent=None):
        super().__init__(parent)

        self.package = package
        self.user = user
        self.payment_response = None

        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("תשלום מאובטח - Secure Payment")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMaximizeButtonHint)

        # Make dialog large
        self.resize(900, 800)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Web view
        self.web_view = QWebEngineView()

        # Setup web channel for JS-Python communication
        self.channel = QWebChannel()
        self.bridge = PaymentBridge()
        self.channel.registerObject('payment_bridge', self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # Connect signals
        self.bridge.payment_success.connect(self.on_payment_success)
        self.bridge.payment_cancelled.connect(self.on_payment_cancelled)

        # Load HTML
        html_path = Path(__file__).parent.parent / 'templates' / 'payment.html'
        self.web_view.setUrl(QUrl.fromLocalFile(str(html_path)))

        # Wait for page to load, then inject configuration
        self.web_view.loadFinished.connect(self.on_page_loaded)

        layout.addWidget(self.web_view)

        logger.info("Payment dialog initialized")

    def on_page_loaded(self, success: bool):
        """Page loaded, inject configuration"""
        if not success:
            logger.error("Failed to load payment page")
            return

        # Get credentials from environment
        mosad_id = os.getenv('NEDARIM_MOSAD_ID', '')
        api_valid = os.getenv('NEDARIM_API_VALID', '')

        # Calculate final price
        from services.package_service import PackageService
        pricing = PackageService.calculate_final_price(self.package)

        # Prepare configuration
        config = {
            'mosadId': mosad_id,
            'apiValid': api_valid,
            'amount': str(int(pricing['final_price'])),
            'packageName': self.package.get('name', ''),
            'packageMinutes': str(self.package.get('minutes', 0)),
            'packagePrints': str(self.package.get('prints', 0)),
            'userName': f"{self.user.get('firstName', '')} {self.user.get('lastName', '')}"
        }

        # Inject into JavaScript
        js_code = f"setConfig({json.dumps(config)});"
        self.web_view.page().runJavaScript(js_code)

        logger.debug("Configuration injected into payment page")

    def on_payment_success(self, response: dict):
        """Handle successful payment"""
        logger.info(f"Payment successful: {response}")
        self.payment_response = response
        self.accept()

    def on_payment_cancelled(self):
        """Handle payment cancellation"""
        logger.info("Payment cancelled")
        self.reject()

    def get_payment_response(self):
        """Get payment response after dialog closes"""
        return self.payment_response
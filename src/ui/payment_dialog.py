"""
Payment Dialog with Firebase Real-Time Listener
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal
from pathlib import Path
import os
import json
import requests
import threading
import time
import sseclient  # For Firebase streaming

from services.payment_bridge import PaymentBridge
from services.purchase_service import PurchaseService
from utils.logger import get_logger
from ui.web.local_server import LocalFileServer

logger = get_logger(__name__)


class FirebaseStreamListener(QThread):
    """Thread to listen for Firebase Realtime Database changes via streaming"""
    
    status_changed = pyqtSignal(dict)  # Emits purchase data when status changes
    
    def __init__(self, database_url: str, auth_token: str, purchase_id: str):
        super().__init__()
        self.database_url = database_url
        self.auth_token = auth_token
        self.purchase_id = purchase_id
        self.running = True
        
    def run(self):
        """Listen for changes to purchase status"""
        logger.info(f"Starting Firebase stream listener for purchase: {self.purchase_id}")
        
        try:
            # Firebase streaming endpoint
            stream_url = f"{self.database_url}/pendingPurchases/{self.purchase_id}.json"
            params = {'auth': self.auth_token}
            
            # Open streaming connection
            response = requests.get(stream_url, params=params, stream=True, timeout=300)
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if not self.running:
                    break
                    
                # Parse event data
                if event.data and event.data != 'null':
                    try:
                        purchase_data = json.loads(event.data)
                        logger.debug(f"Stream event: {event.event}, data: {purchase_data}")
                        
                        # Check if status changed to completed or failed
                        if isinstance(purchase_data, dict):
                            status = purchase_data.get('status')
                            if status in ['completed', 'failed']:
                                logger.info(f"Purchase status changed to: {status}")
                                self.status_changed.emit(purchase_data)
                                self.running = False
                                break
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse stream data: {event.data}")
                        
        except requests.exceptions.Timeout:
            logger.warning("Firebase stream timed out (5 minutes)")
        except Exception as e:
            logger.error(f"Firebase stream error: {e}")
            
        logger.info("Firebase stream listener stopped")
    
    def stop(self):
        """Stop the listener"""
        self.running = False


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
        self._local_server: LocalFileServer | None = None
        self.listener_thread = None
        self.listener_active = False

        # DON'T create pending purchase yet - wait for user to click "Pay"
        # This saves DB writes when users browse/close without paying

        self.init_ui()

    def setup_purchase_listener(self):
        """Setup Firebase real-time listener with exponential backoff fallback"""
        logger.info("Setting up purchase status listener")
        
        # Try Firebase streaming first (cheapest option)
        try:
            self.listener_thread = FirebaseStreamListener(
                self.auth_service.firebase.database_url,
                self.auth_service.firebase.id_token,
                self.purchase_id
            )
            self.listener_thread.status_changed.connect(self.on_purchase_completed)
            self.listener_thread.start()
            self.listener_active = True
            logger.info("Firebase stream listener started")
        except Exception as e:
            logger.warning(f"Failed to start stream listener, falling back to polling: {e}")
            self.start_exponential_backoff_polling()
    
    def start_exponential_backoff_polling(self):
        """Fallback: Poll with exponential backoff to reduce costs"""
        logger.info("Starting exponential backoff polling")
        
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_purchase_status)
        
        # Exponential backoff strategy
        self.check_count = 0
        self.poll_intervals = [
            2, 2, 2, 2, 2,           # First 10s: check every 2s (5 checks)
            3, 3, 3, 3, 3,           # Next 15s: every 3s (5 checks)
            5, 5, 5, 5, 5, 5,        # Next 30s: every 5s (6 checks)
            10, 10, 10, 10, 10, 10,  # Next minute: every 10s (6 checks)
        ]
        # After that: continue with 10s intervals until 5 minutes
        while sum(self.poll_intervals) < 300:  # 5 minutes total
            self.poll_intervals.append(10)
        
        self.current_interval_index = 0
        self.status_timer.start(self.poll_intervals[0] * 1000)
        logger.info(f"Polling started with {len(self.poll_intervals)} checks over 5 minutes")

    def check_purchase_status(self):
        """Check if purchase was completed via callback (with exponential backoff)"""
        self.check_count += 1

        if self.check_count >= len(self.poll_intervals):
            logger.warning("Purchase verification timeout (5 minutes)")
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

                if purchase and purchase.get('status') in ['completed', 'failed']:
                    logger.info(f"Purchase status: {purchase.get('status')}")
                    self.status_timer.stop()
                    self.on_purchase_completed(purchase)

        except Exception as e:
            logger.error(f"Failed to check purchase status: {e}")
        
        # Schedule next check with next interval
        self.current_interval_index += 1
        if self.current_interval_index < len(self.poll_intervals):
            next_interval = self.poll_intervals[self.current_interval_index]
            self.status_timer.setInterval(next_interval * 1000)
            logger.debug(f"Next poll in {next_interval}s")
    
    def on_purchase_completed(self, purchase_data: dict):
        """Handle purchase completion (from stream or polling)"""
        status = purchase_data.get('status')
        
        if status == 'completed':
            logger.info("Purchase completed successfully!")
            self.payment_response = purchase_data.get('rawResponse', {})
            self.accept()
        elif status == 'failed':
            logger.error("Purchase failed")
            # Dialog stays open to show error

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
        self.setMinimumSize(900, 1100)
        self.resize(1000, 1200)

        # Center on screen
        self.center_on_screen()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Web view
        self.web_view = QWebEngineView()
        # Keep default profile (works now); skip advanced debug/profile config

        # Setup web channel
        self.channel = QWebChannel()
        self.bridge = PaymentBridge()
        
        # Configure bridge with purchase creation capability
        purchase_service = PurchaseService(self.auth_service.firebase)
        self.bridge.set_purchase_data(purchase_service, self.user['uid'], self.package)
        
        self.channel.registerObject('payment_bridge', self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # Connect signals
        self.bridge.payment_success.connect(self.on_payment_success)
        self.bridge.payment_cancelled.connect(self.on_payment_cancelled)
        self.bridge.purchase_created.connect(self.on_purchase_created)

        # Load HTML via local http server (avoid file:// origin issues)
        html_dir = Path(__file__).parent.parent / 'templates'
        html_path = html_dir / 'payment.html'
        if not html_path.exists():
            logger.error(f"Payment HTML not found: {html_path}")
            return

        try:
            self._local_server = LocalFileServer(html_dir)
            self._local_server.start()
            page_url = QUrl(f"{self._local_server.base_url}/payment.html")
            self.web_view.setUrl(page_url)
        except Exception as e:
            logger.error(f"Failed starting local server: {e}")
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

    def on_purchase_created(self, purchase_id: str):
        """Called when JavaScript successfully creates pending purchase"""
        self.purchase_id = purchase_id
        logger.info(f"Purchase created, starting listener: {purchase_id}")
        
        # Now start listening for completion
        self.setup_purchase_listener()
    
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

        # Configuration WITHOUT purchase_id (will be added by JavaScript when user clicks pay)
        config = {
            'mosadId': mosad_id,
            'apiValid': api_valid,
            'amount': str(int(pricing['final_price'])),
            'packageName': self.package.get('name', ''),
            'packageMinutes': str(self.package.get('minutes', 0)),
            'packagePrints': str(self.package.get('prints', 0)),
            'userName': f"{self.user.get('firstName', '')} {self.user.get('lastName', '')}",
            'callbackUrl': callback_url,
            # purchaseId will be set by JavaScript after calling createPendingPurchase
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
        # Stop polling timer if active
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # Stop Firebase stream listener if active
        if self.listener_thread and self.listener_thread.isRunning():
            logger.info("Stopping Firebase stream listener")
            self.listener_thread.stop()
            self.listener_thread.wait(2000)  # Wait up to 2 seconds
            
        # Stop local HTTP server if running
        if self._local_server is not None:
            self._local_server.stop()
            self._local_server = None
            
        super().closeEvent(event)
"""
Payment Dialog with Firebase Real-Time Listener
"""

import json
import os
from pathlib import Path

import requests
from PyQt6.QtCore import Qt, QThread, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.organization_metadata_service import OrganizationMetadataService
from services.payment_bridge import PaymentBridge
from services.purchase_service import PurchaseService
from ui.web.local_server import LocalFileServer
from utils.logger import get_logger
from utils.purchase_constants import is_final_status


logger = get_logger(__name__)


class FirebaseStreamListener(QThread):
    """Thread to listen for Firebase Realtime Database changes via streaming"""

    status_changed = pyqtSignal(dict)  # Emits purchase data when status changes

    def __init__(
        self, database_url: str, auth_token: str, purchase_id: str, org_id: str
    ):
        super().__init__()
        self.database_url = database_url
        self.auth_token = auth_token
        self.purchase_id = purchase_id
        self.org_id = org_id
        self.running = True

    def run(self):
        """Listen for changes to purchase status using Firebase REST streaming"""
        logger.info(
            f"Starting Firebase stream listener for purchase: {self.purchase_id}"
        )

        try:
            # Firebase streaming endpoint with multi-tenancy
            org_path = f"organizations/{self.org_id}/purchases/{self.purchase_id}"
            stream_url = f"{self.database_url}/{org_path}.json"
            params = {"auth": self.auth_token}

            # Open streaming connection - Firebase uses a different streaming format
            response = requests.get(stream_url, params=params, stream=True, timeout=300)

            if response.status_code != 200:
                logger.error(
                    f"Firebase stream failed with status: {response.status_code}"
                )
                return

            # Firebase streaming sends data in chunks, not SSE format
            buffer = ""
            for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                if not self.running:
                    break

                if chunk:
                    buffer += chunk

                    # Look for complete JSON objects (Firebase sends them line by line)
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()

                        if line and line != "null":
                            try:
                                purchase_data = json.loads(line)
                                logger.debug(f"Firebase stream data: {purchase_data}")

                                # Check if status changed to completed or failed
                                if isinstance(purchase_data, dict):
                                    status = purchase_data.get("status")
                                    logger.info(f"Received status: {status}")
                                    if is_final_status(status):
                                        logger.info(
                                            f"Purchase status changed to final status: {status}"
                                        )
                                        self.status_changed.emit(purchase_data)
                                        self.running = False
                                        return
                            except json.JSONDecodeError as e:
                                logger.warning(
                                    f"Failed to parse Firebase stream data: {line}, error: {e}"
                                )

        except requests.exceptions.Timeout:
            logger.warning("Firebase stream timed out (5 minutes)")
        except Exception as e:
            logger.error(f"Firebase stream error: {e}")

        logger.info("Firebase stream listener stopped")

    def stop(self):
        """Stop the listener"""
        self.running = False
        if self.isRunning():
            self.quit()
            self.wait(1000)  # Wait up to 1 second for thread to finish


class PaymentDialog(QDialog):
    """Payment dialog with server-side verification.

    Refactored to derive dependencies (user, auth_service) from the given parent
    widget to reduce parameter coupling.
    """

    def __init__(self, package: dict, parent=None):
        super().__init__(parent)

        self.package = package

        logger.debug(
            "PaymentDialog received package",
            package_name=package.get("name"),
            price=package.get("price"),
            action="payment_init",
        )

        # Derive dependencies from parent (e.g., PackagesPage)
        self.auth_service = getattr(parent, "auth_service", None)

        if self.auth_service is None:
            logger.error("PaymentDialog could not find 'auth_service' on parent")
            raise ValueError("Parent must expose 'auth_service'")

        # ALWAYS get fresh user from auth_service - don't rely on cached page data
        # This fixes crashes when page's current_user is stale or None
        derived_user = None
        if hasattr(self.auth_service, "get_current_user"):
            derived_user = self.auth_service.get_current_user()
            logger.debug(
                "PaymentDialog fetched user from auth_service",
                has_user=derived_user is not None,
                has_uid=derived_user.get("uid") if derived_user else None,
            )

        # Fallback to parent's cached user if auth_service returns None
        if derived_user is None:
            derived_user = getattr(parent, "current_user", None)
            logger.debug(
                "PaymentDialog falling back to parent.current_user",
                has_user=derived_user is not None,
            )

        self.user = derived_user or {}
        
        # Validate user has required uid field
        if not self.user.get("uid"):
            logger.error(
                "PaymentDialog: No valid user with uid found",
                derived_user=derived_user,
                action="payment_init_failed",
            )
            raise ValueError("Cannot initiate payment: user not properly loaded")
        
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
        logger.debug(
            "Setting up purchase status listener",
            purchase_id=self.purchase_id,
            action="payment_listener",
        )

        # Try Firebase streaming first (cheapest option)
        try:
            self.listener_thread = FirebaseStreamListener(
                self.auth_service.firebase.database_url,
                self.auth_service.firebase.id_token,
                self.purchase_id,
                self.auth_service.firebase.org_id,  # MULTI-TENANCY
            )
            self.listener_thread.status_changed.connect(self.on_purchase_completed)
            self.listener_thread.start()
            self.listener_active = True
            logger.debug("Firebase stream listener started", action="payment_listener")

            # Also start polling as a backup in case streaming fails
            self.start_exponential_backoff_polling()

        except Exception as e:
            logger.error(f"Failed to start stream listener: {e}")
            logger.debug("Falling back to polling only", action="payment_listener")
            self.start_exponential_backoff_polling()

    def start_exponential_backoff_polling(self):
        """Fallback: Poll with exponential backoff to reduce costs"""
        logger.debug("Starting exponential backoff polling", action="payment_polling")

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_purchase_status)

        # Exponential backoff strategy
        self.check_count = 0
        self.poll_intervals = [
            2,
            2,
            2,
            2,
            2,  # First 10s: check every 2s (5 checks)
            3,
            3,
            3,
            3,
            3,  # Next 15s: every 3s (5 checks)
            5,
            5,
            5,
            5,
            5,
            5,  # Next 30s: every 5s (6 checks)
            10,
            10,
            10,
            10,
            10,
            10,  # Next minute: every 10s (6 checks)
        ]
        # After that: continue with 10s intervals until 5 minutes
        while sum(self.poll_intervals) < 300:  # 5 minutes total
            self.poll_intervals.append(10)

        self.current_interval_index = 0
        self.status_timer.start(self.poll_intervals[0] * 1000)
        logger.debug(
            "Polling started", checks=len(self.poll_intervals), action="payment_polling"
        )

    def check_purchase_status(self):
        """Check if purchase was completed via callback (with exponential backoff)"""
        self.check_count += 1
        logger.debug(
            "Polling purchase status",
            attempt=self.check_count,
            action="payment_polling",
        )

        if self.check_count >= len(self.poll_intervals):
            logger.warning("Purchase verification timeout (5 minutes)")
            self.status_timer.stop()
            return

        # Get purchase status from Firebase with multi-tenancy
        try:
            org_path = f"organizations/{self.auth_service.firebase.org_id}/purchases/{self.purchase_id}"
            url = f"{self.auth_service.firebase.database_url}/{org_path}.json"
            logger.debug("Polling purchase status", action="payment_polling")

            response = requests.get(
                url, params={"auth": self.auth_service.firebase.id_token}, timeout=10
            )

            logger.debug(
                "Poll response received",
                status=response.status_code,
                action="payment_polling",
            )

            if response.status_code == 200:
                purchase = response.json()
                logger.debug(
                    "Purchase data received",
                    status=purchase.get("status"),
                    action="payment_polling",
                )

                if purchase and is_final_status(purchase.get("status")):
                    logger.info(
                        "Purchase status detected",
                        status=purchase.get("status"),
                        action="payment_polling",
                    )
                    self.status_timer.stop()
                    # Stop the stream listener if it's still running
                    if self.listener_thread and self.listener_thread.isRunning():
                        self.listener_thread.stop()
                    self.on_purchase_completed(purchase)
                    return
                elif purchase:
                    logger.debug(
                        "Purchase status pending",
                        status=purchase.get("status"),
                        action="payment_polling",
                    )
                else:
                    logger.warning("Purchase not found in database")
            else:
                logger.error(
                    f"Failed to fetch purchase status: HTTP {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Failed to check purchase status: {e}")

        # Schedule next check with next interval
        self.current_interval_index += 1
        if self.current_interval_index < len(self.poll_intervals):
            next_interval = self.poll_intervals[self.current_interval_index]
            self.status_timer.setInterval(next_interval * 1000)
            logger.debug(
                "Next poll scheduled", interval=next_interval, action="payment_polling"
            )

    def on_purchase_completed(self, purchase_data: dict):
        """Handle purchase completion (from stream or polling)"""
        status = purchase_data.get("status")

        if status == "completed":
            logger.info("Purchase completed successfully!")
            self.payment_response = purchase_data.get("rawResponse", {})

            # Show success message via JavaScript (not Python overlay)
            self.show_success_via_javascript()
        elif status == "failed":
            logger.error("Purchase failed")
            # Dialog stays open to show error

    def show_success_via_javascript(self):
        """Show success message via JavaScript (called when database confirms completion)"""
        try:
            # Call JavaScript showSuccess function
            js_code = "showSuccess();"
            self.web_view.page().runJavaScript(js_code)
            logger.info("Success message displayed via JavaScript")
        except Exception as e:
            logger.error(f"Error calling JavaScript showSuccess: {e}")
            # Fallback: use Python overlay
            self.show_success_message()

    def show_success_message(self):
        """Show success message and auto-close dialog"""
        try:
            # Create success overlay
            success_widget = QWidget()
            success_widget.setObjectName("successOverlay")
            success_widget.setStyleSheet(
                """
                #successOverlay {
                    background-color: rgba(16, 185, 129, 0.95);
                    border-radius: 12px;
                }
            """
            )

            layout = QVBoxLayout(success_widget)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setSpacing(20)

            # Success icon
            icon_label = QLabel("✅")
            icon_label.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("color: #FFFFFF;")

            # Success message
            message_label = QLabel("התשלום הושלם בהצלחה!")
            message_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_label.setStyleSheet("color: #FFFFFF;")

            # Sub message
            sub_message = QLabel("ניתן לחזור לעמוד הבית ולראות את הזמן וההדפסות החדשים")
            sub_message.setFont(QFont("Segoe UI", 14))
            sub_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sub_message.setStyleSheet("color: #FFFFFF; opacity: 0.9;")
            sub_message.setWordWrap(True)

            # Countdown message
            countdown_label = QLabel("החלון ייסגר בעוד 3 שניות...")
            countdown_label.setFont(QFont("Segoe UI", 12))
            countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            countdown_label.setStyleSheet("color: #FFFFFF; opacity: 0.8;")

            layout.addWidget(icon_label)
            layout.addWidget(message_label)
            layout.addWidget(sub_message)
            layout.addWidget(countdown_label)

            # Replace web view with success message
            self.web_view.hide()
            self.layout().addWidget(success_widget)

            # Start countdown timer
            self.countdown_timer = QTimer()
            self.countdown_timer.timeout.connect(self.close_dialog)
            self.countdown_timer.start(3000)  # 3 seconds

            logger.info("Success message displayed, dialog will close in 3 seconds")

        except Exception as e:
            logger.error(f"Error showing success message: {e}")
            # Fallback: close immediately
            self.accept()

    def close_dialog(self):
        """Close the dialog after countdown"""
        self.countdown_timer.stop()
        self.accept()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("תשלום מאובטח - Secure Payment")

        # Allow resize and maximize
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
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
        self.bridge.set_purchase_data(purchase_service, self.user["uid"], self.package)

        self.channel.registerObject("payment_bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # Connect signals
        self.bridge.payment_success.connect(self.on_payment_success)
        self.bridge.payment_cancelled.connect(self.on_payment_cancelled)
        self.bridge.purchase_created.connect(self.on_purchase_created)

        # Load HTML via local http server (avoid file:// origin issues)
        html_dir = Path(__file__).parent.parent / "templates"
        html_path = html_dir / "payment.html"
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

        # Get credentials from organization metadata
        org_metadata_service = OrganizationMetadataService(self.auth_service.firebase)
        credentials_result = org_metadata_service.get_nedarim_credentials(
            self.auth_service.firebase.org_id
        )

        if not credentials_result["success"]:
            logger.error(
                f"Failed to get NEDARIM credentials: {credentials_result['error']}"
            )
            # Show error message to user instead of silently failing
            self.show_credentials_error(credentials_result["error"])
            return

        credentials = credentials_result["credentials"]
        mosad_id = credentials["mosad_id"]
        api_valid = credentials["api_valid"]
        callback_url = os.getenv(
            "NEDARIM_CALLBACK_URL", ""
        )  # Keep callback URL from env for now

        if not mosad_id or not api_valid:
            logger.error("Missing Nedarim Plus credentials")
            self.show_credentials_error("Missing Nedarim Plus credentials")
            return

        # Calculate price
        from services.package_service import PackageService

        pricing = PackageService.calculate_final_price(self.package)

        logger.debug(
            "Pricing calculation",
            original_price=pricing["original_price"],
            final_price=pricing["final_price"],
            action="payment_calc",
        )

        # Calculate amount as string for JavaScript
        amount_str = str(int(pricing["final_price"]))
        logger.debug("Amount calculated", amount=amount_str, action="payment_calc")

        # Configuration WITHOUT purchase_id (will be added by JavaScript when user clicks pay)
        config = {
            "mosadId": mosad_id,
            "apiValid": api_valid,
            "amount": amount_str,
            "packageName": self.package.get("name", ""),
            "packageMinutes": str(self.package.get("minutes", 0)),
            "packagePrints": str(self.package.get("prints", 0)),
            "userName": f"{self.user.get('firstName', '')} {self.user.get('lastName', '')}",
            "callbackUrl": callback_url,
            "orgId": self.auth_service.firebase.org_id,  # MULTI-TENANCY: Pass org to payment gateway
            # purchaseId will be set by JavaScript after calling createPendingPurchase
        }

        js_code = f"setConfig({json.dumps(config)});"
        logger.debug("JavaScript config prepared", action="payment_init")
        self.web_view.page().runJavaScript(js_code)

        logger.debug("Configuration injected")

    def show_credentials_error(self, error_message: str):
        """Show error message when credentials fail to load"""
        try:
            # Create error overlay
            error_widget = QWidget()
            error_widget.setObjectName("errorOverlay")
            error_widget.setStyleSheet(
                """
                #errorOverlay {
                    background-color: rgba(239, 68, 68, 0.95);
                    border-radius: 12px;
                }
            """
            )

            layout = QVBoxLayout(error_widget)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setSpacing(20)

            # Error icon
            icon_label = QLabel("❌")
            icon_label.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("color: #FFFFFF;")

            # Error message
            message_label = QLabel("שגיאה בטעינת נתוני התשלום")
            message_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_label.setStyleSheet("color: #FFFFFF;")

            # Sub message
            sub_message = QLabel(f"פרטים: {error_message}")
            sub_message.setFont(QFont("Segoe UI", 14))
            sub_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sub_message.setStyleSheet("color: #FFFFFF; opacity: 0.9;")
            sub_message.setWordWrap(True)

            # Close button
            close_btn = QPushButton("סגור")
            close_btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            close_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #FFFFFF;
                    color: #DC2626;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F3F4F6;
                }
            """
            )
            close_btn.clicked.connect(self.reject)

            layout.addWidget(icon_label)
            layout.addWidget(message_label)
            layout.addWidget(sub_message)
            layout.addWidget(close_btn)

            # Replace web view with error message
            self.web_view.hide()
            self.layout().addWidget(error_widget)

            logger.error(f"Credentials error displayed: {error_message}")

        except Exception as e:
            logger.error(f"Error showing credentials error: {e}")
            # Fallback: close immediately
            self.reject()

    def on_payment_success(self, response: dict):
        """Handle payment success from JavaScript (immediate feedback)"""
        logger.info("Payment initiated successfully (waiting for callback)")

    def on_payment_cancelled(self):
        """Handle cancellation"""
        logger.info("Payment cancelled")

        # Stop polling timer if it exists (only exists for fallback polling)
        if hasattr(self, "status_timer"):
            self.status_timer.stop()

        # Stop Firebase stream listener if active
        if self.listener_thread and self.listener_thread.isRunning():
            self.listener_thread.stop()

        self.reject()

    def get_payment_response(self):
        """Get payment response after dialog closes"""
        return self.payment_response

    def closeEvent(self, event):
        """Cleanup when dialog closes"""
        # Stop polling timer if active
        if hasattr(self, "status_timer"):
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

"""
Payment Bridge
Communication between Python and JavaScript payment form
"""

import json

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from utils.logger import get_logger


logger = get_logger(__name__)


class PaymentBridge(QObject):
    """Bridge for Python-JavaScript communication"""

    payment_success = pyqtSignal(dict)
    payment_cancelled = pyqtSignal()
    purchase_created = pyqtSignal(str)  # Emits purchase_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.purchase_service = None
        self.user_id = None
        self.package = None

    def set_purchase_data(self, purchase_service, user_id: str, package: dict):
        """Set data needed to create purchases"""
        self.purchase_service = purchase_service
        self.user_id = user_id
        self.package = package

    @pyqtSlot(result=str)
    def createPendingPurchase(self) -> str:
        """Called from JavaScript to create pending purchase before payment"""
        logger.info("JavaScript requested pending purchase creation")

        if not self.purchase_service or not self.user_id:
            logger.error("Purchase service not configured")
            return json.dumps({"success": False, "error": "Not configured"})

        try:
            result = self.purchase_service.create_pending_purchase(
                self.user_id, self.package
            )

            if result.get("success"):
                purchase_id = result["purchase_id"]
                logger.info(f"Pending purchase created: {purchase_id}")
                self.purchase_created.emit(purchase_id)

            return json.dumps(result)
        except Exception as e:
            logger.exception("Failed to create pending purchase")
            return json.dumps({"success": False, "error": str(e)})

    @pyqtSlot(str)
    def paymentSuccess(self, response_json: str):
        """Called from JavaScript when payment succeeds"""
        try:
            response = json.loads(response_json)
            logger.info(f"Payment successful: {response.get('TransactionId')}")
            self.payment_success.emit(response)
        except Exception as e:
            logger.error(f"Failed to parse payment response: {e}")

    @pyqtSlot()
    def paymentCancelled(self):
        """Called from JavaScript when user cancels"""
        logger.info("Payment cancelled by user")
        self.payment_cancelled.emit()

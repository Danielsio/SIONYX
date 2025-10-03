"""
Payment Bridge
Communication between Python and JavaScript payment form
"""

from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal
import json
from utils.logger import get_logger

logger = get_logger(__name__)


class PaymentBridge(QObject):
    """Bridge for Python-JavaScript communication"""

    payment_success = pyqtSignal(dict)
    payment_cancelled = pyqtSignal()

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
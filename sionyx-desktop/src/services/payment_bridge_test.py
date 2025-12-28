"""
Tests for payment_bridge.py - Payment Bridge
Tests Python-JavaScript communication for payment processing.
"""

import json
import pytest
from unittest.mock import Mock, patch
from PyQt6.QtCore import QObject


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def payment_bridge(qapp):
    """Create PaymentBridge instance"""
    from services.payment_bridge import PaymentBridge
    
    bridge = PaymentBridge()
    return bridge


@pytest.fixture
def mock_purchase_service():
    """Create mock purchase service"""
    service = Mock()
    service.create_pending_purchase.return_value = {
        "success": True,
        "purchase_id": "purchase-123"
    }
    return service


# =============================================================================
# Test initialization
# =============================================================================
class TestPaymentBridgeInit:
    """Tests for PaymentBridge initialization"""

    def test_inherits_from_qobject(self, payment_bridge):
        """Test bridge inherits from QObject"""
        assert isinstance(payment_bridge, QObject)

    def test_purchase_service_is_none_initially(self, payment_bridge):
        """Test purchase_service is None initially"""
        assert payment_bridge.purchase_service is None

    def test_user_id_is_none_initially(self, payment_bridge):
        """Test user_id is None initially"""
        assert payment_bridge.user_id is None

    def test_package_is_none_initially(self, payment_bridge):
        """Test package is None initially"""
        assert payment_bridge.package is None

    def test_has_payment_success_signal(self, payment_bridge):
        """Test bridge has payment_success signal"""
        assert hasattr(payment_bridge, "payment_success")

    def test_has_payment_cancelled_signal(self, payment_bridge):
        """Test bridge has payment_cancelled signal"""
        assert hasattr(payment_bridge, "payment_cancelled")

    def test_has_purchase_created_signal(self, payment_bridge):
        """Test bridge has purchase_created signal"""
        assert hasattr(payment_bridge, "purchase_created")


# =============================================================================
# Test set_purchase_data
# =============================================================================
class TestSetPurchaseData:
    """Tests for set_purchase_data method"""

    def test_sets_purchase_service(self, payment_bridge, mock_purchase_service):
        """Test set_purchase_data sets purchase_service"""
        payment_bridge.set_purchase_data(mock_purchase_service, "user-123", {"id": "pkg-1"})
        
        assert payment_bridge.purchase_service == mock_purchase_service

    def test_sets_user_id(self, payment_bridge, mock_purchase_service):
        """Test set_purchase_data sets user_id"""
        payment_bridge.set_purchase_data(mock_purchase_service, "user-123", {"id": "pkg-1"})
        
        assert payment_bridge.user_id == "user-123"

    def test_sets_package(self, payment_bridge, mock_purchase_service):
        """Test set_purchase_data sets package"""
        package = {"id": "pkg-1", "name": "Basic", "price": 100}
        payment_bridge.set_purchase_data(mock_purchase_service, "user-123", package)
        
        assert payment_bridge.package == package


# =============================================================================
# Test createPendingPurchase
# =============================================================================
class TestCreatePendingPurchase:
    """Tests for createPendingPurchase method"""

    def test_returns_error_when_not_configured(self, payment_bridge):
        """Test returns error when purchase service not configured"""
        result = payment_bridge.createPendingPurchase()
        data = json.loads(result)
        
        assert data["success"] is False
        assert "Not configured" in data["error"]

    def test_calls_create_pending_purchase(self, payment_bridge, mock_purchase_service):
        """Test calls purchase service create_pending_purchase"""
        package = {"id": "pkg-1", "name": "Basic"}
        payment_bridge.set_purchase_data(mock_purchase_service, "user-123", package)
        
        payment_bridge.createPendingPurchase()
        
        mock_purchase_service.create_pending_purchase.assert_called_once_with("user-123", package)

    def test_returns_success_on_purchase_created(self, payment_bridge, mock_purchase_service):
        """Test returns success when purchase created"""
        payment_bridge.set_purchase_data(mock_purchase_service, "user-123", {"id": "pkg-1"})
        
        result = payment_bridge.createPendingPurchase()
        data = json.loads(result)
        
        assert data["success"] is True
        assert data["purchase_id"] == "purchase-123"

    def test_emits_purchase_created_signal(self, payment_bridge, mock_purchase_service):
        """Test emits purchase_created signal on success"""
        payment_bridge.set_purchase_data(mock_purchase_service, "user-123", {"id": "pkg-1"})
        
        signal_received = []
        payment_bridge.purchase_created.connect(lambda pid: signal_received.append(pid))
        
        payment_bridge.createPendingPurchase()
        
        assert len(signal_received) == 1
        assert signal_received[0] == "purchase-123"

    def test_returns_error_on_exception(self, payment_bridge, mock_purchase_service):
        """Test returns error on exception"""
        mock_purchase_service.create_pending_purchase.side_effect = Exception("Database error")
        payment_bridge.set_purchase_data(mock_purchase_service, "user-123", {"id": "pkg-1"})
        
        result = payment_bridge.createPendingPurchase()
        data = json.loads(result)
        
        assert data["success"] is False
        assert "Database error" in data["error"]

    def test_does_not_emit_signal_on_failure(self, payment_bridge, mock_purchase_service):
        """Test does not emit signal when purchase creation fails"""
        mock_purchase_service.create_pending_purchase.return_value = {"success": False, "error": "Failed"}
        payment_bridge.set_purchase_data(mock_purchase_service, "user-123", {"id": "pkg-1"})
        
        signal_received = []
        payment_bridge.purchase_created.connect(lambda pid: signal_received.append(pid))
        
        payment_bridge.createPendingPurchase()
        
        assert len(signal_received) == 0


# =============================================================================
# Test paymentSuccess
# =============================================================================
class TestPaymentSuccess:
    """Tests for paymentSuccess method"""

    def test_emits_payment_success_signal(self, payment_bridge):
        """Test emits payment_success signal with parsed response"""
        signal_received = []
        payment_bridge.payment_success.connect(lambda data: signal_received.append(data))
        
        response = {"TransactionId": "txn-123", "Amount": 100}
        payment_bridge.paymentSuccess(json.dumps(response))
        
        assert len(signal_received) == 1
        assert signal_received[0]["TransactionId"] == "txn-123"

    def test_handles_invalid_json(self, payment_bridge):
        """Test handles invalid JSON gracefully"""
        signal_received = []
        payment_bridge.payment_success.connect(lambda data: signal_received.append(data))
        
        # Should not raise, should log error
        payment_bridge.paymentSuccess("not valid json")
        
        # Signal should not be emitted
        assert len(signal_received) == 0


# =============================================================================
# Test paymentCancelled
# =============================================================================
class TestPaymentCancelled:
    """Tests for paymentCancelled method"""

    def test_emits_payment_cancelled_signal(self, payment_bridge):
        """Test emits payment_cancelled signal"""
        signal_received = []
        payment_bridge.payment_cancelled.connect(lambda: signal_received.append(True))
        
        payment_bridge.paymentCancelled()
        
        assert len(signal_received) == 1





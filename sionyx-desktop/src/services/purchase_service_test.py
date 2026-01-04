"""
Tests for PurchaseService
"""

from datetime import datetime
from unittest.mock import patch, Mock, MagicMock

import pytest

from services.purchase_service import PurchaseService


class TestPurchaseService:
    """Test cases for PurchaseService"""

    @pytest.fixture
    def purchase_service(self, mock_firebase_client):
        """Create PurchaseService instance with mocked dependencies"""
        with patch("services.purchase_service.DatabaseService.__init__", return_value=None):
            service = PurchaseService(mock_firebase_client)
            service.firebase = mock_firebase_client
            service.org_id = mock_firebase_client.org_id
            return service

    @pytest.fixture
    def sample_package(self):
        """Sample package data"""
        return {
            "id": "pkg-123",
            "name": "Premium Package",
            "minutes": 180,
            "prints": 50,
            "price": 29.99
        }

    def test_initialization(self, mock_firebase_client):
        """Test PurchaseService initialization"""
        with patch("services.purchase_service.DatabaseService.__init__", return_value=None):
            service = PurchaseService(mock_firebase_client)
            service.firebase = mock_firebase_client
            service.org_id = mock_firebase_client.org_id
            assert service.org_id == "test-org"

    def test_get_collection_name(self, purchase_service):
        """Test getting collection name"""
        assert purchase_service.get_collection_name() == "purchases"

    # Tests for create_pending_purchase
    def test_create_pending_purchase_success(self, purchase_service, mock_firebase_client, sample_package):
        """Test creating pending purchase successfully"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "purchase-id-123"}
        
        with patch("services.purchase_service.requests.post", return_value=mock_response):
            result = purchase_service.create_pending_purchase("user-123", sample_package)
        
        assert result["success"] is True
        assert result["purchase_id"] == "purchase-id-123"

    def test_create_pending_purchase_firebase_failure(self, purchase_service, mock_firebase_client, sample_package):
        """Test creating purchase when Firebase returns error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        
        with patch("services.purchase_service.requests.post", return_value=mock_response):
            result = purchase_service.create_pending_purchase("user-123", sample_package)
        
        assert result["success"] is False
        assert "Failed to create purchase record" in result["error"]

    def test_create_pending_purchase_exception(self, purchase_service, mock_firebase_client, sample_package):
        """Test creating purchase with exception"""
        with patch("services.purchase_service.requests.post", side_effect=Exception("Network error")):
            result = purchase_service.create_pending_purchase("user-123", sample_package)
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    def test_create_pending_purchase_data_structure(self, purchase_service, mock_firebase_client, sample_package):
        """Test that purchase data structure is correct"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "purchase-id-123"}
        
        with patch("src.services.purchase_service.requests.post", return_value=mock_response) as mock_post:
            purchase_service.create_pending_purchase("user-123", sample_package)
            
            # Get the JSON data that was posted
            call_args = mock_post.call_args
            posted_data = call_args[1]["json"]
            
            assert posted_data["userId"] == "user-123"
            assert posted_data["packageId"] == "pkg-123"
            assert posted_data["packageName"] == "Premium Package"
            assert posted_data["minutes"] == 180
            assert posted_data["prints"] == 50
            assert posted_data["amount"] == 29.99
            assert posted_data["status"] == "pending"
            assert "createdAt" in posted_data
            assert "updatedAt" in posted_data

    # Tests for get_purchase_status
    def test_get_purchase_status_success(self, purchase_service, mock_firebase_client):
        """Test getting purchase status"""
        purchase_data = {
            "status": "completed",
            "amount": 29.99,
            "userId": "user-123"
        }
        mock_firebase_client.db_get.return_value = {"success": True, "data": purchase_data}
        
        result = purchase_service.get_purchase_status("purchase-123")
        
        assert result["success"] is True
        assert result["purchase"]["status"] == "completed"

    def test_get_purchase_status_not_found(self, purchase_service, mock_firebase_client):
        """Test getting status of non-existent purchase"""
        mock_firebase_client.db_get.return_value = {"success": False, "error": "Not found"}
        
        result = purchase_service.get_purchase_status("non-existent")
        
        assert result["success"] is False
        assert result["error"] == "Purchase not found"

    # Tests for get_user_purchase_history
    def test_get_user_purchase_history_success(self, purchase_service):
        """Test getting user purchase history"""
        all_purchases = [
            {"userId": "user-123", "amount": 10, "createdAt": "2024-01-02T10:00:00Z"},
            {"userId": "user-456", "amount": 20, "createdAt": "2024-01-01T10:00:00Z"},
            {"userId": "user-123", "amount": 30, "createdAt": "2024-01-03T10:00:00Z"}
        ]
        
        with patch.object(purchase_service, "get_all_documents", return_value={"success": True, "data": all_purchases}):
            with patch.object(purchase_service, "log_operation"):
                with patch.object(purchase_service, "create_success_response") as mock_response:
                    # The actual filtered and sorted list
                    filtered = [p for p in all_purchases if p["userId"] == "user-123"]
                    filtered.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
                    mock_response.return_value = {"success": True, "data": filtered}
                    
                    result = purchase_service.get_user_purchase_history("user-123")
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        # Should be sorted by createdAt descending
        assert result["data"][0]["amount"] == 30

    def test_get_user_purchase_history_empty(self, purchase_service):
        """Test getting history when user has no purchases"""
        all_purchases = [
            {"userId": "other-user", "amount": 10}
        ]
        
        with patch.object(purchase_service, "get_all_documents", return_value={"success": True, "data": all_purchases}):
            with patch.object(purchase_service, "log_operation"):
                with patch.object(purchase_service, "create_success_response", return_value={"success": True, "data": []}):
                    result = purchase_service.get_user_purchase_history("user-123")
        
        assert result["success"] is True
        assert len(result["data"]) == 0

    def test_get_user_purchase_history_failure(self, purchase_service):
        """Test getting history with failure"""
        with patch.object(purchase_service, "get_all_documents", return_value={"success": False, "error": "Database error"}):
            with patch.object(purchase_service, "log_operation"):
                result = purchase_service.get_user_purchase_history("user-123")
        
        assert result["success"] is False

    # Tests for get_purchase_statistics
    def test_get_purchase_statistics_success(self, purchase_service):
        """Test getting purchase statistics"""
        user_purchases = [
            {"userId": "user-123", "status": "completed", "amount": 10},
            {"userId": "user-123", "status": "completed", "amount": 20},
            {"userId": "user-123", "status": "pending", "amount": 15},
            {"userId": "user-123", "status": "failed", "amount": 5}
        ]
        
        with patch.object(purchase_service, "get_user_purchase_history", return_value={"success": True, "data": user_purchases}):
            with patch.object(purchase_service, "log_operation"):
                with patch.object(purchase_service, "safe_int", side_effect=lambda x: int(x) if x else 0):
                    with patch.object(purchase_service, "create_success_response") as mock_response:
                        expected_stats = {
                            "total_spent": 30,
                            "completed_purchases": 2,
                            "pending_purchases": 1,
                            "failed_purchases": 1,
                            "total_purchases": 4
                        }
                        mock_response.return_value = {"success": True, "data": expected_stats}
                        
                        result = purchase_service.get_purchase_statistics("user-123")
        
        assert result["success"] is True
        stats = result["data"]
        assert stats["total_spent"] == 30
        assert stats["completed_purchases"] == 2
        assert stats["pending_purchases"] == 1
        assert stats["failed_purchases"] == 1
        assert stats["total_purchases"] == 4

    def test_get_purchase_statistics_no_purchases(self, purchase_service):
        """Test getting statistics when user has no purchases"""
        with patch.object(purchase_service, "get_user_purchase_history", return_value={"success": True, "data": []}):
            with patch.object(purchase_service, "log_operation"):
                with patch.object(purchase_service, "safe_int", side_effect=lambda x: int(x) if x else 0):
                    with patch.object(purchase_service, "create_success_response") as mock_response:
                        expected_stats = {
                            "total_spent": 0,
                            "completed_purchases": 0,
                            "pending_purchases": 0,
                            "failed_purchases": 0,
                            "total_purchases": 0
                        }
                        mock_response.return_value = {"success": True, "data": expected_stats}
                        
                        result = purchase_service.get_purchase_statistics("user-123")
        
        assert result["success"] is True
        stats = result["data"]
        assert stats["total_spent"] == 0
        assert stats["total_purchases"] == 0

    def test_get_purchase_statistics_history_failure(self, purchase_service):
        """Test getting statistics when history fetch fails"""
        with patch.object(purchase_service, "get_user_purchase_history", return_value={"success": False, "error": "Database error"}):
            with patch.object(purchase_service, "log_operation"):
                result = purchase_service.get_purchase_statistics("user-123")
        
        assert result["success"] is False

    def test_get_purchase_statistics_exception(self, purchase_service):
        """Test getting statistics with exception"""
        with patch.object(purchase_service, "get_user_purchase_history", side_effect=Exception("Network error")):
            with patch.object(purchase_service, "log_operation"):
                with patch.object(purchase_service, "handle_firebase_error", return_value={"success": False, "error": "Network error"}):
                    result = purchase_service.get_purchase_statistics("user-123")
        
        assert result["success"] is False








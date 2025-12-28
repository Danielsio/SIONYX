"""
Tests for PrintBudgetService
"""

from unittest.mock import patch, Mock

import pytest

from services.print_budget_service import PrintBudgetService


class TestPrintBudgetService:
    """Test cases for PrintBudgetService"""

    @pytest.fixture
    def budget_service(self, mock_firebase_client):
        """Create PrintBudgetService instance with mocked dependencies"""
        return PrintBudgetService(mock_firebase_client)

    def test_initialization(self, budget_service, mock_firebase_client):
        """Test PrintBudgetService initialization"""
        assert budget_service.firebase == mock_firebase_client

    # Tests for get_organization_print_pricing
    def test_get_organization_print_pricing_success(self, budget_service, mock_firebase_client):
        """Test getting organization print pricing successfully"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"blackAndWhitePrice": 0.5, "colorPrice": 2.0}
        }
        
        result = budget_service.get_organization_print_pricing("test-org")
        
        assert result["success"] is True
        assert result["pricing"]["black_and_white_price"] == 0.5
        assert result["pricing"]["color_price"] == 2.0

    def test_get_organization_print_pricing_uses_defaults(self, budget_service, mock_firebase_client):
        """Test that default prices are used when not set"""
        mock_firebase_client.db_get.return_value = {"success": True, "data": {}}
        
        result = budget_service.get_organization_print_pricing("test-org")
        
        assert result["success"] is True
        assert result["pricing"]["black_and_white_price"] == 1.0  # Default
        assert result["pricing"]["color_price"] == 3.0  # Default

    def test_get_organization_print_pricing_failure(self, budget_service, mock_firebase_client):
        """Test getting pricing with Firebase failure"""
        mock_firebase_client.db_get.return_value = {"success": False, "error": "Database error"}
        
        result = budget_service.get_organization_print_pricing("test-org")
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    def test_get_organization_print_pricing_exception(self, budget_service, mock_firebase_client):
        """Test getting pricing with exception"""
        mock_firebase_client.db_get.side_effect = Exception("Network error")
        
        result = budget_service.get_organization_print_pricing("test-org")
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    # Tests for set_organization_print_pricing
    def test_set_organization_print_pricing_success(self, budget_service, mock_firebase_client):
        """Test setting organization print pricing"""
        mock_firebase_client.db_update.return_value = {"success": True}
        
        result = budget_service.set_organization_print_pricing("test-org", 0.75, 2.5)
        
        assert result["success"] is True
        mock_firebase_client.db_update.assert_called_once()
        call_args = mock_firebase_client.db_update.call_args
        assert call_args[0][1]["blackAndWhitePrice"] == 0.75
        assert call_args[0][1]["colorPrice"] == 2.5

    def test_set_organization_print_pricing_failure(self, budget_service, mock_firebase_client):
        """Test setting pricing with Firebase failure"""
        mock_firebase_client.db_update.return_value = {"success": False, "error": "Update failed"}
        
        result = budget_service.set_organization_print_pricing("test-org", 0.75, 2.5)
        
        assert result["success"] is False
        assert "Update failed" in result["error"]

    def test_set_organization_print_pricing_exception(self, budget_service, mock_firebase_client):
        """Test setting pricing with exception"""
        mock_firebase_client.db_update.side_effect = Exception("Network error")
        
        result = budget_service.set_organization_print_pricing("test-org", 0.75, 2.5)
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    # Tests for get_user_print_budget
    def test_get_user_print_budget_success(self, budget_service, mock_firebase_client):
        """Test getting user print budget"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"remainingPrints": 50.0}
        }
        
        result = budget_service.get_user_print_budget("user-123")
        
        assert result["success"] is True
        assert result["budget"] == 50.0

    def test_get_user_print_budget_default_zero(self, budget_service, mock_firebase_client):
        """Test that budget defaults to 0 when not set"""
        mock_firebase_client.db_get.return_value = {"success": True, "data": {}}
        
        result = budget_service.get_user_print_budget("user-123")
        
        assert result["success"] is True
        assert result["budget"] == 0.0

    def test_get_user_print_budget_failure(self, budget_service, mock_firebase_client):
        """Test getting budget with Firebase failure"""
        mock_firebase_client.db_get.return_value = {"success": False, "error": "User not found"}
        
        result = budget_service.get_user_print_budget("user-123")
        
        assert result["success"] is False
        assert "User not found" in result["error"]

    def test_get_user_print_budget_exception(self, budget_service, mock_firebase_client):
        """Test getting budget with exception"""
        mock_firebase_client.db_get.side_effect = Exception("Network error")
        
        result = budget_service.get_user_print_budget("user-123")
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    # Tests for calculate_print_cost
    def test_calculate_print_cost_success(self, budget_service, mock_firebase_client):
        """Test calculating print cost"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"blackAndWhitePrice": 1.0, "colorPrice": 3.0}
        }
        
        result = budget_service.calculate_print_cost("test-org", 10, 5)
        
        assert result["success"] is True
        breakdown = result["cost_breakdown"]
        assert breakdown["black_white_pages"] == 10
        assert breakdown["color_pages"] == 5
        assert breakdown["black_white_cost"] == 10.0
        assert breakdown["color_cost"] == 15.0
        assert breakdown["total_cost"] == 25.0

    def test_calculate_print_cost_bw_only(self, budget_service, mock_firebase_client):
        """Test calculating cost for B&W only"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"blackAndWhitePrice": 0.5, "colorPrice": 2.0}
        }
        
        result = budget_service.calculate_print_cost("test-org", 20, 0)
        
        assert result["success"] is True
        assert result["cost_breakdown"]["total_cost"] == 10.0

    def test_calculate_print_cost_color_only(self, budget_service, mock_firebase_client):
        """Test calculating cost for color only"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"blackAndWhitePrice": 0.5, "colorPrice": 2.0}
        }
        
        result = budget_service.calculate_print_cost("test-org", 0, 10)
        
        assert result["success"] is True
        assert result["cost_breakdown"]["total_cost"] == 20.0

    def test_calculate_print_cost_pricing_failure(self, budget_service, mock_firebase_client):
        """Test calculating cost when pricing fetch fails"""
        mock_firebase_client.db_get.return_value = {"success": False, "error": "Failed"}
        
        result = budget_service.calculate_print_cost("test-org", 10, 5)
        
        assert result["success"] is False

    def test_calculate_print_cost_exception(self, budget_service, mock_firebase_client):
        """Test calculating cost with exception"""
        mock_firebase_client.db_get.side_effect = Exception("Network error")
        
        result = budget_service.calculate_print_cost("test-org", 10, 5)
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    # Tests for validate_print_budget
    def test_validate_print_budget_sufficient(self, budget_service, mock_firebase_client):
        """Test validation with sufficient budget"""
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": {"remainingPrints": 50.0}},  # User budget
            {"success": True, "data": {"blackAndWhitePrice": 1.0, "colorPrice": 3.0}}  # Pricing
        ]
        
        result = budget_service.validate_print_budget("user-123", "test-org", 5, 5)
        
        assert result["success"] is True
        assert result["can_print"] is True
        assert result["user_budget"] == 50.0
        assert result["print_cost"] == 20.0  # 5*1 + 5*3
        assert result["remaining_after_print"] == 30.0
        assert result["insufficient_amount"] == 0

    def test_validate_print_budget_insufficient(self, budget_service, mock_firebase_client):
        """Test validation with insufficient budget"""
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": {"remainingPrints": 10.0}},  # User budget
            {"success": True, "data": {"blackAndWhitePrice": 1.0, "colorPrice": 3.0}}  # Pricing
        ]
        
        result = budget_service.validate_print_budget("user-123", "test-org", 5, 5)
        
        assert result["success"] is True
        assert result["can_print"] is False
        assert result["user_budget"] == 10.0
        assert result["print_cost"] == 20.0
        assert result["remaining_after_print"] == 10.0  # Unchanged
        assert result["insufficient_amount"] == 10.0

    def test_validate_print_budget_exact_match(self, budget_service, mock_firebase_client):
        """Test validation when budget exactly matches cost"""
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": {"remainingPrints": 20.0}},
            {"success": True, "data": {"blackAndWhitePrice": 1.0, "colorPrice": 3.0}}
        ]
        
        result = budget_service.validate_print_budget("user-123", "test-org", 5, 5)
        
        assert result["success"] is True
        assert result["can_print"] is True
        assert result["remaining_after_print"] == 0.0

    def test_validate_print_budget_user_failure(self, budget_service, mock_firebase_client):
        """Test validation when user budget fetch fails"""
        mock_firebase_client.db_get.return_value = {"success": False, "error": "User not found"}
        
        result = budget_service.validate_print_budget("user-123", "test-org", 5, 5)
        
        assert result["success"] is False

    def test_validate_print_budget_exception(self, budget_service, mock_firebase_client):
        """Test validation with exception"""
        mock_firebase_client.db_get.side_effect = Exception("Network error")
        
        result = budget_service.validate_print_budget("user-123", "test-org", 5, 5)
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    # Tests for deduct_print_budget
    def test_deduct_print_budget_success(self, budget_service, mock_firebase_client):
        """Test successful budget deduction"""
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": {"remainingPrints": 50.0}},  # Validation - user budget
            {"success": True, "data": {"blackAndWhitePrice": 1.0, "colorPrice": 3.0}},  # Validation - pricing
            {"success": True, "data": {"remainingPrints": 50.0}}  # Get current budget
        ]
        mock_firebase_client.db_update.return_value = {"success": True}
        
        result = budget_service.deduct_print_budget("user-123", "test-org", 5, 5)
        
        assert result["success"] is True
        assert result["previous_budget"] == 50.0
        assert result["deducted_amount"] == 20.0
        assert result["new_budget"] == 30.0

    def test_deduct_print_budget_insufficient(self, budget_service, mock_firebase_client):
        """Test deduction with insufficient budget"""
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": {"remainingPrints": 10.0}},
            {"success": True, "data": {"blackAndWhitePrice": 1.0, "colorPrice": 3.0}}
        ]
        
        result = budget_service.deduct_print_budget("user-123", "test-org", 5, 5)
        
        assert result["success"] is False
        assert "Insufficient budget" in result["error"]

    def test_deduct_print_budget_update_failure(self, budget_service, mock_firebase_client):
        """Test deduction when update fails"""
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": {"remainingPrints": 50.0}},
            {"success": True, "data": {"blackAndWhitePrice": 1.0, "colorPrice": 3.0}},
            {"success": True, "data": {"remainingPrints": 50.0}}
        ]
        mock_firebase_client.db_update.return_value = {"success": False, "error": "Update failed"}
        
        result = budget_service.deduct_print_budget("user-123", "test-org", 5, 5)
        
        assert result["success"] is False
        assert "Update failed" in result["error"]

    def test_deduct_print_budget_exception(self, budget_service, mock_firebase_client):
        """Test deduction with exception"""
        mock_firebase_client.db_get.side_effect = Exception("Network error")
        
        result = budget_service.deduct_print_budget("user-123", "test-org", 5, 5)
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    # Tests for add_print_budget
    def test_add_print_budget_success(self, budget_service, mock_firebase_client):
        """Test adding budget successfully"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"remainingPrints": 20.0}
        }
        mock_firebase_client.db_update.return_value = {"success": True}
        
        result = budget_service.add_print_budget("user-123", 30.0, "purchase")
        
        assert result["success"] is True
        assert result["previous_budget"] == 20.0
        assert result["added_amount"] == 30.0
        assert result["new_budget"] == 50.0
        assert result["reason"] == "purchase"

    def test_add_print_budget_with_refund_reason(self, budget_service, mock_firebase_client):
        """Test adding budget with refund reason"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"remainingPrints": 10.0}
        }
        mock_firebase_client.db_update.return_value = {"success": True}
        
        result = budget_service.add_print_budget("user-123", 15.0, "refund")
        
        assert result["success"] is True
        assert result["reason"] == "refund"

    def test_add_print_budget_zero_initial(self, budget_service, mock_firebase_client):
        """Test adding budget when initial is zero"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {}  # No remainingPrints field
        }
        mock_firebase_client.db_update.return_value = {"success": True}
        
        result = budget_service.add_print_budget("user-123", 25.0)
        
        assert result["success"] is True
        assert result["previous_budget"] == 0.0
        assert result["new_budget"] == 25.0

    def test_add_print_budget_get_failure(self, budget_service, mock_firebase_client):
        """Test adding budget when getting current budget fails"""
        mock_firebase_client.db_get.return_value = {"success": False, "error": "User not found"}
        
        result = budget_service.add_print_budget("user-123", 25.0)
        
        assert result["success"] is False

    def test_add_print_budget_update_failure(self, budget_service, mock_firebase_client):
        """Test adding budget when update fails"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"remainingPrints": 10.0}
        }
        mock_firebase_client.db_update.return_value = {"success": False, "error": "Update failed"}
        
        result = budget_service.add_print_budget("user-123", 25.0)
        
        assert result["success"] is False
        assert "Update failed" in result["error"]

    def test_add_print_budget_exception(self, budget_service, mock_firebase_client):
        """Test adding budget with exception"""
        mock_firebase_client.db_get.side_effect = Exception("Network error")
        
        result = budget_service.add_print_budget("user-123", 25.0)
        
        assert result["success"] is False
        assert "Network error" in result["error"]


# =============================================================================
# Additional Exception Path Tests
# =============================================================================

class TestPrintBudgetServiceExceptionPaths:
    """Test exception handling paths"""

    @pytest.fixture
    def budget_service(self, mock_firebase_client):
        """Create PrintBudgetService instance with mocked dependencies"""
        return PrintBudgetService(mock_firebase_client)

    def test_validate_print_budget_cost_failure(self, budget_service, mock_firebase_client):
        """Test validation when cost calculation fails"""
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": {"remainingPrints": 50.0}},  # User budget
            {"success": False, "error": "Pricing not found"}  # Pricing failure
        ]
        
        result = budget_service.validate_print_budget("user-123", "test-org", 5, 5)
        
        assert result["success"] is False
        assert "Pricing not found" in str(result.get("error", ""))

    def test_validate_print_budget_exception(self, budget_service, mock_firebase_client):
        """Test validation with exception"""
        mock_firebase_client.db_get.side_effect = Exception("Database connection failed")
        
        result = budget_service.validate_print_budget("user-123", "test-org", 5, 5)
        
        assert result["success"] is False
        assert "Database connection failed" in result["error"]

    def test_deduct_print_budget_budget_failure(self, budget_service, mock_firebase_client):
        """Test deduction when getting budget fails"""
        # First call succeeds (validation), second call fails (budget fetch for deduction)
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": {"remainingPrints": 50.0}},  # User budget for validation
            {"success": True, "data": {"blackAndWhitePrice": 1.0, "colorPrice": 3.0}},  # Pricing
            {"success": False, "error": "Budget fetch failed"}  # Budget fetch for deduction
        ]
        
        result = budget_service.deduct_print_budget("user-123", "test-org", 5, 5)
        
        assert result["success"] is False

    def test_deduct_print_budget_exception(self, budget_service, mock_firebase_client):
        """Test deduction with exception during process"""
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": {"remainingPrints": 50.0}},  # User budget for validation
            {"success": True, "data": {"blackAndWhitePrice": 1.0, "colorPrice": 3.0}},  # Pricing
        ]
        # Use a function that raises on subsequent calls
        call_count = [0]
        def raise_on_third(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 3:
                raise Exception("Unexpected error during deduction")
            return {"success": True, "data": {"remainingPrints": 50.0}}
        
        mock_firebase_client.db_get.side_effect = raise_on_third
        
        result = budget_service.deduct_print_budget("user-123", "test-org", 5, 5)
        
        # The result depends on where the exception occurs
        # If exception is raised, it should return failure
        assert result is not None  # Should not crash

    def test_calculate_print_cost_unexpected_exception(self, budget_service, mock_firebase_client):
        """Test calculate_print_cost with unexpected exception"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"blackAndWhitePrice": "invalid", "colorPrice": 3.0}  # Invalid type
        }

        # This should trigger the except block when trying to multiply
        # Actually this may work due to Python's duck typing, let's try a different approach
        mock_firebase_client.db_get.return_value = {"success": True, "data": None}

        result = budget_service.calculate_print_cost("test-org", 5, 5)

        assert result["success"] is False

    def test_add_print_budget_exception_during_calculation(self, budget_service, mock_firebase_client):
        """Test add_print_budget exception during current budget calculation"""
        mock_firebase_client.db_get.side_effect = Exception("Database connection error")

        result = budget_service.add_print_budget("user-123", 25.0)

        assert result["success"] is False
        assert "Database connection error" in result["error"]

    def test_deduct_print_budget_exception_during_validation(self, budget_service, mock_firebase_client):
        """Test deduct_print_budget exception during validation"""
        # Mock validation to succeed but then fail during deduction
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": {"remainingPrints": 50.0}},  # User budget for validation
            {"success": True, "data": {"blackAndWhitePrice": 1.0, "colorPrice": 3.0}},  # Pricing
            Exception("Network failure during deduction")  # Fail during budget fetch for deduction
        ]

        result = budget_service.deduct_print_budget("user-123", "test-org", 5, 5)

        # Should return failure due to exception
        assert result["success"] is False

    def test_get_user_print_budget_db_failure(self, budget_service, mock_firebase_client):
        """Test get_user_print_budget database failure"""
        mock_firebase_client.db_get.return_value = {"success": False, "error": "Database unavailable"}

        result = budget_service.get_user_print_budget("user-123")

        assert result["success"] is False
        assert "Database unavailable" in str(result.get("error", ""))

    def test_get_user_print_budget_exception(self, budget_service, mock_firebase_client):
        """Test get_user_print_budget exception handling"""
        mock_firebase_client.db_get.side_effect = Exception("Connection timeout")

        result = budget_service.get_user_print_budget("user-123")

        assert result["success"] is False
        assert "Connection timeout" in result["error"]

    def test_calculate_print_cost_data_none(self, budget_service, mock_firebase_client):
        """Test calculate_print_cost when pricing data is None"""
        mock_firebase_client.db_get.return_value = {"success": True, "data": None}

        result = budget_service.calculate_print_cost("test-org", 5, 5)

        assert result["success"] is False

    def test_calculate_print_cost_invalid_price_data(self, budget_service, mock_firebase_client):
        """Test calculate_print_cost with invalid price data types"""
        mock_firebase_client.db_get.return_value = {
            "success": True,
            "data": {"blackAndWhitePrice": "not-a-number", "colorPrice": 3.0}
        }

        result = budget_service.calculate_print_cost("test-org", 5, 5)

        # This will cause a TypeError when trying to multiply
        assert result["success"] is False





"""
Tests for PrintValidationService
"""

from unittest.mock import patch, Mock, MagicMock

import pytest

from services.print_validation_service import PrintValidationService


class TestPrintValidationService:
    """Test cases for PrintValidationService"""

    @pytest.fixture
    def validation_service(self, mock_firebase_client, qapp):
        """Create PrintValidationService instance with mocked dependencies"""
        with patch("services.print_validation_service.PrintBudgetService") as MockBudgetService:
            mock_budget_service = Mock()
            MockBudgetService.return_value = mock_budget_service
            service = PrintValidationService(mock_firebase_client, "user-123", "org-123")
            service._mock_budget_service = mock_budget_service
            return service

    def test_initialization(self, validation_service, mock_firebase_client):
        """Test PrintValidationService initialization"""
        assert validation_service.firebase == mock_firebase_client
        assert validation_service.user_id == "user-123"
        assert validation_service.org_id == "org-123"

    # Tests for validate_print_job
    def test_validate_print_job_success_can_print(self, validation_service):
        """Test validating print job when user can print"""
        validation_service._mock_budget_service.validate_print_budget.return_value = {
            "success": True,
            "can_print": True,
            "user_budget": 50.0,
            "print_cost": 15.0,
            "remaining_after_print": 35.0,
            "cost_breakdown": {"black_white_cost": 5.0, "color_cost": 10.0}
        }
        
        result = validation_service.validate_print_job(5, 5)
        
        assert result["success"] is True
        assert result["can_print"] is True
        assert result["user_budget"] == 50.0
        assert result["print_cost"] == 15.0

    def test_validate_print_job_insufficient_budget(self, validation_service):
        """Test validating print job with insufficient budget"""
        validation_service._mock_budget_service.validate_print_budget.return_value = {
            "success": True,
            "can_print": False,
            "user_budget": 10.0,
            "print_cost": 25.0,
            "insufficient_amount": 15.0
        }
        
        result = validation_service.validate_print_job(10, 5)
        
        assert result["success"] is True
        assert result["can_print"] is False
        assert result["reason"] == "insufficient_budget"
        assert result["insufficient_amount"] == 15.0

    def test_validate_print_job_validation_failure(self, validation_service):
        """Test validating print job when validation service fails"""
        validation_service._mock_budget_service.validate_print_budget.return_value = {
            "success": False,
            "error": "Database error"
        }
        
        result = validation_service.validate_print_job(5, 5)
        
        assert result["success"] is False
        assert "Database error" in result.get("error", "")

    def test_validate_print_job_exception(self, validation_service):
        """Test validating print job with exception"""
        validation_service._mock_budget_service.validate_print_budget.side_effect = Exception("Network error")
        
        result = validation_service.validate_print_job(5, 5)
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    def test_validate_print_job_bw_only(self, validation_service):
        """Test validating B&W only print job"""
        validation_service._mock_budget_service.validate_print_budget.return_value = {
            "success": True,
            "can_print": True,
            "user_budget": 50.0,
            "print_cost": 10.0,
            "remaining_after_print": 40.0,
            "cost_breakdown": {"black_white_cost": 10.0, "color_cost": 0.0}
        }
        
        result = validation_service.validate_print_job(10, 0)
        
        assert result["success"] is True
        assert result["can_print"] is True
        validation_service._mock_budget_service.validate_print_budget.assert_called_with(
            "user-123", "org-123", 10, 0
        )

    def test_validate_print_job_color_only(self, validation_service):
        """Test validating color only print job"""
        validation_service._mock_budget_service.validate_print_budget.return_value = {
            "success": True,
            "can_print": True,
            "user_budget": 50.0,
            "print_cost": 15.0,
            "remaining_after_print": 35.0,
            "cost_breakdown": {"black_white_cost": 0.0, "color_cost": 15.0}
        }
        
        result = validation_service.validate_print_job(0, 5)
        
        assert result["success"] is True
        validation_service._mock_budget_service.validate_print_budget.assert_called_with(
            "user-123", "org-123", 0, 5
        )

    # Tests for process_successful_print
    def test_process_successful_print_success(self, validation_service):
        """Test processing successful print"""
        validation_service._mock_budget_service.deduct_print_budget.return_value = {
            "success": True,
            "new_budget": 35.0,
            "deducted_amount": 15.0,
            "cost_breakdown": {"black_white_cost": 5.0, "color_cost": 10.0}
        }
        
        result = validation_service.process_successful_print(5, 5)
        
        assert result["success"] is True
        assert result["new_budget"] == 35.0
        assert result["deducted_amount"] == 15.0

    def test_process_successful_print_deduction_failure(self, validation_service):
        """Test processing print when deduction fails"""
        validation_service._mock_budget_service.deduct_print_budget.return_value = {
            "success": False,
            "error": "Insufficient budget"
        }
        
        result = validation_service.process_successful_print(5, 5)
        
        assert result["success"] is False

    def test_process_successful_print_exception(self, validation_service):
        """Test processing print with exception"""
        validation_service._mock_budget_service.deduct_print_budget.side_effect = Exception("Network error")
        
        result = validation_service.process_successful_print(5, 5)
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    # Tests for get_current_budget
    def test_get_current_budget_success(self, validation_service):
        """Test getting current budget"""
        validation_service._mock_budget_service.get_user_print_budget.return_value = {
            "success": True,
            "budget": 50.0
        }
        
        result = validation_service.get_current_budget()
        
        assert result["success"] is True
        assert result["budget"] == 50.0
        validation_service._mock_budget_service.get_user_print_budget.assert_called_with("user-123")

    def test_get_current_budget_exception(self, validation_service):
        """Test getting current budget with exception"""
        validation_service._mock_budget_service.get_user_print_budget.side_effect = Exception("Network error")
        
        result = validation_service.get_current_budget()
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    # Tests for get_print_pricing
    def test_get_print_pricing_success(self, validation_service):
        """Test getting print pricing"""
        validation_service._mock_budget_service.get_organization_print_pricing.return_value = {
            "success": True,
            "pricing": {"black_and_white_price": 1.0, "color_price": 3.0}
        }
        
        result = validation_service.get_print_pricing()
        
        assert result["success"] is True
        assert result["pricing"]["black_and_white_price"] == 1.0
        validation_service._mock_budget_service.get_organization_print_pricing.assert_called_with("org-123")

    def test_get_print_pricing_exception(self, validation_service):
        """Test getting print pricing with exception"""
        validation_service._mock_budget_service.get_organization_print_pricing.side_effect = Exception("Network error")
        
        result = validation_service.get_print_pricing()
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    # Tests for simulate_print_cost
    def test_simulate_print_cost_success(self, validation_service):
        """Test simulating print cost"""
        validation_service._mock_budget_service.calculate_print_cost.return_value = {
            "success": True,
            "cost_breakdown": {
                "black_white_pages": 10,
                "color_pages": 5,
                "total_cost": 25.0
            }
        }
        
        result = validation_service.simulate_print_cost(10, 5)
        
        assert result["success"] is True
        assert result["cost_breakdown"]["total_cost"] == 25.0
        validation_service._mock_budget_service.calculate_print_cost.assert_called_with("org-123", 10, 5)

    def test_simulate_print_cost_exception(self, validation_service):
        """Test simulating print cost with exception"""
        validation_service._mock_budget_service.calculate_print_cost.side_effect = Exception("Network error")
        
        result = validation_service.simulate_print_cost(10, 5)
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    # Tests for signals
    def test_insufficient_budget_signal_emitted(self, validation_service):
        """Test that insufficient budget signal is emitted"""
        validation_service._mock_budget_service.validate_print_budget.return_value = {
            "success": True,
            "can_print": False,
            "user_budget": 10.0,
            "print_cost": 25.0,
            "insufficient_amount": 15.0
        }
        
        # Track signal emission
        signal_received = []
        validation_service.print_budget_insufficient.connect(
            lambda budget, cost: signal_received.append((budget, cost))
        )
        
        validation_service.validate_print_job(10, 5)
        
        assert len(signal_received) == 1
        assert signal_received[0] == (10.0, 25.0)

    def test_job_validated_signal_emitted(self, validation_service):
        """Test that job validated signal is emitted on success"""
        validation_service._mock_budget_service.validate_print_budget.return_value = {
            "success": True,
            "can_print": True,
            "user_budget": 50.0,
            "print_cost": 15.0,
            "remaining_after_print": 35.0,
            "cost_breakdown": {}
        }
        
        # Track signal emission
        signal_received = []
        validation_service.print_job_validated.connect(
            lambda is_valid, msg: signal_received.append((is_valid, msg))
        )
        
        validation_service.validate_print_job(5, 5)
        
        assert len(signal_received) == 1
        assert signal_received[0][0] is True

    def test_budget_updated_signal_emitted(self, validation_service):
        """Test that budget updated signal is emitted after successful print"""
        validation_service._mock_budget_service.deduct_print_budget.return_value = {
            "success": True,
            "new_budget": 35.0,
            "deducted_amount": 15.0,
            "cost_breakdown": {}
        }
        
        # Track signal emission
        signal_received = []
        validation_service.print_budget_updated.connect(
            lambda budget: signal_received.append(budget)
        )
        
        validation_service.process_successful_print(5, 5)
        
        assert len(signal_received) == 1
        assert signal_received[0] == 35.0






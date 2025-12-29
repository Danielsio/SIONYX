"""
Tests for print_job_simulator.py - Print Job Simulator
Tests print job simulation with budget validation.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtCore import QObject


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def mock_print_validation_service():
    """Create mock print validation service"""
    service = Mock()
    service.validate_print_job.return_value = {
        "success": True,
        "can_print": True,
        "estimated_cost": 5.0,
        "remaining_budget": 95.0
    }
    service.process_successful_print.return_value = {
        "success": True,
        "message": "Print processed"
    }
    return service


@pytest.fixture
def print_simulator(qapp, mock_print_validation_service):
    """Create PrintJobSimulator instance"""
    from services.print_job_simulator import PrintJobSimulator
    
    simulator = PrintJobSimulator(mock_print_validation_service)
    return simulator


# =============================================================================
# Test initialization
# =============================================================================
class TestPrintJobSimulatorInit:
    """Tests for PrintJobSimulator initialization"""

    def test_inherits_from_qobject(self, print_simulator):
        """Test simulator inherits from QObject"""
        assert isinstance(print_simulator, QObject)

    def test_stores_print_validation_service(self, print_simulator, mock_print_validation_service):
        """Test simulator stores print validation service"""
        assert print_simulator.print_validation_service == mock_print_validation_service

    def test_simulated_jobs_is_empty_list(self, print_simulator):
        """Test simulated_jobs is empty list initially"""
        assert print_simulator.simulated_jobs == []

    def test_has_print_job_requested_signal(self, print_simulator):
        """Test simulator has print_job_requested signal"""
        assert hasattr(print_simulator, "print_job_requested")

    def test_has_print_job_completed_signal(self, print_simulator):
        """Test simulator has print_job_completed signal"""
        assert hasattr(print_simulator, "print_job_completed")

    def test_has_print_job_failed_signal(self, print_simulator):
        """Test simulator has print_job_failed signal"""
        assert hasattr(print_simulator, "print_job_failed")


# =============================================================================
# Test simulate_print_job
# =============================================================================
class TestSimulatePrintJob:
    """Tests for simulate_print_job method"""

    def test_emits_print_job_requested_signal(self, print_simulator):
        """Test emits print_job_requested signal"""
        signal_received = []
        print_simulator.print_job_requested.connect(
            lambda bw, c: signal_received.append((bw, c))
        )
        
        print_simulator.simulate_print_job(5, 2)
        
        assert len(signal_received) == 1
        assert signal_received[0] == (5, 2)

    def test_calls_validate_print_job(self, print_simulator, mock_print_validation_service):
        """Test calls validate_print_job with correct params"""
        print_simulator.simulate_print_job(5, 2)
        
        mock_print_validation_service.validate_print_job.assert_called_once_with(5, 2)

    def test_returns_validation_error_on_failure(self, print_simulator, mock_print_validation_service):
        """Test returns validation error when validation fails"""
        mock_print_validation_service.validate_print_job.return_value = {
            "success": False,
            "error": "Service unavailable"
        }
        
        result = print_simulator.simulate_print_job(5, 2)
        
        assert result["success"] is False
        assert "Service unavailable" in result["error"]

    def test_emits_failed_signal_on_validation_error(self, print_simulator, mock_print_validation_service):
        """Test emits print_job_failed signal on validation error"""
        mock_print_validation_service.validate_print_job.return_value = {
            "success": False,
            "error": "Service unavailable"
        }
        
        signal_received = []
        print_simulator.print_job_failed.connect(lambda msg: signal_received.append(msg))
        
        print_simulator.simulate_print_job(5, 2)
        
        assert len(signal_received) == 1
        assert "validation failed" in signal_received[0]

    def test_returns_error_when_cannot_print(self, print_simulator, mock_print_validation_service):
        """Test returns error when can_print is False"""
        mock_print_validation_service.validate_print_job.return_value = {
            "success": True,
            "can_print": False,
            "message": "Insufficient budget"
        }
        
        result = print_simulator.simulate_print_job(5, 2)
        
        assert result["can_print"] is False

    def test_emits_failed_signal_on_insufficient_budget(self, print_simulator, mock_print_validation_service):
        """Test emits print_job_failed signal on insufficient budget"""
        mock_print_validation_service.validate_print_job.return_value = {
            "success": True,
            "can_print": False,
            "message": "Insufficient budget"
        }
        
        signal_received = []
        print_simulator.print_job_failed.connect(lambda msg: signal_received.append(msg))
        
        print_simulator.simulate_print_job(5, 2)
        
        assert len(signal_received) == 1
        assert "Insufficient budget" in signal_received[0]

    def test_returns_success_when_validation_passes(self, print_simulator):
        """Test returns success when validation passes"""
        result = print_simulator.simulate_print_job(5, 2)
        
        assert result["success"] is True
        assert "queued" in result["message"]

    def test_handles_exception(self, print_simulator, mock_print_validation_service):
        """Test handles exception gracefully"""
        mock_print_validation_service.validate_print_job.side_effect = Exception("Network error")
        
        result = print_simulator.simulate_print_job(5, 2)
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    def test_emits_failed_signal_on_exception(self, print_simulator, mock_print_validation_service):
        """Test emits print_job_failed signal on exception"""
        mock_print_validation_service.validate_print_job.side_effect = Exception("Network error")
        
        signal_received = []
        print_simulator.print_job_failed.connect(lambda msg: signal_received.append(msg))
        
        print_simulator.simulate_print_job(5, 2)
        
        assert len(signal_received) == 1


# =============================================================================
# Test _complete_print_job
# =============================================================================
class TestCompletePrintJob:
    """Tests for _complete_print_job method"""

    def test_calls_process_successful_print(self, print_simulator, mock_print_validation_service):
        """Test calls process_successful_print with correct params"""
        print_simulator._complete_print_job(5, 2)
        
        mock_print_validation_service.process_successful_print.assert_called_once_with(5, 2)

    def test_emits_completed_signal_on_success(self, print_simulator):
        """Test emits print_job_completed signal on success"""
        signal_received = []
        print_simulator.print_job_completed.connect(
            lambda bw, c: signal_received.append((bw, c))
        )
        
        print_simulator._complete_print_job(5, 2)
        
        assert len(signal_received) == 1
        assert signal_received[0] == (5, 2)

    def test_emits_failed_signal_on_process_failure(self, print_simulator, mock_print_validation_service):
        """Test emits print_job_failed signal when processing fails"""
        mock_print_validation_service.process_successful_print.return_value = {
            "success": False,
            "error": "Database error"
        }
        
        signal_received = []
        print_simulator.print_job_failed.connect(lambda msg: signal_received.append(msg))
        
        print_simulator._complete_print_job(5, 2)
        
        assert len(signal_received) == 1
        assert "Failed to process" in signal_received[0]

    def test_handles_exception(self, print_simulator, mock_print_validation_service):
        """Test handles exception gracefully"""
        mock_print_validation_service.process_successful_print.side_effect = Exception("Error")
        
        signal_received = []
        print_simulator.print_job_failed.connect(lambda msg: signal_received.append(msg))
        
        # Should not raise
        print_simulator._complete_print_job(5, 2)
        
        assert len(signal_received) == 1


# =============================================================================
# Test simulate_multiple_jobs
# =============================================================================
class TestSimulateMultipleJobs:
    """Tests for simulate_multiple_jobs method"""

    def test_validates_total_pages(self, print_simulator, mock_print_validation_service):
        """Test validates total pages from all jobs"""
        jobs = [(5, 2), (3, 1), (2, 0)]
        
        print_simulator.simulate_multiple_jobs(jobs)
        
        # Should validate with total: 10 B&W, 3 color
        mock_print_validation_service.validate_print_job.assert_called_once_with(10, 3)

    def test_returns_validation_result_on_failure(self, print_simulator, mock_print_validation_service):
        """Test returns validation result when validation fails"""
        mock_print_validation_service.validate_print_job.return_value = {
            "success": False,
            "can_print": False,
            "error": "Budget exceeded"
        }
        
        jobs = [(5, 2)]
        result = print_simulator.simulate_multiple_jobs(jobs)
        
        assert result["success"] is False

    def test_returns_success_with_job_count(self, print_simulator):
        """Test returns success with queued job count"""
        jobs = [(5, 2), (3, 1)]
        
        result = print_simulator.simulate_multiple_jobs(jobs)
        
        assert result["success"] is True
        assert "2" in result["message"]

    def test_returns_total_page_counts(self, print_simulator):
        """Test returns total page counts"""
        jobs = [(5, 2), (3, 1)]
        
        result = print_simulator.simulate_multiple_jobs(jobs)
        
        assert result["total_black_white"] == 8
        assert result["total_color"] == 3

    def test_handles_empty_jobs_list(self, print_simulator, mock_print_validation_service):
        """Test handles empty jobs list"""
        jobs = []
        
        result = print_simulator.simulate_multiple_jobs(jobs)
        
        # Should validate with 0 pages
        mock_print_validation_service.validate_print_job.assert_called_once_with(0, 0)

    def test_handles_exception(self, print_simulator, mock_print_validation_service):
        """Test handles exception gracefully"""
        mock_print_validation_service.validate_print_job.side_effect = Exception("Error")
        
        jobs = [(5, 2)]
        result = print_simulator.simulate_multiple_jobs(jobs)
        
        assert result["success"] is False
        assert "Error" in result["error"]


# =============================================================================
# Test signal types
# =============================================================================
class TestSignalTypes:
    """Tests for signal types and parameters"""

    def test_print_job_requested_has_two_int_params(self, print_simulator):
        """Test print_job_requested signal accepts two ints"""
        received = []
        print_simulator.print_job_requested.connect(
            lambda bw, c: received.append((bw, c))
        )
        print_simulator.print_job_requested.emit(5, 2)
        
        assert received[0] == (5, 2)

    def test_print_job_completed_has_two_int_params(self, print_simulator):
        """Test print_job_completed signal accepts two ints"""
        received = []
        print_simulator.print_job_completed.connect(
            lambda bw, c: received.append((bw, c))
        )
        print_simulator.print_job_completed.emit(5, 2)
        
        assert received[0] == (5, 2)

    def test_print_job_failed_has_string_param(self, print_simulator):
        """Test print_job_failed signal accepts string"""
        received = []
        print_simulator.print_job_failed.connect(lambda msg: received.append(msg))
        print_simulator.print_job_failed.emit("Test error")
        
        assert received[0] == "Test error"







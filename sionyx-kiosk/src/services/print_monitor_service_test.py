"""
Tests for PrintMonitorService (Pause-First Architecture)

Tests cover:
- Initialization and state
- Printer-level pause/resume
- Start/stop monitoring lifecycle
- Job detection via polling
- Cost calculation (pages × copies × price)
- Budget management
- Safe job release mechanism
- Crash recovery
- Edge cases and error handling
- atexit safety handler
"""

import threading
from unittest.mock import Mock, call, patch

import pytest
from PyQt6.QtCore import QTimer

from services.print_monitor_service import (
    JOB_CONTROL_CANCEL,
    JOB_CONTROL_PAUSE,
    JOB_CONTROL_RESUME,
    PRINTER_CONTROL_PAUSE,
    PRINTER_CONTROL_RESUME,
    PRINTER_STATUS_PAUSED,
    PrintMonitorService,
    _atexit_resume_printers,
    _global_lock,
    _globally_paused_printers,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_firebase():
    """Create mock Firebase client"""
    firebase = Mock()
    firebase.db_get = Mock(return_value={"success": True, "data": {}})
    firebase.db_update = Mock(return_value={"success": True})
    return firebase


@pytest.fixture
def mock_win32print():
    """Create a mock win32print module with common attributes"""
    m = Mock()
    m.PRINTER_ENUM_LOCAL = 1
    m.PRINTER_ENUM_CONNECTIONS = 2
    m.OpenPrinter = Mock(return_value=Mock())
    m.ClosePrinter = Mock()
    m.SetPrinter = Mock()
    m.SetJob = Mock()
    m.GetPrinter = Mock(return_value={"Status": 0})
    m.EnumPrinters = Mock(return_value=[])
    m.EnumJobs = Mock(return_value=[])
    m.GetJob = Mock(return_value={})
    return m


@pytest.fixture
def print_monitor(qapp, mock_firebase):
    """Create PrintMonitorService instance"""
    service = PrintMonitorService(
        firebase_client=mock_firebase,
        user_id="test-user-123",
        org_id="test-org-456",
    )
    yield service
    # Cleanup
    if service.is_monitoring():
        service.stop_monitoring()


# =============================================================================
# Initialization Tests
# =============================================================================


class TestInitialization:
    """Tests for service initialization"""

    def test_creates_with_correct_attributes(self, print_monitor, mock_firebase):
        """Test service initializes with correct attributes"""
        assert print_monitor.firebase == mock_firebase
        assert print_monitor.user_id == "test-user-123"
        assert print_monitor.org_id == "test-org-456"

    def test_initial_state_is_not_monitoring(self, print_monitor):
        """Test service starts in non-monitoring state"""
        assert print_monitor.is_monitoring() is False

    def test_initial_known_jobs_empty(self, print_monitor):
        """Test known jobs dict is empty initially"""
        assert print_monitor._known_jobs == {}

    def test_initial_processed_jobs_empty(self, print_monitor):
        """Test processed jobs set is empty initially"""
        assert print_monitor._processed_jobs == set()

    def test_default_pricing(self, print_monitor):
        """Test default pricing values"""
        assert print_monitor._bw_price == 1.0
        assert print_monitor._color_price == 3.0

    def test_initial_paused_printers_empty(self, print_monitor):
        """Test paused printers set is empty initially"""
        assert print_monitor._paused_printers == set()

    def test_initial_releasing_jobs_empty(self, print_monitor):
        """Test releasing jobs set is empty initially"""
        assert print_monitor._releasing_jobs == set()


# =============================================================================
# Printer-Level Pause/Resume Tests
# =============================================================================


class TestPrinterPauseResume:
    """Tests for printer-level pause and resume"""

    def test_pause_printer_success(self, print_monitor, mock_win32print):
        """Test pausing a printer"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            result = print_monitor._pause_printer("HP LaserJet")

        assert result is True
        mock_win32print.SetPrinter.assert_called_once_with(
            handle, 0, None, PRINTER_CONTROL_PAUSE
        )
        assert "HP LaserJet" in print_monitor._paused_printers

    def test_resume_printer_success(self, print_monitor, mock_win32print):
        """Test resuming a printer"""
        print_monitor._paused_printers.add("HP LaserJet")
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            result = print_monitor._resume_printer("HP LaserJet")

        assert result is True
        mock_win32print.SetPrinter.assert_called_once_with(
            handle, 0, None, PRINTER_CONTROL_RESUME
        )
        assert "HP LaserJet" not in print_monitor._paused_printers

    def test_pause_printer_no_win32print(self, print_monitor):
        """Test pause returns False when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            result = print_monitor._pause_printer("Printer1")
        assert result is False

    def test_resume_printer_no_win32print(self, print_monitor):
        """Test resume returns False when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            result = print_monitor._resume_printer("Printer1")
        assert result is False

    def test_pause_printer_exception(self, print_monitor, mock_win32print):
        """Test pause handles exceptions"""
        mock_win32print.OpenPrinter.side_effect = Exception("Access denied")

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            result = print_monitor._pause_printer("Printer1")

        assert result is False
        assert "Printer1" not in print_monitor._paused_printers

    def test_resume_printer_exception(self, print_monitor, mock_win32print):
        """Test resume handles exceptions"""
        print_monitor._paused_printers.add("Printer1")
        mock_win32print.OpenPrinter.side_effect = Exception("Access denied")

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            result = print_monitor._resume_printer("Printer1")

        assert result is False

    def test_pause_all_printers(self, print_monitor, mock_win32print):
        """Test pausing all printers"""
        mock_win32print.EnumPrinters.return_value = [
            (0, "", "Printer1", ""),
            (0, "", "Printer2", ""),
        ]
        mock_win32print.GetPrinter.return_value = {"Status": 0}  # Not paused
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            print_monitor._pause_all_printers()

        assert "Printer1" in print_monitor._paused_printers
        assert "Printer2" in print_monitor._paused_printers

    def test_resume_all_printers(self, print_monitor, mock_win32print):
        """Test resuming all printers we paused"""
        print_monitor._paused_printers = {"Printer1", "Printer2"}
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            print_monitor._resume_all_printers()

        assert len(print_monitor._paused_printers) == 0

    def test_resume_all_printers_empty(self, print_monitor):
        """Test resume all does nothing when no printers paused"""
        with patch.object(print_monitor, "_resume_printer") as mock_resume:
            print_monitor._resume_all_printers()
        mock_resume.assert_not_called()

    def test_is_printer_paused_true(self, print_monitor, mock_win32print):
        """Test detecting a paused printer"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.GetPrinter.return_value = {
            "Status": PRINTER_STATUS_PAUSED
        }

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            result = print_monitor._is_printer_paused("Printer1")

        assert result is True

    def test_is_printer_paused_false(self, print_monitor, mock_win32print):
        """Test detecting an active printer"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.GetPrinter.return_value = {"Status": 0}

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            result = print_monitor._is_printer_paused("Printer1")

        assert result is False

    def test_is_printer_paused_no_win32print(self, print_monitor):
        """Test is_printer_paused returns False when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            result = print_monitor._is_printer_paused("Printer1")
        assert result is False

    def test_pause_all_skips_already_paused(self, print_monitor, mock_win32print):
        """Test _pause_all_printers skips printers already paused"""
        mock_win32print.EnumPrinters.return_value = [
            (0, "", "AlreadyPaused", ""),
        ]
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.GetPrinter.return_value = {
            "Status": PRINTER_STATUS_PAUSED
        }

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            print_monitor._pause_all_printers()

        # SetPrinter should NOT be called with PAUSE since printer is already paused
        for c in mock_win32print.SetPrinter.call_args_list:
            assert c != call(handle, 0, None, PRINTER_CONTROL_PAUSE)

    def test_pause_printer_updates_global_tracker(self, print_monitor, mock_win32print):
        """Test that pausing updates the global atexit tracker"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            print_monitor._pause_printer("TestPrinter")

        with _global_lock:
            assert "TestPrinter" in _globally_paused_printers

        # Cleanup
        with _global_lock:
            _globally_paused_printers.discard("TestPrinter")

    def test_resume_printer_updates_global_tracker(
        self, print_monitor, mock_win32print
    ):
        """Test that resuming updates the global atexit tracker"""
        print_monitor._paused_printers.add("TestPrinter")
        with _global_lock:
            _globally_paused_printers.add("TestPrinter")

        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            print_monitor._resume_printer("TestPrinter")

        with _global_lock:
            assert "TestPrinter" not in _globally_paused_printers


# =============================================================================
# Start/Stop Monitoring Tests
# =============================================================================


class TestStartStopMonitoring:
    """Tests for start and stop monitoring lifecycle"""

    def test_start_monitoring_success(self, print_monitor):
        """Test starting monitoring returns success"""
        with patch.object(print_monitor, "_recover_from_crash"):
            with patch.object(print_monitor, "_load_pricing"):
                with patch.object(print_monitor, "_pause_all_printers"):
                    with patch.object(print_monitor, "_initialize_known_jobs"):
                        result = print_monitor.start_monitoring()

        assert result["success"] is True
        assert print_monitor.is_monitoring() is True

    def test_start_monitoring_already_running(self, print_monitor):
        """Test starting when already monitoring returns message"""
        print_monitor._is_monitoring = True

        result = print_monitor.start_monitoring()

        assert result["success"] is True
        assert result["message"] == "Already monitoring"

    def test_start_monitoring_creates_timer(self, print_monitor):
        """Test starting creates poll timer with 1s interval"""
        with patch.object(print_monitor, "_recover_from_crash"):
            with patch.object(print_monitor, "_load_pricing"):
                with patch.object(print_monitor, "_pause_all_printers"):
                    with patch.object(print_monitor, "_initialize_known_jobs"):
                        print_monitor.start_monitoring()

        assert print_monitor._poll_timer is not None
        assert isinstance(print_monitor._poll_timer, QTimer)

    def test_start_monitoring_calls_pause_all_printers(self, print_monitor):
        """Test that start_monitoring pauses all printers"""
        with patch.object(print_monitor, "_recover_from_crash"):
            with patch.object(print_monitor, "_load_pricing"):
                with patch.object(
                    print_monitor, "_pause_all_printers"
                ) as mock_pause:
                    with patch.object(print_monitor, "_initialize_known_jobs"):
                        print_monitor.start_monitoring()

        mock_pause.assert_called_once()

    def test_start_monitoring_calls_crash_recovery(self, print_monitor):
        """Test that start_monitoring performs crash recovery"""
        with patch.object(
            print_monitor, "_recover_from_crash"
        ) as mock_recover:
            with patch.object(print_monitor, "_load_pricing"):
                with patch.object(print_monitor, "_pause_all_printers"):
                    with patch.object(print_monitor, "_initialize_known_jobs"):
                        print_monitor.start_monitoring()

        mock_recover.assert_called_once()

    def test_start_monitoring_exception_resumes_printers(self, print_monitor):
        """Test that start_monitoring resumes printers on failure"""
        with patch.object(print_monitor, "_recover_from_crash"):
            with patch.object(
                print_monitor, "_load_pricing", side_effect=Exception("Error")
            ):
                with patch.object(
                    print_monitor, "_resume_all_printers"
                ) as mock_resume:
                    result = print_monitor.start_monitoring()

        assert result["success"] is False
        mock_resume.assert_called_once()

    def test_stop_monitoring_success(self, print_monitor):
        """Test stopping monitoring returns success"""
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()

        with patch.object(print_monitor, "_resume_all_printers"):
            result = print_monitor.stop_monitoring()

        assert result["success"] is True
        assert print_monitor.is_monitoring() is False

    def test_stop_monitoring_not_running(self, print_monitor):
        """Test stopping when not monitoring returns message"""
        result = print_monitor.stop_monitoring()

        assert result["success"] is True
        assert result["message"] == "Not monitoring"

    def test_stop_monitoring_resumes_printers(self, print_monitor):
        """Test that stop_monitoring resumes all printers"""
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()

        with patch.object(
            print_monitor, "_resume_all_printers"
        ) as mock_resume:
            print_monitor.stop_monitoring()

        mock_resume.assert_called_once()

    def test_stop_monitoring_clears_state(self, print_monitor):
        """Test stopping clears all tracking state"""
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()
        print_monitor._known_jobs = {"Printer1": {1, 2}}
        print_monitor._processed_jobs = {"Printer1:1"}
        print_monitor._releasing_jobs = {"Printer1:2"}

        with patch.object(print_monitor, "_resume_all_printers"):
            print_monitor.stop_monitoring()

        assert print_monitor._known_jobs == {}
        assert print_monitor._processed_jobs == set()
        assert print_monitor._releasing_jobs == set()

    def test_stop_monitoring_stops_timer(self, print_monitor):
        """Test stopping stops the poll timer"""
        print_monitor._is_monitoring = True
        mock_timer = Mock()
        print_monitor._poll_timer = mock_timer

        with patch.object(print_monitor, "_resume_all_printers"):
            print_monitor.stop_monitoring()

        mock_timer.stop.assert_called_once()
        assert print_monitor._poll_timer is None


# =============================================================================
# Pricing Tests
# =============================================================================


class TestPricing:
    """Tests for pricing functionality"""

    def test_load_pricing_success(self, print_monitor, mock_firebase):
        """Test loading pricing from Firebase"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {
                "blackAndWhitePrice": 0.5,
                "colorPrice": 2.0,
            },
        }

        print_monitor._load_pricing()

        assert print_monitor._bw_price == 0.5
        assert print_monitor._color_price == 2.0

    def test_load_pricing_uses_defaults_on_failure(
        self, print_monitor, mock_firebase
    ):
        """Test pricing uses defaults when Firebase fails"""
        mock_firebase.db_get.return_value = {"success": False}

        print_monitor._load_pricing()

        assert print_monitor._bw_price == 1.0
        assert print_monitor._color_price == 3.0

    def test_load_pricing_handles_exception(self, print_monitor, mock_firebase):
        """Test pricing handles exceptions gracefully"""
        mock_firebase.db_get.side_effect = Exception("Network error")

        print_monitor._load_pricing()

        assert print_monitor._bw_price == 1.0
        assert print_monitor._color_price == 3.0

    def test_calculate_cost_bw_single_copy(self, print_monitor):
        """Test cost: pages × 1 copy × BW price"""
        print_monitor._bw_price = 0.5

        cost = print_monitor._calculate_cost(10, 1, is_color=False)

        assert cost == 5.0  # 10 × 1 × 0.5

    def test_calculate_cost_bw_multiple_copies(self, print_monitor):
        """Test cost: pages × copies × BW price"""
        print_monitor._bw_price = 1.0

        cost = print_monitor._calculate_cost(5, 3, is_color=False)

        assert cost == 15.0  # 5 × 3 × 1.0

    def test_calculate_cost_color_single_copy(self, print_monitor):
        """Test cost: pages × 1 copy × color price"""
        print_monitor._color_price = 2.0

        cost = print_monitor._calculate_cost(10, 1, is_color=True)

        assert cost == 20.0  # 10 × 1 × 2.0

    def test_calculate_cost_color_multiple_copies(self, print_monitor):
        """Test cost: pages × copies × color price"""
        print_monitor._color_price = 3.0

        cost = print_monitor._calculate_cost(5, 2, is_color=True)

        assert cost == 30.0  # 5 × 2 × 3.0

    def test_calculate_cost_single_page_single_copy(self, print_monitor):
        """Test minimum cost: 1 page × 1 copy"""
        print_monitor._bw_price = 1.0

        cost = print_monitor._calculate_cost(1, 1, is_color=False)

        assert cost == 1.0

    def test_is_color_job_from_devmode_color(self, print_monitor):
        """Test color detection returns True for color jobs"""
        mock_devmode = Mock()
        mock_devmode.Color = 2  # DMCOLOR_COLOR

        assert print_monitor._is_color_job_from_devmode(mock_devmode) is True

    def test_is_color_job_from_devmode_bw(self, print_monitor):
        """Test color detection returns False for B&W jobs"""
        mock_devmode = Mock()
        mock_devmode.Color = 1  # DMCOLOR_MONOCHROME

        assert print_monitor._is_color_job_from_devmode(mock_devmode) is False

    def test_is_color_job_from_devmode_none(self, print_monitor):
        """Test color detection returns False when devmode is None"""
        assert print_monitor._is_color_job_from_devmode(None) is False

    def test_is_color_job_from_devmode_missing_attribute(self, print_monitor):
        """Test color detection returns False when Color attribute missing"""
        mock_devmode = Mock(spec=[])

        assert print_monitor._is_color_job_from_devmode(mock_devmode) is False

    def test_is_color_job_from_devmode_exception(self, print_monitor):
        """Test color detection returns False on exception"""
        mock_devmode = Mock()
        type(mock_devmode).Color = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("Error"))
        )

        assert print_monitor._is_color_job_from_devmode(mock_devmode) is False


# =============================================================================
# Copies from DEVMODE Tests
# =============================================================================


class TestCopiesFromDevmode:
    """Tests for _get_copies_from_devmode method"""

    def test_copies_with_value(self, print_monitor):
        """Test extracting copies when value is present"""
        mock_devmode = Mock()
        mock_devmode.Copies = 3
        assert print_monitor._get_copies_from_devmode(mock_devmode) == 3

    def test_copies_none_devmode(self, print_monitor):
        """Test returns 1 when devmode is None"""
        assert print_monitor._get_copies_from_devmode(None) == 1

    def test_copies_zero(self, print_monitor):
        """Test returns 1 when copies is 0"""
        mock_devmode = Mock()
        mock_devmode.Copies = 0
        assert print_monitor._get_copies_from_devmode(mock_devmode) == 1

    def test_copies_negative(self, print_monitor):
        """Test returns 1 when copies is negative"""
        mock_devmode = Mock()
        mock_devmode.Copies = -5
        assert print_monitor._get_copies_from_devmode(mock_devmode) == 1

    def test_copies_missing_attribute(self, print_monitor):
        """Test returns 1 when Copies attribute is missing"""
        mock_devmode = Mock(spec=[])
        assert print_monitor._get_copies_from_devmode(mock_devmode) == 1

    def test_copies_exception(self, print_monitor):
        """Test returns 1 when exception occurs"""
        mock_devmode = Mock()
        type(mock_devmode).Copies = property(
            lambda self: (_ for _ in ()).throw(Exception("Error"))
        )
        assert print_monitor._get_copies_from_devmode(mock_devmode) == 1


# =============================================================================
# Budget Tests
# =============================================================================


class TestBudget:
    """Tests for budget functionality"""

    def test_get_user_budget_success(self, print_monitor, mock_firebase):
        """Test getting user budget from Firebase"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }

        budget = print_monitor._get_user_budget()

        assert budget == 50.0
        mock_firebase.db_get.assert_called_with("users/test-user-123")

    def test_get_user_budget_returns_zero_on_failure(
        self, print_monitor, mock_firebase
    ):
        """Test getting budget returns 0 on failure"""
        mock_firebase.db_get.return_value = {"success": False}

        assert print_monitor._get_user_budget() == 0.0

    def test_get_user_budget_handles_exception(
        self, print_monitor, mock_firebase
    ):
        """Test getting budget handles exceptions"""
        mock_firebase.db_get.side_effect = Exception("Network error")

        assert print_monitor._get_user_budget() == 0.0

    def test_get_user_budget_uses_cache(self, print_monitor, mock_firebase):
        """Test budget is cached for subsequent calls"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }

        # First call - hits Firebase
        budget1 = print_monitor._get_user_budget()
        # Second call - should use cache
        budget2 = print_monitor._get_user_budget()

        assert budget1 == 50.0
        assert budget2 == 50.0
        # Firebase should only be called once (cached on second)
        assert mock_firebase.db_get.call_count == 1

    def test_get_user_budget_force_refresh(self, print_monitor, mock_firebase):
        """Test force_refresh bypasses cache"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }

        print_monitor._get_user_budget()  # Populate cache
        print_monitor._get_user_budget(force_refresh=True)  # Force refresh

        assert mock_firebase.db_get.call_count == 2

    def test_deduct_budget_success(self, print_monitor, mock_firebase):
        """Test deducting budget successfully"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        signal_received = []
        print_monitor.budget_updated.connect(lambda x: signal_received.append(x))

        result = print_monitor._deduct_budget(10.0)

        assert result is True
        assert signal_received == [40.0]

    def test_deduct_budget_failure(self, print_monitor, mock_firebase):
        """Test deducting budget when update fails"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {
            "success": False,
            "error": "Failed",
        }

        assert print_monitor._deduct_budget(10.0) is False

    def test_deduct_budget_cannot_go_negative(
        self, print_monitor, mock_firebase
    ):
        """Test budget cannot go below zero"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 5.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        print_monitor._deduct_budget(10.0)

        call_args = mock_firebase.db_update.call_args
        assert call_args[0][1]["printBalance"] == 0.0

    def test_deduct_budget_exception(self, print_monitor, mock_firebase):
        """Test deduct returns False on exception"""
        mock_firebase.db_update.side_effect = Exception("Database error")

        assert print_monitor._deduct_budget(10.0) is False


# =============================================================================
# Spooler Interaction Tests
# =============================================================================


class TestSpoolerInteraction:
    """Tests for Windows Print Spooler interaction"""

    def test_get_all_printers_no_win32print(self, print_monitor):
        """Test get_all_printers returns empty when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            assert print_monitor._get_all_printers() == []

    def test_get_all_printers_success(self, print_monitor, mock_win32print):
        """Test get_all_printers returns printer names"""
        mock_win32print.EnumPrinters.return_value = [
            (0, "", "HP LaserJet", ""),
            (0, "", "Canon Inkjet", ""),
        ]

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            printers = print_monitor._get_all_printers()

        assert printers == ["HP LaserJet", "Canon Inkjet"]

    def test_get_all_printers_exception(self, print_monitor, mock_win32print):
        """Test get_all_printers handles exceptions"""
        mock_win32print.EnumPrinters.side_effect = Exception("Access denied")

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._get_all_printers() == []

    def test_get_printer_jobs_no_win32print(self, print_monitor):
        """Test returns empty when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            assert print_monitor._get_printer_jobs("Printer1") == []

    def test_get_printer_jobs_success(self, print_monitor, mock_win32print):
        """Test get_printer_jobs returns job list"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 1, "pDocument": "Doc1"},
            {"JobId": 2, "pDocument": "Doc2"},
        ]

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            jobs = print_monitor._get_printer_jobs("Printer1")

        assert len(jobs) == 2
        mock_win32print.ClosePrinter.assert_called_once_with(handle)

    def test_get_printer_jobs_empty(self, print_monitor, mock_win32print):
        """Test get_printer_jobs with empty queue"""
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.EnumJobs.return_value = None

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._get_printer_jobs("Printer1") == []

    def test_get_job_info_success(self, print_monitor, mock_win32print):
        """Test getting job info"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.GetJob.return_value = {"TotalPages": 10, "Status": 0}

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            result = print_monitor._get_job_info("Printer1", 42)

        assert result["TotalPages"] == 10
        mock_win32print.GetJob.assert_called_once_with(handle, 42, 2)

    def test_get_job_info_no_win32print(self, print_monitor):
        """Test returns empty dict when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            assert print_monitor._get_job_info("Printer1", 42) == {}

    def test_pause_job_success(self, print_monitor, mock_win32print):
        """Test pause_job calls SetJob with PAUSE"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            result = print_monitor._pause_job("Printer1", 42)

        assert result is True
        mock_win32print.SetJob.assert_called_once_with(
            handle, 42, 0, None, JOB_CONTROL_PAUSE
        )

    def test_resume_job_success(self, print_monitor, mock_win32print):
        """Test resume_job calls SetJob with RESUME"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            result = print_monitor._resume_job("Printer1", 42)

        assert result is True
        mock_win32print.SetJob.assert_called_once_with(
            handle, 42, 0, None, JOB_CONTROL_RESUME
        )

    def test_cancel_job_success(self, print_monitor, mock_win32print):
        """Test cancel_job calls SetJob with CANCEL"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            result = print_monitor._cancel_job("Printer1", 42)

        assert result is True
        mock_win32print.SetJob.assert_called_once_with(
            handle, 42, 0, None, JOB_CONTROL_CANCEL
        )

    def test_pause_job_no_win32print(self, print_monitor):
        """Test pause returns False when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            assert print_monitor._pause_job("P", 1) is False

    def test_resume_job_no_win32print(self, print_monitor):
        """Test resume returns False when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            assert print_monitor._resume_job("P", 1) is False

    def test_cancel_job_no_win32print(self, print_monitor):
        """Test cancel returns False when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            assert print_monitor._cancel_job("P", 1) is False


# =============================================================================
# Error 87 Handling Tests
# =============================================================================


class TestError87:
    """Tests for error 87 (job already completed) handling"""

    def _make_error_87(self):
        """Create an error with winerror=87"""
        err = Exception("The parameter is incorrect")
        err.winerror = 87
        return err

    def _make_other_error(self):
        """Create a non-87 error"""
        err = Exception("Access denied")
        err.winerror = 5
        return err

    def test_pause_job_error_87(self, print_monitor, mock_win32print):
        """Test pause returns False for error 87"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.SetJob.side_effect = self._make_error_87()

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._pause_job("Printer1", 42) is False

    def test_resume_job_error_87(self, print_monitor, mock_win32print):
        """Test resume returns True for error 87 (job completed fast)"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.SetJob.side_effect = self._make_error_87()

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._resume_job("Printer1", 42) is True

    def test_cancel_job_error_87(self, print_monitor, mock_win32print):
        """Test cancel returns True for error 87 (job already gone)"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.SetJob.side_effect = self._make_error_87()

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._cancel_job("Printer1", 42) is True

    def test_pause_job_other_error(self, print_monitor, mock_win32print):
        """Test pause returns False for non-87 errors"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.SetJob.side_effect = self._make_other_error()

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._pause_job("Printer1", 42) is False

    def test_resume_job_other_error(self, print_monitor, mock_win32print):
        """Test resume returns False for non-87 errors"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.SetJob.side_effect = self._make_other_error()

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._resume_job("Printer1", 42) is False

    def test_cancel_job_other_error(self, print_monitor, mock_win32print):
        """Test cancel returns False for non-87 errors"""
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.SetJob.side_effect = self._make_other_error()

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._cancel_job("Printer1", 42) is False


# =============================================================================
# Polling Tests
# =============================================================================


class TestPolling:
    """Tests for queue polling"""

    def test_initialize_known_jobs(self, print_monitor, mock_win32print):
        """Test initializing known jobs snapshot"""
        mock_win32print.EnumPrinters.return_value = [
            (0, "", "Printer1", ""),
        ]
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 1},
            {"JobId": 2},
        ]

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            print_monitor._initialize_known_jobs()

        assert print_monitor._known_jobs["Printer1"] == {1, 2}

    def test_initialize_known_jobs_no_printers(self, print_monitor):
        """Test initializing with no printers"""
        with patch.object(print_monitor, "_get_all_printers", return_value=[]):
            print_monitor._initialize_known_jobs()

        assert print_monitor._known_jobs == {}

    def test_poll_not_monitoring(self, print_monitor):
        """Test polling does nothing when not monitoring"""
        print_monitor._is_monitoring = False

        with patch.object(print_monitor, "_get_all_printers") as mock_get:
            print_monitor._poll_print_queues()

        mock_get.assert_not_called()

    def test_poll_detects_new_job(self, print_monitor, mock_win32print):
        """Test polling detects a new print job"""
        print_monitor._is_monitoring = True
        print_monitor._known_jobs = {"Printer1": {1, 2}}

        mock_win32print.EnumPrinters.return_value = [
            (0, "", "Printer1", ""),
        ]
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 1},
            {"JobId": 2},
            {"JobId": 3, "pDocument": "New Doc", "TotalPages": 5},
        ]

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            with patch.object(
                print_monitor, "_handle_new_job"
            ) as mock_handle:
                print_monitor._poll_print_queues()

        mock_handle.assert_called_once()
        call_args = mock_handle.call_args
        assert call_args[0][0] == "Printer1"
        assert call_args[0][1]["JobId"] == 3

    def test_poll_skips_already_processed(self, print_monitor, mock_win32print):
        """Test polling skips already processed jobs"""
        print_monitor._is_monitoring = True
        print_monitor._known_jobs = {"Printer1": set()}
        print_monitor._processed_jobs = {"Printer1:3"}

        mock_win32print.EnumPrinters.return_value = [
            (0, "", "Printer1", ""),
        ]
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 3, "pDocument": "Doc"},
        ]

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            with patch.object(
                print_monitor, "_handle_new_job"
            ) as mock_handle:
                print_monitor._poll_print_queues()

        mock_handle.assert_not_called()

    def test_poll_skips_releasing_jobs(self, print_monitor, mock_win32print):
        """Test polling skips jobs being released"""
        print_monitor._is_monitoring = True
        print_monitor._known_jobs = {"Printer1": set()}
        print_monitor._releasing_jobs = {"Printer1:3"}

        mock_win32print.EnumPrinters.return_value = [
            (0, "", "Printer1", ""),
        ]
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 3, "pDocument": "Doc"},
        ]

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            with patch.object(
                print_monitor, "_handle_new_job"
            ) as mock_handle:
                print_monitor._poll_print_queues()

        mock_handle.assert_not_called()

    def test_poll_cleans_processed_jobs(self, print_monitor, mock_win32print):
        """Test polling cleans up processed jobs no longer in queue"""
        print_monitor._is_monitoring = True
        print_monitor._known_jobs = {"Printer1": {1, 2}}
        print_monitor._processed_jobs = {"Printer1:1", "Printer1:2"}

        mock_win32print.EnumPrinters.return_value = [
            (0, "", "Printer1", ""),
        ]
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 2},  # Only job 2 remains
        ]

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            print_monitor._poll_print_queues()

        assert "Printer1:1" not in print_monitor._processed_jobs
        assert "Printer1:2" in print_monitor._processed_jobs

    def test_poll_handles_exception(self, print_monitor):
        """Test polling handles exceptions gracefully"""
        print_monitor._is_monitoring = True

        with patch.object(
            print_monitor,
            "_get_all_printers",
            side_effect=Exception("Error"),
        ):
            # Should not raise
            print_monitor._poll_print_queues()


# =============================================================================
# Job Handling Tests
# =============================================================================


class TestJobHandling:
    """Tests for job handling (approve/deny) logic"""

    def test_handle_job_approved(self, print_monitor, mock_firebase):
        """Test job is approved when budget is sufficient"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        mock_devmode = Mock()
        mock_devmode.Copies = 1
        mock_devmode.Color = 1  # B&W

        job_data = {
            "JobId": 1,
            "pDocument": "Test Doc",
            "TotalPages": 5,
            "Status": 0,
            "pDevMode": mock_devmode,
        }

        allowed_signals = []
        print_monitor.job_allowed.connect(
            lambda *args: allowed_signals.append(args)
        )

        with patch.object(print_monitor, "_release_job"):
            print_monitor._handle_new_job("Printer1", job_data)

        assert len(allowed_signals) == 1
        doc_name, pages, cost, remaining = allowed_signals[0]
        assert doc_name == "Test Doc"
        assert pages == 5  # 5 pages × 1 copy
        assert cost == 5.0  # 5 × 1 × 1.0
        assert remaining == 45.0

    def test_handle_job_approved_with_copies(self, print_monitor, mock_firebase):
        """Test job cost includes copies multiplier"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 100.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        mock_devmode = Mock()
        mock_devmode.Copies = 3
        mock_devmode.Color = 1

        job_data = {
            "JobId": 1,
            "pDocument": "Multi-copy",
            "TotalPages": 5,
            "Status": 0,
            "pDevMode": mock_devmode,
        }

        allowed_signals = []
        print_monitor.job_allowed.connect(
            lambda *args: allowed_signals.append(args)
        )

        with patch.object(print_monitor, "_release_job"):
            print_monitor._handle_new_job("Printer1", job_data)

        _, pages, cost, _ = allowed_signals[0]
        assert pages == 15  # 5 pages × 3 copies
        assert cost == 15.0  # 5 × 3 × 1.0

    def test_handle_job_approved_color(self, print_monitor, mock_firebase):
        """Test color job uses color pricing"""
        print_monitor._bw_price = 1.0
        print_monitor._color_price = 3.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 100.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        mock_devmode = Mock()
        mock_devmode.Copies = 1
        mock_devmode.Color = 2  # DMCOLOR_COLOR

        job_data = {
            "JobId": 1,
            "pDocument": "Color Doc",
            "TotalPages": 5,
            "Status": 0,
            "pDevMode": mock_devmode,
        }

        allowed_signals = []
        print_monitor.job_allowed.connect(
            lambda *args: allowed_signals.append(args)
        )

        with patch.object(print_monitor, "_release_job"):
            print_monitor._handle_new_job("Printer1", job_data)

        _, _, cost, _ = allowed_signals[0]
        assert cost == 15.0  # 5 × 1 × 3.0 (color)

    def test_handle_job_denied_insufficient_budget(
        self, print_monitor, mock_firebase
    ):
        """Test job is denied when budget is insufficient"""
        print_monitor._bw_price = 10.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 5.0},
        }

        job_data = {
            "JobId": 1,
            "pDocument": "Big Doc",
            "TotalPages": 10,
            "Status": 0,
        }

        blocked_signals = []
        print_monitor.job_blocked.connect(
            lambda *args: blocked_signals.append(args)
        )

        with patch.object(
            print_monitor, "_cancel_job", return_value=True
        ) as mock_cancel:
            print_monitor._handle_new_job("Printer1", job_data)

        mock_cancel.assert_called_once_with("Printer1", 1)
        assert len(blocked_signals) == 1
        doc_name, pages, cost, budget = blocked_signals[0]
        assert doc_name == "Big Doc"
        assert pages == 10  # 10 × 1 copy
        assert cost == 100.0  # 10 × 1 × 10.0
        assert budget == 5.0

    def test_handle_job_zero_pages_defaults_to_1(
        self, print_monitor, mock_firebase
    ):
        """Test job with 0 pages defaults to 1"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 10.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        job_data = {
            "JobId": 1,
            "pDocument": "Empty",
            "TotalPages": 0,
            "Status": 0,
        }

        allowed_signals = []
        print_monitor.job_allowed.connect(
            lambda *args: allowed_signals.append(args)
        )

        with patch.object(print_monitor, "_release_job"):
            print_monitor._handle_new_job("Printer1", job_data)

        assert allowed_signals[0][1] == 1  # Defaults to 1 page

    def test_handle_job_deduction_fails_cancels(
        self, print_monitor, mock_firebase
    ):
        """Test job is cancelled when budget deduction fails"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {
            "success": False,
            "error": "DB error",
        }

        job_data = {
            "JobId": 1,
            "pDocument": "Test",
            "TotalPages": 5,
            "Status": 0,
        }

        error_signals = []
        print_monitor.error_occurred.connect(
            lambda msg: error_signals.append(msg)
        )

        with patch.object(
            print_monitor, "_cancel_job", return_value=True
        ) as mock_cancel:
            print_monitor._handle_new_job("Printer1", job_data)

        mock_cancel.assert_called_once()
        assert len(error_signals) == 1


# =============================================================================
# Safe Job Release Tests
# =============================================================================


class TestSafeJobRelease:
    """Tests for the safe job release mechanism"""

    def test_release_job_full_flow(self, print_monitor):
        """Test the complete release flow: pause others → resume printer →
        wait → re-pause printer → resume others"""
        # Setup: one other job in queue besides ours
        print_monitor._paused_printers.add("Printer1")

        other_jobs = [
            {"JobId": 99, "pDocument": "Other"},
            {"JobId": 42, "pDocument": "Ours"},
        ]

        call_order = []

        def track_pause_job(printer, job_id):
            call_order.append(f"pause_job:{job_id}")
            return True

        def track_resume_job(printer, job_id):
            call_order.append(f"resume_job:{job_id}")
            return True

        def track_resume_printer(printer):
            call_order.append("resume_printer")
            return True

        def track_pause_printer(printer):
            call_order.append("pause_printer")
            return True

        with patch.object(
            print_monitor, "_get_printer_jobs", return_value=other_jobs
        ):
            with patch.object(
                print_monitor, "_pause_job", side_effect=track_pause_job
            ):
                with patch.object(
                    print_monitor,
                    "_resume_printer",
                    side_effect=track_resume_printer,
                ):
                    with patch.object(
                        print_monitor,
                        "_wait_for_job_completion",
                    ):
                        with patch.object(
                            print_monitor,
                            "_pause_printer",
                            side_effect=track_pause_printer,
                        ):
                            with patch.object(
                                print_monitor,
                                "_resume_job",
                                side_effect=track_resume_job,
                            ):
                                print_monitor._release_job("Printer1", 42)

        # Verify order: pause other → resume printer → (wait) → re-pause → resume other
        assert call_order == [
            "pause_job:99",
            "resume_printer",
            "pause_printer",
            "resume_job:99",
        ]

    def test_release_job_tracks_releasing_state(self, print_monitor):
        """Test that releasing job is tracked and cleaned up"""
        # We need to check that _releasing_jobs is set during release
        was_releasing = [False]

        def check_releasing(printer, job_id):
            with print_monitor._lock:
                was_releasing[0] = "Printer1:42" in print_monitor._releasing_jobs

        with patch.object(
            print_monitor, "_get_printer_jobs", return_value=[]
        ):
            with patch.object(print_monitor, "_resume_printer", return_value=True):
                with patch.object(
                    print_monitor,
                    "_wait_for_job_completion",
                    side_effect=check_releasing,
                ):
                    with patch.object(
                        print_monitor, "_pause_printer", return_value=True
                    ):
                        print_monitor._release_job("Printer1", 42)

        assert was_releasing[0] is True
        # Should be cleaned up after
        assert "Printer1:42" not in print_monitor._releasing_jobs

    def test_release_job_re_pauses_on_exception(self, print_monitor):
        """Test printer is re-paused even if release fails"""
        with patch.object(
            print_monitor, "_get_printer_jobs", return_value=[]
        ):
            with patch.object(
                print_monitor,
                "_resume_printer",
                side_effect=Exception("Fail"),
            ):
                with patch.object(
                    print_monitor, "_pause_printer"
                ) as mock_pause:
                    print_monitor._release_job("Printer1", 42)

        # Should attempt to re-pause on failure
        mock_pause.assert_called()

    def test_wait_for_job_completion_job_finishes(self, print_monitor):
        """Test wait_for_job_completion detects job leaving queue"""
        call_count = [0]

        def mock_is_in_queue(printer, job_id):
            call_count[0] += 1
            return call_count[0] < 3  # Gone on 3rd check

        with patch.object(
            print_monitor, "_is_job_in_queue", side_effect=mock_is_in_queue
        ):
            with patch("time.sleep"):
                print_monitor._wait_for_job_completion("Printer1", 42)

        assert call_count[0] == 3

    def test_wait_for_job_completion_timeout(self, print_monitor):
        """Test wait_for_job_completion handles timeout"""
        # Use a very short timeout so it exits quickly
        with patch.object(
            print_monitor, "_is_job_in_queue", return_value=True
        ):
            with patch("time.sleep"):
                print_monitor._wait_for_job_completion(
                    "Printer1", 42, timeout=0.001
                )
                # Should exit without error after timeout

    def test_is_job_in_queue_true(self, print_monitor):
        """Test is_job_in_queue returns True when job exists"""
        with patch.object(
            print_monitor,
            "_get_printer_jobs",
            return_value=[{"JobId": 42}, {"JobId": 43}],
        ):
            assert print_monitor._is_job_in_queue("Printer1", 42) is True

    def test_is_job_in_queue_false(self, print_monitor):
        """Test is_job_in_queue returns False when job is gone"""
        with patch.object(
            print_monitor,
            "_get_printer_jobs",
            return_value=[{"JobId": 43}],
        ):
            assert print_monitor._is_job_in_queue("Printer1", 42) is False


# =============================================================================
# Spool Wait Tests
# =============================================================================


class TestSpoolWait:
    """Tests for _wait_for_spool_complete"""

    def test_returns_immediately_if_not_spooling(self, print_monitor):
        """Test returns immediately if job is done spooling"""
        job_data = {"TotalPages": 5, "Status": 0}

        result = print_monitor._wait_for_spool_complete(
            "Printer1", 1, job_data
        )

        assert result == job_data

    def test_waits_for_spooling_to_complete(self, print_monitor):
        """Test waits until spooling flag is cleared"""
        job_data = {"TotalPages": 0, "Status": 8}  # JOB_STATUS_SPOOLING

        # After 2 checks, spooling completes
        call_count = [0]

        def mock_get_job_info(printer, job_id):
            call_count[0] += 1
            if call_count[0] < 3:
                return {"TotalPages": 0, "Status": 8, "Size": 100}
            return {"TotalPages": 5, "Status": 0, "Size": 5000}

        with patch.object(
            print_monitor, "_get_job_info", side_effect=mock_get_job_info
        ):
            with patch("time.sleep"):
                result = print_monitor._wait_for_spool_complete(
                    "Printer1", 1, job_data
                )

        assert result["TotalPages"] == 5

    def test_stable_page_count_accepted(self, print_monitor):
        """Test page count is accepted after stabilizing"""
        job_data = {"TotalPages": 0, "Status": 8}

        # Page count stabilizes at 3 after being stable for 3 checks
        call_count = [0]

        def mock_get_job_info(printer, job_id):
            call_count[0] += 1
            return {"TotalPages": 3, "Status": 8, "Size": 1000}

        with patch.object(
            print_monitor, "_get_job_info", side_effect=mock_get_job_info
        ):
            with patch("time.sleep"):
                result = print_monitor._wait_for_spool_complete(
                    "Printer1", 1, job_data
                )

        assert result["TotalPages"] == 3

    def test_job_disappears_during_spool(self, print_monitor):
        """Test handles job disappearing during spool wait"""
        job_data = {"TotalPages": 0, "Status": 8}

        with patch.object(
            print_monitor, "_get_job_info", return_value={}
        ):
            with patch("time.sleep"):
                result = print_monitor._wait_for_spool_complete(
                    "Printer1", 1, job_data
                )

        # Should return original data since job disappeared
        assert result == job_data


# =============================================================================
# Crash Recovery Tests
# =============================================================================


class TestCrashRecovery:
    """Tests for crash recovery on startup"""

    def test_recover_no_leftover_printers(self, print_monitor):
        """Test recovery does nothing when no printers left paused"""
        with _global_lock:
            _globally_paused_printers.clear()

        with patch.object(
            print_monitor, "_resume_printer"
        ) as mock_resume:
            print_monitor._recover_from_crash()

        mock_resume.assert_not_called()

    def test_recover_resumes_leftover_printers(self, print_monitor):
        """Test recovery resumes printers from global tracker"""
        with _global_lock:
            _globally_paused_printers.add("CrashedPrinter")

        with patch.object(
            print_monitor, "_is_printer_paused", return_value=True
        ):
            with patch.object(
                print_monitor, "_resume_printer"
            ) as mock_resume:
                print_monitor._recover_from_crash()

        mock_resume.assert_called_once_with("CrashedPrinter")

        # Global set should be cleared
        with _global_lock:
            assert len(_globally_paused_printers) == 0

    def test_recover_skips_not_paused(self, print_monitor):
        """Test recovery skips printers that aren't actually paused"""
        with _global_lock:
            _globally_paused_printers.add("NotPausedPrinter")

        with patch.object(
            print_monitor, "_is_printer_paused", return_value=False
        ):
            with patch.object(
                print_monitor, "_resume_printer"
            ) as mock_resume:
                print_monitor._recover_from_crash()

        mock_resume.assert_not_called()

        # Cleanup
        with _global_lock:
            _globally_paused_printers.clear()

    def test_recover_handles_exception(self, print_monitor):
        """Test recovery handles exceptions gracefully"""
        with _global_lock:
            _globally_paused_printers.add("ErrorPrinter")

        with patch.object(
            print_monitor,
            "_is_printer_paused",
            side_effect=Exception("Error"),
        ):
            # Should not raise
            print_monitor._recover_from_crash()

        # Cleanup
        with _global_lock:
            _globally_paused_printers.clear()

    def test_recover_no_win32print(self, print_monitor):
        """Test recovery does nothing without win32print"""
        with patch("services.print_monitor_service.win32print", None):
            # Should not raise
            print_monitor._recover_from_crash()


# =============================================================================
# Atexit Handler Tests
# =============================================================================


class TestAtexitHandler:
    """Tests for the module-level atexit handler"""

    def test_atexit_resumes_paused_printers(self):
        """Test atexit handler resumes globally tracked printers"""
        mock_w32 = Mock()
        mock_handle = Mock()
        mock_w32.OpenPrinter.return_value = mock_handle

        with _global_lock:
            _globally_paused_printers.add("AtexitPrinter")

        with patch("services.print_monitor_service.win32print", mock_w32):
            _atexit_resume_printers()

        mock_w32.SetPrinter.assert_called_once_with(
            mock_handle, 0, None, PRINTER_CONTROL_RESUME
        )

        # Cleanup
        with _global_lock:
            _globally_paused_printers.discard("AtexitPrinter")

    def test_atexit_no_printers_noop(self):
        """Test atexit handler does nothing when no printers tracked"""
        with _global_lock:
            _globally_paused_printers.clear()

        mock_w32 = Mock()
        with patch("services.print_monitor_service.win32print", mock_w32):
            _atexit_resume_printers()

        mock_w32.OpenPrinter.assert_not_called()

    def test_atexit_no_win32print_noop(self):
        """Test atexit handler does nothing without win32print"""
        with _global_lock:
            _globally_paused_printers.add("NoPrinter")

        with patch("services.print_monitor_service.win32print", None):
            # Should not raise
            _atexit_resume_printers()

        # Cleanup
        with _global_lock:
            _globally_paused_printers.discard("NoPrinter")

    def test_atexit_handles_exception(self):
        """Test atexit handler swallows exceptions"""
        with _global_lock:
            _globally_paused_printers.add("ErrorPrinter")

        mock_w32 = Mock()
        mock_w32.OpenPrinter.side_effect = Exception("Crash")

        with patch("services.print_monitor_service.win32print", mock_w32):
            # Should not raise
            _atexit_resume_printers()

        # Cleanup
        with _global_lock:
            _globally_paused_printers.discard("ErrorPrinter")


# =============================================================================
# Signal Tests
# =============================================================================


class TestSignals:
    """Tests for signal emissions"""

    def test_job_allowed_signal(self, print_monitor):
        """Test job_allowed signal emits correctly"""
        received = []
        print_monitor.job_allowed.connect(lambda *args: received.append(args))

        print_monitor.job_allowed.emit("Doc", 5, 10.0, 40.0)

        assert received == [("Doc", 5, 10.0, 40.0)]

    def test_job_blocked_signal(self, print_monitor):
        """Test job_blocked signal emits correctly"""
        received = []
        print_monitor.job_blocked.connect(lambda *args: received.append(args))

        print_monitor.job_blocked.emit("Doc", 10, 100.0, 5.0)

        assert received == [("Doc", 10, 100.0, 5.0)]

    def test_budget_updated_signal(self, print_monitor):
        """Test budget_updated signal emits correctly"""
        received = []
        print_monitor.budget_updated.connect(lambda x: received.append(x))

        print_monitor.budget_updated.emit(42.5)

        assert received == [42.5]

    def test_error_occurred_signal(self, print_monitor):
        """Test error_occurred signal emits correctly"""
        received = []
        print_monitor.error_occurred.connect(lambda x: received.append(x))

        print_monitor.error_occurred.emit("Test error")

        assert received == ["Test error"]


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases"""

    def test_concurrent_job_processing(self, print_monitor):
        """Test concurrent job processing is thread-safe"""
        print_monitor._is_monitoring = True
        process_count = [0]

        job_data = {"JobId": 1, "pDocument": "Test", "TotalPages": 1, "Status": 0}

        def mock_handle(*args):
            process_count[0] += 1

        def mock_poll():
            # Simulate detecting job 1
            with print_monitor._lock:
                if "Printer1:1" in print_monitor._processed_jobs:
                    return
                print_monitor._processed_jobs.add("Printer1:1")
            mock_handle("Printer1", job_data)

        threads = [
            threading.Thread(target=mock_poll)
            for _ in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should only process once
        assert process_count[0] == 1

    def test_poll_with_no_printers(self, print_monitor):
        """Test poll handles no printers gracefully"""
        print_monitor._is_monitoring = True

        with patch.object(print_monitor, "_get_all_printers", return_value=[]):
            # Should not crash
            print_monitor._poll_print_queues()

    def test_handle_job_with_no_devmode(self, print_monitor, mock_firebase):
        """Test job handling when DEVMODE is None (defaults to 1 copy, B&W)"""
        print_monitor._bw_price = 2.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 100.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        job_data = {
            "JobId": 1,
            "pDocument": "No DevMode",
            "TotalPages": 3,
            "Status": 0,
            # No pDevMode key
        }

        allowed_signals = []
        print_monitor.job_allowed.connect(
            lambda *args: allowed_signals.append(args)
        )

        with patch.object(print_monitor, "_release_job"):
            print_monitor._handle_new_job("Printer1", job_data)

        _, pages, cost, _ = allowed_signals[0]
        assert pages == 3  # 3 × 1 copy
        assert cost == 6.0  # 3 × 1 × 2.0 (B&W default)

    def test_pause_all_no_printers(self, print_monitor):
        """Test pause_all_printers handles no printers"""
        with patch.object(print_monitor, "_get_all_printers", return_value=[]):
            # Should not crash
            print_monitor._pause_all_printers()

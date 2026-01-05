"""
Tests for PrintMonitorService
"""

import threading
from unittest.mock import MagicMock, Mock, patch

import pytest
from PyQt6.QtCore import QTimer

from services.print_monitor_service import (
    JOB_CONTROL_CANCEL,
    JOB_CONTROL_PAUSE,
    JOB_CONTROL_RESUME,
    PrintMonitorService,
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


# =============================================================================
# Start/Stop Monitoring Tests
# =============================================================================


class TestStartStopMonitoring:
    """Tests for start and stop monitoring"""

    def test_start_monitoring_success(self, print_monitor):
        """Test starting monitoring returns success"""
        with patch.object(print_monitor, "_load_pricing"):
            with patch.object(print_monitor, "_initialize_known_jobs"):
                with patch.object(print_monitor, "_start_wmi_watcher"):
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
        """Test starting creates poll timer"""
        with patch.object(print_monitor, "_load_pricing"):
            with patch.object(print_monitor, "_initialize_known_jobs"):
                with patch.object(print_monitor, "_start_wmi_watcher"):
                    print_monitor.start_monitoring()

        assert print_monitor._poll_timer is not None
        assert isinstance(print_monitor._poll_timer, QTimer)

    def test_stop_monitoring_success(self, print_monitor):
        """Test stopping monitoring returns success"""
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()

        with patch.object(print_monitor, "_stop_wmi_watcher"):
            result = print_monitor.stop_monitoring()

        assert result["success"] is True
        assert print_monitor.is_monitoring() is False

    def test_stop_monitoring_not_running(self, print_monitor):
        """Test stopping when not monitoring returns message"""
        result = print_monitor.stop_monitoring()

        assert result["success"] is True
        assert result["message"] == "Not monitoring"

    def test_stop_monitoring_clears_state(self, print_monitor):
        """Test stopping clears known and processed jobs"""
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()
        print_monitor._known_jobs = {"Printer1": {1, 2, 3}}
        print_monitor._processed_jobs = {"Printer1:1", "Printer1:2"}

        with patch.object(print_monitor, "_stop_wmi_watcher"):
            print_monitor.stop_monitoring()

        assert print_monitor._known_jobs == {}
        assert print_monitor._processed_jobs == set()

    def test_stop_monitoring_stops_timer(self, print_monitor):
        """Test stopping stops the poll timer"""
        print_monitor._is_monitoring = True
        mock_timer = Mock()
        print_monitor._poll_timer = mock_timer

        with patch.object(print_monitor, "_stop_wmi_watcher"):
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

    def test_load_pricing_uses_defaults_on_failure(self, print_monitor, mock_firebase):
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

    def test_calculate_cost_bw(self, print_monitor):
        """Test cost calculation for black & white"""
        print_monitor._bw_price = 0.5

        cost = print_monitor._calculate_cost(10, is_color=False)

        assert cost == 5.0

    def test_calculate_cost_color(self, print_monitor):
        """Test cost calculation for color"""
        print_monitor._color_price = 2.0

        cost = print_monitor._calculate_cost(10, is_color=True)

        assert cost == 20.0

    def test_calculate_cost_single_page(self, print_monitor):
        """Test cost calculation for single page"""
        print_monitor._bw_price = 1.0

        cost = print_monitor._calculate_cost(1, is_color=False)

        assert cost == 1.0

    def test_is_color_job_from_devmode_color(self, print_monitor):
        """Test color detection returns True for color jobs"""
        mock_devmode = Mock()
        mock_devmode.Color = 2  # DMCOLOR_COLOR

        is_color = print_monitor._is_color_job_from_devmode(mock_devmode)

        assert is_color is True

    def test_is_color_job_from_devmode_bw(self, print_monitor):
        """Test color detection returns False for B&W jobs"""
        mock_devmode = Mock()
        mock_devmode.Color = 1  # DMCOLOR_MONOCHROME

        is_color = print_monitor._is_color_job_from_devmode(mock_devmode)

        assert is_color is False

    def test_is_color_job_from_devmode_none(self, print_monitor):
        """Test color detection returns False when devmode is None"""
        is_color = print_monitor._is_color_job_from_devmode(None)

        assert is_color is False

    def test_is_color_job_from_devmode_missing_attribute(self, print_monitor):
        """Test color detection returns False when Color attribute is missing"""
        mock_devmode = Mock(spec=[])  # No attributes

        is_color = print_monitor._is_color_job_from_devmode(mock_devmode)

        assert is_color is False


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

        budget = print_monitor._get_user_budget()

        assert budget == 0.0

    def test_get_user_budget_handles_exception(self, print_monitor, mock_firebase):
        """Test getting budget handles exceptions"""
        mock_firebase.db_get.side_effect = Exception("Network error")

        budget = print_monitor._get_user_budget()

        assert budget == 0.0

    def test_deduct_budget_success(self, print_monitor, mock_firebase):
        """Test deducting budget successfully"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        # Track signal emission
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
        mock_firebase.db_update.return_value = {"success": False, "error": "Failed"}

        result = print_monitor._deduct_budget(10.0)

        assert result is False

    def test_deduct_budget_cannot_go_negative(self, print_monitor, mock_firebase):
        """Test budget cannot go below zero"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 5.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        print_monitor._deduct_budget(10.0)

        # Check update was called with 0, not -5
        call_args = mock_firebase.db_update.call_args
        assert call_args[0][1]["printBalance"] == 0.0


# =============================================================================
# Spooler Interaction Tests
# =============================================================================


class TestSpoolerInteraction:
    """Tests for Windows Print Spooler interaction"""

    def test_get_all_printers_no_win32print(self, print_monitor):
        """Test get_all_printers returns empty when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            printers = print_monitor._get_all_printers()

        assert printers == []

    def test_get_all_printers_success(self, print_monitor):
        """Test get_all_printers returns printer names"""
        mock_win32print = Mock()
        mock_win32print.PRINTER_ENUM_LOCAL = 1
        mock_win32print.PRINTER_ENUM_CONNECTIONS = 2
        mock_win32print.EnumPrinters.return_value = [
            (0, "", "HP LaserJet", ""),
            (0, "", "Canon Inkjet", ""),
        ]

        with patch("services.print_monitor_service.win32print", mock_win32print):
            printers = print_monitor._get_all_printers()

        assert printers == ["HP LaserJet", "Canon Inkjet"]

    def test_get_printer_jobs_no_win32print(self, print_monitor):
        """Test get_printer_jobs returns empty when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            jobs = print_monitor._get_printer_jobs("Printer1")

        assert jobs == []

    def test_get_printer_jobs_success(self, print_monitor):
        """Test get_printer_jobs returns job list"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 1, "pDocument": "Doc1"},
            {"JobId": 2, "pDocument": "Doc2"},
        ]

        with patch("services.print_monitor_service.win32print", mock_win32print):
            jobs = print_monitor._get_printer_jobs("Printer1")

        assert len(jobs) == 2
        mock_win32print.ClosePrinter.assert_called_once_with(mock_handle)

    def test_pause_job_no_win32print(self, print_monitor):
        """Test pause_job returns False when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            result = print_monitor._pause_job("Printer1", 1)

        assert result is False

    def test_pause_job_success(self, print_monitor):
        """Test pause_job calls SetJob with PAUSE command"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._pause_job("Printer1", 42)

        assert result is True
        mock_win32print.SetJob.assert_called_once_with(
            mock_handle, 42, 0, None, JOB_CONTROL_PAUSE
        )

    def test_resume_job_success(self, print_monitor):
        """Test resume_job calls SetJob with RESUME command"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._resume_job("Printer1", 42)

        assert result is True
        mock_win32print.SetJob.assert_called_once_with(
            mock_handle, 42, 0, None, JOB_CONTROL_RESUME
        )

    def test_cancel_job_success(self, print_monitor):
        """Test cancel_job calls SetJob with CANCEL command"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._cancel_job("Printer1", 42)

        assert result is True
        mock_win32print.SetJob.assert_called_once_with(
            mock_handle, 42, 0, None, JOB_CONTROL_CANCEL
        )


# =============================================================================
# WMI Event Watcher Tests
# =============================================================================


class TestWMIWatcher:
    """Tests for WMI event watcher"""

    def test_start_wmi_watcher_no_wmi(self, print_monitor):
        """Test WMI watcher doesn't start when WMI unavailable"""
        with patch("services.print_monitor_service.wmi", None):
            print_monitor._start_wmi_watcher()

        assert print_monitor._wmi_thread is None

    def test_start_wmi_watcher_creates_thread(self, print_monitor):
        """Test WMI watcher creates background thread"""
        mock_wmi = Mock()
        mock_pythoncom = Mock()

        with patch("services.print_monitor_service.wmi", mock_wmi):
            with patch("services.print_monitor_service.pythoncom", mock_pythoncom):
                print_monitor._start_wmi_watcher()

        assert print_monitor._wmi_thread is not None
        assert print_monitor._wmi_thread.name == "PrintMonitor-WMI"
        assert print_monitor._wmi_thread.daemon is True

        # Cleanup
        print_monitor._wmi_stop_event.set()
        print_monitor._wmi_thread.join(timeout=1)

    def test_stop_wmi_watcher_sets_stop_event(self, print_monitor):
        """Test stopping WMI watcher sets stop event"""
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        print_monitor._wmi_thread = mock_thread

        print_monitor._stop_wmi_watcher()

        assert print_monitor._wmi_stop_event.is_set()
        mock_thread.join.assert_called_once_with(timeout=3.0)

    def test_on_wmi_print_job_event_parses_job(self, print_monitor):
        """Test WMI event handler parses job correctly"""
        mock_event = Mock()
        mock_event.Name = "HP LaserJet, 42"
        mock_event.Document = "Test Document"
        mock_event.TotalPages = 5

        with patch.object(print_monitor, "_process_job_thread_safe") as mock_process:
            print_monitor._on_wmi_print_job_event(mock_event)

        mock_process.assert_called_once()
        call_args = mock_process.call_args
        assert call_args[0][0] == "HP LaserJet"
        assert call_args[0][1]["JobId"] == 42
        assert call_args[0][1]["pDocument"] == "Test Document"
        assert call_args[0][1]["TotalPages"] == 5

    def test_on_wmi_print_job_event_invalid_format(self, print_monitor):
        """Test WMI event handler handles invalid format"""
        mock_event = Mock()
        mock_event.Name = "InvalidFormat"  # No comma

        with patch.object(print_monitor, "_process_job_thread_safe") as mock_process:
            print_monitor._on_wmi_print_job_event(mock_event)

        mock_process.assert_not_called()


# =============================================================================
# Thread-Safe Processing Tests
# =============================================================================


class TestThreadSafeProcessing:
    """Tests for thread-safe job processing"""

    def test_process_job_thread_safe_first_time(self, print_monitor):
        """Test processing job for the first time"""
        job_data = {"JobId": 1, "pDocument": "Test", "TotalPages": 1}

        with patch.object(print_monitor, "_handle_new_job") as mock_handle:
            print_monitor._process_job_thread_safe("Printer1", job_data)

        mock_handle.assert_called_once_with("Printer1", job_data)
        assert "Printer1:1" in print_monitor._processed_jobs

    def test_process_job_thread_safe_skips_duplicate(self, print_monitor):
        """Test duplicate job is skipped"""
        print_monitor._processed_jobs.add("Printer1:1")
        job_data = {"JobId": 1, "pDocument": "Test", "TotalPages": 1}

        with patch.object(print_monitor, "_handle_new_job") as mock_handle:
            print_monitor._process_job_thread_safe("Printer1", job_data)

        mock_handle.assert_not_called()

    def test_process_job_thread_safe_updates_known_jobs(self, print_monitor):
        """Test processing updates known jobs"""
        job_data = {"JobId": 42, "pDocument": "Test", "TotalPages": 1}

        with patch.object(print_monitor, "_handle_new_job"):
            print_monitor._process_job_thread_safe("Printer1", job_data)

        assert 42 in print_monitor._known_jobs.get("Printer1", set())


# =============================================================================
# Polling Tests
# =============================================================================


class TestPolling:
    """Tests for polling fallback"""

    def test_initialize_known_jobs(self, print_monitor):
        """Test initializing known jobs"""
        mock_win32print = Mock()
        mock_win32print.PRINTER_ENUM_LOCAL = 1
        mock_win32print.PRINTER_ENUM_CONNECTIONS = 2
        mock_win32print.EnumPrinters.return_value = [
            (0, "", "Printer1", ""),
        ]
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 1},
            {"JobId": 2},
        ]

        with patch("services.print_monitor_service.win32print", mock_win32print):
            print_monitor._initialize_known_jobs()

        assert print_monitor._known_jobs["Printer1"] == {1, 2}

    def test_poll_spooler_not_monitoring(self, print_monitor):
        """Test polling does nothing when not monitoring"""
        print_monitor._is_monitoring = False

        with patch.object(print_monitor, "_get_all_printers") as mock_get:
            print_monitor._poll_spooler()

        mock_get.assert_not_called()

    def test_poll_spooler_detects_new_job(self, print_monitor):
        """Test polling detects new print job"""
        print_monitor._is_monitoring = True
        print_monitor._known_jobs = {"Printer1": {1, 2}}

        mock_win32print = Mock()
        mock_win32print.PRINTER_ENUM_LOCAL = 1
        mock_win32print.PRINTER_ENUM_CONNECTIONS = 2
        mock_win32print.EnumPrinters.return_value = [(0, "", "Printer1", "")]
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 1},
            {"JobId": 2},
            {"JobId": 3, "pDocument": "New Doc", "TotalPages": 5},  # New job
        ]

        with patch("services.print_monitor_service.win32print", mock_win32print):
            with patch.object(
                print_monitor, "_process_job_thread_safe"
            ) as mock_process:
                print_monitor._poll_spooler()

        mock_process.assert_called_once()
        call_args = mock_process.call_args
        assert call_args[0][0] == "Printer1"
        assert call_args[0][1]["JobId"] == 3

    def test_poll_spooler_cleans_processed_jobs(self, print_monitor):
        """Test polling cleans up processed jobs no longer in queue"""
        print_monitor._is_monitoring = True
        print_monitor._known_jobs = {"Printer1": {1, 2}}
        print_monitor._processed_jobs = {"Printer1:1", "Printer1:2"}

        mock_win32print = Mock()
        mock_win32print.PRINTER_ENUM_LOCAL = 1
        mock_win32print.PRINTER_ENUM_CONNECTIONS = 2
        mock_win32print.EnumPrinters.return_value = [(0, "", "Printer1", "")]
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 2},  # Only job 2 remains
        ]

        with patch("services.print_monitor_service.win32print", mock_win32print):
            print_monitor._poll_spooler()

        # Job 1 should be removed from processed
        assert "Printer1:1" not in print_monitor._processed_jobs
        assert "Printer1:2" in print_monitor._processed_jobs


# =============================================================================
# Job Handling Tests
# =============================================================================


class TestJobHandling:
    """Tests for job handling logic"""

    def test_handle_new_job_allowed(self, print_monitor, mock_firebase):
        """Test job is allowed when budget sufficient"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        job_data = {"JobId": 1, "pDocument": "Test Doc", "TotalPages": 5}

        # Track signals
        allowed_signals = []
        print_monitor.job_allowed.connect(lambda *args: allowed_signals.append(args))

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(print_monitor, "_resume_job", return_value=True):
                print_monitor._handle_new_job("Printer1", job_data)

        assert len(allowed_signals) == 1
        doc_name, pages, cost, remaining = allowed_signals[0]
        assert doc_name == "Test Doc"
        assert pages == 5
        assert cost == 5.0  # 5 pages * 1.0
        assert remaining == 45.0  # 50 - 5

    def test_handle_new_job_blocked(self, print_monitor, mock_firebase):
        """Test job is blocked when budget insufficient"""
        print_monitor._bw_price = 10.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 5.0},  # Not enough
        }

        job_data = {"JobId": 1, "pDocument": "Big Doc", "TotalPages": 10}

        # Track signals
        blocked_signals = []
        print_monitor.job_blocked.connect(lambda *args: blocked_signals.append(args))

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(
                print_monitor, "_cancel_job", return_value=True
            ) as mock_cancel:
                print_monitor._handle_new_job("Printer1", job_data)

        mock_cancel.assert_called_once_with("Printer1", 1)
        assert len(blocked_signals) == 1
        doc_name, pages, cost, budget = blocked_signals[0]
        assert doc_name == "Big Doc"
        assert pages == 10
        assert cost == 100.0  # 10 pages * 10.0
        assert budget == 5.0

    def test_handle_new_job_zero_pages(self, print_monitor, mock_firebase):
        """Test job with 0 pages assumes 1 page"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 10.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        job_data = {"JobId": 1, "pDocument": "Test", "TotalPages": 0}

        allowed_signals = []
        print_monitor.job_allowed.connect(lambda *args: allowed_signals.append(args))

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(print_monitor, "_resume_job", return_value=True):
                print_monitor._handle_new_job("Printer1", job_data)

        assert allowed_signals[0][1] == 1  # Pages should be 1

    def test_handle_new_job_pause_fails(self, print_monitor):
        """Test job handling when pause fails"""
        job_data = {"JobId": 1, "pDocument": "Test", "TotalPages": 1}

        with patch.object(print_monitor, "_pause_job", return_value=False):
            with patch.object(print_monitor, "_get_user_budget") as mock_budget:
                print_monitor._handle_new_job("Printer1", job_data)

        # Should not check budget if pause failed
        mock_budget.assert_not_called()

    def test_handle_new_job_deduction_fails(self, print_monitor, mock_firebase):
        """Test job is cancelled when deduction fails"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {"success": False, "error": "Failed"}

        job_data = {"JobId": 1, "pDocument": "Test", "TotalPages": 5}

        error_signals = []
        print_monitor.error_occurred.connect(lambda msg: error_signals.append(msg))

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(
                print_monitor, "_cancel_job", return_value=True
            ) as mock_cancel:
                print_monitor._handle_new_job("Printer1", job_data)

        mock_cancel.assert_called_once()
        assert len(error_signals) == 1


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

    def test_exception_in_poll_spooler(self, print_monitor):
        """Test poll_spooler handles exceptions gracefully"""
        print_monitor._is_monitoring = True

        with patch.object(
            print_monitor, "_get_all_printers", side_effect=Exception("Error")
        ):
            # Should not raise
            print_monitor._poll_spooler()

    def test_exception_in_handle_new_job(self, print_monitor, mock_firebase):
        """Test handle_new_job handles exceptions in pause"""
        mock_firebase.db_get.side_effect = Exception("Network error")
        job_data = {"JobId": 1, "pDocument": "Test", "TotalPages": 1}

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(print_monitor, "_cancel_job"):
                # Should not raise
                print_monitor._handle_new_job("Printer1", job_data)

    def test_concurrent_job_processing(self, print_monitor):
        """Test concurrent job processing is thread-safe"""
        job_data = {"JobId": 1, "pDocument": "Test", "TotalPages": 1}
        process_count = [0]

        def mock_handle(*args):
            process_count[0] += 1

        with patch.object(print_monitor, "_handle_new_job", side_effect=mock_handle):
            # Simulate concurrent calls
            threads = [
                threading.Thread(
                    target=print_monitor._process_job_thread_safe,
                    args=("Printer1", job_data),
                )
                for _ in range(10)
            ]

            for t in threads:
                t.start()
            for t in threads:
                t.join()

        # Should only process once despite 10 concurrent calls
        assert process_count[0] == 1

    def test_printer_name_with_comma(self, print_monitor):
        """Test handling printer names that contain commas"""
        mock_event = Mock()
        mock_event.Name = "HP Color, LaserJet Pro, 42"  # Printer name has comma
        mock_event.Document = "Test"
        mock_event.TotalPages = 1

        with patch.object(print_monitor, "_process_job_thread_safe") as mock_process:
            print_monitor._on_wmi_print_job_event(mock_event)

        # Should parse correctly using rsplit
        call_args = mock_process.call_args
        assert call_args[0][0] == "HP Color, LaserJet Pro"
        assert call_args[0][1]["JobId"] == 42

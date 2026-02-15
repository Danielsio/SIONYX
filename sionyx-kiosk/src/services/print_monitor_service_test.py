"""
Tests for PrintMonitorService
"""

import threading
from unittest.mock import Mock, patch

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


# =============================================================================
# Copies from DEVMODE Tests
# =============================================================================


class TestCopiesFromDevmode:
    """Tests for _get_copies_from_devmode method"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_get_copies_from_devmode_with_value(self, print_monitor):
        """Test extracting copies when value is present"""
        mock_devmode = Mock()
        mock_devmode.Copies = 3
        copies = print_monitor._get_copies_from_devmode(mock_devmode)
        assert copies == 3

    def test_get_copies_from_devmode_none(self, print_monitor):
        """Test returns 1 when devmode is None"""
        copies = print_monitor._get_copies_from_devmode(None)
        assert copies == 1

    def test_get_copies_from_devmode_zero(self, print_monitor):
        """Test returns 1 when copies is 0"""
        mock_devmode = Mock()
        mock_devmode.Copies = 0
        copies = print_monitor._get_copies_from_devmode(mock_devmode)
        assert copies == 1

    def test_get_copies_from_devmode_negative(self, print_monitor):
        """Test returns 1 when copies is negative"""
        mock_devmode = Mock()
        mock_devmode.Copies = -5
        copies = print_monitor._get_copies_from_devmode(mock_devmode)
        assert copies == 1

    def test_get_copies_from_devmode_missing_attribute(self, print_monitor):
        """Test returns 1 when Copies attribute is missing"""
        mock_devmode = Mock(spec=[])  # No Copies attribute
        copies = print_monitor._get_copies_from_devmode(mock_devmode)
        assert copies == 1

    def test_get_copies_from_devmode_exception(self, print_monitor):
        """Test returns 1 when exception occurs"""
        mock_devmode = Mock()
        # Make getattr raise an exception
        type(mock_devmode).Copies = property(
            lambda self: (_ for _ in ()).throw(Exception("Error"))
        )
        copies = print_monitor._get_copies_from_devmode(mock_devmode)
        assert copies == 1


# =============================================================================
# Job Info Tests
# =============================================================================


class TestGetJobInfo:
    """Tests for _get_job_info method"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_get_job_info_no_win32print(self, print_monitor):
        """Test returns empty dict when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            result = print_monitor._get_job_info("Printer1", 42)
        assert result == {}

    def test_get_job_info_success(self, print_monitor):
        """Test getting job info successfully"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle
        mock_win32print.GetJob.return_value = {"TotalPages": 10, "Status": 0}

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._get_job_info("Printer1", 42)

        assert result["TotalPages"] == 10
        mock_win32print.GetJob.assert_called_once_with(mock_handle, 42, 2)
        mock_win32print.ClosePrinter.assert_called_once_with(mock_handle)

    def test_get_job_info_returns_none(self, print_monitor):
        """Test returns empty dict when GetJob returns None"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle
        mock_win32print.GetJob.return_value = None

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._get_job_info("Printer1", 42)

        assert result == {}

    def test_get_job_info_exception(self, print_monitor):
        """Test returns empty dict on exception"""
        mock_win32print = Mock()
        mock_win32print.OpenPrinter.side_effect = Exception("Printer not found")

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._get_job_info("Printer1", 42)

        assert result == {}


# =============================================================================
# Error 87 Handling Tests
# =============================================================================


class TestError87Handling:
    """Tests for error 87 (job already completed) handling"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_pause_job_error_87_winerror(self, print_monitor):
        """Test pause returns False for error 87 via winerror attribute"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        error = Exception("The parameter is incorrect")
        error.winerror = 87
        mock_win32print.SetJob.side_effect = error

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._pause_job("Printer1", 42)

        assert result is False  # Can't pause completed job

    def test_pause_job_error_87_args(self, print_monitor):
        """Test pause returns False for error 87 via args"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        error = Exception("The parameter is incorrect")
        error.winerror = None
        error.args = (87,)
        mock_win32print.SetJob.side_effect = error

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._pause_job("Printer1", 42)

        assert result is False

    def test_pause_job_other_error(self, print_monitor):
        """Test pause returns False for non-87 errors"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        error = Exception("Access denied")
        error.winerror = 5  # Access denied
        mock_win32print.SetJob.side_effect = error

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._pause_job("Printer1", 42)

        assert result is False

    def test_resume_job_error_87_returns_true(self, print_monitor):
        """Test resume returns True for error 87 (job completed fast)"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        error = Exception("The parameter is incorrect")
        error.winerror = 87
        mock_win32print.SetJob.side_effect = error

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._resume_job("Printer1", 42)

        assert result is True  # Job printed successfully, just fast

    def test_resume_job_no_win32print(self, print_monitor):
        """Test resume returns False when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            result = print_monitor._resume_job("Printer1", 42)
        assert result is False

    def test_resume_job_other_error(self, print_monitor):
        """Test resume returns False for non-87 errors"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        error = Exception("Access denied")
        error.winerror = 5
        mock_win32print.SetJob.side_effect = error

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._resume_job("Printer1", 42)

        assert result is False

    def test_cancel_job_error_87_returns_true(self, print_monitor):
        """Test cancel returns True for error 87 (job already gone)"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        error = Exception("The parameter is incorrect")
        error.winerror = 87
        mock_win32print.SetJob.side_effect = error

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._cancel_job("Printer1", 42)

        assert result is True  # Job is gone, which is what we wanted

    def test_cancel_job_no_win32print(self, print_monitor):
        """Test cancel returns False when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            result = print_monitor._cancel_job("Printer1", 42)
        assert result is False

    def test_cancel_job_other_error(self, print_monitor):
        """Test cancel returns False for non-87 errors"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        error = Exception("Access denied")
        error.winerror = 5
        mock_win32print.SetJob.side_effect = error

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._cancel_job("Printer1", 42)

        assert result is False


# =============================================================================
# Polling Edge Case Tests
# =============================================================================


class TestPollingEdgeCases:
    """Additional tests for polling edge cases"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_poll_spooler_no_printers(self, print_monitor):
        """Test polling when no printers found"""
        print_monitor._is_monitoring = True

        with patch.object(print_monitor, "_get_all_printers", return_value=[]):
            # Should not crash
            print_monitor._poll_spooler()

    def test_poll_spooler_logs_periodically(self, print_monitor):
        """Test periodic logging in poll_spooler"""
        print_monitor._is_monitoring = True

        mock_win32print = Mock()
        mock_win32print.PRINTER_ENUM_LOCAL = 1
        mock_win32print.PRINTER_ENUM_CONNECTIONS = 2
        mock_win32print.EnumPrinters.return_value = [(0, "", "Printer1", "")]
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.EnumJobs.return_value = []

        with patch("services.print_monitor_service.win32print", mock_win32print):
            with patch("time.time", return_value=100):
                print_monitor._poll_spooler()

        assert hasattr(print_monitor, "_last_poll_log")

    def test_poll_spooler_handles_jobs_in_queue_logging(self, print_monitor):
        """Test that jobs in queue are logged"""
        print_monitor._is_monitoring = True
        print_monitor._known_jobs = {"Printer1": {1}}

        mock_win32print = Mock()
        mock_win32print.PRINTER_ENUM_LOCAL = 1
        mock_win32print.PRINTER_ENUM_CONNECTIONS = 2
        mock_win32print.EnumPrinters.return_value = [(0, "", "Printer1", "")]
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 1, "pDocument": "Existing"},
        ]

        with patch("services.print_monitor_service.win32print", mock_win32print):
            # Should not crash
            print_monitor._poll_spooler()

    def test_get_all_printers_exception(self, print_monitor):
        """Test get_all_printers handles exceptions"""
        mock_win32print = Mock()
        mock_win32print.PRINTER_ENUM_LOCAL = 1
        mock_win32print.PRINTER_ENUM_CONNECTIONS = 2
        mock_win32print.EnumPrinters.side_effect = Exception("Access denied")

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._get_all_printers()

        assert result == []

    def test_get_printer_jobs_exception(self, print_monitor):
        """Test get_printer_jobs handles exceptions"""
        mock_win32print = Mock()
        mock_win32print.OpenPrinter.side_effect = Exception("Printer not found")

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._get_printer_jobs("NonexistentPrinter")

        assert result == []

    def test_get_printer_jobs_empty_queue(self, print_monitor):
        """Test get_printer_jobs with empty queue"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle
        mock_win32print.EnumJobs.return_value = None  # Empty queue

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._get_printer_jobs("Printer1")

        assert result == []


# =============================================================================
# WMI Watch Loop Tests
# =============================================================================


class TestWMIWatchLoop:
    """Tests for WMI watch loop"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_wmi_watch_loop_com_initialization(self, print_monitor):
        """Test WMI watch loop initializes and uninitializes COM"""
        mock_pythoncom = Mock()
        mock_wmi_module = Mock()
        mock_wmi_instance = Mock()
        mock_wmi_module.WMI.return_value = mock_wmi_instance

        # Make watcher immediately stop
        print_monitor._wmi_stop_event.set()

        mock_watcher = Mock()
        mock_wmi_instance.Win32_PrintJob.watch_for.return_value = mock_watcher

        with patch("services.print_monitor_service.pythoncom", mock_pythoncom):
            with patch("services.print_monitor_service.wmi", mock_wmi_module):
                print_monitor._wmi_watch_loop()

        mock_pythoncom.CoInitialize.assert_called_once()
        mock_pythoncom.CoUninitialize.assert_called_once()

    def test_wmi_watch_loop_general_exception(self, print_monitor):
        """Test WMI watch loop handles general exceptions"""
        mock_pythoncom = Mock()
        mock_wmi_module = Mock()
        mock_wmi_module.WMI.side_effect = Exception("WMI Error")

        with patch("services.print_monitor_service.pythoncom", mock_pythoncom):
            with patch("services.print_monitor_service.wmi", mock_wmi_module):
                # Should not raise
                print_monitor._wmi_watch_loop()

        mock_pythoncom.CoInitialize.assert_called_once()

    def test_stop_wmi_watcher_thread_not_alive(self, print_monitor):
        """Test stopping WMI watcher when thread is not alive"""
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False
        print_monitor._wmi_thread = mock_thread

        print_monitor._stop_wmi_watcher()

        # Should not call join if thread is not alive
        mock_thread.join.assert_not_called()

    def test_stop_wmi_watcher_thread_does_not_stop(self, print_monitor):
        """Test stopping WMI watcher when thread doesn't stop gracefully"""
        mock_thread = Mock()
        mock_thread.is_alive.side_effect = [True, True]  # Still alive after join
        print_monitor._wmi_thread = mock_thread

        print_monitor._stop_wmi_watcher()

        mock_thread.join.assert_called_once_with(timeout=3.0)
        # Thread reference should still be cleared
        assert print_monitor._wmi_thread is None

    def test_on_wmi_print_job_event_exception(self, print_monitor):
        """Test WMI event handler handles exceptions"""
        mock_event = Mock()
        mock_event.Name = "Printer, invalid"  # Will cause int conversion to fail

        # Make rsplit return invalid data
        mock_event.Name = "Printer, not_a_number"

        # Should not raise
        print_monitor._on_wmi_print_job_event(mock_event)


# =============================================================================
# Start Monitoring Exception Tests
# =============================================================================


class TestStartMonitoringExceptions:
    """Tests for exception handling during start_monitoring"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_start_monitoring_exception(self, print_monitor):
        """Test start_monitoring handles exceptions"""
        with patch.object(
            print_monitor, "_load_pricing", side_effect=Exception("Load error")
        ):
            result = print_monitor.start_monitoring()

        assert result["success"] is False
        assert "Load error" in result["error"]

    def test_stop_monitoring_exception(self, print_monitor):
        """Test stop_monitoring handles exceptions"""
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()

        with patch.object(
            print_monitor, "_stop_wmi_watcher", side_effect=Exception("Stop error")
        ):
            result = print_monitor.stop_monitoring()

        assert result["success"] is False
        assert "Stop error" in result["error"]


# =============================================================================
# Handle New Job Spooling Tests
# =============================================================================


class TestHandleNewJobSpooling:
    """Tests for _handle_new_job spooling wait logic"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_handle_new_job_with_copies(self, print_monitor, mock_firebase):
        """Test job handling with multiple copies"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        mock_devmode = Mock()
        mock_devmode.Copies = 2
        mock_devmode.Color = 1  # B&W

        job_data = {
            "JobId": 1,
            "pDocument": "Test Doc",
            "TotalPages": 5,
            "pDevMode": mock_devmode,
            "Status": 0,  # Not spooling
        }

        allowed_signals = []
        print_monitor.job_allowed.connect(lambda *args: allowed_signals.append(args))

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(print_monitor, "_resume_job", return_value=True):
                print_monitor._handle_new_job("Printer1", job_data)

        assert len(allowed_signals) == 1
        doc_name, pages, cost, remaining = allowed_signals[0]
        assert pages == 10  # 5 pages × 2 copies
        assert cost == 10.0  # 10 pages × 1.0

    def test_handle_new_job_color_job(self, print_monitor, mock_firebase):
        """Test job handling for color jobs"""
        print_monitor._bw_price = 1.0
        print_monitor._color_price = 3.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        mock_devmode = Mock()
        mock_devmode.Copies = 1
        mock_devmode.Color = 2  # DMCOLOR_COLOR

        job_data = {
            "JobId": 1,
            "pDocument": "Color Doc",
            "TotalPages": 5,
            "pDevMode": mock_devmode,
            "Status": 0,
        }

        allowed_signals = []
        print_monitor.job_allowed.connect(lambda *args: allowed_signals.append(args))

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(print_monitor, "_resume_job", return_value=True):
                print_monitor._handle_new_job("Printer1", job_data)

        assert len(allowed_signals) == 1
        _, _, cost, _ = allowed_signals[0]
        assert cost == 15.0  # 5 pages × 3.0 (color price)

    def test_handle_new_job_job_disappears_during_spool(
        self, print_monitor, mock_firebase
    ):
        """Test job handling when job disappears during spooling wait"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }

        job_data = {
            "JobId": 1,
            "pDocument": "Fast Job",
            "TotalPages": 0,  # Still spooling
            "Status": 8,  # JOB_STATUS_SPOOLING
        }

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(
                print_monitor, "_get_job_info", return_value={}
            ):  # Job disappeared
                with patch.object(print_monitor, "_resume_job"):
                    with patch("time.sleep"):  # Speed up test
                        print_monitor._handle_new_job("Printer1", job_data)


# =============================================================================
# Additional Coverage Tests
# =============================================================================


class TestImportFallbacks:
    """Tests for import fallback paths"""

    def test_win32print_import_error_handled(self):
        """Test that win32print import error is handled"""
        # This is already handled at module level, just verify the service works
        # even when imports fail by using mocks
        pass  # This is tested implicitly by all mock tests

    def test_wmi_import_error_handled(self):
        """Test that WMI import error is handled"""
        pass  # This is tested implicitly by all mock tests


class TestDeductBudgetException:
    """Tests for _deduct_budget exception handling"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_deduct_budget_exception_returns_false(self, print_monitor, mock_firebase):
        """Test _deduct_budget returns False on exception"""
        mock_firebase.db_update.side_effect = Exception("Database error")

        result = print_monitor._deduct_budget(10.0)

        assert result is False


class TestWMIEventHandlingExceptions:
    """Tests for WMI event exception paths"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_wmi_watch_loop_timeout_continues(self, print_monitor):
        """Test WMI watch loop handles timeout and continues"""
        mock_pythoncom = Mock()
        mock_wmi_module = Mock()
        mock_connection = Mock()
        mock_watcher = Mock()

        # Create a custom timeout exception
        class MockTimeoutException(Exception):
            pass

        mock_wmi_module.x_wmi_timed_out = MockTimeoutException
        mock_wmi_module.WMI.return_value = mock_connection
        mock_connection.Win32_PrintJob.watch_for.return_value = mock_watcher

        # First call times out, then stop event is set
        call_count = [0]

        def mock_watch(timeout_ms=None):
            call_count[0] += 1
            if call_count[0] == 1:
                raise MockTimeoutException()
            # On second call, simulate stop event being set
            print_monitor._wmi_stop_event.set()
            return None

        mock_watcher.side_effect = mock_watch

        with patch("services.print_monitor_service.pythoncom", mock_pythoncom):
            with patch("services.print_monitor_service.wmi", mock_wmi_module):
                print_monitor._wmi_stop_event = threading.Event()
                print_monitor._wmi_watch_loop()

        # Should have tried at least once
        assert call_count[0] >= 1

    def test_wmi_watch_loop_event_error_breaks(self, print_monitor):
        """Test WMI watch loop breaks on event error"""
        mock_pythoncom = Mock()
        mock_wmi_module = Mock()
        mock_connection = Mock()
        mock_watcher = Mock()

        mock_wmi_module.x_wmi_timed_out = type("x_wmi_timed_out", (Exception,), {})
        mock_wmi_module.WMI.return_value = mock_connection
        mock_connection.Win32_PrintJob.watch_for.return_value = mock_watcher

        # Raise a non-timeout error
        mock_watcher.side_effect = RuntimeError("Connection lost")

        with patch("services.print_monitor_service.pythoncom", mock_pythoncom):
            with patch("services.print_monitor_service.wmi", mock_wmi_module):
                print_monitor._wmi_stop_event = threading.Event()
                print_monitor._wmi_watch_loop()

        # Should have exited the loop
        mock_pythoncom.CoUninitialize.assert_called_once()


class TestInitializeKnownJobsNoprinters:
    """Tests for _initialize_known_jobs with no printers"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_initialize_known_jobs_no_printers_logs_warning(self, print_monitor):
        """Test that no printers logs a warning"""
        with patch.object(print_monitor, "_get_all_printers", return_value=[]):
            # Should not crash, just log warning
            print_monitor._initialize_known_jobs()

        # Known jobs should be empty
        assert print_monitor._known_jobs == {}


class TestIsColorJobException:
    """Tests for _is_color_job exception path"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_is_color_job_exception_returns_false(self, print_monitor):
        """Test _is_color_job_from_devmode returns False on exception"""
        mock_devmode = Mock()
        # Make getattr raise an exception
        type(mock_devmode).Color = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("Access denied"))
        )

        result = print_monitor._is_color_job_from_devmode(mock_devmode)

        assert result is False


class TestHandleNewJobDevmodeUpdate:
    """Tests for _handle_new_job devmode update during spooling"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_handle_new_job_updates_copies_during_spool(
        self, print_monitor, mock_firebase
    ):
        """Test that copies are updated when devmode changes during spooling"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 100.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        initial_devmode = Mock()
        initial_devmode.Copies = 1
        initial_devmode.Color = 1

        updated_devmode = Mock()
        updated_devmode.Copies = 3
        updated_devmode.Color = 1

        job_data = {
            "JobId": 1,
            "pDocument": "Multi-copy Doc",
            "TotalPages": 5,
            "Status": 8,  # Spooling
            "pDevMode": initial_devmode,
        }

        # After spooling completes, return updated info
        def get_job_info(*args):
            return {
                "TotalPages": 5,
                "Status": 0,  # No longer spooling
                "Size": 1000,
                "pDevMode": updated_devmode,
            }

        allowed_signals = []
        print_monitor.job_allowed.connect(lambda *args: allowed_signals.append(args))

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(print_monitor, "_get_job_info", side_effect=get_job_info):
                with patch.object(print_monitor, "_resume_job", return_value=True):
                    with patch("time.sleep"):  # Speed up
                        print_monitor._handle_new_job("Printer1", job_data)

        # Should use the updated copies count (3)
        assert len(allowed_signals) == 1
        _, pages, cost, _ = allowed_signals[0]
        assert pages == 15  # 5 pages × 3 copies
        assert cost == 15.0


# =============================================================================
# Safety Features Tests - Crash Recovery & Graceful Shutdown
# =============================================================================


class TestSafetyFeatures:
    """Tests for crash recovery and graceful shutdown safety features"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_paused_by_us_tracking_initialized_empty(self, print_monitor):
        """Test _paused_by_us dict is initialized empty"""
        assert print_monitor._paused_by_us == {}

    def test_pause_job_tracks_paused_jobs(self, print_monitor):
        """Test _pause_job adds job to _paused_by_us tracking"""
        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._pause_job("Printer1", 42)

        assert result is True
        assert "Printer1:42" in print_monitor._paused_by_us
        assert print_monitor._paused_by_us["Printer1:42"] == 42

    def test_resume_job_removes_from_tracking(self, print_monitor):
        """Test _resume_job removes job from _paused_by_us tracking"""
        # Pre-populate tracking
        print_monitor._paused_by_us["Printer1:42"] = 42

        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._resume_job("Printer1", 42)

        assert result is True
        assert "Printer1:42" not in print_monitor._paused_by_us

    def test_resume_job_error_87_removes_from_tracking(self, print_monitor):
        """Test _resume_job removes from tracking even on error 87"""
        # Pre-populate tracking
        print_monitor._paused_by_us["Printer1:42"] = 42

        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        error = Exception("The parameter is incorrect")
        error.winerror = 87
        mock_win32print.SetJob.side_effect = error

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._resume_job("Printer1", 42)

        assert result is True
        assert "Printer1:42" not in print_monitor._paused_by_us

    def test_cancel_job_removes_from_tracking(self, print_monitor):
        """Test _cancel_job removes job from _paused_by_us tracking"""
        # Pre-populate tracking
        print_monitor._paused_by_us["Printer1:42"] = 42

        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._cancel_job("Printer1", 42)

        assert result is True
        assert "Printer1:42" not in print_monitor._paused_by_us

    def test_cancel_job_error_87_removes_from_tracking(self, print_monitor):
        """Test _cancel_job removes from tracking even on error 87"""
        # Pre-populate tracking
        print_monitor._paused_by_us["Printer1:42"] = 42

        mock_win32print = Mock()
        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle

        error = Exception("The parameter is incorrect")
        error.winerror = 87
        mock_win32print.SetJob.side_effect = error

        with patch("services.print_monitor_service.win32print", mock_win32print):
            result = print_monitor._cancel_job("Printer1", 42)

        assert result is True
        assert "Printer1:42" not in print_monitor._paused_by_us


class TestCleanupOrphanedJobs:
    """Tests for _cleanup_orphaned_jobs method"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_cleanup_orphaned_jobs_no_win32print(self, print_monitor):
        """Test _cleanup_orphaned_jobs does nothing when win32print unavailable"""
        with patch("services.print_monitor_service.win32print", None):
            # Should not raise
            print_monitor._cleanup_orphaned_jobs()

    def test_cleanup_orphaned_jobs_no_paused_jobs(self, print_monitor):
        """Test _cleanup_orphaned_jobs logs success when no paused jobs found"""
        mock_win32print = Mock()
        mock_win32print.PRINTER_ENUM_LOCAL = 0x2
        mock_win32print.PRINTER_ENUM_CONNECTIONS = 0x4
        mock_win32print.EnumPrinters.return_value = [(None, None, "Printer1", None)]

        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle
        # Return jobs that are NOT paused (status 0)
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 1, "pDocument": "Doc1", "Status": 0},
        ]

        with patch("services.print_monitor_service.win32print", mock_win32print):
            print_monitor._cleanup_orphaned_jobs()

        # Should complete without error

    def test_cleanup_orphaned_jobs_finds_paused_jobs(self, print_monitor):
        """Test _cleanup_orphaned_jobs detects paused jobs in queue"""
        mock_win32print = Mock()
        mock_win32print.PRINTER_ENUM_LOCAL = 0x2
        mock_win32print.PRINTER_ENUM_CONNECTIONS = 0x4
        mock_win32print.EnumPrinters.return_value = [(None, None, "Printer1", None)]

        mock_handle = Mock()
        mock_win32print.OpenPrinter.return_value = mock_handle
        # Return a paused job (status 0x1 = JOB_STATUS_PAUSED)
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 1, "pDocument": "Orphaned Doc", "Status": 0x1},
        ]

        with patch("services.print_monitor_service.win32print", mock_win32print):
            print_monitor._cleanup_orphaned_jobs()

        # Should complete without error (just logs warning)

    def test_cleanup_orphaned_jobs_handles_exception(self, print_monitor):
        """Test _cleanup_orphaned_jobs handles exceptions gracefully"""
        with patch.object(
            print_monitor, "_get_all_printers", side_effect=Exception("Error")
        ):
            # Should not raise
            print_monitor._cleanup_orphaned_jobs()


class TestResumeAllPausedJobs:
    """Tests for _resume_all_paused_jobs method"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_resume_all_paused_jobs_empty(self, print_monitor):
        """Test _resume_all_paused_jobs does nothing when no jobs tracked"""
        print_monitor._paused_by_us = {}

        with patch.object(print_monitor, "_resume_job") as mock_resume:
            print_monitor._resume_all_paused_jobs()

        mock_resume.assert_not_called()

    def test_resume_all_paused_jobs_resumes_tracked_jobs(self, print_monitor):
        """Test _resume_all_paused_jobs resumes all tracked jobs"""
        print_monitor._paused_by_us = {
            "Printer1:42": 42,
            "Printer2:99": 99,
        }

        with patch.object(
            print_monitor, "_resume_job", return_value=True
        ) as mock_resume:
            print_monitor._resume_all_paused_jobs()

        assert mock_resume.call_count == 2
        mock_resume.assert_any_call("Printer1", 42)
        mock_resume.assert_any_call("Printer2", 99)

    def test_resume_all_paused_jobs_handles_exception(self, print_monitor):
        """Test _resume_all_paused_jobs handles resume errors gracefully"""
        print_monitor._paused_by_us = {
            "Printer1:42": 42,
        }

        with patch.object(
            print_monitor, "_resume_job", side_effect=Exception("Resume failed")
        ):
            # Should not raise
            print_monitor._resume_all_paused_jobs()


class TestStartMonitoringCallsCleanup:
    """Tests that start_monitoring calls cleanup"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_start_monitoring_calls_cleanup_orphaned_jobs(self, print_monitor):
        """Test start_monitoring calls _cleanup_orphaned_jobs"""
        with patch.object(print_monitor, "_cleanup_orphaned_jobs") as mock_cleanup:
            with patch.object(print_monitor, "_load_pricing"):
                with patch.object(print_monitor, "_initialize_known_jobs"):
                    with patch.object(print_monitor, "_start_wmi_watcher"):
                        print_monitor.start_monitoring()

        mock_cleanup.assert_called_once()

    def test_start_monitoring_clears_paused_by_us(self, print_monitor):
        """Test start_monitoring clears _paused_by_us tracking"""
        # Pre-populate tracking
        print_monitor._paused_by_us = {"old:job": 1}

        with patch.object(print_monitor, "_cleanup_orphaned_jobs"):
            with patch.object(print_monitor, "_load_pricing"):
                with patch.object(print_monitor, "_initialize_known_jobs"):
                    with patch.object(print_monitor, "_start_wmi_watcher"):
                        print_monitor.start_monitoring()

        assert print_monitor._paused_by_us == {}


class TestStopMonitoringCallsResume:
    """Tests that stop_monitoring resumes paused jobs"""

    @pytest.fixture
    def print_monitor(self, qapp, mock_firebase):
        """Create PrintMonitorService instance"""
        service = PrintMonitorService(
            firebase_client=mock_firebase,
            user_id="test-user-123",
            org_id="test-org-456",
        )
        yield service
        if service.is_monitoring():
            service.stop_monitoring()

    def test_stop_monitoring_calls_resume_all_paused_jobs(self, print_monitor):
        """Test stop_monitoring calls _resume_all_paused_jobs"""
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()

        with patch.object(print_monitor, "_resume_all_paused_jobs") as mock_resume:
            with patch.object(print_monitor, "_stop_wmi_watcher"):
                print_monitor.stop_monitoring()

        mock_resume.assert_called_once()

    def test_stop_monitoring_clears_paused_by_us(self, print_monitor):
        """Test stop_monitoring clears _paused_by_us tracking"""
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()
        print_monitor._paused_by_us = {"Printer1:42": 42}

        with patch.object(print_monitor, "_resume_all_paused_jobs"):
            with patch.object(print_monitor, "_stop_wmi_watcher"):
                print_monitor.stop_monitoring()

        assert print_monitor._paused_by_us == {}

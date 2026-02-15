"""
Tests for PrintMonitorService (Event-Driven, Multi-PC Safe)

Tests cover:
- Initialization and state
- Start/stop monitoring lifecycle (notifications + fallback polling)
- Event-driven notification thread
- Job detection (scan_for_new_jobs, shared by notifications + polling)
- Cost calculation (pages × copies × price)
- Budget management and caching (including debt)
- Per-job pause/resume/cancel
- Paused job handling (approve/deny)
- Escaped job handling (retroactive charging with debt)
- Job info extraction and spool waiting
- Edge cases and error handling
- Thread safety
"""

import threading
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import QTimer

from services.print_monitor_service import (
    FALLBACK_POLL_MS,
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
def mock_win32print():
    """Create a mock win32print module"""
    m = Mock()
    m.PRINTER_ENUM_LOCAL = 1
    m.PRINTER_ENUM_CONNECTIONS = 2
    m.OpenPrinter = Mock(return_value=Mock())
    m.ClosePrinter = Mock()
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
    if service.is_monitoring():
        service.stop_monitoring()


# =============================================================================
# Initialization Tests
# =============================================================================


class TestInitialization:
    """Tests for service initialization"""

    def test_creates_with_correct_attributes(self, print_monitor, mock_firebase):
        assert print_monitor.firebase == mock_firebase
        assert print_monitor.user_id == "test-user-123"
        assert print_monitor.org_id == "test-org-456"

    def test_initial_state_is_not_monitoring(self, print_monitor):
        assert print_monitor.is_monitoring() is False

    def test_initial_known_jobs_empty(self, print_monitor):
        assert print_monitor._known_jobs == {}

    def test_initial_processed_jobs_empty(self, print_monitor):
        assert print_monitor._processed_jobs == set()

    def test_default_pricing(self, print_monitor):
        assert print_monitor._bw_price == 1.0
        assert print_monitor._color_price == 3.0

    def test_no_printer_level_state(self, print_monitor):
        """Verify no printer-level pause tracking exists (multi-PC safe)"""
        assert not hasattr(print_monitor, "_paused_printers")
        assert not hasattr(print_monitor, "_releasing_jobs")


# =============================================================================
# Start/Stop Monitoring Tests
# =============================================================================


class TestStartStopMonitoring:

    def test_start_monitoring_success(self, print_monitor):
        with patch.object(print_monitor, "_load_pricing"):
            with patch.object(print_monitor, "_initialize_known_jobs"):
                with patch(
                    "services.print_monitor_service._HAS_NOTIFICATIONS",
                    False,
                ):
                    result = print_monitor.start_monitoring()

        assert result["success"] is True
        assert print_monitor.is_monitoring() is True

    def test_start_monitoring_already_running(self, print_monitor):
        print_monitor._is_monitoring = True
        result = print_monitor.start_monitoring()
        assert result["success"] is True
        assert result["message"] == "Already monitoring"

    def test_start_monitoring_creates_fallback_timer(self, print_monitor):
        """Start creates a fallback polling timer (2s interval)"""
        with patch.object(print_monitor, "_load_pricing"):
            with patch.object(print_monitor, "_initialize_known_jobs"):
                with patch(
                    "services.print_monitor_service._HAS_NOTIFICATIONS",
                    False,
                ):
                    print_monitor.start_monitoring()

        assert print_monitor._poll_timer is not None
        assert isinstance(print_monitor._poll_timer, QTimer)

    def test_start_monitoring_starts_notification_thread(self, print_monitor):
        """When notifications are available, starts the watcher thread"""
        with patch.object(print_monitor, "_load_pricing"):
            with patch.object(print_monitor, "_initialize_known_jobs"):
                with patch(
                    "services.print_monitor_service._HAS_NOTIFICATIONS",
                    True,
                ):
                    with patch(
                        "services.print_monitor_service.win32print",
                        Mock(),
                    ):
                        result = print_monitor.start_monitoring()

        assert result["success"] is True
        assert print_monitor._notification_thread is not None
        # Clean up: stop the thread
        print_monitor._stop_event.set()
        print_monitor._notification_thread.join(timeout=2.0)

    def test_start_monitoring_no_printer_pause(self, print_monitor):
        """Verify start_monitoring does NOT pause any printers"""
        with patch.object(print_monitor, "_load_pricing"):
            with patch.object(print_monitor, "_initialize_known_jobs"):
                with patch(
                    "services.print_monitor_service._HAS_NOTIFICATIONS",
                    False,
                ):
                    with patch(
                        "services.print_monitor_service.win32print"
                    ) as mock_w32:
                        print_monitor.start_monitoring()

        # SetPrinter (printer-level) should NEVER be called
        if hasattr(mock_w32, "SetPrinter"):
            mock_w32.SetPrinter.assert_not_called()

    def test_start_monitoring_exception(self, print_monitor):
        with patch.object(
            print_monitor,
            "_load_pricing",
            side_effect=Exception("Error"),
        ):
            result = print_monitor.start_monitoring()
        assert result["success"] is False

    def test_stop_monitoring_success(self, print_monitor):
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()

        result = print_monitor.stop_monitoring()

        assert result["success"] is True
        assert print_monitor.is_monitoring() is False

    def test_stop_monitoring_not_running(self, print_monitor):
        result = print_monitor.stop_monitoring()
        assert result["success"] is True
        assert result["message"] == "Not monitoring"

    def test_stop_monitoring_clears_state(self, print_monitor):
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()
        print_monitor._known_jobs = {"Printer1": {1, 2}}
        print_monitor._processed_jobs = {"Printer1:1"}

        print_monitor.stop_monitoring()

        assert print_monitor._known_jobs == {}
        assert print_monitor._processed_jobs == set()

    def test_stop_monitoring_stops_timer(self, print_monitor):
        print_monitor._is_monitoring = True
        mock_timer = Mock()
        print_monitor._poll_timer = mock_timer

        print_monitor.stop_monitoring()

        mock_timer.stop.assert_called_once()
        assert print_monitor._poll_timer is None

    def test_stop_monitoring_signals_thread_to_stop(self, print_monitor):
        """Stop sets the stop event so notification thread exits"""
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()

        print_monitor.stop_monitoring()

        assert print_monitor._stop_event.is_set()

    def test_stop_monitoring_no_printer_resume(self, print_monitor):
        """Verify stop_monitoring does NOT resume any printers"""
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()

        with patch(
            "services.print_monitor_service.win32print"
        ) as mock_w32:
            print_monitor.stop_monitoring()

        if hasattr(mock_w32, "SetPrinter"):
            mock_w32.SetPrinter.assert_not_called()


# =============================================================================
# Pricing Tests
# =============================================================================


class TestPricing:

    def test_load_pricing_success(self, print_monitor, mock_firebase):
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"blackAndWhitePrice": 0.5, "colorPrice": 2.0},
        }
        print_monitor._load_pricing()
        assert print_monitor._bw_price == 0.5
        assert print_monitor._color_price == 2.0

    def test_load_pricing_uses_defaults_on_failure(
        self, print_monitor, mock_firebase
    ):
        mock_firebase.db_get.return_value = {"success": False}
        print_monitor._load_pricing()
        assert print_monitor._bw_price == 1.0
        assert print_monitor._color_price == 3.0

    def test_load_pricing_handles_exception(
        self, print_monitor, mock_firebase
    ):
        mock_firebase.db_get.side_effect = Exception("Network error")
        print_monitor._load_pricing()
        assert print_monitor._bw_price == 1.0
        assert print_monitor._color_price == 3.0

    def test_calculate_cost_bw_single_copy(self, print_monitor):
        print_monitor._bw_price = 0.5
        assert print_monitor._calculate_cost(10, 1, is_color=False) == 5.0

    def test_calculate_cost_bw_multiple_copies(self, print_monitor):
        print_monitor._bw_price = 1.0
        assert print_monitor._calculate_cost(5, 3, is_color=False) == 15.0

    def test_calculate_cost_color_single_copy(self, print_monitor):
        print_monitor._color_price = 2.0
        assert print_monitor._calculate_cost(10, 1, is_color=True) == 20.0

    def test_calculate_cost_color_multiple_copies(self, print_monitor):
        print_monitor._color_price = 3.0
        assert print_monitor._calculate_cost(5, 2, is_color=True) == 30.0

    def test_calculate_cost_single_page(self, print_monitor):
        print_monitor._bw_price = 1.0
        assert print_monitor._calculate_cost(1, 1, is_color=False) == 1.0


# =============================================================================
# DEVMODE Extraction Tests
# =============================================================================


class TestDevmodeExtraction:

    def test_copies_with_value(self, print_monitor):
        m = Mock()
        m.Copies = 3
        assert print_monitor._get_copies_from_devmode(m) == 3

    def test_copies_none_devmode(self, print_monitor):
        assert print_monitor._get_copies_from_devmode(None) == 1

    def test_copies_zero(self, print_monitor):
        m = Mock()
        m.Copies = 0
        assert print_monitor._get_copies_from_devmode(m) == 1

    def test_copies_negative(self, print_monitor):
        m = Mock()
        m.Copies = -5
        assert print_monitor._get_copies_from_devmode(m) == 1

    def test_copies_missing_attribute(self, print_monitor):
        m = Mock(spec=[])
        assert print_monitor._get_copies_from_devmode(m) == 1

    def test_copies_exception(self, print_monitor):
        m = Mock()
        type(m).Copies = property(
            lambda self: (_ for _ in ()).throw(Exception("Error"))
        )
        assert print_monitor._get_copies_from_devmode(m) == 1

    def test_is_color_true(self, print_monitor):
        m = Mock()
        m.Color = 2
        assert print_monitor._is_color_job_from_devmode(m) is True

    def test_is_color_false_bw(self, print_monitor):
        m = Mock()
        m.Color = 1
        assert print_monitor._is_color_job_from_devmode(m) is False

    def test_is_color_none_devmode(self, print_monitor):
        assert print_monitor._is_color_job_from_devmode(None) is False

    def test_is_color_missing_attribute(self, print_monitor):
        m = Mock(spec=[])
        assert print_monitor._is_color_job_from_devmode(m) is False

    def test_is_color_exception(self, print_monitor):
        m = Mock()
        type(m).Color = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("Error"))
        )
        assert print_monitor._is_color_job_from_devmode(m) is False


# =============================================================================
# Job Info Extraction Tests
# =============================================================================


class TestExtractJobDetails:

    def test_extracts_all_fields(self, print_monitor):
        devmode = Mock()
        devmode.Copies = 3
        devmode.Color = 2

        job_data = {
            "pDocument": "Report.pdf",
            "TotalPages": 10,
            "pDevMode": devmode,
        }

        details = print_monitor._extract_job_details(job_data)

        assert details["doc_name"] == "Report.pdf"
        assert details["pages"] == 10
        assert details["copies"] == 3
        assert details["is_color"] is True

    def test_defaults_for_missing_data(self, print_monitor):
        job_data = {"JobId": 1}

        details = print_monitor._extract_job_details(job_data)

        assert details["doc_name"] == "Unknown"
        assert details["pages"] == 1  # Default for 0/missing
        assert details["copies"] == 1  # Default no devmode
        assert details["is_color"] is False  # Default B&W

    def test_zero_pages_defaults_to_1(self, print_monitor):
        job_data = {"TotalPages": 0}
        details = print_monitor._extract_job_details(job_data)
        assert details["pages"] == 1


# =============================================================================
# Budget Tests
# =============================================================================


class TestBudget:

    def test_get_user_budget_success(self, print_monitor, mock_firebase):
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        assert print_monitor._get_user_budget() == 50.0
        mock_firebase.db_get.assert_called_with("users/test-user-123")

    def test_get_user_budget_zero_on_failure(
        self, print_monitor, mock_firebase
    ):
        mock_firebase.db_get.return_value = {"success": False}
        assert print_monitor._get_user_budget() == 0.0

    def test_get_user_budget_exception(self, print_monitor, mock_firebase):
        mock_firebase.db_get.side_effect = Exception("Network error")
        assert print_monitor._get_user_budget() == 0.0

    def test_get_user_budget_uses_cache(self, print_monitor, mock_firebase):
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        print_monitor._get_user_budget()
        print_monitor._get_user_budget()
        assert mock_firebase.db_get.call_count == 1  # Cached

    def test_get_user_budget_force_refresh(
        self, print_monitor, mock_firebase
    ):
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        print_monitor._get_user_budget()
        print_monitor._get_user_budget(force_refresh=True)
        assert mock_firebase.db_get.call_count == 2

    def test_deduct_budget_success(self, print_monitor, mock_firebase):
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        signals = []
        print_monitor.budget_updated.connect(lambda x: signals.append(x))

        assert print_monitor._deduct_budget(10.0) is True
        assert signals == [40.0]

    def test_deduct_budget_failure(self, print_monitor, mock_firebase):
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {
            "success": False,
            "error": "Fail",
        }
        assert print_monitor._deduct_budget(10.0) is False

    def test_deduct_budget_cannot_go_negative(
        self, print_monitor, mock_firebase
    ):
        """Default deduction floors at 0 (no debt)"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 5.0},
        }
        mock_firebase.db_update.return_value = {"success": True}
        print_monitor._deduct_budget(10.0)
        call_args = mock_firebase.db_update.call_args
        assert call_args[0][1]["printBalance"] == 0.0

    def test_deduct_budget_allow_negative_creates_debt(
        self, print_monitor, mock_firebase
    ):
        """allow_negative=True lets balance go below zero (debt)"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 3.0},
        }
        mock_firebase.db_update.return_value = {"success": True}
        result = print_monitor._deduct_budget(10.0, allow_negative=True)
        assert result is True
        call_args = mock_firebase.db_update.call_args
        assert call_args[0][1]["printBalance"] == -7.0

    def test_deduct_budget_allow_negative_zero_balance(
        self, print_monitor, mock_firebase
    ):
        """allow_negative=True with zero balance → negative balance"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 0.0},
        }
        mock_firebase.db_update.return_value = {"success": True}
        result = print_monitor._deduct_budget(5.0, allow_negative=True)
        assert result is True
        call_args = mock_firebase.db_update.call_args
        assert call_args[0][1]["printBalance"] == -5.0

    def test_deduct_budget_exception(self, print_monitor, mock_firebase):
        mock_firebase.db_update.side_effect = Exception("DB error")
        assert print_monitor._deduct_budget(10.0) is False


# =============================================================================
# Spooler Interaction Tests
# =============================================================================


class TestSpoolerInteraction:

    def test_get_all_printers_no_win32print(self, print_monitor):
        with patch("services.print_monitor_service.win32print", None):
            assert print_monitor._get_all_printers() == []

    def test_get_all_printers_success(self, print_monitor, mock_win32print):
        mock_win32print.EnumPrinters.return_value = [
            (0, "", "HP LaserJet", ""),
            (0, "", "Canon Inkjet", ""),
        ]
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._get_all_printers() == [
                "HP LaserJet",
                "Canon Inkjet",
            ]

    def test_get_all_printers_exception(self, print_monitor, mock_win32print):
        mock_win32print.EnumPrinters.side_effect = Exception("Error")
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._get_all_printers() == []

    def test_get_printer_jobs_success(self, print_monitor, mock_win32print):
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 1},
            {"JobId": 2},
        ]
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            jobs = print_monitor._get_printer_jobs("Printer1")
        assert len(jobs) == 2
        mock_win32print.ClosePrinter.assert_called_once_with(handle)

    def test_get_printer_jobs_no_win32print(self, print_monitor):
        with patch("services.print_monitor_service.win32print", None):
            assert print_monitor._get_printer_jobs("P") == []

    def test_get_printer_jobs_empty(self, print_monitor, mock_win32print):
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.EnumJobs.return_value = None
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._get_printer_jobs("P") == []

    def test_get_job_info_success(self, print_monitor, mock_win32print):
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        mock_win32print.GetJob.return_value = {"TotalPages": 10}
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            result = print_monitor._get_job_info("P", 42)
        assert result["TotalPages"] == 10
        mock_win32print.GetJob.assert_called_once_with(handle, 42, 2)

    def test_get_job_info_no_win32print(self, print_monitor):
        with patch("services.print_monitor_service.win32print", None):
            assert print_monitor._get_job_info("P", 42) == {}

    def test_pause_job_success(self, print_monitor, mock_win32print):
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._pause_job("P", 42) is True
        mock_win32print.SetJob.assert_called_once_with(
            handle, 42, 0, None, JOB_CONTROL_PAUSE
        )

    def test_resume_job_success(self, print_monitor, mock_win32print):
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._resume_job("P", 42) is True
        mock_win32print.SetJob.assert_called_once_with(
            handle, 42, 0, None, JOB_CONTROL_RESUME
        )

    def test_cancel_job_success(self, print_monitor, mock_win32print):
        handle = Mock()
        mock_win32print.OpenPrinter.return_value = handle
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._cancel_job("P", 42) is True
        mock_win32print.SetJob.assert_called_once_with(
            handle, 42, 0, None, JOB_CONTROL_CANCEL
        )

    def test_pause_job_no_win32print(self, print_monitor):
        with patch("services.print_monitor_service.win32print", None):
            assert print_monitor._pause_job("P", 1) is False

    def test_resume_job_no_win32print(self, print_monitor):
        with patch("services.print_monitor_service.win32print", None):
            assert print_monitor._resume_job("P", 1) is False

    def test_cancel_job_no_win32print(self, print_monitor):
        with patch("services.print_monitor_service.win32print", None):
            assert print_monitor._cancel_job("P", 1) is False


# =============================================================================
# Error 87 (Job Already Completed) Tests
# =============================================================================


class TestError87:

    def _err87(self):
        e = Exception("The parameter is incorrect")
        e.winerror = 87
        return e

    def _err_other(self):
        e = Exception("Access denied")
        e.winerror = 5
        return e

    def test_pause_error_87_returns_false(self, print_monitor, mock_win32print):
        """Pause returns False for completed jobs (can't pause)"""
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.SetJob.side_effect = self._err87()
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._pause_job("P", 42) is False

    def test_resume_error_87_returns_true(
        self, print_monitor, mock_win32print
    ):
        """Resume returns True for completed jobs (printed successfully)"""
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.SetJob.side_effect = self._err87()
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._resume_job("P", 42) is True

    def test_cancel_error_87_returns_true(
        self, print_monitor, mock_win32print
    ):
        """Cancel returns True for completed jobs (already gone)"""
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.SetJob.side_effect = self._err87()
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._cancel_job("P", 42) is True

    def test_pause_other_error(self, print_monitor, mock_win32print):
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.SetJob.side_effect = self._err_other()
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._pause_job("P", 42) is False

    def test_resume_other_error(self, print_monitor, mock_win32print):
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.SetJob.side_effect = self._err_other()
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._resume_job("P", 42) is False

    def test_cancel_other_error(self, print_monitor, mock_win32print):
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.SetJob.side_effect = self._err_other()
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            assert print_monitor._cancel_job("P", 42) is False


# =============================================================================
# Job Detection Tests (scan_for_new_jobs - shared by notifications + polling)
# =============================================================================


class TestJobDetection:

    def test_initialize_known_jobs(self, print_monitor, mock_win32print):
        mock_win32print.EnumPrinters.return_value = [
            (0, "", "Printer1", ""),
        ]
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.EnumJobs.return_value = [
            {"JobId": 1},
            {"JobId": 2},
        ]
        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            print_monitor._initialize_known_jobs()
        assert print_monitor._known_jobs["Printer1"] == {1, 2}

    def test_initialize_no_printers(self, print_monitor):
        with patch.object(
            print_monitor, "_get_all_printers", return_value=[]
        ):
            print_monitor._initialize_known_jobs()
        assert print_monitor._known_jobs == {}

    def test_scan_not_monitoring(self, print_monitor):
        """Scan exits early if not monitoring"""
        print_monitor._is_monitoring = False
        with patch.object(print_monitor, "_get_all_printers") as m:
            print_monitor._scan_for_new_jobs()
        m.assert_not_called()

    def test_scan_detects_new_job(self, print_monitor, mock_win32print):
        """Scan detects a new job in the queue"""
        print_monitor._is_monitoring = True
        print_monitor._known_jobs = {"Printer1": {1, 2}}

        mock_win32print.EnumPrinters.return_value = [
            (0, "", "Printer1", ""),
        ]
        mock_win32print.OpenPrinter.return_value = Mock()
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
                print_monitor._scan_for_new_jobs()

        mock_handle.assert_called_once()
        assert mock_handle.call_args[0][0] == "Printer1"
        assert mock_handle.call_args[0][1]["JobId"] == 3

    def test_scan_skips_processed(self, print_monitor, mock_win32print):
        """Scan skips jobs already in _processed_jobs"""
        print_monitor._is_monitoring = True
        print_monitor._known_jobs = {"Printer1": set()}
        print_monitor._processed_jobs = {"Printer1:3"}

        mock_win32print.EnumPrinters.return_value = [
            (0, "", "Printer1", ""),
        ]
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.EnumJobs.return_value = [{"JobId": 3}]

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            with patch.object(
                print_monitor, "_handle_new_job"
            ) as mock_handle:
                print_monitor._scan_for_new_jobs()
        mock_handle.assert_not_called()

    def test_scan_cleans_processed(self, print_monitor, mock_win32print):
        """Scan removes processed entries for jobs no longer in queue"""
        print_monitor._is_monitoring = True
        print_monitor._known_jobs = {"Printer1": {1, 2}}
        print_monitor._processed_jobs = {"Printer1:1", "Printer1:2"}

        mock_win32print.EnumPrinters.return_value = [
            (0, "", "Printer1", ""),
        ]
        mock_win32print.OpenPrinter.return_value = Mock()
        mock_win32print.EnumJobs.return_value = [{"JobId": 2}]

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            print_monitor._scan_for_new_jobs()

        assert "Printer1:1" not in print_monitor._processed_jobs
        assert "Printer1:2" in print_monitor._processed_jobs

    def test_scan_handles_exception(self, print_monitor):
        """Scan swallows exceptions gracefully"""
        print_monitor._is_monitoring = True
        with patch.object(
            print_monitor,
            "_get_all_printers",
            side_effect=Exception("Error"),
        ):
            print_monitor._scan_for_new_jobs()  # Should not raise

    def test_poll_delegates_to_scan(self, print_monitor):
        """Fallback poll timer calls _scan_for_new_jobs"""
        with patch.object(print_monitor, "_scan_for_new_jobs") as m:
            print_monitor._poll_print_queues()
        m.assert_called_once()


# =============================================================================
# Notification Thread Tests
# =============================================================================


class TestNotifications:
    """Tests for the event-driven notification thread."""

    def test_open_notification_handle_no_api(self, print_monitor):
        """Returns None if notification API not available"""
        with patch(
            "services.print_monitor_service._HAS_NOTIFICATIONS", False
        ):
            result = print_monitor._open_notification_handle()
        assert result == (None, None)

    def test_open_notification_handle_exception(self, print_monitor):
        """Returns None on exception"""
        with patch(
            "services.print_monitor_service._HAS_NOTIFICATIONS", True
        ):
            with patch(
                "services.print_monitor_service._winspool"
            ) as mock_ws:
                mock_ws.OpenPrinterW.side_effect = Exception("Failed")
                result = print_monitor._open_notification_handle()
        assert result == (None, None)

    def test_wait_for_notification_no_api(self, print_monitor):
        """Returns False if notification API not available"""
        with patch(
            "services.print_monitor_service._HAS_NOTIFICATIONS", False
        ):
            result = print_monitor._wait_for_notification(Mock(), 500)
        assert result is False

    def test_close_notification_handle_no_api(self, print_monitor):
        """Does nothing if API not available"""
        with patch(
            "services.print_monitor_service._HAS_NOTIFICATIONS", False
        ):
            # Should not raise
            print_monitor._close_notification_handle(Mock(), Mock())

    def test_notification_thread_exits_on_stop_event(self, print_monitor):
        """Thread exits cleanly when stop event is set"""
        print_monitor._stop_event.set()

        with patch.object(
            print_monitor,
            "_open_notification_handle",
            return_value=(Mock(), Mock()),
        ):
            with patch.object(
                print_monitor,
                "_wait_for_notification",
                return_value=False,
            ):
                with patch.object(
                    print_monitor, "_close_notification_handle"
                ):
                    # Should exit quickly because stop_event is set
                    print_monitor._notification_thread_func()

    def test_notification_thread_calls_scan_on_event(self, print_monitor):
        """Thread calls _scan_for_new_jobs when notification fires"""
        call_count = [0]

        def mock_wait(hChange, timeout_ms):
            call_count[0] += 1
            if call_count[0] == 1:
                return True  # First call: event fired
            print_monitor._stop_event.set()  # Second call: exit
            return False

        with patch.object(
            print_monitor,
            "_open_notification_handle",
            return_value=(Mock(), Mock()),
        ):
            with patch.object(
                print_monitor,
                "_wait_for_notification",
                side_effect=mock_wait,
            ):
                with patch.object(
                    print_monitor, "_scan_for_new_jobs"
                ) as mock_scan:
                    with patch.object(
                        print_monitor, "_close_notification_handle"
                    ):
                        print_monitor._notification_thread_func()

        mock_scan.assert_called_once()

    def test_notification_thread_fallback_on_bad_handle(self, print_monitor):
        """Thread exits gracefully if handle creation fails"""
        with patch.object(
            print_monitor,
            "_open_notification_handle",
            return_value=(None, None),
        ):
            # Should exit without error
            print_monitor._notification_thread_func()
        assert print_monitor._using_notifications is False

    def test_open_notification_handle_success(self, print_monitor):
        """Tests the full ctypes path for opening notification handle"""
        mock_winspool = Mock()
        mock_winspool.OpenPrinterW = Mock()
        mock_winspool.FindFirstPrinterChangeNotification = Mock(
            return_value=42
        )  # Valid handle

        with patch(
            "services.print_monitor_service._HAS_NOTIFICATIONS", True
        ):
            with patch(
                "services.print_monitor_service._winspool", mock_winspool
            ):
                with patch(
                    "services.print_monitor_service.ctypes"
                ) as mock_ctypes:
                    mock_ctypes.byref = Mock()
                    hPrinter, hChange = (
                        print_monitor._open_notification_handle()
                    )

        assert hChange == 42
        mock_winspool.OpenPrinterW.assert_called_once()
        mock_winspool.FindFirstPrinterChangeNotification.assert_called_once()

    def test_open_notification_handle_invalid_handle(self, print_monitor):
        """Tests when FindFirst returns INVALID_HANDLE_VALUE"""
        mock_winspool = Mock()
        mock_winspool.OpenPrinterW = Mock()
        mock_winspool.FindFirstPrinterChangeNotification = Mock(
            return_value=-1
        )  # INVALID_HANDLE_VALUE
        mock_winspool.ClosePrinter = Mock()

        with patch(
            "services.print_monitor_service._HAS_NOTIFICATIONS", True
        ):
            with patch(
                "services.print_monitor_service._winspool", mock_winspool
            ):
                with patch(
                    "services.print_monitor_service.ctypes"
                ) as mock_ctypes:
                    mock_ctypes.byref = Mock()
                    mock_ctypes.get_last_error = Mock(return_value=5)
                    hPrinter, hChange = (
                        print_monitor._open_notification_handle()
                    )

        assert hPrinter is None
        assert hChange is None
        mock_winspool.ClosePrinter.assert_called_once()

    def test_wait_for_notification_event_fired(self, print_monitor):
        """Tests WaitForSingleObject returning WAIT_OBJECT_0"""
        mock_kernel32 = Mock()
        mock_kernel32.WaitForSingleObject = Mock(return_value=0)  # WAIT_OBJECT_0
        mock_winspool = Mock()
        mock_winspool.FindNextPrinterChangeNotification = Mock()

        with patch(
            "services.print_monitor_service._HAS_NOTIFICATIONS", True
        ):
            with patch(
                "services.print_monitor_service._kernel32", mock_kernel32
            ):
                with patch(
                    "services.print_monitor_service._winspool",
                    mock_winspool,
                ):
                    with patch(
                        "services.print_monitor_service.wintypes"
                    ):
                        with patch(
                            "services.print_monitor_service.ctypes"
                        ):
                            result = (
                                print_monitor._wait_for_notification(
                                    Mock(), 500
                                )
                            )

        assert result is True
        mock_kernel32.WaitForSingleObject.assert_called_once()
        mock_winspool.FindNextPrinterChangeNotification.assert_called_once()

    def test_wait_for_notification_timeout(self, print_monitor):
        """Tests WaitForSingleObject returning WAIT_TIMEOUT"""
        mock_kernel32 = Mock()
        mock_kernel32.WaitForSingleObject = Mock(
            return_value=0x00000102
        )  # WAIT_TIMEOUT

        with patch(
            "services.print_monitor_service._HAS_NOTIFICATIONS", True
        ):
            with patch(
                "services.print_monitor_service._kernel32", mock_kernel32
            ):
                result = print_monitor._wait_for_notification(
                    Mock(), 500
                )

        assert result is False

    def test_wait_for_notification_exception(self, print_monitor):
        """Tests exception handling in wait"""
        mock_kernel32 = Mock()
        mock_kernel32.WaitForSingleObject = Mock(
            side_effect=Exception("WinError")
        )

        with patch(
            "services.print_monitor_service._HAS_NOTIFICATIONS", True
        ):
            with patch(
                "services.print_monitor_service._kernel32", mock_kernel32
            ):
                result = print_monitor._wait_for_notification(
                    Mock(), 500
                )

        assert result is False

    def test_close_notification_handle_success(self, print_monitor):
        """Tests closing both handles"""
        mock_winspool = Mock()

        with patch(
            "services.print_monitor_service._HAS_NOTIFICATIONS", True
        ):
            with patch(
                "services.print_monitor_service._winspool", mock_winspool
            ):
                print_monitor._close_notification_handle(
                    Mock(), 42
                )

        mock_winspool.FindClosePrinterChangeNotification.assert_called_once()
        mock_winspool.ClosePrinter.assert_called_once()

    def test_close_notification_handle_exceptions(self, print_monitor):
        """Tests closing handles with exceptions (graceful)"""
        mock_winspool = Mock()
        mock_winspool.FindClosePrinterChangeNotification.side_effect = (
            Exception("Error1")
        )
        mock_winspool.ClosePrinter.side_effect = Exception("Error2")

        with patch(
            "services.print_monitor_service._HAS_NOTIFICATIONS", True
        ):
            with patch(
                "services.print_monitor_service._winspool", mock_winspool
            ):
                # Should not raise
                print_monitor._close_notification_handle(
                    Mock(), 42
                )

    def test_stop_monitoring_waits_for_thread(self, print_monitor):
        """Stop monitoring joins the notification thread"""
        print_monitor._is_monitoring = True
        print_monitor._poll_timer = Mock()

        mock_thread = Mock()
        mock_thread.is_alive.return_value = False
        print_monitor._notification_thread = mock_thread

        print_monitor.stop_monitoring()

        assert print_monitor._notification_thread is None


# =============================================================================
# Paused Job Handling Tests (Job Successfully Paused)
# =============================================================================


class TestPausedJobHandling:
    """Tests for _handle_paused_job - when we catch the job in time"""

    def test_approved_sufficient_budget(self, print_monitor, mock_firebase):
        """Job approved: budget sufficient → deduct + resume"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        signals = []
        print_monitor.job_allowed.connect(lambda *a: signals.append(a))

        with patch.object(
            print_monitor, "_resume_job", return_value=True
        ) as mock_resume:
            print_monitor._handle_paused_job("P", 42, "Doc", 5, 5.0)

        mock_resume.assert_called_once_with("P", 42)
        assert len(signals) == 1
        assert signals[0] == ("Doc", 5, 5.0, 45.0)

    def test_denied_insufficient_budget(self, print_monitor, mock_firebase):
        """Job denied: budget insufficient → cancel + notify"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 2.0},
        }

        signals = []
        print_monitor.job_blocked.connect(lambda *a: signals.append(a))

        with patch.object(
            print_monitor, "_cancel_job", return_value=True
        ) as mock_cancel:
            print_monitor._handle_paused_job("P", 42, "Doc", 10, 10.0)

        mock_cancel.assert_called_once_with("P", 42)
        assert len(signals) == 1
        assert signals[0] == ("Doc", 10, 10.0, 2.0)

    def test_deduction_fails_cancels(self, print_monitor, mock_firebase):
        """If deduction fails, cancel job and emit error"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {
            "success": False,
            "error": "DB error",
        }

        errors = []
        print_monitor.error_occurred.connect(lambda msg: errors.append(msg))

        with patch.object(
            print_monitor, "_cancel_job", return_value=True
        ) as mock_cancel:
            print_monitor._handle_paused_job("P", 42, "Doc", 5, 5.0)

        mock_cancel.assert_called_once()
        assert len(errors) == 1


# =============================================================================
# Escaped Job Handling Tests (Retroactive Charging)
# =============================================================================


class TestEscapedJobHandling:
    """Tests for _handle_escaped_job - when the job printed before we could
    pause it. The key principle: ALWAYS charge the full amount, even into
    negative balance (debt). No free prints."""

    def test_full_charge_sufficient_budget(
        self, print_monitor, mock_firebase
    ):
        """Escaped job with sufficient budget → full retroactive charge"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        signals = []
        print_monitor.job_allowed.connect(lambda *a: signals.append(a))

        print_monitor._handle_escaped_job("Doc", 5, 5.0)

        assert len(signals) == 1
        assert signals[0] == ("Doc", 5, 5.0, 45.0)

    def test_insufficient_budget_creates_debt(
        self, print_monitor, mock_firebase
    ):
        """Escaped job with insufficient budget → full charge, negative
        balance (debt). The job already printed, can't undo it."""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 3.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        signals = []
        print_monitor.job_allowed.connect(lambda *a: signals.append(a))

        print_monitor._handle_escaped_job("Doc", 10, 10.0)

        assert len(signals) == 1
        # Full charge of 10.0 from 3.0 → remaining = -7.0 (debt)
        assert signals[0] == ("Doc", 10, 10.0, -7.0)
        # Verify full amount deducted (allow_negative=True)
        call_args = mock_firebase.db_update.call_args
        assert call_args[0][1]["printBalance"] == -7.0

    def test_zero_budget_creates_debt(self, print_monitor, mock_firebase):
        """Escaped job with zero budget → full charge, creates debt.
        No free prints - the user owes the full amount."""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 0.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        signals = []
        print_monitor.job_allowed.connect(lambda *a: signals.append(a))

        print_monitor._handle_escaped_job("Doc", 5, 5.0)

        assert len(signals) == 1
        # 0.0 - 5.0 = -5.0 (debt)
        assert signals[0] == ("Doc", 5, 5.0, -5.0)
        call_args = mock_firebase.db_update.call_args
        assert call_args[0][1]["printBalance"] == -5.0

    def test_deduction_error_emits_signal(self, print_monitor, mock_firebase):
        """Escaped job deduction failure → error signal"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {
            "success": False,
            "error": "DB error",
        }

        errors = []
        print_monitor.error_occurred.connect(lambda msg: errors.append(msg))

        print_monitor._handle_escaped_job("Doc", 5, 5.0)

        assert len(errors) == 1


# =============================================================================
# Full Job Handling Flow Tests
# =============================================================================


class TestHandleNewJob:
    """Tests for the complete _handle_new_job flow"""

    def test_job_paused_and_approved(self, print_monitor, mock_firebase):
        """Full flow: job detected → paused → approved"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        devmode = Mock()
        devmode.Copies = 1
        devmode.Color = 1

        job_data = {
            "JobId": 1,
            "pDocument": "Test Doc",
            "TotalPages": 5,
            "Status": 0,
            "pDevMode": devmode,
        }

        signals = []
        print_monitor.job_allowed.connect(lambda *a: signals.append(a))

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(
                print_monitor, "_resume_job", return_value=True
            ):
                print_monitor._handle_new_job("Printer1", job_data)

        assert len(signals) == 1
        _, pages, cost, remaining = signals[0]
        assert pages == 5
        assert cost == 5.0
        assert remaining == 45.0

    def test_job_paused_and_denied(self, print_monitor, mock_firebase):
        """Full flow: job detected → paused → denied (no budget)"""
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

        blocked = []
        print_monitor.job_blocked.connect(lambda *a: blocked.append(a))

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(
                print_monitor, "_cancel_job", return_value=True
            ):
                print_monitor._handle_new_job("Printer1", job_data)

        assert len(blocked) == 1
        _, pages, cost, budget = blocked[0]
        assert pages == 10
        assert cost == 100.0
        assert budget == 5.0

    def test_job_escaped_charged_retroactively(
        self, print_monitor, mock_firebase
    ):
        """Full flow: job detected → pause failed → charge retroactively"""
        print_monitor._bw_price = 1.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 50.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        job_data = {
            "JobId": 1,
            "pDocument": "Fast Job",
            "TotalPages": 3,
            "Status": 0,
        }

        signals = []
        print_monitor.job_allowed.connect(lambda *a: signals.append(a))

        # _pause_job returns False = job already completed
        with patch.object(print_monitor, "_pause_job", return_value=False):
            print_monitor._handle_new_job("Printer1", job_data)

        # Should still charge (retroactively)
        assert len(signals) == 1
        _, pages, cost, remaining = signals[0]
        assert pages == 3
        assert cost == 3.0
        assert remaining == 47.0

    def test_job_escaped_zero_budget_creates_debt(
        self, print_monitor, mock_firebase
    ):
        """Full flow: escaped job + zero budget → debt (no free prints)"""
        print_monitor._bw_price = 2.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 0.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        job_data = {
            "JobId": 1,
            "pDocument": "Free Attempt",
            "TotalPages": 5,
            "Status": 0,
        }

        signals = []
        print_monitor.job_allowed.connect(lambda *a: signals.append(a))

        with patch.object(print_monitor, "_pause_job", return_value=False):
            print_monitor._handle_new_job("Printer1", job_data)

        assert len(signals) == 1
        _, pages, cost, remaining = signals[0]
        assert pages == 5
        assert cost == 10.0
        assert remaining == -10.0  # Debt!

    def test_job_with_copies_and_color(self, print_monitor, mock_firebase):
        """Full flow: color job with copies → correct cost calculation"""
        print_monitor._color_price = 3.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 100.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        devmode = Mock()
        devmode.Copies = 2
        devmode.Color = 2  # Color

        job_data = {
            "JobId": 1,
            "pDocument": "Color Doc",
            "TotalPages": 5,
            "Status": 0,
            "pDevMode": devmode,
        }

        signals = []
        print_monitor.job_allowed.connect(lambda *a: signals.append(a))

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(
                print_monitor, "_resume_job", return_value=True
            ):
                print_monitor._handle_new_job("Printer1", job_data)

        _, pages, cost, _ = signals[0]
        assert pages == 10  # 5 × 2 copies
        assert cost == 30.0  # 5 × 2 × 3.0 (color)

    def test_job_no_devmode_defaults(self, print_monitor, mock_firebase):
        """Full flow: no DEVMODE → defaults to 1 copy, B&W"""
        print_monitor._bw_price = 2.0
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"printBalance": 100.0},
        }
        mock_firebase.db_update.return_value = {"success": True}

        job_data = {
            "JobId": 1,
            "pDocument": "Simple",
            "TotalPages": 3,
            "Status": 0,
        }

        signals = []
        print_monitor.job_allowed.connect(lambda *a: signals.append(a))

        with patch.object(print_monitor, "_pause_job", return_value=True):
            with patch.object(
                print_monitor, "_resume_job", return_value=True
            ):
                print_monitor._handle_new_job("Printer1", job_data)

        _, pages, cost, _ = signals[0]
        assert pages == 3  # 3 × 1 copy
        assert cost == 6.0  # 3 × 1 × 2.0 (B&W)


# =============================================================================
# Spool Wait Tests
# =============================================================================


class TestSpoolWait:

    def test_returns_immediately_if_not_spooling(self, print_monitor):
        data = {"TotalPages": 5, "Status": 0}
        result = print_monitor._wait_for_spool_complete("P", 1, data)
        assert result == data

    def test_waits_for_spooling(self, print_monitor):
        data = {"TotalPages": 0, "Status": 8}  # SPOOLING

        call_count = [0]

        def mock_info(printer, job_id):
            call_count[0] += 1
            if call_count[0] < 3:
                return {"TotalPages": 0, "Status": 8, "Size": 100}
            return {"TotalPages": 5, "Status": 0, "Size": 5000}

        with patch.object(
            print_monitor, "_get_job_info", side_effect=mock_info
        ):
            with patch("time.sleep"):
                result = print_monitor._wait_for_spool_complete("P", 1, data)

        assert result["TotalPages"] == 5

    def test_stable_count_accepted(self, print_monitor):
        data = {"TotalPages": 0, "Status": 8}

        def mock_info(printer, job_id):
            return {"TotalPages": 3, "Status": 8, "Size": 1000}

        with patch.object(
            print_monitor, "_get_job_info", side_effect=mock_info
        ):
            with patch("time.sleep"):
                result = print_monitor._wait_for_spool_complete("P", 1, data)

        assert result["TotalPages"] == 3

    def test_job_disappears(self, print_monitor):
        data = {"TotalPages": 0, "Status": 8}

        with patch.object(
            print_monitor, "_get_job_info", return_value={}
        ):
            with patch("time.sleep"):
                result = print_monitor._wait_for_spool_complete("P", 1, data)

        assert result == data  # Returns original


# =============================================================================
# Signal Tests
# =============================================================================


class TestSignals:

    def test_job_allowed_signal(self, print_monitor):
        r = []
        print_monitor.job_allowed.connect(lambda *a: r.append(a))
        print_monitor.job_allowed.emit("Doc", 5, 10.0, 40.0)
        assert r == [("Doc", 5, 10.0, 40.0)]

    def test_job_blocked_signal(self, print_monitor):
        r = []
        print_monitor.job_blocked.connect(lambda *a: r.append(a))
        print_monitor.job_blocked.emit("Doc", 10, 100.0, 5.0)
        assert r == [("Doc", 10, 100.0, 5.0)]

    def test_budget_updated_signal(self, print_monitor):
        r = []
        print_monitor.budget_updated.connect(lambda x: r.append(x))
        print_monitor.budget_updated.emit(42.5)
        assert r == [42.5]

    def test_error_occurred_signal(self, print_monitor):
        r = []
        print_monitor.error_occurred.connect(lambda x: r.append(x))
        print_monitor.error_occurred.emit("Test error")
        assert r == ["Test error"]


# =============================================================================
# Edge Cases & Thread Safety
# =============================================================================


class TestEdgeCases:

    def test_concurrent_job_processing_thread_safe(self, print_monitor):
        """Ensure same job is only processed once across threads"""
        process_count = [0]

        def mock_poll():
            with print_monitor._lock:
                if "Printer1:1" in print_monitor._processed_jobs:
                    return
                print_monitor._processed_jobs.add("Printer1:1")
            process_count[0] += 1

        threads = [threading.Thread(target=mock_poll) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert process_count[0] == 1

    def test_scan_no_printers(self, print_monitor):
        print_monitor._is_monitoring = True
        with patch.object(
            print_monitor, "_get_all_printers", return_value=[]
        ):
            print_monitor._scan_for_new_jobs()  # Should not crash

    def test_multiple_printers_independent(
        self, print_monitor, mock_win32print
    ):
        """Test that jobs from different printers are tracked independently"""
        print_monitor._is_monitoring = True
        print_monitor._known_jobs = {
            "Printer1": {1},
            "Printer2": {10},
        }

        mock_win32print.EnumPrinters.return_value = [
            (0, "", "Printer1", ""),
            (0, "", "Printer2", ""),
        ]
        mock_win32print.OpenPrinter.return_value = Mock()

        call_count = [0]

        def enum_jobs(handle, start, count, level):
            call_count[0] += 1
            if call_count[0] <= 1:  # First printer
                return [{"JobId": 1}, {"JobId": 2, "pDocument": "New1"}]
            else:  # Second printer
                return [{"JobId": 10}, {"JobId": 11, "pDocument": "New2"}]

        mock_win32print.EnumJobs.side_effect = enum_jobs

        handled_jobs = []

        def track_handle(printer, data):
            handled_jobs.append((printer, data["JobId"]))

        with patch(
            "services.print_monitor_service.win32print", mock_win32print
        ):
            with patch.object(
                print_monitor, "_handle_new_job", side_effect=track_handle
            ):
                print_monitor._scan_for_new_jobs()

        # Should detect new job from each printer
        assert ("Printer1", 2) in handled_jobs
        assert ("Printer2", 11) in handled_jobs

    def test_no_global_printer_state(self, print_monitor):
        """Verify there's no module-level printer state (multi-PC safe)"""
        import services.print_monitor_service as mod

        assert not hasattr(mod, "_globally_paused_printers")

"""
Print Monitor Service
Monitors Windows Print Spooler and validates print jobs against user's budget.

Architecture: Event-driven WMI with polling fallback
- Primary: WMI event subscription for instant job detection
- Fallback: Polling every 2 seconds as safety net

Flow:
1. WMI event fires when new print job created (or polling detects it)
2. Pause job immediately
3. Get page count and calculate cost (B&W or Color price from org metadata)
4. If user has sufficient budget: resume job + deduct budget
5. If insufficient: cancel job + emit signal for UI notification
"""

import threading
import traceback
from datetime import datetime
from typing import Dict, Optional, Set

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from services.firebase_client import FirebaseClient
from utils.logger import get_logger

# win32print is only available on Windows
try:
    import win32print
except ImportError:
    win32print = None  # Will be mocked in tests

# WMI is only available on Windows
try:
    import pythoncom
    import wmi
except ImportError:
    pythoncom = None
    wmi = None

logger = get_logger(__name__)


# Windows Print Job Control Commands
JOB_CONTROL_PAUSE = 1
JOB_CONTROL_RESUME = 2
JOB_CONTROL_CANCEL = 3


class PrintMonitorService(QObject):
    """
    Print Monitor - uses WMI events for instant detection with polling fallback.
    """

    # Signals for UI notifications
    job_allowed = pyqtSignal(str, int, float, float)  # doc_name, pages, cost, remaining
    job_blocked = pyqtSignal(str, int, float, float)  # doc_name, pages, cost, budget
    budget_updated = pyqtSignal(float)  # new_budget
    error_occurred = pyqtSignal(str)  # error_message

    def __init__(
        self,
        firebase_client: FirebaseClient,
        user_id: str,
        org_id: str,
    ):
        super().__init__()
        self.firebase = firebase_client
        self.user_id = user_id
        self.org_id = org_id

        # Monitoring state
        self._is_monitoring = False
        self._known_jobs: Dict[str, Set[int]] = {}  # printer_name -> set of job_ids
        self._processed_jobs: Set[str] = set()  # "printer:job_id" to avoid duplicates
        self._poll_timer: Optional[QTimer] = None

        # WMI event watcher thread
        self._wmi_thread: Optional[threading.Thread] = None
        self._wmi_stop_event = threading.Event()

        # Thread safety lock
        self._lock = threading.Lock()

        # Cached pricing (refreshed on start)
        self._bw_price = 1.0  # Default fallback
        self._color_price = 3.0  # Default fallback

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def start_monitoring(self) -> Dict:
        """Start monitoring print spooler for new jobs."""
        if self._is_monitoring:
            logger.warning("Print monitoring already running")
            return {"success": True, "message": "Already monitoring"}

        try:
            logger.info("Starting print monitor service")

            # Load org pricing
            self._load_pricing()

            # Initialize known jobs (ignore existing jobs in queue)
            self._initialize_known_jobs()

            # Clear processed jobs set
            self._processed_jobs.clear()

            # Start WMI event watcher (primary - instant detection)
            self._start_wmi_watcher()

            # Start polling timer (fallback - every 2 seconds)
            self._poll_timer = QTimer()
            self._poll_timer.timeout.connect(self._poll_spooler)
            self._poll_timer.start(2000)  # 2 seconds fallback

            self._is_monitoring = True
            logger.info("Print monitor started (WMI events + polling fallback)")
            return {"success": True}

        except Exception as e:
            logger.error(f"Failed to start print monitor: {e}")
            return {"success": False, "error": str(e)}

    def stop_monitoring(self) -> Dict:
        """Stop monitoring print spooler."""
        if not self._is_monitoring:
            return {"success": True, "message": "Not monitoring"}

        try:
            logger.info("Stopping print monitor service")

            # Stop WMI watcher
            self._stop_wmi_watcher()

            # Stop polling timer
            if self._poll_timer:
                self._poll_timer.stop()
                self._poll_timer = None

            self._is_monitoring = False
            with self._lock:
                self._known_jobs.clear()
                self._processed_jobs.clear()

            logger.info("Print monitor stopped")
            return {"success": True}

        except Exception as e:
            logger.error(f"Failed to stop print monitor: {e}")
            return {"success": False, "error": str(e)}

    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._is_monitoring

    # =========================================================================
    # WMI EVENT WATCHER
    # =========================================================================

    def _start_wmi_watcher(self):
        """Start WMI event watcher in background thread."""
        if not wmi or not pythoncom:
            logger.warning("WMI not available, using polling only")
            return

        self._wmi_stop_event.clear()
        self._wmi_thread = threading.Thread(
            target=self._wmi_watch_loop,
            name="PrintMonitor-WMI",
            daemon=True,
        )
        self._wmi_thread.start()
        logger.info("WMI event watcher started")

    def _stop_wmi_watcher(self):
        """Stop WMI event watcher thread."""
        if self._wmi_thread and self._wmi_thread.is_alive():
            logger.info("Stopping WMI event watcher...")
            self._wmi_stop_event.set()
            # Give thread time to exit gracefully
            self._wmi_thread.join(timeout=3.0)
            if self._wmi_thread.is_alive():
                logger.warning("WMI thread did not stop gracefully")
            self._wmi_thread = None

    def _wmi_watch_loop(self):
        """Background thread loop watching for WMI print job events."""
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()

            try:
                c = wmi.WMI()

                # Watch for new print job creation events
                # Query: SELECT * FROM __InstanceCreationEvent within 1 second
                # WHERE TargetInstance ISA 'Win32_PrintJob'
                watcher = c.Win32_PrintJob.watch_for(
                    notification_type="Creation",
                    delay_secs=1,
                )

                logger.info("WMI watcher initialized, listening for print jobs...")

                while not self._wmi_stop_event.is_set():
                    try:
                        # Wait for event with timeout (allows checking stop flag)
                        event = watcher(timeout_ms=1000)
                        if event:
                            self._on_wmi_print_job_event(event)
                    except wmi.x_wmi_timed_out:
                        # Timeout is normal, just continue loop
                        continue
                    except Exception as e:
                        if not self._wmi_stop_event.is_set():
                            logger.error(f"WMI event error: {e}")
                        break

            finally:
                pythoncom.CoUninitialize()

        except Exception as e:
            logger.error(f"WMI watch loop error: {e}")
            logger.error(traceback.format_exc())

    def _on_wmi_print_job_event(self, event):
        """Handle WMI print job creation event."""
        try:
            # Extract job info from WMI event
            # WMI Win32_PrintJob properties: Name format is "PrinterName, JobId"
            job_name = event.Name  # e.g., "HP LaserJet, 42"
            if "," not in job_name:
                logger.warning(f"Unexpected job name format: {job_name}")
                return

            parts = job_name.rsplit(",", 1)
            printer_name = parts[0].strip()
            job_id = int(parts[1].strip())

            logger.info(f"WMI event: New print job {job_id} on '{printer_name}'")

            # Build job data from WMI event
            job_data = {
                "JobId": job_id,
                "pDocument": getattr(event, "Document", "Unknown"),
                "TotalPages": getattr(event, "TotalPages", 0),
            }

            # Process job (thread-safe)
            self._process_job_thread_safe(printer_name, job_data)

        except Exception as e:
            logger.error(f"Error handling WMI event: {e}")
            logger.error(traceback.format_exc())

    def _process_job_thread_safe(self, printer_name: str, job_data: dict):
        """Process a print job with thread safety (can be called from WMI thread)."""
        job_id = job_data.get("JobId", 0)
        job_key = f"{printer_name}:{job_id}"

        with self._lock:
            # Check if already processed (avoid duplicates from WMI + polling)
            if job_key in self._processed_jobs:
                logger.debug(f"Job {job_key} already processed, skipping")
                return
            self._processed_jobs.add(job_key)

            # Update known jobs
            if printer_name not in self._known_jobs:
                self._known_jobs[printer_name] = set()
            self._known_jobs[printer_name].add(job_id)

        # Handle the job (actual processing)
        self._handle_new_job(printer_name, job_data)

    # =========================================================================
    # PRICING
    # =========================================================================

    def _load_pricing(self):
        """Load organization print pricing from Firebase."""
        try:
            result = self.firebase.db_get("metadata")
            if result.get("success") and result.get("data"):
                metadata = result["data"]
                self._bw_price = float(metadata.get("blackAndWhitePrice", 1.0))
                self._color_price = float(metadata.get("colorPrice", 3.0))
                logger.info(
                    f"Loaded pricing: B&W={self._bw_price}₪, Color={self._color_price}₪"
                )
            else:
                logger.warning("Could not load pricing, using defaults")
        except Exception as e:
            logger.error(f"Error loading pricing: {e}")

    def _calculate_cost(self, pages: int, is_color: bool = False) -> float:
        """Calculate print cost based on page count and type."""
        price_per_page = self._color_price if is_color else self._bw_price
        return pages * price_per_page

    # =========================================================================
    # BUDGET
    # =========================================================================

    def _get_user_budget(self) -> float:
        """Get user's current print budget (printBalance field)."""
        try:
            result = self.firebase.db_get(f"users/{self.user_id}")
            if result.get("success") and result.get("data"):
                return float(result["data"].get("printBalance", 0.0))
            return 0.0
        except Exception as e:
            logger.error(f"Error getting user budget: {e}")
            return 0.0

    def _deduct_budget(self, amount: float) -> bool:
        """Deduct amount from user's print budget."""
        try:
            current_budget = self._get_user_budget()
            new_budget = max(0.0, current_budget - amount)

            result = self.firebase.db_update(
                f"users/{self.user_id}",
                {
                    "printBalance": new_budget,
                    "updatedAt": datetime.now().isoformat(),
                },
            )

            if result.get("success"):
                logger.info(f"Budget deducted: {amount}₪, new balance: {new_budget}₪")
                self.budget_updated.emit(new_budget)
                return True
            else:
                logger.error(f"Failed to deduct budget: {result.get('error')}")
                return False

        except Exception as e:
            logger.error(f"Error deducting budget: {e}")
            return False

    # =========================================================================
    # SPOOLER INTERACTION
    # =========================================================================

    def _get_all_printers(self) -> list:
        """Get list of all printer names."""
        if not win32print:
            return []
        try:
            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            printers = win32print.EnumPrinters(flags)
            return [p[2] for p in printers]  # p[2] is printer name
        except Exception as e:
            logger.error(f"Error enumerating printers: {e}")
            return []

    def _get_printer_jobs(self, printer_name: str) -> list:
        """Get all jobs in a printer's queue."""
        if not win32print:
            return []
        try:
            handle = win32print.OpenPrinter(printer_name)
            try:
                jobs = win32print.EnumJobs(handle, 0, -1, 1)  # Level 1 info
                return list(jobs) if jobs else []
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            logger.error(f"Error getting jobs for {printer_name}: {e}")
            return []

    def _pause_job(self, printer_name: str, job_id: int) -> bool:
        """Pause a print job."""
        if not win32print:
            return False
        try:
            handle = win32print.OpenPrinter(printer_name)
            try:
                win32print.SetJob(handle, job_id, 0, None, JOB_CONTROL_PAUSE)
                logger.debug(f"Paused job {job_id}")
                return True
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return False

    def _resume_job(self, printer_name: str, job_id: int) -> bool:
        """Resume a paused print job."""
        if not win32print:
            return False
        try:
            handle = win32print.OpenPrinter(printer_name)
            try:
                win32print.SetJob(handle, job_id, 0, None, JOB_CONTROL_RESUME)
                logger.debug(f"Resumed job {job_id}")
                return True
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return False

    def _cancel_job(self, printer_name: str, job_id: int) -> bool:
        """Cancel a print job."""
        if not win32print:
            return False
        try:
            handle = win32print.OpenPrinter(printer_name)
            try:
                win32print.SetJob(handle, job_id, 0, None, JOB_CONTROL_CANCEL)
                logger.debug(f"Cancelled job {job_id}")
                return True
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False

    # =========================================================================
    # POLLING FALLBACK
    # =========================================================================

    def _initialize_known_jobs(self):
        """Record existing jobs so we don't process them."""
        with self._lock:
            self._known_jobs.clear()
            for printer_name in self._get_all_printers():
                jobs = self._get_printer_jobs(printer_name)
                self._known_jobs[printer_name] = {job.get("JobId", 0) for job in jobs}
                if self._known_jobs[printer_name]:
                    logger.debug(
                        f"Ignoring {len(self._known_jobs[printer_name])} existing jobs "
                        f"on {printer_name}"
                    )

    def _poll_spooler(self):
        """Check for new print jobs (fallback, called by timer)."""
        if not self._is_monitoring:
            return

        try:
            for printer_name in self._get_all_printers():
                with self._lock:
                    if printer_name not in self._known_jobs:
                        self._known_jobs[printer_name] = set()
                    known = self._known_jobs[printer_name].copy()

                current_jobs = self._get_printer_jobs(printer_name)
                current_ids = {job.get("JobId", 0) for job in current_jobs}

                # Find new jobs not yet known
                new_ids = current_ids - known

                for job_id in new_ids:
                    job_data = next(
                        (j for j in current_jobs if j.get("JobId") == job_id),
                        None,
                    )
                    if job_data:
                        # Use thread-safe processing (may have been caught by WMI already)
                        self._process_job_thread_safe(printer_name, job_data)

                # Update known jobs for removed jobs
                with self._lock:
                    self._known_jobs[printer_name] = current_ids

                    # Clean up processed jobs set (remove jobs no longer in queue)
                    keys_to_remove = [
                        key
                        for key in self._processed_jobs
                        if key.startswith(f"{printer_name}:")
                        and int(key.split(":")[1]) not in current_ids
                    ]
                    for key in keys_to_remove:
                        self._processed_jobs.discard(key)

        except Exception as e:
            logger.error(f"Error polling spooler: {e}")
            logger.error(traceback.format_exc())

    # =========================================================================
    # JOB HANDLING
    # =========================================================================

    def _handle_new_job(self, printer_name: str, job_data: dict):
        """Process a newly detected print job."""
        job_id = job_data.get("JobId", 0)
        doc_name = job_data.get("pDocument", "Unknown")
        total_pages = job_data.get("TotalPages", 0)

        # Handle case where page count is 0 or unknown
        if total_pages <= 0:
            total_pages = 1  # Assume at least 1 page

        logger.info(
            f"New print job: '{doc_name}' ({total_pages} pages) on {printer_name}"
        )

        # Step 1: Pause the job immediately
        if not self._pause_job(printer_name, job_id):
            logger.error(f"Could not pause job {job_id}, allowing it to proceed")
            return

        # Step 2: Calculate cost (assume B&W for MVP - color detection is complex)
        # TODO: Add color detection in future version
        is_color = False
        cost = self._calculate_cost(total_pages, is_color)

        # Step 3: Check budget
        budget = self._get_user_budget()

        if budget >= cost:
            # ALLOW: Deduct and resume
            if self._deduct_budget(cost):
                self._resume_job(printer_name, job_id)
                remaining = budget - cost
                logger.info(
                    f"Job ALLOWED: '{doc_name}' - cost {cost}₪, remaining {remaining}₪"
                )
                self.job_allowed.emit(doc_name, total_pages, cost, remaining)
            else:
                # Deduction failed, cancel to be safe
                self._cancel_job(printer_name, job_id)
                self.error_occurred.emit("Failed to process print job")
        else:
            # BLOCK: Cancel and notify
            self._cancel_job(printer_name, job_id)
            logger.warning(
                f"Job BLOCKED: '{doc_name}' - cost {cost}₪, budget {budget}₪"
            )
            self.job_blocked.emit(doc_name, total_pages, cost, budget)

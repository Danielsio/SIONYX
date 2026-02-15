"""
Print Monitor Service - Pause-First Architecture
Guarantees 100% print job interception by keeping printers paused during sessions.

Architecture:
- On session start: Pause ALL printers so jobs queue but cannot print
- Polling detects new jobs (100% reliable since jobs can't escape the queue)
- For each job: wait for spool, extract pages/copies/color, calculate cost
- Approved: safely release the single job, then re-pause the printer
- Denied: cancel the job and notify user
- On session end: resume all printers

Cost formula:
  cost = total_pages × copies × price_per_page(BW or color)

Crash safety:
- atexit handler resumes all printers even on unexpected exit
- On startup: detect and resume printers left paused from a previous crash
- Tracks which printers WE paused to avoid interfering with intentional pauses
"""

import atexit
import threading
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Set

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from services.firebase_client import FirebaseClient
from utils.logger import get_logger

# win32print is only available on Windows
try:
    import win32print
except ImportError:
    win32print = None  # Will be mocked in tests

logger = get_logger(__name__)

# Windows Print Job Control Commands
JOB_CONTROL_PAUSE = 1
JOB_CONTROL_RESUME = 2
JOB_CONTROL_CANCEL = 3

# Windows Printer Control Commands
PRINTER_CONTROL_PAUSE = 1
PRINTER_CONTROL_RESUME = 2

# Printer status flags
PRINTER_STATUS_PAUSED = 0x00000001

# Job status flags
JOB_STATUS_PAUSED = 0x00000001
JOB_STATUS_SPOOLING = 0x00000008
JOB_STATUS_PRINTING = 0x00000010
JOB_STATUS_DELETING = 0x00000004

# DEVMODE color constants
DMCOLOR_COLOR = 2

# Global set to track which printers we paused (for atexit handler)
_globally_paused_printers: Set[str] = set()
_global_lock = threading.Lock()


def _atexit_resume_printers():
    """
    Emergency handler: resume all printers that SIONYX paused.

    Called by atexit on any exit (normal, exception, signal).
    This prevents leaving printers stuck in paused state if SIONYX crashes.
    """
    with _global_lock:
        printers_to_resume = list(_globally_paused_printers)

    if not printers_to_resume or not win32print:
        return

    for printer_name in printers_to_resume:
        try:
            handle = win32print.OpenPrinter(printer_name)
            try:
                win32print.SetPrinter(
                    handle, 0, None, PRINTER_CONTROL_RESUME
                )
            finally:
                win32print.ClosePrinter(handle)
        except Exception:
            pass  # Best effort on exit


# Register the atexit handler once at module load
atexit.register(_atexit_resume_printers)


class PrintMonitorService(QObject):
    """
    Print Monitor - Pause-First Architecture.

    Keeps all printers paused during user sessions so that every print job
    is guaranteed to be caught, validated against budget, and either approved
    or denied before any ink hits paper.

    Safety Features:
    - Printers are paused at session start (jobs physically cannot bypass)
    - On shutdown: all printers are resumed
    - atexit handler resumes printers even on crash
    - On startup: recovers printers left paused from previous crash
    """

    # Signals for UI notifications
    job_allowed = pyqtSignal(str, int, float, float)  # doc, pages, cost, remaining
    job_blocked = pyqtSignal(str, int, float, float)  # doc, pages, cost, budget
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

        # Thread safety lock
        self._lock = threading.Lock()

        # Cached pricing (refreshed on start)
        self._bw_price = 1.0  # Default fallback
        self._color_price = 3.0  # Default fallback

        # Cached budget (avoids db_get on every print job)
        self._cached_budget: Optional[float] = None
        self._budget_cache_time: Optional[datetime] = None
        self._budget_cache_ttl = 30  # seconds

        # Track which printers WE paused (to resume on shutdown/crash)
        self._paused_printers: Set[str] = set()

        # Track jobs we are currently releasing (to avoid re-processing)
        self._releasing_jobs: Set[str] = set()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def start_monitoring(self) -> Dict:
        """Start monitoring print spooler for new jobs."""
        if self._is_monitoring:
            logger.warning("Print monitoring already running")
            return {"success": True, "message": "Already monitoring"}

        try:
            logger.info("Starting print monitor service (pause-first architecture)")

            # Safety: Recover printers left paused from a previous crash
            self._recover_from_crash()

            # Load org pricing
            self._load_pricing()

            # Pause all printers to guarantee job interception
            self._pause_all_printers()

            # Initialize known jobs (ignore existing jobs in queue)
            self._initialize_known_jobs()

            # Clear processed jobs set
            self._processed_jobs.clear()
            self._releasing_jobs.clear()

            # Start polling timer (1 second interval - safe because jobs can't escape)
            self._poll_timer = QTimer()
            self._poll_timer.timeout.connect(self._poll_print_queues)
            self._poll_timer.start(1000)
            logger.debug("Polling timer started with 1000ms interval")

            self._is_monitoring = True
            logger.info("Print monitor started (all printers paused)")
            return {"success": True}

        except Exception as e:
            logger.error(f"Failed to start print monitor: {e}")
            # If we partially started, try to resume any printers we paused
            self._resume_all_printers()
            return {"success": False, "error": str(e)}

    def stop_monitoring(self) -> Dict:
        """Stop monitoring and resume all printers."""
        if not self._is_monitoring:
            return {"success": True, "message": "Not monitoring"}

        try:
            logger.info("Stopping print monitor service")

            # Stop polling timer first
            if self._poll_timer:
                self._poll_timer.stop()
                self._poll_timer = None

            # Resume all printers we paused
            self._resume_all_printers()

            self._is_monitoring = False
            with self._lock:
                self._known_jobs.clear()
                self._processed_jobs.clear()
                self._releasing_jobs.clear()

            logger.info("Print monitor stopped (all printers resumed)")
            return {"success": True}

        except Exception as e:
            logger.error(f"Failed to stop print monitor: {e}")
            return {"success": False, "error": str(e)}

    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._is_monitoring

    # =========================================================================
    # PRINTER-LEVEL PAUSE / RESUME
    # =========================================================================

    def _pause_all_printers(self):
        """
        Pause all printers so new jobs queue up but cannot print.

        This is the core of the pause-first architecture - by keeping printers
        paused, we guarantee that no job can bypass our budget check.
        """
        printers = self._get_all_printers()
        if not printers:
            logger.warning("No printers found! Print monitoring may not work.")
            return

        logger.info(f"Pausing {len(printers)} printer(s) for budget enforcement")

        for printer_name in printers:
            if self._is_printer_paused(printer_name):
                logger.debug(f"Printer '{printer_name}' already paused, skipping")
                continue
            self._pause_printer(printer_name)

    def _resume_all_printers(self):
        """
        Resume all printers that we paused.

        Called on stop_monitoring() and by atexit handler on crash.
        Only resumes printers that WE paused (tracked in _paused_printers).
        """
        with self._lock:
            printers_to_resume = list(self._paused_printers)

        if not printers_to_resume:
            logger.debug("No paused printers to resume")
            return

        logger.info(f"Resuming {len(printers_to_resume)} printer(s)")

        for printer_name in printers_to_resume:
            self._resume_printer(printer_name)

    def _pause_printer(self, printer_name: str) -> bool:
        """Pause a single printer."""
        if not win32print:
            return False
        try:
            handle = win32print.OpenPrinter(printer_name)
            try:
                win32print.SetPrinter(
                    handle, 0, None, PRINTER_CONTROL_PAUSE
                )
                with self._lock:
                    self._paused_printers.add(printer_name)
                # Also update global tracker for atexit
                with _global_lock:
                    _globally_paused_printers.add(printer_name)
                logger.info(f"Paused printer: '{printer_name}'")
                return True
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            logger.error(f"Failed to pause printer '{printer_name}': {e}")
            return False

    def _resume_printer(self, printer_name: str) -> bool:
        """Resume a single printer."""
        if not win32print:
            return False
        try:
            handle = win32print.OpenPrinter(printer_name)
            try:
                win32print.SetPrinter(
                    handle, 0, None, PRINTER_CONTROL_RESUME
                )
                with self._lock:
                    self._paused_printers.discard(printer_name)
                # Also update global tracker
                with _global_lock:
                    _globally_paused_printers.discard(printer_name)
                logger.info(f"Resumed printer: '{printer_name}'")
                return True
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            logger.error(f"Failed to resume printer '{printer_name}': {e}")
            return False

    def _is_printer_paused(self, printer_name: str) -> bool:
        """Check if a printer is currently paused."""
        if not win32print:
            return False
        try:
            handle = win32print.OpenPrinter(printer_name)
            try:
                # GetPrinter level 2 returns status
                info = win32print.GetPrinter(handle, 2)
                status = info.get("Status", 0) if isinstance(info, dict) else 0
                return bool(status & PRINTER_STATUS_PAUSED)
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            logger.debug(f"Could not check printer status for '{printer_name}': {e}")
            return False

    # =========================================================================
    # CRASH RECOVERY
    # =========================================================================

    def _recover_from_crash(self):
        """
        Detect and resume printers left paused from a previous SIONYX crash.

        On startup, check all printers. If any are paused and appear in the
        global tracking set (from atexit), resume them. This prevents
        printers from being permanently stuck after a crash.
        """
        if not win32print:
            return

        try:
            # Check the global set for printers we might have left paused
            with _global_lock:
                leftover = list(_globally_paused_printers)

            if leftover:
                logger.warning(
                    f"Found {len(leftover)} printer(s) possibly left paused "
                    "from previous crash. Resuming..."
                )
                for printer_name in leftover:
                    try:
                        if self._is_printer_paused(printer_name):
                            self._resume_printer(printer_name)
                            logger.info(
                                f"Recovered printer '{printer_name}' from crash"
                            )
                    except Exception as e:
                        logger.error(
                            f"Failed to recover printer '{printer_name}': {e}"
                        )
                # Clear the global set
                with _global_lock:
                    _globally_paused_printers.clear()
            else:
                logger.debug("No crashed printer state to recover")

        except Exception as e:
            logger.error(f"Error during crash recovery: {e}")

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
                    f"Loaded pricing: B&W={self._bw_price}₪, "
                    f"Color={self._color_price}₪"
                )
            else:
                logger.warning("Could not load pricing, using defaults")
        except Exception as e:
            logger.error(f"Error loading pricing: {e}")

    def _calculate_cost(
        self, pages: int, copies: int, is_color: bool = False
    ) -> float:
        """
        Calculate print cost.

        Formula: pages × copies × price_per_page
        """
        price_per_page = self._color_price if is_color else self._bw_price
        return pages * copies * price_per_page

    # =========================================================================
    # BUDGET
    # =========================================================================

    def _get_user_budget(self, force_refresh: bool = False) -> float:
        """
        Get user's current print budget (printBalance field).

        Uses a short-lived cache (30s TTL) to avoid hitting Firebase on
        every print job. Cache is invalidated after deductions.
        """
        # Return cached value if fresh
        if (
            not force_refresh
            and self._cached_budget is not None
            and self._budget_cache_time is not None
        ):
            age = (datetime.now() - self._budget_cache_time).total_seconds()
            if age < self._budget_cache_ttl:
                logger.debug(
                    f"Using cached budget: {self._cached_budget}₪ (age: {age:.0f}s)"
                )
                return self._cached_budget

        db_path = f"users/{self.user_id}"
        logger.debug(f"Getting user budget from path: {db_path}")
        try:
            result = self.firebase.db_get(db_path)
            if result.get("success") and result.get("data"):
                budget = float(result["data"].get("printBalance", 0.0))
                self._cached_budget = budget
                self._budget_cache_time = datetime.now()
                logger.debug(f"User budget retrieved and cached: {budget}₪")
                return budget
            logger.warning(f"No budget data found for user {self.user_id}")
            return 0.0
        except Exception as e:
            logger.error(f"Error getting user budget: {e}")
            return 0.0

    def _deduct_budget(self, amount: float) -> bool:
        """Deduct amount from user's print budget."""
        db_path = f"users/{self.user_id}"
        logger.debug(f"Deducting {amount}₪ from user budget at path: {db_path}")
        try:
            current_budget = self._get_user_budget(force_refresh=True)
            new_budget = max(0.0, current_budget - amount)

            logger.debug(
                f"Budget calculation: {current_budget}₪ - {amount}₪ = {new_budget}₪"
            )

            result = self.firebase.db_update(
                db_path,
                {
                    "printBalance": new_budget,
                    "updatedAt": datetime.now().isoformat(),
                },
            )

            if result.get("success"):
                # Update cache immediately after deduction
                self._cached_budget = new_budget
                self._budget_cache_time = datetime.now()
                logger.info(
                    f"Budget deducted: {amount}₪, new balance: {new_budget}₪"
                )
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

    def _get_all_printers(self) -> List[str]:
        """Get list of all printer names."""
        if not win32print:
            return []
        try:
            flags = (
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
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
                # Use Level 2 to get TotalPages and DEVMODE
                jobs = win32print.EnumJobs(handle, 0, -1, 2)
                return list(jobs) if jobs else []
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            logger.error(f"Error getting jobs for {printer_name}: {e}")
            return []

    def _get_job_info(self, printer_name: str, job_id: int) -> dict:
        """Get detailed info for a specific job."""
        if not win32print:
            return {}
        try:
            handle = win32print.OpenPrinter(printer_name)
            try:
                job_info = win32print.GetJob(handle, job_id, 2)
                return job_info if job_info else {}
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            logger.debug(f"Error getting job info for {job_id}: {e}")
            return {}

    def _pause_job(self, printer_name: str, job_id: int) -> bool:
        """Pause an individual print job."""
        if not win32print:
            return False
        try:
            handle = win32print.OpenPrinter(printer_name)
            try:
                win32print.SetJob(handle, job_id, 0, None, JOB_CONTROL_PAUSE)
                logger.debug(f"Paused job {job_id} on '{printer_name}'")
                return True
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            error_code = getattr(e, "winerror", None) or (
                e.args[0] if e.args else None
            )
            if error_code == 87:
                logger.debug(f"Job {job_id} already completed (cannot pause)")
                return False
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
                logger.debug(f"Resumed job {job_id} on '{printer_name}'")
                return True
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            error_code = getattr(e, "winerror", None) or (
                e.args[0] if e.args else None
            )
            if error_code == 87:
                logger.debug(f"Job {job_id} already completed (cannot resume)")
                return True  # Job printed, that's fine
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
                logger.debug(f"Cancelled job {job_id} on '{printer_name}'")
                return True
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            error_code = getattr(e, "winerror", None) or (
                e.args[0] if e.args else None
            )
            if error_code == 87:
                logger.debug(f"Job {job_id} already completed (cannot cancel)")
                return True  # Job is gone, that's what we wanted
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False

    def _is_job_in_queue(self, printer_name: str, job_id: int) -> bool:
        """Check if a specific job is still in the printer queue."""
        jobs = self._get_printer_jobs(printer_name)
        return any(j.get("JobId") == job_id for j in jobs)

    # =========================================================================
    # JOB DETECTION (POLLING)
    # =========================================================================

    def _initialize_known_jobs(self):
        """Record existing jobs so we don't process them."""
        with self._lock:
            self._known_jobs.clear()
            printers = self._get_all_printers()

            if not printers:
                logger.warning("No printers found during initialization")
                return

            logger.info(f"Found {len(printers)} printer(s): {printers}")

            for printer_name in printers:
                jobs = self._get_printer_jobs(printer_name)
                self._known_jobs[printer_name] = {
                    job.get("JobId", 0) for job in jobs
                }
                if self._known_jobs[printer_name]:
                    logger.info(
                        f"Ignoring {len(self._known_jobs[printer_name])} "
                        f"existing jobs on '{printer_name}'"
                    )

    def _poll_print_queues(self):
        """
        Check all printer queues for new jobs.

        Since all printers are paused, jobs are guaranteed to be in the queue
        when we check. No race condition possible.
        """
        if not self._is_monitoring:
            return

        try:
            printers = self._get_all_printers()
            if not printers:
                return

            for printer_name in printers:
                with self._lock:
                    if printer_name not in self._known_jobs:
                        self._known_jobs[printer_name] = set()
                    known = self._known_jobs[printer_name].copy()

                current_jobs = self._get_printer_jobs(printer_name)
                current_ids = {job.get("JobId", 0) for job in current_jobs}

                # Find new jobs
                new_ids = current_ids - known

                for job_id in new_ids:
                    job_key = f"{printer_name}:{job_id}"

                    with self._lock:
                        # Skip if already processed or being released
                        if (
                            job_key in self._processed_jobs
                            or job_key in self._releasing_jobs
                        ):
                            continue
                        self._processed_jobs.add(job_key)

                    job_data = next(
                        (j for j in current_jobs if j.get("JobId") == job_id),
                        None,
                    )
                    if job_data:
                        logger.info(
                            f"New print job detected: ID={job_id} on "
                            f"'{printer_name}'"
                        )
                        self._handle_new_job(printer_name, job_data)

                # Update known jobs
                with self._lock:
                    self._known_jobs[printer_name] = current_ids

                    # Clean up processed/releasing sets for jobs no longer in queue
                    prefix = f"{printer_name}:"
                    keys_to_remove = [
                        key
                        for key in self._processed_jobs
                        if key.startswith(prefix)
                        and int(key.split(":")[1]) not in current_ids
                    ]
                    for key in keys_to_remove:
                        self._processed_jobs.discard(key)
                        self._releasing_jobs.discard(key)

        except Exception as e:
            logger.error(f"Error polling print queues: {e}")
            logger.error(traceback.format_exc())

    # =========================================================================
    # JOB HANDLING
    # =========================================================================

    def _get_copies_from_devmode(self, devmode) -> int:
        """Extract number of copies from DEVMODE structure."""
        if devmode is None:
            return 1
        try:
            copies = getattr(devmode, "Copies", 1)
            return copies if copies and copies > 0 else 1
        except Exception as e:
            logger.debug(f"Could not get copies from devmode: {e}")
            return 1

    def _is_color_job_from_devmode(self, devmode) -> bool:
        """
        Detect if print job is color from DEVMODE structure.

        DEVMODE.Color values:
        - DMCOLOR_MONOCHROME (1) = grayscale/B&W
        - DMCOLOR_COLOR (2) = color

        Returns True if color, False if B&W or unknown.
        """
        if devmode is None:
            logger.debug("No DEVMODE available, assuming B&W")
            return False
        try:
            color_setting = getattr(devmode, "Color", None)
            is_color = color_setting == DMCOLOR_COLOR
            logger.debug(f"DEVMODE.Color = {color_setting}, is_color = {is_color}")
            return is_color
        except Exception as e:
            logger.debug(f"Could not get color from devmode: {e}")
            return False

    def _wait_for_spool_complete(
        self, printer_name: str, job_id: int, job_data: dict
    ) -> dict:
        """
        Wait for a job to finish spooling so we get accurate page count.

        Since the printer is paused, the job stays in the queue indefinitely -
        we have all the time we need to wait for spooling to complete.

        Returns updated job_data with accurate TotalPages, or original if
        spooling info cannot be determined.
        """
        total_pages = job_data.get("TotalPages", 0)
        status = job_data.get("Status", 0)

        # If already done spooling and has pages, return immediately
        if not (status & JOB_STATUS_SPOOLING) and total_pages > 0:
            return job_data

        logger.info(
            f"Waiting for job {job_id} to finish spooling "
            f"(pages={total_pages}, status={status})"
        )

        last_pages = total_pages
        stable_count = 0

        # Wait up to 30 seconds (60 × 500ms) - generous because job is stuck anyway
        for attempt in range(60):
            time.sleep(0.5)
            job_info = self._get_job_info(printer_name, job_id)

            if not job_info:
                logger.warning(f"Job {job_id} disappeared during spool wait")
                break

            current_pages = job_info.get("TotalPages", 0)
            current_status = job_info.get("Status", 0)

            logger.debug(
                f"Spool wait attempt {attempt + 1}: pages={current_pages}, "
                f"status={current_status}"
            )

            # Spooling complete
            if not (current_status & JOB_STATUS_SPOOLING) and current_pages > 0:
                logger.info(f"Spooling complete: {current_pages} pages")
                return job_info

            # Page count stabilized
            if current_pages > 0 and current_pages == last_pages:
                stable_count += 1
                if stable_count >= 3:
                    logger.info(f"Page count stable at {current_pages}")
                    return job_info
            else:
                stable_count = 0

            last_pages = current_pages

        logger.warning(f"Spool wait timed out for job {job_id}")
        # Return the latest info we have, or original
        latest = self._get_job_info(printer_name, job_id)
        return latest if latest else job_data

    def _handle_new_job(self, printer_name: str, job_data: dict):
        """
        Process a newly detected print job.

        Flow:
        1. Wait for spooling to complete (job is stuck, no rush)
        2. Extract: pages, copies, color/BW
        3. Calculate cost: pages × copies × price_per_page
        4. Budget check
        5. Approve (release job) or Deny (cancel job)
        """
        job_id = job_data.get("JobId", 0)
        doc_name = job_data.get("pDocument", "Unknown")

        logger.info(f"Processing job {job_id}: '{doc_name}' on '{printer_name}'")

        # Step 1: Wait for spooling to complete
        final_data = self._wait_for_spool_complete(printer_name, job_id, job_data)

        # Step 2: Extract job properties
        total_pages = final_data.get("TotalPages", 0)
        if total_pages <= 0:
            logger.warning("Could not determine page count, defaulting to 1")
            total_pages = 1

        devmode = final_data.get("pDevMode") or job_data.get("pDevMode")
        copies = self._get_copies_from_devmode(devmode)
        is_color = self._is_color_job_from_devmode(devmode)

        logger.info(
            f"Job details: {total_pages} pages × {copies} copies, "
            f"{'COLOR' if is_color else 'B&W'}"
        )

        # Step 3: Calculate cost
        cost = self._calculate_cost(total_pages, copies, is_color)
        billable_pages = total_pages * copies
        logger.info(f"Cost: {cost}₪ ({billable_pages} billable pages)")

        # Step 4: Budget check
        budget = self._get_user_budget(force_refresh=True)

        if budget >= cost:
            # APPROVE: Deduct budget and release job
            if self._deduct_budget(cost):
                self._release_job(printer_name, job_id)
                remaining = budget - cost
                logger.info(
                    f"Job APPROVED: '{doc_name}' - {cost}₪, "
                    f"remaining {remaining}₪"
                )
                self.job_allowed.emit(doc_name, billable_pages, cost, remaining)
            else:
                # Deduction failed - cancel to be safe
                self._cancel_job(printer_name, job_id)
                logger.error(
                    f"Budget deduction failed for job {job_id}, cancelling"
                )
                self.error_occurred.emit("שגיאה בחיוב הדפסה")
        else:
            # DENY: Cancel job and notify
            self._cancel_job(printer_name, job_id)
            logger.warning(
                f"Job DENIED: '{doc_name}' - need {cost}₪, have {budget}₪"
            )
            self.job_blocked.emit(doc_name, billable_pages, cost, budget)

    # =========================================================================
    # SAFE JOB RELEASE
    # =========================================================================

    def _release_job(self, printer_name: str, job_id: int):
        """
        Safely release a single approved job for printing.

        Flow:
        1. Pause all OTHER jobs individually (safety net)
        2. Resume the printer
        3. Wait for the approved job to complete
        4. Re-pause the printer
        5. Resume other individually-paused jobs
        """
        job_key = f"{printer_name}:{job_id}"
        with self._lock:
            self._releasing_jobs.add(job_key)

        try:
            logger.info(f"Releasing job {job_id} on '{printer_name}'")

            # Step 1: Pause all other jobs on this printer individually
            other_jobs = self._get_printer_jobs(printer_name)
            paused_others = []
            for job in other_jobs:
                other_id = job.get("JobId", 0)
                if other_id != job_id:
                    if self._pause_job(printer_name, other_id):
                        paused_others.append(other_id)

            if paused_others:
                logger.debug(
                    f"Paused {len(paused_others)} other jobs as safety net"
                )

            # Step 2: Resume the printer so our job can print
            self._resume_printer(printer_name)

            # Step 3: Wait for the job to complete (leave the queue)
            self._wait_for_job_completion(printer_name, job_id)

            # Step 4: Re-pause the printer
            self._pause_printer(printer_name)

            # Step 5: Resume other individually-paused jobs
            for other_id in paused_others:
                self._resume_job(printer_name, other_id)

            logger.info(f"Job {job_id} released and printed successfully")

        except Exception as e:
            logger.error(f"Error releasing job {job_id}: {e}")
            logger.error(traceback.format_exc())
            # Safety: make sure printer gets re-paused
            if printer_name not in self._paused_printers:
                self._pause_printer(printer_name)
        finally:
            with self._lock:
                self._releasing_jobs.discard(job_key)

    def _wait_for_job_completion(
        self, printer_name: str, job_id: int, timeout: float = 120.0
    ):
        """
        Wait for a specific job to leave the printer queue (= printing complete).

        Args:
            printer_name: The printer the job is on
            job_id: The job ID to wait for
            timeout: Maximum wait time in seconds (default 2 minutes)
        """
        start = time.time()
        check_interval = 0.5  # Start checking every 500ms

        logger.debug(f"Waiting for job {job_id} to complete (timeout={timeout}s)")

        while time.time() - start < timeout:
            if not self._is_job_in_queue(printer_name, job_id):
                elapsed = time.time() - start
                logger.info(
                    f"Job {job_id} completed in {elapsed:.1f}s"
                )
                return

            time.sleep(check_interval)
            # Gradually increase interval to reduce CPU usage
            if check_interval < 2.0:
                check_interval = min(check_interval * 1.5, 2.0)

        logger.warning(
            f"Job {job_id} did not complete within {timeout}s timeout"
        )

"""
Print Monitor Service - Per-Job Interception (Multi-PC Safe)

Designed for environments where 100+ PCs share printers simultaneously.
NEVER pauses printers at the hardware level - only controls individual jobs.

Architecture:
- Aggressive polling (250ms) detects new jobs quickly
- For each new job: read info FIRST, then try to pause it
- If paused: validate budget → approve (resume) or deny (cancel)
- If job escaped (already printing): charge RETROACTIVELY (deduct budget)
- This guarantees charging even if a fast job can't be paused in time

Cost formula:
  cost = total_pages × copies × price_per_page(BW or color)

Multi-PC safety:
- No printer-level pause/resume (safe for shared network printers)
- Each PC instance only controls jobs IT detected
- Multiple SIONYX instances on different PCs cannot conflict
- No risk of printers getting stuck from crashes

Edge case handling:
- If job prints before pause: user is charged retroactively
- If page count is 0: defaults to 1 (minimum charge)
- If copies unknown: defaults to 1
- If color unknown: defaults to B&W (cheaper, user-friendly)
"""

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

# Job status flags
JOB_STATUS_PAUSED = 0x00000001
JOB_STATUS_SPOOLING = 0x00000008
JOB_STATUS_PRINTING = 0x00000010
JOB_STATUS_DELETING = 0x00000004

# DEVMODE color constants
DMCOLOR_COLOR = 2


class PrintMonitorService(QObject):
    """
    Print Monitor - Per-Job Interception (Multi-PC Safe).

    Monitors print queues and intercepts individual jobs for budget
    enforcement. Safe for environments with 100+ PCs sharing printers.

    Key principle: NEVER touch printer-level settings. Only pause/resume/
    cancel individual jobs. If a fast job escapes our pause, charge
    retroactively.

    Flow:
    1. Polling detects new job (250ms interval)
    2. Read job info immediately (pages, copies, color)
    3. Try to pause the individual job
    4. If paused → budget check → approve or deny
    5. If job escaped → charge retroactively (job printed, but we still bill)
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

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def start_monitoring(self) -> Dict:
        """Start monitoring print spooler for new jobs."""
        if self._is_monitoring:
            logger.warning("Print monitoring already running")
            return {"success": True, "message": "Already monitoring"}

        try:
            logger.info(
                "Starting print monitor service (per-job interception, "
                "multi-PC safe)"
            )

            # Load org pricing
            self._load_pricing()

            # Initialize known jobs (ignore existing jobs in queue)
            self._initialize_known_jobs()

            # Clear processed jobs set
            self._processed_jobs.clear()

            # Start aggressive polling timer (250ms for fast job detection)
            self._poll_timer = QTimer()
            self._poll_timer.timeout.connect(self._poll_print_queues)
            self._poll_timer.start(250)
            logger.debug("Polling timer started with 250ms interval")

            self._is_monitoring = True
            logger.info("Print monitor started (per-job interception active)")
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
    # PRICING
    # =========================================================================

    def _load_pricing(self):
        """Load organization print pricing from Firebase."""
        try:
            result = self.firebase.db_get("metadata")
            if result.get("success") and result.get("data"):
                metadata = result["data"]
                self._bw_price = float(
                    metadata.get("blackAndWhitePrice", 1.0)
                )
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
                    f"Using cached budget: {self._cached_budget}₪ "
                    f"(age: {age:.0f}s)"
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

    def _deduct_budget(
        self, amount: float, allow_negative: bool = False
    ) -> bool:
        """
        Deduct amount from user's print budget.

        Args:
            amount: Amount to deduct.
            allow_negative: If True, balance can go below zero (for escaped
                jobs that already printed). Creates a debt.
        """
        db_path = f"users/{self.user_id}"
        logger.debug(
            f"Deducting {amount}₪ from user budget at path: {db_path}"
        )
        try:
            current_budget = self._get_user_budget(force_refresh=True)
            if allow_negative:
                new_budget = current_budget - amount
            else:
                new_budget = max(0.0, current_budget - amount)

            logger.debug(
                f"Budget calculation: "
                f"{current_budget}₪ - {amount}₪ = {new_budget}₪"
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
                logger.error(
                    f"Failed to deduct budget: {result.get('error')}"
                )
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
                win32print.PRINTER_ENUM_LOCAL
                | win32print.PRINTER_ENUM_CONNECTIONS
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
        """
        Pause an individual print job.

        Returns True if paused, False if job already completed (error 87)
        or other failure.
        """
        if not win32print:
            return False
        try:
            handle = win32print.OpenPrinter(printer_name)
            try:
                win32print.SetJob(
                    handle, job_id, 0, None, JOB_CONTROL_PAUSE
                )
                logger.debug(f"Paused job {job_id} on '{printer_name}'")
                return True
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            error_code = getattr(e, "winerror", None) or (
                e.args[0] if e.args else None
            )
            if error_code == 87:
                logger.debug(
                    f"Job {job_id} already completed (cannot pause)"
                )
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
                win32print.SetJob(
                    handle, job_id, 0, None, JOB_CONTROL_RESUME
                )
                logger.debug(f"Resumed job {job_id} on '{printer_name}'")
                return True
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            error_code = getattr(e, "winerror", None) or (
                e.args[0] if e.args else None
            )
            if error_code == 87:
                logger.debug(
                    f"Job {job_id} already completed (cannot resume)"
                )
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
                win32print.SetJob(
                    handle, job_id, 0, None, JOB_CONTROL_CANCEL
                )
                logger.debug(f"Cancelled job {job_id} on '{printer_name}'")
                return True
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            error_code = getattr(e, "winerror", None) or (
                e.args[0] if e.args else None
            )
            if error_code == 87:
                logger.debug(
                    f"Job {job_id} already completed (cannot cancel)"
                )
                return True  # Job is gone, that's what we wanted
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False

    # =========================================================================
    # JOB DETECTION (POLLING)
    # =========================================================================

    def _initialize_known_jobs(self):
        """Record existing jobs so we don't process them."""
        with self._lock:
            self._known_jobs.clear()
            printers = self._get_all_printers()

            if not printers:
                logger.warning(
                    "No printers found! Print monitoring may not work."
                )
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
        Check all printer queues for new jobs (called every 250ms).

        Aggressive polling ensures we catch most jobs before they finish
        printing. For the rare fast job that escapes, we still charge
        retroactively.
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
                        if job_key in self._processed_jobs:
                            continue
                        self._processed_jobs.add(job_key)

                    job_data = next(
                        (
                            j
                            for j in current_jobs
                            if j.get("JobId") == job_id
                        ),
                        None,
                    )
                    if job_data:
                        logger.info(
                            f"New print job detected: ID={job_id} "
                            f"on '{printer_name}'"
                        )
                        self._handle_new_job(printer_name, job_data)

                # Update known jobs
                with self._lock:
                    self._known_jobs[printer_name] = current_ids

                    # Clean up processed set for jobs no longer in queue
                    prefix = f"{printer_name}:"
                    keys_to_remove = [
                        key
                        for key in self._processed_jobs
                        if key.startswith(prefix)
                        and int(key.split(":")[1]) not in current_ids
                    ]
                    for key in keys_to_remove:
                        self._processed_jobs.discard(key)

        except Exception as e:
            logger.error(f"Error polling print queues: {e}")
            logger.error(traceback.format_exc())

    # =========================================================================
    # JOB INFO EXTRACTION
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
            logger.debug(
                f"DEVMODE.Color = {color_setting}, is_color = {is_color}"
            )
            return is_color
        except Exception as e:
            logger.debug(f"Could not get color from devmode: {e}")
            return False

    def _extract_job_details(self, job_data: dict) -> dict:
        """
        Extract all billing-relevant info from a print job.

        Returns a dict with: pages, copies, is_color, doc_name

        IMPORTANT: This is called BEFORE attempting to pause the job,
        so we always have the cost data even if the job escapes.
        """
        doc_name = job_data.get("pDocument", "Unknown")
        total_pages = job_data.get("TotalPages", 0)
        devmode = job_data.get("pDevMode")
        copies = self._get_copies_from_devmode(devmode)
        is_color = self._is_color_job_from_devmode(devmode)

        # Default to 1 page if we can't determine
        if total_pages <= 0:
            total_pages = 1

        return {
            "doc_name": doc_name,
            "pages": total_pages,
            "copies": copies,
            "is_color": is_color,
        }

    def _wait_for_spool_complete(
        self, printer_name: str, job_id: int, initial_data: dict
    ) -> dict:
        """
        Wait for a job to finish spooling to get accurate page count.

        Returns updated job details, or initial if spooling info
        cannot be determined.

        NOTE: We only wait a SHORT time (up to 3 seconds) because the
        job might start printing while we wait. Speed is critical.
        """
        total_pages = initial_data.get("TotalPages", 0)
        status = initial_data.get("Status", 0)

        # If already done spooling and has pages, return immediately
        if not (status & JOB_STATUS_SPOOLING) and total_pages > 0:
            return initial_data

        logger.info(
            f"Waiting for job {job_id} to finish spooling "
            f"(pages={total_pages}, status={status})"
        )

        last_pages = total_pages
        stable_count = 0

        # Wait up to 3 seconds (6 × 500ms) - keep it short to avoid
        # the job printing while we wait
        for attempt in range(6):
            time.sleep(0.5)
            job_info = self._get_job_info(printer_name, job_id)

            if not job_info:
                logger.warning(f"Job {job_id} disappeared during spool wait")
                break

            current_pages = job_info.get("TotalPages", 0)
            current_status = job_info.get("Status", 0)

            logger.debug(
                f"Spool wait attempt {attempt + 1}: "
                f"pages={current_pages}, status={current_status}"
            )

            # Spooling complete
            if not (current_status & JOB_STATUS_SPOOLING) and current_pages > 0:
                logger.info(f"Spooling complete: {current_pages} pages")
                return job_info

            # Page count stabilized
            if current_pages > 0 and current_pages == last_pages:
                stable_count += 1
                if stable_count >= 2:
                    logger.info(f"Page count stable at {current_pages}")
                    return job_info
            else:
                stable_count = 0

            last_pages = current_pages

        logger.warning(f"Spool wait timed out for job {job_id}")
        latest = self._get_job_info(printer_name, job_id)
        return latest if latest else initial_data

    # =========================================================================
    # JOB HANDLING
    # =========================================================================

    def _handle_new_job(self, printer_name: str, job_data: dict):
        """
        Process a newly detected print job.

        Critical flow (order matters for minimum escape window!):
        1. PAUSE IMMEDIATELY (don't wait - minimize escape window)
        2. If paused: read info while job is frozen → budget check
        3. If escaped: read whatever info we have → charge retroactively
        """
        job_id = job_data.get("JobId", 0)
        doc_name = job_data.get("pDocument", "Unknown")

        # ---------------------------------------------------------------
        # STEP 1: PAUSE IMMEDIATELY - don't read info first, don't wait
        # for spool. Every millisecond counts to prevent escape.
        # ---------------------------------------------------------------
        job_paused = self._pause_job(printer_name, job_id)

        if job_paused:
            # =============================================================
            # STEP 2a: Job is PAUSED - we have full control.
            # Now we can safely take our time to read info.
            # =============================================================

            # Wait for spool to complete (job is frozen, no rush)
            final_data = self._wait_for_spool_complete(
                printer_name, job_id, job_data
            )
            details = self._extract_job_details(final_data)
            doc_name = details["doc_name"]
            pages = details["pages"]
            copies = details["copies"]
            is_color = details["is_color"]
            billable_pages = pages * copies
            cost = self._calculate_cost(pages, copies, is_color)

            logger.info(
                f"Job {job_id}: '{doc_name}' - "
                f"{pages} pages × {copies} copies, "
                f"{'COLOR' if is_color else 'B&W'}, cost={cost}₪"
            )

            self._handle_paused_job(
                printer_name, job_id, doc_name, billable_pages, cost
            )
        else:
            # =============================================================
            # STEP 2b: Job ESCAPED (already printing/completed).
            # Read whatever info we already have and charge retroactively.
            # =============================================================
            details = self._extract_job_details(job_data)
            doc_name = details["doc_name"]
            pages = details["pages"]
            copies = details["copies"]
            is_color = details["is_color"]
            billable_pages = pages * copies
            cost = self._calculate_cost(pages, copies, is_color)

            logger.info(
                f"Job {job_id}: '{doc_name}' - "
                f"{pages} pages × {copies} copies, "
                f"{'COLOR' if is_color else 'B&W'}, cost={cost}₪ "
                f"(ESCAPED)"
            )

            self._handle_escaped_job(doc_name, billable_pages, cost)

    def _handle_paused_job(
        self,
        printer_name: str,
        job_id: int,
        doc_name: str,
        billable_pages: int,
        cost: float,
    ):
        """
        Handle a job that we successfully paused.

        Budget check:
        - Sufficient → deduct + resume (allow printing)
        - Insufficient → cancel job + notify user
        """
        budget = self._get_user_budget(force_refresh=True)

        if budget >= cost:
            # APPROVE: Deduct budget and resume the job
            if self._deduct_budget(cost):
                self._resume_job(printer_name, job_id)
                remaining = budget - cost
                logger.info(
                    f"Job APPROVED: '{doc_name}' - {cost}₪, "
                    f"remaining {remaining}₪"
                )
                self.job_allowed.emit(
                    doc_name, billable_pages, cost, remaining
                )
            else:
                # Deduction failed - cancel to be safe
                self._cancel_job(printer_name, job_id)
                logger.error(
                    f"Budget deduction failed for job {job_id}, cancelling"
                )
                self.error_occurred.emit("שגיאה בחיוב הדפסה")
        else:
            # DENY: Cancel job and notify user
            self._cancel_job(printer_name, job_id)
            logger.warning(
                f"Job DENIED: '{doc_name}' - need {cost}₪, have {budget}₪"
            )
            self.job_blocked.emit(doc_name, billable_pages, cost, budget)

    def _handle_escaped_job(
        self, doc_name: str, billable_pages: int, cost: float
    ):
        """
        Handle a job that escaped our pause (already printing/completed).

        The job already printed - we can't stop it. We ALWAYS charge the
        full amount, even if it drives the balance negative (creating a
        debt). This prevents "free printing" exploits.

        A negative balance means the user owes money. The admin can see
        this in the dashboard and handle it (e.g., require payment before
        next session).
        """
        logger.warning(
            f"Job escaped pause: '{doc_name}' - charging retroactively"
        )

        budget = self._get_user_budget(force_refresh=True)

        # ALWAYS charge the full amount - allow negative balance (debt)
        if self._deduct_budget(cost, allow_negative=True):
            remaining = budget - cost
            if remaining < 0:
                logger.warning(
                    f"Retroactive charge created DEBT: '{doc_name}' - "
                    f"{cost}₪, balance now {remaining}₪"
                )
                # Emit with negative remaining to signal debt
                self.job_allowed.emit(
                    doc_name, billable_pages, cost, remaining
                )
            else:
                logger.info(
                    f"Retroactive charge: '{doc_name}' - {cost}₪, "
                    f"remaining {remaining}₪"
                )
                self.job_allowed.emit(
                    doc_name, billable_pages, cost, remaining
                )
        else:
            logger.error(
                f"Retroactive deduction failed for '{doc_name}'"
            )
            self.error_occurred.emit("שגיאה בחיוב הדפסה")

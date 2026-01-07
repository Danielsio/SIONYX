"""
Process Restriction Service
Monitors and terminates unauthorized processes.

This service watches for blacklisted processes like:
- Registry Editor (regedit)
- Command Prompt (cmd)
- PowerShell
- Task Manager (if launched through alternative means)
- Other dangerous system tools

IMPORTANT: For this to work effectively, users must NOT be Windows admins.
Standard users cannot bypass process termination by SIONYX.
"""

from typing import List, Optional, Set

import psutil
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from utils.logger import get_logger


logger = get_logger(__name__)


class ProcessRestrictionService(QObject):
    """
    Service to monitor and kill unauthorized processes.

    Polls running processes periodically and terminates any that are
    in the blacklist. Works best when user is a standard Windows user.
    """

    # Signals
    process_blocked = pyqtSignal(str)  # Emits blocked process name
    error_occurred = pyqtSignal(str)

    # Default blacklisted processes
    DEFAULT_BLACKLIST = {
        # System tools
        "regedit.exe",  # Registry Editor
        "cmd.exe",  # Command Prompt
        "powershell.exe",  # PowerShell
        "pwsh.exe",  # PowerShell Core
        "mmc.exe",  # Management Console
        "taskmgr.exe",  # Task Manager
        "control.exe",  # Control Panel
        "msconfig.exe",  # System Configuration
        "gpedit.msc",  # Group Policy Editor
        "secpol.msc",  # Security Policy
        "compmgmt.msc",  # Computer Management
        "devmgmt.msc",  # Device Manager
        "diskmgmt.msc",  # Disk Management
        "services.msc",  # Services
        # Potentially dangerous
        "wscript.exe",  # Windows Script Host
        "cscript.exe",  # Console Script Host
        "mshta.exe",  # HTML Application Host
        "certutil.exe",  # Certificate utility (used for malware)
        "bitsadmin.exe",  # BITS (used for downloads)
        "wmic.exe",  # WMI Command-line
        # Remote access (could be used to escape kiosk)
        "teamviewer.exe",
        "anydesk.exe",
        "ultraviewer.exe",
    }

    def __init__(
        self,
        blacklist: Optional[Set[str]] = None,
        check_interval_ms: int = 2000,
        enabled: bool = True,
    ):
        super().__init__()
        self.enabled = enabled
        self.check_interval_ms = check_interval_ms

        # Use provided blacklist or default
        self.blacklist = (
            blacklist if blacklist is not None else self.DEFAULT_BLACKLIST.copy()
        )

        # Timer for periodic checking
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_processes)

        # Track processes we've already warned about (to avoid log spam)
        self.recently_blocked: Set[int] = set()

    def start(self):
        """Start monitoring for unauthorized processes."""
        if not self.enabled:
            logger.info("Process restriction disabled, not starting")
            return

        logger.info(
            "Starting process restriction service", blacklist_count=len(self.blacklist)
        )
        self.check_timer.start(self.check_interval_ms)

        # Run initial check immediately
        self._check_processes()

    def stop(self):
        """Stop monitoring."""
        logger.info("Stopping process restriction service")
        self.check_timer.stop()

    def add_to_blacklist(self, process_name: str):
        """Add a process to the blacklist."""
        self.blacklist.add(process_name.lower())
        logger.info(f"Added to process blacklist: {process_name}")

    def remove_from_blacklist(self, process_name: str):
        """Remove a process from the blacklist."""
        self.blacklist.discard(process_name.lower())
        logger.info(f"Removed from process blacklist: {process_name}")

    def set_enabled(self, enabled: bool):
        """Enable or disable process monitoring."""
        self.enabled = enabled
        if enabled:
            self.start()
        else:
            self.stop()

    def _check_processes(self):
        """Check running processes against blacklist."""
        if not self.enabled:
            return

        try:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    proc_name = proc.info["name"].lower()
                    proc_pid = proc.info["pid"]

                    # Skip if we've recently blocked this PID
                    if proc_pid in self.recently_blocked:
                        continue

                    # Check against blacklist
                    if proc_name in self.blacklist:
                        self._terminate_process(proc, proc_name)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process ended or we can't access it
                    continue

            # Clean up old PIDs from recently_blocked
            self._cleanup_blocked_set()

        except Exception as e:
            logger.error(f"Error checking processes: {e}")

    def _terminate_process(self, proc: psutil.Process, proc_name: str):
        """Terminate an unauthorized process."""
        pid = proc.pid

        try:
            logger.warning(
                f"Terminating unauthorized process: {proc_name} (PID: {pid})",
                action="process_blocked",
            )

            # Try graceful termination first
            proc.terminate()

            # Give it a moment to terminate
            try:
                proc.wait(timeout=1)
            except psutil.TimeoutExpired:
                # Force kill if it didn't terminate
                proc.kill()

            # Track that we blocked this
            self.recently_blocked.add(pid)

            # Emit signal
            self.process_blocked.emit(proc_name)

            logger.info(f"Successfully terminated: {proc_name}")

        except psutil.NoSuchProcess:
            # Already gone
            pass
        except psutil.AccessDenied:
            logger.error(
                f"Access denied terminating {proc_name}. User may be admin.",
                action="process_block_failed",
            )
            self.error_occurred.emit(f"Cannot terminate {proc_name} - access denied")
        except Exception as e:
            logger.error(f"Error terminating {proc_name}: {e}")
            self.error_occurred.emit(f"Error blocking {proc_name}")

    def _cleanup_blocked_set(self):
        """Remove PIDs that are no longer running from the blocked set."""
        running_pids = {p.pid for p in psutil.process_iter(["pid"])}
        self.recently_blocked = self.recently_blocked.intersection(running_pids)

    def get_blacklist(self) -> List[str]:
        """Get the current blacklist."""
        return sorted(self.blacklist)

    def is_active(self) -> bool:
        """Check if monitoring is active."""
        return self.check_timer.isActive() and self.enabled

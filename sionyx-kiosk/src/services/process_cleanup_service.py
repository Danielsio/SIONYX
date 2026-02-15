"""
Process Cleanup Service
Closes user programs when a new session starts.

This ensures a clean state for each customer in kiosk environments.
"""

import subprocess
import sys
import time
from typing import Dict, List

from utils.logger import get_logger


# Hide console window on Windows when spawning subprocesses (tasklist, taskkill)
_SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


logger = get_logger(__name__)


class ProcessCleanupService:
    """
    Service to close user programs before a new session starts.

    This provides a clean slate for each customer by closing:
    - Browsers (Chrome, Edge, Firefox, etc.)
    - Office applications (Word, Excel, etc.)
    - Media players (VLC, Windows Media Player, etc.)
    - Other user applications

    System processes and SIONYX are preserved.
    """

    # Processes that should NEVER be killed
    # These are essential for Windows and SIONYX to function
    WHITELIST = {
        # SIONYX
        "sionyx.exe",
        "python.exe",  # For development
        "pythonw.exe",
        # Windows core
        "system",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "winlogon.exe",
        "explorer.exe",
        "dwm.exe",
        "taskhostw.exe",
        "sihost.exe",
        "ctfmon.exe",
        "conhost.exe",
        "fontdrvhost.exe",
        "audiodg.exe",
        "runtimebroker.exe",
        "searchhost.exe",
        "startmenuexperiencehost.exe",
        "textinputhost.exe",
        "shellexperiencehost.exe",
        "applicationframehost.exe",
        "systemsettings.exe",
        "securityhealthservice.exe",
        "securityhealthsystray.exe",
        "msmpeng.exe",  # Windows Defender
        "nissrv.exe",
        "wuauclt.exe",
        "trustedinstaller.exe",
        "tiworker.exe",
        "dllhost.exe",
        "msiexec.exe",
        "spoolsv.exe",  # Print spooler
        "searchindexer.exe",
        "registry",
        "memory compression",
        "system idle process",
        # Drivers
        "igfxem.exe",
        "igfxhk.exe",
        "igfxtray.exe",
        "nvcontainer.exe",
        "nvidia share.exe",
        # Common utilities to keep
        "onedrive.exe",
        "settingsynchost.exe",
    }

    # Processes to specifically target for cleanup
    # These are common user applications
    TARGETS = {
        # Browsers
        "chrome.exe",
        "msedge.exe",
        "firefox.exe",
        "opera.exe",
        "brave.exe",
        "iexplore.exe",
        # Office
        "winword.exe",
        "excel.exe",
        "powerpnt.exe",
        "outlook.exe",
        "onenote.exe",
        "mspub.exe",
        "msaccess.exe",
        # Media
        "vlc.exe",
        "wmplayer.exe",
        "spotify.exe",
        "groove.exe",
        "movies & tv.exe",
        "itunes.exe",
        # Communication
        "teams.exe",
        "slack.exe",
        "discord.exe",
        "zoom.exe",
        "skype.exe",
        "telegram.exe",
        "whatsapp.exe",
        # File managers
        "totalcmd.exe",
        "doublecmd.exe",
        # Text editors
        "notepad.exe",
        "notepad++.exe",
        "wordpad.exe",
        "code.exe",  # VS Code
        # PDF readers
        "acrord32.exe",
        "acrobat.exe",
        "foxit reader.exe",
        # Image viewers
        "photos.exe",
        "mspaint.exe",
        "photoviewer.exe",
        # Games (common)
        "steam.exe",
        "epicgameslauncher.exe",
        # Misc
        "calculator.exe",
        "snippingtool.exe",
    }

    def __init__(self):
        """Initialize the process cleanup service."""
        self._cleanup_results: Dict[str, bool] = {}

    def cleanup_user_processes(self) -> Dict[str, any]:
        """
        Close all user processes that aren't in the whitelist.

        Returns:
            Dict with success status and details
        """
        logger.info("Starting user process cleanup for new session")

        closed_count = 0
        failed_count = 0
        closed_processes = []
        failed_processes = []

        # Get list of running processes
        running_processes = self._get_running_processes()

        # Stubborn processes that need special handling (kill by name first)
        stubborn_processes = {"discord.exe", "teams.exe", "slack.exe", "zoom.exe"}

        for process_name, pids in running_processes.items():
            process_lower = process_name.lower()

            # Skip whitelisted processes
            if process_lower in self.WHITELIST:
                continue

            # Only kill if it's a known target
            if process_lower in self.TARGETS:
                # For stubborn processes, try kill by name first (more effective)
                if process_lower in stubborn_processes:
                    success = self._kill_by_name(process_name)
                    if success:
                        closed_count += len(pids)
                        if process_name not in closed_processes:
                            closed_processes.append(process_name)
                    else:
                        failed_count += len(pids)
                        if process_name not in failed_processes:
                            failed_processes.append(process_name)
                else:
                    # Regular kill by PID with retry
                    for pid in pids:
                        success = self._kill_process(pid, process_name)
                        if success:
                            closed_count += 1
                            if process_name not in closed_processes:
                                closed_processes.append(process_name)
                        else:
                            failed_count += 1
                            if process_name not in failed_processes:
                                failed_processes.append(process_name)

        result = {
            "success": failed_count == 0,
            "closed_count": closed_count,
            "failed_count": failed_count,
            "closed_processes": closed_processes,
            "failed_processes": failed_processes,
        }

        if closed_count > 0:
            logger.info(
                f"Process cleanup complete: {closed_count} processes closed",
                closed=closed_processes,
            )
        else:
            logger.info("No user processes found to clean up")

        if failed_count > 0:
            logger.warning(
                f"Failed to close {failed_count} processes",
                failed=failed_processes,
            )

        return result

    def _get_running_processes(self) -> Dict[str, List[int]]:
        """
        Get list of currently running processes.

        Returns:
            Dict mapping process name to list of PIDs
        """
        processes: Dict[str, List[int]] = {}

        try:
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=_SUBPROCESS_FLAGS,
            )

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                # Parse CSV format: "process.exe","1234","Console","1","10,000 K"
                parts = line.split(",")
                if len(parts) >= 2:
                    # Remove quotes
                    name = parts[0].strip('"')
                    try:
                        pid = int(parts[1].strip('"'))
                        if name not in processes:
                            processes[name] = []
                        processes[name].append(pid)
                    except ValueError:
                        continue

        except subprocess.TimeoutExpired:
            logger.warning("Timeout getting process list")
        except Exception as e:
            logger.error(f"Error getting process list: {e}")

        return processes

    def _kill_process(self, pid: int, name: str, retry_count: int = 2) -> bool:
        """
        Kill a process by PID with retry logic.

        Uses /F (force) and /T (tree - kill child processes) flags.
        Retries on failure to handle stubborn processes like Discord.

        Args:
            pid: Process ID
            name: Process name (for logging)
            retry_count: Number of retries on failure (default 2)

        Returns:
            True if successfully killed
        """
        for attempt in range(retry_count + 1):
            try:
                # Use /F (force) and /T (tree - kill child processes)
                result = subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F", "/T"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=_SUBPROCESS_FLAGS,
                )

                if result.returncode == 0:
                    logger.debug(f"Killed process: {name} (PID: {pid})")
                    return True
                else:
                    # Check if process no longer exists (already dead)
                    if "not found" in result.stderr.lower():
                        logger.debug(f"Process already terminated: {name} (PID: {pid})")
                        return True

                    if attempt < retry_count:
                        logger.debug(
                            f"Retry {attempt + 1}/{retry_count} for {name}: {result.stderr.strip()}"
                        )
                        time.sleep(0.2)  # Brief delay before retry
                    else:
                        logger.debug(
                            f"Failed to kill {name} after {retry_count + 1} attempts"
                        )
                        return False

            except subprocess.TimeoutExpired:
                logger.warning(f"Timeout killing process: {name}")
                if attempt == retry_count:
                    return False
                time.sleep(0.2)
            except Exception as e:
                logger.error(f"Error killing process {name}: {e}")
                return False

        return False

    def _kill_by_name(self, process_name: str) -> bool:
        """
        Kill all instances of a process by name.

        This is more effective for stubborn processes like Discord
        that have multiple PIDs. Kills all at once.

        Args:
            process_name: Process name (e.g., "Discord.exe")

        Returns:
            True if successfully killed
        """
        try:
            result = subprocess.run(
                ["taskkill", "/IM", process_name, "/F", "/T"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=_SUBPROCESS_FLAGS,
            )

            if result.returncode == 0:
                logger.debug(f"Killed all instances of: {process_name}")
                return True
            elif "not found" in result.stderr.lower():
                logger.debug(f"Process not running: {process_name}")
                return True
            else:
                logger.debug(
                    f"Failed to kill by name {process_name}: {result.stderr.strip()}"
                )
                return False

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout killing process by name: {process_name}")
            return False
        except Exception as e:
            logger.error(f"Error killing process by name {process_name}: {e}")
            return False

    def close_browsers_only(self) -> Dict[str, any]:
        """
        Close only browser processes.

        This is a lighter-weight option that only closes browsers
        without affecting other applications.

        Returns:
            Dict with success status and details
        """
        logger.info("Closing browser processes only")

        browser_processes = {
            "chrome.exe",
            "msedge.exe",
            "firefox.exe",
            "opera.exe",
            "brave.exe",
            "iexplore.exe",
        }

        closed_count = 0
        running = self._get_running_processes()

        for process_name, pids in running.items():
            if process_name.lower() in browser_processes:
                for pid in pids:
                    if self._kill_process(pid, process_name):
                        closed_count += 1

        return {"success": True, "closed_count": closed_count}

    def is_process_running(self, process_name: str) -> bool:
        """
        Check if a specific process is running.

        Args:
            process_name: Name of the process (e.g., "chrome.exe")

        Returns:
            True if the process is running
        """
        running = self._get_running_processes()
        return process_name.lower() in {k.lower() for k in running.keys()}

    def get_running_user_processes(self) -> List[str]:
        """
        Get list of running user processes (non-system).

        Returns:
            List of process names
        """
        running = self._get_running_processes()
        user_processes = []

        for name in running.keys():
            if name.lower() not in self.WHITELIST:
                user_processes.append(name)

        return user_processes

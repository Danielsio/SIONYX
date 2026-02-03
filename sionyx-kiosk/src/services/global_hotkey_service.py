"""
Global Hotkey Service
Handles system-wide hotkeys that work even when the app is not in focus
"""

import os
import threading

import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

from utils.logger import get_logger
from utils.const import ADMIN_EXIT_HOTKEY_DEFAULT
from utils.registry_config import is_production, read_registry_value


logger = get_logger(__name__)


class GlobalHotkeyService(QObject):
    """Service for handling global hotkeys"""

    # Signals
    admin_exit_requested = pyqtSignal()  # Emits when admin exit hotkey is pressed

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.hotkey_thread = None
        self.admin_exit_hotkey = self._resolve_admin_exit_hotkey()

    def start(self):
        """Start listening for global hotkeys"""
        if self.is_running:
            logger.warning("Global hotkey service is already running")
            return

        logger.info(
            "Starting global hotkey service",
            hotkeys=self._get_admin_exit_hotkeys(),
        )
        self.is_running = True

        # Start hotkey listener in a separate thread
        self.hotkey_thread = threading.Thread(
            target=self._listen_for_hotkeys, daemon=True
        )
        self.hotkey_thread.start()

    def stop(self):
        """Stop listening for global hotkeys"""
        if not self.is_running:
            return

        logger.info("Stopping global hotkey service")
        self.is_running = False

        # Unhook all hotkeys
        try:
            keyboard.unhook_all()
        except Exception as e:
            logger.warning(f"Error unhooking hotkeys: {e}")

    def _listen_for_hotkeys(self):
        """Listen for global hotkeys in a separate thread"""
        try:
            # Register global hotkeys for admin exit (configurable + legacy)
            for hotkey in self._get_admin_exit_hotkeys():
                keyboard.add_hotkey(hotkey, self._on_admin_exit_hotkey)

            # Keep the thread alive
            while self.is_running:
                keyboard.wait()

        except Exception as e:
            logger.error(f"Error in global hotkey listener: {e}")
        finally:
            logger.info("Global hotkey listener thread ended")

    def _on_admin_exit_hotkey(self):
        """Handle admin exit hotkey press"""
        logger.info("Global admin exit hotkey pressed")
        self.admin_exit_requested.emit()

    def _resolve_admin_exit_hotkey(self) -> str:
        """Resolve admin exit hotkey from config with sane defaults."""
        hotkey = None
        if is_production():
            hotkey = read_registry_value("AdminExitHotkey")
        if not hotkey:
            hotkey = os.getenv("ADMIN_EXIT_HOTKEY")
        hotkey = (hotkey or ADMIN_EXIT_HOTKEY_DEFAULT).strip().lower().replace(" ", "")
        return hotkey or ADMIN_EXIT_HOTKEY_DEFAULT

    def _get_admin_exit_hotkeys(self) -> list[str]:
        """Return primary + legacy admin exit hotkeys."""
        hotkeys = [self.admin_exit_hotkey, "ctrl+alt+q"]
        unique_hotkeys = []
        for hotkey in hotkeys:
            if hotkey not in unique_hotkeys:
                unique_hotkeys.append(hotkey)
        return unique_hotkeys

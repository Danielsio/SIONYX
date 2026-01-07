"""
Keyboard Restriction Service
Blocks dangerous system keys to prevent users from escaping kiosk mode.

Blocks:
- Alt+Tab (window switching)
- Alt+F4 (close window)
- Windows key (Start menu)
- Ctrl+Shift+Esc (Task Manager)
- Ctrl+Alt+Del handled by Group Policy (cannot be blocked by apps)

IMPORTANT: This is a software layer. For true security, also use:
1. Standard Windows user accounts (not admin)
2. Group Policy restrictions
3. AppLocker / Software Restriction Policies
"""

import ctypes
import threading
from ctypes import wintypes
from typing import Callable, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from utils.logger import get_logger


logger = get_logger(__name__)

# Windows API constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

VK_TAB = 0x09
VK_ESCAPE = 0x1B
VK_F4 = 0x73
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_DELETE = 0x2E

# Modifier key states
VK_MENU = 0x12  # Alt key
VK_CONTROL = 0x11  # Ctrl key
VK_SHIFT = 0x10  # Shift key

# Load Windows DLLs
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Callback type for low-level keyboard hook
HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.c_int,  # Return type
    ctypes.c_int,  # nCode
    wintypes.WPARAM,  # wParam
    wintypes.LPARAM,  # lParam
)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    """Windows keyboard hook data structure."""

    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KeyboardRestrictionService(QObject):
    """
    Service to block dangerous system keys in kiosk mode.

    Uses Windows low-level keyboard hook to intercept and block keys
    before they reach the system.
    """

    # Signals
    blocked_key_pressed = pyqtSignal(str)  # Emits name of blocked key combo

    def __init__(self, enabled: bool = True):
        super().__init__()
        self.enabled = enabled
        self.hook_handle = None
        self.hook_thread = None
        self._hook_proc = None  # Keep reference to prevent garbage collection

        # Track which keys are blocked
        self.blocked_combos = {
            "alt+tab": True,
            "alt+f4": True,
            "alt+esc": True,
            "win": True,
            "ctrl+shift+esc": True,
            "ctrl+esc": True,  # Also opens Start menu
        }

    def start(self):
        """Start the keyboard restriction hook."""
        if not self.enabled:
            logger.info("Keyboard restriction disabled, not starting")
            return

        if self.hook_handle:
            logger.warning("Keyboard hook already installed")
            return

        logger.info("Starting keyboard restriction service")

        # Start hook in separate thread with its own message loop
        self.hook_thread = threading.Thread(
            target=self._run_hook_loop, daemon=True, name="KeyboardHook"
        )
        self.hook_thread.start()

    def stop(self):
        """Stop the keyboard restriction hook."""
        if self.hook_handle:
            logger.info("Stopping keyboard restriction service")
            user32.UnhookWindowsHookEx(self.hook_handle)
            self.hook_handle = None

    def set_enabled(self, enabled: bool):
        """Enable or disable the restrictions."""
        self.enabled = enabled
        if enabled and not self.hook_handle:
            self.start()
        elif not enabled and self.hook_handle:
            self.stop()

    def _run_hook_loop(self):
        """Run the hook in its own thread with a message loop."""
        try:
            # Create the hook callback
            self._hook_proc = HOOKPROC(self._keyboard_hook_callback)

            # Install the hook
            self.hook_handle = user32.SetWindowsHookExW(
                WH_KEYBOARD_LL, self._hook_proc, kernel32.GetModuleHandleW(None), 0
            )

            if not self.hook_handle:
                error = ctypes.get_last_error()
                logger.error(f"Failed to install keyboard hook: error {error}")
                return

            logger.info("Keyboard restriction hook installed successfully")

            # Run message loop (required for low-level hooks)
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

        except Exception as e:
            logger.error(f"Error in keyboard hook thread: {e}")
        finally:
            if self.hook_handle:
                user32.UnhookWindowsHookEx(self.hook_handle)
                self.hook_handle = None

    def _keyboard_hook_callback(self, nCode: int, wParam: int, lParam: int) -> int:
        """
        Low-level keyboard hook callback.

        Returns:
            1 to block the key, or CallNextHookEx result to pass through
        """
        if nCode >= 0 and self.enabled:
            # Get the keyboard data
            kb_data = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            vk_code = kb_data.vkCode

            # Check modifier states
            alt_pressed = user32.GetAsyncKeyState(VK_MENU) & 0x8000
            ctrl_pressed = user32.GetAsyncKeyState(VK_CONTROL) & 0x8000
            shift_pressed = user32.GetAsyncKeyState(VK_SHIFT) & 0x8000

            # Check for blocked combinations
            blocked = False
            combo_name = ""

            # Windows key
            if vk_code in (VK_LWIN, VK_RWIN):
                if self.blocked_combos.get("win"):
                    blocked = True
                    combo_name = "Windows key"

            # Alt+Tab
            elif vk_code == VK_TAB and alt_pressed:
                if self.blocked_combos.get("alt+tab"):
                    blocked = True
                    combo_name = "Alt+Tab"

            # Alt+F4
            elif vk_code == VK_F4 and alt_pressed:
                if self.blocked_combos.get("alt+f4"):
                    blocked = True
                    combo_name = "Alt+F4"

            # Alt+Escape
            elif vk_code == VK_ESCAPE and alt_pressed:
                if self.blocked_combos.get("alt+esc"):
                    blocked = True
                    combo_name = "Alt+Escape"

            # Ctrl+Shift+Escape (Task Manager)
            elif vk_code == VK_ESCAPE and ctrl_pressed and shift_pressed:
                if self.blocked_combos.get("ctrl+shift+esc"):
                    blocked = True
                    combo_name = "Ctrl+Shift+Escape"

            # Ctrl+Escape (Start menu)
            elif vk_code == VK_ESCAPE and ctrl_pressed and not shift_pressed:
                if self.blocked_combos.get("ctrl+esc"):
                    blocked = True
                    combo_name = "Ctrl+Escape"

            if blocked:
                logger.debug(f"Blocked key combination: {combo_name}")
                # Emit signal (thread-safe via Qt's queued connection)
                try:
                    self.blocked_key_pressed.emit(combo_name)
                except Exception:
                    pass  # Don't let signal errors crash the hook
                return 1  # Block the key

        # Pass to next hook
        return user32.CallNextHookEx(self.hook_handle, nCode, wParam, lParam)

    def is_active(self) -> bool:
        """Check if the hook is currently active."""
        return self.hook_handle is not None and self.enabled

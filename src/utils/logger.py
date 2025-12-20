"""
Professional Structured Logging System
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


# Context variables for request tracking
_request_id: ContextVar[str] = ContextVar("request_id", default="")
_user_id: ContextVar[str] = ContextVar("user_id", default="")
_org_id: ContextVar[str] = ContextVar("org_id", default="")


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for production logging"""

    def format(self, record):
        """Format log record as structured JSON"""
        # Base log structure
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context if available
        if _request_id.get():
            log_entry["request_id"] = _request_id.get()
        if _user_id.get():
            log_entry["user_id"] = _user_id.get()
        if _org_id.get():
            log_entry["org_id"] = _org_id.get()

        # Add extra fields from record
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)

        # Add exception info if present
        if record.exc_info:
            import traceback

            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": "".join(traceback.format_exception(*record.exc_info)),
            }

        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output - Clean & Readable"""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[38;5;245m",  # Gray
        "INFO": "\033[38;5;39m",    # Bright Blue
        "WARNING": "\033[38;5;214m", # Orange
        "ERROR": "\033[38;5;196m",   # Red
        "CRITICAL": "\033[38;5;201m", # Magenta/Pink
    }
    
    BG_COLORS = {
        "DEBUG": "",
        "INFO": "",
        "WARNING": "\033[48;5;234m",  # Dark background for warnings
        "ERROR": "\033[48;5;52m",     # Dark red background
        "CRITICAL": "\033[48;5;53m",  # Dark magenta background
    }

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    
    # Colors for different parts
    TIME_COLOR = "\033[38;5;244m"      # Medium gray
    MODULE_COLOR = "\033[38;5;141m"    # Light purple
    CONTEXT_COLOR = "\033[38;5;244m"   # Gray
    MESSAGE_COLOR = "\033[38;5;255m"   # White

    # Level labels (short, clean)
    LEVEL_LABELS = {
        "DEBUG": "DBG",
        "INFO": "INF",
        "WARNING": "WRN",
        "ERROR": "ERR",
        "CRITICAL": "CRT",
    }

    def format(self, record):
        """Format log record with clean, readable colors"""
        level_color = self.COLORS.get(record.levelname, self.RESET)
        bg_color = self.BG_COLORS.get(record.levelname, "")
        level_label = self.LEVEL_LABELS.get(record.levelname, record.levelname[:3])

        # Format timestamp (cleaner)
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")

        # Format module name (clean, max 12 chars)
        module = record.name.split(".")[-1]
        if len(module) > 12:
            module = module[:11] + "…"

        # Build context info (only show if present, cleaner format)
        context_str = ""
        if _request_id.get():
            context_str = f"{self.CONTEXT_COLOR}#{_request_id.get()[:6]}{self.RESET} "

        # Build the formatted output
        # Format: TIME  LEVEL  MODULE  MESSAGE
        colored_output = (
            f"{self.TIME_COLOR}{timestamp}{self.RESET}  "
            f"{bg_color}{level_color}{self.BOLD}{level_label}{self.RESET}  "
            f"{self.MODULE_COLOR}{module:12}{self.RESET}  "
            f"{context_str}"
            f"{self.MESSAGE_COLOR}{record.getMessage()}{self.RESET}"
        )

        # Add exception info if present
        if record.exc_info:
            colored_output += f"\n{self.format_exception(record.exc_info)}"

        return colored_output

    def format_exception(self, exc_info):
        """Format exception with color"""
        import traceback

        tb = "".join(traceback.format_exception(*exc_info))
        return f"{self.COLORS['ERROR']}{tb}{self.RESET}"


class FileFormatter(logging.Formatter):
    """Structured formatter for file output"""

    def format(self, record):
        """Format log record for file with structured data"""
        # Base log structure
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context if available
        if _request_id.get():
            log_entry["request_id"] = _request_id.get()
        if _user_id.get():
            log_entry["user_id"] = _user_id.get()
        if _org_id.get():
            log_entry["org_id"] = _org_id.get()

        # Add extra fields from record
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)

        # Add exception info if present
        if record.exc_info:
            import traceback

            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": "".join(traceback.format_exception(*record.exc_info)),
            }

        return json.dumps(log_entry, ensure_ascii=False)


class SionyxLogger:
    """Professional logging system"""

    _initialized = False

    @classmethod
    def setup(cls, log_level=logging.INFO, log_to_file=True, enable_colors=True):
        """
        Setup professional logging system

        Args:
            log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Enable file logging
            enable_colors: Enable colored console output
        """
        if cls._initialized:
            return

        # Create logs directory in user's AppData (works with Program Files installation)
        # This avoids permission issues when installed in Program Files
        if getattr(sys, "frozen", False):
            # Running as PyInstaller executable - use AppData
            log_dir = Path.home() / "AppData" / "Local" / "SIONYX" / "logs"
        else:
            # Running as script - use project root
            app_dir = Path(__file__).parent.parent.parent
            log_dir = app_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Log files
        today = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"sionyx_{today}.log"
        error_log_file = log_dir / f"sionyx_errors_{today}.log"

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture everything
        root_logger.handlers.clear()

        # Console Handler (colored, INFO and above) - PyInstaller compatibility
        if sys.stdout is not None:
            console_handler = logging.StreamHandler(sys.stdout)
        else:
            # Fallback for PyInstaller when stdout is None
            console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        # Set UTF-8 encoding for console output
        if hasattr(console_handler.stream, "reconfigure"):
            console_handler.stream.reconfigure(encoding="utf-8")

        # Check if stdout is available and is a TTY (PyInstaller compatibility)
        stdout_available = sys.stdout is not None and hasattr(sys.stdout, "isatty")
        is_tty = stdout_available and sys.stdout.isatty()

        if enable_colors and is_tty:
            console_handler.setFormatter(ColoredFormatter())
        else:
            # Fallback to clean simple format if no colors or stdout issues
            simple_format = logging.Formatter(
                "%(asctime)s  %(levelname)-3.3s  %(name)-12.12s  %(message)s",
                datefmt="%H:%M:%S",
            )
            console_handler.setFormatter(simple_format)

        root_logger.addHandler(console_handler)

        # File Handler (detailed, all levels)
        if log_to_file:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(FileFormatter())
            root_logger.addHandler(file_handler)

            # Error File Handler (errors only)
            error_handler = logging.FileHandler(error_log_file, encoding="utf-8")
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(FileFormatter())
            root_logger.addHandler(error_handler)

        cls._initialized = True

        # Log startup banner (clean and minimal)
        logger = logging.getLogger(__name__)
        logger.info("")
        logger.info("━━━ SIONYX ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"    Log Level: {logging.getLevelName(log_level)}")
        if log_to_file:
            logger.info(f"    Log File: {log_file.name}")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("")

    @classmethod
    def cleanup_old_logs(cls, days_to_keep=7):
        """Remove log files older than specified days"""
        # Use same directory as setup
        if getattr(sys, "frozen", False):
            # Running as PyInstaller executable - use AppData
            log_dir = Path.home() / "AppData" / "Local" / "SIONYX" / "logs"
        else:
            # Running as script - use project root
            app_dir = Path(__file__).parent.parent.parent
            log_dir = app_dir / "logs"
        if not log_dir.exists():
            return

        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days_to_keep)

        for log_file in log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff.timestamp():
                log_file.unlink()
                logging.getLogger(__name__).debug(f"Deleted old log: {log_file.name}")


def set_context(request_id: str = None, user_id: str = None, org_id: str = None):
    """Set logging context for request tracking"""
    if request_id:
        _request_id.set(request_id)
    if user_id:
        _user_id.set(user_id)
    if org_id:
        _org_id.set(org_id)


def clear_context():
    """Clear all logging context"""
    _request_id.set("")
    _user_id.set("")
    _org_id.set("")


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return str(uuid.uuid4())[:8]


class StructuredLogger:
    """Enhanced logger with structured logging capabilities"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _log_with_context(
        self, level: int, message: str, extra_data: Dict[str, Any] = None
    ):
        """Log with structured context data"""
        extra = {}
        if extra_data:
            extra["extra_data"] = extra_data

        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Debug level logging with structured data"""
        self._log_with_context(logging.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs):
        """Info level logging with structured data"""
        self._log_with_context(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs):
        """Warning level logging with structured data"""
        self._log_with_context(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs):
        """Error level logging with structured data"""
        self._log_with_context(logging.ERROR, message, kwargs)

    def critical(self, message: str, **kwargs):
        """Critical level logging with structured data"""
        self._log_with_context(logging.CRITICAL, message, kwargs)

    def exception(self, message: str, **kwargs):
        """Exception logging with traceback"""
        self._log_with_context(logging.ERROR, message, kwargs)
        self.logger.exception(message)


def get_logger(name: str) -> StructuredLogger:
    """
    Get structured logger for a module

    Usage:
        from utils.logger import get_logger, set_context
        logger = get_logger(__name__)

        # Set context for request tracking
        set_context(request_id="req123", user_id="user456", org_id="org789")

        # Structured logging
        logger.info("User authenticated", user_id="user123", action="login")
        logger.error("Database error", operation="create_user", error_code="DB001")
        logger.debug("Processing request", request_data={"param": "value"})
    """
    return StructuredLogger(name)
